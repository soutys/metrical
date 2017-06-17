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

import gzip
import linecache
import logging
import os
import tracemalloc
from queue import Empty

from requests import (
    codes,
    RequestException,
    Session,
)

from metricol.inputs import MetricInput
from metricol.outputs import MetricOutput


tracemalloc.start()

LOG = logging.getLogger(__name__)


def display_top(snapshot, key_type='lineno', limit=10):
    '''Logs limited top of tracemalloc snapshot
    '''
    snapshot = snapshot.filter_traces((
        tracemalloc.Filter(False, '<frozen importlib._bootstrap>'),
        tracemalloc.Filter(False, '<unknown>'),
    ))
    top_stats = snapshot.statistics(key_type)

    LOG.warning('Top %s lines', limit)
    for index, stat in enumerate(top_stats[:limit], 1):
        frame = stat.traceback[0]
        # replace '/path/to/module/file.py' with 'module/file.py'
        filename = os.sep.join(frame.filename.split(os.sep)[-2:])
        LOG.warning(
            '#%s: %s:%s: %.1f KiB', index, filename, frame.lineno, stat.size / 1024)
        line = linecache.getline(frame.filename, frame.lineno).strip()
        if line:
            LOG.warning('    %s', line)

    other = top_stats[limit:]
    if other:
        size = sum(stat.size for stat in other)
        LOG.warning('%s other: %.1f KiB', len(other), size / 1024)
    total = sum(stat.size for stat in top_stats)
    LOG.warning('Total allocated size: %.1f KiB', total / 1024)


class GraphiteGateway(MetricOutput):
    '''Graphite pusher class
    '''
    options = [
        'scheme', 'host', 'port', 'uri', 'hostname', 'prefix', 'gzip_level',
        'cafile', 'cli_certfile', 'cli_keyfile']

    def __init__(self, section, queue):
        super(GraphiteGateway, self).__init__(section, queue)
        self.req_session = Session()
        self.url = 'http://localhost/'
        self.gzip_level = 0


    def prepare_things(self):
        super(GraphiteGateway, self).prepare_things()
        self.url = '%(scheme)s://%(host)s:%(port)s%(uri)s' % self.cfg
        self.req_session.headers = {'Host': self.cfg['hostname']}
        gzip_level = self.cfg.get('gzip_level')
        if gzip_level and gzip_level.isdigit():
            self.gzip_level = int(gzip_level)
        if self.gzip_level:
            self.req_session.headers['Content-Encoding'] = 'gzip'
        self.req_session.stream = False
        self.req_session.allow_redirects = True
        self.req_session.verify = self.cfg['cafile']
        self.req_session.cert = (
            self.cfg['cli_certfile'], self.cfg['cli_keyfile'])


    def get_metric_line(self, metric_data):
        '''Converts metric data tuple to metric line
        '''
        _key, _val, _type, _ts = metric_data
        _line = _key + ' ' + str(_val) + ' ' + str(_ts)
        if _type == MetricInput.METRIC_TYPE_GAUGE:
            return self.cfg['prefix'] + 'gauges.' + _line
        elif _type == MetricInput.METRIC_TYPE_COUNTER:
            return self.cfg['prefix'] + 'counts.' + _line
        elif _type == MetricInput.METRIC_TYPE_TIMER:
            return self.cfg['prefix'] + 'timers.' + _line

        LOG.warning('Unknown metric type: %s @ %s', _type, _line)


    def do_things(self):
        batch = []
        while True:
            try:
                metric_data = self.queue.get(block=False)
                metric_line = self.get_metric_line(metric_data)
                if metric_line:
                    batch.append(metric_line)
            except Empty:
                break

        if not batch:
            return

        payload = '\n'.join(batch)
        if self.gzip_level:
            payload = gzip.compress(
                bytes(payload, encoding='utf-8'), compresslevel=self.gzip_level)

        try:
            resp = self.req_session.post(self.url, data=payload)
            if resp.status_code != codes['ok']:
                LOG.warning('Code %s @ %s', resp.status_code, repr(self.url))
        except RequestException as exc:
            LOG.warning('%s @ %s', repr(exc), repr(self.url))

        snapshot = tracemalloc.take_snapshot()
        display_top(snapshot)
