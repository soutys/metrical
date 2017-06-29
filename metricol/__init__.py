# -*- coding: utf-8 -*-

'''Package info module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import os

__author__ = 'soutys <soutys@example.com>'
__version__ = open(
    os.path.join(os.path.dirname(__file__), 'VERSION'), 'r').read().strip()
# https://pypi.python.org/pypi?%3Aaction=list_classifiers
__classifiers__ = [
    'Development Status :: 1 - Planning',
    # 'Development Status :: 2 - Pre-Alpha',
    # 'Development Status :: 3 - Alpha',
    # 'Development Status :: 4 - Beta',
    # 'Development Status :: 5 - Production/Stable',
    # 'Development Status :: 6 - Mature',
    # 'Development Status :: 7 - Inactive',
    'Environment :: Other Environment',
    'Intended Audience :: Developers',
    'Intended Audience :: System Administrators',
    'License :: OSI Approved :: MIT License',
    'Operating System :: POSIX',
    'Operating System :: POSIX :: Linux',
    'Programming Language :: Python',
    'Programming Language :: Python :: 3 :: Only',
    'Topic :: Scientific/Engineering',
    'Topic :: Scientific/Engineering :: Information Analysis',
    'Topic :: System',
    'Topic :: System :: Benchmark',
    'Topic :: System :: Monitoring',
    'Topic :: System :: Networking :: Monitoring',
    'Topic :: System :: Systems Administration',
    'Topic :: Utilities',
]


# vim: ts=4:sw=4:et:fdm=indent:ff=unix
