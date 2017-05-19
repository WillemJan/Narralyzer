#!/usr/bin/env python2.7

import os, sys

sys.path.append(os.path.dirname(__file__))
VIRT_ENV = os.path.dirname(__file__) + os.sep + "env/bin/activate_this.py"
execfile(VIRT_ENV, dict(__file__=VIRT_ENV))

import ast
import codecs
import datetime
import magic
import os
import string
import sys
import sys
import xml.etree.ElementTree as etree
import urllib

import narralyzer
from narralyzer import visualize_ners

from collections import Counter
from dateutil.tz import tzlocal
from flask import *
from flask_mako import MakoTemplates
from langdetect import detect
from time import gmtime, strftime
from werkzeug import secure_filename

UPLOAD_FOLDER = '/var/www/narralyzer/upload'

sys.path.append(os.path.dirname(__file__))

application = Flask(__name__)
application.debug = True
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

template_path =  os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
application.template_folder = template_path

mako = MakoTemplates(application)

#ALLOWED_EXTENSIONS = set(['pdf', 'xml', 'txt'])
ALLOWED_EXTENSIONS = set(['xml'])

def tei_to_chapters(fname):
    """ Convert a TEI 2 xml into an array of chapters with text,
    and return the title. """

    data = codecs.open(fname,'r', 'utf-8').read().replace('&nbsp', '')

    utf8_parser = etree.XMLParser(encoding='utf-8')
    book = etree.fromstring(data.encode('utf-8'), parser=utf8_parser)

    all_text = u""
    chapters = []
    chap_title = ''
    text = ''
    title = ''

    for item in book.iter():
        if item.tag == 'author':
            author = item.text
        if item.tag == 'title' and not title and item.attrib.get('type') and item.attrib.get('type') == 'main':
            title = item.text

        if item.tag == 'head':
            if item.attrib and item.attrib.get('rend') and \
            item.attrib.get('rend') == 'h2' and not item.text is None:
                chap_title = item.text

        if item.tag == 'head':
            if item.attrib and item.attrib.get('rend') and \
            item.attrib.get('rend') == 'h3' and not item.text is None:
                chap_title += '\n' + item.text

        if item.tag == 'div':
            if item.attrib and item.attrib.get('type') and \
            item.attrib.get('type') == 'chapter':
                all_text += text
                chapters.append([chap_title, text])
                text = ''
                chap_title = ''

        if 'rend' in item.attrib and not item.text is None:
            text += item.text + "\n"
        if item.tag == "p" and not item.text is None:
            text += item.text + "\n"

    chapters.append([chap_title, text])
    return author, title, chapters, all_text

def tei_check(path_to_file):
    """ Returns true if the file is an TEI-xml
    The following part of the header must be found in the first 10 lines of the file.
    <!DOCTYPE TEI.2 PUBLIC ....
    """
    i=0

    fh = open(path_to_file, 'r')
    for i in range(9):
        data = fh.readline().encode('utf-8')
        if '<!DOCTYPE TEI.2 PUBLIC' in data:
            return True

    return False

def handle_uploaded_document(uploaded_org_filename, path_uploaded_file):
    if uploaded_org_filename.lower().endswith('xml'):
        if tei_check(path_uploaded_file):
            ftype = 'xml (TEI 2)'
            author, title, chapters, all_text = tei_to_chapters(path_uploaded_file)
        else:
            error_msg = 'Uploaded xml file not a TEI file.'
            return render_template('error.html',
                    error_msg=error_msg)

    ner_per_chapter = []

    for chapter in chapters:
        # Apply narralyzer to text, (the first element is chapter name)
        text = narralyzer.Language(chapter[1])
        text.parse()
        if not text.error:
            # TODO: enable next line, later on in the analyze step,
            # walk over all the text to redo-analysis.
            #ner_per_chapter.append(sorted(set(text.result.get('ners'))))
            ner_per_chapter.append(text.result.get('ners'))

    return render_template('characters.html',
            characters=ner_per_chapter,
            filename=uploaded_org_filename)

class Narrative():
    titles = []
    chapters = []
    title = ''
    nr_of_chapters = 0

    def __init__(self, author, title, chapters):
        self.title = title
        self.author = author

        for (title, chapter) in chapters:
            self.chapters.append(chapter)
            self.titles.append(title)

        self.nr_of_chapters = len(chapters)

        lang = []
        for chap in self.chapters:
            lang.append(detect(chap))

        self.lang = Counter(lang).most_common()[0][0]

    def __repr__(self):
        return ('Narrative: %s, consisting of %s chapters.' % (self.title, len(self.chapters)))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@application.route('/characters', methods=['GET', 'POST'])
def characters():
    if request.method == 'POST':
        upload = request.files['file']

        if upload and allowed_file(upload.filename):
            filename = secure_filename(upload.filename)
            path_uploaded_file = os.path.join(application.config['UPLOAD_FOLDER'], filename)
            upload.save(path_uploaded_file)
            upload_magic = ''

            try:
                upload_magic = str(magic.from_file(application.config['UPLOAD_FOLDER'] + os.sep + filename)).lower()
            except:
                error = 'Error: Could not classify file, corrupted file?'
                return render_template('error.html', val=error)

            if not (upload_magic.startswith('pdf') or 'unicode text' in upload_magic or upload_magic.startswith('xml')):
                error = 'Uploaded file type not supported, please upload in pdf, xml(TEI) or txt form. (Got: %s)' % upload_magic
                return render_template('error.html', val=error)
            return handle_uploaded_document(secure_filename(upload.filename), path_uploaded_file)

        else:
            error = 'Error: Did not recieve valid file, filename must end with either .xml, .pdf or .txt'
            return render_template('error.html', val=error)
    else:
        try:
            chapters = request.args.get('chapters').split(',')
        except:
            chapters = "0"

        text = narralyzer.Language(request.args.get('code'))
        text.parse()

        if text.error:
            return render_template('error.html',
                    error_msg=text.error_msg)

        # TODO: write data to disk, and generate a filename
        return render_template('characters.html',
                chapters=['1','2','3'],
                #sorted_characters=
                #sorted(set(text.result.get('ners'))),
                characters=text.result.get('ners'),
                filename='uploaded text',
                #chapters=chapters,
                text=all_text)

@application.route('/analyze', methods=['GET', 'POST'])
def analyze():
    # Combine all characters from all chapters into one long list
    all_characters = []

    name = secure_filename(request.args.get('filename').split('.')[0])

    input_characters = ast.literal_eval(urllib.unquote(request.args.get('characters').decode('utf8')))

    counter = 1
    for char in input_characters:
        characters = []
        for i in char:
            all_characters.append(i)
            characters.append(i)
        visualize_ners.render_chapter(0, name + str(counter), characters)
        counter += 1

    visualize_ners.render_chapter(0, name + '_all', all_characters)



    return render_template('analyze.html', output=name, counter=counter)

@application.route('/chapters', methods=['GET', 'POST'])
def chapters():
    return render_template('chapters.html', raw_text=request.args.get('raw_text'))

@application.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

if __name__ == "__main__":
    application.run(threaded=True, debug=True, port=60606, host="kbresearch.nl")
