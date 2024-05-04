# -*- coding: utf-8 -*-

def terminology_entry_from_string(terminology_str):
    """Converts a terminology string to a dict.

    Example terminology string:

        Segmentation category and type - 3D Slicer General Anatomy list
        ~SCT^49755003^Morphologically Altered Structure
        ~SCT^4147007^Mass
        ~^^
        ~Anatomic codes - DICOM master list
        ~SCT^23451007^Adrenal gland
        ~SCT^24028007^Right

    Resulting dict:

        {
            'contextName': 'Segmentation category and type - 3D Slicer General Anatomy list',
            'category': ['SCT', '49755003', 'Morphologically Altered Structure'],
            'type': ['SCT', '4147007', 'Mass'],
            'anatomicContextName': 'Anatomic codes - DICOM master list',
            'anatomicRegion': ['SCT', '23451007', 'Adrenal gland'],
            'anatomicRegionModifier': ['SCT', '24028007', 'Right']
        }

    Specification of terminology entry string is available at
    https://slicer.readthedocs.io/en/latest/developer_guide/modules/segmentations.html#terminologyentry-tag
    """

    terminology_items = terminology_str.split('~')

    terminology = {}
    terminology['contextName'] = terminology_items[0]

    terminology['category'] = terminology_items[1].split("^")
    terminology['type'] = terminology_items[2].split("^")
    typeModifier = terminology_items[3].split("^")
    if any(item != '' for item in typeModifier):
        terminology['typeModifier'] = typeModifier

    anatomicContextName = terminology_items[4]
    if anatomicContextName:
        terminology['anatomicContextName'] = anatomicContextName
    anatomicRegion = terminology_items[5].split("^")
    if any(item != '' for item in anatomicRegion):
        terminology['anatomicRegion'] = anatomicRegion
        anatomicRegionModifier = terminology_items[6].split("^")
        if any(item != '' for item in anatomicRegionModifier):
            terminology['anatomicRegionModifier'] = anatomicRegionModifier

    return terminology

def terminology_entry_to_string(terminology):
    """Converts a terminology dict to string.
    """
    terminology_str = ""

    if 'contextName' in terminology:
        terminology_str += terminology['contextName']
    else:
        terminology_str += ""
    terminology_str += '~' + '^'.join(terminology['category'])
    terminology_str += '~' + '^'.join(terminology['type'])
    if 'typeModifier' in terminology:
        typeModifier = terminology['typeModifier']
    else:
        typeModifier = ['', '', '']
    terminology_str += '~' + '^'.join(typeModifier)

    if 'anatomicContextName' in terminology:
        terminology_str += "~" + terminology['anatomicContextName']
    else:
        terminology_str += "~"
    if 'anatomicRegion' in terminology:
        anatomic_region = terminology['anatomicRegion']
    else:
        anatomic_region = ['', '', '']
    terminology_str += '~' + '^'.join(anatomic_region)
    if 'anatomicRegionModifier' in terminology:
        anatomic_region_modifier = terminology['anatomicRegionModifier']
    else:
        anatomic_region_modifier = ['', '', '']
    terminology_str += '~' + '^'.join(anatomic_region_modifier)

    return terminology_str


def generate_unique_segment_id(existing_segment_ids):
    """Generate a unique segment ID, i.e., an ID that is not among existing_segment_ids."""
    i = 1
    while True:
        segment_id = "Segment_" + str(i)
        if segment_id not in existing_segment_ids:
            return segment_id
        i += 1


