#!/usr/bin/env python

try:
  from setuptools import setup, find_packages
except ImportError:
  from distutils.core import setup

version = '0.0.1'

setup(
  name='multitrie',
  version=version,
  download_url='https://github.com/Pixelapse/multitrie/tarball/v%s' % version,
  url='http://github.com/Pixelapse/multitrie',
  author='Michael Wu',
  author_email='michael@pixelapse.com',
  maintainer='Pixelapse',
  maintainer_email='hello@pixelapse.com',
  packages=find_packages(),
  description='Implementation of the trie data structure',
  long_description=open('README.md').read(),
  license=open('LICENSE').read()
)
