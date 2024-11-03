from typing import Any
import numpy
from pandas.core.common import flatten

import arcpy

PY_VERSION: str = "PYTHON_9.3"  # is this really required by arc???


def area_unit_converter(unit_name: str) -> float:
    """
    Converts the base unit of `SquareMetres` to the desired unit.

    :param unit_name:
    :type str:
        The name of the desired areal unit to convert to.

    :return:
    :type float:
        The scale factor for converting from square metres to the desired unit.

    :raises:
    KeyError
        If the desired unit is not found, a KeyError is returned.
    """
    # ideally, lowercase keys would be used, to avoid case sensitiveness,
    # but these labels are
    mapper: dict[str, float] = {
        "Acres": 4046.86,
        "Ares": 100.0,
        "Hectares": 10000.0,
        "SquareCentimeters": 0.0001,
        "SquareDecimeters": 0.01,
        "SquareMeters": 1.0,
        "SquareFeet": 0.092903,
        "SquareInches": 0.00064516,
        "SquareKilometers": 1000000.0,
        "SquareMiles": 2589990.0,
        "SquareMillimeters": 0.000001,
        "SquareYards": 0.83613,
    }

    result = mapper.get(unit_name, None)

    if result is None:
        msg: str = f"Areal unit name not found: {unit_name}"
        raise KeyError(msg)

    return result


def unique(data: list[Any]) -> list[Any]:
    """
    Given a list of elements, return a unique listing.
    """
    # alternatively just use set(data)
    # but following (with some mods) the original implementation
    uniq = numpy.unique(data).tolist()

    return uniq


def unique_2D(
    data: list[tuple[list[Any], list[Any]]]
) -> list[tuple[list[Any], list[Any]]]:
    """
    Given a list of lists, eg [[1, 2], [3, 4], [5, 6]], return the unique listing
    of the 2 element entries.

    :param data:
    :type list:
        A list containing entries of 2 element lists.

    :return:
    :type list:
        A unique listing of the 2 element entries.
    """
    uniq = numpy.unique(data, axis=0).tolist()

    return uniq


def calculate_common(data1: list[Any], data2: list[Any]) -> int:
    """
    Calculate the intersection of two lists and return the total number
    of common elements.

    :param data1:
         A list of elements.

    :param data2:
         A list of elements.

    :return:
        The total number of common elements between both lists.
    """
    n_common = len(set(data1).intersection(data2))

    return n_common


def delete_items(data: list[str]) -> None:
    """
    Wrapper for an ArcGIS method for deleting features either on disk or in-memory.

    :param data:
        A list of entries (presumably strings) that ArcGIS would delete.

    :return:
        None.
    """
    if data:
        for item in data:
            arcpy.AddMessage(f"Deleting: {item}")
            arcpy.Delete_management(item)
    else:
        arcpy.AddMessage("No data items to delete")


def add_id_field(feature: str, field_name: str) -> None:
    """
    Wrapper for an ArcGIS method to create a featureID fields with
    unique ID values.
    The field type is specified to be LONG with a precision of 15.

    :param feature:
        A string referring to a specific feature class.

    :param field_name:
        A string referring to the field name to insert into the feature class.

    :return:
        None.
    """
    field_type: str = "LONG"
    field_precision: int = 15
    expression: str = "!OBJECTID!"

    fields = arcpy.ListFields(feature)
    field_names = [f.name for f in fields]

    if field_name in field_names:
        arcpy.AddMessage(f"{field_name} exists and will be recalculated")
    else:
        arcpy.AddField_management(feature, field_name, field_type, field_precision)

    arcpy.CalculateField_management(feature, field_name, expression, PY_VERSION)

    arcpy.AddMessage(f"{field_name} added and calculated")


