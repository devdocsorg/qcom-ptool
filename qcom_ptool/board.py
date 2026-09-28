# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause
"""
Multi-storage board model and composition resolver.

A board file declares a ``platform`` and a list of ``storage`` devices, each
with its own partitions. Three composition mechanisms layer on top:

* board-level ``extends:`` - inherit a single base board and override by
  stable identifier (storage ``id``, partition ``name``);
* storage-level ``includes:`` - concatenate shared partition fragments from
  ``_common/`` into a storage's partition list;
* variant overlays (``--hlos`` / ``--boot-fw``) - applied last, merged by the
  same identifiers.

Resolution order is: base board -> derived board -> storage includes ->
variant overlays. Merges are deep and field-by-field; entries are matched by
``id`` (storage) or ``name`` (partition), and anything unmatched is appended
in file order. There is no partition deletion in v1.

The resolver operates on raw YAML dicts. Each fully-resolved storage is then
validated against the strict single-storage ``partitions.schema.json`` and
reduced to a :class:`qcom_ptool.spec.LoadedSpec` through the very same
normalisation helpers the YAML loader uses, so a resolved board emits XML
byte-identical to an equivalent hand-written single-storage file.
"""

from __future__ import annotations

import copy
import json
import os
from collections.abc import Mapping, Sequence
from importlib import resources
from typing import Any, TypedDict

import jsonschema
import yaml  # type: ignore[import-untyped]

from qcom_ptool.loaders.yaml import _disk_from_node, _partition_from_node
from qcom_ptool.spec import LoadedSpec, PartitionsByLun

_SCHEMA_PACKAGE = "qcom_ptool.schema"

# Storage keys that describe the disk geometry (everything except id / includes
# / partitions). Used to reduce a resolved storage into the single-storage
# document shape that partitions.schema.json validates.
_DISK_KEYS = (
    "type",
    "size",
    "sector-size",
    "write-protect-boundary",
    "grow-last-partition",
    "align-partitions",
)


class BoardResolveError(ValueError):
    """Raised when a board file cannot be loaded, composed or validated."""


class ResolvedBoard(TypedDict):
    """A board with every extends/includes/variant applied."""

    platform: dict[str, Any]
    storage: list[dict[str, Any]]


# ---------------------------------------------------------------------------
# Schema / file helpers
# ---------------------------------------------------------------------------


def _load_schema(name: str) -> dict[str, Any]:
    """Return a packaged JSON Schema by file name.

    :param name: Schema file in ``qcom_ptool/schema``, such as ``board.schema.json``.
    :returns: The parsed schema.

    Example: ``_load_schema("board.schema.json")["required"]`` returns ``["storage"]``.
    """
    text = resources.files(_SCHEMA_PACKAGE).joinpath(name).read_text(encoding="utf-8")
    schema: dict[str, Any] = json.loads(text)
    return schema


def _read_mapping(path: str, schema: str) -> dict[str, Any]:
    """Load ``path`` as YAML, validate against ``schema`` and return a copy.

    :param path: YAML file to read.
    :param schema: Schema file name used for validation.
    :returns: A deep copy of the validated mapping.
    :raises BoardResolveError: If the file cannot be read, is not a mapping, or fails validation.

    Example: ``_read_mapping("platforms/boards/glymur-crd.yaml", "board.schema.json")["platform"]``
    returns ``{"name": "glymur-crd"}``.
    """
    try:
        with open(path) as f:
            document = yaml.safe_load(f)
    except OSError as exc:
        raise BoardResolveError("cannot read %s: %s" % (path, exc)) from exc
    if not isinstance(document, Mapping):
        raise BoardResolveError(
            "%s: expected a top-level mapping, got %s" % (path, type(document).__name__)
        )
    try:
        jsonschema.validate(document, _load_schema(schema))
    except jsonschema.exceptions.ValidationError as exc:
        raise BoardResolveError("%s: schema validation failed: %s" % (path, exc.message)) from exc
    return copy.deepcopy(dict(document))


# ---------------------------------------------------------------------------
# Deep-merge primitives (by stable identifier)
# ---------------------------------------------------------------------------


def _merge_partitions(base: list[dict[str, Any]], overlay: Sequence[Mapping[str, Any]]) -> None:
    """Merge ``overlay`` partitions into ``base`` by ``name``.

    A same-named partition is deep-merged field-by-field in place (so an
    override can set only ``size`` and inherit the rest); a new partition is
    appended in overlay order. Nothing is ever moved or removed.

    :param base: Partition list changed in place.
    :param overlay: Partitions merged into ``base``.

    Example: ``_merge_partitions(base, [{"name": "efi", "size": "8KB"}])`` changes only the
    size of ``efi`` in ``base``.
    """
    index = {p["name"]: p for p in base if "name" in p}
    for entry in overlay:
        name = entry.get("name")
        target = index.get(name)
        if target is not None:
            target.update(copy.deepcopy(dict(entry)))
        else:
            new_entry = copy.deepcopy(dict(entry))
            base.append(new_entry)
            if name is not None:
                index[name] = new_entry


