# -*- coding: utf-8 -*-

'''Logs' watcher metrics input module
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
import select
import shlex
import subprocess
import time

from metricol.inputs import MetricInput


LOG = logging.getLogger(__name__)


def parse_log_line(line, pattern):
    '''Parses log line using pattern
    '''
    print(line, pattern)
    return {}


class LogWatch(MetricInput):
    '''Logs watcher
    '''
    options = ['log_fpath', 'pattern', 'prefix']
    TAIL_CMD_FMT = '/usr/bin/tail --follow=name --lines=1000 --quiet --retry %s'

    def __init__(self, section, queue):
        super(LogWatch, self).__init__(section, queue)
        self.sel_poll = select.poll()
        self.proc = None
        self.prev_values = {}


    def prepare_things(self):
        super(LogWatch, self).prepare_things()
        cmd = self.TAIL_CMD_FMT % self.cfg['log_fpath']
        pattern = re.compile(self.cfg['pattern'])
        self.data_parser = lambda line: parse_log_line(line, pattern)

        try:
            self.proc = subprocess.Popen(
                shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=False, close_fds=False)
            self.sel_poll.register(
                self.proc.stdout, select.POLLIN | select.POLLPRI)
            self.sel_poll.register(
                self.proc.stderr, select.POLLIN | select.POLLPRI)
        except OSError as exc:
            LOG.error('%s @ %s', repr(exc), repr(cmd))


    def stop_things(self):
        super(LogWatch, self).stop_things()
        if not self.proc:
            return

        self.proc.kill()
        self.sel_poll.unregister(self.proc.stdout)
        self.sel_poll.unregister(self.proc.stderr)


    def fetch_data(self):
        no_data = True
        for fileno, _ in self.sel_poll.poll(100):
            if fileno == self.proc.stdout.fileno():
                line = self.proc.stdout.readline().strip()
                if line:
                    no_data = False
                    LOG.info('OUT: %s', repr(line))
            elif fileno == self.proc.stderr.fileno():
                line = self.proc.stderr.readline().strip()
                if line:
                    no_data = False
                    LOG.warning('ERR: %s', repr(line))

        if no_data:
            time.sleep(1.0)


    def iter_metrics(self, key, val, tstamp):
        metric_type = MetricInput.METRIC_TYPE_GAUGE
        prev_val = val
        if key in self.counters_keys:
            metric_type = MetricInput.METRIC_TYPE_COUNTER
            prev_val = self.prev_values.get(key)
            self.prev_values[key] = val
            if prev_val is not None:
                val -= prev_val
        elif key in self.timers_keys:
            metric_type = MetricInput.METRIC_TYPE_TIMER

        if prev_val is not None:
            yield (
                self.cfg['prefix'] + key, val, metric_type, tstamp)


    def get_metrics(self):
        '''Returns a list of metrics
        '''
        data = self.fetch_data()
        for key, (now_ts, val) in self.parse_data(data).items():
            for metric_data in self.iter_metrics(key, val, now_ts):
                self.queue.put(metric_data)
