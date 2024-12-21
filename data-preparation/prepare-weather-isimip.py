#!/bin/python3

'''
This script prepares weather forcing for the COmmunity SWAT+ Model
(CoSWAT-Global) from ISIMIP datasets starting with ISIMIP-3a.

Author  : Celray James CHAWANDA
Date    : 14/07/2022
Contact : celray@chawanda.com
Licence : MIT
GitHub  : github.com/celray
'''

import multiprocessing
import struct
from datetime import datetime

import geopandas
import pandas
import rasterio
import os, sys
import numpy
from cjfx import (clip_features, create_path, download_file, exists, list_folders, python_variable,
                  extract_timeseries_from_netcdf, file_name, list_files, delete_file, ignore_warnings,
                  points_to_geodataframe, read_from, write_to, report, show_progress)
from osgeo import gdal, ogr

ignore_warnings()

# change working directory
me = os.path.realpath(__file__)
os.chdir(os.path.dirname(me))

import datavariables as variables

def save_ts(file_n, var, lon, lat, out_file, progress_count = None, progress_total = None):
    if exists(out_file):
        report(f"\t> {out_file} exists        ")

    else:
        if (not progress_count is None) and (not progress_total is None):
            pass
        else:
            report(f"\t> saving {out_file}        ")

        extract_timeseries_from_netcdf(file_n, var, lon, lat).to_csv(out_file)


def get_raster_value_for_coords(lon, lat, rasterio_array):
    row, col = rasterio_array.index(lon,lat)
    try:
        val = rasterio_array.read(1)[row,col]
    except:
        val = -999
    return(val)


def get_raster_value_for_coords_memory(lon, lat, rasterio_array):
    row, col = rasterio_array.index(lon,lat)
    try:
        val = rasterio_array.read(1)[row,col]
    except:
        val = -999
    return(val)


def write_station_weather_files(coord_, variable, coord_obj, coordinateElevs, rOw, cOl):
    '''
    function to write station weather files
    '''
    
    file_name_plus = f"O{str(coord_[0]).replace('.','').replace('-','M')}A{str(coord_[1]).replace('.','').replace('-','M')}.{extensions[variable]}"
    # print(file_name_plus)

    df = None
    df_tasmin = None

    create_df = True
    for year_range in available_years:
        fname_current = f"{ts_dir}/{variable}/{str(coord_[0])}_{str(coord_[1])}_{variable}_{year_range}.nc.csv"
        fname_current_tasmin = None

        if variable == 'tasmax':
            fname_current_tasmin = f"{ts_dir}/tasmin/{str(coord_[0])}_{str(coord_[1])}_tasmin_{year_range}.nc.csv"

        if create_df:
            df = pandas.read_csv(fname_current)
            if variable == 'tasmax':
                df_tasmin = pandas.read_csv(fname_current_tasmin)
            create_df = False
        else:
            df = pandas.concat([df, pandas.read_csv(fname_current)], axis=0)
            if variable == 'tasmax':
                df_tasmin = pandas.concat([df_tasmin, pandas.read_csv(fname_current_tasmin)], axis=0)

    if variable == 'hurs':
        df[variable] = df[variable] / 100
        
    if variable == 'rhs':
        df[variable] = df[variable] / 100
        
    elif variable == 'rlds':
        df[variable] = df[variable] * 0.0864    # currently solar radiation, rlds, is in W/m2 

    elif variable == 'pr':
        df[variable] = df[variable] * 86400     # kg/m2/day --> kg/m2 is 1 mm of water, 1 day is 86400 seconds

    elif variable == 'wnd':
        pass
    
    elif variable == 'tasmax':
        df['tasmax']  = df['tasmax'] - 273.15
        df['tasmin']  = df_tasmin['tasmin'] - 273.15

        df.tasmin = df.tasmin.astype(float)
                
    df['date'] = pandas.to_datetime(df['time'])
    df['year'] = df['date'].dt.year
    df['jday'] = df['date'].dt.strftime('%j')
    
    # sort by date
    df = df.sort_values(by=['date'])

    number_of_years = df['date'].dt.year.nunique()

    if variable == 'tasmax':
        df = df[['year', 'jday', 'tasmin', variable]]
        final_ts = df.to_string(buf=None, columns=None, col_space=[4,6,10, 10], header=False, index=False, na_rep='NaN', formatters=None, float_format=None, sparsify=None, index_names=False, justify=None, max_rows=None, max_cols=None, show_dimensions=False, decimal='.', line_width=None, min_rows=None, max_colwidth=None, encoding=None)
    else:
        df = df[['year', 'jday', variable]]
        final_ts = df.to_string(buf=None, columns=None, col_space=[4,6,10], header=False, index=False, na_rep='NaN', formatters=None, float_format=None, sparsify=None, index_names=False, justify=None, max_rows=None, max_cols=None, show_dimensions=False, decimal='.', line_width=None, min_rows=None, max_colwidth=None, encoding=None)

    elev = -999
    try:
        elev = coordinateElevs[rOw,cOl]
    except:
        elev = -999

    new_stringplus = stringplus.format(
        filename    = f'{file_name_plus}:' ,                                            
        comments    = f'{extensions[variable]} file for station {file_name(file_name_plus, extension=False)}' ,                                            
        yr_nmbr     = str(number_of_years).rjust(4),                                            
        lat         = str(coord_[1]).rjust(10),                                            
        lon         = str(coord_[0]).rjust(10) ,                                            
        elev        = f'{elev}'.rjust(10),                                                
    )

    fnameplus = f"../model-data/{region}/weather/swatplus/{scenario}/O{str(coord_[0]).replace('.','').replace('-','M')}A{str(coord_[1]).replace('.','').replace('-','M')}.{extensions[variable]}"

    final_string = new_stringplus + final_ts
    report(f"\t> writing {fnameplus}")
    write_to(fnameplus, final_string)

    return True