def _merge_storage(base: dict[str, Any], overlay: Mapping[str, Any]) -> None:
    """Merge one storage ``overlay`` into ``base`` (matched by id upstream).

    :param base: Storage mapping changed in place.
    :param overlay: Storage fields to merge; ``partitions`` and ``includes`` are merged,
        other fields replace the base value.

    Example: ``_merge_storage(storage, {"id": "ufs", "size": 2048})`` sets ``storage["size"]``.
    """
    for key, value in overlay.items():
        if key == "id":
            continue
        if key == "partitions":
            base.setdefault("partitions", [])
            _merge_partitions(base["partitions"], value)
        elif key == "includes":
            merged = base.setdefault("includes", [])
            for inc in value:
                if inc not in merged:
                    merged.append(inc)
        else:
            base[key] = copy.deepcopy(value)


def _merge_storage_list(base: list[dict[str, Any]], overlay: Sequence[Mapping[str, Any]]) -> None:
    """Merge ``overlay`` storage entries into ``base`` by ``id``.

    :param base: Storage list changed in place.
    :param overlay: Storages merged by ``id``; unmatched storages are appended.

    Example: ``_merge_storage_list(board["storage"], overlay["storage"])``
    """
    index = {s["id"]: s for s in base if "id" in s}
    for entry in overlay:
        sid = entry.get("id")
        target = index.get(sid)
        if target is not None:
            _merge_storage(target, entry)
        else:
            new_entry = copy.deepcopy(dict(entry))
            base.append(new_entry)
            if sid is not None:
                index[sid] = new_entry


# ---------------------------------------------------------------------------
# Board-level extends
# ---------------------------------------------------------------------------


def _load_board_with_extends(path: str, root: str, chain: tuple[str, ...]) -> dict[str, Any]:
    """Load a board file and fold its single base (if any) underneath it.

    :param path: Board file to load.
    :param root: Platforms directory that ``extends`` paths resolve against.
    :param chain: Real paths already visited, used to detect cycles.
    :returns: The board with its base folded underneath it.
    :raises BoardResolveError: On an ``extends`` cycle or an invalid file.

    Example: ``_load_board_with_extends("platforms/boards/glymur-crd.yaml", "platforms", ())``
    """
    real = os.path.realpath(path)
    if real in chain:
        raise BoardResolveError("extends cycle detected at %s" % path)
    board = _read_mapping(path, "board.schema.json")
    base_ref = board.pop("extends", None)
    if base_ref is None:
        return board
    base_path = os.path.join(root, base_ref)
    base = _load_board_with_extends(base_path, root, (*chain, real))
    _merge_storage_list(base.setdefault("storage", []), board.get("storage", []))
    if "platform" in board:
        base["platform"] = board["platform"]
    return base


# ---------------------------------------------------------------------------
# Storage-level includes
# ---------------------------------------------------------------------------


def _fragment_partitions(path: str, root: str, chain: tuple[str, ...]) -> list[dict[str, Any]]:
    """Resolve a ``_common/`` fragment (transitively) into a partition list.

    :param path: Fragment file to load.
    :param root: Platforms directory that ``includes`` paths resolve against.
    :param chain: Real paths already visited, used to detect cycles.
    :returns: The fragment's partitions after its own includes.
    :raises BoardResolveError: On an ``includes`` cycle or an invalid file.

    Example: ``_fragment_partitions("platforms/_common/boot.yaml", "platforms", ())``
    """
    real = os.path.realpath(path)
    if real in chain:
        raise BoardResolveError("includes cycle detected at %s" % path)
    fragment = _read_mapping(path, "include.schema.json")
    partitions: list[dict[str, Any]] = []
    for inc in fragment.get("includes", []):
        inc_parts = _fragment_partitions(os.path.join(root, inc), root, (*chain, real))
        _merge_partitions(partitions, inc_parts)
    _merge_partitions(partitions, fragment.get("partitions", []))
    return partitions


def _expand_includes(storage: dict[str, Any], root: str) -> None:
    """Replace a storage's ``includes:`` + inline ``partitions:`` with one list.

    Ordering: included fragments in listed order first, then the storage's own
    inline partitions, with same-named entries merged in place.

    :param storage: Storage mapping changed in place.
    :param root: Platforms directory that ``includes`` paths resolve against.
    :raises BoardResolveError: If an included fragment is invalid or cyclic.

    Example: ``_expand_includes(storage, "platforms")`` leaves ``storage`` without ``includes``.
    """
    includes = storage.pop("includes", [])
    expanded: list[dict[str, Any]] = []
    for inc in includes:
        inc_parts = _fragment_partitions(os.path.join(root, inc), root, ())
        _merge_partitions(expanded, inc_parts)
    _merge_partitions(expanded, storage.get("partitions", []))
    storage["partitions"] = expanded


