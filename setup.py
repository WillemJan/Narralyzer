#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
""" Setup script for Narralyzer """

import os
import sys

from narralyzer import config

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

if sys.argv[-1] == 'test':
    sys.exit(os.system('./run-tests.sh'))

# define entry points
entry_point = ("""
    [console_scripts]
    config=narralyzer:narralyzer_config
""")

config = config.Config()
required = config.get('required')

setup(
    author=config.get('author'),
    description="Narralyzer",
    entry_points=entry_point,
    install_requires=required,
    license='GPLv3',
    name='narralyzer',
    package_dir=[],
    url='http://kbresearch.nl/narralyzer',
    version=config.get('version'),
)