# TODO: investigate
#   is this a close duplicate of add_id_field???
#   specifies the field name, doesn't add a final arcpy.AddMessage
#   but more or less is doing the same as add_id_field()
def calculate_feature_ids(feature: str) -> None:
    """
    Wrapper for an ArcGIS method to calculate and add unique feature IDs
    to a feature ID field.
    The field name is defined to be "featID", with a field type of "Long"
    and a field precision of 6.

    :param feature:
        A string referring to a specific feature class.

    :return:
        None.
    """
    field_name: str = "featID"
    field_type: str = "LONG"
    field_precision: int = 15
    expression: str = "!OBJECTID!"

    fields = arcpy.ListFields(feature)
    field_names = [f.name for f in fields]

    if field_name in field_names:
        arcpy.AddMessage(f"{field_name} exists and will be recalculated")
    else:
        arcpy.AddField_management(feature, field_name, field_type, field_precision)

    arcpy.CalculateField_management(feature, field_name, expression)


def calculate_feature_id_angle(
    in_link_feat: str, origin_point_feat: str, dest_point_feat: str
):
    field: str = "featID1"
    in_id: str = "ORIG_FID"
    join_id: str = "OBJECTID"

    expression: str = f"!{origin_point_feat}.featID!"
    addLongField(in_link_feat, origin_point_feat, field, in_id, join_id, expression)

    field = "angle1"
    expression = f"!{origin_point_feat}.angle!"
    addField(in_link_feat, origin_point_feat, field, in_id, join_id, expression)

    field = "featID2"
    in_id = "DEST_FID"
    join_id = "OBJECTID"
    expression = f"!{dest_point_feat}.featID!"
    addLongField(in_link_feat, dest_point_feat, field, in_id, join_id, expression)

    field = "angle2"
    expression = f"!{dest_point_feat}.angle!"
    addField(in_link_feat, dest_point_feat, field, in_id, join_id, expression)


def delete_field(feature: str, field_name: str) -> None:
    """
    Wrapper for an ArcGIS method to delete a field from a given feature.

    :param feature:
        A string referring to a specific feature class.

    :param field_name:
        A string referring to the field name to insert into the feature class.

    :return:
        None.
    """
    fields = arcpy.ListFields(feature)
    field_names = [f.name for f in fields if f.name == field_name]

    if field_names:
        arcpy.AddMessage(f"{field_name} exists and will be deleted")
        arcpy.DeleteField_management(feature, field_names)
    else:
        arcpy.AddMessage(f"{field_name} does not exist")


def find_new_feature_ids(
    feature: str, ids: list[int], near_ids: list[int]
) -> list[int]:
    """
    Finds the polygon features that connect with each other (e.g near_dist == 0)
    and generate a new list of feature IDs with the connected features being
    assigned the same feature ID.
    """
    # TODO:
    #     this whole function needs an overhaul

    obj_ids: list[int] = []
    feat_ids: list[int] = []

    cursor = arcpy.SearchCursor(feature)
    for row in cursor:
        obj_id = row.getValue("OBJECTID")
        feat_id = row.getValue("featID")
        feat_ids.append(feat_id)
        obj_ids.append(obj_id)

    # each element contains a list of ids referring to connected features
    # eg [[1, 2, 3, 5], [4, 9], [6, 13]]
    temp_list_list: list[list[int]] = []

    another_list = []

    # loop over each feature
    for i, idx in enumerate(ids):
        temp_list = []
        if idx not in another_list:
            # get the ID of its connected feature
            near_id = near_ids[i]
            temp_list.append(idx)
            temp_list.append(near_id)

            temp_arr = numpy.where(numpy.asarray(ids) == near_id)[0]

            for el in temp_arr:
                temp_list.append(near_ids[el])

            unq = unique(temp_list)
            temp_list_list.append(unq)

            # flatten to convert 2D list to 1D list
            another_list = list(flatten(temp_list_list))

    temp_list_list1: list[list[int]] = []

    # original comment indicated a deep copy
    # list.copy() is only a shallow copy ...
    temp_list_list_copy = temp_list_list.copy()

    while len(temp_list_list) > 0:
        temp_list = temp_list_list[0]
        temp_list_copy = temp_list.copy()

        for temp_list1 in temp_list_list_copy:
            length = calculate_common(temp_list_copy, temp_list1)

            if length:
                temp_list_list.remove(temp_list1)

                for el in temp_list1:
                    temp_list_copy.append(el)

                temp_list_copy = unique(temp_list_copy)

        list1 = list(flatten(temp_list_copy))
        list2 = unique(list1)
        temp_list_list1.append(list2)
        temp_list_list_copy = temp_list_list.copy()

    # generate a new list of feature IDs
    # the connected features are assigned the same feature ID
    feature_ids_new = feat_ids.copy()
    for temp_list in temp_list_list1:
        index_list = []
        feature_id_list = []

        for idv in temp_list:
            idx = obj_ids.index(idv)
            feature_id = feat_ids[idx]
            index_list.append(idx)
            feature_id_list.append(feature_id)

        for index in index_list:
            feature_ids_new[index] = feat_ids[0]

    return feature_ids_new


