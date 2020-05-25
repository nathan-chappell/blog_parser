#!/bin/bash

SYS_PYTHON=/usr/bin/python3
MONO_SITE=http://www.mono-software.com
SITE_PATH=/files/
SITE_ZIP=site.zip
ZIP_URL=${MONO_SITE}${SITE_PATH}${SITE_ZIP}
ES_PATH=https://artifacts.elastic.co/downloads/elasticsearch/
ES_BASE=elasticsearch
ES_VERSION=7.7.0
ES_PATH="${ES_BASE}-${ES_VERSION}"
ES_ARCH=linux-x86_64
ES_TARGET="${ES_PATH}-${ES_ARCH}.tar.gz"

completion_message="Installation complete. Be sure to check out the readme. To use the application, it is necssary to start an elasticsearch instance (node) before running main.py."

message_() {
    if [ -e $SYS_PYTHON ]; then
        python -c "from util import bannerfy; print(bannerfy('$1'))"
    else
        echo "********************************************************************************"
        echo $1
        echo "********************************************************************************"
    fi
}

message() {
    message_ "$1"
    message_ "$1" >> install_log.log
}

check_dep() {
    if ! command -v $1 >/dev/null; then
        echo "$1 required for installation"
        sudo apt install $1
    fi
    if command -v $1 >/dev/null; then
        return 0
    else
        return -1
    fi
}

check_deps() {
    if check_dep wget && check_dep python3; then
        return 0
    else
        message "need wget and python, exiting"
        exit -1
    fi
}

dl_if_not_exists() {
    if [ -e ${1##*/} ]; then
        message "${1} already exists, continuing installation"
    else
        wget $1
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
dl_if_not_exists "$ZIP_URL"

message "extracting $SITE_ZIP"
unzip $SITE_ZIP -d site

message "downloading ElasticSearch"
dl_if_not_exists "${ES_PATH}${ES_TARGET}"

message "extracting ElasticSearch"
tar -xf $ES_TARGET

message "copying stopwords file"
cp stopwords ${ES_PATH}/config/stopwords

message "$completion_message"

