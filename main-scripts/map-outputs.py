#!/bin/python3

'''
this script coordinates the mapping of the COmmunity SWAT+ Model
(CoSWAT-Global) results. A project aimed at providing a community
contributed global SWAT+ model initiated and led by Celray James
CHAWANDA.

Author  : Celray James CHAWANDA
Date    : 23/02/2023

Contact : celray@chawanda.com
          celray.chawanda.com

Licence : MIT 2023
GitHub  : github.com/celray
'''

import os
import sys
from cjfx import *

ignore_warnings()

# change working directory
me = os.path.realpath(__file__)
os.chdir(os.path.dirname(me))

import datavariables as variables



def make_gpkg(region, version, map_columns, map_log):

    print(f'\t> mapping {region}')

    hrus2shapefile_fn   = f'../model-setup/CoSWATv{version}/{region}/Watershed/Shapes/hrus2.shp'
    hrus_wb_aa_fn       = f'../model-setup/CoSWATv{version}/{region}/Scenarios/Default/TxtInOut/hru_wb_aa.txt'

    # check if necessay files exist
    if not (exists(hrus2shapefile_fn) and exists(hrus_wb_aa_fn)):
        write_to(map_log, f'{datetime.datetime.now()} - ! cannot map results from {region}', mode='a')
        print(f'\t! cannot map results from {region}')
        print(f'\t  - check that {hrus2shapefile_fn} exists')
        print(f'\t  - check that {hrus_wb_aa_fn} exists')
        return None
    
    hrus_gpd    = geopandas.read_file(hrus2shapefile_fn)
    
    hrus_gpd['region'] = \
                f'{region}'

    wb_pd       = pandas.read_csv(hrus_wb_aa_fn, skiprows=1, delim_whitespace=True, low_memory=False)
    wb_pd       = wb_pd[wb_pd['jday'] != 'mm']


    wb_pd['gis_id']     = pandas.to_numeric(wb_pd['gis_id'], errors='coerce')
    hrus_gpd['HRUS']    = pandas.to_numeric(hrus_gpd['HRUS'], errors='coerce')

    for map_col in map_columns:
        wb_pd[map_col] = pandas.to_numeric(wb_pd[map_col], errors='coerce')

    merged_pd   = pandas.merge(hrus_gpd, wb_pd, how = 'inner', left_on='HRUS', right_on='gis_id')

    maps_gpd    = geopandas.GeoDataFrame(merged_pd, geometry='geometry', crs = hrus_gpd.crs)
    
    if len(maps_gpd.index) == 0:
        print(f'\t! cannot map results from {region}')
        print(f'\t  - check that the model was fully run')
        return None

    fn = f'../model-setup/CoSWATv{version}/{region}/Evaluation/Shape/wb_map_vars.gpkg'
    create_path(fn)
    delete_file(fn, v = False)
    maps_gpd.to_file(fn)

    return maps_gpd





args = sys.argv

if __name__ == "__main__":

    if len(sys.argv) >= 3: regions = sys.argv[2:]
    else: regions = list_folders("../data-preparation/resources/regions/")

    version_             = args[1]

    map_columns_         = ["precip", "snofall", "snomlt", "surq_gen", "latq", "wateryld", "perc", "et", "ecanopy", "eplant", "esoil", "surq_cont", "cn", "sw_init", "sw_final", "sw_ave", "sw_300", "sno_init", "sno_final", "snopack", "pet", "qtile", "irr", "surq_runon", "latq_runon", "overbank", "surq_cha", "surq_res", "surq_ls", "latq_cha", "latq_res", "latq_ls", "satex", "satex_chan", "sw_change", "lagsurf", "laglatq", "lagsatex"]
    out_shape_map_fn    = f'../model-outputs/version-{version_}/maps/shapefiles/map-data.gpkg'

    cumulative = None

    if not exists(out_shape_map_fn):
        variables.output_re_shape = True

    map_log_ = write_to(f'../model-outputs/version-{version_}/maps/map.log', '', mode='o')

    jobs = []
    if variables.output_re_shape:
        for region_ in regions:
            jobs.append([region_, version_, map_columns_, map_log_])
            
            
        # Create a multiprocessing Pool
        with multiprocessing.Pool(20) as pool:
            results = [pool.apply_async(make_gpkg, job) for job in jobs]

            for result in results:
                maps_gpd_ = result.get() 
                if maps_gpd_ is None: continue

                if cumulative is None:
                    cumulative = maps_gpd_
                else:
                    cumulative = geopandas.GeoDataFrame(pandas.concat([cumulative, maps_gpd_], ignore_index=True), geometry='geometry', crs = maps_gpd_.crs)


    else:
        print(f'\t> reading previous cumulative output vector data')
        cumulative = geopandas.read_file(out_shape_map_fn)


    if not cumulative is None:
        if variables.output_re_shape:
            create_path(out_shape_map_fn)
            delete_file(out_shape_map_fn, v = False)
            cumulative.to_file(out_shape_map_fn)

        print(f'\t> creating raster files')
        # rasterise_columns = ["precip", "snofall", "snomlt", "surq_gen", "latq", "wateryld", "perc", "et", "ecanopy", "eplant", "esoil", "cn", "sw_init", "sw_final", "sw_ave", "snopack", "pet", "qtile", "irr", "surq_runon", "latq_runon", "overbank", "surq_cha", "surq_res", "latq_cha", "latq_res", "latq_ls", "satex", "sw_change", "lagsurf", "laglatq"]
        rasterise_columns = ["precip", "snofall", "snomlt", "surq_gen", "latq", "wateryld", "perc", "et", "ecanopy", "eplant", "esoil", "cn", "sw_init", "sw_final", "sw_ave", "snopack", "pet"]
        for col_name in rasterise_columns:
            out_raster = f'../model-outputs/version-{version_}/maps/raster-maps/{col_name}.tif'
            print(f'\t - {out_raster}')
            create_path(out_raster)
            rasterise_shape(out_shape_map_fn, col_name, out_raster, f'../data-preparation/dem-ws/aster/global-aster.tif')
        
        