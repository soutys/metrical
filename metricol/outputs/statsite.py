# -*- coding: utf-8 -*-

'''Graphite output plugins module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import logging
from queue import Empty

from statsd.client import StatsClient

from metricol.inputs import MetricInput
from metricol.outputs import MetricOutput


LOG = logging.getLogger(__name__)


class Statsite(MetricOutput):
    '''Statsite pusher class
    '''
    options = ['host', 'port']

    def __init__(self, section, queue):
        super(Statsite, self).__init__(section, queue)
        self.client = None


    def prepare_things(self):
        super(Statsite, self).prepare_things()
        self.client = StatsClient(
            host=self.cfg['host'], port=int(self.cfg['port']), maxudpsize=1024)


    def do_things(self):
        while True:
            try:
                _key, _val, _type, _ = self.queue.get(block=False)
                LOG.info('%s / %s (%s) / %s', _key, _val, type(_val), _type)
                if _type == MetricInput.METRIC_TYPE_GAUGE:
                    self.client.gauge(_key, _val)
                elif _type == MetricInput.METRIC_TYPE_COUNTER:
                    self.client.incr(_key, count=_val)
                elif _type == MetricInput.METRIC_TYPE_TIMER:
                    self.client.timing(_key, _val)
            except Empty:
                break