def read_segmentation(filename, skip_voxels=False):
    """Read segmentation metadata from a .seg.nrrd file and store it in a dict.

    Example header:

        NRRD0004
        # Complete NRRD file format specification at:
        # http://teem.sourceforge.net/nrrd/format.html
        type: unsigned char
        dimension: 3
        space: left-posterior-superior
        sizes: 128 128 34
        space directions: (-3.04687595367432,0,0) (0,-3.04687595367432,0) (0,0,9.9999999999999964)
        kinds: domain domain domain
        encoding: gzip
        space origin: (193.09599304199222,216.39599609374994,-340.24999999999994)
        Segment0_Color:=0.992157 0.909804 0.619608
        Segment0_ColorAutoGenerated:=1
        Segment0_Extent:=0 124 0 127 0 33
        Segment0_ID:=Segment_1
        Segment0_LabelValue:=1
        Segment0_Layer:=0
        Segment0_Name:=ribs
        Segment0_NameAutoGenerated:=1
        Segment0_Tags:=Segmentation.Status:inprogress|TerminologyEntry:Segmentation category and type - 3D Slicer General Anatomy list~SCT^123037004^Anatomical Structure~SCT^113197003^Rib~^^~Anatomic codes - DICOM master list~^^~^^|
        Segment1_Color:=1 1 0.811765
        Segment1_ColorAutoGenerated:=1
        Segment1_Extent:=0 124 0 127 0 33
        Segment1_ID:=Segment_2
        Segment1_LabelValue:=2
        Segment1_Layer:=0
        Segment1_Name:=cervical vertebral column
        Segment1_NameAutoGenerated:=1
        Segment1_Tags:=Segmentation.Status:inprogress|TerminologyEntry:Segmentation category and type - 3D Slicer General Anatomy list~SCT^123037004^Anatomical Structure~SCT^122494005^Cervical spine~^^~Anatomic codes - DICOM master list~^^~^^|
        Segment2_Color:=0.886275 0.792157 0.52549
        Segment2_ColorAutoGenerated:=1
        Segment2_Extent:=0 124 0 127 0 33
        Segment2_ID:=Segment_3
        Segment2_LabelValue:=3
        Segment2_Layer:=0
        Segment2_Name:=thoracic vertebral column
        Segment2_NameAutoGenerated:=1
        Segment2_Tags:=Some field:some value|Segmentation.Status:inprogress|TerminologyEntry:Segmentation category and type - 3D Slicer General Anatomy list~SCT^123037004^Anatomical Structure~SCT^122495006^Thoracic spine~^^~Anatomic codes - DICOM master list~^^~^^|
        Segmentation_ContainedRepresentationNames:=Binary labelmap|Closed surface|
        Segmentation_ConversionParameters:=Collapse labelmaps|1|Merge the labelmaps into as few shared labelmaps as possible 1 = created labelmaps will be shared if possible without overwriting each other.&Compute surface normals|1|Compute surface normals. 1 (default) = surface normals are computed. 0 = surface normals are not computed (slightly faster but produces less smooth surface display).&Crop to reference image geometry|0|Crop the model to the extent of reference geometry. 0 (default) = created labelmap will contain the entire model. 1 = created labelmap extent will be within reference image extent.&Decimation factor|0.0|Desired reduction in the total number of polygons. Range: 0.0 (no decimation) to 1.0 (as much simplification as possible). Value of 0.8 typically reduces data set size by 80% without losing too much details.&Default slice thickness|0.0|Default thickness for contours if slice spacing cannot be calculated.&End capping|1|Create end cap to close surface inside contours on the top and bottom of the structure.\n0 = leave contours open on surface exterior.\n1 (default) = close surface by generating smooth end caps.\n2 = close surface by generating straight end caps.&Fractional labelmap oversampling factor|1|Determines the oversampling of the reference image geometry. All segments are oversampled with the same value (value of 1 means no oversampling).&Joint smoothing|0|Perform joint smoothing.&Oversampling factor|1|Determines the oversampling of the reference image geometry. If it's a number, then all segments are oversampled with the same value (value of 1 means no oversampling). If it has the value "A", then automatic oversampling is calculated.&Reference image geometry|3.0468759536743195;0;0;-193.0959930419922;0;3.0468759536743195;0;-216.39599609374994;0;0;9.999999999999998;-340.24999999999994;0;0;0;1;0;127;0;127;0;33;|Image geometry description string determining the geometry of the labelmap that is created in course of conversion. Can be copied from a volume, using the button.&Smoothing factor|-0.5|Smoothing factor. Range: 0.0 (no smoothing) to 1.0 (strong smoothing).&Threshold fraction|0.5|Determines the threshold that the closed surface is created at as a fractional value between 0 and 1.&
        Segmentation_MasterRepresentation:=Binary labelmap
        Segmentation_ReferenceImageExtentOffset:=0 0 0
        
    Example header in case of overlapping segments:

        NRRD0004
        # Complete NRRD file format specification at:
        # http://teem.sourceforge.net/nrrd/format.html
        type: unsigned char
        dimension: 4
        space: left-posterior-superior
        sizes: 5 256 256 130
        space directions: none (0,1,0) (0,0,-1) (-1.2999954223632812,0,0)
        kinds: list domain domain domain
        encoding: gzip
        space origin: (86.644897460937486,-133.92860412597656,116.78569793701172)
        Segment0_...

    Returned segmentation object:

        {
            "voxels": (numpy array of voxel values),
            "ijkToLPS": [[  -3.04687595,    0.        ,    0.        ,  193.09599304],
                        [   0.        ,   -3.04687595,    0.        ,  216.39599609],
                        [   0.        ,    0.        ,   10.        , -340.25      ],
                        [   0.        ,    0.        ,    0.        ,    1.        ]],
            "encoding": "gzip",
            "containedRepresentationNames": ["Binary labelmap", "Closed surface"],
            "conversionParameters": [
                {"name": "Collapse labelmaps", "value": "1", "description": "Merge the labelmaps into as few shared labelmaps as possible 1 = created labelmaps will be shared if possible without overwriting each other."},
                {"name": "Compute surface normals", "value": "1", "description": "Compute surface normals. 1 (default) = surface normals are computed. 0 = surface normals are not computed (slightly faster but produces less smooth surface display)."},
                {"name": "Crop to reference image geometry", "value": "0", "description": "Crop the model to the extent of reference geometry. 0 (default) = created labelmap will contain the entire model. 1 = created labelmap extent will be within reference image extent."},
                {"name": "Decimation factor", "value": "0.0", "description": "Desired reduction in the total number of polygons. Range: 0.0 (no decimation) to 1.0 (as much simplification as possible). Value of 0.8 typically reduces data set size by 80% without losing too much details."},
                {"name": "Default slice thickness", "value": "0.0", "description": "Default thickness for contours if slice spacing cannot be calculated."},
                {"name": "End capping", "value": "1", "description": "Create end cap to close surface inside contours on the top and bottom of the structure.\n0 = leave contours open on surface exterior.\n1 (default) = close surface by generating smooth end caps.\n2 = close surface by generating straight end caps."},
                {"name": "Fractional labelmap oversampling factor", "value": "1", "description": "Determines the oversampling of the reference image geometry. All segments are oversampled with the same value (value of 1 means no oversampling)."},
                {"name": "Joint smoothing", "value": "0", "description": "Perform joint smoothing."},
                {"name": "Oversampling factor", "value": "1", "description": "Determines the oversampling of the reference image geometry. If it's a number, then all segments are oversampled with the same value (value of 1 means no oversampling). If it has the value \"A\", then automatic oversampling is calculated."},
                {"name": "Reference image geometry", "value": "3.0468759536743195;0;0;-193.0959930419922;0;3.0468759536743195;0;-216.39599609374994;0;0;9.999999999999998;-340.24999999999994;0;0;0;1;0;127;0;127;0;33;", "description": "Image geometry description string determining the geometry of the labelmap that is created in course of conversion. Can be copied from a volume, using the button."},
                {"name": "Smoothing factor", "value": "-0.5", "description": "Smoothing factor. Range: 0.0 (no smoothing) to 1.0 (strong smoothing)."},
                {"name": "Threshold fraction", "value": "0.5", "description": "Determines the threshold that the closed surface is created at as a fractional value between 0 and 1."}
            ],
            "masterRepresentation": "Binary labelmap",
            "referenceImageExtentOffset": [0, 0, 0]           
            "segments": [
                {
                    "color": [0.992157, 0.909804, 0.619608],
                    "colorAutoGenerated": true,
                    "extent": [0, 124, 0, 127, 0, 33],
                    "id": "Segment_1",
                    "labelValue": 1,
                    "layer": 0,
                    "name": "ribs",
                    "nameAutoGenerated": true,
                    "status": "inprogress",
                    "terminology": {
                        "contextName": "Segmentation category and type - 3D Slicer General Anatomy list",
                        "category": ["SCT", "123037004", "Anatomical Structure"],
                        "type": ["SCT", "113197003", "Rib"] }
                },
                {
                    "color": [1.0, 1.0, 0.811765],
                    "colorAutoGenerated": true,
                    "extent": [0, 124, 0, 127, 0, 33],
                    "id": "Segment_2",
                    "labelValue": 2,
                    "layer": 0,
                    "name": "cervical vertebral column",
                    "nameAutoGenerated": true,
                    "status": "inprogress",
                    "terminology": {
                        "contextName": "Segmentation category and type - 3D Slicer General Anatomy list",
                        "category": ["SCT", "123037004", "Anatomical Structure"],
                        "type": ["SCT", "122494005", "Cervical spine"] },
                    "tags": {
                        "Some field": "some value" }
                }
            ]
        }
    """

    from collections import OrderedDict
    import logging
    import nrrd
    import numpy as np
    import re

    if skip_voxels:
        header = nrrd.read_header(filename)
        voxels = None
    else:
        voxels, header = nrrd.read(filename)

    segmentation = OrderedDict()

    segments_fields = {}  # map from segment index to key:value map

    multiple_layers = False
    spaceToLps = np.eye(4)
    ijkToSpace = np.eye(4)

    # Store header fields
    for header_key in header:
        if header_key in ["type", "endian", "dimension", "sizes"]:
            # these are stored in the voxel array, it would be redundant to store in metadata
            continue

        if header_key == "space":
            if header[header_key] == "left-posterior-superior":
                spaceToLps = np.eye(4)
            elif header[header_key] == "right-anterior-superior":
                spaceToLps = np.diag([-1.0, -1.0, 1.0, 1.0])
            else:
                # LPS and RAS are the most commonly used image orientations, for now we only support these
                raise IOError("space field must be 'left-posterior-superior' or 'right-anterior-superior'")
            continue
        elif header_key == 'kinds':
            if header[header_key] == ['domain', 'domain', 'domain']:
                multiple_layers = False
            elif header[header_key] == ['list', 'domain', 'domain', 'domain']:
                multiple_layers = True
            else:
                raise IOError("kinds field must be 'domain domain domain' or 'list domain domain domain'")
            continue
        elif header_key == "space origin":
            ijkToSpace[0:3, 3] = header[header_key]
            continue
        elif header_key == "space directions":
            space_directions = header[header_key]
            if space_directions.shape[0] == 4:
                # 4D segmentation, skip first (nan) row
                ijkToSpace[0:3, 0:3] = header[header_key][1:4, 0:3]
            else:
                ijkToSpace[0:3, 0:3] = header[header_key]
            continue
        elif header_key == "Segmentation_ContainedRepresentationNames":
            # Segmentation_ContainedRepresentationNames:=Binary labelmap|Closed surface|
            representations = header[header_key].split("|")
            representations[:] = [item for item in representations if item != '']  # Remove empty elements
            segmentation["containedRepresentationNames"] = representations
            continue
        elif header_key == "Segmentation_ConversionParameters":
            parameters = []
            # Segmentation_ConversionParameters:=Collapse labelmaps|1|Merge the labelmaps into as few...&Compute surface normals|1|Compute...&Crop to reference image geometry|0|Crop the model...&
            parameters_str = header[header_key].split("&")
            for parameter_str in parameters_str:
                if not parameter_str.strip():
                    # empty parameter description is ignored
                    continue
                parameter_info = parameter_str.split("|")
                if len(parameter_info) != 3:
                    raise IOError("Segmentation_ConversionParameters field value is invalid (each parameter must be defined by 3 strings)")
                parameters.append({"name": parameter_info[0], "value": parameter_info[1], "description": parameter_info[2]})
            if parameters:
                segmentation["conversionParameters"] = parameters
            continue
        elif header_key == "Segmentation_MasterRepresentation":
            # Segmentation_MasterRepresentation:=Binary labelmap
            segmentation["masterRepresentation"] = header[header_key]
            continue
        elif header_key == "Segmentation_ReferenceImageExtentOffset":
            # Segmentation_ReferenceImageExtentOffset:=0 0 0
            segmentation["referenceImageExtentOffset"] = [int(i) for i in header[header_key].split(" ")]
            continue
        
        segment_match = re.match("^Segment([0-9]+)_(.+)", header_key)
        if segment_match:
            # Store in segment_fields (segmentation field)
            segment_index = int(segment_match.groups()[0])
            segment_key = segment_match.groups()[1]
            if segment_index not in segments_fields:
                segments_fields[segment_index] = {}
            segments_fields[segment_index][segment_key] = header[header_key]
            continue
        
        segmentation[header_key] = header[header_key]

    # Compute voxel to physical transformation matrix
    ijkToLps = np.dot(spaceToLps, ijkToSpace)
    segmentation["ijkToLPS"] = ijkToLps

    segmentation["voxels"] = voxels

    # Process segment_fields to build segment_info

    # Get all used segment IDs (necessary for creating unique segment IDs)
    segment_ids = set()
    for segment_index in segments_fields:
        if "ID" in segments_fields[segment_index]:
            segment_ids.add(segments_fields[segment_index]["ID"])

    # Store segment metadata in segments_info
    segments_info = []
    for segment_index in sorted(segments_fields.keys()):
        segment_fields = segments_fields[segment_index]
        if "ID" in segment_fields:  # Segment0_ID:=Segment_1
            segment_id = segment_fields["ID"]
        else:
            segment_id = generate_unique_segment_id(segment_ids)
            segment_ids.add(segment_id)
            logging.debug(f"Segment ID was not found for index {segment_index}, use automatically generated ID: {segment_id}")

        segment_info = {}
        segment_info["id"] = segment_id
        if "Color" in segment_fields:
            segment_info["color"] = [float(i) for i in segment_fields["Color"].split(" ")]  # Segment0_Color:=0.501961 0.682353 0.501961
        if "ColorAutoGenerated" in segment_fields:
            segment_info["colorAutoGenerated"] = int(segment_fields["ColorAutoGenerated"]) != 0  # Segment0_ColorAutoGenerated:=1
        if "Extent" in segment_fields:
            segment_info["extent"] = [int(i) for i in segment_fields["Extent"].split(" ")]  # Segment0_Extent:=68 203 53 211 24 118
        if "LabelValue" in segment_fields:
            segment_info["labelValue"] = int(segment_fields["LabelValue"])  # Segment0_LabelValue:=1
        if "Layer" in segment_fields:
            segment_info["layer"] = int(segment_fields["Layer"])  # Segment0_Layer:=0
        if "Name" in segment_fields:
            segment_info["name"] = segment_fields["Name"]  # Segment0_Name:=Segment_1
        if "NameAutoGenerated" in segment_fields:
            segment_info["nameAutoGenerated"] = int(segment_fields["NameAutoGenerated"]) != 0  # Segment0_NameAutoGenerated:=1
        # Segment0_Tags:=Segmentation.Status:inprogress|TerminologyEntry:Segmentation category and type - 3D Slicer General Anatomy list
        # ~SCT^85756007^Tissue~SCT^85756007^Tissue~^^~Anatomic codes - DICOM master list~^^~^^|
        if "Tags" in segment_fields:
            tags = {}
            tags_str = segment_fields["Tags"].split("|")
            for tag_str in tags_str:
                tag_str = tag_str.strip()
                if not tag_str:
                    continue
                key, value = tag_str.split(":", maxsplit=1)
                # Process known tags: TerminologyEntry and Segmentation.Status, store all other tags as they are
                if key == "TerminologyEntry":
                    segment_info["terminology"] = terminology_entry_from_string(value)
                elif key == "Segmentation.Status":
                    segment_info["status"] = value
                else:
                    tags[key] = value
            if tags:
                segment_info["tags"] = tags
        segments_info.append(segment_info)

    segmentation["segments"] = segments_info

    return segmentation


