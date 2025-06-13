#!/bin/env python3
'''


'''

from cjfx import *

class plant:
    def __init__(
            self, name:str, lc_status:str = "n", lai_init:float = 0,
            bm_init:float = 0, yrs_init:float = 0
            ):
        self.plt_name   = name
        self.lc_status  = lc_status
        self.lai_init   = lai_init
        self.bm_init    = bm_init
        self.phu_init   = 0
        self.plnt_pop   = 0
        self.yrs_init   =  yrs_init
        self.rsd_init   = 10000

    def __str__(self):
        return f'{self.plt_name}'

class pcom:
    def __init__(self, comm:str, rotYr:int = 1):
        self.comm = comm
        self.pltRotYr = rotYr
        self.pltCnt = 0
        self.plants = []

    def addPlant(self, plantOb:plant):
        self.plants.append(plantOb)
        self.pltCnt = len(self.plants)

    def __str__(self):
        return f'{self.comm} ({"".join([p.plt_name for p in self.plants]) if not len(self.plants) == 0 else "None"})'
    

# example usage
fc = read_from("D:/Projects/Tools/WISE/CoSWAT-Framework/model-setup/CoSWATv0.1.0/asia-korea/Scenarios/Default/TxtInOut/plant.ini")

plantDatabase = {}

currentPcom = None

for line in fc[2:]:
    parts = line.split()
    if len(parts) < 4:
        currentPcom = parts[0]
        plantDatabase[currentPcom] = pcom(currentPcom)
        plantDatabase[currentPcom].pltRotYr = int(parts[2])
        continue

    name, lc_status, lai_init, bm_init, yrs_init = parts[0], parts[1], parts[2], parts[3], parts[6]

    newPlant = plant(name, lc_status, lai_init, bm_init, yrs_init)
    plantDatabase[currentPcom].addPlant(newPlant)


plantDatabase['rice140_comm'] = pcom('rice140_comm')
plantDatabase['rice140_rye'] = pcom('rice140_rye')

rice140 = plant('rice140', lai_init=0.3, bm_init=35, lc_status = "n")
rice140.phu_init = 50; rice140.plnt_pop = 125

rye = plant('rye', lai_init=0, bm_init=35, lc_status = "y")
rye.plnt_pop = 100

plantDatabase['rice140_comm'].addPlant(rice140)
plantDatabase['rice140_rye'].addPlant(rice140)
plantDatabase['rice140_rye'].addPlant(rye)

finalString = "plant.ini: written by Park \npcom_name          plt_cnt  rot_yr_ini          plt_name     lc_status      lai_init       bm_init      phu_init      plnt_pop      yrs_init      rsd_init \n"

for pcomName in plantDatabase:
    finalString += pcomName.ljust(19)
    finalString += f"{plantDatabase[pcomName].pltCnt}".rjust(7)
    finalString += f"{plantDatabase[pcomName].pltRotYr}".rjust(12); finalString += "\n"

    for pObj in plantDatabase[pcomName].plants:
        finalString += f"{pObj.plt_name}".rjust(56)
        finalString += f"{pObj.lc_status}".rjust(14)
        finalString += f"{pObj.lai_init}".rjust(14)
        finalString += f"{pObj.bm_init}".rjust(14)
        finalString += f"{pObj.phu_init}".rjust(14)
        finalString += f"{pObj.plnt_pop}".rjust(14)
        finalString += f"{pObj.yrs_init}".rjust(14)
        finalString += f"{pObj.rsd_init}".rjust(14); finalString += "\n"


print(finalString)

write_to("D:/Projects/Tools/WISE/CoSWAT-Framework/model-setup/CoSWATv0.1.0/asia-korea/Scenarios/Default/TxtInOut/plant2.ini", finalString)

