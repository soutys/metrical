# -*- coding: utf-8 -*-

'''File system disks spaces usage metrics input module
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
import shlex
import subprocess

from metricol.inputs import MetricInput


LOG = logging.getLogger(__name__)

DF_CMD_FMT = '/bin/df --all --block-size=1 --output=%(output)s'
DF_COLUMNS = ['target', 'itotal', 'iused', 'iavail', 'size', 'used', 'avail']
SPACES_RE = re.compile(r'\s{2,}', re.M)


def parse_df_metrics(fetched_data, targets):
    '''Parses df output
    '''
    output = {}
    for line in SPACES_RE.sub(' ', fetched_data).splitlines():
        columns = line.split(' ')
        if columns[0] not in targets:
            continue
        label = targets[columns[0]]
        for idx, column in enumerate(DF_COLUMNS[1:]):
            output[label + '.' + column] = int(columns[idx + 1])

    return output


class DisksSpaces(MetricInput):
    '''System disks data fetcher / parser class
    '''
    options = ['targets', 'prefix']

    def __init__(self, section, queue):
        super(DisksSpaces, self).__init__(section, queue)
        self.data_parser = None


    def prepare_things(self):
        super(DisksSpaces, self).prepare_things()
        targets = {}
        for mount_label in self.cfg['targets'].split(','):
            mount, label = mount_label.split(':')
            targets[mount.strip()] = label.strip()
        self.data_parser = lambda fetched_data: parse_df_metrics(
            fetched_data, targets)


    def fetch_data(self):
        fetched_data = ''

        cmd = DF_CMD_FMT % {'output': ','.join(DF_COLUMNS)}
        try:
            with subprocess.Popen(
                shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                shell=False, close_fds=False) as proc:
                err_buf = proc.stderr.read().strip()
                if err_buf:
                    LOG.warning('ERR: %s', repr(err_buf))
                fetched_data = str(proc.stdout.read().strip(), encoding='utf-8')
        except OSError as exc:
            LOG.error('%s @ %s', repr(exc), repr(cmd))

        return fetched_data


    def iter_metrics(self, key, val, tstamp):
        yield (self.cfg['prefix'] + key, val, MetricInput.METRIC_TYPE_GAUGE, tstamp)
