#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
'''
    narralyzer.config
    ~~~~~~~~~~~~~~~~~

    Handle misc config variables.

    :copyright: (c) 2016 Koninklijke Bibliotheek, by Willem-Jan Faber.
    :license: GPLv3, see LICENCE.txt for more details.
'''

from os import path
from ConfigParser import ConfigParser

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

try:
    from narralyzer.util import logger as logger
except:
    from utils import logger


class Config():
    """
    Configuration file dict.

    >>> config = Config()
    >>> config.get('supported_languages')
    'de en nl sp'
    >>> config.get('SUPPORTED_LANGUAGES')
    'DE EN NL SP'
    >>> config.get('version')
    '0.1'
    """

    config = {
        'config_file': 'conf/config.ini',
        'models': None,
        'root': None,
        'supported_languages': [],
        'version': '0.1',
    }

    logger = None

    def __init__(self):
        # Try to find out where the root of this package is.
        if self.config.get('root', None) is None:
            root = path.join(
                    path.dirname(
                        path.abspath(__file__)))

            root = path.join(root, '..')
            self.config['root'] = path.abspath(root)

        root = self.config['root']

        # Initialize the logger with the name of this class.
        if self.logger is None:
            self.logger = logger(self.__class__.__name__, 'debug')
            self.logger.debug("Assuming root: {0}".format(root))

        # Set the path to the config-file (config.ini).
        config_file = path.join(root, self.config.get('config_file'))
        self.config['config_file'] = config_file

        # Read and parse the config file, 
        # skip if this has been done before.
        if self.config.get('models', None) is None:
            self._parse_config(config_file)

    def _parse_config(self, config_file):
        # Check if the config file at least exists.
        if not path.isfile(config_file):
            msg = ("Could not open config file: {0}".format(
                path.abspath(config_file)))
            self.logger.critical(msg)
            sys.exit(-1)

        # Use https://docs.python.org/3.5/library/configparser.html
        # to open and parse the config.
        config = ConfigParser()
        try:
            config.read(config_file)
            self.logger.debug("Using config file: {0}".format(
                config_file))
        except:
            self.logger.critical("Failed to open: {0}".format(
                config_file))

        # Use the values in the config-file to populate
        # the config dictionary.
        self.config['models'] = {}
        for section in config.sections():
            if section.startswith('lang_'):
                language = section.replace('lang_', '')
                port = config.get(section, 'port')
                ner = config.get(section, 'stanford_ner')
                ner_source = config.get(section, 'stanford_ner_source')

                self.config['models'][language] = {
                        'port': port,
                        'stanford_ner': ner,
                        'stanford_ner_source': ner_source,
                }
            if section == 'main':
                for key in config.items(section):
                    self.config[key[0]] = key[1]

        for language in self.config.get('models'):
            if language not in self.config["supported_languages"]:
                self.config["supported_languages"].append(language)

    def get(self, variable):
        trump_was_here = False
        if variable.isupper():
            variable = variable.lower()
            trump_was_here = True

        result = self.config.get(variable, None)
        if isinstance(result, list):
            if trump_was_here:
                return " ".join(sorted(result)).upper()
            else:
                return " ".join(sorted(result))

        if not isinstance(result, str):
            return None

        elif trump_was_here:
            return result.upper()
        return result

    def __repr__(self):
        current_config = ""
        for item in sorted(self.config):
            current_config += "\n\t{0}: {1}".format(item, self.get(item))
        result = "Available config parameters:\n\t{0}".format(
                current_config.strip())
        return result

if __name__ == "__main__":
    config = Config()
    if len(sys.argv) >= 2 and "test" not in " ".join(sys.argv):
        result = config.get(" ".join(sys.argv[1:]))
        if result is None:
            msg = "Config key {0} unknown.".format(" ".join(sys.argv[1:]))
            config.logger.fatal(msg)
            exit(-1)
        else:
            print(result)
    else:
        if len(sys.argv) >= 2 and "test" in " ".join(sys.argv):
            import doctest
            doctest.testmod(verbose=False)
        else:
            print(config)
