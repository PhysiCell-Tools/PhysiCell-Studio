#!/bin/sh -f
cd /opt/pcstudio
/usr/local/pcstudio-venv/bin/python3 /opt/pcstudio/bin/studio.py -c /opt/pcstudio/config/PhysiCell_settings.xml --galaxy --samples
