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

from metricol.commons import decode_time


LOG = logging.getLogger(__name__)


def clean_uri(uri):
    '''Cleans URI
    '''
    if uri.count('/') > 1:
        prefix = uri.split('/', 2)[1]
        if prefix.isalnum():
            return prefix

    return '_other'


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
            data['uri'] = clean_uri(data['uri'])

        for field in ['method', 'uri', 'http']:
            if field not in data:
                continue
            data[field + '.' + data.pop(field).replace('.', '_')] = 1

        for field in ['rbytes', 'bbytes', 'creqs']:
            if field not in data:
                continue
            data[field] = int(data[field])

        for field in ['rtime', 'uctim', 'uhtim', 'urtim', 'gzip']:
            if field not in data:
                continue
            if data[field] == '-':
                del data[field]
            else:
                data[field] = float(data[field])

        if 'pipe' in data:
            if data['pipe'] != 'p':
                del data['pipe']

        LOG.debug('DATA: %s', repr(data))

        time = data.pop('time')
        if time:
            yield (idx, (time, data))
