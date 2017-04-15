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

from . import MetricInput


LOG = logging.getLogger(__name__)

NGINX_STATUS_RE = re.compile(r'Active connections:\s*(?P<active>[0-9]+)\s+' \
    r'server accepts handled requests\s+' \
    r'(?P<accepts>[0-9]+)\s+(?P<handled>[0-9]+)\s+(?P<requests>[0-9]+)\s+' \
    r'Reading:\s*(?P<reading>[0-9]+)\s+Writing:\s*(?P<writing>[0-9]+)\s+' \
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
    URL_FMT = '%(scheme)s://%(host)s:%(port)s%(uri)s'

    def __init__(self, section):
        super(NginxStatus, self).__init__(section)
        self.data_parser = parse_nginx_status

    def fetch_data(self):
        '''Fetches data from service
        '''
        url = self.URL_FMT % self.section
        try:
            headers = {'Host': self.section['server_name']}
            resp = Session().get(
                url, headers=headers, stream=False, allow_redirects=True)
            if resp.status_code == codes['ok']:
                return resp.text
        except RequestException as exc:
            LOG.warning('%s @ %s', repr(exc), repr(url))

        return ''

    def iter_metrics(self, key, val):
        yield self.section['prefix'] + key + ':' + str(val) + '|g'