def write_segmentation(file, segmentation, compression_level=9, index_order=None):
    """
    Extracts segments from a segmentation volume and header.
    :param segmentation: segmentation metadata and voxels
    """
    import numpy as np

    voxels = segmentation["voxels"]
    if voxels is None:
        raise ValueError("Segmentation does not contain voxels")

    # Copy non-segmentation fields to the extracted header
    output_header = {}

    for key in segmentation:
        if key == "voxels":
            # written separately
            continue
        if key == "segments":
            # written later
            continue
        elif key == "ijkToLPS":
            # image geometry will be set later in space directions, space origin fields
            ijkToLPS = segmentation[key]
            continue
        elif key == "containedRepresentationNames":
            # Segmentation_ContainedRepresentationNames:=Binary labelmap|Closed surface|
            # An extra closing "|" is added as this is requires by some older Slicer versions.
            representations = "|".join(segmentation[key]) + "|"
            output_header["Segmentation_ContainedRepresentationNames"] = representations
        elif key == "conversionParameters":
            # Segmentation_ConversionParameters:=Collapse labelmaps|1|Merge the labelmaps into as few...&Compute surface normals|1|Compute...&Crop to reference image geometry|0|Crop the model...&
            parameters_str = ""
            parameters = segmentation[key]
            for parameter in parameters:
                if parameters_str != "":
                    parameters_str += "&"
                parameters_str += f"{parameter['name']}|{parameter['value']}|{parameter['description']}"
            output_header["Segmentation_ConversionParameters"] = parameters_str
        elif key == "masterRepresentation":
            # Segmentation_MasterRepresentation:=Binary labelmap
            output_header["Segmentation_MasterRepresentation"] = segmentation[key]
        elif key == "referenceImageExtentOffset":
            # Segmentation_ReferenceImageExtentOffset:=0 0 0
            offset = segmentation[key]
            output_header["Segmentation_ReferenceImageExtentOffset"] = " ".join([str(i) for i in offset])
        else:
            output_header[key] = segmentation[key]

    # Add kinds, space directions, space origin to the header
    # kinds: list domain domain domain
    kinds = ["domain", "domain", "domain"]

    # space directions: (0,1,0) (0,0,-1) (-1.2999954223632812,0,0)
    # 'space directions', array([
        #   [ 0.        ,  1.        ,  0.        ],
        #   [ 0.        ,  0.        , -1.        ],
        #   [-1.29999542,  0.        ,  0.        ]]))
    space_directions = np.array(ijkToLPS)[0:3, 0:3]

    # Add 4th dimension metadata if array is 4-dimensional (there are overlapping segments)
    dims = len(voxels.shape)
    if dims == 4:
        # kinds: list domain domain domain
        # ('kinds', ['list', 'domain', 'domain', 'domain'])
        kinds = ["list"] + kinds
        # space directions: none (0,1,0) (0,0,-1) (-1.2999954223632812,0,0)
        # 'space directions', array([
        #   [        nan,         nan,         nan],
        #   [ 0.        ,  1.        ,  0.        ],
        #   [ 0.        ,  0.        , -1.        ],
        #   [-1.29999542,  0.        ,  0.        ]]))
        nan_column = np.array()
        space_directions = np.row_stack(([np.nan, np.nan, np.nan], space_directions))
    elif dims != 3:
        raise ValueError("Unsupported number of dimensions: " + str(dims))

    output_header["kinds"] = kinds
    output_header["space directions"] = space_directions
    output_header["space origin"] = np.array(ijkToLPS)[0:3, 3]
    output_header["space"] = "left-posterior-superior"  # DICOM uses LPS coordinate system

    # Set defaults
    if "encoding" not in segmentation:
        output_header["encoding"] = "gzip"
    if "referenceImageExtentOffset" not in segmentation:
        output_header["Segmentation_ReferenceImageExtentOffset"] = "0 0 0"
    if "masterRepresentation" not in segmentation:
        output_header["Segmentation_MasterRepresentation"] = "Binary labelmap"

    # Add segments fields to the header

    # Get list of segment IDs (needed if we need to genereate new ID)
    segment_ids = set()
    for output_segment_index, segment in enumerate(segmentation["segments"]):
        if "id" in segment:
            segment_ids.add(segment["id"])

    for output_segment_index, segment in enumerate(segmentation["segments"]):

        # Copy all segment fields corresponding to this segment
        output_tags = []
        for segment_key in segment:
            if segment_key == "labelValue":
                # Segment0_LabelValue:=1
                field_name = "LabelValue"
                value = str(segment[segment_key])
            elif segment_key == "layer":
                # Segment0_Layer:=0
                field_name = "Layer"
                value = str(segment[segment_key])
            elif segment_key == "name":
                # Segment0_Name:=Segment_1
                field_name = "Name"
                value = segment[segment_key]
            elif segment_key == "id":    
                # Segment0_ID:=Segment_1
                field_name = "ID"
                value = segment[segment_key]
            elif segment_key == "color":
                # Segment0_Color:=0.501961 0.682353 0.501961
                field_name = "Color"
                value = ' '.join([str(i) for i in segment[segment_key]])
            elif segment_key == "nameAutoGenerated":
                # Segment0_NameAutoGenerated:=1
                field_name = "NameAutoGenerated"
                value = 1 if segment[segment_key] else 0
            elif segment_key == "colorAutoGenerated":
                # Segment0_ColorAutoGenerated:=1
                field_name = "ColorAutoGenerated"
                value = 1 if segment[segment_key] else 0
            # Process information stored in tags, for example:
            # Segment0_Tags:=Segmentation.Status:inprogress|TerminologyEntry:Segmentation category and type - 3D Slicer General Anatomy list
            # ~SCT^85756007^Tissue~SCT^85756007^Tissue~^^~Anatomic codes - DICOM master list~^^~^^|
            elif segment_key == "terminology":
                # Terminology is stored in a tag
                terminology_str = terminology_entry_to_string(segment[segment_key])
                output_tags.append(f"TerminologyEntry:{terminology_str}")
                # Add tags later
                continue
            elif segment_key == "status":
                # Segmentation status is stored in a tag
                output_tags.append(f"Segmentation.Status:{segment[segment_key]}")
                # Add tags later
                continue
            elif segment_key == "tags":
                # Other tags
                tags = segment[segment_key]
                for tag_key in tags:
                    output_tags.append(f"{tag_key}:{tags[tag_key]}")
                # Add tags later
                continue
            elif segment_key == "extent":
                # Segment0_Extent:=68 203 53 211 24 118
                field_name = "Extent"
                value = ' '.join([str(i) for i in segment[segment_key]])
            else:
                field_name = segment_key
                value = segment[segment_key]

            output_header[f"Segment{output_segment_index}_{field_name}"] = value
                
        if "id" not in segment:
            # If user has not specified ID, generate a unique one
            new_segment_id = generate_unique_segment_id(segment_ids)
            output_header[f"Segment{output_segment_index}_ID"] = new_segment_id
            segment_ids.add(new_segment_id)

        if "layer" not in segment:
            # If user has not specified layer, set it to 0
            output_header[f"Segment{output_segment_index}_Layer"] = "0"

        if "extent" not in segment:
            # If user has not specified extent, set it to the full extent
            output_shape = voxels.shape[-3:]
            output_header[f"Segment{output_segment_index}_Extent"] = f"0 {output_shape[0]-1} 0 {output_shape[1]-1} 0 {output_shape[2]-1}"

        # Add tags
        # Need to end with "|" as earlier Slicer versions require this
        output_header[f"Segment{output_segment_index}_Tags"] = "|".join(output_tags) + "|"

    # Write segmentation to file
    if index_order is None:
        index_order = 'F'
    import nrrd
    nrrd.write(file, voxels, output_header, compression_level=compression_level, index_order=index_order)