if __name__ == '__main__':

    for scenario in variables.weather_pr_links_list:

        if not variables.prepare_weather:
            sys.exit()
        
        if len(sys.argv) < 2:
            # print(f"! select a region for which to prepare the dataset. options are: {', '.join(list_folders('./resources/regions/'))}\n")
            regions = list_folders('./resources/regions/')
        else:
            regions = sys.argv[1:]


        print('# preparing weather\n')
            
        details = {
            'auth': variables.final_proj_auth,
            'code': variables.final_proj_code,
            'scenario': scenario,
        }

        extensions = {
                'hurs'         : 'hmd',
                'rhs'          : 'hmd',
                'sfcwind'      : 'wnd',
                'sfcWind'      : 'wnd',
                'wind'         : 'wnd',
                'pr'           : 'pcp',
                'rlds'         : 'slr',
                'tasmin_tasmax': 'tmp',
                'tasmin'       : 'tmp',
                'tasmax'       : 'tmp',
        }

        stringplus = \
            '{filename}: {comments}\n' + \
            'nbyr     tstep       lat       lon      elev\n' + \
            '{yr_nmbr}         0{lat}{lon}{elev}\n'

        # prepare shapefile
        data = []

        if variables.prepare_weather:
            for latitude in numpy.arange(-85.25, 86.25, variables.weather_resolution):
                for longitude in numpy.arange(-179.25,180.25, variables.weather_resolution):
                    data.append([latitude, longitude])

            cols = ['longitude', 'latitude']
            points_to_geodataframe(data, out_shape=variables.weather_points_all, columns=cols)

        

        ts_dir = create_path(f'./weather-ws/time_series/{scenario}/')

        for region in regions:
            # pool = multiprocessing.Pool(variables.processes)

            details['region'] = region

            # clip shapefile
            print(f'\t> cliping weather station points to {variables.cutline.format(**details)}')
            final_point_df = clip_features(variables.cutline.format(**details), variables.weather_points_all, "./resources/regions/{region}/weather-station-points-{auth}-{code}.gpkg".format(**details))
            

            print(f'\t> enumerating available variables')
            weather_variables = []
            available_years = []
            # jobs = []
            # write_to(f'./weather-ws/{region}_file_list.txt', '')
            for fn in (list_files(f"./weather-ws/download/{scenario}/", 'nc') + list_files(f"./weather-ws/download/{scenario}/", 'nc4')) :
                cVariable    = file_name(fn, extension = False).split('_')[0]
                year_range  = f"{file_name(fn, extension = False).split('_')[-2]}-{file_name(fn, extension = False).split('_')[-1]}"
                if not cVariable in weather_variables: weather_variables.append(cVariable)
                if not year_range in available_years: available_years.append(year_range)
            
            # available_years = ['1971-1980', '1981-1990', '1991-2000', '2001-2010', '2011-2016']

            # if variables.redo_weather:
            #     csv_files = []
            #     for variable in weather_variables:
            #         print(f'\t> listing time series csv files for {variable}')
            #         csv_files += list_files(f'{ts_dir}/{variable}/', 'csv')
            #     python_variable('save', f'./weather-ws/pikle/csv_files-{scenario}.pickle', csv_files)
            # else:
            #     if exists(f'./weather-ws/pikle/csv_files-{scenario}.pickle'):
            #         csv_files = python_variable('load', f'./weather-ws/pikle/csv_files-{scenario}.pickle')
            #     else:
            #         csv_files = []
            #         for variable in weather_variables:
            #             print(f'\t> listing time series csv files for {variable}')
            #             csv_files += list_files(f'{ts_dir}/{variable}/', 'csv')

            #         python_variable('save', f'./weather-ws/pikle/csv_files-{scenario}.pickle', csv_files)

            raster_data = rasterio.open('./dem-ws/aster/global-aster.tif')
            final_point_df_reproj = final_point_df.to_crs('{auth}:{code}'.format(**details))

            # jobs = []

            coordinates_selected = []
            region_points = clip_features(
                variables.cutline.format(**details),
                "./resources/regions/{region}/weather-station-points-{auth}-{code}.gpkg".format(**details),
                f'./weather-ws/{region}-points.gpkg'
            )

            for index, row in region_points.iterrows():
                coordinates_selected.append(f"{row['geometry'].x},{row['geometry'].y}")

            coordinates_ = {}
            for index, row in final_point_df.iterrows():
                if not f"{row['geometry'].x},{row['geometry'].y}" in coordinates_selected:
                    continue
                coordinates_[(row['geometry'].x, row['geometry'].y)] = final_point_df_reproj.loc[index, 'geometry']
            
            print(f'\t> writing files for {region}...')

            [delete_file(fn) for fn in list_files("../model-data/{region}/weather/swatplus/{scenario}/".format(**details))]

            counter = 0
            all = len(coordinates_) * (len(weather_variables) - 1)

            station_coodinate_elevations = raster_data.read(1)

            # this needs parallelisation! mua hahahahahahaha
            station_jobs = []
            for coordIndex in coordinates_:
                coordObject = coordinates_[coordIndex]

                for currVariable in weather_variables:
                    if currVariable   == 'tasmin': continue
                    
                    
                    
                    counter += 1
                    show_progress(counter, all, string_before = "      ", string_after=f"{coordIndex}  ")
                    # elevation = get_raster_value_for_coords(coordObject.x, coordObject.y, raster_data)

                    row__, col__ = raster_data.index(coordObject.x, coordObject.y)

                    station_jobs.append([
                        coordIndex,
                        currVariable,
                        coordObject,
                        station_coodinate_elevations,

                        row__,
                        col__,

                    ])
            
            processing_pool = multiprocessing.Pool(variables.processes)
            processing_pool.starmap(write_station_weather_files, station_jobs)
            processing_pool.close()
            processing_pool.join()




            tmp_files = list_files(f"../model-data/{region}/weather/swatplus/{scenario}/", 'tmp'); tmp_files = [file_name(fn, extension=True) for fn in tmp_files] 
            pcp_files = list_files(f"../model-data/{region}/weather/swatplus/{scenario}/", 'pcp'); pcp_files = [file_name(fn, extension=True) for fn in pcp_files] 
            slr_files = list_files(f"../model-data/{region}/weather/swatplus/{scenario}/", 'slr'); slr_files = [file_name(fn, extension=True) for fn in slr_files] 
            hmd_files = list_files(f"../model-data/{region}/weather/swatplus/{scenario}/", 'hmd'); hmd_files = [file_name(fn, extension=True) for fn in hmd_files] 
            wnd_files = list_files(f"../model-data/{region}/weather/swatplus/{scenario}/", 'wnd'); wnd_files = [file_name(fn, extension=True) for fn in wnd_files] 

            tmp_cli_string = "tmp.cli: Temperature file names - file written by SWAT+ CoSWAT-GM Data Writer\nfilename\n"
            for tmp_fn in tmp_files:
                tmp_cli_string += f"{tmp_fn}\n"


            pcp_cli_string = "pcp.cli: Precipitation file names - file written by SWAT+ CoSWAT-GM Data Writer\nfilename\n"
            for pcp_fn in pcp_files:
                pcp_cli_string += f"{pcp_fn}\n"



            slr_cli_string = "slr.cli: Solar radiation file names - file written by SWAT+ CoSWAT-GM Data Writer\nfilename\n"
            for slr_fn in slr_files:
                slr_cli_string += f"{slr_fn}\n"



            hmd_cli_string = "hmd.cli: Relative humidity file names - file written by SWAT+ CoSWAT-GM Data Writer\nfilename\n"
            for hmd_fn in hmd_files:
                hmd_cli_string += f"{hmd_fn}\n"



            wnd_cli_string = "wnd.cli: Wind speed file names - file written by SWAT+ CoSWAT-GM Data Writer\nfilename\n"
            for wnd_fn in wnd_files:
                wnd_cli_string += f"{wnd_fn}\n"

            write_to(f"../model-data/{region}/weather/swatplus/{scenario}/tmp.cli", tmp_cli_string)
            write_to(f"../model-data/{region}/weather/swatplus/{scenario}/pcp.cli", pcp_cli_string)
            write_to(f"../model-data/{region}/weather/swatplus/{scenario}/slr.cli", slr_cli_string)
            write_to(f"../model-data/{region}/weather/swatplus/{scenario}/hmd.cli", hmd_cli_string)
            write_to(f"../model-data/{region}/weather/swatplus/{scenario}/wnd.cli", wnd_cli_string)

            print('\n\n')

