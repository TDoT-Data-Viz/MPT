import arcpy
import os

"""Script for the LTS Script Tool that automates the Level of Traffic Stress component of the MPT.

Required:
Trims Tables DV - the path to a gdb with the necessary TRIMS tables.
Output Directory - the path to a folder where you want the output to go.

The final layer is currently called 'Overlay_E". It is a table with 'LaneScore', 'SpeedScore', 'CurbScore', 'SidewalkScore',
'BikeLaneScore', 'AADTScore', and the average of them all as 'LTS_SCORE'.
"""

# The necessary TRIMS tables are: 'GEOMETRICS', 'RD_SGMNT', 'RDWAY_DESCR', and 'TRAFFIC'
# Create a copy of the above tables. Make sure to name them correctly, or change the script accordingly.
# Path to your gdb with copy of TRIMS tables.
tt = arcpy.GetParameterAsText(0)
# Get user defined path to working database.
output = arcpy.GetParameterAsText(1)
# Drop-down with planning areas. This allows you to create lts for any or all planning areas
area = arcpy.GetParameterAsText(2)
# Drop-down that defines functional classifications. The MPT treats collectors and arterials separately
func_class = arcpy.GetParameterAsText(3)

arcpy.AddMessage(area)
pa = area.replace(" ", "_")

# Dictionary that holds the values for each planning area's counties and the MPA code. This allows us to do queries so
# that we can create LTS for the different planning areas.

# TODO: Fix this hideous dictionary.
planning_areas = {
    "First TN": ["30, 37, 46, 34, 86, 90, 82, 10", "IS NULL"],
    "Northwest RPO": ["48,66,92,40,3,9,27,17,23", "IS NULL"],
    "Middle TN RPO": ["81,42,11,22,43", "IS NULL"],
    "South Central West RPO": ["41,51,68,50,91", "IS NULL"],
    "West TN RPO": ["49,24,84", "IS NULL"],
    "Southwest RPO": ["38,35,39,12,20,36,55", "IS NULL"],
    "Dale Hollow RPO": ["14,25,56,44,67,80,85,69", "IS NULL"],
    "East TN North RPO": ["7,13,1,29,65,76,87", "IS NULL"],
    "Nashville MPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,"
                      "34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,"
                      "65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95",
                      "= 210"],
    "Memphis MPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,34,"
                    "35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,"
                    "67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95", "= 191"],
    "Center Hill RPO": ["8,18,21,71,89,93,88", "IS NULL"],
    "Clarksville MPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,"
                        "33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,"
                        "63,64,65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,"
                        "94,95","= 55"],
    "South Central East RPO": ["16,28,26,2,52,59,64", "IS NULL"],
    "Jackson MPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,34,"
                    "35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,"
                    "67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95","= 143"],
    "Southeast RPO": ["4,6,31,33,58,54,61,77,70,72", "IS NULL"],
    "Johnson City MPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,"
                         "33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,"
                         "63,64,65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,"
                         "94,95","= 148"],
    "Kingsport MTPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,"
                       "34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,"
                       "65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95",
                       "= 152"],
    "Bristol MTPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,"
                     "34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,"
                     "65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95",
                     "= 34"],
    "Knoxville TPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,"
                      "34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,"
                      "65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95",
                      "= 155"],
    "Lakeway MTPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,"
                     "34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,"
                     "65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95",
                     "= 388"],
    "Chattanooga TPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,"
                        "33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,"
                        "63,64,65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,"
                        "94,95","= 52"],
    "East TN South RPO": ["5,15,62,45,53,78,73", "IS NULL"],
    "Cleveland MPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,"
                      "34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,"
                      "65,66,67,68,69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95",
                      "= 56"],
    "All MPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,34,35,"
                "36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,"
                "69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95","IN (210,191,55,143,"
                                                                                                "148,152,34,155,388,"
                                                                                                "52,56)"],
    "All RPO": ["73,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,23,22,24,26,25,27,28,29,30,31,32,33,34,35,"
                "36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,"
                "69,70,71,72,75,74,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95","IS NULL"]

}

# Defines which values to use for the defined functional classification.
if func_class == "Collectors":
    func_classes = "('07', '08', '17', '18')"
elif func_class == "Arterials":
    func_classes = "('02', '06', '14', '16')"

# Gets the county values from the 'planning_area' dictionary for the selected planning area.
counties = planning_areas.get(area)[0]
urb_area = planning_areas.get(area)[1]
arcpy.AddMessage(urb_area)
arcpy.AddMessage(pa)

# Create gdb for output
arcpy.CreateFileGDB_management(output, pa + "_" + func_class)
db = os.path.join(output, pa + "_" + func_class + ".gdb")