def segment_from_name(segmentation, segment_name):
    segments = segmentation["segments"]
    for segment in segments:
        if segment_name == segment["name"]:
            return segment
    raise KeyError("segment not found by name " + segment_name)


def segments_from_name(segmentation, segment_name):
    found_segments = []
    segments = segmentation["segments"]
    for segment in segments:
        if segment_name == segment["name"]:
            found_segments.append(segment)
    return found_segments


def segments_from_terminology(segmentation, terminology):
    found_segments = []
    segments = segmentation["segments"]
    for segment in segments:
        if "terminology" in segment:
            if terminology_entry_matches(segment["terminology"], terminology):
                found_segments.append(segment)
    return found_segments

def terminology_code_matches(code1, code2):
    # Coding scheme designator
    if code1[0] != code2[0]:
        return False
    # Code value
    if code1[1] != code2[1]:
        return False
    return True

def terminology_entry_matches(terminology1, terminology2):
    # Category
    if not terminology_code_matches(terminology1['category'], terminology2['category']):
        return False
    # Type
    if not terminology_code_matches(terminology1['type'], terminology2['type']):
        return False
    # Optional type modifier
    if "typeModifier" in terminology1 and "typeModifier" in terminology2:
        # Both have type modifier
        if not terminology_code_matches(terminology1['typeModifier'], terminology2['typeModifier']):
            return False
    elif "typeModifier" in terminology1 or "typeModifier" in terminology2:
        # Only one of the two has type modifier
        return False
    # Optional anatomic region
    if "anatomicRegion" in terminology1 and "anatomicRegion" in terminology2:
        # Both have anatomic region
        if not terminology_code_matches(terminology1['anatomicRegion'], terminology2['anatomicRegion']):
            return False
        # Optional anatomic region modifier
        if "anatomicRegionModifier" in terminology1 and "anatomicRegionModifier" in terminology2:
            # Both have anatomic region modifier
            if not terminology_code_matches(terminology1['anatomicRegionModifier'][0], terminology2['anatomicRegionModifier'][0]):
                return False
        elif "anatomicRegionModifier" in terminology1 or "anatomicRegionModifier" in terminology2:
            # Only one of the two has anatomic region modifier
            return False
    elif "anatomicRegion" in terminology1 or "anatomicRegion" in terminology2:
        # Only one of the two has anatomic region
        return False
    # Terminologies match
    return True

