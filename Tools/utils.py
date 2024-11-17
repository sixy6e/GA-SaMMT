from pathlib import Path
from typing import Any
import numpy
import pandas
from pandas.core.common import flatten

import arcpy
from arcpy import sa

PY_VERSION: str = "PYTHON_9.3"  # is this really required by arc???

# TODO; relook at the list[tuple[list[Any], list[Any]]] vars, as they're probably
#       list[tuple[Any, Any]] instead


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
    # TODO: change relevant string inputs to float

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
    arcpy.CalculateField_management(
        in_link_feat, field_name, expression, PY_VERSION, code_block
    )
    arcpy.AddMessage("fields added and calculated")

    # select a subset, removing self-links (e.g., from S point of a feature to the N point of the same feature, indicated by 'temp == 1')
    # removing links with angle_diff larger than the angle threshold
    link_temp_feat = "linkTempFeat"
    if link_direction == "FH":
        where_clause = f"angle_diff < {angle_threshold}"
    else:
        where_clause = "(idRatio <> 1) And (angle_diff < {angle_threshold})"
    arcpy.Select_analysis(in_link_feat, link_temp_feat, where_clause)

    # further select from the above subset based on the speficied criteria
    # for the link direction
    in_feat_count = int(arcpy.GetCount_management(link_temp_feat).getOutput(0))
    # inFeatCount = 0 indicates that there is not any feature satsifying the
    # criterion specified (angle_diff < angleThreshold) for the link direction.

    link_temp_feat1 = "linkTempFeat1"

    if in_feat_count > 0:
        lat = float(angle_threshold) + 20.0
        dt = float(dist_threshold) * 0.3
        dist_t1 = 0.2 * float(dist_threshold)
        dist_t2 = -0.2 * float(dist_threshold)

        # python-3.10 has a 'match/case' switch which would be better here
        if link_direction == "SN":
            # two "Or" conditions:
            # 1. the northern feature is at some distance
            #    north of the southern feature (Y_diff attribute) and the two
            #    features have similar orientations
            #    (within a threshold)(link_angle_diff attribute)
            # 2. the northern and southern features are close together in both
            #    the north-south direction (Y_diff attribute) and
            #    link direction (LINK_DIST attribute)
            # C1 | C2
            condition1 = f"((Y_diff > {dist_t1}) And (link_angle_diff < {lat}))"
            condition2 = f"((Y_diff < {dist_t1}) And (Y_diff > {dist_t2}) And (LINK_DIST < {dt}))"  # noqa: E501  # pylint: disable=line-too-long
            where_clause = f"{condition1} Or {condition2}"
        elif link_direction == "NS":
            # two "Or" conditions:
            # 1. the southern feature is at some distance south of the
            #    northern feature (Y_diff attribute) and the two features have
            #    similar orientations
            #    (within a threshold) (link_angle_diff attribute)
            # 2. the northern and southern features are close together in
            #    both the north-south direction (Y_diff attribute) and
            #    link direction (LINK_DIST attribute)
            # C1 | C2
            condition1 = f"((Y_diff < {dist_t2}) And (link_angle_diff < {lat}))"
            condition2 = f"((Y_diff < {dist_t1}) And (Y_diff > {dist_t2}) And (LINK_DIST < {dt}))"  # noqa: E501  # pylint: disable=line-too-long
            where_clause = f"{condition1} Or {condition2}"
        elif link_direction == "WE":
            # two "Or" conditions:
            # 1. the western feature is at some distance west of the
            #    eastern feature (X_diff attribute) and the two features have
            #    similar orientations (within a threshold)
            # 2. the western and eastern features are close together in both
            #    the east-west direction (X_diff attribute) and link direction
            # C1 | C2
            condition1 = f"((X_diff > {dist_t1}) And (link_angle_diff < {lat}))"
            condition2 = f"((X_diff < {dist_t1}) And (X_diff > {dist_t2}) And (LINK_DIST < {dt}))"  # noqa: E501  # pylint: disable=line-too-long
            where_clause = f"{condition1} Or {condition2}"
        elif link_direction == "EW":
            # two "Or" conditions:
            # 1. the eastern feature is at some distance east of the
            #    western feature (X_diff attribute) and the two features
            #    have similar orientations (within a threshold)
            # 2. the western and eastern features are close together in both
            #    the east-west direction (X_diff attribute) and link direction
            # C1 | C2
            condition1 = f"((X_diff < {dist_t2}) And (link_angle_diff < {lat}))"
            condition2 = f"((X_diff < {dist_t1}) And (X_diff > {dist_t2}) And (LINK_DIST < {dt}))"  # noqa: E501  # pylint: disable=line-too-long
            where_clause = f"{condition1} Or {condition2}"
        elif link_direction == "EN":
            # several "And" conditons:
            # 1. the orientation of the eastern feature (angle1 attribute)
            #    must be 90-135
            # 2. the orientation of the northern feature (angle2 attribute)
            #    must be 135-180
            # 3. a complex "Or" conditon:
            #    a) the eastern feature and the northern feature must be at
            #       some distant away from each other in both
            #       N-S (Y_diff attribute) and E-W (X_diff attribute) directions
            #       and the two features have similar orientations
            #       (within a threshold)
            #    b) the eastern feature and the northern feature must be close
            #       in link direction and also close in either the
            #       N-S or E-W direction
            # C1 & [{(C2 | C3) & C4} | C5]
            condition1 = f"(angle1 >= 90) And (angle1 <= 135) And (angle2 >= 135)"  # noqa: E501  # pylint: disable=line-too-long
            condition2 = f"((Y_diff < {dist_t1}) And (Y_diff > {dist_t2}))"
            condition3 = f"((X_diff < {dist_t1}) And (X_diff > {dist_t2}))"
            condition4 = f"(link_dist < {dt})"
            condition5 = f"((Y_diff > {dist_t1}) And (X_diff < {dist_t2}) And (link_angle_diff < {lat}))"  # noqa: E501  # pylint: disable=line-too-long
            where_clause = f"{condition1} And ((({condition2} Or {condition3}) And {condition4}) Or {condition5})"  # noqa: E501  # pylint: disable=line-too-long
        elif link_direction == "NE":
            # several "And" conditons:
            # 1. the orientation of the northern feature (angle1 attribute)
            #    must be 135-180; and 2. the orientation of the eastern
            #    feature (angle1 attribute) must be 135-180
            # 3. a complex "Or" conditon:
            #    a) the northern feature and the eastern feature must be at
            #       some distant away from each other in both
            #       N-S (Y_diff attribute) and E-W (X_diff attribute) directions
            #       and the two features have similar orientations
            #       (within a threshold)
            #    b) the eastern feature and the northern feature must be close
            #       in link direction and also close in either the
            #       N-S or E-W direction
            # C1 & [{(C2 | C3) & C4} | C5]
            condition1 = f"(angle2 >= 90) And (angle2 <= 135) and (angle1 >= 135)"
            condition2 = f"((Y_diff < {dist_t1}) And (Y_diff > {dist_t2}))"
            condition3 = f"((X_diff < {dist_t1}) And (X_diff > {dist_t2}))"
            condition4 = f"(link_dist < {dt})"
            condition5 = f"((Y_diff < {dist_t2}) And (X_diff > {dist_t1}) And (link_angle_diff < {lat}))"  # noqa: E501  # pylint: disable=line-too-long
            where_clause = f"{condition1} And ((({condition2} Or {condition3}) And {condition4}) Or {condition5})"  # noqa: E501  # pylint: disable=line-too-long
        elif link_direction == "SW":
            # several "And" conditons:
            # 1. the orientation of the southern feature must be 135-180
            # 2. the orientation of the western feature must be 90-135
            # 3. a complex "Or" conditon:
            #    a) the southern feature and the western feature must be at
            #       some distant away from each other in both N-S and
            #       E-W directions and the two features have similar
            #       orientations (within a threshold)
            # b) the southern feature and the western feature must be close
            #    in link direction and also close in either the
            #    N-S or E-W direction
            # C1 & [{(C2 | C3) & C4} | C5]
            condition1 = f"(angle1 >= 135) And (angle2 >=90) And (angle2 <= 135)"
            condition2 = f"((Y_diff < {dist_t1}) And (Y_diff > {dist_t2}))"
            condition3 = f"((X_diff < {dist_t1}) And (X_diff > {dist_t2}))"
            condition4 = f"(link_dist < {dt})"
            condition5 = f"((Y_diff > {dist_t1}) And (X_diff < {dist_t2}) And (link_angle_diff < {lat}))"
            where_clause = f"{condition1} And ((({condition2} Or {condition3}) And {condition4}) Or {condition5})"  # noqa: E501  # pylint: disable=line-too-long
        elif link_direction == "WS":
            # several "And" conditons:
            # 1. the orientation of the western feature must be 90-135
            # 2. the orientation of the southern feature must be 135-180
            # 3. a complex "Or" conditon:
            #    a) the western feature and the southern feature must be at
            #       some distant away from each other in both N-S and E-W
            #       directions and the two features have similar orientations
            #       (within a threshold)
            #    b) the southern feature and the western feature must be close
            #       in link direction and also close in either the
            #       N-S or E-W direction
            # C1 & [{(C2 | C3) & C4} | C5]
            condition1 = f"(angle2 = 135) And (angle1 >= 90) And (angle1 <= 135)"
            condition2 = f"((Y_diff < {dist_t1}) And (Y_diff > {dist_t2}))"
            condition3 = f"((X_diff < {dist_t1}) And (X_diff > {dist_t2}))"
            condition4 = f"(link_dist < {dt})"
            condition5 = f"((Y_diff < {dist_t2}) And (X_diff > {dist_t1}) And (link_angle_diff < {lat}))"
            where_clause = f"{condition1} And ((({condition2} Or {condition3}) And {condition4}) Or {condition5})"  # noqa: E501  # pylint: disable=line-too-long
        elif link_direction == "SE":
            # several "And" conditons:
            # 1. the orientation of the southern feature must be 0-45
            # 2. the orientation of the eastern feature must be 45-90
            # 3. a complex "Or" conditon:
            #    a) the southern feature and the eastern feature must be at
            #       some distant away from each other in both
            #       N-S and E-W directions and the two features have similar
            #       orientations (within a threshold)
            #    b) the southern feature and the eastern feature must be close
            #       in link direction and also close in either the
            #       N-S or E-W direction
            # C1 & [{(C2 | C3) & C4} | C5]
            condition1 = f"(angle1 <= 45) And (angle2 >= 45) And (angle2 <= 90)"
            condition2 = f"((Y_diff < {dist_t1}) And (Y_diff > {dist_t2}))"
            condition3 = f"((X_diff < {dist_t1}) And (X_diff > {dist_t2}))"
            condition4 = f"(link_dist < {dt})"
            condition5 = f"((Y_diff > {dist_t1}) And (X_diff > {dist_t1}) And (link_angle_diff < {lat}))"
            where_clause = f"{condition1} And ((({condition2} Or {condition3}) And {condition4}) Or {condition5})"
        elif link_direction == "ES":
            # several "And" conditons:
            # 1. the orientation of the eastern feature must be 45-90
            # 2. the orientation of the eastern feature must be 0-45
            # 3. a complex "Or" conditon:
            #    a) the southern feature and the eastern feature must be at
            #       some distant away from each other in both
            #       N-S and E-W directions and the two features have similar
            #       orientations (within a threshold)
            #    b) the southern feature and the eastern feature must be close
            #       in link direction and also close in either the
            #       N-S or E-W direction
            # C1 & [{(C2 | C3) & C4} | C5]
            condition1 = f"(angle2 <= 45) And (angle1 >= 45) And (angle1 <= 90)"
            condition2 = f"((Y_diff < {dist_t1}) And (Y_diff > {dist_t2}))"
            condition3 = f"((X_diff < {dist_t1}) And (X_diff > {dist_t2}))"
            condition4 = f"(link_dist < {dt})"
            condition5 = f"((Y_diff < {dist_t2}) And (X_diff < {dist_t2}) And (link_angle_diff < {lat}))"
            where_clause = f"{condition1} And ((({condition2} Or {condition3}) And {condition4}) Or {condition5})"
        elif link_direction == "WN":
            # several "And" conditons:
            # 1. the orientation of the western feature must be 45-90
            # 2. the orientation of the northern feature must be 0-45
            # 3. a complex "Or" conditon:
            #    a) the western feature and the northern feature must be at
            #       some distant away from each other in both
            #       N-S and E-W directions and the two features have similar
            #       orientations (within a threshold)
            #    b) the western feature and the northern feature must be close
            #       in link direction and also close in either the
            #       N-S or E-W direction
            # C1 & [{(C2 | C3) & C4} | C5]
            condition1 = f"(angle1 >= 45) And (angle1 <= 90) And (angle2 <= 45))"
            condition2 = f"((Y_diff < {dist_t1}) And (Y_diff > {dist_t2}))"
            condition3 = f"((X_diff < {dist_t1}) And (X_diff > {dist_t2}))"
            condition4 = f"(link_dist < {dt})"
            condition5 = f"((Y_diff > {dist_t1}) And (X_diff > {dist_t1}) And (link_angle_diff < {lat}))"
            where_clause = f"{condition1} And ((({condition2} Or {condition3}) And {condition4}) Or {condition5})"
        elif link_direction == "NW":
            # several "And" conditons:
            # 1. the orientation of the northern feature must be 0-45
            # 2. the orientation of the western feature must be 45-90
            # 3. a complex "Or" conditon:
            #    a) the northern feature and the western feature must be at
            #       some distant away from each other in both
            #       N-S and E-W directions and the two features have similar
            #       orientations (within a threshold)
            #    b) the western feature and the northern feature must be close
            #       in link direction and also close in either the
            #       N-S or E-W direction
            # C1 & [{(C2 | C3) & C4} | C5]
            condition1 = f"((angle2 >= 45) And (angle2 <= 90) And (angle1 <= 45))"
            condition2 = f"((Y_diff < {dist_t1}) And (Y_diff > {dist_t2}))"
            condition3 = f"((X_diff < {dist_t1}) And (X_diff > {dist_t2}))"
            condition4 = f"(link_dist < {dt})"
            condition5 = f"((Y_diff < {dist_t2}) And (X_diff < {dist_t2}) And (link_angle_diff < {lat}))"  # noqa: E501  # pylint: disable=line-too-long
            where_clause = f"{condition1} And ((({condition2} Or {condition3}) And {condition4}) Or {condition5})"  # noqa: E501  # pylint: disable=line-too-long
        elif link_direction == "FH":
            # connect foot to head features, not longer in use
            # TODO; if no longer in use, it is better to remove or at the very
            #       least, comment this whole condition out
            # two "Or" conditions:
            # 1. the two features are close together in both
            #    north-south and east-west directions
            #    (X_diff and Y_diff attributes) and
            #    link direction (LINK_DIST attribute)
            # 2. the two features are not close in either north-south
            #    (Y_diff attribute) or east-west directions (X_diff attribute)
            #    and they have similar orientations (within a threshold)
            #    (link_angle_diff attribute).
            # ((C1 & C2) | C3) | ((C4 | C5) And C6)
            condition1 = f"(X_diff <= {dist_t1}) And (X_diff >= {dist_t2})"
            condition2 = f"(Y_diff <= {dist_t1}) And (Y_diff >= {dist_t2})"
            condition3 = f"(LINK_DIST < {dt})"
            condition4 = f"(X_diff > {dist_t1}) Or (X_diff < {dist_t2})"
            condition5 = f"(Y_diff > {dist_t2}) Or (Y_diff < {dist_t2})"  # TODO; confirm correctness # noqa: E501  # pylint: disable=line-too-long
            condition6 = f"(link_angle_diff < {lat})"
            where_clause = f"(({condition1} & {condition2}) | {condition3}) | (({condition4} | {condition5}) And {condition6})"  # noqa: E501  # pylint: disable=line-too-long

        arcpy.Select_analysis(link_temp_feat, link_temp_feat1, where_clause)
    else:
        arcpy.Copy_management(link_temp_feat, link_temp_feat1)

    arcpy.AddMessage("first selection done")

    # further selection
    in_feat_count = int(arcpy.GetCount_management(link_temp_feat1).getOutput(0))

    if in_feat_count > 0:
        # here is different between the combined option and the other two options
        # the combined option would likely generate multiple records have the
        # same [originID,destID]
        # we need to select the one with minimum distance
        cursor = arcpy.SearchCursor(link_temp_feat1)

        # TODO; the `list` appended to the variable name is superfluous
        #       scan through to ensure the name can be simplified eg temp_ids
        # TODO; once we're clear on the explicit type, change `Any` to reflect it
        temp_id_list: list[Any] = []
        origin_id_list: list[Any] = []
        dest_id_list: list[Any] = []
        dist_list: list[Any] = []
        id_list_list: list[tuple[list[Any], list[Any]]] = []

        for row in cursor:
            temp_id = row.getValue("tempID")
            origin_id = row.getValue("ORIG_FID")
            dest_id = row.getValue("DEST_FID")
            dist = row.getValue("LINK_DIST")

            # changing to tuple to be clear on the dimensionality
            id_list = (
                origin_id,
                dest_id,
            )
            temp_id_list.append(temp_id)
            origin_id_list.append(origin_id)
            dest_id_list.append(dest_id)
            dist_list.append(dist)
            id_list_list.append(id_list)

        leng1 = len(id_list_list)
        id_list_list1 = unique_2D(id_list_list)
        leng2 = len(id_list_list1)

        if leng1 > leng2:
            # Mid points and Most distant points option
            # (ie. the combined option) selected
            temp_id_list1 = []
            ids_array = numpy.asarray(id_list_list)

            for id_list in id_list_list:
                indices = numpy.where(
                    (ids_array[:, 0] == id_list[0]) & (ids_array[:, 1] == id_list[1])
                )[0]

                index_list = indices.tolist()
                dist_list_temp = []
                for index in indices:
                    dist_list_temp.append(dist_list[index])

                # select the index with minimum distance
                j = index_list[dist_list_temp.index(min(dist_list_temp))]
                temp_id_list1.append(temp_id_list[j])

            # select subset
            text = ",".join([str(i) for i in temp_id_list1])
            text = f"({text})"
            where_clause = f"tempID IN {text}"
            arcpy.Select_analysis(link_temp_feat1, out_link_feat1, where_clause)
        else:
            # one of the other two options selected
            arcpy.Copy_management(link_temp_feat1, out_link_feat1)
    else:
        arcpy.Copy_management(link_temp_feat1, out_link_feat1)

    arcpy.AddMessage("second selection done")

    # further selection
    in_feat_count = int(arcpy.GetCount_management(out_link_feat1).getOutput(0))

    if in_feat_count > 0:
        # doing the third selection
        # if multiple records have the same ORIG_FID or DEST_ID
        # (eg., between [1,3] and [1,4] or between [1,10] and [2,10]),
        # just select the one with min combination of distance and angle_diff
        cursor = arcpy.SearchCursor(out_link_feat1)

        temp_id_list: list[Any] = []
        origin_id_list: list[Any] = []
        dest_id_list: list[Any] = []
        dist_list: list[Any] = []
        angle_list: list[Any] = []

        for row in cursor:
            # TODO; it'd be cleaner to just do
            #       temp_id_list.append(row.getValue("tempID"))
            temp_id = row.getValue("tempID")
            origin_id = row.getValue("ORIG_FID")
            dest_id = row.getValue("DEST_FID")
            dist = row.getValue("LINK_DIST")
            angle = row.getValue("angle_diff")

            temp_id_list.append(temp_id)
            origin_id_list.append(origin_id)
            dest_id_list.append(dest_id)
            dist_list.append(dist)
            angle_list.append(angle)

        # in_id_list_list: list[tuple[list[Any], list[Any]]] = []
        # for i, val in enumerate(origin_id_list):
        #     in_id_list_list.append((val, dest_id_list[i]))
        in_id_list_list = list(zip(origin_id_list, dest_id_list))

        # call the doLists() function to conduct the selection
        list1, list2, list3, list4, list5 = do_lists(
            origin_id_list,
            dest_id_list,
            in_id_list_list,
            dist_list,
            angle_list,
            dist_threshold,
            angle_threshold,
            dist_weight,
            angle_weight,
        )

        # update the list
        temp_id_list1 = [in_id_list_list.index(i) for i in list3]

        # select subset
        text = ",".join([str(i) for i in temp_id_list1])
        text = f"({text})"
        where_clause = f"tempID IN {text}"
        arcpy.Select_analysis(out_link_feat1, out_link_feat2, where_clause)
    else:
        arcpy.Copy_management(out_link_feat1, out_link_feat2)

    arcpy.AddMessage("third selection done")

    arcpy.Delete_management(link_temp_feat)
    arcpy.Delete_management(link_temp_feat1)


