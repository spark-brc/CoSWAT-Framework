#!/bin/bash 

mkdir -p data-preparation/resources 
unzip data-preparation/resources/regions.zip -d data-preparation/resources
unzip data-preparation/resources/QSWATPlus.zip -d data-preparation/resources
docker buildx build -t coswat --progress=plain .
docker run -it -v "./:/CoSWAT-Global-Model" coswat