# def find_new_feature_ids_1(feature: str, head_feature: str, foot_feature: str, distance):
#     """
#     Identifies the linear polygon features that can be connected.
#     These features satisfy the following conditions:
#         1. The distance between the head of one feature and the foot of
#            another feature is less than a user-defined threshold
#         2. The two nearby features align in orientation with the
#            intersecting angle < 45 degrees.
#     Generates a new list of feature IDs with the connected features
#     being assigned the same feature ID.
#     """
#    # TODO:
#    #     this whole function needs an overhaul
#    # not including for now, as it doesn't appear to be called by anything anywhere


#         # inFeat: input linear Bathymetric Low features
#         # headFeat: input head features
#         # footFeat: input foot features
#         # distThreshold: a distance threshold used to evaluate the connecting condition
#
#         ## connect features that have head to foot distance less than the distance threshold, and intersecting angle less than 45 degree
#
#         ### calculate distances between the head and foot features
#         itemList = []
#
#         headFeat1 = "headFeat1"
#         footFeat1 = "footFeat1"
#         itemList.append(headFeat1)
#         itemList.append(footFeat1)
#
#         arcpy.Copy_management(headFeat, headFeat1)
#         arcpy.Copy_management(footFeat, footFeat1)
#
#         fieldName = "featID"
#         self.deleteField(headFeat1, fieldName)
#         self.deleteField(footFeat1, fieldName)
#
#         fieldName = "rectangle_Orientation"
#         self.deleteField(headFeat1, fieldName)
#         self.deleteField(footFeat1, fieldName)
#
#         headFeat2 = "headFeat2"
#         footFeat2 = "footFeat2"
#         itemList.append(headFeat2)
#         itemList.append(footFeat2)
#         ## use spatial join to copy the featID and rectangle_Orientation fields to the head and foot features
#         arcpy.SpatialJoin_analysis(headFeat1, inFeat, headFeat2)
#         arcpy.SpatialJoin_analysis(footFeat1, inFeat, footFeat2)
#         # Calculates distances between head and foot features within the input distance threshold (searchRadius)
#         nearTable = "head_foot_nearTable"
#         itemList.append(nearTable)
#         location = "NO_LOCATION"
#         angle = "NO_ANGLE"
#         closest = "ALL"
#         searchRadius = distThreshold
#         arcpy.GenerateNearTable_analysis(
#             headFeat2,
#             footFeat2,
#             nearTable,
#             search_radius=searchRadius,
#             location=location,
#             angle=angle,
#             closest=closest,
#         )
#
#         ### get initial list of a pair of features that have head to foot distance less than the input distance threshold
#
#         headIDList1 = []
#         footIDList1 = []
#         cursor = arcpy.SearchCursor(nearTable)
#         for row in cursor:
#             inFID = row.getValue("IN_FID")
#             nearFID = row.getValue("NEAR_FID")
#             headIDList1.append(inFID)
#             footIDList1.append(nearFID)
#         del cursor, row
#
#         # get  attribute values from the input head features
#         headIDAll = []
#         headFeatIDAll = []
#         headOrientationAll = []
#         cursor = arcpy.SearchCursor(headFeat2)
#         for row in cursor:
#             objectID = row.getValue("OBJECTID")
#             featID = row.getValue("featID")
#             orientation = row.getValue("rectangle_Orientation")
#             headIDAll.append(objectID)
#             headFeatIDAll.append(featID)
#             headOrientationAll.append(orientation)
#         del cursor, row
#         # get  attribute values from the input foot features
#         footIDAll = []
#         footFeatIDAll = []
#         footOrientationAll = []
#         cursor = arcpy.SearchCursor(footFeat2)
#         for row in cursor:
#             objectID = row.getValue("OBJECTID")
#             featID = row.getValue("featID")
#             orientation = row.getValue("rectangle_Orientation")
#             footIDAll.append(objectID)
#             footFeatIDAll.append(featID)
#             footOrientationAll.append(orientation)
#         del cursor, row
#
#         headFeatIDList1 = []
#         footFeatIDList1 = []
#         headOrientationList1 = []
#         footOrientationList1 = []
#
#         for idv in headIDList1:
#             featID = headFeatIDAll[headIDAll.index(idv)]
#             orientation = headOrientationAll[headIDAll.index(idv)]
#             headFeatIDList1.append(featID)
#             headOrientationList1.append(orientation)
#
#         for idv in footIDList1:
#             featID = footFeatIDAll[footIDAll.index(idv)]
#             orientation = footOrientationAll[footIDAll.index(idv)]
#             footFeatIDList1.append(featID)
#             footOrientationList1.append(orientation)
#
#         ### calculate intersecting angles for the feature pairs
#         angleList = []
#         i = 0
#         while i < len(headOrientationList1):
#             orientation1 = headOrientationList1[i]
#             orientation2 = footOrientationList1[i]
#             orientation_diff = abs(orientation1 - orientation2)
#             angleList.append(orientation_diff)
#             i += 1
#
#         ### select feature pairs that have intersecting angle less than 45 degree
#         idListList1 = []
#         headFeatIDList2 = []
#         footFeatIDList2 = []
#         i = 0
#         while i < len(angleList):
#             angle = angleList[i]
#             headFeatID = headFeatIDList1[i]
#             footFeatID = footFeatIDList1[i]
#             if (angle < 45) or (angle > 135):
#                 idListList1.append([headFeatID, footFeatID])
#                 headFeatIDList2.append(headFeatID)
#                 footFeatIDList2.append(footFeatID)
#             i += 1
#
#         ### merge feature pairs if they share a common feature
#         idListList2 = (
#             []
#         )  # each element list contains ids of connected features e.g. [[1, 2, 3, 5], [4, 9], [6, 13]],
#         i = 0
#         headIDArray = np.asarray(headFeatIDList2)
#         footIDArray = np.asarray(footFeatIDList2)
#         while i < len(idListList1):
#             tempList = []
#             ids = idListList1[i]
#             headID = headFeatIDList2[i]
#             footID = footFeatIDList2[i]
#
#             if (
#                 headFeatIDList2.count(headID) > 1
#             ):  # if multiple pairs share the same headID (e.g. [1,2],[1,3]), select the feature pair with the minimum intersecting angle
#                 indices = np.where(headIDArray == headID)[0]
#                 angleListTemp = []
#                 for index in indices:
#                     angle = angleList[index]
#                     angleListTemp.append(angle)
#                 ids1 = idListList1[angleList.index(min(angleListTemp))]
#                 if ids1 not in idListList2:
#                     idListList2.append(ids1)
#             elif (
#                 footFeatIDList2.count(footID) > 1
#             ):  # if multiple pairs share the same footID (e.g. [2,1],[3,1]), select the feature pair with the minimum intersecting angle
#                 indices = np.where(footIDArray == footID)[0]
#                 angleListTemp = []
#                 for index in indices:
#                     angle = angleList[index]
#                     angleListTemp.append(angle)
#                 ids1 = idListList1[angleList.index(min(angleListTemp))]
#                 if ids1 not in idListList2:
#                     idListList2.append(ids1)
#             elif (
#                 headID in footFeatIDList2
#             ):  # if two pairs (e.g., [2,1],[5,2]), indicates the three features are connected, so add both pairs
#                 ids1 = idListList1[footFeatIDList2.index(headID)]
#                 tempList.append(ids)
#                 tempList.append(ids1)
#                 tempList = self.getUnique(tempList)
#                 if tempList not in idListList2:
#                     idListList2.append(tempList)
#             elif (
#                 footID in headFeatIDList2
#             ):  # if two pairs (e.g., [1,2],[2,5]), indicates the three features are connected, so add both pairs
#                 ids1 = idListList1[headFeatIDList2.index(footID)]
#                 tempList.append(ids)
#                 tempList.append(ids1)
#                 tempList = self.getUnique(tempList)
#                 if tempList not in idListList2:
#                     idListList2.append(tempList)
#             else:  # otherwise, just keep the pair
#                 idListList2.append(ids)
#             i += 1
#
#         cursor = arcpy.SearchCursor(inFeat)
#         featIDList = []
#         for row in cursor:
#             featID = row.getValue("featID")
#             featIDList.append(featID)
#         del cursor, row
#
#         ### assign a same featID to features to be connected
#         featIDNewList = featIDList.copy()
#         for tempList in idListList2:
#             indexList = []
#             featureIDList = []
#             for idv in tempList:
#                 index = featIDList.index(idv)
#                 featureID = featIDList[index]
#                 indexList.append(index)
#                 featureIDList.append(featureID)
#             for index in indexList:
#                 featIDNewList[index] = featureIDList[0]
#
#         return featIDNewList