# line 3568
def get_index(
    index: numpy.ndarray,
    distances: numpy.ndarray,
    angles: numpy.ndarray,
    dist_threshold: float,
    angle_threshold: float,
    dist_weight: float,
    angle_weight: float,
) -> int:
    """
    Return the indices based on distance and angle criteria.

    :param index:
        Initial index list.

    :param distances:
        Initial distance list.

    :param angles:
        Initial angle list.

    :param dist_threshold:
        Threshold value for distance between two nearby features.

    :param angle_threshold:
        Threshold value for the intersecting angle between two nearby features.

    :param dist_weight:
        Weight assigned to distance; used to calculate a combination metric
        from distance and angle.

    :param angle_weight:
        Weight assigned to angle; used to calculate a combination metric
        from distance and angle.
    """
    # TODO: the input lists should be arrays.
    #       that way manual looping can be avoided.
    #       pay the extra memory to perform it faster with numpy
    #       Alternatively, we force to arrays for this routine ...

    # the original code, working on lists
    # distThreshold = float(distThreshold)
    # angleThreshold = float(angleThreshold)
    # distWeight = float(distWeight)
    # angleWeight = float(angleWeight)

    # cL = []  # elements in list cL are calculated from distance and angle
    # i = 0
    # while i < len(distList):
    #     d = distList[i] / distThreshold
    #     a = angleList[i] / angleThreshold
    #     # calculate weighted average from distWeight and angleWeight
    #     c = (d * distWeight + a * angleWeight) / (distWeight + angleWeight)
    #     cL.append(c)
    #     i += 1

    # cArr = np.asarray(cL)
    # indices = np.where(cArr == np.min(cArr))[0]
    # # if multiple elements satisfying the minimum criteria, select the one with a smaller anlge
    # if len(indices) > 1:
    #     aList = []
    #     for i in indices:
    #         aList.append(angleList[i])
    #     return indexList[angleList.index(min(aList))]
    # else:
    #     return indexList[indices[0]]

    # numpy method; assumes everything is 1D
    dn = distances / dist_threshold
    an = angles / angle_threshold
    weight_sum = dist_weight + angle_weight

    # calculate weighted average from distWeight and angleWeight
    weighted = (dn * dist_weight + an * angle_weight) / weight_sum

    wh = weighted == numpy.min(weighted)

    # if multiple elements satisfying the minimum criteria,
    # select the one with a smaller angle
    indices = numpy.arange(len(weighted))
    angle_idx = angles[wh].argmin()

    idx = indices[wh][angle_idx]

    return int(index[idx])


