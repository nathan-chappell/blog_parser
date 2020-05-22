#!/bin/bash

SYS_PYTHON=/usr/bin/python3
MONO_SITE=http://www.mono-software.com
SITE_PATH=/files/
SITE_ZIP=site.zip
ZIP_URL=${MONO_SITE}${SITE_PATH}${SITE_ZIP}

completion_message="Installation complete. Be sure to check out the readme. To use the application, it is necssary to start an elasticsearch instance (node) before running main.py."

message() {
    if [ -e $SYS_PYTHON ]; then
        python -c "from util import bannerfy; print(bannerfy('$1'))"
    else
        echo "********************************************************************************"
        echo $1
        echo "********************************************************************************"
    fi
}

if [ ! -e /usr/bin/python3 ]; then
	message "python3 not found in /usr/bin.  Exiting"
    exit -1
fi

message "Setting up virtual environment in $(pwd)"
$SYS_PYTHON -m venv .
source bin/activate

message "upgrading pip"
python -m pip install --upgrade pip

message "installing requirements"
pip install -r requirements.txt

message "downloading $SITE_ZIP from ${MONO_SITE}${SITE_PATH}"
if [ -e ./site.zip ]; then
    message "${SITE_ZIP} already exists, continuing installation"
elif [ -e /usr/bin/wget ]; then
    wget $ZIP_URL
elif [ -e /usr/bin/curl ]; then
    curl $ZIP_URL
else
    message "need wget or curl to download files"
    message "try: sudo apt install wget curl"
    exit -1
fi

message "extracting $SITE_ZIP"
unzip $SITE_ZIP

message "cloning elasticsearch repo"
# Error checking probably necessary here...
git clone http://github.com/elastic/elasticsearch --depth 1

message "$completion_message"

