#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
    narralyzer.utils
    ~~~~~~~~~~~~~~~~
    Misc utilities to support Narralyzer.

    :copyright: (c) 2016 Koninklijke Bibliotheek, by Willem-Jan Faber.
    :license: GPLv3, see licence.txt for more details.
"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import codecs
import cPickle
import gzip
import json
import logging
import os
import time


# Define how often you want to see messages
DEFAULT_LOGLEVEL = logging.DEBUG

# Define how pretty the logs look
LOG_FORMAT = 'narralyzer.%(name)-12s %(asctime)s %(levelname)-8s "%(message)s"'

# Get the package-base-path
BASE_PATH = ''

# Path to test data
TESTDATA_PATH = os.sep +'test_data' + os.sep

# Path to output files
OUTPUT_PATH = os.sep + 'out' + os.sep

def logger(name, loglevel='warning'):
    try:
        loglevel = getattr(logging,
                        [l for l in dir(logging) if l.isupper() and l.lower() == loglevel].pop())
    except:
        loglevel = DEFAULT_LOGLEVEL

    logger = logging.getLogger(name)
    handler = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(loglevel)
    return logger

def narralyze(input_text, output_name=False, return_json=True, verbose=True):
    from lang_lib import Language

    if not input_text:
        msg = "Did not recieve any text to work with"
        return

    output_name = os.path.join(
            BASE_PATH,
            OUTPUT_PATH,
            output_name
    )

    '''

    if not os.path.isfile(output_name):
        # Open and read the test-book.
        fh = codecs.open(fname_txt, 'r', encoding='utf-8')
        book = fh.read().replace('\n', ' ')
        fh.close()

        # Tag each sentence.
        t = time.time()
        lang = Language(book)
        lang.parse()
        if verbose:
            print("Took %s to parse %s bytes" % (str(round(time.time() - t)),
                                                 str(len(book))))

        # Store the result to a compressed pickle file.
        fh = gzip.GzipFile(ofname, 'wb')
        fh.write(cPickle.dumps(lang.result))
        fh.close()
        result = lang.result
    else:
        if not os.path.isfile(ofname):
            ofname = os.path.join("..", OUTPUT, fname.replace('.txt', '.pickle.gz'))
        # Load the tagged sentences from a compressed pickle file.
        fh = gzip.GzipFile(ofname, 'rb')
        raw_data = ""
        data = fh.read()

        while data:
            raw_data += data
            data = fh.read()

        langlib_result = cPickle.loads(raw_data)
        fh.close()
        result = langlib_result

    if return_json:
        return json.dumps(result)
    return result
    '''

if __name__ == "__main__":
    print("https://www.youtube.com/watch?v=SIIzl-bNtg0")
    #if len(sys.argv) >= 2 and 'test' in " ".join(sys.argv):
    #    import doctest
    #    doctest.testmod(verbose=True)

    #from pprint import pprint
    #book = load_test_book('dutch_book_gbid_20060.txt')
    #pprint(book)
