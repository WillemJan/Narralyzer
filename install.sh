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

# Fetch and unpack the Stanford core package.
function fetch_stanford_core {
    STANFORD_CORE=$($CONFIG stanford_core_source)
    get_if_not_there $STANFORD_CORE
    if [ -f $(basename $STANFORD_CORE) ]; then
        unzip -q -n $(basename "$STANFORD_CORE")
        # Remove the download package aferwards.
        rm $(basename "$STANFORD_CORE")
        # TODO: fix next line
        ln -s $(find -name \*full\* -type d) core
    fi
}

# Moves the retrieved classifiers into there respective lang dir, 
# and generate md5sum usefull for reference later.
function move_classifiers_inplace {
    for lang in $($CONFIG supported_languages | xargs); do
        target_path=$($CONFIG root)
        echo "LANG: $lang"
        echo "target_path: $target_path"
        target_path="$target_path$($CONFIG stanford_ner_path)"/"$lang"
        echo "target_path: $target_path"
        if [ ! -d $target_path ]; then
            mkdir -p $target_path || airbag "Could not create directory: $target_path" $LINENO
            inform_user "Created directory: $target_path"
        fi
        src="$($CONFIG root)"/"$(find stanford/models -name $($CONFIG "lang_"$lang"_stanford_ner") -type f || airbag "Could not find model for $lang." $LINENO)"
        checksum=$(md5sum -b "$src" | cut -d ' ' -f 1 || airbag "Failed to md5sum $src" $LINENO) 
        target="$target_path"/"$checksum"
        inform_user "Moving classifier $src to $target...."
        # SHOWER-THOUGHT: I could also link them, and delete unused files..
        # For now, this feels right.
        mv "$src" "$target" || airbag "Failed to move $src to $target" $LINENO
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
        airbag "Python 2.7 is not available, helas. sudo apt-get install python2.7?" $LINENO
    fi
    inform_user "Python 2.7 is available."
}

# Check if we find (Python) virtualenv.
is_virtualenv_avail() {
    is_avail=$(which virtualenv | wc -l)
    if [ "$is_avail" = "0" ]; then
        airbag "Virtualenv is not available, helas. sudo-apt-get install virtualenv?" $LINENO
    fi
    inform_user "Virtualenv is available."
}

#--------------------------------------------------------
# /Functions
#-------------------------------------------------------

# Create directory stanford if not exists.
path=$($CONFIG root)"/stanford"
if [ ! -d "$path" ]; then
    mkdir -p "$path" || airbag "Could not create dir $path" $LINENO
fi

# If stanford-corenlp-full*.zip is allready there, do nothing.
full=$(find ./stanford/ -name \*full\* | wc -l)
if [ "$full" = "0" ];then
    # Fetch stanford-core and install it.
    cd "$path" || airbag "Could not enter directory: $path" $LINENO
    fetch_stanford_core || airbag "Could not fetch stanford core."
    cd ..
else
    inform_user "Not fetching stanford-core, allready there."
fi

# If the Stanford models are allready there, do nothing.
if [ ! -f 'stanford/models' ]; then
    if [ ! -d 'stanford/models' ]; then
        # Else fetch and unpack models.
        mkdir -p "stanford/models" && cd "stanford/models" || airbag "Could not create/enter directory: $path." $LINENO
        fetch_stanford_lang_models || airbag "Error while fetching language models." $LINENO
        cd ../..

        # Move the Stanford language models to the 'stanford_ner_path',
        # as defined in config.ini. Also fingerpint the models with md5sum,
        # and delete the orginal files.
        stanford_ner_path=$($CONFIG stanford_ner_path)
        if [ ! -d $stanford_ner_path ]; then
            mkdir -p $stanford_ner_path || airbag "Could not create directory: $stanford_ner_path." $LINENO
            move_classifiers_inplace || airbag "Could not move Stanford laguage models in place." $LINENO
            path="$($CONFIG root)""/stanford/models"
            inform_user "Removing unused Stanford models from $path"
            rm -rf "$path" || airbag "Was unable to remove: $path"
            touch "$path"
        else
            inform_user "NER language models allready in place."
        fi
    else
        inform_user "Not fetching stanford language models from upstream, allready there."
    fi
else
    inform_user "Not fetching stanford language models, allready installed."
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

    req=$($CONFIG root)"/requirements.txt"
    if [ -f "$req" ]; then
        inform_user "Running pip -r $req"
        cat "$req"
        pip install -r "$req" || airbag "Something went wrong while installing the required python packages."
    else
        airbag "Could not find requirements.txt in $req"
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
