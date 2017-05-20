# -*- coding: utf-8 -*-

'''common metrics input module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import logging
import time

from metricol.commons import ManageableThread


LOG = logging.getLogger(__name__)


class MetricInput(ManageableThread):
    '''Metrics fetcher / parser class
    '''
    METRIC_TYPE_GAUGE = 'g'
    METRIC_TYPE_COUNTER = 'c'
    METRIC_TYPE_TIMER = 'ms'
    options = []
    absolute_keys = []
    counter_keys = []
    kv_keys = []
    timer_keys = []

    def __init__(self, section, queue):
        self._section = section
        self.queue = queue
        self.cfg = {}
        self.data_parser = lambda data: data
        super(MetricInput, self).__init__(name=self._section.name)


    def prepare_things(self):
        for field in self.options:
            self.cfg[field] = self._section[field]
        self.period = int(self._section.get('period', self.period))
        for field in ['absolute_keys', 'counter_keys', 'kv_keys', 'timer_keys']:
            if field not in self._section:
                continue
            setattr(
                self, field, [_key.strip() for _key in self._section[field].split(',')])


    def do_things(self):
        self.get_metrics()


    def stop_things(self):
        pass


    def fetch_data(self):
        '''Fetches data from service
        '''
        raise NotImplementedError


    def parse_data(self, data):
        '''Parses fetched data
        '''
        if not data:
            return {}

        return self.data_parser(data)


    def iter_metrics(self, key, val, now_ts):
        '''Generates metrics
        '''
        raise NotImplementedError


    def get_metrics(self):
        '''Returns a list of metrics
        '''
        now_ts = time.time()
        data = self.fetch_data()
        for key, val in self.parse_data(data).items():
            for metric_data in self.iter_metrics(key, val, now_ts):
                self.queue.put(metric_data)