# Creates a layer that includes events from 'RD_SGMNT' that correspond to the selected functional classes and counties.
rd_seg = arcpy.analysis.TableSelect(os.path.join(tt, "RD_SGMNT"), os.path.join(db, func_class + "_" + pa),
                                    "NBR_TENN_CNTY IN ({}) And FUNC_CLASS IN {} AND STDY_AREA {}".format(counties,
                                                                                                         func_classes,
                                                                                                         urb_area))
# Creates a layer that includes events from 'TRAFFIC' that correspond to the selected counties.
traffic = arcpy.analysis.TableSelect(os.path.join(tt, "TRAFFIC"), os.path.join(db, "Traffic_" + pa),
                                     "NBR_TENN_CNTY IN ({})".format(counties))
# Creates a layer that includes events from 'GEOMETRICS' that correspond to the selected counties.
geometrics = arcpy.analysis.TableSelect(os.path.join(tt, "GEOMETRICS"), os.path.join(db, "Geometrics_" + pa),
                                        "NBR_TENN_CNTY IN ({})".format(counties))
# Overlays events from 'traffic' onto 'rd_seg'. Pretty sure this is simply a inner join or left join.
traffic_base = arcpy.lr.OverlayRouteEvents(rd_seg, "ID_NUMBER Line RS_BEG_LOG_MLE RS_END_LOG_MLE", traffic,
                                           "ID_NUMBER Line TR_BEG_LOG_MLE TR_END_LOG_MLE", "INTERSECT",
                                           os.path.join(db, func_class + "_TrafficBase"), "ID_NUMBER Line BLM ELM",
                                           "NO_ZERO", "FIELDS", "INDEX")

# Overlays events from 'geometrics' onto 'rd_seg'. Pretty sure this is simply a inner join or left join.
geo_base = arcpy.lr.OverlayRouteEvents(rd_seg, "ID_NUMBER Line RS_BEG_LOG_MLE RS_END_LOG_MLE", geometrics,
                                       "ID_NUMBER Line RD_BEG_LOG_MLE RD_END_LOG_MLE", "INTERSECT",
                                       os.path.join(db, func_class + "_GeoBase"), "ID_NUMBER Line BLM ELM", "NO_ZERO",
                                       "FIELDS", "INDEX")

# Grab county road way description events from 'RDWAY_DESCR' table
rdway_desc = arcpy.analysis.TableSelect(os.path.join(tt, "RDWAY_DESCR"), os.path.join(db, "Rdway_descr_" + pa),
                                        "NBR_TENN_CNTY IN ({})".format(counties))

# Query out sidewalk features from 'rdway_desc'
sidewalk_feats = arcpy.analysis.TableSelect(rdway_desc, os.path.join(db, "SidewalkFeatures"),
                                            "FEAT_CMPOS IN ('43', '44', '45')")

# Create 'Sidewalks_Identical' layer and the 'Sidewalks_NoIdentical' layer.
sidewalks_id = arcpy.lr.OverlayRouteEvents(rd_seg, "ID_NUMBER Line RS_BEG_LOG_MLE RS_END_LOG_MLE", sidewalk_feats,
                                           "ID_NUMBER Line RD_BEG_LOG_MLE RD_END_LOG_MLE", "INTERSECT",
                                           os.path.join(db, "Sidewalks_Identical"), "ID_NUMBER Line BLM ELM", "NO_ZERO",
                                           "FIELDS", "INDEX")
arcpy.management.AddField(sidewalks_id, "Sidewalk_Present", "TEXT", None, None, None, '', "NULLABLE", "NON_REQUIRED",
                          '')
arcpy.management.CalculateField(sidewalks_id, "Sidewalk_Present", '"YES"', "PYTHON3", '')
sidewalks_no_id = arcpy.TableToTable_conversion(sidewalks_id, arcpy.env.workspace, "Sidewalks_NoIdentical")
arcpy.management.DeleteIdentical(sidewalks_no_id, "ID_NUMBER;BLM;ELM", None, 0)

# Create 'Pavement_features' layer
pave_feats = arcpy.analysis.TableSelect(rdway_desc, os.path.join(db, "Pavement_features"),
                                        "TYP_FEAT IN (2, 3, 4, 5, 6, 10, 11, 12, 14, 15, 19, 20, 21, 30, 35, 40)")
# Create 'Pavement_Curb' layer.
pave_curb = arcpy.lr.OverlayRouteEvents(rd_seg, "ID_NUMBER Line RS_BEG_LOG_MLE RS_END_LOG_MLE", pave_feats,
                                        "ID_NUMBER Line RD_BEG_LOG_MLE RD_END_LOG_MLE", "INTERSECT",
                                        os.path.join(db, "Pavement_Curb"), "ID_NUMBER Line BLM ELM", "NO_ZERO",
                                        "FIELDS", "INDEX")
