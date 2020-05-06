#!/usr/bin/env python

from setuptools import setup

setup(name='cs2qif',
      version='1.3',
      description='Credit Suisse online banking csv to qif converter.',
      author='Edoardo Di Matteo',
      author_email='edoardo.dimatteo@gmail.com',
      url='https://github.com/edimatt/cs2qif',
      packages=['Qif'],
      install_requires=['chardet'],
      entry_points={
          'console_scripts': ['cs2qif = Qif.QifConverter:parseargs']
      },
      classifiers=['Intended Audience :: End Users/Desktop',
                   'Programming Language :: Python',
                   'Operating System :: MacOS :: MacOS X',
                   'Operating System :: Microsoft :: Windows',
                   'Operating System :: POSIX :: Linux',
                   'License :: OSI Approved :: GNU General Public License v3' +
                   ' or later (GPLv3+)'])
