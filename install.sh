#!/usr/bin/env bash

# Fix *.sh files first, then turn on Travis again
exit

#
# File: install.sh
#
# This file is part of the Narralyzer package.
# see: http://github.com/WillemJan/Narralyzer

# If you run into troubles try this: 
# 
# sudo apt-get install -y build-essesntials libdb-dev virtualenv python2.7 libxml2-dev libxslt1-dev
#
# Or leave a ping here: https://www.github.com/WillemJan/Narralyzer
#

CONFIG="./narralyzer/config.py"

# Tika will take care of most input document conversion.
TIKA=$($CONFIG tika)

# Where Stanford core lives.
STANFORD_CORE=$($CONFIG stanford_core)

# Where the language models live.
STANFORD_DE="http://nlp.stanford.edu/software/stanford-german-2016-01-19-models.jar"
STANFORD_EN="http://nlp.stanford.edu/software/stanford-english-corenlp-2016-01-10-models.jar"
STANFORD_NL="https://raw.githubusercontent.com/WillemJan/Narralyzer_Dutch_languagemodel/master/dutch.crf.gz"
STANFORD_SP="http://nlp.stanford.edu/software/stanford-spanish-corenlp-2015-10-14-models.jar"

# Little wrapper to datestamp outgoing messages.
function inform_user() {
    msg="$1"
    timestamp=$(date "+%Y-%m-%d %H:%M")
    echo "$timestamp: Narralyzer install.sh $msg"
}

# Fetch the given URL, and save to disk
# use the 'basename' for storing.
function get_if_not_there () {
    URL=$1
    retries=10
    not_done=true
    if [ ! -f $(basename $URL) ]; then
        while not_done; do
           inform_user "Fetching $URL..."
           wget_output=$(wget -q "$URL")
           if [ $? -ne 0 ]; then
               inform_user "Error while fetching $URL, $retries left."
               retries=$(($retries - 1))
           else
               not_done=false
           fi
        done
    else
        inform_user "Not fetching $URL, file allready there."
    fi

}

# Fetch and unpack the Stanford core package.
function fetch_stanford_core {
    get_if_not_there $STANFORD_CORE
    if [ -f $(basename $STANFORD_CORE) ]; then
        unzip -q -n $(basename "$STANFORD_CORE")
        rm $(basename "$STANFORD_CORE")
        ln -s $(find -name \*full\* -type d) core
    fi
}

# Fetch and unpack the language models.
# (Might move them into this repo for ease later).
function fetch_stanford_lang_models {
    get_if_not_there $STANFORD_DE 
    get_if_not_there $STANFORD_EN 
    get_if_not_there $STANFORD_NL
    get_if_not_there $STANFORD_SP
    find . -name \*.jar -exec unzip -q -o '{}' ';'
    # rm *.jar <- Save some diskspace here.
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
    mkdir stanford && cd stanford
else
    cd stanford
fi

    # If stanford-corenlp-full*.zip is allready there, do nothing.
    full=$(find -name \*full\* | wc -l)
    if [ "$full" = "0" ];then
        # Fetch stanford-core from their site,
        # and install it.
        fetch_stanford_core
    else
        inform_user "Not fetching stanford-core, allready there."
    fi

    # If the models are allready there, do nothing.
    if [ ! -d 'models' ]; then
        # Else fetch and unpack models.
        mkdir models && cd models
        fetch_stanford_lang_models
        cd ..
    fi

# Now leave the install dir.
cd ..

# Check if the virtual env exists, if not, create one and within
# the virtual env install the required packages.
if [ ! -d "env" ]; then
    is_python2_7_avail
    is_virtualenv_avail

    inform_user "Creating new virtualenv using python2.7 in ./env"
    virtualenv -p python2.7 ./env

    inform_user "Entering virtualenv, to leave: deactivate"
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
#    mkdir tika && cd tika
#    get_if_not_there $TIKA
#    unzip -q -n basename "$TIKA"
#    rm basename"$TIKA"
#fi
