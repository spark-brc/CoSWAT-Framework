#!/bin/bash

echo "moving to taudem directory"
cd /tmp/compileTauDem/TauDEM/src/build

echo creating cmake files
# cmake ..

echo "making taudem"
# make -j8

echo "moving to taudem bin directory"
# cp -r /tmp/compileTauDem/TauDEM/src/build/* /root/.local/share/SWATPlus/TauDEM5Bin/

echo "changing permissions"
chmod 777 /root/.local/share/SWATPlus/TauDEM5Bin/*
