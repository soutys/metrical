# -*- coding: utf-8 -*-

'''system networking metrics input module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import logging
import glob
import os

from metricol.inputs import MetricInput


LOG = logging.getLogger(__name__)

GLOB_SPEC = '/sys/class/net/%(iface)s/statistics/*'


def parse_net_metrics(fetched_data):
    '''Parses loadavg output
    '''
    output = {}
    for iface, values_dc in fetched_data.items():
        for fpath, value in values_dc.items():
            try:
                output[iface + '.' + os.path.basename(fpath)] = int(value)
            except (TypeError, ValueError):
                pass

    return output


class SysClassNet(MetricInput):
    '''System network fetcher / parser class
    '''
    options = ['interfaces', 'prefix']

    def __init__(self, section, queue):
        super(SysClassNet, self).__init__(section, queue)
        self.data_parser = parse_net_metrics
        self.prev_values = {}


    def fetch_data(self):
        '''Fetches data from system
        '''
        fetched_data = {}
        for iface in [_iface.strip() for _iface in self.cfg['interfaces'].split(',')]:
            fetched_data[iface] = {}
            for fpath in glob.glob(GLOB_SPEC % {'iface': iface}):
                try:
                    with open(fpath, 'rb') as fd_obj:
                        fetched_data[iface][fpath] = str(fd_obj.read(), encoding='utf-8')
                except (IOError, OSError) as exc:
                    LOG.warning('%s @ %s', repr(exc), repr(fpath))

        return fetched_data


    def iter_metrics(self, key, val, tstamp):
        prev_val = self.prev_values.get(key)
        self.prev_values[key] = val
        if prev_val is not None and val >= prev_val:
            val -= prev_val
            yield (self.cfg['prefix'] + key, val, MetricInput.METRIC_TYPE_COUNTER, tstamp)
