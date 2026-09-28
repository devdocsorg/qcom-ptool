# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause

import getopt
import os
import sys
from xml.etree import ElementTree as ET


def usage():
    """Print the ``gen_contents`` usage text and exit.

    :raises SystemExit: Always, with status 1.

    Example: ``qcom-ptool gen_contents -h`` calls this function.
    """
    print(
        (
            "\n\tUsage: %s -t <template> -p <partitions_xml_path> -o <output> \n\tVersion 0.1\n"
            % (sys.argv[0])
        )
    )
    sys.exit(1)


def ParseXML(XMLFile):
    """Parse an XML file and return its root element.

    :param XMLFile: Path of the XML file to parse.
    :type XMLFile: str
    :returns: The root element, or ``None`` after printing an error when the file is
        missing or malformed.
    :rtype: xml.etree.ElementTree.Element | None

    Example: ``ParseXML("partitions.xml").tag`` returns ``"configuration"``.
    """
    try:
        tree = ET.parse(XMLFile)
        root = tree.getroot()
        return root
    except FileNotFoundError:
        print(f"Error: File '{XMLFile}' not found")
        return None
    except ET.ParseError as e:
        print(f"Error: Failed parsing '{XMLFile}': {e}")
        return None


def UpdateMetaData(TemplateRoot, PartitionRoot, BuildId):
    """Fill a contents template with build IDs and the files a partition XML needs.

    Every ``builds_flat/build`` receives a ``build_id``. In the ``common`` build, the
    placeholder ``download_file``, ``partition_file`` and ``partition_patch_file``
    entries are replaced with one entry per partition image, GPT file, rawprogram
    file and patch file.

    :param TemplateRoot: Root element of the parsed ``contents.xml.in`` template; changed in place.
    :type TemplateRoot: xml.etree.ElementTree.Element
    :param PartitionRoot: Root element of the parsed ``partitions.xml``.
    :type PartitionRoot: xml.etree.ElementTree.Element
    :param BuildId: Text written to each ``build_id`` element; may be empty.
    :type BuildId: str

    Example: ``UpdateMetaData(ParseXML("contents.xml.in"), ParseXML("partitions.xml"), "")``
    """
    ChipIdList = TemplateRoot.findall("product_info/chipid")
    DefaultStorageType: str = ""
    for ChipId in ChipIdList:
        Flavor = ChipId.get("flavor")
        StorageType = ChipId.get("storage_type")
        print(f"Chipid Flavor: {Flavor} Storage Type: {StorageType}")
        if Flavor == "default":
            DefaultStorageType = ChipId.get("storage_type", "")

    PhyPartition = PartitionRoot.findall("physical_partition")
    Partitions = []
    for partition in PartitionRoot.findall("physical_partition/partition"):
        label = partition.get("label")
        filename = partition.get("filename")
        if label and filename:
            Partitions.append({"label": label, "filename": filename})
    print(f"Partitions: {Partitions}")

    def _add_file_elements(parent_element, pathname, file_path_flavor=None):
        """Helper function to add file_name and file_path sub-elements.

        :param parent_element: Element that receives ``file_name`` and ``file_path``.
        :type parent_element: xml.etree.ElementTree.Element
        :param pathname: File path split into its name and directory.
        :type pathname: str
        :param file_path_flavor: Optional ``flavor`` attribute for ``file_path``.
        :type file_path_flavor: str | None

        Example: ``_add_file_elements(build, "gpt_main0.bin")`` adds ``gpt_main0.bin`` in ``.``.
        """
        file_name_text = os.path.basename(pathname)
        file_path_text = os.path.dirname(pathname)
        if not file_path_text:  # no directory, use explicit . as current dir
            file_path_text = "."

        new_file_name = ET.SubElement(parent_element, "file_name")
        new_file_name.text = file_name_text
        new_file_path = ET.SubElement(parent_element, "file_path")
        if file_path_flavor:
            new_file_path.set("flavor", file_path_flavor)
        new_file_path.text = file_path_text

    builds = TemplateRoot.findall("builds_flat/build")
    for build in builds:
        Name = build.find("name")
        if Name is None or Name.text is None:
            continue
        print(f"Build Name: {Name.text}")
        new_build_id = ET.SubElement(build, "build_id")
        new_build_id.text = BuildId
        if Name.text != "common":
            continue
        DownloadFile = build.find("download_file")
        if DownloadFile is not None:
            build.remove(DownloadFile)
            # Partition entires
            for Partition in Partitions:
                new_download_file = ET.SubElement(build, "download_file")
                new_download_file.set("fastboot_complete", Partition["label"])
                _add_file_elements(new_download_file, Partition["filename"])
            # GPT Main & GPT Backup entries
            for PhysicalPartitionNumber in range(0, len(PhyPartition)):
                new_download_file = ET.SubElement(build, "download_file")
                new_download_file.set("storage_type", DefaultStorageType)
                _add_file_elements(
                    new_download_file, "gpt_main%d.bin" % (PhysicalPartitionNumber)
                )
                new_download_file = ET.SubElement(build, "download_file")
                new_download_file.set("storage_type", DefaultStorageType)
                _add_file_elements(
                    new_download_file, "gpt_backup%d.bin" % (PhysicalPartitionNumber)
                )

        PartitionFile = build.find("partition_file")
        if PartitionFile is not None:
            build.remove(PartitionFile)
            # Rawprogram entries
            for PhysicalPartitionNumber in range(0, len(PhyPartition)):
                new_partition_file = ET.SubElement(build, "partition_file")
                new_partition_file.set("storage_type", DefaultStorageType)
                _add_file_elements(
                    new_partition_file,
                    "rawprogram%d.xml" % (PhysicalPartitionNumber),
                    "default",
                )

        PartitionPatchFile = build.find("partition_patch_file")
        if PartitionPatchFile is not None:
            build.remove(PartitionPatchFile)
            # Patch entries
            for PhysicalPartitionNumber in range(0, len(PhyPartition)):
                new_partition_patch_file = ET.SubElement(build, "partition_patch_file")
                new_partition_patch_file.set("storage_type", DefaultStorageType)
                _add_file_elements(
                    new_partition_patch_file,
                    "patch%d.xml" % (PhysicalPartitionNumber),
                    "default",
                )


###############################################################################
# main
###############################################################################


if len(sys.argv) < 3:
    usage()

try:
    if sys.argv[1] == "-h" or sys.argv[1] == "--help":
        usage()
    try:
        build_id = ""
        opts, rem = getopt.getopt(sys.argv[1:], "t:p:o:b:")
        for opt, arg in opts:
            if opt in ["-t"]:
                template = arg
            elif opt in ["-p"]:
                partition_xml = arg
            elif opt in ["-o"]:
                output_xml = arg
            elif opt in ["-b"]:
                build_id = arg
            else:
                usage()
    except Exception as argerr:
        print(str(argerr))
        usage()

    print("Selected Template:  " + template)
    xml_root = ParseXML(template)

    print("Selected Partition XML:  " + partition_xml)
    partition_root = ParseXML(partition_xml)

    UpdateMetaData(xml_root, partition_root, build_id)

    OutputTree = ET.ElementTree(xml_root)
    ET.indent(OutputTree, space="\t", level=0)
    OutputTree.write(
        output_xml, encoding="utf-8", xml_declaration=True, short_empty_elements=False
    )
except Exception as e:
    print(("Error: ", e))
    sys.exit(1)

sys.exit(0)
