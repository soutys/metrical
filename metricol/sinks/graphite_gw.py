# -*- coding: utf-8 -*-

'''Graphite sink plugin module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import logging
import sys
from queue import Queue

from metricol.outputs.graphite_gw import GraphiteGateway as GraphiteGatewayOutput


LOG = logging.getLogger(__name__)


class GraphiteGateway(GraphiteGatewayOutput):
    '''Graphite gateway sink class
    '''
    def get_metrics(self):
        '''Puts metrics on a queue
        '''
        for metric in sys.stdin.read().split('\n'):
            if metric and metric.count('|') == 2:
                self.queue.put(metric.split('|'))

    def get_metric_line(self, metric_data):
        _key, _val, _ts = metric_data
        return ' '.join([self.cfg['prefix'] + _key, _val, _ts])


def main():
    '''Main method
    '''
    from metricol.monitor import pre_setup

    cfg = pre_setup()

    section_name = 'sink:graphite_gw'
    section_proxy = cfg[section_name]
    output_queue = Queue()

    plug_obj = GraphiteGateway(section_proxy, output_queue)
    plug_obj.daemon = False
    plug_obj.get_metrics()
    plug_obj.start()
    plug_obj.stop()


if __name__ == '__main__':
    main()
