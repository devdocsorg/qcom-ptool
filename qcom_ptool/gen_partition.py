# Copyright (c) 2019, The Linux Foundation. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#     * Neither the name of The Linux Foundation nor the names of its
#       contributors may be used to endorse or promote products derived
#       from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY EXPRESS OR IMPLIED
# WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NON-INFRINGEMENT
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from __future__ import annotations

import getopt
import os
import sys
import xml.etree.ElementTree as ET
from typing import NoReturn
from xml.dom import minidom

from qcom_ptool.loaders import load as load_spec
from qcom_ptool.spec import DiskParams, PartitionsByLun


def usage() -> NoReturn:
    """Print the ``gen_partition`` command-line usage and exit with status 1.

    Raises:
        SystemExit: Always.

    Example:
        ``qcom-ptool gen_partition -h`` prints this usage.
    """
    print(
        "\n\tUsage:\n"
        "\t  %s -i <input> -o <output> "
        "[-m name1=image1,name2=image2,...]\n"
        "\t  %s --board <board.yaml> [--hlos <name>] [--boot-fw <name>] "
        "[--root <dir>] [-C <outdir> | -o <out1> -o <out2> ...]\n"
        "\n\tIn --board mode each storage is written to "
        "<outdir>/<storage-id>/partitions.xml\n"
        "\t(default outdir: .), or to one explicit -o per storage in "
        "declared order.\n"
        "\tVersion 1.0\n" % (sys.argv[0], sys.argv[0])
    )
    sys.exit(1)


def generate_multi_lun_xml(
    disk_params: DiskParams, partitions: PartitionsByLun, output_xml: str
) -> None:
    """Write a partitions.xml file for ptool from disk parameters and partitions.

    Disk parameters other than ``size`` and ``type`` become ``KEY=value`` lines in
    ``parser_instructions``; each LUN (physical partition) with at least one entry
    becomes a ``physical_partition`` element, in ascending LUN order.

    Args:
        disk_params (DiskParams): Normalised disk parameters from a loader.
        partitions (PartitionsByLun): Partition entries grouped by LUN.
        output_xml (str): Path of the XML file to write.

    Example:
        ``generate_multi_lun_xml(spec["disk"], spec["partitions"], "partitions.xml")``
    """
    root = ET.Element("configuration")
    parser_instruction_text = ""

    for key, value in disk_params.items():
        if key != "size" and key != "type":
            parser_instruction_text += "\n\t" + str(key) + "=" + str(value) + "\n\t"

    ET.SubElement(root, "parser_instructions").text = parser_instruction_text

    for _phys_part, entries in sorted(partitions.items(), key=lambda item: int(item[0])):
        found = False
        for part_entry in entries:

            # if there is no partition in the LUN, skip the physical_partition in XML
            # only create the physical_partition once we have at least one partition
            if not found:
                phy_part = ET.SubElement(root, "physical_partition")
            ET.SubElement(phy_part, "partition", attrib=part_entry)
            found = True

    xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml()
    with open(output_xml, "w") as f:
        f.write(xmlstr)


def generate_partition_xml(
    disk_params: DiskParams, partitions: PartitionsByLun, output_xml: str
) -> None:
    """Write partitions.xml for a supported storage type, or report an unsupported one.

    eMMC, NVMe, SPI-NOR, and UFS layouts are written with
    ``generate_multi_lun_xml``; any other type prints a message and writes nothing.

    Args:
        disk_params (DiskParams): Normalised disk parameters, including ``type``.
        partitions (PartitionsByLun): Partition entries grouped by LUN.
        output_xml (str): Path of the XML file to write.

    Example:
        ``generate_partition_xml(spec["disk"], spec["partitions"], "partitions.xml")``
    """
    print("Generating %s XML %s" % (disk_params["type"].upper(), output_xml))

    if disk_params["type"] in ("emmc", "nvme", "spinor", "ufs"):
        generate_multi_lun_xml(disk_params, partitions, output_xml)
    else:
        print(
            "%s XML generation is curently not supported."
            % (disk_params["type"].upper())
        )


###############################################################################
# main


