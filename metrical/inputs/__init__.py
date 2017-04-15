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


LOG = logging.getLogger(__name__)


class MetricInput:
    '''metric fetcher / parser class
    '''
    def __init__(self, section):
        self.section = section
        self.data_parser = lambda data: data

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

    def iter_metrics(self, key, val):
        '''Generates metrics
        '''
        raise NotImplementedError

    def get_metrics(self):
        '''Returns a list of metrics
        '''
        data = self.fetch_data()
        metrics = []
        for key, val in self.parse_data(data).items():
            for metric in self.iter_metrics(key, val):
                metrics.append(metric)

        return metrics