def merge_features(
    feature: str, dissolve_feature: str, dissolve_feature1: str, dissolve_feature2: str
) -> int:
    """
    Counts of features sharing borders and merges input features sharing points.

    :param feature:
        Input features.

    :param dissolve_feature:
        Input features after merging features sharing borders and points.

    :param dissolve_feature1:
        Input features after merging only features sharing borders.

    :param dissolve_feature2:
        Output features after merging only features sharing points.

    :return:
        Number of features sharing borders.
    """
    # TODO;
    # apart from appending, this list isn't used for any purpose
    # it is superfluous and should be removed
    items: list[str] = []

    tmp_layer: str = "tempLyr"
    select_feat1: str = "selectFeat1"
    select_feat2: str = "selectFeat2"
    select_feat3: str = "selectFeat3"
    select_feat3_1: str = "selectFeat3_1"

    erased_feat: str = "erasedFeat"
    erased_feat1: str = "easedFeat1"

    # select individual input features that share points and those stand-alone features
    arcpy.MakeFeatureLayer_management(feature, tmp_layer)
    arcpy.SelectLayerByLocation_management(
        tmp_layer, "ARE_IDENTICAL_TO", dissolve_feature1
    )
    items.append(select_feat1)
    arcpy.CopyFeatures_management(tmp_layer, select_feat1)
    arcpy.AddMessage(f"{select_feat1} done")

    # select dissolved features sharing points and stand-alone features
    arcpy.MakeFeatureLayer_management(dissolve_feature, tmp_layer)
    arcpy.SelectLayerByLocation_management(tmp_layer, "intersect", select_feat1)
    items.append(select_feat2)
    arcpy.CopyFeatures_management(tmp_layer, select_feat2)
    arcpy.AddMessage(f"{select_feat2} done")

    # select individual input features sharing borders
    arcpy.MakeFeatureLayer_management(feature, tmp_layer)
    arcpy.SelectLayerByLocation_management(
        tmp_layer,
        "ARE_IDENTICAL_TO",
        dissolve_feature1,
        invert_spatial_relationship="INVERT",
    )
    items.append(select_feat3)
    arcpy.CopyFeatures_management(tmp_layer, select_feat3)
    arcpy.AddMessage(f"{select_feat3} done")

    count = int(arcpy.GetCount_management(select_feat3).getOutput(0))

    # erase features that share borders from selected dissolved features sharing points
    # and stand-alone features
    items.append(erased_feat)
    arcpy.Erase_analysis(select_feat2, select_feat3, erased_feat)

    # select individual input features sharing both borders and points
    arcpy.MakeFeatureLayer_management(select_feat3, tmp_layer)
    arcpy.SelectLayerByLocation_management(
        tmp_layer,
        "BOUNDARY_TOUCHES",
        erased_feat,
        invert_spatial_relationship="INVERT",
    )
    items.append(select_feat3_1)
    arcpy.CopyFeatures_management(tmp_layer, select_feat3_1)
    arcpy.AddMessage(f"{select_feat3_1} done")

    # erase features that share borders from dissolved features sharing points
    # and stand-alone features
    items.append(erased_feat1)
    arcpy.Erase_analysis(dissolve_feature, select_feat3_1, erased_feat1)

    # merge features in the erased and fourth sets
    # which results in output features after merging features sharing points
    in_features = [erased_feat1, select_feat3_1]
    arcpy.Merge_management(in_features, dissolve_feature2)
    items.append(tmp_layer)
    # TODO; if the deletion is commented out, why collect the list?
    # self.deleteDataItems(itemList)

    return count