# 3612
def do_lists(
    feat_id1_list: list[int],
    feat_id2_list: list[int],
    in_id_list_list: list[list[int]],
    dist_list: list[float],
    angle_list: list[float],
    dist_threshold: float,
    angle_threshold: float,
    dist_weight: float,
    angle_weight: float,
):
    """
    Updates ids list when multiple elements share "from" or "to" points.

    :param feat_id1_list:
        Feature IDs of the `from` points.

    :param feat_id2_list:
        Feature IDs of the `to` points.

    :param in_id_list_list:
        List of lists containing [feat_id1, feat_id2].

    :param dist_list:
        Initial distance list.

    :param angle_list:
        Initial angle list.

    :param dist_threshold:
        Threshold value for distance between two nearby features.

    :param angle_threshold:
        Threshold value for the intersecting angle between two nearby features.

    :param dist_weight:
        Weight assigned to distance; used to calculate a combination metric
        from distance and angle.

    :param angle_weight:
        Weight assigned to angle; used to calculate a combination metric
        from distance and angle.
    """
    # TODO:
    #     Much refactoring could be done here. again the reworking of lists
    #     to numpy arrays.
    #     Also, this func could contain a private func that performs the loops
    #     and returns the result, or turn this func itself to iterate once,
    #     and the caller be responsible for iterating
    out_id_list_list1: list[int] = []
    out_id_list_list2: list[int] = []
    feat_id1_list1: list[int] = []
    feat_id1_list2: list[int] = []
    feat_id2_list1: list[int] = []
    feat_id2_list2: list[int] = []
    dist_list1: list[float] = []
    dist_list2: list[float] = []
    angle_list1: list[float] = []
    angle_list2: list[float] = []

    # first round, doing features sharing featID1 (featID of the from point)
    # each element in outIDListList1 contains ids of connected features
    # e.g. [[1, 2, 3, 5], [4, 9], [6, 13]]
    for i, ids in enumerate(in_id_list_list):
        feat_id1 = feat_id1_list[i]

        # if multiple pairs share the same feat_id1
        # (e.g. [1,2],[1,3]), select the feature pair with the minimum
        # combination of intersecting angle and distance
        if feat_id1_list1.count(feat_id1) > 1:
            indices = numpy.where(numpy.asarray(feat_id1_list) == feat_id1)[0]
            angles_temp = numpy.asarray(angle_list)[indices]
            dists_temp = numpy.asarray(dist_list)[indices]
            j = get_index(
                indices,
                dists_temp,
                angles_temp,
                dist_threshold,
                angle_threshold,
                dist_weight,
                angle_weight,
            )
            ids1 = in_id_list_list[j]

            # only append ids1 if it is not already in the existing list of lists
            if ids1 not in out_id_list_list1:
                out_id_list_list1.append(ids1)

        else:  # otherwise, just keep the pair
            out_id_list_list1.append(ids)

    # update lists
    for ids in out_id_list_list1:
        i = in_id_list_list.index(ids)
        feat_id1_list1.append(feat_id1_list[i])
        feat_id2_list1.append(feat_id2_list[i])
        dist_list1.append(dist_list[i])
        angle_list1.append(angle_list[i])

    # second round, doing features sharing featID2
    # the inputs are the updated lists from the first round
    for i, ids in enumerate(out_id_list_list1):
        feat_id2 = feat_id2_list1[i]

        # if multiple pairs share the same feat_id2
        # (e.g. [3,2],[4,2]), select the feature pair with the minimum
        # combination of intersecting angle and distance
        if feat_id2_list1.count(feat_id2) > 1:
            indices = numpy.where(numpy.asarray(feat_id2_list1) == feat_id2)[0]
            angles_temp = numpy.asarray(angle_list1)[indices]
            dists_temp = numpy.asarray(dist_list1)[indices]
            j = get_index(
                indices,
                dists_temp,
                angles_temp,
                dist_threshold,
                angle_threshold,
                dist_weight,
                angle_weight,
            )
            ids1 = out_id_list_list1[j]

            # only append ids1 if it is not already in the existing list of lists
            if ids1 not in out_id_list_list2:
                out_id_list_list2.append(ids1)

        else:  # otherwise, just keep the pair
            out_id_list_list2.append(ids)

    # update lists
    for ids in out_id_list_list2:
        i = out_id_list_list1.index(ids)
        feat_id1_list2.append(feat_id1_list1[i])
        feat_id2_list2.append(feat_id2_list1[i])
        dist_list2.append(dist_list1[i])
        angle_list2.append(angle_list1[i])

    result = (
        feat_id1_list2,
        feat_id2_list2,
        out_id_list_list2,
        dist_list2,
        angle_list2,
    )

    return result


