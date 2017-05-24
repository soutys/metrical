# -*- coding: utf-8 -*-

'''auth.log line plugin
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
        if 'user' in data:
            data['user'] = data['user'].replace('.', '_')

        LOG.debug('DATA: %s', repr(data))

        time = data.pop('time')
        if time:
            yield (idx, (time, data))