def _add_field(
    in_feature: str,
    field_name: str,
    field_type: str,
    field_precision: int | None = None,
    field_scale: int | None = None,
    field_length: int | None = None,
    field_alias: str | None = None,
    field_is_nullable: str | None = None,
    field_is_required: str | None = None,
    field_domain: str | None = None,
    field_names: list[str] | None = None,
) -> None:
    """
    Wrapper for ArcGIS arcpy.AddField_management.
    """
    if field_names is None:
        fields = arcpy.ListFields(in_feature)
        field_names = [f.name for f in fields]

    if field_name in field_names:
        arcpy.AddMessage(f"{field_name} exists and will be recalculated")
    else:
        arcpy.AddField_management(
            in_feature,
            field_name,
            field_type,
            field_precision=field_precision,
            field_scale=field_scale,
            field_length=field_length,
            field_alias=field_alias,
            field_is_nullable=field_is_nullable,
            field_is_required=field_is_required,
            field_domain=field_domain,
        )


def _calculate_join_field(
    in_feature: str,
    join_feature: str,
    field_name: str,
    in_id: str,
    join_id: str,
    expression: str,
) -> None:
    """
    Wrapper for ArcGIS to calculate a newly created field
    (or overwrite and existing field) from a joined feature class.
    """
    layer_name: str = "tempLyr"

    arcpy.MakeFeatureLayer_management(in_feature, layer_name)
    arcpy.AddJoin_management(layer_name, in_id, join_feature, join_id, "KEEP_ALL")
    arcpy.CalculateField_management(layer_name, field_name, expression, PY_VERSION)
    arcpy.RemoveJoin_management(layer_name, join_feature)
    arcpy.Delete_management(layer_name)


