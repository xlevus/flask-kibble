#!/usr/bin/env python

from setuptools import setup

import os
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(name='flask-ndb-crud',
    version='0.0.1',
    description='CRUD library for appengine.',
    long_description=read('README.md'),
    author='Chris Targett',
    author_email='chris@xlevus.net',
    url='http://github.com/xlevus/flask-ndb-crud',
    packages=['flask_ndbcrud'],
    install_requires = ['flask','wtforms'],
    classifiers=[
    ],
    keywords='flask wtforms appengine ndb',
    license='',
    test_suite='nose.collector',
    tests_require=['nose'],
)