def do_lists_v2(
    feat_id1_list: list[Any],
    feat_id2_list: list[Any],
    in_id_list_list: list[list[int]],
    dist_list: list[Any],
    angle_list: list[Any],
    dist_threshold: float,
    angle_threshold: float,
    dist_weight: float,
    angle_weight: float,
):
    """
    TODO.
    """

    def update(
        feat_ids: list[Any],
        in_ids: list[list[int]],
        distances: list[Any],
        angles: list[Any],
        dist_threshold: float,
        angle_threshold: float,
        dist_weight: float,
        angle_weight: float,
    ) -> list[list[int]]:
        """Helper func private to do_lists_v2."""
        out_ids: list[list[int]] = []

        # first round, doing features sharing featID1 (featID of the from point)
        # each element in outIDListList1 contains ids of connected features
        # e.g. [[1, 2, 3, 5], [4, 9], [6, 13]]
        for i, ids in enumerate(in_ids):
            feat_id = feat_ids[i]

            # if multiple pairs share the same feat_id1
            # (e.g. [1,2],[1,3]), select the feature pair with the minimum
            # combination of intersecting angle and distance
            if feat_ids.count(feat_id) > 1:
                indices = numpy.where(numpy.asarray(feat_ids) == feat_id)[0]
                angles_temp = numpy.asarray(angles)[indices]
                dists_temp = numpy.asarray(distances)[indices]
                j = get_index(
                    indices,
                    dists_temp,
                    angles_temp,
                    dist_threshold,
                    angle_threshold,
                    dist_weight,
                    angle_weight,
                )
                ids1 = in_ids[j]

                # only append ids1 if it is not already in the existing list of lists
                if ids1 not in out_ids:
                    out_ids.append(ids1)

            else:  # otherwise, just keep the pair
                out_ids.append(ids)

        return out_ids

    # temps; first pass
    feat_ids1_list1: list[int] = []
    feat_ids2_list1: list[int] = []
    dist_list1: list[float] = []
    angle_list1: list[float] = []

    # first round, doing features sharing featID1 (featID of the from point)
    # each element in outIDListList1 contains ids of connected features
    # e.g. [[1, 2, 3, 5], [4, 9], [6, 13]]
    out_ids1 = update(
        feat_id1_list,
        in_id_list_list,
        dist_list,
        angle_list,
        dist_threshold,
        angle_threshold,
        dist_weight,
        angle_weight,
    )

    # update feature lists
    for ids in out_ids1:
        i = in_id_list_list.index(ids)
        feat_ids1_list1.append(feat_id1_list[i])
        feat_ids2_list1.append(feat_id2_list[i])
        dist_list1.append(dist_list[i])
        angle_list1.append(angle_list[i])

    # return vars; second pass
    feat_ids1_list2: list[int] = []
    feat_ids2_list2: list[int] = []
    dist_list2: list[float] = []
    angle_list2: list[float] = []

    # second round, doing features sharing featID2
    # the inputs are the updated lists from the first round
    out_ids2 = update(
        feat_ids2_list1,
        out_ids1,
        dist_list1,
        angle_list1,
        dist_threshold,
        angle_threshold,
        dist_weight,
        angle_weight,
    )

    # update feature lists
    for ids in out_ids2:
        i = out_ids1.index(ids)
        feat_ids1_list2.append(feat_ids1_list1[i])
        feat_ids2_list2.append(feat_ids2_list1[i])
        dist_list2.append(dist_list1[i])
        angle_list2.append(angle_list1[i])

    result = (
        feat_ids1_list2,
        feat_ids2_list2,
        out_ids2,
        dist_list2,
        angle_list2,
    )

    return result


