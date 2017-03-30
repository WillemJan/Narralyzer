#!/usr/bin/env python2.7

import os, sys

sys.path.append(os.path.dirname(__file__))
VIRT_ENV = os.path.dirname(__file__) + os.sep + "env/bin/activate_this.py"
execfile(VIRT_ENV, dict(__file__=VIRT_ENV))

#from pprint import pprint
#import tika
#from tika import parser
#parsed = parser.from_file('/data/zevv/shared_stuff/books/0131774298/Expert_C_Programming_-_Deep_C_Secrets.pdf',  'http://localhost:9091/tika')
#nl=NL()
#nl.text=parsed["content"]
#nl.parse()
#pprint(nl.result)

import codecs
import datetime
import magic
import os
import string
import sys
import sys
import xml.etree.ElementTree as etree

from collections import Counter
from dateutil.tz import tzlocal
from flask import *
from flask_mako import MakoTemplates
from langdetect import detect
from time import gmtime, strftime
from werkzeug import secure_filename

UPLOAD_FOLDER = 'upload'

sys.path.append(os.path.dirname(__file__))

application = Flask(__name__)
application.debug = True
application.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

template_path =  os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
application.template_folder = template_path

mako = MakoTemplates(application)

ALLOWED_EXTENSIONS = set(['pdf', 'xml', 'txt'])

def tei_to_chapters(fname):
    """ Convert a TEI 2 xml into an array of chapters with text,
    and return the title.
    """
    data = codecs.open(fname,'r', 'utf-8').read().replace('&nbsp', '')

    utf8_parser = etree.XMLParser(encoding='utf-8')
    book = etree.fromstring(data.encode('utf-8'), parser=utf8_parser)

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
                chapters.append([chap_title, text])
                text = ''
                chap_title = ''

        if 'rend' in item.attrib and not item.text is None:
            text += item.text + "\n"
        if item.tag == "p" and not item.text is None:
            text += item.text + "\n"

    chapters.append([chap_title, text])
    return author, title, chapters

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
    now = str(datetime.datetime.now(tzlocal())).split('.')[:-1][0]
    data = codecs.open(path_uploaded_file,'r', 'utf-8').read()

    t_ascii_letters = 0
    t_punct_letters = 0
    t_noise_letters = 0

    for j in data:
        if j in string.ascii_letters or j in string.digits:
            t_ascii_letters += 1

    for j in data:
        if j in string.punctuation:
            t_punct_letters += 1

    for j in data:
        if j not in string.printable:
            t_noise_letters += 1

    if uploaded_org_filename.lower().endswith('xml'):
        if tei_check(path_uploaded_file):
            ftype = 'xml (TEI 2)'
        else:
            ftype = 'xml (other)'
        author, title, chapters = tei_to_chapters(path_uploaded_file)


    if uploaded_org_filename.lower().endswith('txt'):
        ftype = 'txt'

    if uploaded_org_filename.lower().endswith('pdf'):
        ftype = 'pdf'
        parsed = parser.from_file(path_uploaded_file)
        text=parsed["content"]
        print(text)
        #nl.parse()
        #pprint(nl.result)

    return render_template('file_uploaded.html',
                            filename=uploaded_org_filename,
                            ftype=ftype,
                            datetime=now,
                            filesize=len(data),
                            t_ascii_letters=t_ascii_letters,
                            t_punct_letters=t_punct_letters,
                            t_noise_letters=t_noise_letters,
                            narrative=narrative)

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

@application.route('/', methods=['GET', 'POST'])
def index():
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


            return handle_uploaded_document(upload.filename, path_uploaded_file)

        else:
            error = 'Error: Did not recieve valid file, filename must end with either .xml, .pdf or .txt'
            return render_template('error.html', val=error)

    elif request.method == 'GET' and request.args.get('lang', ''):
        return render_template('analyze.html')

    return render_template('index.html')

if __name__ == "__main__":
    application.run(threaded=True, port=60606, host="fe2")
