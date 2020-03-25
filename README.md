# MPT
## Multimodal Prioritization Tool

The Multimodal Prioritization Tool (MPT) uses spatial analysis and data from various sources to identify the suitability of multimodal projects. The goal is to identify the roads and communities that would benefit most from a multimodal project and the feasibility of projects based on the existing physical features and infrastructure of road segments. This is documentation on the process.


## Four Components of the MPT

The composite score of the MPT or the Multimodal Priority Index (MPI) is comprised of the scores from four layers: Level of Traffic Stress, Equity, Safety, and Demand.


## Level of Traffic Stress (LTS)

Inputs: Trims Tables (RD_SGMNT, TRAFFIC, GEOMETRICS, RDWAY_DESCR)

This layer looks at qualitative features of road segments including speed limit, pavement width, number of lanes, traffic volume, sidewalks and bike lanes to determine a stress score. To create this layer, run the LTS script tool. Arterials and collectors are treated separately, so this tool is ran for each functional class. You can choose the functional class using the drop-down in the tool. The tool also allows you to create the LTS layer for individual planning areas or groups. The current way we are doing things is separating MPO and Rural areas. So the LTS script will be ran four times in order to create a statewide output — All MPO Collectors, All MPO Arterials, All RPO Collectors, All RPO Arterials. 

See script documentation for more detailed information on the operations taking place.

Note: This is very similar to how we create the Infrastructure layer (INFRA) for the Pedestrian Road Safety Initiative (PRSI).

### Create Unique IDs

The LTS output is what will eventually become the final network. It is important to set up a unique ID (UID) at this stage, because we will be segmenting the network further and will use this UID to link the data to the correct segment. The format I’ve come up with is a simple field calculation using planning area information, functional class, and OBJECTID. For example, if I were doing MPO collectors I would create a field in the final output (‘Overlay_E’) called ‘UID’. Then do the following field calculation:

`'U_COL_'+str(!OBJECTID!)`

The ‘U’ stands for ‘Urban’.

If I were doing RPO arterials, I would do the following:

`'R_ART_'+str(!OBJECTID!)`

The ‘R’ stands for ‘Rural’

Any convention will work as long as there is a way to distinguish between planning areas and functional classification.


## Demand

Inputs: Planning Areas (Polygon), NLCD Land Cover Class (Raster), Active Businesses (Point), Block Groups w/ Pop Density - Emp Density - Active Commute (Polygon), Colleges (Point), Supplemental Colleges (Point), Private Schools (Point), Public Schools (Point), Transit (Polyline)

The Demand layer is spatially derived. It looks at points of attraction including active businesses, transit stops, colleges, schools, and hospitals to develop a score based on the distance to these points. It also takes into account population density, employment density, and commuter information. To create this layer, run the demand.py script. This script uses the Euclidean Distance tool to generate a series of rasters from the vector inputs. The rasters created indicate the distance from the vector feature to the the surrounding areas and are then reclassified 1-5 based on set distance groups. See the scoring table below.

| Distance in Feet (Pedestrian) | Score | Distance in Feet (Bike)       | Score |
| ----------------------------- | ----- | ----------------------------- | ----- |
| 0 - 1320                      | 5     | 0 - 5280                      | 5     |
| 1320 - 2640                   | 4     | 5280 - 10560                  | 4     |
| 2640 - 3960                   | 3     | 10560 - 15840                 | 3     |
| 3960  - 5280                  | 2     | 15840 - 21120                 | 2     |
| 5280 +                        | 1     | 21120 +                       | 1     |


Three rasters are created from the block group polygons using ‘Pop_Density’, ‘Employ_Density’, and ‘Active_Commute’ as the scores. These raster are reclassified using the Slice tool. 

The Land Cover Class layer is reclassified using the following criteria:

| Level of Development        | Score |
| --------------------------- | ----- |
| Developed, High Intensity   | 5     |
| Developed, Medium Intensity | 4     |
| Developed, Low Intensity    | 3     |
| No Data                     | 1     |

A weighted sum of all of the above rasters is created and then reclassified into 5 classes using Slice tool (Natural Breaks).

Zonal Statistics is performed using the block groups as the zones and the mean value as the statistic. This layer is then reclassified once more using the Slice tool (Natural Breaks) 

The output of the script is a polygon layer with a score 1 - 5. See script documentation for more information.

## Safety

Inputs: Crash Layer, LTS Layers

Once you have a LTS road network and crash data you can use the Safety Scoring tool to calculate the raw severity and raw frequency scores. The tool does the work for you, but below is an explanation of how the scores are derived.