# ---------------------------------------------------------------------------
# Public resolution
# ---------------------------------------------------------------------------


def _variant_path(root: str, axis: str, name: str) -> str:
    """Return the file path of a variant overlay.

    :param root: Platforms directory.
    :param axis: Variant axis, ``hlos`` or ``boot-fw``.
    :param name: Variant name without the ``.yaml`` suffix.
    :returns: ``<root>/variants/<axis>/<name>.yaml``.

    Example: ``_variant_path("platforms", "hlos", "debian")`` returns
    ``"platforms/variants/hlos/debian.yaml"``.
    """
    return os.path.join(root, "variants", axis, name + ".yaml")


def _validate_resolved_storage(storage: Mapping[str, Any]) -> None:
    """Validate a fully-resolved storage against the strict single-storage schema.

    :param storage: Fully resolved storage.
    :raises BoardResolveError: If the storage does not satisfy ``partitions.schema.json``.

    Example: ``_validate_resolved_storage(board["storage"][0])`` returns ``None`` for a valid storage.
    """
    disk = {k: storage[k] for k in _DISK_KEYS if k in storage}
    document = {"disk": disk, "partitions": storage.get("partitions", [])}
    try:
        jsonschema.validate(document, _load_schema("partitions.schema.json"))
    except jsonschema.exceptions.ValidationError as exc:
        raise BoardResolveError(
            "storage %r resolved to an invalid spec: %s"
            % (storage.get("id", "?"), exc.message)
        ) from exc


def resolve_board(
    path: str,
    root: str | None = None,
    hlos: str | None = None,
    boot_fw: str | None = None,
) -> ResolvedBoard:
    """Resolve ``path`` into a fully-composed :class:`ResolvedBoard`.

    ``root`` is the platforms directory that ``extends:`` / ``includes:`` paths
    and variant names resolve against; it defaults to the parent of the board
    file's directory when that directory is ``boards/``, else the board file's
    own directory.

    :param path: Board file.
    :param root: Platforms directory, or ``None`` to derive it.
    :param hlos: HLOS variant name, or ``None``.
    :param boot_fw: Boot firmware variant name, or ``None``.
    :returns: The composed platform and storages.
    :raises BoardResolveError: If a file is invalid, cyclic, or resolves to an invalid storage.

    Example: ``len(resolve_board("platforms/boards/glymur-crd.yaml")["storage"])`` returns ``2``.
    """
    if root is None:
        parent = os.path.dirname(os.path.abspath(path))
        root = os.path.dirname(parent) if os.path.basename(parent) == "boards" else parent

    board = _load_board_with_extends(path, root, ())
    storages = board.get("storage", [])
    if not storages:
        raise BoardResolveError("%s: board declares no storage" % path)

    for storage in storages:
        _expand_includes(storage, root)

    for axis, name in (("hlos", hlos), ("boot-fw", boot_fw)):
        if name is None:
            continue
        overlay = _read_mapping(_variant_path(root, axis, name), "board.schema.json")
        _merge_storage_list(storages, overlay.get("storage", []))

    for storage in storages:
        _validate_resolved_storage(storage)

    return {"platform": board.get("platform", {}), "storage": storages}


# ---------------------------------------------------------------------------
# Reduction to the emitter's LoadedSpec
# ---------------------------------------------------------------------------


def storage_to_loaded_spec(
    storage: Mapping[str, Any],
    image_map: Mapping[str, str] | None = None,
) -> LoadedSpec:
    """Reduce one resolved storage to a LoadedSpec via the YAML loader helpers.

    :param storage: Fully resolved storage.
    :param image_map: Partition name to image filename overrides.
    :returns: The normalised disk settings and partitions.

    Example: ``storage_to_loaded_spec(board["storage"][0])["disk"]["type"]`` returns ``"nvme"``
    for Glymur-CRD.
    """
    if image_map is None:
        image_map = {}
    disk = _disk_from_node(storage)
    partitions: PartitionsByLun = {}
    for node in storage.get("partitions", []):
        phys_part, entry = _partition_from_node(node, image_map)
        partitions.setdefault(phys_part, []).append(entry)
    return {"disk": disk, "partitions": partitions}


def board_to_specs(
    board: ResolvedBoard,
    image_map: Mapping[str, str] | None = None,
) -> list[tuple[str, LoadedSpec]]:
    """Reduce a resolved board to ``[(storage_id, LoadedSpec), ...]`` in order.

    :param board: Resolved board.
    :param image_map: Partition name to image filename overrides.
    :returns: Storage IDs paired with their normalised specifications.

    Example: ``[sid for sid, _ in board_to_specs(board)]`` returns ``["nvme", "spinor"]``
    for Glymur-CRD.
    """
    return [
        (storage.get("id", ""), storage_to_loaded_spec(storage, image_map))
        for storage in board["storage"]
    ]
