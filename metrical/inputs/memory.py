# -*- coding: utf-8 -*-

'''memory metrics input module
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

from . import MetricInput


LOG = logging.getLogger(__name__)

UNITS = r'kMGTP'
UNIT_BASE = 1024
METRIC_RE = re.compile(r'([A-Za-z]+):\s*([0-9]+)(?:\s*([' + UNITS + r'])B)?')
METRICS_MAP = {
    'MemTotal': 'total',
    'MemFree': 'free',
    'Cached': 'cached',
    'Buffers': 'buffers',
    'SwapTotal': 'swap_total',
    'SwapFree': 'swap_free',
    'Active': 'active',
    'Inactive': 'inactive',
    'Unevictable': 'unevictable',
    'Mlocked': 'mlocked',
    'Dirty': 'dirty',
    'Writeback': 'writeback',
    'AnonPages': 'anon_pages',
    'Shmem': 'shared',
    'SReclaimable': 'slab_reclaim',
    'SUnreclaim': 'slab_unreclaim',
}


def parse_meminfo(buf):
    '''Parses meminfo output
    '''
    metrics_dc = {}
    for match in METRIC_RE.finditer(buf):
        key, val, unit = match.groups()
        if key not in METRICS_MAP:
            continue
        unit_val = 1
        if unit:
            try:
                unit_val = UNIT_BASE ** (UNITS.index(unit) + 1)
            except IndexError:
                pass
        metrics_dc[key] = int(val) * unit_val

    return metrics_dc


class MemInfo(MetricInput):
    '''memory info fetcher / parser class
    '''
    def __init__(self, section):
        super(MemInfo, self).__init__(section)
        self.data_parser = parse_meminfo

    def fetch_data(self):
        '''Fetches data from service
        '''
        fpath = self.section['meminfo']
        try:
            with open(fpath, 'rb') as fd_obj:
                return str(fd_obj.read(), encoding='utf-8')
        except (IOError, OSError) as exc:
            LOG.warning('%s @ %s', repr(exc), repr(fpath))

        return ''

    def iter_metrics(self, key, val):
        yield self.section['prefix'] + METRICS_MAP[key] + ':' + str(val) + '|g'
