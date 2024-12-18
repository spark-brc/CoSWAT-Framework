#!/bin/python3

'''
This script runs the COmmunity SWAT+ Model
(CoSWAT-Global) one by one.

Author  : Celray James CHAWANDA
Date    : 14/07/2022
Contact : celray@chawanda.com
Licence : MIT
GitHub  : github.com/celray
'''

import os, sys, platform, shutil
from cjfx import list_folders, exists, write_to, sqlite_connection, list_files, file_name, copy_file, show_progress, goto_dir, pandas, sqlite3, ignore_warnings, download_file

ignore_warnings()

if __name__ == '__main__':

    # change working directory
    goto_dir(__file__)

    # get model setup version
    version = sys.argv[1]

    if not exists(f"../model-setup/CoSWATv{version}"):
        print(f'\t! the version CoSWATv{version} does not exist')
        sys.exit(1)

    # get regions 
    if len(sys.argv) >= 3: regions = sys.argv[2:]
    else: regions = list_folders("../data-preparation/resources/regions/")

    for region in regions:
                    
        # set up api and project variables

        # download weatherGen if it does not exist
        if not exists('../data-preparation/resources/swatplus_wgn.sqlite'):
            
            if not exists('../data-preparation/resources/swatplus_wgn.zip'):
                print('\n\t> downloading weather generator database because it does not exist in your system')
                download_file("https://plus.swat.tamu.edu/downloads/swatplus_wgn.zip", '../data-preparation/resources/swatplus_wgn.zip')

            shutil.unpack_archive('../data-preparation/resources/swatplus_wgn.zip', '../data-preparation/resources/')
        
        if exists('/root/.local/share/SWATPlus/SWATPlusEditor/resources/app.asar.unpacked/static/api_dist/swatplus_api'):
            copy_file('/root/.local/share/SWATPlus/SWATPlusEditor/resources/app.asar.unpacked/static/api_dist/swatplus_api',
                      '../data-preparation/resources/swatplus_api', replace=True)

        api              = f'../data-preparation/resources/swatplus_api' if platform.system() == "Linux" else None
        project_db       = f'../model-setup/CoSWATv{version}/{region}/{region}.sqlite'
        datasets_db_file = f'../data-preparation/resources/swatplus_datasets.sqlite'
        weather_dir      = f'../model-data/{region}/weather/swatplus/observed'
        other_scenarios  = [dn for dn in list_folders(f'../model-data/{region}/weather/swatplus/') if dn != 'observed']
        txtinout_dir     = f'../model-setup/CoSWATv{version}/{region}/Scenarios/Default/TxtInOut'
        weather_wgn_db   = f'../data-preparation/resources/swatplus_wgn.sqlite'; weather_wgn_db = os.path.abspath(weather_wgn_db)
        editor_version   = f'2.3.3'
        db_sqlite        = sqlite_connection(project_db) 
        db_sqlite.connect()

        print('')

        if not exists(project_db):
            print(f'\t! {region} does not exist in CoSWATv{version}, skipping')
            continue
        
        try:
            cnx = sqlite3.connect(project_db)
            project_info = pandas.read_sql_query("SELECT * FROM project_config", cnx).iloc[0].to_dict()
        except:
            print(f'\t! {region} from CoSWATv{version} cannot be processed, skipping')
            continue
        
        if not project_info['hrus_done'] == 1: 
            print(f'\t! HRUs for {region} (CoSWATv{version}) have not been created, skipping')
            continue
        
        if api is None:
            raise ValueError('API cannot be of type "None", please add api location for SWAT Editor')


        db_sqlite    = sqlite_connection(project_db) 
        db_sqlite.connect()


        db_sqlite.cursor.execute(f"UPDATE project_config SET editor_version = '{editor_version}' WHERE id='1';")

        # update project_config tables based on csv.
        # this is a workaround
        """
        I have patched the swatplus_api's import_gis.py in the function insert_landuse with this:


		# start cjames edit
		import os
		os.system(f'python3 ../data-preparation/swatplus_api_patch.py "{self.project_db_file}"')
		# end cjames edit

        """

        db_sqlite.commit_changes()

        # set up project
        command  = f'setup_project '
        command += f"--project_db_file {project_db} "
        command += f"--delete_existing n "
        command += f"--project_name {region} "

        command += f"--datasets_db_file {datasets_db_file} "
        command += f"--constant_ps n "
        command += f"--is_lte n "
        command += f"--update_project_values n "
        command += f"--reimport_gis n "
        command += f"--editor_version {editor_version} "
        
        os.system(command = f'{api} {command}')

        db_sqlite.cursor.execute(f"UPDATE project_config SET editor_version = '{editor_version}' WHERE id='1';")
        db_sqlite.commit_changes()


        # import weather
        weather_files_list = list_files(f"{weather_dir}/")
        counter = 0; all = len(weather_files_list)
        print(f'\n\t> copying observed weather files')
        for fn in weather_files_list:
            counter += 1; show_progress(counter, all)
            copy_file(fn, f"{txtinout_dir}/{file_name(fn)}", replace=False)

        db_sqlite.cursor.execute("UPDATE project_config SET weather_data_dir = 'Scenarios/Default/TxtInOut' WHERE id='1';")
        db_sqlite.cursor.execute("UPDATE project_config SET input_files_dir = 'Scenarios/Default/TxtInOut' WHERE id='1';")
        db_sqlite.cursor.execute("UPDATE project_config SET wgn_table_name = 'wgn_cfsr_world' WHERE id='1';")
        db_sqlite.cursor.execute(f"UPDATE project_config SET wgn_db = '{weather_wgn_db}' WHERE id='1';")
        db_sqlite.commit_changes()

        command  = f'import_weather '

        command += f"--project_db_file {project_db} "
        command += f"--delete_existing y "
        command += f"--create_stations n "
        command += f"--import_type wgn "
        command += f"--editor_version {editor_version} "
        command += f"--import_method database "
        command += f"--wgn_db {weather_wgn_db} "
        command += f"--file1 {weather_wgn_db} "
        command += f"--wgn_table wgn_cfsr_world "

        os.system(command = f'{api} {command}')

        command  = f'import_weather '

        command += f"--project_db_file {project_db} "
        command += f"--delete_existing y "
        command += f"--create_stations y "
        command += f"--import_type observed "
        command += f"--editor_version {editor_version} "
        command += f"--weather_import_format plus "
        command += f"--weather_dir {weather_dir} "
        os.system(command = f'{api} {command}')


        # write files
        command  = f'write_files '
        command += f"--project_db_file {project_db} "

        os.system(command = f'{api} {command}')
        db_sqlite.close_connection()

        for scen in other_scenarios:
            f_list = list_files(f'../model-data/{region}/weather/swatplus/{scen}/')

            print(f'\n\t> copying {scen} weather files')
            for fn in f_list:
                copy_file(fn, f"{txtinout_dir}/{scen}/{file_name(fn)}", replace=True)

        # modify weather path in file.cio
                

        from cjfx import alert
        alert(f'done with editor in {region}', 'SWAT+ Editor run complete')

        print()
