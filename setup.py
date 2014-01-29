#!/usr/bin/env python

from distutils.core import setup

setup(name='powerdaemon',
      version='1.0',
      description='Power Management server',
      author='Gene Paul Quevedo',
      author_email='gene.quevedo@gmail.com',
      url='',
      package_dir={'': 'src'},	
      py_modules=['PowerManager', 'ipaddressfinder','sessionfinder', 'configreader'],
      #packages=['PowerManager', 'ipaddressfinder','sessionfinder', 'configreader'],
     )