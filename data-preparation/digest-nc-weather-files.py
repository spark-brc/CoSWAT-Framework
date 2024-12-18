#!/bin/python3

from cjfx import *
import numpy

ignore_warnings()

# change working directory
me = os.path.realpath(__file__)
os.chdir(os.path.dirname(me))

from resources import datavariables as variables

# functions

def save_ts_csv(time_stamps: pandas.DataFrame, ts_values, variable_name: str, out_file_name: str) -> None:
    time_stamps[variable_name]  = ts_values
    time_stamps.to_csv(out_file_name, index = False)


if __name__ == '__main__':

    for scenario in variables.weather_pr_links_list:
        ds_f_names  = list_files(f'./weather-ws/download/{scenario}/', 'nc')
        ds_f_names  += list_files(f'./weather-ws/download/{scenario}/', 'nc4')

        ts_dir      = f'./weather-ws/time_series/{scenario}'

        # # listing existing csvs
        # all_csvs = list_files(f'{ts_dir}/')

        # current_fns = []

        # if variables.redo_weather:
        #     count_number = 0; end_number = len(all_csvs)
        #     print(f"> there are {end_number} csv files in total")
        #     for fn_ in all_csvs:
        #         count_number += 1
        #         # show_progress(count_number, end_number, bar_length = 300, string_before = "  ")
        #         current_fns.append(file_name(fn_))

        # ts_dir      = './tmp_dir'

        # download weather nc_files that do not exist
        if variables.redo_weather:
            download_list = []
            download_string = 'this file is created automatically\n\n'

            for line in read_from(variables.weather_pr_links_list[scenario]) + read_from(variables.weather_hurs_links_list[scenario]) + \
                read_from(variables.weather_tasmin_links_list[scenario]) + read_from(variables.weather_tasmax_links_list[scenario]) + \
                read_from(variables.weather_wind_links_list[scenario]) + read_from(variables.weather_rlds_links_list[scenario]):
                    line = line.strip()
                    if variables.weather_redownload:
                        download_list.append([f'{line}', f'./weather-ws/download/{scenario}/'])
                        download_string += f'{line}\n'
                    elif not exists(f'./weather-ws/download/{scenario}/{file_name(line)}'):
                        download_list.append([f'{line}', f'./weather-ws/download/{scenario}/'])
                        download_string += f'{line}\n'

            create_path(f'./weather-ws/download/{scenario}/')

            write_to("./weather-ws/download_links.txt", download_string)
            
            # extract weather
            pool = multiprocessing.Pool(7)

            results = pool.starmap_async(download_file, download_list)
            results.get()
            pool.close()
            print()

            ds_f_names  = list_files(f'./weather-ws/download/{scenario}/', 'nc')
            ds_f_names  += list_files(f'./weather-ws/download/{scenario}/', 'nc4')


        print('\n# exporting netcdf files to csv timeseries')
        create_path(f'{ts_dir}/')

        pool = multiprocessing.Pool(variables.processes)

        main_counter = 0; end_total = len(ds_f_names)
        for ds_fn in ds_f_names:
            main_counter += 1

            # f_names_to_do = [

            # ]

            # do_it = False

            # for f_name_todo in f_names_to_do:
            #     if f_name_todo in ds_fn:
            #         do_it = True
            #         break

            # if not do_it: continue
            # if main_counter < 100: continue

            # if not 'pr' in ds_fn: continue
            # if not '1941' in ds_fn: continue

            report(f'\t> digesting {ds_fn} - ({main_counter} of {end_total})   ')
            fn_parts    = file_name(ds_fn, extension=False).split('_')

            # ipsl-cm6a-lr_r1i1p1f1_w5e5_ssp585_hurs_global_daily_2061_2070.nc

            # tasmin_gswp3-ewembi_1981_1990.nc4
            var_name    = fn_parts[-5] if scenario != "observed" else fn_parts[0]
            yr_end      = fn_parts[-1] if scenario != "observed" else fn_parts[-1].split('.')[0]
            yr_start    = fn_parts[-2] if scenario != "observed" else fn_parts[-2].split('-')[0]



            ds = xarray.open_dataset(ds_fn)

            time_dataframe_col = ds.time.to_dataframe()

            longitudes  = list(ds.lon.data)
            latitudes   = list(ds.lat.data)

            result = ds[var_name].to_numpy()

            print()
            dt_obj  = []
            end     = result.shape[2]
            count   = 0
            
            for x in range(0, result.shape[2]):
                t_stamp_at_t = datetime.datetime.now()
                jobs    = []
                copy_jobs = []
                for y in range(0, result.shape[1]):
                    old_fn_to_fix = f'{ts_dir}/{longitudes[x]}_{latitudes[y]}_{var_name}_{yr_start}-{yr_end}.nc.csv'
                    out_fn = f'{ts_dir}/{var_name}/{longitudes[x]}_{latitudes[y]}_{var_name}_{yr_start}-{yr_end}.nc.csv'
                    if (not exists(out_fn)) or variables.redo_weather:
                        # if file_name(out_fn) in current_fns: continue
                        
                        # if exists(old_fn_to_fix):
                        #     copy_jobs.append([old_fn_to_fix, out_fn, True, False, True])
                        # else:
                        #     if not exists(out_fn):
                        create_path(out_fn)
                        jobs.append([time_dataframe_col, result[:,y,x], var_name, out_fn])

                        # save_ts_csv(time_dataframe_col, result[:,y,x], var_name, out_fn)
                
                results_ = pool.starmap_async(save_ts_csv, jobs)
                results_.get()
                # results_ = pool.starmap_async(copy_file, copy_jobs)
                # results_.get()

                count += 1
                dt_obj.append(datetime.datetime.now() - t_stamp_at_t)
                if len(dt_obj) > 100: del dt_obj[0]
                show_progress(count, end, bar_length = 100, string_before='\t  progress ', dt = dt_obj, string_after=f'{x + 1} of {len(longitudes)} (longitude = {longitudes[x]})')

            print('\n\n')

        pool.close()

        print()
