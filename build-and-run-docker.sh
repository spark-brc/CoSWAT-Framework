#!/bin/bash 

docker buildx build -t coswat --progress=plain .
docker run -it -v "./:/CoSWAT-Global-Model" coswat
