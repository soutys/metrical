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
import logging
from queue import Empty

from requests import (
    codes,
    RequestException,
    Session,
)

from metricol.inputs import MetricInput
from metricol.outputs import MetricOutput


LOG = logging.getLogger(__name__)


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


    def do_things(self):
        batch = []
        while True:
            try:
                metric_data = self.queue.get(block=False)
                metric_line = self.get_metric_line(metric_data)
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
