#!/bin/python3

'''
this script coordinates the setup of the COmmunity SWAT+ Model
(CoSWAT-Global) development. A project aimed at providing a community
contributed global SWAT+ model initiated and led by Celray James CHAWANDA.

Author  : 
Date    : 

Contact : 
        

Licence : MIT 2022
GitHub  : github.com/celray
'''

import os
import sys
import platform
import shutil
from termcolor import colored
import numpy as np
from cjfx import list_all_files, read_from
from resources import pcom

# change working directory
me = os.path.realpath(__file__)
os.chdir(os.path.dirname(me))

class Paddy:
    def __init__(self, version):
        self.version = version
        self.projDir = f"../model-setup/CoSWATv{version}/"

    def get_model_paths(self):
        all_models = list_all_files("../model-setup/", "qgs")
        versions = {}
        for model in all_models:
            model = model.split("/")[-1].split("\\") if platform.system() == "Windows" else model.split("/")
            v = model[0 if platform.system() == 'Windows' else 2].lower().replace('coswatv', '')
            r = model[1 if platform.system() == 'Windows' else 3]
            if not v in versions:
                versions[v] = []
            versions[v].append(r)
        # print(versions)
        # regions[0] == "all"
        regions = versions[self.version]
        return regions

    def _get_paths(self, region):
        txtDir = os.path.join(self.projDir, region, 'Scenarios', 'Default', 'TxtInOut')
        backupDir = os.path.join(txtDir, 'paddy_backup')
        return txtDir, backupDir


    def create_backup(self, region):
        filesToCopy = [
            "file.cio",
            "hru-data.hru",
            "hydrology.wet",
            "hydrology.hyd",
            "wetland.wet",
            "initial.res",
            "irr.ops",
            "landuse.lum",
            "plant.ini"
        ]
        suffix = ' passed'
        print(f" > Creating 'paddy_backup' folder in {region} txtDir ...")

        txtDir, backupDir = self._get_paths(region)
        if not os.path.isdir(backupDir):
            os.makedirs(backupDir)
            for j in filesToCopy:
                if not os.path.isfile(os.path.join(backupDir, j)):
                    shutil.copy2(os.path.join(txtDir, j), os.path.join(backupDir, j))
                    print("  >>> '{}' file copied ...".format(j) + colored(suffix, 'green'))
            print(f" > Creating 'paddy_backup' folder in {region} txtDir ..." + colored(suffix, 'green') + "\n")
        else:
            print(f" > 'paddy_backup' folder already exists in {region} txtDir ..." + colored("existed", 'red') + "\n")

    def conv_hrudata(self, region, lumlist=None):
        if lumlist is None:  # landcode
            lumlist = ["rice"]
        txtDir, backupDir = self._get_paths(region)
        with open(os.path.join(backupDir, 'hru-data.hru'), "r") as f:
            data = f.readlines()
            ndigits = len(str(data[-1].split()[0]))
            for ll in lumlist:
                c = 0
                for line in data:
                    if (
                        (len(line.split()) >=6) and 
                        (line.split()[5] != "null") and 
                        (line.split()[5].startswith(ll))
                    ):
                        new_line = self.replace_line_hrudata(line, ndigits)
                        data[c] = new_line
                    c += 1
        with open(os.path.join(txtDir, "hru-data.hru"), "w") as wf:
            wf.writelines(data)
        new_file = os.path.join(txtDir, 'hru-data.hru')
        print(
            f" {'>'*3} {os.path.basename(new_file)}" + 
            " file is overwritten successfully!"
            )
        
    def replace_line_hrudata(self, line, nd):
        parts = line.split()
        new_line = (
            f'{int(parts[0]):8d}'+ f'{parts[1]:>9s}'+ f'{parts[2]:>27s}'+
            f'{parts[3]:>18s}'+ f'{parts[4]:>18s}'+ f"{'rice_paddy_lum':>18s}"+
            f'{parts[6]:>18s}' + f"{f'paddy{int(parts[0][-4:]):>0{nd}d}':>18s}" + 
            f'{parts[8]:>18s}' + f'{parts[9]:>18s}'
            "\n"
        )
        return new_line

    def get_paddy_objs(self, region):
        # Get paddy objects from hru-data.hru file

        txtDir, _ = self._get_paths(region) 
        with open(os.path.join(txtDir, 'hru-data.hru'), "r") as f:
            data = f.readlines()
            paddy_objs = []
            for line in data:
                if len(line.split()) >=7 and line.split()[7].startswith("paddy"):
                    paddy_objs.append([line.split()[1], line.split()[7]])
            paddy_objs = np.array(paddy_objs)
        return paddy_objs

    # NOTE: this function is used for new version
    def conv_wetlandwet(self, region):
        txtDir, backupDir = self._get_paths(region)
        paddy_objs = self.get_paddy_objs(region)
        # print(paddy_objs[:, 1])
        with open(os.path.join(backupDir, "wetland.wet"), "r") as fw:
            data = fw.readlines()
            ndigits = len(str(data[-1].split()[0]))
            stid = int(data[-1].split()[0]) + 1
            # print(stid)
            for paddy_obj in paddy_objs[:, 1]:
                new_line = (
                    f'{int(stid):8d}' 
                    f'  {paddy_obj:<16s}' 
                    f"{'initwet2':>18s}" 
                    f"{'paddy':>18s}" 
                    # f"{paddy_obj:>18s}" 
                    f"{'weir':>18s}" 
                    f"{'sedwet1':>18s}" 
                    f"{'nutwet1':>18s}\n" 
                )
                data.append(new_line)
                stid += 1
        # create weir column if not exists
        if data[1].split()[-1] == "nut":
            data[1] = data[1].rstrip() + f"{'weir':>18s}\n"

        # add weir1 to paddy lines and null to others
        for c2, line in enumerate(data):
            if line.split()[3] == "paddy":
                data[c2] = line.rstrip() + f"{'weir1':>18s}\n"
            elif line.split()[0].isdigit() and line.split()[3] != "paddy":
                data[c2] = line.rstrip() + f"{'null':>18s}\n"
            else:
                pass

        with open(os.path.join(txtDir, "wetland.wet"), "w") as wf:
            wf.writelines(data)

    # NOTE: this function is used for old version
    def conv_wetlandwet_(self, region):
        txtDir, backupDir = self._get_paths(region)
        paddy_objs = self.get_paddy_objs(region)
        # print(paddy_objs[:, 1])
        with open(os.path.join(backupDir, "wetland.wet"), "r") as fw:
            data = fw.readlines()
            ndigits = len(str(data[-1].split()[0]))
            stid = int(data[-1].split()[0]) + 1
            # print(stid)
            for paddy_obj in paddy_objs[:, 1]:
                new_line = (
                    f'{int(stid):8d}' 
                    f'  {paddy_obj:<16s}' 
                    f"{'high_init':>18s}" 
                    f"{'paddy':>18s}" 
                    # f"{paddy_obj:>18s}" 
                    f"{'weir':>18s}" 
                    f"{'sedwet1':>18s}" 
                    f"{'nutwet1':>18s}\n" 
                )
                data.append(new_line)
                stid += 1

        with open(os.path.join(txtDir, "wetland.wet"), "w") as wf:
            wf.writelines(data)

        '''        # this is for testing
    # print(paddy_objs)
        with open(os.path.join(self.wd, 'backup', 'wetland.wet'), "r") as f:
            data = f.readlines()
            ndigits = len(str(data[-1].split()[0]))
            for ll in lumlist:
                c = 0
                for line in data:
                    if line.split()[5] != "null" and line.split()[5].startswith(ll):
                        new_line = self.replace_line(line, ndigits)
                        data[c] = new_line
                    c += 1
        '''

    def replace_line_wetlandwet(self, line, nd):
        parts = line.split()
        new_line = (
            f'{int(parts[0]):8d}'+ f'{parts[1]:>9s}'+ f'{parts[2]:>27s}'+
            f'{parts[3]:>18s}'+ f'{parts[4]:>18s}'+ f"{'rice_paddy_lum':>18s}"+
            f'{parts[6]:>18s}' + f"{f'paddy{int(parts[0][-4:]):>0{nd}d}':>18s}" + 
            f'{parts[8]:>18s}' + f'{parts[9]:>18s}'
            "\n"
        )
        return new_line

    def conv_filecio(self, region):
        txtDir, backupDir = self._get_paths(region)
        with open(os.path.join(backupDir, 'file.cio'), "r") as f:
            data = f.readlines()
            c = 0
            modi = "notyet"
            for line in data:
                if line.split()[0] == "reservoir" and not "weir.res" in line.split():
                    modi = "y"
                    nc = len(line.split())
                    ridx = line.split().index("null")
                    newlist = line.split()
                    newlist[ridx] = "weir.res"
                    newline = []
                    for i in newlist:
                        newline.append(f'{i:<18s}')
                    newline.append("\n")
                    newline ="".join(newline)
                    data[c] = newline
                c += 1
        if modi == "y":    
            with open(os.path.join(txtDir, "file.cio"), "w") as wf:
                wf.writelines(data)
            new_file = os.path.join(txtDir, 'file.cio')
            print(
                f" {'>'*3} {os.path.basename(new_file)}" + 
                " file is overwritten successfully!"
                )
        else:
            new_file = os.path.join(txtDir, 'file.cio')
            print(
                f"  {'>'*3} {os.path.basename(new_file)}" + 
                " file is not overwritten!"
                )

    def conv_initialres(self, region):
        txtDir, backupDir = self._get_paths(region)
        with open(os.path.join(backupDir, "initial.res"), "r") as fw:
            data = fw.readlines()
            fc = [line.split()[0] for line in data]
        modi = 'n'
        if "low_init" not in fc:
            modi = 'y'
            lowinit_line = (
                f"{'low_init':<16s}"+ f"{'low_init':>18s}"+ f"{'no_ini':>18s}"+ f"{'no_ini':>18s}"+
                f"{'null':>18s}"+ f"{'null':>18s}"+ f"{'null':>18s}"
                "\n"                
            )
            data.append(lowinit_line)

        if "high_init" not in fc:
            modi = 'y'
            highinit_line = (
                f"{'high_init':<16s}"+ f"{'high_init':>18s}"+ f"{'low_ini':>18s}"+ f"{'low_ini':>18s}"+
                f"{'null':>18s}"+ f"{'null':>18s}"+ f"{'null':>18s}"
                "\n"                
            )
            data.append(highinit_line)

        if modi == "y": 
            with open(os.path.join(txtDir, "initial.res"), "w") as wf:
                wf.writelines(data)
            new_file = os.path.join(txtDir, 'initial.res')
            print(
                f" {'>'*3} {os.path.basename(new_file)}" + 
                " file is overwritten successfully!"
                )
        else:
            new_file = os.path.join(txtDir, 'initial.res')
            print(
                f" {'>'*3} {os.path.basename(new_file)}" + 
                " file is not overwritten!"
                )

    def conv_irrops(self, region):
        txtDir, backupDir = self._get_paths(region)
        with open(os.path.join(backupDir, "irr.ops"), "r") as fw:
            data = fw.readlines()
            fc = [line.split()[0] for line in data if line !='\n']
        print(fc)
        modi = 'n'
        if "ponding90" not in fc:
            modi = 'y'
            ponding90_line = (
                f"{'ponding90':<16s}"+ f"{90:>14.5f}"+ f"{1:>14.5f}"+ f"{0:>14.5f}"+
                f"{60:>14.5f}"+ f"{0:>14.5f}"+ f"{0:>14.5f}" + f"{0:>14.5f}"
                "\n"                
            )
            data.append(ponding90_line)
        if "ponding_off" not in fc:
            modi = 'y'
            ponding_off_line = (
                f"{'ponding_off':<16s}"+ f"{0:>14.5f}"+ f"{1:>14.5f}"+ f"{0.1:>14.5f}"+
                f"{0:>14.5f}"+ f"{0:>14.5f}"+ f"{0:>14.5f}" + f"{0:>14.5f}"
                "\n"                
            )
            data.append(ponding_off_line)
        if modi == "y":    
            with open(os.path.join(txtDir, "irr.ops"), "w") as wf:
                wf.writelines(data)
            new_file = os.path.join(txtDir, "irr.ops")
            print(
                f" {'>'*3} {os.path.basename(new_file)}" + 
                " file is overwritten successfully!"
                )
        else:
            new_file = os.path.join(txtDir, "irr.ops")
            print(
                f" {'>'*3} {os.path.basename(new_file)}" + 
                " file is not overwritten!"
                )

    def conv_hydwet(self, region, paddy_ids=False):
        txtDir, backupDir = self._get_paths(region)
        paddy_objs = self.get_paddy_objs(region)
        # print(paddy_objs)
        with open(os.path.join(backupDir, "hydrology.wet"), "r") as fw:
            data = fw.readlines()
            # ndigits = len(str(data[-1].split()[0]))
            # stid = int(data[-1].split()[0]) + 1
            if paddy_ids is True:
                for paddy_obj in paddy_objs:
                    new_line = (
                        # f'{int(stid):8d}' + 
                        f'{paddy_obj[1]:<16s}' 
                        f"{1:>14.5f}" 
                        f"{150:>14.5f}" 
                        f"{1:>14.5f}" 
                        f"{150:>14.5f}" 
                        f"{0.5:>14.5f}" 
                        f"{0.75:>14.5f}" 
                        f"{1:>14.5f}" 
                        f"{1:>14.5f}" 
                        f"{1:>14.5f}" 
                        f"{1:>14.5f}\n" 
                    )
                    data.append(new_line)
            else:
                new_line = (
                    # f'{int(stid):8d}' + 
                    f'{"paddy":<16s}' 
                    f"{1:>14.5f}" 
                    f"{150:>14.5f}" 
                    f"{1:>14.5f}" 
                    f"{150:>14.5f}" 
                    f"{0.5:>14.5f}" 
                    f"{0.75:>14.5f}" 
                    f"{1:>14.5f}" 
                    f"{1:>14.5f}" 
                    f"{1:>14.5f}" 
                    f"{1:>14.5f}\n" 
                )
                data.append(new_line)             
                # stid += 1
        with open(os.path.join(txtDir, "hydrology.wet"), "w") as wf:
            wf.writelines(data)

    def conv_landlum(self, region):
        txtDir, backupDir = self._get_paths(region)
        with open(os.path.join(backupDir,"landuse.lum"), "r") as fw:
            data = fw.readlines()
            fc = [line.split()[0] for line in data if line !='\n']
        print(fc[2:])
        modi = 'n'
        if "rice_paddy_lum" not in fc:
            newlist = [
                'rice_paddy_lum', 'null', 'rice120_comm', 'paddy', 'legr_strow_p', 'ter_1-2_sodout', 'null', 'null', 'chisplow_nores',
                ] + ['null']*5
            newline = []
            for i in newlist:
                if i == 'rice_paddy_lum':
                    newline.append(f'{i:<20s}')
                elif i == 'paddy':
                    newline.append(f'{i:>43s}')
                else:
                    newline.append(f'{i:>18s}')
            newline.append("\n")
            newline ="".join(newline)            
            data.append(newline)
            modi = 'y'
        if modi == "y":    
            with open(os.path.join(txtDir, "landuse.lum"), "w") as wf:
                wf.writelines(data)
            new_file = os.path.join(txtDir, "landuse.lum")
            print(
                f" {'>'*3} {os.path.basename(new_file)}" + 
                " file is overwritten successfully!"
                )
        else:
            new_file = os.path.join(txtDir, "landuse.lum")
            print(
                f" {'>'*3} {os.path.basename(new_file)}" + 
                " file is not overwritten!"
                )

    def rice_database(self, region):


        txtDir, backupDir = self._get_paths(region)
        backupPltDb = read_from(os.path.join(backupDir, "plant.ini"))
        plantDatabase = {}
        currentPcom = None
        # pcom.PlantCom('rice1')

        for line in backupPltDb[2:]:
            parts = line.split()
            if len(parts) < 4:
                currentPcom = parts[0]
                plantDatabase[currentPcom] = pcom.PlantCom(currentPcom)
                plantDatabase[currentPcom].pltRotYr = int(parts[2])
                continue
            name, lc_status, lai_init, bm_init, yrs_init = parts[0], parts[1], parts[2], parts[3], parts[6]
            newPlant = pcom.Plant(name, lc_status, lai_init, bm_init, yrs_init)
            plantDatabase[currentPcom].addPlant(newPlant)
        plantDatabase['rice140_comm'] = pcom.PlantCom('rice140_comm')
        plantDatabase['rice140_rye'] = pcom.PlantCom('rice140_rye')

        
        print(plantDatabase)
        '''    
        '''

        # rice_db = {
        #     'rice140_comm': [[1, 1],
        # }







    def conv_plantin(self, region):
        txtDir, backupDir = self._get_paths(region)

        inf = "plant.ini"
        with open(os.path.join(backupDir, inf), "r") as fw:
            data = fw.readlines()
            fc = [line.split()[0] for line in data if line !='\n']
        print(fc[2:])
        modi = 'n'
        if "rice120_comm" not in fc:
            newlist = [
                'rice120_comm', 1, 1]
            newlist2 = [
                'rice120', 'n', 0, 0, 0, 0, 0, 10000
                ]           
            newline = []
            for i in newlist:
                if i == 'rice120_comm':
                    newline.append(f'{i:<16s}')
                else:
                    newline.append(f'{i:>10d}')
            newline.append("\n")
            newline ="".join(newline)
            newline2 = []
            for i in newlist2:
                if i == 'rice120':
                    newline2.append(f'{i:>44s}')
                elif i == "n" or i == "y":
                    newline2.append(f'{i:>14s}')
                else:
                    newline2.append(f'{i:>14.5f}')
            newline2.append("\n")
            newline2 ="".join(newline2)
            data.append(newline)
            data.append(newline2)
            modi = 'y'
        if modi == "y":    
            with open(os.path.join(txtDir, inf), "w") as wf:
                wf.writelines(data)
            new_file = os.path.join(txtDir, inf)
            print(
                f" {'>'*3} {os.path.basename(new_file)}" + 
                " file is overwritten successfully!"
                )
        else:
            new_file = os.path.join(txtDir, inf)
            print(
                f" {'>'*3} {os.path.basename(new_file)}" + 
                " file is not overwritten!"
                )

    def conv_hyd_perco(self, region, perco=None):
        txtDir, backupDir = self._get_paths(region)
        if perco is None:
            perco = 0.0001
        # get paddy hru
        paddy_objs = self.get_paddy_objs(region)

        with open(os.path.join(backupDir, 'hydrology.hyd'), "r") as f:
            data = f.readlines()
            c = 0
            for line in data:
                if line.split()[0] in paddy_objs:
                    new_line = self.replace_line_hyd(line, perco)
                    data[c] = new_line
                c += 1
        with open(os.path.join(txtDir, "hydrology.hyd"), "w") as wf:
            wf.writelines(data)
        new_file = os.path.join(txtDir, 'hydrology.hyd')
        print(
            f" {'>'*3} {os.path.basename(new_file)}" + 
            " file is overwritten successfully!"
            )

    def replace_line_hyd(self, line, perco):
        parts = line.split()
        newline = []
        for i in range(len(parts)):
            if i == 0:
                newline.append(f'{parts[i]:<16s}')
            elif i == 10:
                newline.append(f'{perco:>14.5f}')
            else:
                newline.append(f"{float(parts[i]):>14.5f}" )
        newline.append("\n")
        newline ="".join(newline)            
        return newline







    def conv_paddy(self):
        regions = self.get_model_paths()
        for region in regions:
            print(f"\n\n### running paddy conversion for {region} ... " + colored('started!', 'blue'))
            # self.create_backup(region)
            # self.conv_hrudata(region)
            # self.conv_wetlandwet(region)
            # self.conv_filecio(region) # new version would not need this
            # self.conv_initialres(region) # new version would not need this
            # self.conv_irrops(region)
            # self.conv_hydwet(region)
            # self.conv_landlum(region)
            self.conv_plantin(region)
            # self.conv_hyd_perco(region, perco=0.0001)
            print(f"\n### running paddy conversion for {region} ... " + colored('completed!', 'green') + "\n\n")




if __name__ == "__main__":
    m1 = Paddy('0.1.0')
    # m1.conv_paddy()
    m1.rice_database('asia-korea')


    # args = sys.argv
    # all_models = list_all_files("../model-setup/", "qgs")
    # versions = {}

    # for model in all_models:
    #     model = model.split("/")[-1].split("\\") if platform.system() == "Windows" else model.split("/")
    #     v = model[0 if platform.system() == 'Windows' else 2].lower().replace('coswatv', '')
    #     r = model[1 if platform.system() == 'Windows' else 3]
    #     if v == '0.4.0':
    #         print(model)
    # get_model_paths('0.4.0')




    #     if not v in versions:
    #         versions[v] = []
    #     versions[v].append(r)
                
    # if len(args) < 4:
    #     print("please select a version years and region (...py version yrFrom-yrTo region1 region2... ). \nyou can also use '...py version yrFrom-yrTo all' to run for all regions. \nthese are available:")
        
    #     for k in versions:
    #         print(f"    {v}")
    #         for m in versions[k]:
    #             print(f"\t- {m}")
        
    #     quit()


    # print(all_models)
    # print(" > Creating 'paddy_backup' folder in working directory ..." + colored('testing...', 'green'))