arcpy.management.AddField(pave_curb, "Join_Link", 'TEXT', None, None, None, '', "NULLABLE", "NON_REQUIRED", '')
arcpy.management.CalculateField(pave_curb, "Join_Link", "!NBR_RTE!+'-'+str(!BLM!)+'-'+str(!ELM!)", "PYTHON3", '')
# Sum FEAT_WIDTH of segments.
curb_stats = arcpy.analysis.Statistics(pave_curb, os.path.join(db, "Pavement_curb_Statistics"), "FEAT_WIDTH SUM",
                                       "NBR_RTE;BLM;ELM")
arcpy.management.AddField(curb_stats, "Join_Link", 'TEXT', None, None, None, '', "NULLABLE", "NON_REQUIRED", '')
arcpy.management.CalculateField(curb_stats, "Join_Link", "!NBR_RTE!+'-'+str(!BLM!)+'-'+str(!ELM!)", "PYTHON3", '')
pave_curb_joined = arcpy.management.AddJoin(pave_curb, "Join_Link", curb_stats, "Join_Link", "KEEP_ALL")

arcpy.AddMessage("Join Complete. Saved as 'pave_curb_joined'")

# Create 'Bikelanes_Identical' layer and the 'Bikelanes_NoIdentical'.
bikelanes_id = arcpy.analysis.TableSelect(pave_curb, os.path.join(db, "Bikelanes_Identical"), "TYP_FEAT = 30")
arcpy.management.AddField(bikelanes_id, "Bikelane_Present", "TEXT", None, None, None, '', "NULLABLE", "NON_REQUIRED",
                          '')
arcpy.management.CalculateField(bikelanes_id, "Bikelane_Present", '"YES"', "PYTHON3", '')
bikelanes_no_id = arcpy.TableToTable_conversion(bikelanes_id, arcpy.env.workspace, "Bikelanes_NoIdentical")
arcpy.management.DeleteIdentical(bikelanes_no_id, "ID_NUMBER;BLM;ELM", None, 0)

# Create 'Medians' layer.
medians = arcpy.analysis.TableSelect(pave_curb, os.path.join(db, "Medians"), "TYP_FEAT = 40")

# Add scoring fields to '***_TrafficBase'.
add_fields = ["EquityScore", "DemandScore", "LaneScore", "SpeedScore", "CurbScore", "SidewalkScore", "BikeLaneScore",
              "AADTScore"]
for field in add_fields:
    arcpy.management.AddField(traffic_base, field, "DOUBLE", None, None, None, '', "NULLABLE", "NON_REQUIRED", '')

# Overlay A
ov_a = arcpy.lr.OverlayRouteEvents(geo_base, "ID_NUMBER Line BLM ELM", pave_curb_joined, "ID_NUMBER Line BLM ELM",
                                   "UNION", os.path.join(db, "Overlay_A"), "ID_NUMBER Line BLM_A ELM_A", "NO_ZERO",
                                   "FIELDS", "INDEX")
arcpy.management.DeleteIdentical(ov_a, "ID_NUMBER;BLM_A;ELM_A", None, 0)
# Overlay B
ov_b = arcpy.lr.OverlayRouteEvents(ov_a, "ID_NUMBER Line BLM_A ELM_A", sidewalks_no_id, "ID_NUMBER Line BLM ELM",
                                   "UNION", os.path.join(db, "Overlay_B"), "ID_NUMBER Line BLM_B ELM_B", "NO_ZERO",
                                   "FIELDS", "INDEX")
arcpy.management.DeleteIdentical(ov_b, "ID_NUMBER;BLM_B;ELM_B", None, 0)
# Overlay C
ov_c = arcpy.lr.OverlayRouteEvents(ov_b, "ID_NUMBER Line BLM_B ELM_B", bikelanes_no_id, "ID_NUMBER Line BLM ELM",
                                   "UNION", os.path.join(db, "Overlay_C"), "ID_NUMBER Line BLM_C ELM_C", "NO_ZERO",
                                   "FIELDS", "INDEX")
arcpy.management.DeleteIdentical(ov_c, "ID_NUMBER;BLM_C;ELM_C", None, 0)
# Overlay D
ov_d = arcpy.lr.OverlayRouteEvents(ov_c, "ID_NUMBER Line BLM_C ELM_C", medians, "ID_NUMBER Line BLM ELM", "UNION",
                                   os.path.join(db, "Overlay_D"), "ID_NUMBER Line BLM_D ELM_D", "NO_ZERO", "FIELDS",
                                   "INDEX")