The tool does an overlay of the Crash Layer and LTS layer so that we can apply the crash events to the proper segment.  A field is added and calculated called “BASIC_CRASH”. This field reflects the number of crashes that occur per segment that do not involve injury or death. Then it calculates the crash severity using the following formula:

`Raw Severity (RAW_SEV)  = (TOTAL KILLED * 5 + TOTAL INCAP* 4 + TOTAL OTHER * 3 + BASIC * 2)`

Next, the tool creates Summary Statistics of the overlay, calculating the sum of the Raw Severity (RAW_SEV) and the count of the case numbers (CASENO) using “UID” as the “Case field”.

This gives us the Severity (RAW_SEV) and Frequency (RAW_FREQ) values for each segment in the LTS. 

You can join the Summary Statistics layer to the LTS by “UID”.

Calculate the Safety Score by taking the average of the Severity and Frequency.


## Equity

Inputs: EJ Layer, LTS

The EJ Layer is created outside of this tool. The layer has an EJ Index field which is is based on demographics including poverty level, minority populations, zero car households, age, disability, education level, low English proficiency. We use the EJ Index to calculate the Equity score. First we scale the values 1 to 5, treating MPO and Rural areas separately. You can use the Scale Feature tool for this. To calculate the Equity Score for the LTS segments use the Weighted Average method described in this document.


### Weighted Average Method

This is a method to get the weighted average of a polygon score onto a road segment that passes through multiple polygons. There are other ways to do this, but this is the way I came up with so we could avoid doing it spatially.

Note: You must have a unique ID (“UID”) before proceeding. If you do not go through the Create Unique IDs process described in this document.  Input Class Features is your LTS layer. Zone features are the polygon layers that have the scores you wish to apply to the LTS segments. Case Fields should be “UID”.

Step 1. Tool → Tabulate Intersection

This segments the LTS Layer at the polygon boundaries and provides a length of the segment and the percentage of the segment that falls in a given polygon.

![](https://paper-attachments.dropbox.com/s_8A2862899E9F54AC38A59AC29AFD0CEEF1083FEF37BCE17529AC3E3AA1C63DFD_1568122745656_TabInter.PNG)
![](https://paper-attachments.dropbox.com/s_8A2862899E9F54AC38A59AC29AFD0CEEF1083FEF37BCE17529AC3E3AA1C63DFD_1568122745665_tabinttable.PNG)


Step 2. Create ‘wScore’ field and calculate weighted score using Tool → Calculate Field

![](https://paper-attachments.dropbox.com/s_8A2862899E9F54AC38A59AC29AFD0CEEF1083FEF37BCE17529AC3E3AA1C63DFD_1568122865766_add+field.PNG)
![](https://paper-attachments.dropbox.com/s_8A2862899E9F54AC38A59AC29AFD0CEEF1083FEF37BCE17529AC3E3AA1C63DFD_1568122865772_CalcField.PNG)
![](https://paper-attachments.dropbox.com/s_8A2862899E9F54AC38A59AC29AFD0CEEF1083FEF37BCE17529AC3E3AA1C63DFD_1568122865781_tabinttable+2.PNG)


Step 3.  Tool → Summary Statistics

![](https://paper-attachments.dropbox.com/s_8A2862899E9F54AC38A59AC29AFD0CEEF1083FEF37BCE17529AC3E3AA1C63DFD_1568122972377_summary_stats.PNG)
![](https://paper-attachments.dropbox.com/s_8A2862899E9F54AC38A59AC29AFD0CEEF1083FEF37BCE17529AC3E3AA1C63DFD_1568122972383_sumstatstable.PNG)


Step 4. Join Tables

![](https://paper-attachments.dropbox.com/s_8A2862899E9F54AC38A59AC29AFD0CEEF1083FEF37BCE17529AC3E3AA1C63DFD_1568123162793_join.PNG)



## Things To Improve

Non-coincident Polygons
Setting up some type of topology checks on our polygon layers will be beneficial to the process. Some polygons are not coincident or they do not totally encompass our road network. This causes issues with the weighted average process.

Lost Fields
Somewhere in the process some field information is being lost. For example, I’ve had trouble with ‘rte_nme’. My quick fix has been to rejoin the tables with the missing information, but it would be worth it to take some time and fix the problem.

Model Criteria (features) Overlap
It’s possible that some features of this model are being accounted for more than once. I think it would be worth running a PCA to identify possible model features with high correlation.