def add_double_field(
    in_feature: str,
    join_feature: str,
    field_name: str,
    in_id: str,
    join_id: str,
    expression: str,
    field_precision: int = 15,
    field_scale: int = 6,
) -> None:
    """
    Adds and calculates a field of type DOUBLE from a joined feature class.

    :param in_feature:
         Input feature class or table.

    :param join_feature:
         Feature class or table to be joined with the input feature class
         or table.

    :param field_name:
        The field name from the input feature class or table to be calculated
        from the join_feature class or table.

    :param in_id:
        The field name for the input feature class or table containing the unique IDs.

    :param join_id:
        The field name for the join feature class or table containing the unique IDs.

    :param expression:
        The logical expression used to calculate the field.

    :param field_precision:
        The number of digits that can be stored in the field.

    :param field_scale:
        The number of decimal places stored in a field.
    """
    _add_field(
        in_feature,
        field_name,
        field_type="DOUBLE",
        field_precision=field_precision,
        field_scale=field_scale,
    )

    _calculate_join_field(
        in_feature, join_feature, field_name, in_id, join_id, expression
    )

    arcpy.AddMessage(f"{field_name} added and calculated")


def add_long_field(
    in_feature: str,
    join_feature: str,
    field_name: str,
    in_id: str,
    join_id: str,
    expression: str,
    field_precision: int = 15,
) -> None:
    """
    Adds and calculates a field of type LONG from a joined feature class.

    :param in_feature:
         Input feature class or table.

    :param join_feature:
         Feature class or table to be joined with the input feature class
         or table.

    :param field_name:
        The field name from the input feature class or table to be calculated
        from the join_feature class or table.

    :param in_id:
        The field name for the input feature class or table containing the unique IDs.

    :param join_id:
        The field name for the join feature class or table containing the unique IDs.

    :param expression:
        The logical expression used to calculate the field.

    :param field_precision:
        The number of digits that can be stored in the field.
    """
    _add_field(
        in_feature, field_name, field_type="LONG", field_precision=field_precision
    )

    _calculate_join_field(
        in_feature, join_feature, field_name, in_id, join_id, expression
    )

    arcpy.AddMessage(f"{field_name} added and calculated")


