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
# Goal of this install procedure is to get && install && config tools/language models needed.
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

# Moves the retrieved classifiers
# into there respective lang dir.
function move_classifiers_inplace {
    for lang in $($CONFIG supported_languages | xargs);do
        target_path=$(./narralyzer/config.py stanford_ner_path)
        src=$(find ./stanford/models -name $($CONFIG "lang_"$lang"_stanford_ner") -type f)
        checksum=$(md5sum $src)
        target=$target_path"/"$lang"/"$checksum
        inform_user "Moving classiefer $src to $target"
    done
}

# Fetch and unpack the language models.
function fetch_stanford_lang_models {
    for lang in $($CONFIG supported_languages | xargs);do
        get_if_not_there $($CONFIG "lang_"$lang"_stanford_ner_source")
    done
    find . -name \*.jar -exec unzip -q -o '{}' ';'
}

# Check if Python2.7 is installed on the os,
# we might need that in the near future.
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

# Create directory stanford if not exists.
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

stanford_ner_path=$($CONFIG stanford_ner_path)
echo $stanford_ner_path
if [ ! -d $stanford_ner_path ]; then
    mkdir -p $stanford_ner_path
    move_classifiers_inplace
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
