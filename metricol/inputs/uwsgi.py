# -*- coding: utf-8 -*-

'''uWSGI metrics input module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import logging

from requests import codes, RequestException, Session

from metricol.inputs import MetricInput


LOG = logging.getLogger(__name__)

STRAIGHT_METRICS = [
    'listen_queue',
    'listen_queue_errors',
    'signal_queue',
    'load',
]
LOCK_METRICS = [
    'user 0',
    'signal',
    'filemon',
    'timer',
    'rbtimer',
    'cron',
    'rpc',
    'snmp',
]
WORKER_METRICS = [
    'requests',
    'delta_requests',
    'exceptions',
    'harakiri_count',
    'signals',
    'signal_queue',
    'rss',
    'vsz',
    'respawn_count',
    'tx',
    'avg_rt',
]


class UwsgiStats(MetricInput):
    '''uWSGI status fetcher / parser class
    '''
    options = ['scheme', 'host', 'port', 'uri', 'server_name', 'prefix']
    URL_FMT = '%(scheme)s://%(host)s:%(port)s%(uri)s'

    def __init__(self, section, queue):
        super(UwsgiStats, self).__init__(section, queue)
        self.req_session = Session()
        self.url = 'http://localhost/'
        self.prev_values = {}


    def prepare_things(self):
        super(UwsgiStats, self).prepare_things()
        self.url = self.URL_FMT % self.cfg
        self.req_session.headers = {'Host': self.cfg['server_name']}
        self.req_session.stream = False
        self.req_session.allow_redirects = True


    def fetch_data(self):
        '''Fetches data from service
        '''
        try:
            resp = self.req_session.get(self.url)
            if resp.status_code == codes['ok']:
                return resp.json()
        except RequestException as exc:
            LOG.warning('%s @ %s', repr(exc), repr(self.url))

        return {}


    def iter_metrics(self, key, val, tstamp):
        if key in STRAIGHT_METRICS:
            yield (
                self.cfg['prefix'] + key, val, MetricInput.METRIC_TYPE_GAUGE,
                tstamp)

        elif key == 'locks':
            for lock in val:
                for _key, _val in lock.items():
                    if _key not in LOCK_METRICS:
                        continue
                    mkey = key + '.' + _key.replace(' ', '_')
                    prev_val = self.prev_values.get(mkey)
                    self.prev_values[mkey] = _val
                    if prev_val is not None:
                        _val -= prev_val
                        yield (
                            self.cfg['prefix'] + mkey, _val,
                            MetricInput.METRIC_TYPE_COUNTER, tstamp)

        elif key == 'sockets':
            for idx, socket in enumerate(val):
                for _key in ['queue', 'shared']:
                    yield (
                        self.cfg['prefix'] + key + '.' + str(idx) + '.' + _key,
                        socket[_key], MetricInput.METRIC_TYPE_GAUGE, tstamp)

        elif key == 'workers':
            for worker in val:
                for _key in WORKER_METRICS:
                    yield (
                        self.cfg['prefix'] + key + '.' + str(worker['id']) +
                        '.' + _key,
                        worker[_key], MetricInput.METRIC_TYPE_GAUGE, tstamp)