def do_lists1(
    feat_id1_list: list[int],
    feat_id2_list: list[int],
    in_id_list_list: list[list[int]],
    dist_list: list[float],
    angle_list: list[float],
    dist_threshold: float,
    angle_threshold: float,
    dist_weight: float,
    angle_weight: float,
) -> list[list[int]]:
    """
    Further updates ids list when multiple elements connected through sharing
    `from` and `to` points.
    Must be called after do_lists()
    (e.g., using the outputs from do_lists() as inputs)

    :param feat_id1_list:
        Feature IDs of the `from` points.

    :param feat_id2_list:
        Feature IDs of the `to` points.

    :param in_id_list_list:
        List of tuples containing (feat_id1, feat_id2).

    :param dist_list:
        Initial distance list.

    :param angle_list:
        Initial angle list.

    :param dist_threshold:
        Threshold value for distance between two nearby features.

    :param angle_threshold:
        Threshold value for the intersecting angle between two nearby features.

    :param dist_weight:
        Weight assigned to distance; used to calculate a combination metric
        from distance and angle.

    :param angle_weight:
        Weight assigned to angle; used to calculate a combination metric
        from distance and angle.
    """
    out_list_list: list[list[int]] = []

    # np arrays
    # TODO; look to work directly with np arrays rather than back and forth conversion
    feat_ids1 = numpy.asarray(feat_id1_list)
    feat_ids2 = numpy.asarray(feat_id2_list)
    angles = numpy.asarray(angle_list)
    distances = numpy.asarray(dist_list)

    for i, ids in enumerate(in_id_list_list):
        temp_list: list[list[int]] = []
        feat_id1 = feat_id1_list[i]
        feat_id2 = feat_id2_list[i]

        if feat_id2_list.count(feat_id1) > 0:
            # if two pairs (e.g., [2,1],[5,2]), indicates the three features
            # are connected, so add both pair
            indices = numpy.where(feat_ids2 == feat_id1)[0]
            angles_temp = angles[indices]
            dists_temp = distances[indices]

            j = get_index(
                indices,
                dists_temp,
                angles_temp,
                dist_threshold,
                angle_threshold,
                dist_weight,
                angle_weight,
            )
            ids1 = in_id_list_list[j]

            temp_list.append(ids)
            temp_list.append(ids1)

            temp_list = unique(temp_list)

            if temp_list not in out_list_list:
                out_list_list.append(temp_list)
        elif feat_id1_list.count(feat_id2) > 0:
            # if two pairs (e.g., [1,2],[2,5]), indicates the three features
            # are connected, so add both pairs
            indices = numpy.where(feat_ids1 == feat_id1)[0]
            angles_temp = angles[indices]
            dists_temp = distances[indices]

            j = get_index(
                indices,
                dists_temp,
                angles_temp,
                dist_threshold,
                angle_threshold,
                dist_weight,
                angle_weight,
            )
            ids1 = in_id_list_list[j]

            temp_list.append(ids)
            temp_list.append(ids1)

            temp_list = unique(temp_list)

            if temp_list not in out_list_list:
                out_list_list.append(temp_list)
        else:
            # otherwise, just keep the pair
            out_list_list.append(ids)

    return out_list_list


# 3844
def merge_list(data: list[list[int]]):
    """
    Merges common elements from multiple lists into one list.

    :param data:
        List of lists containing feature IDs eg:
        [[1, 2, 3, 5], [4, 9], [6, 13]]
    """
    # each element list contains ids of connected features e.g.
    # [[1, 2, 3, 5], [4, 9], [6, 13]],
    result: list[list[int]] = []

    data_cp = data.copy()

    # each loop remove an element list from inList, until none left
    # at the same time, build a new list (of list)
    # TODO: the issue that jumps out in this approach is that if there are
    #       are no common elements, this while loop could run forever.
    #       Confirm that this would never be the case
    while data:
        record = data[0].copy()

        # compare the element with all elements in the list one by one
        for item in data_cp:
            # find the number of common elements bewtween the two lists
            length = calculate_common(record, item)
            if length:
                data.remove(item)
                for el in item:
                    record.append(el)

                # unique values within a list
                record = unique(record)

        unq = unique(list(flatten(record)))
        result.append(unq)
        data_cp = data.copy()

    return result


def create_lists(linked_features: list[str]):
    """
    Wrapper around ArcGIS to read the records for each feature into
    Python and return lists for the following attributes:
        * angle_diff
        * LINK_DIST
        * featID1
        * featID2
    """
    feat_ids1: list[int] = []
    feat_ids2: list[int] = []
    feat_ids: list[list[int]] = []
    angles: list[float] = []
    distances: list[float] = []

    for link_feat in linked_features:
        feat_count = int(arcpy.GetCount_management(link_feat).getOutput(0))
        arcpy.AddMessage(f"{link_feat} has {feat_count} features.")

        if feat_count:
            cursor = arcpy.SearchCursor(link_feat)

            for row in cursor:
                angles.append(row.getValue("angle_diff"))
                distances.append(row.getValue("LINK_DIST"))

                feat_id1 = row.getValue("featID1")
                feat_id2 = row.getValue("featID2")
                feat_ids1.append(feat_id1)
                feat_ids2.append(feat_id2)
                feat_ids.append([feat_id1, feat_id2])

    return feat_ids1, feat_ids2, feat_ids, distances, angles


# TODO; the `old` label in the function inidicates its an older version.
#       confirm that this function is no longer required
# 3904
def direction_points_old(
    in_feat_class: str, mbr_line_class: str, temp_folder: Path, out_point_feat: Path
) -> None:
    """
    Generate direction point features from the input features and the bounding
    rectangle features.
    This one would potentially resulted in a small number of incorrect points,
    e.g. two points on different features may be on the same line.

    :param in_feat_class:
        Represents the polygons to be connected;
        input Bathymetric High Features.

    :param mbr_line_class:
        A subset of lines from the the minimum bounding rectangles
        of in_feat_class. For each feature that are two lines,
        either N and S or E and W.

    :param temp_folder:
        A filepath to a location that will store the temporary files.

    :param out_point_feat:
        Output direction point features.

    :notes:
        The label `class` isn't referring to a Python class,
        but a classification.
    """
    in_feat_vertices = "inFeatVertices"

    # convert each input feature to points;
    arcpy.FeatureVerticesToPoints_management(in_feat_class, in_feat_vertices, "ALL")

    layer1 = "layer1"
    arcpy.MakeFeatureLayer_management(in_feat_vertices, layer1)

    # select those points that are on the selected bounding rectangle
    # boundaries (N and S or E and W)
    arcpy.SelectLayerByLocation_management(layer1, "INTERSECT", mbr_line_class)
    selected_points = "selectedPoints1"
    arcpy.CopyFeatures_management(layer1, selected_points)

    # spatial join to append attributes from mbr_line_class
    join_feat = "joinFeat"
    arcpy.SpatialJoin_analysis(selected_points, mbr_line_class, join_feat)

    # only need these attributes, with additional
    # POINT_X and POINT_Y attributes added
    fields_to_keep = ["featID", "rectangle_Orientation", "direction"]
    fields_to_delete = []
    fields = arcpy.ListFields(join_feat)

    for field in fields:
        if not field.required:
            if field.name not in fields_to_keep:
                fields_to_delete.append(field.name)

    arcpy.DeleteField_management(join_feat, fields_to_delete)
    arcpy.AddXY_management(join_feat)

    # delete schema.ini which may contains incorrect data types
    schema_pth = temp_folder.joinpath("schema.ini")
    if schema_pth.exists():
        schema_pth.unlink()

    # export the attributes to a csv file
    csv_pth = temp_folder.joinpath("joinFeat_points.csv")
    arcpy.CopyRows_management(join_feat, str(csv_pth))

    # read the csv file as a pandas data frame
    point_df = pandas.read_csv(csv_pth, sep=",", header=0, index_col="OBJECTID")

    ids = []
    angles = []
    directions = []
    x_coords = []
    y_coords = []

    # loop through each feature
    for fid in point_df.featID.unique():
        # intend to select two points (e.g., E and W, W and E, N and S, S and N)
        # for each input feature; each point requires one row
        ids.append(fid)  # for first point (one element in the list)
        ids.append(fid)  # for second point (next element in the list)

        # temp_df contains candidate points for a selected polygon feature
        temp_df = point_df.loc[point_df.featID == fid]
        idx = temp_df.POINT_Y == temp_df.POINT_Y.max()
        angle = temp_df.loc[idx]["rectangle_Orientation"].values[0]
        angles.append(angle)
        angles.append(angle)

        if (angle >= 45) & (angle <= 135):
            # POINT_X.max() indicates E
            idx = temp_df.POINT_X == temp_df.POINT_X.max()
            subs = temp_df.loc[idx]
            directions.append(subs["direction"].values[0])
            x_coords.append(subs["POINT_X"].values[0])
            y_coords.append(subs["POINT_Y"].values[0])

            # POINT_X.min() indicates W
            idx = temp_df.POINT_X == temp_df.POINT_X.min()
            subs = temp_df.loc[idx]
            directions.append(subs["direction"].values[0])
            x_coords.append(subs["POINT_X"].values[0])
            y_coords.append(subs["POINT_Y"].values[0])
        else:
            # POINT_Y.max() indicates N
            idx = temp_df.POINT_Y == temp_df.POINT_Y.max()
            subs = temp_df.loc[idx]
            directions.append(subs["direction"].values[0])
            x_coords.append(subs["POINT_X"].values[0])
            y_coords.append(subs["POINT_Y"].values[0])

            # POINT_Y.min() indicates S
            idx = temp_df.POINT_Y == temp_df.POINT_Y.min()
            subs = temp_df.loc[idx]
            directions.append(subs["direction"].values[0])
            x_coords.append(subs["POINT_X"].values[0])
            y_coords.append(subs["POINT_Y"].values[0])

    # create a new dataframe
    df = pandas.DataFrame(
        {
            "featID": ids,
            "angle": angles,
            "direction": directions,
            "POINT_X": x_coords,
            "POINT_Y": y_coords,
        }
    )

    # export the dataframe to a csv file
    out_pth = temp_folder.joinpath("joinFeat_points1_selected.csv")
    df.to_csv(out_pth, sep=",", header=True)

    # create point featureclass from the csv file
    arcpy.XYTableToPoint_management(
        str(out_pth),
        str(out_point_feat),
        "POINT_X",
        "POINT_Y",
        "#",
        mbr_line_class,
    )


