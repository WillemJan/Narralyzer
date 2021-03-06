#!/usr/bin/env bash

#
# File: start_stanford.sh
#
# This file is part of the Narralyzer package.
# see: http://github.com/WillemJan/Narralyzer
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
    echo "$timestamp: Narralyzer start_stanford.sh $msg"
}

#------------------------------------------------
# /Functions
#------------------------------------------------

#inform_user "Changing directory to $($CONFIG stanford_core)"
#cd $($CONFIG stanford_core)

# Use system wide default java.
JAVA=$(which java)

java_version=($JAVA -version)
inform_user "Using java version: $java_version"

# Use a whopping 4g per language.
JAVA_MEM="-mx4g"

scriptdir=$($CONFIG stanford_core)

# Start several Stanford core servers.
for lang in $($CONFIG supported_languages | xargs); do
    classifier=$($CONFIG lang_"$lang"_stanford_ner)
    port=$($CONFIG lang_"$lang"_stanford_port)
    model_path=$($CONFIG stanford_models)

    count=$(lsof -i tcp -n | grep $port | wc -l)
    if [ "$count" == "1" ]; then
        inform_user "Not starting $lang on port $port for it is allready running."
    else
        inform_user "Starting Stanford-core for language: $lang on port: $port"
        inform_user "$JAVA $JAVA_MEM -Djava.net.preferIPv4Stack=true -cp $scriptdir/\* edu.stanford.nlp.ie.NERServer -port $port -loadClassifier $model_path/$classifier -outputFormat inlineXML"
        (($JAVA $JAVA_MEM -Djava.net.preferIPv4Stack=true -cp $scriptdir/\* edu.stanford.nlp.ie.NERServer -port $port -loadClassifier $model_path/$classifier -outputFormat inlineXML 2>&1) > /dev/null) &
    fi
done

# Wait until the cores are booted and responsive,
# if parameter 'waitforstartup' is given to start_stanford.sh.
for lang in $($CONFIG supported_languages | xargs); do
    port=$($CONFIG lang_"$lang"_stanford_port)
    if [ "$1" == "waitforstartup" ];then
        count=$(lsof -i tcp -n | grep $port | wc -l)
        while [ "$count" != "1" ]; do
            inform_user "Waiting for Stanford-core: $lang port: $port"
            sleep 1
            count=$(lsof -i tcp -n | grep $port | wc -l)
        done
    fi
done
