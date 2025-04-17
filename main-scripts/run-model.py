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

import os, sys, platform
from cjfx import list_all_files, exists, write_to, run_swat_plus, ignore_warnings

ignore_warnings()

# change working directory
me = os.path.realpath(__file__)
os.chdir(os.path.dirname(me))

import datavariables as variables
from resources.print_file import print_prt

if __name__ == "__main__":

    args = sys.argv

    all_models = list_all_files("../model-setup/", "qgs")
    versions = {}

    for model in all_models:
        model = model.split("/")[-1].split("\\") if platform.system() == "Windows" else model.split("/")
        v = model[0 if platform.system() == 'Windows' else 2].lower().replace('coswatv', '')
        r = model[1 if platform.system() == 'Windows' else 3]

        if not v in versions:
            versions[v] = []
        
        versions[v].append(r)
                
    if len(args) < 4:
        print("please select a version years and region (...py version yrFrom-yrTo region1 region2... ). \nyou can also use '...py version yrFrom-yrTo all' to run for all regions. \nthese are available:")
        
        for k in versions:
            print(f"    {v}")
            for m in versions[k]:
                print(f"\t- {m}")
        
        quit()

    version         = args[1]
    yr_fro, yr_to   = args[2].split("-")
    regions         = args[3:]

    if regions[0] == "all": regions = versions[version]

    for region in regions:
        txtDir = f"{os.path.dirname(me)}/../model-setup/CoSWATv{version}/{region}/Scenarios/Default/TxtInOut"

        write_to(f"{txtDir}/time.sim", f"time.sim: written by CoSWAT Data Writer\nday_start  yrc_start   day_end   yrc_end      step  \n       0      {yr_fro}         0      {yr_to}         0  ")
        write_to(f"{txtDir}/print.prt", print_prt)
        if exists(f"{txtDir}/file.cio"):
            end_section = '\n' if platform.system() == 'Windows' else ''
            print(f"\n\n# running SWAT+ for {region}{end_section}")
            run_swat_plus(txtDir, executable_path = variables.executable_path)
            if platform.system() == "Windows": print()
        else:
            print(f"\n\n! cannot run SWAT+ for {region}")
    


        

