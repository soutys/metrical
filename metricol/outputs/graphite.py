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

from requests import (
    codes,
    RequestException,
    Session,
)

from metricol.outputs import MetricOutput


LOG = logging.getLogger(__name__)


class GraphiteGateway(MetricOutput):
    '''Graphite pusher class
    '''
    options = [
        'scheme', 'host', 'port', 'uri', 'hostname', 'prefix',
        'cafile', 'cli_certfile', 'cli_keyfile']

    def __init__(self, section, queue):
        super(GraphiteGateway, self).__init__(section, queue)
        self.req_session = Session()
        self.url = 'http://localhost/'


    def prepare_things(self):
        super(GraphiteGateway, self).prepare_things()
        self.url = '%(scheme)s://%(host)s:%(port)s%(uri)s' % self.cfg
        self.req_session.headers = {'Host': self.cfg['hostname']}
        self.req_session.stream = False
        self.req_session.allow_redirects = True
        self.req_session.verify = self.cfg['cafile']
        self.req_session.cert = (
            self.cfg['cli_certfile'], self.cfg['cli_keyfile'])


    def _create_socket(self, cfg):
        '''Creates a socket and connects to the service
        '''
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect((self.cfg['host'], int(self.cfg['port'])))
        except (IOError, OSError, socket.timeout, socket.error) as exc:
            LOG.error(
                'Failed to connect to %s @ %s:%s', repr(exc), self.cfg['host'],
                self.cfg['port'])
            sock = None

        return sock


    def do_things(self):
        batch = []
        while True:
            try:
                batch.append(self.queue.get(block=False))
            except Empty:
                break

        if not batch:
            return

        statsite_cfg = cfg['statsite']
        buf = bytes('\n'.join(metrics) + '\n', encoding='utf-8')
        sock = None
        for _ in range(4):
            if sock:
                try:
                    sock.sendall(buf)
                    break
                except (IOError, OSError, socket.timeout, socket.error) as exc:
                    LOG.error(
                        'Failed to write metric: %s @ %s', repr(exc),
                        repr(metrics))
            sock = _create_socket(statsite_cfg)

        if sock:
            sock.close()
