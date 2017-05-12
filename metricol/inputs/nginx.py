# -*- coding: utf-8 -*-

'''nginx metrics input module
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

from requests import codes, RequestException, Session

from metricol.inputs import MetricInput


LOG = logging.getLogger(__name__)

NGINX_STATUS_RE = re.compile(
    r'Active connections:\s*(?P<active>[0-9]+)\s+'
    r'server accepts handled requests\s+'
    r'(?P<accepts>[0-9]+)\s+(?P<handled>[0-9]+)\s+(?P<requests>[0-9]+)\s+'
    r'Reading:\s*(?P<reading>[0-9]+)\s+Writing:\s*(?P<writing>[0-9]+)\s+'
    r'Waiting:\s*(?P<waiting>[0-9]+)', re.M)


def parse_nginx_status(buf):
    '''Parses nginx status output
    '''
    match = NGINX_STATUS_RE.search(buf)
    if match:
        return match.groupdict()


class NginxStatus(MetricInput):
    '''nginx status fetcher / parser class
    '''
    options = ['scheme', 'host', 'port', 'uri', 'server_name', 'prefix']
    URL_FMT = '%(scheme)s://%(host)s:%(port)s%(uri)s'
    counters_keys = ['accepts', 'handled', 'requests']

    def __init__(self, section, queue):
        super(NginxStatus, self).__init__(section, queue)
        self.data_parser = parse_nginx_status
        self.req_session = Session()
        self.url = 'http://localhost/'
        self.prev_values = {}


    def prepare_things(self):
        super(NginxStatus, self).prepare_things()
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
                return resp.text
        except RequestException as exc:
            LOG.warning('%s @ %s', repr(exc), repr(self.url))

        return ''


    def iter_metrics(self, key, val, tstamp):
        prev_val = val = int(val) if val.isdigit() else float(val)
        metric_type = MetricInput.METRIC_TYPE_GAUGE
        if key in self.counters_keys:
            metric_type = MetricInput.METRIC_TYPE_COUNTER
            prev_val = self.prev_values.get(key)
            self.prev_values[key] = val
            if prev_val is not None:
                val -= prev_val

        if prev_val is not None:
            yield (self.cfg['prefix'] + key, val, metric_type, tstamp)