# TODO; the `old` label in the function inidicates its an older version.
#       confirm that this function is no longer required.
#       Also, is direction_points_old the preferred function???
# 4051
def direction_points_old1(
    in_feat_class: str, mbr_line_class: str, temp_folder: Path, out_point_feat: Path
) -> None:
    """
    Generate direction point features from the input features and the bounding
    rectangle features.
    This one would potentially resulted in a small number of incorrect points,
    e.g. two points on different features may be on the same line.

    :param in_feat_class:
        Represents the polygons to be connected;
        input Bathymetric High Features.

    :param mbr_line_class:
        A subset of lines from the the minimum bounding rectangles
        of in_feat_class. For each feature that are two lines,
        either N and S or E and W.

    :param temp_folder:
        A filepath to a location that will store the temporary files.

    :param out_point_feat:
        Output direction point features.

    :notes:
        The label `class` isn't referring to a Python class,
        but a classification.
        This function but is very time consuming
    """

    def arc_search_cursor(feature_label: str, direction: str, selected_points: str):
        """
        ArcGIS wrapper for search cursor. Not for generic use,
        is specific to the function that this function is embedded within.
        """
        ids: list[int] = []
        angles: list[float] = []
        directions: list[str] = []
        x_coords: list[float] = []
        y_coords: list[float] = []

        cursor = arcpy.SearchCursor(feature_label)
        arcpy.AddMessage(f"Searching: {feature_label}")

        for row in cursor:
            feat_id = row.getValue("featID")
            arcpy.AddMessage(f"featID: {feat_id}")

            ids.append(feat_id)
            angles.append(row.getValue("rectangle_Orientation"))
            directions.append(direction)

            temp_feat = "tempFeat"
            where_clause = f"featID = {feat_id}"
            arcpy.Select_analysis(selected_points, temp_feat, where_clause)

            temp_feat1 = "tempFeat1"
            arcpy.Select_analysis(feature_label, temp_feat1, where_clause)

            layer_temp = "layerTemp"
            arcpy.MakeFeatureLayer_management(temp_feat, layer_temp)

            # select those points that are on the selected bounding
            # rectangle boundaries (N and S or E and W)
            arcpy.SelectLayerByLocation_management(layer_temp, "INTERSECT", temp_feat1)
            temp_points = "tempPoints"
            arcpy.CopyFeatures_management(layer_temp, temp_points)

            cursor1 = arcpy.SearchCursor(temp_points)
            row1 = cursor1.next()
            x_coords.append(row1.getValue("POINT_X"))
            y_coords.append(row1.getValue("POINT_Y"))

            # cleanup
            arcpy.Delete_management(temp_feat)
            arcpy.Delete_management(temp_feat1)
            arcpy.Delete_management(temp_points)
            arcpy.Delete_management(layer_temp)

        return ids, angles, directions, x_coords, y_coords

    in_feat_vertices = "inFeatVertices"

    # convert each input feature to points;
    arcpy.FeatureVerticesToPoints_management(in_feat_class, in_feat_vertices, "ALL")

    layer1 = "layer1"
    arcpy.MakeFeatureLayer_management(in_feat_vertices, layer1)

    # select those points that are on the selected bounding rectangle
    # boundaries (N and S or E and W)
    arcpy.SelectLayerByLocation_management(layer1, "INTERSECT", mbr_line_class)
    selected_points = "selectedPoints1"
    arcpy.CopyFeatures_management(layer1, selected_points)
    arcpy.AddXY_management(selected_points)

    ids = []
    angles = []
    directions = []
    x_coords = []
    y_coords = []

    direction_content = list(
        zip(
            ["MbrLineN", "MbrLineS", "MbrLineE", "MbrLineW"],
            ["N", "S", "E", "W"],
        )
    )

    for line, direction in direction_content:
        where_clause = f"direction = '{direction}'"
        arcpy.Select_analysis(mbr_line_class, line, where_clause)

    for line, direction in direction_content:
        data = arc_search_cursor(line, direction, selected_points)
        ids.extend(data[0])
        angles.extend(data[1])
        directions.extend(data[2])
        x_coords.extend(data[3])
        y_coords.extend(data[4])

    # create a new dataframe
    df = pandas.DataFrame(
        {
            "featID": ids,
            "angle": angles,
            "direction": directions,
            "POINT_X": x_coords,
            "POINT_Y": y_coords,
        }
    )

    # export the dataframe to a csv file
    out_pth = temp_folder.joinpath("joinFeat_points1_selected.csv")
    df.to_csv(out_pth, sep=",", header=True)

    # create point featureclass from the csv file
    arcpy.XYTableToPoint_management(
        str(out_pth), str(out_point_feat), "POINT_X", "POINT_Y", "#", mbr_line_class
    )