def add_text_field(
    in_feature: str,
    join_feature: str,
    field_name: str,
    in_id: str,
    join_id: str,
    expression: str,
    field_length: int = 10,
) -> None:
    """
    Adds and calculates a field of type TEXT from a joined feature class.

    :param in_feature:
         Input feature class or table.

    :param join_feature:
         Feature class or table to be joined with the input feature class
         or table.

    :param field_name:
        The field name from the input feature class or table to be calculated
        from the join_feature class or table.

    :param in_id:
        The field name for the input feature class or table containing the unique IDs.

    :param join_id:
        The field name for the join feature class or table containing the unique IDs.

    :param expression:
        The logical expression used to calculate the field.

    :param field_length:
        The number of characters that can be stored in the field.
    """
    _add_field(in_feature, field_name, field_type="TEXT", field_length=field_length)

    _calculate_join_field(
        in_feature, join_feature, field_name, in_id, join_id, expression
    )

    arcpy.AddMessage(f"{field_name} added and calculated")


def duplicates(data: list[str | int]) -> list[str | int]:
    """
    Find the duplicated elements.

    :param data:
        A list of hashable entries.
    """
    # dupes = list({x for x in data if data.count(x) > 1})  # O(n**2) slow
    seen = set()
    dupes = [
        x for x in data if x in seen or seen.add(x)
    ]  # type:ignore[func-returns-value]  # noqa: E501  # pylint: disable=line-too-long

    return dupes


