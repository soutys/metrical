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

import dateutil.parser as du_parser

from metricol.inputs import MetricInput


LOG = logging.getLogger(__name__)


def decode_time(value):
    '''Decodes time representation
    '''
    try:
        return int(du_parser.parse(value).timestamp())
    except (OverflowError, ValueError) as exc:
        LOG.warning('%s @ %s', repr(exc), repr(value))


def parse_log_lines(lines, pattern_fn):
    '''Parses log line using pattern
    '''
    for idx, line in enumerate(lines):
        match = pattern_fn(line)
        if not match:
            continue

        data = match.groupdict()
        if 'time' in data:
            data['time'] = decode_time(data['time'])
        if 'uri' in data:
            if data['uri'].count('/') > 1:
                data['uri'] = data['uri'].split('/', 1)[0].replace('.', '_')
            if not data['uri']:
                data['uri'] = '_other'
        if 'http' in data:
            data['http'] = data['http'].replace('.', '_')

        for field in ['uctim', 'uhtim', 'urtim', 'gzip']:
            if field in data and data[field] == '-':
                del data[field]

        if 'pipe' in data:
            if data['pipe'] != 'p':
                del data['pipe']

        LOG.info('DATA: %s', repr(data))

        yield (idx, (data.pop('time'), data))


class LogWatch(MetricInput):
    '''Logs watcher
    '''
    options = ['log_fpath', 'pattern', 'method', 'prefix']
    counter_keys = [
        'method',
        'uri',
        'http',
        'status',
        'rbytes',
        'bbytes',
        'pipe',
        'fun',
        'lvl',
    ]
    timer_keys = [
        'uctim',
        'uhtim',
        'urtim',
        'rtime',
    ]
    TAIL_CMD_FMT = '/usr/bin/tail --follow=name --lines=1000 --quiet --retry %s'

    def __init__(self, section, queue):
        super(LogWatch, self).__init__(section, queue)
        self.sel_poll = select.poll()
        self.proc = None


    def prepare_things(self):
        super(LogWatch, self).prepare_things()
        cmd = self.TAIL_CMD_FMT % self.cfg['log_fpath']
        pattern = re.compile(self.cfg['pattern'])
        pattern_fn = getattr(pattern, self.cfg['method'])
        self.data_parser = lambda lines: parse_log_lines(
            lines, pattern_fn)

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
        fetched_data = []
        for fileno, _ in self.sel_poll.poll(100):
            if fileno == self.proc.stdout.fileno():
                line = str(self.proc.stdout.readline().strip(), encoding='utf-8')
                if line:
                    fetched_data.append(line)
            elif fileno == self.proc.stderr.fileno():
                line = self.proc.stderr.readline().strip()
                if line:
                    LOG.warning('ERR: %s', repr(line))

        return fetched_data


    def iter_metrics(self, _, val, tstamp):
        for _key, _val in val.items():
            metric_type = MetricInput.METRIC_TYPE_GAUGE
            if _key in self.counter_keys:
                metric_type = MetricInput.METRIC_TYPE_COUNTER
            elif _key in self.timer_keys:
                metric_type = MetricInput.METRIC_TYPE_TIMER

            key = _key
            if _key in ['fun', 'http', 'lvl', 'method', 'status', 'uri', 'pipe']:
                key += '.' + _val
                _val = 1

            yield (self.cfg['prefix'] + key, _val, metric_type, tstamp)


    def get_metrics(self):
        '''Returns a list of metrics
        '''
        data = self.fetch_data()
        for key, (now_ts, val) in self.parse_data(data):
            for metric_data in self.iter_metrics(key, val, now_ts):
                self.queue.put(metric_data)
