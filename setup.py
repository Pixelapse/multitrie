#!/usr/bin/env python

try:
  from setuptools import setup, find_packages
except ImportError:
  from distutils.core import setup

import multitrie

setup(
  name='multitrie',
  version=multitrie.__version__,
  url='http://github.com/Pixelapse/multitrie',
  author='Michael Wu',
  author_email='michael@pixelapse.com',
  maintainer='Pixelapse',
  maintainer_email='hello@pixelapse.com',
  packages=find_packages(),
  long_description=open('README.md').read(),
  license=open('LICENSE').read()
)
