#!/usr/bin/env bash

#
# File: run-tests.sh
#
# This file is part of the Narralyzer package.
# see: http://github.com/WillemJan/Narralyzer
#

# Little wrapper to datestamp outgoing messages.
function inform_user() {
    msg="$1"
    timestamp=$(date "+%Y-%m-%d %H:%M")
    echo "$timestamp: Narralyzer start_stanford.sh $msg"
}


# Run a doctest
function run_test() {
    fname="$1"
    inform_user "Running doctests for: $fname"
    python2.7 "$fname" test || exit -1
}

(
# Start Stanford-NER (Which will bind tot a socket on localhost)
# see conf/config.ini

inform_user "Starting Stanford."
. start_stanford.sh waitforstartup

inform_user "Crawling into virtualenv."
. env/bin/activate

run_test "./narralyzer/stanford_ner_wrapper.py"
run_test "./narralyzer/lang_lib.py"
run_test "./narralyzer/utils.py"
run_test "./narralyzer/config.py"

duc index .
duc ls

convert ./artwork/narralyzer_logo_small.png jpg:- | jp2a --colors --width=100 -
) || exit -1
