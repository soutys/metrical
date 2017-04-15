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

from . import MetricInput


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
    URL_FMT = '%(scheme)s://%(host)s:%(port)s%(uri)s'

    def fetch_data(self):
        '''Fetches data from service
        '''
        url = self.URL_FMT % self.section
        try:
            headers = {'Host': self.section['server_name']}
            resp = Session().get(
                url, headers=headers, stream=False, allow_redirects=True)
            if resp.status_code == codes['ok']:
                return resp.json()
        except RequestException as exc:
            LOG.warning('%s @ %s', repr(exc), repr(url))

        return {}

    def iter_metrics(self, key, val):
        if key in STRAIGHT_METRICS:
            yield self.section['prefix'] + key + ':' + str(val) + '|g'
        elif key == 'locks':
            for lock in val:
                for _key, _val in lock.items():
                    if _key in LOCK_METRICS:
                        yield self.section['prefix'] + key + '.' \
                            + _key.replace(' ', '_') + ':' + str(_val) + '|c'
        elif key == 'sockets':
            for idx, socket in enumerate(val):
                for _key in ['queue', 'shared']:
                    _val = socket[_key]
                    yield self.section['prefix'] + key + '.' + str(idx) \
                        + '.' + _key + ':' + str(_val) + '|g'
        elif key == 'workers':
            for worker in val:
                for _key in WORKER_METRICS:
                    _val = worker[_key]
                    yield self.section['prefix'] + str(key) + '.' \
                        + str(worker['id']) + '.' + str(_key) + ':' + str(_val) + '|g'
