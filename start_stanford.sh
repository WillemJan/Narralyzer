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

PATH_TO_STANFORD_CORE="stanford/core/"
inform_user "Changing directory to $PATH_TO_STANFORD_CORE"
cd $PATH_TO_STANFORD_CORE

# Prefix for logfile output name, to turn logging off
# change LOG to "/dev/null".
LOG="stanford_"

# Use system wide default java.
JAVA=$(which java)
# Except if your hostname "fe2"
# So this private litte hack is to be ignored.
if [ $HOSTNAME == "fe2" ]; then
    JAVA=/home/aloha/java/bin/java
fi

java_version=($JAVA -version)
inform_user "Using java version: $java_version"

# Use a whopping 4g per language.
JAVA_MEM="-mx4g"

# From the Stanford repo:
OS=$(uname)
# Some machines (older OS X, BSD, Windows environments) don't support readlink -e
if hash readlink 2>/dev/null; then
  scriptdir=$(dirname $0)
else
  scriptpath=$(readlink -e "$0") || scriptpath=$0
  scriptdir=$(dirname "$scriptpath")
fi

# Fire several stanford core server.
for lang in $($CONFIG supported_languages | xargs); do
    classifier=$($CONFIG lang_"$lang"_stanford_path)
    port=$($CONFIG lang_"$lang"_stanford_port)
    is_running=$(ps x | grep "$classifier" | grep -v 'grep' | wc -l)
    if [ "$is_running" == "1" ]; then
        inform_user "Not starting $lang on port $port for it is allready running."
    else
        inform_user "Starting Stanford-core for language: $lang on port: $port"
        inform_user "$JAVA $JAVA_MEM -Djava.net.preferIPv4Stack=true -cp $scriptdir/\* edu.stanford.nlp.ie.NERServer -port $port -loadClassifier $classifier -outputFormat inlineXML"
        $JAVA $JAVA_MEM -Djava.net.preferIPv4Stack=true -cp $scriptdir/\* edu.stanford.nlp.ie.NERServer -port $port -loadClassifier $classifier -outputFormat inlineXML 2>&1  &
    fi
done

# Wait until the cores are booted and responsive,
# if parameter 'waitforstartup' is given to start_stanford.sh.
for lang in $($CONFIG supported_languages | xargs); do
    port=$($CONFIG lang_$lang_stanford_port)
    if [ "$1" == "waitforstartup" ];then
        count=$(lsof -i tcp -n | grep $port | wc -l)
        while [ "$count" != "1" ]; do
            inform_user "Waiting for Stanford-core: $lang port: $port"
            sleep 1
            count=$(lsof -i tcp -n | grep $port | wc -l)
        done
    fi
done

inform_user "Moving to directory where we started"
cd -
