#!/usr/bin/env bash

#
# File: install.sh
#
# This file is part of the Narralyzer package.
# see: http://github.com/WillemJan/Narralyzer
#

# If you run into troubles try this: 
# 
# sudo apt-get install -y build-essesntials libdb-dev virtualenv python2.7 libxml2-dev libxslt1-dev
#
# Or leave a ping here: https://www.github.com/WillemJan/Narralyzer
#

# Narralyzer config util,
# all (global) variables should be defined in the conf/conf.ini file.
CONFIG=$(./narralyzer/config.py self)

# Little wrapper to datestamp outgoing messages.
function inform_user() {
    msg="$1"
    timestamp=$(date "+%Y-%m-%d %H:%M")
    echo "$timestamp: Narralyzer install.sh $msg"
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
                   inform_user "Error while fetching $URL, no retries left."
                   exit -1
               else
                   inform_user "Error while fetching $URL, $retries left."
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

# Fetch and unpack the Stanford core package.
function fetch_stanford_core {
    STANFORD_CORE=$($CONFIG stanford_core)
    get_if_not_there $STANFORD_CORE
    if [ -f $(basename $STANFORD_CORE) ]; then
        unzip -q -n $(basename "$STANFORD_CORE")
        # Remove the download package aferwards.
        rm $(basename "$STANFORD_CORE")
        # TODO: fix next line
        ln -s $(find -name \*full\* -type d) core
    fi
}

# Fetch and unpack the language models.
function fetch_stanford_lang_models {
    for lang in $($CONFIG supported_languages | xargs);do
        get_if_not_there $($CONFIG "lang_"$lang"_stanford_ner_source")
    done
    find . -name \*.jar -exec unzip -q -o '{}' ';'
    # TODO: Use config.py to md5sum the models,
    # and move them to the proper dir,
    # delete the rest of unpacked files.
}

# Check if Python2.7 is installed on the os,
# we might need that in the near futute.
is_python2_7_avail() {
    is_avail=$(which python2.7 | wc -l)
    if [ "$is_avail" = "0" ]; then
        inform_user "Python 2.7 is not available, helas. sudo apt-get install python2.7?"
        exit -1
    fi
    inform_user "Python 2.7 is available."
}

# Check if we find (Python) virtualenv.
is_virtualenv_avail() {
    is_avail=$(which virtualenv | wc -l)
    if [ "$is_avail" = "0" ]; then
        inform_user "Virtualenv is not available, helas. sudo-apt-get install virtualenv?"
        exit -1
    fi
    inform_user "Virtualenv is available."
}

# Now move to install dir for installation of core and models.
if [ ! -d 'stanford' ]; then
    mkdir stanford
fi

# If stanford-corenlp-full*.zip is allready there, do nothing.
full=$(find ./stanford/ -name \*full\* | wc -l)
if [ "$full" = "0" ];then
    # Fetch stanford-core from their site,
    # and install it.
    cd stanford
    fetch_stanford_core
    cd ..
else
    inform_user "Not fetching stanford-core, allready there."
fi

# If the models are allready there, do nothing.
if [ ! -d 'stanford/models' ]; then
    # Else fetch and unpack models.
    mkdir -p stanford/models && cd stanford/models
    fetch_stanford_lang_models
    cd ../..
else
    inform_user "Not fetching stanford language models, allready there."
fi

# Check if the virtual env exists, if not, create one and within
# the virtual env install the required packages.
if [ ! -d "env" ]; then
    is_python2_7_avail
    is_virtualenv_avail

    inform_user "Creating new virtualenv using python2.7 in ./env"
    virtualenv -p python2.7 ./env

    inform_user "Entering virtualenv, to leave: deactivate."
    source env/bin/activate

    inform_user "Upgrade pip and setuptools to latest version."
    pip install --upgrade pip setuptools

    if [ -f ~/requirements.txt ]; then
        req="~/requirements.txt"
    else
        req=$(find ~ -name 'requirements.txt'  | grep '/Narralyzer/')
    fi

    if [ -f "$req" ]; then
        inform_user "Installing the following packages."
        cat "$req"
        pip install -r "$req"
    fi
fi

#if [ ! -d 'tika' ]; then
# Tika will take care of most input document conversion.
#TIKA=$($CONFIG tika)
#    mkdir tika && cd tika
#    get_if_not_there $TIKA
#    unzip -q -n basename "$TIKA"
#    rm basename"$TIKA"
#fi
