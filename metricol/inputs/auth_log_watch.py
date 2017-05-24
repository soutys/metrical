# -*- coding: utf-8 -*-

'''Auth logs' watcher metrics input module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import logging

from metricol.inputs import MetricInput
from metricol.inputs.log_watch import LogWatch


LOG = logging.getLogger(__name__)


class AuthLogWatch(LogWatch):
    '''Auth logs watcher
    '''
    def __init__(self, section, queue):
        super(AuthLogWatch, self).__init__(section, queue)
        self.prev_values = {}


    def iter_metrics(self, _, val, tstamp):
        user = val['user']
        if 'action' in val:
            # sessions
            if val['action'] == 'opened':
                if user in self.prev_values:
                    cnt = self.prev_values[user] + 1
                else:
                    cnt = 1
            else:
                if user in self.prev_values:
                    cnt = self.prev_values[user] - 1
                else:
                    cnt = 0
            if cnt < 0:
                cnt = 0
            self.prev_values[user] = cnt
            yield (
                self.cfg['prefix'] + user, cnt, MetricInput.METRIC_TYPE_GAUGE, tstamp)
        else:
            # attempts
            yield (
                self.cfg['prefix'] + val['method'] + '.' + user, 1,
                MetricInput.METRIC_TYPE_COUNTER, tstamp)
