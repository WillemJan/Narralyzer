#!/usr/bin/env bash

#
# File: install.sh
#
# This file is part of the Narralyzer package.
# see: http://github.com/WillemJan/Narralyzer
#

# If you run into troubles try this:
#
# sudo apt-get install -y build-essential libdb-dev virtualenv python2.7 libxml2-dev libxslt1-dev
#
# Or leave a ping here: https://www.github.com/WillemJan/Narralyzer
#
# Goal of this install procedure is to get && install && config tools/language models needed.
# And fetch javascrip libs as needed.

# Narralyzer config util,
# all (global) variables should be defined in the conf/conf.ini file.
CONFIG=$(./narralyzer/config.py self)

#------------------------------------------------
# Functions
#------------------------------------------------

# Little wrapper to datestamp outgoing messages.
function inform_user() {
    msg="$1"
    timestamp=$(date "+%Y-%m-%d %H:%M")
    echo "$timestamp: Narralyzer install.sh $msg"
}

# Little wrapper to safely exit the burning script.
function airbag() {
    inform_user $1
    echo "Exit with -1, from: install.sh:$2"
    exit -1
}

# Fetch the given URL, and save to disk
# use the 'basename' for storing,
# retry a couple of times before failing.
function get_if_not_there () {
    URL=$1
    retries=4
    not_done="true"
    if [ ! -f $(basename $URL) ]; then
        while [ $not_done == "true" ]; do
           inform_user "Fetching $URL..."
           wget_output=$(wget -q "$URL")
           if [ $? -ne 0 ]; then
               # If downloading fails, try again.
               retries=$(($retries - 1))
               if [ $retries == 0 ]; then
                   $(wget -q "$URL")
                   airbag "Error while fetching $URL, no retries left." $LINENO
               else
                   inform_user "Error while fetching $URL, $retries left." $LINENO
                   sleep 1
               fi
           else
               # Else leave the loop.
               not_done="false"
           fi
        done
    else
        inform_user "Not fetching $URL, file allready there."
    fi
}

# Check if Python2.7 is installed on the os,
# we might need that in the near future.
function is_python2_7_avail() {
    is_avail=$(which python2.7 | wc -l)
    if [ "$is_avail" = "0" ]; then
        airbag "Python 2.7 is not available, helas. sudo apt-get install python2.7?" $LINENO
    fi
    inform_user "Python 2.7 is available."
}

# Check if we find (Python) virtualenv.
function is_virtualenv_avail() {
    is_avail=$(which virtualenv | wc -l)
    if [ "$is_avail" = "0" ]; then
        airbag "Virtualenv is not available, helas. sudo-apt-get install virtualenv?" $LINENO
    fi
    inform_user "Virtualenv is available."
}

# Fetch external github repository.
function fetch_and_install_language_models() {
    inform_user "Fetching and installing language models."
    git submodule init
    git submodule update
    cd ./language_models/stanford/
    ./generate_stanford_lang_snapshot.sh
    ./generate_stanford_ner_snapshot.sh
    cd -
}

#--------------------------------------------------------
# /Functions
#-------------------------------------------------------

# Get external language models
# https://github.com/WillemJan/Narralyzer_languagemodel

if [ ! -f "language_models/.git" ]; then
    fetch_and_install_language_models
else
    inform_user "Language model allready available, preforming update"
    git submodule update
fi

# Check if the virtual env exists, if not, create one and within
# the virtual env install the required packages.
if [ ! -d "env" ]; then
    is_python2_7_avail
    is_virtualenv_avail

    inform_user "Creating new virtualenv using python2.7 in ./env"
    virtualenv -p python2.7 ./env

    cd site; ln -s ../env ./; cd ..

    inform_user "Entering virtualenv, to leave: deactivate."
    source env/bin/activate

    inform_user "Upgrade pip and setuptools to latest version."
    pip install --upgrade pip setuptools

    req=$($CONFIG root)"/requirements.txt"
    if [ -f "$req" ]; then
        inform_user "Running: python2.7 setup.py install"
        python2.7 setup.py install || airbag "Something went wrong while running: python2.7 setup.py install"
    else
        airbag "Could not find requirements.txt in $req"
    fi
else
    inform_user "Virtualenv allready present, preforming update."
    source env/bin/activate
    python2.7 setup.py install || airbag "Something went wrong while running: python2.7 setup.py install"
fi

if [ ! -f "site/static/js/codemirror.zip" ]; then
    cd site/static/js/
    get_if_not_there http://codemirror.net/codemirror.zip
    unzip codemirror.zip
    ln -s $(find . -type d | head -2 | tail -1) codemirror
    cd -
fi

if [ ! -f "site/static/js/jquery.js" ]; then
    cd site/static/js/
    get_if_not_there https://code.jquery.com/jquery-3.2.0.min.js
    ln -s jquery-3.2.0.min.js jquery.js
    cd -
fi