arcpy.management.DeleteIdentical(ov_d, "ID_NUMBER;BLM_D;ELM_D", None, 0)
# Overlay D
ov_e = arcpy.lr.OverlayRouteEvents(ov_d, "ID_NUMBER Line BLM_D ELM_D", traffic_base, "ID_NUMBER Line BLM ELM", "UNION",
                                   os.path.join(db, "Overlay_E"), "ID_NUMBER Line BLM_E ELM_E", "NO_ZERO", "FIELDS",
                                   "INDEX")
arcpy.management.DeleteIdentical(ov_e, "ID_NUMBER;BLM_E;ELM_E", None, 0)

# Scoring

# Field Calculate Null values in 'SPD_LMT' to 0.
# This didn't work when I first developed this because ArcPro is bugged or I am a moron. Could work now.
# arcpy.management.SelectLayerByAttribute("ov_e", "NEW_SELECTION", "SPD_LMT IS NULL", None)
# arcpy.management.CalculateField("ov_e", "SPD_LMT", 0, "PYTHON3", '')
# This is currently a weird way of calculating it because of the ArcPro bug.
arcpy.management.CalculateField(ov_e, "SPD_LMT", "calcNulls(!SPD_LMT!)", "PYTHON3",
                                "def calcNulls(field):\n    if field is None:\n        return 0\n    else:\n        "
                                "return field")

# This is essentially just a field calc for creating Sidewalk and Bikelane score.
fields = ['Sidewalk_Present', 'SidewalkScore']
with arcpy.da.UpdateCursor(ov_e, fields) as cursor:
    for row in cursor:
        if row[0] == "YES":
            row[1] = 1
        else:
            row[1] = 5
        cursor.updateRow(row)
    del cursor

fields = ['Bikelane_Present', 'BikeLaneScore']
with arcpy.da.UpdateCursor(ov_e, fields) as cursor:
    for row in cursor:
        if row[0] == "YES":
            row[1] = 1
        else:
            row[1] = 5
        cursor.updateRow(row)
    del cursor

# Field calc score fields
arcpy.management.CalculateField(ov_e, "CurbScore", "!SUM_FEAT_WIDTH!", "PYTHON3", '')
arcpy.management.CalculateField(ov_e, "LaneScore", "!NBR_LANES!", "PYTHON3", '')
arcpy.management.CalculateField(ov_e, "SpeedScore", "!SPD_LMT!", "PYTHON3", '')
arcpy.management.CalculateField(ov_e, "AADTScore", "!AADT!", "PYTHON3", '')

# This is a weird method for rescaling values. There is def another way. I also have a rescale function/tool that could
# replace this dumb method.
table = arcpy.analysis.Statistics(ov_e, os.path.join(db, "ov_e_Statistics"),
                                  "LaneScore MIN;LaneScore MAX;CurbScore MIN;CurbScore MAX;SpeedScore MIN;SpeedScore "
                                  "MAX;AADTScore MIN;AADTScore MAX",
                                  None)

with arcpy.da.SearchCursor(table, ['MIN_LaneScore', 'MAX_LaneScore', 'MIN_CurbScore', 'MAX_CurbScore', 'MIN_SpeedScore',
                                   'MAX_SpeedScore', 'MIN_AADTScore', 'MAX_AADTScore']) as cur:
    for row in cur:
        min_lane, max_lane, min_curb, max_curb, min_speed, max_speed, min_aadt, max_aadt = row
del cur

arcpy.management.CalculateField(ov_e, "LaneScore",
                                "((!LaneScore! - {})/({}-{}))*(5-1)+1".format(min_lane, max_lane, min_lane), "PYTHON3",
                                '')
arcpy.management.CalculateField(ov_e, "SpeedScore",
                                "((!SpeedScore! - {})/({}-{}))*(5-1)+1".format(min_speed, max_speed, min_speed),
                                "PYTHON3", '')
arcpy.management.CalculateField(ov_e, "CurbScore",
                                "((!CurbScore! - {})/({}-{}))*(5-1)+1".format(min_curb, max_curb, min_curb), "PYTHON3",
                                '')
arcpy.management.CalculateField(ov_e, "AADTScore",
                                "((!AADTScore! - {})/({}-{}))*(5-1)+1".format(min_aadt, max_aadt, min_aadt), "PYTHON3",
                                '')

arcpy.management.AddField(ov_e, "LTS_SCORE", "DOUBLE", None, None, None, '', "NULLABLE", "NON_REQUIRED", '')
arcpy.management.CalculateField(ov_e, "LTS_SCORE",
                                "(!AADTScore!+!CurbScore!+!LaneScore!+!SpeedScore!+!BikelaneScore!+!SidewalkScore!)/6",
                                "PYTHON3", '')
