#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
'''
    narralyzer.config
    ~~~~~~~~~~~~~~~~~

    Handle misc config variables.

    :copyright: (c) 2016 Koninklijke Bibliotheek, by Willem-Jan Faber.
    :license: GPLv3, see licence.txt for more details.
'''

from os import path, listdir
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
    Configuration module.

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
        'self': path.abspath(__file__),
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
            self.logger = logger(self.__class__.__name__, 'info')
            self.logger.debug("Assuming root: {0}".format(root))

        # Set the path to the config-file (config.ini).
        config_file = path.join(root, self.config.get('config_file'))
        self.config['config_file'] = config_file

        # Read and parse the config file,
        # skip if this has been done before.
        if self.config.get('models', None) is None:
            self._parse_config(config_file)

        # Config file was parsable,


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
                language_3166 = section.replace('lang_', '')
                self.config['models'][language_3166] = {
                            'language_3166': language_3166
                }

                for val in config.items(section):
                    if val[0] not in self.config['models'][language_3166]:
                        self.config['models'][language_3166][val[0]] = val[1]

            if section == 'main':
                for key in config.items(section):
                    self.config[key[0]] = key[1]

        for language in self.config.get('models'):
            if language not in self.config["supported_languages"]:
                self.config["supported_languages"].append(language)

    def get(self, variable):
        # If enduser wants caps.
        end_users_wants_uppercase = False
        if variable.isupper():
            variable = variable.lower()
            # Give him or her caps!
            end_users_wants_uppercase = True

        result = self.config.get(variable, None)
        if variable.startswith('lang_'):
            # Special case for the language modes.
            result = self.config.get('models', None)

        # If the requested config variable was not found, exit.
        if not isinstance(result, (str, dict, list)):
            return None

        # Parse the 'models', into lang_en_stanford_port: 9991 fashion.
        if isinstance(result, dict):
            if variable.endswith('stanford_path'):
                requested_language = variable.replace('_stanford_path', '')
                requested_language = requested_language.replace('lang_', '')
                for language_3166 in result:
                    if language_3166 == requested_language:
                        ner_path = self.config.get('stanford_ner_path')
                        ner_path = path.join(
                                self.config.get('root'),
                                ner_path,
                                language_3166)
                        result = listdir(ner_path)[0]
                        result = path.join(ner_path, result)
            else:
                for language_3166 in result:
                    if not isinstance(result, dict):
                        continue
                    for key in result.get(language_3166):
                        key_name = "lang_{0}_{1}".format(language_3166, key)
                        if key_name == variable:
                            result = result.get(language_3166).get(key)
                            break
            if not isinstance(result, str):
                return None

        # Lists will be displayed with spaces in between
        if isinstance(result, list):
            result = " ".join(sorted(result))

        # If the requested variable is one of the .txt files,
        # read the file from disk, and return it.
        if isinstance(result, str):
            if result.endswith(".txt"):
                with open(path.join(self.config.get('root'), result)) as fh:
                    result = ", ".join(
                            [i.strip() for i in (
                                fh.read().split('\n')[:4])])[:-1]

        # Make a wish come true
        if end_users_wants_uppercase:
            return result.upper()
        return result

    def __repr__(self):
        current_config = ""
        for item in sorted(self.config):
            if not self.get(item) is None:
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
