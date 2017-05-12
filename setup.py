# -*- coding: utf-8 -*-

'''Setup script
'''

import os

from setuptools import setup, find_packages


WORK_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(WORK_DIR)
os.sys.path.insert(1, WORK_DIR)

PKG_NAME = os.path.basename(WORK_DIR)
PKG_MOD = __import__(PKG_NAME)

PKG_AUTHOR_NAME, PKG_AUTHOR_EMAIL = PKG_MOD.__author__.rsplit(' ', 1)
PKG_AUTHOR_EMAIL = PKG_AUTHOR_EMAIL.strip('<>')

PKG_VERSION = PKG_MOD.__version__
PKG_CLASSIFIERS = PKG_MOD.__classifiers__

PKG_INFO = open(os.path.join(WORK_DIR, 'README.rst'), 'r').readlines()
PKG_DESC_SHORT = PKG_INFO[0]
PKG_DESC_LONG = ''.join(PKG_INFO)

PKG_LICENSE_FULL = open(os.path.join(WORK_DIR, 'LICENSE'), 'r').readlines()
PKG_LICENSE_NAME = PKG_LICENSE_FULL[0].strip()

PKG_REQS = open(os.path.join(WORK_DIR, 'requirements.txt')).readlines()


setup(
    name=PKG_NAME,
    version=PKG_VERSION,
    author=PKG_AUTHOR_NAME,
    author_email=PKG_AUTHOR_EMAIL,
    url='https://github.com/soutys/' + PKG_NAME,
    maintainer=PKG_AUTHOR_NAME,
    maintainer_email=PKG_AUTHOR_EMAIL,
    description=PKG_DESC_SHORT,
    long_description=PKG_DESC_LONG,
    classifiers=PKG_CLASSIFIERS,
    install_requires=PKG_REQS,
    packages=find_packages(),
    license=PKG_LICENSE_NAME,
    keywords='system services monitoring',
    test_suite='tests',
    entry_points={
        'console_scripts': [
            PKG_NAME + ' = ' + PKG_NAME + '.cmd:main',
        ],
    },
)


# vim: ts=4:sw=4:et:fdm=indent:ff=unix
