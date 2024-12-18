# Use the official Ubuntu 22.04 LTS as a base image
FROM ubuntu:22.04

# Set DEBIAN_FRONTEND to noninteractive to avoid prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# Install Python 3.10 and required dependencies
RUN apt-get update && apt-get install -y python3.10 python3.10-venv python3.10-dev python3-pip gnupg software-properties-common qgis cmake openmpi-bin openmpi-common openssh-client openssh-server libopenmpi-dev unzip nano imagemagick libmagickwand-dev gdal-bin libgdal-dev python3-gdal ffmpeg


# Install the Python package cjfx
RUN pip3 install hydroeval wand cython
RUN pip3 install matplotlib
RUN pip3 install cjfx
RUN pip3 install netcdf4 fiona
RUN pip3 install numpy==1.23.4

# Set Python 3.10 as the default python3
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1

RUN wget https://celray.chawanda.com/assets/downloads/swatplus-linux.tgz -O /tmp/swatplus-linux.tgz
RUN mkdir -p /tmp/swatplus-linux/
RUN tar -xvzf /tmp/swatplus-linux.tgz -C /tmp/swatplus-linux/
RUN cd /tmp/swatplus-linux/ && ./installforme.sh

# Set the default command to run when the container starts

# compile TauDEM
RUN mkdir -p /tmp/compileTauDem
COPY docker-resources/TauDEM.zip /tmp/compileTauDem/TauDEM.zip
COPY docker-resources/setupTaudem.sh /tmp/compileTauDem/setupTaudem.sh
RUN unzip /tmp/compileTauDem/TauDEM.zip -d /tmp/compileTauDem/

RUN chmod +x /tmp/compileTauDem/setupTaudem.sh
RUN /tmp/compileTauDem/setupTaudem.sh

ENV QT_QPA_PLATFORM=offscreen
RUN echo 'export XDG_RUNTIME_DIR=/tmp/runtime-root' >> ~/.bashrc
RUN mkdir -p /tmp/runtime-root
RUN chmod 700 /tmp/runtime-root

ENV OMPI_ALLOW_RUN_AS_ROOT=1
ENV OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1

# Copy the CoSWAT-Global-Model folder into the Docker image
RUN mkdir -p /CoSWAT-Global-Model/data-preparation/resources
COPY data-preparation/resources /CoSWAT-Global-Model/data-preparation/resources
# COPY CoSWAT-Global-Model /CoSWAT-Global-Model

# add paths to path and pythonpath in bashrc
# /CoSWAT-Global-Model
# /CoSWAT-Global-Model/data-preparation
RUN echo 'export PATH=$PATH:/CoSWAT-Global-Model' >> ~/.bashrc
RUN echo 'export PYTHONPATH=$PYTHONPATH:/CoSWAT-Global-Model' >> ~/.bashrc
RUN echo 'export PATH=$PATH:/CoSWAT-Global-Model/data-preparation' >> ~/.bashrc 
RUN echo 'export PYTHONPATH=$PYTHONPATH:/CoSWAT-Global-Model/data-preparation' >> ~/.bashrc
RUN echo 'export PATH=$PATH:/CoSWAT-Global-Model/main-scripts' >> ~/.bashrc 
RUN echo 'export PYTHONPATH=$PYTHONPATH:/CoSWAT-Global-Model/main-scripts' >> ~/.bashrc

COPY docker-resources/testingScript.sh /tmp/testingScript.sh
RUN chmod +x /tmp/testingScript.sh

RUN cp /root/.local/share/SWATPlus/SWATPlusEditor/resources/app.asar.unpacked/static/api_dist/swatplus_api /CoSWAT-Global-Model/data-preparation/resources/swatplus_api

CMD ["bash"]