def do_links1(
    in_link_feat: str,
    out_link_feat1: str,
    out_link_feat2: str,
    dist_threshold: str,
    angle_threshold: str,
    dist_weight: float,
    angle_weight: float,
    link_direction: str,
) -> None:
    """
    Selects two subssets from the input link features.

    :param in_link_feat:
        Input link feature class obtained from the GenerateOriginDestinationLinks ArcGIS tool.

    :param out_link_feat1:
        Output link featureclass after the first selection.

    :param out_link_feat2:
        Output link featureclass after the second selection.

    :param dist_threshold:
        Threshold value for distancebetween two nearby features.

    :param angle_threshold:
        Threshold value for the intersecting angle between two nearby features.

    :param dist_weight:
        Weight assigned to distance, used to calculate a combined metric
        from the distance and angle metrics.

    :param angle_weigth:
        Weight assigned to angle, used to calculate a combined metric
        from the distance and angle metrics.

    :param link_direction:
        A string indicating the link direction to be processed.

    :return:
        None.
    """
    # notes:
    # the string code blocks haven't been declared using nested triple quotes
    # as editors were having coniptions in displaying colour syntax
    # in edition, they weren't the easiest to read as the identations differed
    # from the function they were declared within

    field_precision: int = 15
    field_scale: int = 6

    fields = arcpy.ListFields(in_link_feat)
    field_names = [f.name for f in fields]

    # add and calculate a number of fields
    field_name = "tempID"
    _add_field(
        in_link_feat,
        field_name,
        field_type="LONG",
        field_precision=field_precision,
        field_names=field_names,
    )

    expression: str = "!OBJECTID!"
    arcpy.CalculateField_management(in_link_feat, field_name, expression, PY_VERSION)

    # id ratio
    if link_direction != "FH":
        field_name = "idRatio"
        _add_field(
            in_link_feat,
            field_name,
            field_type="DOUBLE",
            field_precision=field_precision,
            field_scale=field_scale,
            field_names=field_names,
        )
        expression = "!ORIG_FID! / !DEST_FID!"
        arcpy.CalculateField_management(
            in_link_feat, field_name, expression, PY_VERSION
        )

    # angle diff
    field_name = "angle_diff"
    _add_field(
        in_link_feat,
        field_name,
        field_type="DOUBLE",
        field_precision=field_precision,
        field_scale=field_scale,
        field_names=field_names,
    )
    expression = "get_angle(abs(!angle1! - !angle2!))"
    code_block = (
        "def get_angle(in_angle):\n"
        "    result = in_angle\n"
        "    if in_angle > 90:\n"
        "        result = 180 - in_angle\n"
        "    return result"
    )
    arcpy.CalculateField_management(
        in_link_feat, field_name, expression, PY_VERSION, code_block
    )

    # X diff
    field_name = "X_diff"
    _add_field(
        in_link_feat,
        field_name,
        field_type="DOUBLE",
        field_precision=field_precision,
        field_scale=field_scale,
        field_names=field_names,
    )
    expression = "!ORIG_X! - !DEST_X!"
    arcpy.CalculateField_management(in_link_feat, field_name, expression, PY_VERSION)

    # Y diff
    field_name = "Y_diff"
    _add_field(
        in_link_feat,
        field_name,
        field_type="DOUBLE",
        field_precision=field_precision,
        field_scale=field_scale,
        field_names=field_names,
    )
    expression = "!ORIG_Y! - !DEST_Y!"
    arcpy.CalculateField_management(in_link_feat, field_name, expression, PY_VERSION)

    # link angle
    field_name = "link_angle"
    _add_field(
        in_link_feat,
        field_name,
        field_type="DOUBLE",
        field_precision=field_precision,
        field_scale=field_scale,
        field_names=field_names,
    )
    expression = "get_angle(!X_diff!,!Y_diff!)"
    code_block = (
        "def get_angle(x, y)\n"
        "    if y == 0:\n"
        "        result = 90\n"
        "    else:\n"
        "        angle = math.degrees(math.atan(x/y))\n"
        "        if angle < 0:\n"
        "            result = 180 + angle\n"
        "        else:\n"
        "            result = angle\n"
        "    return result"
    )
    arcpy.CalculateField_management(
        in_link_feat, field_name, expression, PY_VERSION, code_block
    )

    # link angle diff
    field_name = "link_angle_diff"
    _add_field(
        in_link_feat,
        field_name,
        field_type="DOUBLE",
        field_precision=field_precision,
        field_scale=field_scale,
        field_names=field_names,
    )
    expression = "(get_angle(abs(!angle1! - !link_angle!)) + get_angle(abs(!angle2! - !link_angle!))) / 2"
    code_block = (
        "def get_angle(in_angle):\n"
        "    result = in_angle\n"
        "    if in_angle > 90:\n"
        "        result = 180 - in_angle\n"
        "    return result"
    )
    arcpy.CalculateField_management(in_link_feat, field_name, expression, PY_VERSION, code_block)
    arcpy.AddMessage("fields added and calculated")
