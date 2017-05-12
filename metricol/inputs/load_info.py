# -*- coding: utf-8 -*-

'''load metrics input module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import logging
import re

from metricol.inputs import MetricInput


LOG = logging.getLogger(__name__)

METRIC_RE = re.compile(r'^([.0-9]+) [.0-9]+ [.0-9]+ ([0-9]+)/([0-9]+) [0-9]+$')


def parse_loadavg(buf):
    '''Parses loadavg output
    '''
    match = METRIC_RE.match(buf)
    if not match:
        return {}

    load, running, existing = match.groups()
    return {
        'load': float(load),
        'running': int(running),
        'existing': int(existing),
    }


class LoadInfo(MetricInput):
    '''loadavg fetcher / parser class
    '''
    options = ['loadavg', 'prefix']

    def __init__(self, section, queue):
        super(LoadInfo, self).__init__(section, queue)
        self.data_parser = parse_loadavg


    def fetch_data(self):
        '''Fetches data from service
        '''
        fpath = self.cfg['loadavg']
        try:
            with open(fpath, 'rb') as fd_obj:
                return str(fd_obj.read(), encoding='utf-8')
        except (IOError, OSError) as exc:
            LOG.warning('%s @ %s', repr(exc), repr(fpath))

        return ''


    def iter_metrics(self, key, val, tstamp):
        yield (
            self.cfg['prefix'] + key, val, MetricInput.METRIC_TYPE_GAUGE,
            tstamp)