def main(argv: list[str] | None = None) -> int:
    """Run ``gen_partition``: convert a partition layout or a board file into partitions.xml.

    With ``-i`` a single ``.conf`` or YAML layout is written to the one ``-o``
    output. With ``--board`` every storage of the resolved board is written to
    ``<outdir>/<storage-id>/partitions.xml`` or to one ``-o`` per storage.
    ``-m name=file,...`` overrides partition file names.

    Args:
        argv (list[str] | None): Command line including the program name; ``sys.argv`` when None.

    Returns:
        int: 0 on success, 1 when the layout or board cannot be loaded or the
        outputs do not match the storages.

    Raises:
        SystemExit: The options are invalid or ``-h`` is given; usage is printed.

    Example:
        ``main(["gen_partition", "-i", "platforms/qcs6490-rb3gen2/ufs/partitions.conf", "-o", "partitions.xml"])``
        returns ``0``.
    """
    if argv is None:
        argv = sys.argv

    if len(argv) < 3:
        usage()

    input_file: str | None = None
    board_file: str | None = None
    root: str | None = None
    hlos: str | None = None
    boot_fw: str | None = None
    outputs: list[str] = []
    outdir: str | None = None
    image_map: dict[str, str] = {}

    if argv[1] == "-h" or argv[1] == "--help":
        usage()
    try:
        opts, _rem = getopt.getopt(
            argv[1:], "i:o:m:C:", ["board=", "hlos=", "boot-fw=", "root="]
        )
        for opt, arg in opts:
            if opt == "-i":
                input_file = arg
            elif opt == "-o":
                outputs.append(arg)
            elif opt == "--board":
                board_file = arg
            elif opt == "--hlos":
                hlos = arg
            elif opt == "--boot-fw":
                boot_fw = arg
            elif opt == "--root":
                root = arg
            elif opt == "-C":
                outdir = arg
            elif opt == "-m":
                for mapping in arg.split(","):
                    tags = mapping.split("=")
                    if len(tags) > 1:
                        image_map[tags[0]] = tags[1]
            else:
                usage()
    except Exception as argerr:
        print(str(argerr))
        usage()

    if (board_file is None) == (input_file is None):
        print("Error: pass exactly one of -i <input> or --board <board.yaml>")
        usage()
    if outputs and outdir is not None:
        print("Error: pass either -C <outdir> or explicit -o outputs, not both")
        usage()

    if board_file is not None:
        return _run_board(board_file, root, hlos, boot_fw, outputs, outdir, image_map)

    if input_file is None or len(outputs) != 1:
        print("Error: -i single-storage mode takes exactly one -o")
        usage()
    try:
        spec = load_spec(input_file, image_map=image_map)
    except Exception as e:
        print("Error: ", e)
        return 1

    generate_partition_xml(spec["disk"], spec["partitions"], outputs[0])
    return 0


def _run_board(
    board_file: str,
    root: str | None,
    hlos: str | None,
    boot_fw: str | None,
    outputs: list[str],
    outdir: str | None,
    image_map: dict[str, str],
) -> int:
    """Resolve a board file and write one partitions.xml per storage.

    Args:
        board_file (str): Board YAML file.
        root (str | None): Platforms directory for ``extends`` and ``includes``, or None to derive it.
        hlos (str | None): ``hlos`` variant overlay name, or None.
        boot_fw (str | None): ``boot-fw`` variant overlay name, or None.
        outputs (list[str]): Explicit output paths, one per storage in board order;
            empty to write under ``outdir``.
        outdir (str | None): Directory for ``<storage-id>/partitions.xml`` outputs; ``.`` when None.
        image_map (dict[str, str]): Partition names mapped to replacement file names.

    Returns:
        int: 0 on success, 1 when the board cannot be resolved or the number of
        outputs differs from the number of storages.

    Example:
        ``_run_board("platforms/boards/glymur-crd.yaml", None, None, None, [], "platforms/glymur-crd", {})``
        writes ``platforms/glymur-crd/nvme/partitions.xml`` and ``platforms/glymur-crd/spinor/partitions.xml``.
    """
    # Late import so the -i path never pulls in PyYAML / jsonschema.
    from qcom_ptool.board import board_to_specs, resolve_board

    try:
        board = resolve_board(board_file, root=root, hlos=hlos, boot_fw=boot_fw)
        specs = board_to_specs(board, image_map=image_map)
    except Exception as e:
        print("Error: ", e)
        return 1

    if not outputs:
        # Default layout: one <outdir>/<storage-id>/partitions.xml per storage.
        base = outdir if outdir is not None else "."
        outputs = [os.path.join(base, sid, "partitions.xml") for sid, _ in specs]
        for path in outputs:
            os.makedirs(os.path.dirname(path), exist_ok=True)

    if len(outputs) != len(specs):
        ids = ", ".join(sid for sid, _ in specs)
        print(
            "Error: board declares %d storage(s) [%s] but %d -o output(s) given"
            % (len(specs), ids, len(outputs))
        )
        return 1

    for (sid, spec), output in zip(specs, outputs):
        print("Storage %s -> %s" % (sid, output))
        generate_partition_xml(spec["disk"], spec["partitions"], output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
