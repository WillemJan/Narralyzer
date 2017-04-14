#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
    narralyzer.lang_lib
    ~~~~~~~~~~~~~~~~~~~
    Implements sentence level analyzer for natural language.

    Method: Building on the shoulders of giants.

    :copyright: (c) 2016 Koninklijke Bibliotheek, by Willem Jan Faber.
    :license: GPLv3, see licence.txt for more details.
"""

import importlib
import string
import sys

from langdetect import detect
from numpy import mean
from Queue import Queue
from segtok.segmenter import split_multi
from stanford_probablepeople_wrapper import stanford_probablepeople_wrapper
from threading import Thread

try:
    from narralyzer import config
except:
    import config

try:
    from narralyzer import utils
except:
    import utils

reload(sys)
sys.setdefaultencoding('utf-8')

class Language:
    '''
    Intro
    -----
    The ``lang_lib.Language`` class is part of the Narralyzer project.
    This class takes care of chopping up strings/documents into sentences,
    and applies the following:
    
        - Named entity recogniton (Stanford CoreNLP)
          http://nlp.stanford.edu/software/CRF-NER.shtml

                I've recently discovered https://github.com/mitll/MITIE,
                which might be a nice option as well.

        - Part-of-speech tagging (CLiPS-pattern)
          http://www.clips.ua.ac.be/pattern 
                 For this project we've looked at several of those,
                 In Dutch we have the luxory of using either:
                     http://www.let.rug.nl/vannoord/alp/Alpino/ 
                     I've seen this one work, but was not able to install it properly.
                     Guess it's a bit outdated. Anyway have no idea how to install it.

                     https://languagemachines.github.io/frog/
                     Haven't had time to figuere out a way to use it within my repo,
                     takes a long time to build, but will probably out-preform CLiPS.
                
                Since our main focus was at the end NER's, CLiPS will do for now.

        - Sentence segmentation (segtok.segmenter)
          http://fnl.es/segtok-a-segmentation-and-tokenization-library.html

        - Sentiment analyzer (CLiPS-pattern)
          http://www.clips.ua.ac.be/pattern

        - Splitting names (Of detected NER's, as of yet untrained)
          https://github.com/datamade/probablepeople

    Using ``lang_lib.Language``
    ---------------------------
    >>> lang = Language(("Willem-Jan Faber just invoked lang_lib.Language, while wishing he was in West Virginia."))
    Using detected language 'en' to parse input text.
    >>> lang.parse()
    >>> from pprint import pprint; pprint(lang.result)
    {'lang': u'en',
     'sentences': {0: {'count': 0,
                       'pos': [{'string': u'Willem-Jan', 'tag': u'NNP'},
                               {'string': u'Faber', 'tag': u'NNP'},
                               {'string': u'just', 'tag': u'RB'},
                               {'string': u'invoked', 'tag': u'VBN'},
                               {'string': u'lang_lib.Language', 'tag': u'NN'},
                               {'string': u',', 'tag': u','},
                               {'string': u'while', 'tag': u'IN'},
                               {'string': u'wishing', 'tag': u'VBG'},
                               {'string': u'he', 'tag': u'PRP'},
                               {'string': u'was', 'tag': u'VBD'},
                               {'string': u'in', 'tag': u'IN'},
                               {'string': u'West', 'tag': u'NNP'},
                               {'string': u'Virginia', 'tag': u'NNP'},
                               {'string': u'.', 'tag': u'.'}],
                       'sentiment': (0.0, 0.0),
                       'stanford': {'ners': [{'string': 'Willem-Jan Faber',
                                              'tag': 'person'},
                                             {'string': 'West Virginia',
                                              'tag': 'location'}],
                                    'pp': [{'parse': [('Willem-Jan',
                                                       'GivenName'),
                                                      ('Faber', 'Surname')],
                                            'tag': {'GivenName': 'Willem-Jan',
                                                    'Surname': 'Faber'}}],
                                    'raw_ners': [{'string': 'Willem-Jan Faber',
                                                  'tag': 'person'},
                                                 {'string': 'West Virginia',
                                                  'tag': 'location'}],
                                    'raw_response': u'<PERSON>Willem-Jan Faber</PERSON> just invoked lang_lib.Language, while wishing he was in <LOCATION>West Virginia</LOCATION>.'},
                       'stats': {'ascii_lowercase': 71,
                                 'count': 87,
                                 'digits': 0,
                                 'lowercase': 65,
                                 'printable': 87,
                                 'unprintable': 0,
                                 'uppercase': 6},
                       'string': u'Willem-Jan Faber just invoked lang_lib.Language, while wishing he was in West Virginia.'}},
     'stats': {'avg_length': 87, 'max': 87, 'min': 87},
     'text': 'Willem-Jan Faber just invoked lang_lib.Language, while wishing he was in West Virginia.'}

    Source code: https://github.com/KBNLresearch/Narralyzer
    '''
    sentences = {}
    stanford_port = 9990

    use_threads = False
    nr_of_threads = 10

    use_stats = True

    sentiment_avail = True
    config = config.Config()

    def __init__(self, text=False, lang=False, use_langdetect=True):
        if not text:
            msg = "Did not get any text to look at."
            print(msg)
            sys.exit(-1)

        if len(text) < 9:
            msg = "Input text is way to small to say something credible about it."
            print(msg)
            sys.exit(-1)

        detected_lang = False
        if use_langdetect and not lang:
            try:
                detected_lang = detect(text)
                if detected_lang not in STANFORD_NER_SERVERS:
                    msg = "Detected language (%s) is not (yet) supported.\n" % detected_lang
                    print(msg)
                msg = "Using detected language '%s' to parse input text." % detected_lang
                print(msg)
                lang = detected_lang
            except:
                msg = "Could not automaticly detect language."
                print(msg)
        elif use_langdetect and lang:
            msg = "Skipping language detection, user specified %s as language" % lang
            print(msg)

        if not lang or lang not in self.config.get('supported_languages').lower():
            msg = "Did not find suitable language to parse text in."
            print(msg, lang)
            sys.exit(-1)

        self.stanford_port = STANFORD_NER_SERVERS.get(lang)

        pattern = False
        try:
            pattern = importlib.import_module('pattern.' + lang)
        except:
            msg = "Requested language is not (yet) supported, failed to import pattern.%s" % lang
            print(msg)
            sys.exit(-1)

        self._pattern_parse = pattern.parse

        try:
            self._pattern_sentiment = pattern.sentiment
        except:
            self.sentiment_avail = False

        self._pattern_tag = pattern.tag

        self.result = {"text": text,
                       "lang": lang,
                       "sentences": {},
                       "stats": {}}

    def parse(self):
        for count, sentence in enumerate(split_multi(self.result["text"])):
            self.result["sentences"][count] = {"string": sentence,
                                               "pos": [],
                                               "sentiment": [],
                                               "stanford": [],
                                               "count": count}

        if self.use_threads:
            self._threaded_parser()
        else:
            self._parser()

        if self.use_stats:
            self.stats_all()

    def _parser(self):
        for count, sentence in enumerate(self.result["sentences"].values()):
            sentence = sentence.get("string")
            result = self._parse_singleton(sentence, count)
            for item in result:
                self.result["sentences"][count][item] = result[item]

    def _threaded_parser(self):
        work_queue = Queue()
        result_queue = Queue()

        for count, sentence in enumerate(self.result["sentences"].values()):
            work_queue.put({"string": sentence.get("string"),
                            "count": sentence.get("count")})

        nr_of_threads = self.nr_of_threads
        if len(self.result["sentences"]) <= self.nr_of_threads:
            nr_of_threads = len(self.result["sentences"])

        threads = []
        for worker in range(nr_of_threads):
            process = Thread(target=self._parse_queue,
                             args=(work_queue, result_queue))
            process.daemon = True
            process.start()
            threads.append(process)

        for thread in threads:
            thread.join()

        try:
            result = result_queue.get_nowait()
        except:
            msg = "Thread did not recieve input from queue, bye!"
            print(msg)
            result = False

        while result:
            count = result.get('count')
            for item in result:
                if item == 'count':
                    continue
                self.result["sentences"][count][item] = result.get(item)
            try:
                result = result_queue.get_nowait()
            except:
                result = False

    def _parse_queue(self, work_queue, done_queue):
        done = False
        while not done:
            try:
                job = work_queue.get_nowait()
                result = self._parse_singleton(job.get('string'),
                                               job.get('count'))
                done_queue.put(result)
            except:
                done = True

    def _parse_singleton(self, sentence, count):
        result = {"count": count,
                  "pos": False,
                  "sentiment": False,
                  "stanford": False,
                  "stats": False}

        if len(sentence) < 2:
            return result

        if self.sentiment_avail:
            result["sentiment"] = self._pattern_sentiment(sentence)

        res = stanford_probablepeople_wrapper(sentence,
                                              port=self.config.get('models').get(self.lang).get('port'),
                                              use_pp=True)

        pos = []
        for word, pos_tag in self._pattern_tag(sentence):
            pos.append({"string": word, "tag": pos_tag})

        result["pos"] = pos

        return result

    def stats_pos(self):
        pass

    def stats_ner(self):
        pass

    @staticmethod
    def stats_sentence(sentence):
        ascii_letters = count = digits = lowercase = \
         printable = uppercase = unprintable = 0

        for count, char in enumerate(sentence):
            if char in string.printable:
                printable += 1
                if char in string.digits:
                    digits += 1
                elif char in string.ascii_letters:
                    ascii_letters += 1
                    if char in string.ascii_lowercase:
                        lowercase += 1
                    elif char in string.ascii_uppercase:
                        uppercase += 1
            else:
                unprintable += 1

        stats = {"ascii_lowercase": ascii_letters,
                 "count": count + 1,  # a='123'; for i in enumerate(a): print(i)
                 "digits": digits,
                 "lowercase": lowercase,
                 "printable": printable,
                 "uppercase": uppercase,
                 "unprintable": unprintable}

        return stats

    def stats_all(self):
        max_len = min_len = 0  # Min and max sentence length.
        avg = []  # Store all sentence length's.
        for sentence in self.result["sentences"].values():
            # Caluclate the stats per sentence.
            sentence_stats = self.stats_sentence(sentence.get("string"))
            avg.append(sentence_stats.get("count"))

            if sentence_stats.get("count") > max_len:
                max_len = sentence_stats.get("count")

            if sentence_stats.get("count") < min_len:
                min_len = sentence_stats.get("count")

            if min_len == 0:
                min_len = sentence_stats.get("count")

            self.result["sentences"][sentence.get("count")]["stats"] = sentence_stats

        # Caluclate the total stats.
        avg_sentence_length = int(round(mean(avg)))
        stats = {}
        stats["max"] = max_len
        stats["min"] = min_len
        stats["total_len"] = all
        self.result["stats"] = stats

if __name__ == '__main__':
    if len(sys.argv) >= 2 and "test" in " ".join(sys.argv):
        import doctest
        doctest.testmod(verbose=True)

    if len(sys.argv) >= 2 and "time" or "profile" in " ".join(sys.argv):
        import time
        import json

        from django.utils.encoding import smart_text
        from gutenberg.acquire import load_etext
        from gutenberg.cleanup import strip_headers
        from pycallgraph import PyCallGraph
        from pycallgraph.output import GraphvizOutput

        if "time" in " ".join(sys.argv):
            print("Timing non-threaded lang_lib")
            s = time.time()
            lang = Language(text)
            lang.use_threads = False
            lang.parse()
            print("Took %s seconds" % (str(round(s - time.time()) * -1)))

            print("Timing threaded lang_lib")
            s = time.time()
            lang = Language(text)
            lang.use_threads = True
            lang.parse()
            print("Took %s seconds" % (str(round(s - time.time()) * -1)))

            print("Timing ner-vanilla")
            s = time.time()
            stanford_ner_wrapper(text, 9992)
            print("Took %s seconds" % (str(round(s - time.time()) * -1)))

            outfile = "../out/%s.pos_ner_sentiment.json" % gutenberg_test_id
            print("Writing output in json-format to: %s" % outfile)
            with open(outfile, "w") as fh:
                fh.write(json.dumps(lang.result))

            with PyCallGraph(output=GraphvizOutput()):
                lang = Language(text)
                lang.use_threads = True
                lang.parse()
