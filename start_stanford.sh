#!/usr/bin/env bash

#
# File: start_stanford.sh
#
# This file is part of the Narralyzer package.
# see: http://github.com/WillemJan/Narralyzer
#

# Fix *.sh files first, then turn on Travis again
exit


#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#  
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

CONFIG="./narralyzer/config.py"

DE_CLASSIFIER="../models/edu/stanford/nlp/models/ner/german.dewac_175m_600.crf.ser.gz"
DE_PORT=9990

EN_CLASSIFIER="../models/edu/stanford/nlp/models/ner/english.all.3class.distsim.crf.ser.gz"
EN_PORT=9991

# FR_CLASSIFIER="../models/edu/stanford/nlp/models/srparser/frenchSR.beam.ser.gz"
# FR_PORT=9992

NL_CLASSIFIER="../models/dutch.crf.gz"
NL_PORT=9993

SP_CLASSIFIER="../models//edu/stanford/nlp/models/ner/spanish.ancora.distsim.s512.crf.ser.gz"
SP_PORT=9994

SUPPORTED_LANG=$($CONFIG SUPPORTED_LANGUAGES)

# Little wrapper to datestamp outgoing messages.
function inform_user() {
    msg="$1"
    timestamp=$(date "+%Y-%m-%d %H:%M")
    echo "$timestamp: Narralyzer start_stanford.sh $msg"
}

# Path to Stanford-core lib.
# (Should be installed the by install.sh).
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
for lang in $(echo $SUPPORTED_LANG | sort | xargs);do
    classifier=$(eval "echo \$${lang}_CLASSIFIER")
    port=$(eval "echo \$${lang}_PORT")
    is_running=$(ps x | grep "$classifier" | grep -v 'grep' | wc -l)
    if [ "$is_running" == "1" ]; then
        inform_user "Not starting $lang on port $port for it is allready running."
    else
        inform_user "Starting Stanford-core for language: $lang on port: $port"
        inform_user "$JAVA $JAVA_MEM -Djava.net.preferIPv4Stack=true -cp $scriptdir/\* edu.stanford.nlp.ie.NERServer -port $port -loadClassifier $classifier -outputFormat inlineXML"
        # TODO Logging would be nice.
        $JAVA $JAVA_MEM -Djava.net.preferIPv4Stack=true -cp $scriptdir/\* edu.stanford.nlp.ie.NERServer -port $port -loadClassifier $classifier -outputFormat inlineXML > "$LOG$lang.log" 2>&1  &
    fi
done

# Wait until the cores are booted and responsive,
# if parameter 'waitforstartup' is given to start_stanford.sh.
for lang in $(echo $SUPPORTED_LANG | sort | xargs);do
    port=$(eval "echo \$${lang}_PORT")
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