# TODO; confirm that this function replaces both
#       direction_points_old1 and direction_points_old
# 4270
def direction_points(
    in_feat_class: str, mbr_line_class: str, temp_folder: Path, out_point_feat: Path
):
    """
    Generate direction point features from the input features.
    Two points are generated for each feature at its north and south sides
    or its east and west sides.

    :param in_feat_class:
        Represents the polygons to be connected;
        input Bathymetric High Features.

    :param mbr_line_class:
        A subset of lines from the the minimum bounding rectangles
        of in_feat_class. For each feature that are two lines,
        either N and S or E and W.

    :param temp_folder:
        A filepath to a location that will store the temporary files.

    :param out_point_feat:
        Output direction point features.

    :notes:
        The label `class` isn't referring to a Python class,
        but a classification.
    """
    items: list[str] = []

    in_feat_vertices = "inFeatVertices"
    items.append(in_feat_vertices)

    # convert each input feature to points
    arcpy.FeatureVerticesToPoints_management(in_feat_class, in_feat_vertices, "ALL")

    # for each polygon, the first vertice and the last vertice are identical,
    # need to remove the duplicate
    vertice_tab = "verticeTab"
    items.append(vertice_tab)
    stats_field = [["OBJECTID", "MIN"]]
    case_field = "featID"
    arcpy.Statistics_analysis(in_feat_vertices, vertice_tab, stats_field, case_field)

    ids: list[int] = []
    cursor = arcpy.SearchCursor(vertice_tab)
    for row in cursor:
        ids.append(row.getValue("MIN_OBJECTID"))

    del cursor  # TODO; is this necessary? maybe arc leaves a dangling pointer?

    in_feat_vertices1 = "inFeatVertices1"
    items.append(in_feat_vertices1)

    # select subset
    text = ",".join([str(i) for i in ids])
    text = f"({text})"
    where_clause = f"OBJECTID NOT IN {text}"
    arcpy.Select_analysis(in_feat_vertices, in_feat_vertices1, where_clause)

    # select polygon points on the bounding rectangle boundaries
    layer1 = "layer1"
    items.append(layer1)
    arcpy.MakeFeatureLayer_management(in_feat_vertices1, layer1)

    # select those points that are on the selected bounding rectangle boundaries
    # (N and S or E and W)
    arcpy.SelectLayerByLocation_management(layer1, "INTERSECT", mbr_line_class)
    selected_points = "selectedPoints1"
    items.append(selected_points)
    arcpy.AddXY_management(selected_points)

    # separate into four boundary types
    direction_content = list(
        zip(
            ["MbrLineN", "MbrLineS", "MbrLineE", "MbrLineW"],
            ["N", "S", "E", "W"],
        )
    )

    for line, direction in direction_content:
        items.append(line)
        where_clause = f"direction = '{direction}'"
        arcpy.Select_analysis(mbr_line_class, line, where_clause)

    # when the orientation is straight north (=0) or straight east (=90),
    # multiple points can be on the boundaries
    # in this case, need to select only one point (first point)
    # for each boundary
    selected_points_1 = "selectedPoints1_1"
    items.append(selected_points_1)
    where_clause = "rectangle_Orientation = 0"
    arcpy.Select_analysis(selected_points, selected_points_1, where_clause)

    tab1 = "tab1"
    items.append(tab1)
    stats_fields = [["OBJECTID", "MIN"]]
    case_fields = ["featID", "POINT_Y"]
    arcpy.Statistics_analysis(selected_points_1, tab1, stats_fields, case_fields)

    ids = []
    cursor = arcpy.SearchCursor(tab1)
    for row in cursor:
        ids.append(row.getValue("MIN_OBJECTID"))

    del cursor  # TODO; is this necessary? maybe arc leaves a dangling pointer?

    selected_points_1_1 = "selectedPoints1_1_1"
    items.append(selected_points_1_1)

    # select subset
    text = ",".join([str(i) for i in ids])
    text = f"({text})"
    where_clause = f"OBJECTID IN {text}"
    arcpy.Select_analysis(selected_points_1, selected_points_1_1, where_clause)

    selected_points_2 = "selectedPoints1_2"
    items.append(selected_points_2)
    where_clause = "rectangle_Orientation = 90"
    arcpy.Select_analysis(selected_points, selected_points_2, where_clause)

    tab2 = "tab2"
    items.append(tab2)
    stats_fields = [["OBJECTID", "MIN"]]
    case_fields = ["featID", "POINT_X"]
    arcpy.Statistics_analysis(selected_points_2, tab2, stats_fields, case_fields)

    ids = []
    cursor = arcpy.SearchCursor(tab2)
    for row in cursor:
        ids.append(row.getValue("MIN_OBJECTID"))

    del cursor

    selected_points_2_1 = "selectedPoints1_2_1"
    items.append(selected_points_2_1)

    # select subset
    text = ",".join([str(i) for i in ids])
    text = f"({text})"
    where_clause = f"OBJECTID IN {text}"
    arcpy.Select_analysis(selected_points_2, selected_points_2_1, where_clause)

    # select those points that are not from features orienting
    # straight north and straight east
    selected_points_4 = "selectedPoints1_4"
    items.append(selected_points_4)
    where_clause = "(rectangle_Orientation <> 0) And (rectangle_Orientation <> 90)"
    arcpy.Select_analysis(selected_points, selected_points_4, where_clause)

    # merge these three subsets to form a new set of points
    selected_points1 = "selectedPoints2"
    items.append(selected_points1)
    inputs = [selected_points_1_1, selected_points_2_1, selected_points_4]
    arcpy.Merge_management(inputs, selected_points1)

    # generate direction lists
    ids = []
    angles: list[float] = []
    directions: list[str] = []
    x_coords: list[float] = []
    y_coords: list[float] = []

    # TODO; implement
    # generate_direction_point_lists()
    for line, direction in direction_content:
        data = generate_direction_points(selected_points1, line, direction)

        ids.extend(data[0])
        angles.extend(data[1])
        directions.extend(data[2])
        x_coords.extend(data[3])
        y_coords.extend(data[4])

    # create a new dataframe
    df = pandas.DataFrame(
        {
            "featID": ids,
            "angle": angles,
            "direction": directions,
            "POINT_X": x_coords,
            "POINT_Y": y_coords,
        }
    )

    # export the dataframe to a csv file
    out_pth = temp_folder.joinpath("points1_selected.csv")
    df.to_csv(out_pth, sep=",", header=True)

    # create point featureclass from the csv file
    arcpy.XYTableToPoint_management(
        str(out_pth), str(out_point_feat), "POINT_X", "POINT_Y", "#", mbr_line_class
    )

    # delete temporary data
    delete_items(items)


# 4443
def generate_direction_points(
    point_feat: str,
    mbr_line_feat: str,
    direction: str,
) -> tuple[list[int], list[float], list[str], list[float], list[float]]:
    """
    Generates five lists from the direction points input featureclass.

    :param point_feat:
        Input direction points feature class.

    :param mbr_line_feat:
        Input bounding rectangle boundaries feature class.

    :param direction:
        Indicates the direction.

    :notes:
        The original function appended in-place and returned the variables,
        making it a little confusing to follow exactly what's going on.
        Instead, this version will return new lists, and make the caller
        responsible for appending.
    """
    items: list[str] = []
    layer_temp = "layerTemp"
    items.append(layer_temp)
    arcpy.MakeFeatureLayer_management(point_feat, layer_temp)

    # select those points that are on the selected bounding rectangle boundaries
    # (N and S or E and W)
    arcpy.SelectLayerByLocation_management(layer_temp, "INTERSECT", mbr_line_feat)
    selected_points_temp = "selectedPointsTemp"
    # items.append(selected_points_temp)  # TODO; original code had layerTemp, mistake??
    arcpy.CopyFeatures_management(layer_temp, selected_points_temp)

    # build two featID lists: one contains features with only one
    # candidate point; the other contains mutliple candidate points
    sum_tab = "sumTab"
    items.append(sum_tab)
    stats_fields = [["featID", "COUNT"]]
    case_field = "featID"
    arcpy.Statistics_analysis(selected_points_temp, sum_tab, stats_fields, case_field)

    feat_ids_1: list[int] = []
    feat_ids_2: list[int] = []

    cursor = arcpy.SearchCursor(sum_tab)
    for row in cursor:
        count = int(row.getValue("COUNT_featID"))
        feat_id = row.getValue("featID")

        if count > 1:
            feat_ids_2.append(feat_id)
        else:
            feat_ids_1.append(feat_id)

    del cursor

    if feat_ids_1:
        # select subset
        text = ",".join([str(i) for i in feat_ids_1])
        text = f"({text})"
        where_clause = f"featID IN {text}"
        selected_points_temp1 = "selectedPoints1Temp1"
        items.append(selected_points_temp1)
        arcpy.Select_analysis(selected_points_temp, selected_points_temp1, where_clause)

    out_ids: list[int] = []
    out_angles: list[float] = []
    out_directions: list[str] = []
    out_x_coords: list[float] = []
    out_y_coords: list[float] = []

    # deal with the first subset
    in_feat_count = int(arcpy.GetCount_management(selected_points_temp1).getOutput(0))
    if in_feat_count:
        cursor = arcpy.SearchCursor(selected_points_temp1)

        for row in cursor:
            feat_id = row.getValue("featID")
            arcpy.AddMessage(f"featID: {feat_id}")
            out_ids.append(feat_id)
            out_angles.append(row.getValue("rectangle_Orientation"))
            out_directions.append(direction)
            out_x_coords.append(row.getValue("POINT_X"))
            out_y_coords.append(row.getValue("POINT_Y"))

        del cursor

    # deal with the second subset
    if feat_ids_2:
        for idv in feat_ids_2:
            arcpy.AddMessage(f"idV: {idv}")
            temp_feat = "tempFeat"
            where_clause = f"featID = {idv}"
            arcpy.Select_analysis(point_feat, temp_feat, where_clause)

            temp_feat1 = "tempFeat1"
            arcpy.Select_analysis(mbr_line_feat, temp_feat1, where_clause)

            layer_temp1 = "layerTemp1"
            arcpy.MakeFeatureLayer_management(temp_feat, layer_temp1)

            # select those points that are on the selected bounding
            # rectangle boundaries (N and S or E and W)
            arcpy.SelectLayerByLocation_management(layer_temp1, "INTERSECT", temp_feat1)
            temp_points = "tempPoints"
            arcpy.CopyFeatures_management(layer_temp1, temp_points)

            in_feat_count = int(arcpy.GetCount_management(temp_points).getOutput(0))
            if in_feat_count:
                out_ids.append(idv)

                cursor1 = arcpy.SearchCursor(temp_points)
                row1 = cursor1.next()  # get the first candidate point
                out_x_coords.append(row1.getValue("POINT_X"))
                out_y_coords.append(row1.getValue("POINT_Y"))

                out_angles.append(row1.getValue("rectangle_Orientation"))
                out_directions.append(direction)

                del cursor1, row1

            arcpy.Delete_management(temp_feat)
            arcpy.Delete_management(temp_feat1)
            arcpy.Delete_management(temp_points)
            # arcpy.Delete_management(layer_temp1)  # TODO; orig code had layer_temp

    delete_items(items)

    return out_ids, out_angles, out_directions, out_x_coords, out_y_coords


