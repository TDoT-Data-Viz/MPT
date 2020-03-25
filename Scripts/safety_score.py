import arcpy
import os

# Get roads layer
roads = arcpy.GetParameterAsText(0)
rn_blm = arcpy.GetParameterAsText(1)
rn_elm = arcpy.GetParameterAsText(2)
# Get crash layer
crashes = arcpy.GetParameterAsText(3)
clm = arcpy.GetParameterAsText(4)
# Get user defined path to working database.
output = arcpy.GetParameterAsText(5)
ttl_kill = arcpy.GetParameterAsText(6)
ttl_inca = arcpy.GetParameterAsText(7)
ttl_other = arcpy.GetParameterAsText(8)

arcpy.AddMessage(roads)
arcpy.AddMessage(crashes)
arcpy.AddMessage(output)
arcpy.AddMessage("Running Safety Scoring on {} {}".format(crashes, roads))

# Convert layers to tables for use in overlays.
ct = arcpy.conversion.TableToTable(crashes, output, "CRASH_TABLE")
rt = arcpy.conversion.TableToTable(roads, output, "T_" + roads)

crash_ovl = arcpy.lr.OverlayRouteEvents(rt, "ID_NUMBER Line {} {}".format(rn_blm, rn_elm), ct,
                                        "ID_NUMBER Line {} {}".format(clm, clm), "INTERSECT",
                                        os.path.join(output, os.path.basename(crashes) + "_Crash_Overlay"),
                                        "IDNUMBER_C Line BLM_C ELM_C","ZERO", "FIELDS", "INDEX")

arcpy.management.AddField(crash_ovl, "BASIC_CRASH", "INTEGER", None, None, None, '', "NULLABLE", "NON_REQUIRED", '')
arcpy.management.AddField(crash_ovl, "RAW_SEV", "INTEGER", None, None, None, '', "NULLABLE", "NON_REQUIRED", '')

# Calculate Basic Crash score
with arcpy.da.UpdateCursor(crash_ovl, [ttl_kill, ttl_inca, ttl_other, 'BASIC_CRASH'])as cur:
    for row in cur:
        if row[0] == 0 and row[1] == 0 and row[2] == 0:
            row[3] = 1
        else:
            row[3] = 0
        cur.updateRow(row)
del cur

# Calculate Raw Severity
arcpy.management.CalculateField(crash_ovl, "RAW_SEV",
                                "(!{}!*5) + (!{}!*4) + (!{}! *3) + (!BASIC_CRASH! *2)".format(ttl_kill, ttl_inca,
                                                                                              ttl_other), "PYTHON3", '')
# Summary Statistics to sum the severity and frequency for each segment in the road network.
ss = arcpy.analysis.Statistics(crash_ovl, os.path.join(output, os.path.basename(crashes) + "_SS"),
                               "BASIC_CRASH SUM;{} SUM;{} SUM;{} SUM;RAW_SEV SUM; CASENO COUNT".format(ttl_other,
                                                                                                       ttl_inca,
                                                                                                       ttl_kill), "UID")

# Rename Fields
arcpy.AlterField_management(ss, 'SUM_RAW_SEV', 'RAW_SEV', 'RAW_SEV', 'DOUBLE', '4', 'NULLABLE', 'DO_NOT_CLEAR')
arcpy.AlterField_management(ss, 'COUNT_CASENO', 'RAW_FREQ', 'RAW_FREQ', 'LONG', '4', 'NULLABLE', 'DO_NOT_CLEAR')