#!/bin/python3

'''
This script monitors the progress of weather data processing
since the parallelisation in the main script makes it hard to
add a progress bar.

Author  : Celray James CHAWANDA
Date    : 24/01/2023
Contact : celray@chawanda.com
Licence : MIT
GitHub  : github.com/celray
'''

from resources import datavariables as variables
import time
import struct
from datetime import datetime

import os
import sys
from cjfx import (exists, list_folders, read_from, show_progress, report)
from osgeo import gdal, ogr


# change working directory
me = os.path.realpath(__file__)
os.chdir(os.path.dirname(me))


if __name__ == '__main__':

    if len(sys.argv) < 2:
        print(f"! select a region for which to monitor progress the dataset. options are: {', '.join(list_folders('./resources/regions/'))}\n")
        sys.exit()

    region = sys.argv[1]

    print(f'\n# monitoring weather data preparation for {region}\n')

    progress = 0

    while not exists(f'./weather-ws/{region}_file_list.txt'):
        report('\t! waiting for data preparation process      ')
        time.sleep(20)

    fc = read_from(f'./weather-ws/{region}_file_list.txt')
    
    total = len(fc)
    current_count = 0
    dt_obj = []


    dcounter = 0
    time_stamp = datetime.now()
    while progress < 1:
        count = 0

        for line in fc:
            if exists(line.strip()):
                count += 1

        if count > current_count:
            dt_obj.append(datetime.now() - time_stamp)
            dcounter += (current_count - count)
            current_count = count
            time_stamp = datetime.now()


        progress = count/total

        show_progress(count, total, dt = dt_obj, d_count=dcounter)
        time.sleep(20)

show_progress(1, 1)

print('\n\n')