# 4561
def select_links(
    in_links_feat: str,
    points_feat_from: str,
    points_feat_to: str,
    out_links_feat: str,
) -> None:
    """
    Selects as subset of input links.

    :param in_links_feat:
        Input links feature class.

    :param points_feat_from:
        Feature class represents the from point of a link.

    :param points_feat_to:
        Feature class represents the to point of a link.

    :param out_links_feat:
        Output the subset of links after the selection process.
    """
    # add and calculate fields
    fields = ["featID1", "fromLocation", "fromDirection"]
    values = ["featID", "location", "direction"]
    in_id = "ORIG_FID"
    join_id = "OBJECTID"

    for item in zip(fields, values):
        expression = f"!{points_feat_from}.{item[1]}!"
        add_long_field(
            in_links_feat, points_feat_from, item[0], in_id, join_id, expression
        )

    fields = ["featID2", "toLocation", "toDirection"]
    in_id = "DEST_FID"
    join_id = "OBJECTID"

    for item in zip(fields, values):
        expression = f"!{points_feat_to}.{item[1]}!"
        add_long_field(
            in_links_feat, points_feat_to, item[0], in_id, join_id, expression
        )

    # add more fields
    field_name1 = "idDiff"
    field_type = "LONG"
    field_precision = 15
    arcpy.AddField_management(in_links_feat, field_name1, field_type, field_precision)

    expression = "!featID1! - !featID2!"
    arcpy.CalculateField_management(in_links_feat, field_name1, expression)
    links_feat1_temp = "links1Temp"
    where_clause = "idDiff <> 0"
    arcpy.Select_analysis(in_links_feat, links_feat1_temp, where_clause)

    # generate summary statistics
    tab1 = "tab1"
    stats_fields = [["LINK_DIST", "MIN"]]
    case_field = "featID1"
    arcpy.Statistics_analysis(links_feat1_temp, tab1, stats_fields, case_field)

    field_name2 = "distDiff"
    in_id = "featID1"
    join_id = "featID1"
    expression = f"!{links_feat1_temp}.LINK_DIST! - !{tab1}.MIN_LINK_DIST!"
    add_double_field(links_feat1_temp, tab1, field_name2, in_id, join_id, expression)

    # select a subset of links based on the following condition
    links_feat2_temp = "links2Temp"
    where_clause = "distDiff = 0"
    arcpy.Select_analysis(links_feat1_temp, links_feat2_temp, where_clause)

    # further selection based on the following condition
    where_clause = "(fromLocation = 'F') And (toLocation = 'H')"
    arcpy.Select_analysis(links_feat2_temp, out_links_feat, where_clause)

    delete_items([links_feat1_temp, links_feat2_temp, tab1])


# 4630
def to_fh_points(
    in_points_feat: str,
    mosaic_bathy: str,
    temp_folder: Path,
    out_point_feat: Path,
):
    """
    Identifies the input poions as either head (H) points or foot (F) points.

    :param in_points_feat:
        Input feature class represents direction points.

    :param mosaic_bathy:
        Input bathymetry data.

    :param temp_folder:
        A filepath to a location that will store the temporary files.

    :param out_point_feat:
        Output point feature class with a new field indicating the
        H or F location.
    """
    point_feat_temp = "pointFeatTemp"

    # to identify a point as either H or F point, we need to obtain the
    # bathymetry value for this point
    sa.ExtractValuesToPoints(in_points_feat, mosaic_bathy, point_feat_temp)
    arcpy.AddMessage("extract depth values done")

    # delete schema.ini which may contains incorrect data types
    schema_pth = temp_folder.joinpath("schema.ini")
    if schema_pth.exists():
        schema_pth.unlink()

    # export the attributes to a csv file
    csv_pth = temp_folder.joinpath("pointFeat1.csv")
    arcpy.CopyRows_management(point_feat_temp, csv_pth)

    # read the csv file as a pandas data frame
    point_df = pandas.read_csv(csv_pth, sep=",", header=0, index_col="OBJECTID")

    ids: list[int] = []
    angles: list[float] = []
    directions: list[str] = []
    locations: list[str] = []
    x_coords: list[float] = []
    y_coords: list[float] = []

    # loop through each feature
    for fid in point_df.featID.unique():
        # intend to select two points (e.g., E and W, W and E, N and S, S and N)
        # for each input feature; each point requires one row
        ids.append(fid)  # for first point (one element in the list)
        ids.append(fid)  # for second point (next element in the list)

        # temp_df contains candidate points for a selected polygon feature
        temp_df = point_df.loc[point_df.featID == fid]
        idx = temp_df.POINT_Y == temp_df.POINT_Y.max()
        angle = temp_df.loc[idx]["angle"].values[0]
        angles.append(angle)
        angles.append(angle)

        # RASTERVALU.max() indicates head
        idx = temp_df.RASTERVALU == temp_df.RASTERVALU.max()
        subs = temp_df[idx]
        x_coords.append(subs["POINT_X"].values[0])
        y_coords.append(subs["POINT_Y"].values[0])
        directions.append(subs["direction"].values[0])
        locations.append("H")

        # RASTERVALU.min() indicates foot
        idx = temp_df.RASTERVALU == temp_df.RASTERVALU.min()
        subs = temp_df[idx]
        x_coords.append(subs["POINT_X"].values[0])
        y_coords.append(subs["POINT_Y"].values[0])
        directions.append(subs["direction"].values[0])
        locations.append("F")

    # create a new dataframe
    df = pandas.DataFrame(
        {
            "featID": ids,
            "angle": angles,
            "direction": directions,
            "location": locations,
            "POINT_X": x_coords,
            "POINT_Y": y_coords,
        }
    )

    # export the dataframe to a csv file
    out_pth = temp_folder.joinpath("pointFeat2.csv")
    df.to_csv(out_pth, sep=",", header=True)

    # create point featureclass from the csv file
    arcpy.XYTableToPoint_management(
        str(out_pth), str(out_point_feat), "POINT_X", "POINT_Y", "#", in_points_feat
    )

    delete_items([point_feat_temp, str(csv_pth), str(out_pth)])
