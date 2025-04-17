#!/bin/python3

'''
This script prepares the lake data for the whole world filtered by areal threshold.
It is part of the data preparation scripts for the  COmmunity SWAT+ Model (CoSWAT-Global)
development. A project aimed at providing a community contributed global SWAT+ model
initiated and led by Celray James CHAWANDA.

Author  : Celray James CHAWANDA
Date    : 19/07/2022
Contact : celray@chawanda.com
Licence : MIT
GitHub  : github.com/celray
'''

# imports
from cjfx import clip_features, geopandas, create_path, list_folders, ignore_warnings
import time, sys, os
from shapely.geometry import Polygon, MultiPolygon

ignore_warnings()


# functions
def removeHoles(thisGeometry):
    # leave empty geoms alone
    if thisGeometry.is_empty:
        return thisGeometry

    geomType = thisGeometry.geom_type
    if geomType == 'Polygon':
        # rebuild from exterior only
        return Polygon(thisGeometry.exterior)

    if geomType == 'MultiPolygon':
        # iterate over .geoms, not the object itself
        polys = [Polygon(poly.exterior) for poly in thisGeometry.geoms]
        return MultiPolygon(polys)

    # fallback for other types (Point, LineString, etc.)
    return thisGeometry


# change working directory
me = os.path.realpath(__file__)
os.chdir(os.path.dirname(me))

import datavariables as variables

print('\n# preparing lakes data...\n')
if len(sys.argv) < 2:
    regions = list_folders('./resources/regions/')
    print(f"  > using all regions: {', '.join(regions)}\n")
else:
    regions = sys.argv[1:]
    print(f"  > using regions: {', '.join(regions)}\n")
    


details = {
    'auth': variables.final_proj_auth,
    'code': variables.final_proj_code,
}

input_gdf               = geopandas.read_file(f"{variables.grand_and_lakes}")

for region in regions:
    details['region'] = region
    create_path(variables.grand_final_shp.format(**details))

    regionfn                = "./resources/regions/{region}/bounding-box-{auth}-{code}.gpkg".format(**details)
    regionfn                = "./resources/regions/{region}/outlets-buffer.gpkg".format(**details)

    mask_gdf                = geopandas.read_file(regionfn)
    clippedReservoirs       = input_gdf.clip(mask_gdf.to_crs(input_gdf.crs))

    clippedReservoirs               = clippedReservoirs.to_crs("{auth}:{code}".format(**details))
    clippedReservoirs["calcAreas"]  = clippedReservoirs.geometry.area / 1000000
    clippedReservoirs["calcVol"]    = clippedReservoirs.calcAreas * 2.1
    clippedReservoirs["RES"]        = 1

    clippedReservoirs = clippedReservoirs[clippedReservoirs.calcAreas > (variables.grand_lake_thres)]

    # Assuming 'gdf' is your GeoDataFrame with polygons
    clippedReservoirs['geometry'] = clippedReservoirs['geometry'].apply(removeHoles)

    clippedReservoirs.to_file(variables.grand_final_shp.format(**details))
    clippedReservoirs.to_file(variables.grand_final_gpkg.format(**details), driver = 'GPKG')
