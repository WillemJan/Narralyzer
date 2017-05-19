#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
"""
    narralyzer.visualize_ners
    ~~~~~~~~~~~~~~~~~~~~~~~~~
    Implements a dialog visualisation between person's extracted from text.

    :copyright: (c) 2016 Koninklijke Bibliotheek, by Willem Jan Faber.
    :license: GPLv3, see licence.txt for more details.
"""

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

import os
import string
import sys

from django.utils.encoding import smart_text
from graphviz import Digraph
from pprint import pprint


#TODO: the incomming name array should be re-constructed,
# for it is a merged list as input, and we want to iterate over
# the complete chapter again to make sure we get the interactions drawn,
# not a single compressed list of characters.

#TODO: grab the output path from narralyzer config

def analyze(ner_array, dot, filename, source_narrative=['chapter1.txt', 'chapter2.txt', 'chapter3.txt']):
    # The incoming list should be re-run through the text..

    ner = {}
    print("Total nr of NER's: %i " % len(ner_array))
    for item in ner_array:
        if not item in ner:
            ner[item] = 0
        else:
            ner[item] += 1

    ranks = sorted(ner.items(), key=lambda x: x[1])
    to_remove = []

    for item in to_remove:
        ner.pop(item)

    person_matrix = {}

    interaction_scale = 0

    prev_item = ner_array[-1]
    for item in ner:
        person = item
        person_matrix[person] = {}
        for item in ner_array:
            if not item == person and prev_item == person:
                if not item in person_matrix[person]:
                    person_matrix[person][item] = 1
                else:
                    person_matrix[person][item] += 1
                    if person_matrix[person][item] > interaction_scale:
                        interaction_scale = person_matrix[person][item]
            prev_item = item
    translate_table = {}

    i = 0
    j = 0
    for item in person_matrix:
        if j == 0:
            translate_table[item] = string.letters[i]
        else:
            translate_table[item] = string.letters[j] + string.letters[i]
        dot.node(translate_table[item], item)
        i += 1
        if i > 51:
            j += 1
            i = 0

    for item in person_matrix:
        for person in person_matrix[item]:
            if (person_matrix[item][person]):
                if item in translate_table and person in translate_table:
                    dot.edge(translate_table[item],
                             translate_table[person],
                             color=color_code(person_matrix[item][person], interaction_scale),
                             bgcolor='red',
                             arrowtail='both',
                             label=str(person_matrix[item][person]))

    dot.render(filename, view=False, cleanup=True)

def color_code(value, max_value):
    per = (value * (max_value / 100.0)) * 100
    if per < 25.0:
        return 'green'
    if per < 50.0:
        return 'blue'
    if per < 75.0:
        return 'yellow'
    return 'red'


def render_chapter(chapter_nr='0', name='test', ner_array=[]):
    dot = Digraph(comment=name, format='png')
    analyze(ner_array, dot, "/var/www/narralyzer/static/output/" + name)

if __name__ == "__main__":
    name = 'vondel'
    dot = Digraph(comment=name)
    ner_array = []
    result = stanford_ner_wrapper(data, 9991)

    for ner in result.get('ners'):
        if ('per' or 'person') in ner.get('tag'):
            ner_array.append(ner.get('string'))

    analyze(ner_array, dot, name)
