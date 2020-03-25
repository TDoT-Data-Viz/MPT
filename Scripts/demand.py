import arcpy
import os
import time

from arcpy import env


def demand(planning_area, inputs, output):
    """Function that automates the Demand component of the MPT.

    Required parameters:
    'planning_area' - the path to a boundary layer for the area of interest.
    'inputs' - the path to a geodatabase with input layers (ex. active businesses, hospitals, etc.).
    'output' - the path to a geodatabase for outputs to be stored.

    bike distance groups = "0 5280 5;5280 10560 4;10560 15840 3;15840 21120 2;21120 1000000 1"
    ped distance groups = "0 1320 5;1320 2640 4;2640 3960 3;3960 5280 2;5280 1000000 1"

    TODO: Elaborate on the full script function.
    """
    # Saves the start time so script duration can be calculated.
    start_time = time.time()

    # Checkout Spatial Analyst
    arcpy.CheckOutExtension("Spatial")

    # Set workspace, extent, mask and spatial reference according to 'inputs' and 'planning_area' provided.
    env.workspace = inputs
    env.extent = planning_area
    env.mask = planning_area
    sr = arcpy.Describe(planning_area).spatialReference
    env.outputCoordinateSystem = sr

    # Sets the cellsize. This can easily be a parameter if we decided to vary our cell size in the future.
    # This has to be set or the output changes slightly. 
    env.cellSize = 30
    print("Environment Set Up")

    # Get a list of all point and polyline features features in 'inputs' database
    ed_features = arcpy.ListFeatureClasses(feature_type="POINT")
    for i in arcpy.ListFeatureClasses(feature_type="POLYLINE"):
        ed_features.append(i)
    print(ed_features)

    # Run Euclidean Distance for each point feature in 'inputs' database and Reclassify 1-5.
    for fc in ed_features:
        ed_layer = arcpy.gp.EucDistance_sa(os.path.join(inputs, fc), os.path.join(output, "rED_"+fc), "")
        # The values can be changed to create Bike or Ped Demand layer.
        # TODO: Make distance groups a parameter of the function.
        arcpy.gp.Reclassify_sa(ed_layer, "VALUE", "0 1320 5;1320 2640 4;2640 3960 3;3960 5280 2;5280 1000000 1",
                               os.path.join(output, "rWS_"+fc), "DATA")
        # This clears the memory so you don't run out.
        del ed_layer

    # Create rasters for "Pop_Density", "Employ_Density", and "Active_Commute" found in BG_2017
    # Note: In BG_2017 Employ_Density field name is actually "Employ_D"
    block_group = os.path.join(inputs, 'BG_2017')
    print("Starting polygon to raster conversions")
    r_pop_den = arcpy.PolygonToRaster_conversion(block_group, "Pop_Density", os.path.join(output, 'r_pop_den'), "CELL_CENTER", "NONE")
    r_commute = arcpy.PolygonToRaster_conversion(block_group, "Active_Commute", os.path.join(output, 'r_commute'), "CELL_CENTER", "NONE")
    r_employ_den = arcpy.PolygonToRaster_conversion(block_group, "Employ_D", os.path.join(output, 'r_employ_den'), "CELL_CENTER", "NONE")

    # Reclassify Pop, Emp, Commute using Jenks
    print("Starting Slices")
    arcpy.gp.Slice_sa(r_pop_den, os.path.join(output, 'rWS_PopDensity'), "5" ,"NATURAL_BREAKS", "1" )
    arcpy.gp.Slice_sa(r_employ_den, os.path.join(output, 'rWS_EmpDensity'), "5" ,"NATURAL_BREAKS", "1" )
    arcpy.gp.Slice_sa(r_commute, os.path.join(output, 'rWS_Commute'), "5" ,"NATURAL_BREAKS", "1" )
    print("Starting LC Reclass")
    # Reclassify Land Cover
    arcpy.gp.Reclassify_sa(os.path.join(inputs, 'ActiveLC'), "NLCD_Land_Cover_Class",
                           "'Developed, Low Intensity' 3;'Developed, Medium Intensity' 4;'Developed, High Intensity' "
                           "5;NODATA 1",
                           os.path.join(output, 'rWS_LandCover'), "DATA")

    # Build weighted sum table
    env.workspace = output
    ws_table = [[raster, "VALUE", 1] for raster in arcpy.ListRasters("rWS_*")]

    # Create weighted sum
    ws_table_obj = arcpy.sa.ws_table(ws_table)
    out_ws = arcpy.sa.WeightedSum(ws_table_obj)
    out_ws.save(os.path.join(output, "Weighted_Sum"))

    # Reclassify Weighted Sum 
    ws_slice = arcpy.gp.Slice_sa(out_ws, os.path.join(output, "ws_slice"), "5", "NATURAL_BREAKS", "1")

    # Zonal Statistics using Blocks
    zonal_stats = arcpy.gp.ZonalStatistics_sa(os.path.join(inputs, "Blocks"), "OBJECTID", ws_slice,
                                     os.path.join(output, "ZonalSt_Demand"), "MEAN", "DATA")
    
    # Reclassify Zonal Statistics
    final_demand = arcpy.gp.Slice_sa(zonal_stats, os.path.join(output, "FinalDemand"), "5", "NATURAL_BREAKS", "1")
    
    # Convert FinalDemand to Polygon
    arcpy.RasterToPolygon_conversion(final_demand, os.path.join(output, "Demand_Polygons"), "SIMPLIFY", "Value", "")
    
    print("--- %s seconds ---" % (time.time() - start_time))


# Example
demand(r"C:\Users\jj10048\Desktop\Projects\MSI\SupplyScriptTest\Demand.gdb\SW",
       r"C:\Users\jj10048\Desktop\Projects\MSI\SupplyScriptTest\Demand.gdb",
       r"C:\Users\jj10048\Desktop\Projects\MSI\SupplyScriptTest\Ped_Statewide.gdb")
