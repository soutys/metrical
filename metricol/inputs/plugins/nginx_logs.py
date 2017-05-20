# -*- coding: utf-8 -*-

'''nginx log line plugin
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import logging

import dateutil.parser as du_parser


LOG = logging.getLogger(__name__)


def decode_time(value):
    '''Decodes time representation
    '''
    try:
        return int(du_parser.parse(value).timestamp())
    except (OverflowError, ValueError) as exc:
        LOG.warning('%s @ %s', repr(exc), repr(value))


def parse_log_lines(lines, pattern_fn):
    '''Parses log line using pattern
    '''
    for idx, line in enumerate(lines):
        match = pattern_fn(line)
        if not match:
            continue

        data = match.groupdict()
        if 'time' in data:
            data['time'] = decode_time(data['time'])
        if 'uri' in data:
            if data['uri'].count('/') > 1:
                data['uri'] = data['uri'].split('/', 1)[0].replace('.', '_')
            if not data['uri']:
                data['uri'] = '_other'
        if 'http' in data:
            data['http'] = data['http'].replace('.', '_')

        for field in ['uctim', 'uhtim', 'urtim', 'gzip']:
            if field in data and data[field] == '-':
                del data[field]

        if 'pipe' in data:
            if data['pipe'] != 'p':
                del data['pipe']

        LOG.debug('DATA: %s', repr(data))

        time = data.pop('time')
        if time:
            yield (idx, (time, data))
