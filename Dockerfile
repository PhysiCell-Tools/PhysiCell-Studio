FROM jlesage/baseimage-gui:ubuntu-24.04-v4 AS build

# MAINTAINER Randy Heiland, randy.heiland@gmail.com

# Build a Docker image for PhysiCell Studio (to become an "Interactive tool" for Galaxy)
#   https://github.com/PhysiCell-Tools/PhysiCell-Studio
#   PhysiCell Studio currently uses PyQt5 for its GUI and we would like to retain
#   that for the Galaxy tool, at least for now.
#
# References:
#   https://github.com/usegalaxy-eu/docker-qupath
#   https://github.com/jlesage/docker-baseimage-gui

# Experimented with this env var, but it seems to make no difference. When we try to run
# the tool in a local Galaxy server, we get: 
# File "/usr/local/pcstudio-venv/lib/python3.12/site-packages/matplotlib/pyplot.py", line 433, in switch_backend
#   raise ImportError(
#   ImportError: Cannot load backend 'Qt5Agg' which requires the 'qt' interactive framework, as 'headless' is currently running)
# ENV DEBIAN_FRONTEND=noninteractive

# This fix: libGL error: No matching fbConfigs or visuals found
ENV LIBGL_ALWAYS_INDIRECT=1

# some of these pkgs may not be necessary, e.g., openjfx, but leaving in for now
        #  openjfx \
RUN printf "root:x:0:\nstaff:x:50:\n" > /tmp/.group && \
    printf "root:x:0:0:root:/root:/bin/bash\n" > /tmp/.passwd && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends \
         ca-certificates \
         wget \
         zip \
         libgl1 \
         xz-utils \
         nano \
         libglib2.0-0t64 \
         libfontconfig1 \
         libfreetype6 \
         libdbus-1-3 \
         libxcb-icccm4 \
         libxcb-image0 \
         libxcb-keysyms1 \
         libxcb-render-util0 \
         libxcb-render0 \
         libxcb-shape0 \
         libxcb-xinerama0 \
         libxcb-xkb1 \
         libxkbcommon-x11-0 \
         libxkbcommon0 \
         python3 python3-venv python3-pip \
         g++ libomp-dev && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /usr/local/pcstudio-venv
RUN /usr/local/pcstudio-venv/bin/pip install matplotlib scipy pandas PyQt5 galaxy-ie-helpers PyGithub 

RUN mkdir -p /opt/pcstudio/bin/images &&\
    mkdir -p /opt/pcstudio/bin/icon &&\
    mkdir -p /opt/pcstudio/config &&\
    mkdir -p /opt/pcstudio/samples &&\
    chmod -R 777 /opt/pcstudio &&\
    mkdir /import &&\
    chmod -R 777 /import
#    mkdir -p /opt/pcstudio/output &&\   # don't need as it's created on a "Run"

# Generate and install favicons.
# RUN APP_ICON_URL=https://github.com/pcstudio/pcstudio/wiki/images/pcstudio_131.png && \
#     install_app_icon.sh "$APP_ICON_URL"

COPY startapp.sh /startapp.sh
RUN chmod +x /startapp.sh

COPY ./bin/* /opt/pcstudio/bin/
COPY ./bin/images/* /opt/pcstudio/bin/images/
COPY ./bin/icon/* /opt/pcstudio/bin/icon/
COPY ./config/* /opt/pcstudio/config/
COPY ./samples/* /opt/pcstudio/samples/
COPY ./project /opt/pcstudio/
COPY ./omp_hello /opt/pcstudio/
COPY ./VERSION.txt /opt/pcstudio/
RUN chmod -R 777 /opt/pcstudio

# Installing a few extensions
# RUN cd /opt/pcstudio/pcstudio/lib/app/ && \
#     wget https://github.com/pcstudio/pcstudio-extension-djl/releases/download/v0.3.0/pcstudio-extension-djl-0.3.0.jar &&\
#     wget https://github.com/pcstudio/pcstudio-extension-stardist/releases/download/v0.5.0/pcstudio-extension-stardist-0.5.0.jar &&\
#     sed -i '/^\[Application\]$/a app.classpath=$APPDIR/pcstudio-extension-djl-0.3.0.jar' pcstudio.cfg  && \
#     sed -i '/^\[Application\]$/a app.classpath=$APPDIR/pcstudio-extension-stardist-0.5.0.jar' pcstudio.cfg

# Set the name of the application.
# rwh: where/how is this used?
ENV APP_NAME="pcstudio"

# rwh: what do the following do?
ENV KEEP_APP_RUNNING=0
ENV TAKE_CONFIG_OWNERSHIP=1

COPY rc.xml.template /opt/base/etc/openbox/rc.xml.template

WORKDIR /config
