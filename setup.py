#!/usr/bin/env python

import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

def rebuild_manifest():
    with open('MANIFEST.in', 'w') as f:
        for root, dirs, files in os.walk('flask_kibble/templates'):
            if files:
                f.write('include ' + os.path.join(root, '*.html\n'))

        for root, dirs, files in os.walk('flask_kibble/static'):
            if files:
                f.write('include ' + os.path.join(root, '*\n'))

rebuild_manifest()

setup(
    name='flask-kibble',
    version='0.0.1',
    description='Admin interface library for appengine.',
    long_description=read('README.md'),
    author='Chris Targett',
    author_email='chris@xlevus.net',
    url='http://github.com/xlevus/flask-kibble',
    packages=find_packages(
        exclude=['tests'],
    ),
    install_requires=['flask', 'wtforms>=2.0.0', 'wtforms-ndb>=0.0.2'],
    classifiers=[
    ],
    keywords='flask wtforms appengine ndb',
    license='',
    test_suite='nose.collector',
    tests_require=['nose', 'flask-testing', 'mock', 'flask-gae'],
    include_package_data=True,
)
