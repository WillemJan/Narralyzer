#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
    narralyzer.stanford_probablepeople_wrapper
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Implements tiny wrapper for Stanford CoreNLP NER,
    and invokes the awsome powers of probablepeople!

    Hint's on setting up a high-preformance NER-farm.
    http://stanfordnlp.github.io/CoreNLP/corenlp-server.html#dedicated-server
    Or see the hint's in 'lang_lib.py'.

    :copyright: (c) 2016 Koninklijke Bibliotheek, by Willem-Jan Faber.
    :license: GPLv3, see licence.txt for more details.
"""

import logging
import lxml.html
import sys

reload(sys)
sys.setdefaultencoding('utf-8')

from probablepeople import parse
from socket import (AF_INET,
                   error,
                   SHUT_RDWR,
                   socket,
                   SOCK_STREAM)

from contextlib import contextmanager
from django.utils.encoding import smart_text

log = logging.Logger(__name__, logging.DEBUG)


@contextmanager
def _tcpip4_socket(host, port):
    """Open a TCP/IP4 socket to designated host/port.
    This code originates from 'pip install ner',
    but the module itself was broken, so took usefull code
    and improved on it.
    """

    sock = socket(AF_INET, SOCK_STREAM)
    sock.settimeout(50)

    try:
        sock.connect((host, port))
        yield sock
    finally:
        try:
            sock.shutdown(SHUT_RDWR)
        except error:
            log.error("Socket error %s %s" % (host, str(port)))
            pass
        except OSError:
            log.error("OSEerror %s %s" % (host, str(port)))
            pass
        finally:
            sock.close()


def sppw(text, port=False, use_pp=True, host='localhost'):
    """
    Standalone function to wrap and combine Stanford NER and probablepeople.

    >>> res = sppw("Willem-Alexander (Dutch: [ˈʋɪləm aːlɛkˈsɑndər]; Willem-Alexander Claus George Ferdinand; born 27 April 1967) is the King of the Netherlands.", 9991)
    >>> from pprint import pprint;pprint(res)
    {'ners': [{'string': 'Willem-Alexander', 'tag': 'person'},
              {'string': 'Willem-Alexander Claus George Ferdinand',
               'tag': 'person'},
              {'string': 'Netherlands', 'tag': 'location'}],
     'pp': [[('Willem-Alexander', 'GivenName')],
            [('Willem-Alexander', 'CorporationName'),
             ('Claus', 'CorporationName'),
             ('George', 'CorporationName'),
             ('Ferdinand', 'CorporationName')]],
     'raw_ners': [{'string': 'Willem-Alexander', 'tag': 'person'},
                  {'string': 'Willem-Alexander Claus George Ferdinand',
                   'tag': 'person'},
                  {'string': 'Netherlands', 'tag': 'location'}],
     'raw_response': u'<PERSON>Willem-Alexander</PERSON> (Dutch: [\u02c8\u028b\u026al\u0259m a\u02d0l\u025bk\u02c8s\u0251nd\u0259r]; <PERSON>Willem-Alexander Claus George Ferdinand</PERSON>; born 27 April 1967) is the King of the <LOCATION>Netherlands</LOCATION>.'}
    >>> res = sppw("Prof. Albert Einstein vertoeft op het oogenblik te Londen, en gisteravond was hij in Savoy Hotel eeregast aan een diner, gegeven door de Ort and Oze Societies. De voorzitter van de Engelsche sectie dier Vereeniging is Lord • Rothschild ; de voorzitter van de Duitsche sectie is prof. Einstein.  Lord Rothschild presideerde het diner; aan zijn rechterhand zat de beroemdste geleerde van onzen tyd, aan zijn linkerhand de beroemdste dichter, Bernard Shaw. Rechts van Einstein zat Wells.  Het was een gastmaal voor het intellect en z|jn dames.  Ik wil er geen verslag van geven, maar my bepalen tot enkele aanteekeningen.", 9993, True)
    >>> from pprint import pprint;pprint(res)
    {'ners': [{'string': 'Albert Einstein vertoeft', 'tag': 'pers'},
              {'string': 'Londen', 'tag': 'org'},
              {'string': 'gisteravond was hij in Savoy Hotel eeregast',
               'tag': 'org'},
              {'string': 'Ort and Oze Societies', 'tag': 'org'},
              {'string': 'Engelsche', 'tag': 'otros'},
              {'string': u'Vereeniging is Lord \u2022 Rothschild', 'tag': 'org'},
              {'string': 'Duitsche', 'tag': 'otros'},
              {'string': 'Einstein', 'tag': 'pers'},
              {'string': 'Rothschild', 'tag': 'org'},
              {'string': 'zat', 'tag': 'org'},
              {'string': 'Bernard Shaw', 'tag': 'pers'},
              {'string': 'Rechts van Einstein zat Wells', 'tag': 'pers'},
              {'string': 'Het', 'tag': 'pers'}],
     'pp': [[('Albert', 'GivenName'),
             ('Einstein', 'Surname'),
             ('vertoeft', 'Surname')],
            [('Einstein', 'Surname')],
            [('Bernard', 'GivenName'), ('Shaw', 'Surname')],
            [('Rechts', 'GivenName'),
             ('van', 'Surname'),
             ('Einstein', 'Surname'),
             ('zat', 'GivenName'),
             ('Wells', 'Surname')],
            [('Het', 'ShortForm')]],
     'raw_ners': [{'string': 'Albert Einstein vertoeft', 'tag': 'pers'},
                  {'string': 'Londen', 'tag': 'org'},
                  {'string': 'gisteravond was hij in Savoy Hotel eeregast',
                   'tag': 'org'},
                  {'string': 'Ort and Oze Societies', 'tag': 'org'},
                  {'string': 'Engelsche', 'tag': 'otros'},
                  {'string': u'Vereeniging is Lord \u2022 Rothschild',
                   'tag': 'org'},
                  {'string': 'Duitsche', 'tag': 'otros'},
                  {'string': 'Einstein', 'tag': 'pers'},
                  {'string': 'Rothschild', 'tag': 'org'},
                  {'string': 'zat', 'tag': 'org'},
                  {'string': 'Bernard Shaw', 'tag': 'pers'},
                  {'string': 'Rechts van Einstein zat Wells', 'tag': 'pers'},
                  {'string': 'Het', 'tag': 'pers'}],
     'raw_response': u'Prof. <PERS>Albert Einstein vertoeft</PERS> op het oogenblik te <ORG>Londen</ORG>, en <ORG>gisteravond was hij in Savoy Hotel eeregast</ORG> aan een diner, gegeven door de <ORG>Ort and Oze Societies</ORG>. De voorzitter van de <OTROS>Engelsche</OTROS> sectie dier <ORG>Vereeniging is Lord \u2022 Rothschild</ORG> ; de voorzitter van de <OTROS>Duitsche</OTROS> sectie is prof. <PERS>Einstein</PERS>.  Lord <ORG>Rothschild</ORG> presideerde het diner; aan zijn rechterhand <ORG>zat</ORG> de beroemdste geleerde van onzen tyd, aan zijn linkerhand de beroemdste dichter, <PERS>Bernard Shaw</PERS>. <PERS>Rechts van Einstein zat Wells</PERS>.  <PERS>Het</PERS> was een gastmaal voor het intellect en z|jn dames.  Ik wil er geen verslag van geven, maar my bepalen tot enkele aanteekeningen.'}
    >>> res = sppw("Prof. Albert Einstein vertoeft op het oogenblik te Londen, en gisteravond was hij in Savoy Hotel eeregast aan een diner, gegeven door de Ort and Oze Societies. De voorzitter van de Engelsche sectie dier Vereeniging is Lord • Rothschild ; de voorzitter van de Duitsche sectie is prof. Einstein.  Lord Rothschild presideerde het diner; aan zijn rechterhand zat de beroemdste geleerde van onzen tyd, aan zijn linkerhand de beroemdste dichter, Bernard Shaw. Rechts van Einstein zat Wells.  Het was een gastmaal voor het intellect en z|jn dames.  Ik wil er geen verslag van geven, maar my bepalen tot enkele aanteekeningen.", 9993, True)
    >>> from pprint import pprint;pprint(res)
    {'ners': [{'string': 'Albert Einstein vertoeft', 'tag': 'pers'},
              {'string': 'Londen', 'tag': 'org'},
              {'string': 'gisteravond was hij in Savoy Hotel eeregast',
               'tag': 'org'},
              {'string': 'Ort and Oze Societies', 'tag': 'org'},
              {'string': 'Engelsche', 'tag': 'otros'},
              {'string': u'Vereeniging is Lord \u2022 Rothschild', 'tag': 'org'},
              {'string': 'Duitsche', 'tag': 'otros'},
              {'string': 'Einstein', 'tag': 'pers'},
              {'string': 'Rothschild', 'tag': 'org'},
              {'string': 'zat', 'tag': 'org'},
              {'string': 'Bernard Shaw', 'tag': 'pers'},
              {'string': 'Rechts van Einstein zat Wells', 'tag': 'pers'},
              {'string': 'Het', 'tag': 'pers'}],
     'pp': [[('Albert', 'GivenName'),
             ('Einstein', 'Surname'),
             ('vertoeft', 'Surname')],
            [('Einstein', 'Surname')],
            [('Bernard', 'GivenName'), ('Shaw', 'Surname')],
            [('Rechts', 'GivenName'),
             ('van', 'Surname'),
             ('Einstein', 'Surname'),
             ('zat', 'GivenName'),
             ('Wells', 'Surname')],
            [('Het', 'ShortForm')]],
     'raw_ners': [{'string': 'Albert Einstein vertoeft', 'tag': 'pers'},
                  {'string': 'Londen', 'tag': 'org'},
                  {'string': 'gisteravond was hij in Savoy Hotel eeregast',
                   'tag': 'org'},
                  {'string': 'Ort and Oze Societies', 'tag': 'org'},
                  {'string': 'Engelsche', 'tag': 'otros'},
                  {'string': u'Vereeniging is Lord \u2022 Rothschild',
                   'tag': 'org'},
                  {'string': 'Duitsche', 'tag': 'otros'},
                  {'string': 'Einstein', 'tag': 'pers'},
                  {'string': 'Rothschild', 'tag': 'org'},
                  {'string': 'zat', 'tag': 'org'},
                  {'string': 'Bernard Shaw', 'tag': 'pers'},
                  {'string': 'Rechts van Einstein zat Wells', 'tag': 'pers'},
                  {'string': 'Het', 'tag': 'pers'}],
     'raw_response': u'Prof. <PERS>Albert Einstein vertoeft</PERS> op het oogenblik te <ORG>Londen</ORG>, en <ORG>gisteravond was hij in Savoy Hotel eeregast</ORG> aan een diner, gegeven door de <ORG>Ort and Oze Societies</ORG>. De voorzitter van de <OTROS>Engelsche</OTROS> sectie dier <ORG>Vereeniging is Lord \u2022 Rothschild</ORG> ; de voorzitter van de <OTROS>Duitsche</OTROS> sectie is prof. <PERS>Einstein</PERS>.  Lord <ORG>Rothschild</ORG> presideerde het diner; aan zijn rechterhand <ORG>zat</ORG> de beroemdste geleerde van onzen tyd, aan zijn linkerhand de beroemdste dichter, <PERS>Bernard Shaw</PERS>. <PERS>Rechts van Einstein zat Wells</PERS>.  <PERS>Het</PERS> was een gastmaal voor het intellect en z|jn dames.  Ik wil er geen verslag van geven, maar my bepalen tot enkele aanteekeningen.'}
    """
    for s in ("\f", "\n", "\r", "\t", "\v"):  # strip whitespaces
        text = text.replace(s, '')
    text += "\n"  # ensure end-of-line

    with _tcpip4_socket(host, port) as s:
        if not isinstance(text, bytes):
            text = text.encode('utf-8')
        s.sendall(text)

        tagged_text = s.recv(10*len(text))

    result = tagged_text.decode("utf-8")

    ner = {"raw_response": result,
           "raw_ners": [],
           "ners": []}

    result = "<xml>%s</xml>" % result
    res = lxml.html.fromstring(result)

    for item in res.iter():
        if item.tag == 'xml':
            continue
        ner["raw_ners"].append({"string": item.text,
                                "tag": item.tag})

    counter_ners = 0
    ners = []
    for item in ner["raw_ners"]:
        if item.get("tag")[0] == 'i':
            if counter_ners and len(ners) >= counter_ners - 1:
                ners[counter_ners - 1]["string"] += ' ' + item.get("string")
        else:
            tag = item.get("tag")
            if "-" in tag:
                tag = tag.split('-')[1]
            ners.append({"string": item.get("string"),
                         "tag": tag})
            counter_ners += 1
    ner["ners"] = ners

    # Apply probablepeople / (parse and tag)
    if not use_pp:
        ners["pp"] = None
        return ner

    pp = []
    for item in ners:
        # Loop over the Stanford NER (per/ person) results,
        # and apply probablepeople, which raises when fails, (so try).
        if "per" in item["tag"].lower():
            try:
                result = parse(item.get('string'))
            except:
                log.error("Could not run probablepeople")

            if result:
                result = parse(item["string"])
                pp.append(result)
    ner["pp"] = pp
    return ner


if __name__ == '__main__':
    if len(sys.argv) >= 2 and 'test' in " ".join(sys.argv):
        import doctest
        doctest.testmod(verbose=True)

    if len(sys.argv) >= 2 and 'profile' in " ".join(sys.argv):
        from gutenberg.acquire import load_etext
        from gutenberg.cleanup import strip_headers
        from pycallgraph import PyCallGraph
        from pycallgraph.output import GraphvizOutput

        text = smart_text(strip_headers(load_etext(54807)).strip())
        with PyCallGraph(output=GraphvizOutput()):
            stanford_ner_wrapper(text, 9992, True)