def segment_id_from_name(segmentation, segment_name):
    segments = segmentation["segments"]
    for segment in segments:
        if segment_name == segments[segment_id]["name"]:
            return segment_id
    raise KeyError("segment_id not found by name " + segment_name)


def segment_names(segmentation):
    names = []
    segments = segmentation["segments"]
    for segment in segments:
        names.append(segment["name"])
    return names


def extract_segments(segmentation, segment_names_to_label_values, minimalExtent=False):
    """
    Extracts segments from a segmentation volume and header.
    Segmentation is collapsed into a 3D volume, if there were overlapping segments then the ones listed later in the segment_names_to_label_values list will overwrite the earlier ones.
    :param voxels: 3D or 4D array of voxel values
    :param header: dictionary of NRRD header fields
    :param segmentation_metadata: dictionary of segmentation metadata
    :param segment_names_to_label_values: list of segment name to label value pairs
    :param minimalExtent: if True then only the minimal extent of the segment is stored. False is recommended for compatibility with older Slicer versions.
    :return: 3D array of extracted voxels, dictionary of extracted header fields
    """

    from collections import OrderedDict
    import copy
    import numpy as np

    voxels = segmentation["voxels"]
    if voxels is None:
        raise ValueError("Segmentation does not contain voxels")

    # Create empty array from last 3 dimensions (output will be flattened to a 3D array)
    output_shape = voxels.shape[-3:]
    output_voxels = np.zeros(output_shape, dtype=voxels.dtype)

    # Crete independent copy of the input image and segmentation
    output_segmentation = OrderedDict()

    output_segmentation["voxels"] = output_voxels
    
    for key in segmentation:
        if key == "voxels":
            continue
        elif key == "segments":
            continue
        else:
            output_segmentation[key] = copy.deepcopy(segmentation[key])

    output_segments = []
    output_segmentation["segments"] = output_segments

    # Copy extracted segments
    dims = len(voxels.shape)
    for output_segment_index, segment_name_to_label_value in enumerate(segment_names_to_label_values):
        if type(segment_name_to_label_value[0]) is str:
            # Find segment from terminology
            segments = segments_from_name(segmentation, segment_name_to_label_value[0])
        else:
            segments = segments_from_terminology(segmentation, segment_name_to_label_value[0])
        if not segments:
            raise ValueError(f"Segment not found: {segment_name_to_label_value[0]}")
        segment_id = segments[0]["id"]
        output_segment = copy.deepcopy(segments[0])
        output_label_value = segment_name_to_label_value[1]
        output_segment["labelValue"] = output_label_value
        output_segment["layer"] = 0 # Output is a single layer (3D volume)

        unionOfAllExtents = [0, -1, 0, -1, 0, -1]
        for segment in segments:
            # Copy relabeled voxel data
            input_label_value = segment["labelValue"]
            if dims == 3:
                segment_voxel_positions = np.where(output_voxels[voxels == input_label_value])
            elif dims == 4:
                inputLayer = segment["layer"]
                segment_voxel_positions = np.where(voxels[inputLayer, :, :, :] == input_label_value)
            else:
                raise ValueError("Voxel array dimension is invalid")
            output_voxels[segment_voxel_positions] = output_label_value
            if minimalExtent:
                if "extent" in segment:
                    extent = segment["extent"]
                    if _isValidExtent(extent):
                        # Valid extent, expand the current extent
                        if _isValidExtent(unionOfAllExtents):
                            for axis in range(3):
                                if extent[axis*2] < unionOfAllExtents[axis*2]:
                                    unionOfAllExtents[axis*2] = extent[axis*2]
                                if extent[axis*2+1] > unionOfAllExtents[axis*2+1]:
                                    unionOfAllExtents[axis*2+1] = extent[axis*2+1]
                        else:
                            unionOfAllExtents = extent.copy()

        if minimalExtent:
            output_segment["extent"] = unionOfAllExtents
        else:
            # Use the full extent as segment extent. This is a workaround for a Slicer bug
            # that used the first segment's extent when reading a layer, cropping all other segments
            # that had larger extent than the first segment.
            output_segment["extent"] = [0, output_shape[0]-1, 0, output_shape[1]-1, 0, output_shape[2]-1]

        output_segments.append(output_segment)

    return output_segmentation

def _isValidExtent(extent):
    return extent[0] <= extent[1] and extent[2] <= extent[3] and extent[4] <= extent[5]
