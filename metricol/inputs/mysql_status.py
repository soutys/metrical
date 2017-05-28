# -*- coding: utf-8 -*-

'''mysql status metrics input module
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

from mysql.connector import connect, Error

from metricol.inputs import MetricInput


LOG = logging.getLogger(__name__)

STATUS_QUERY = 'SELECT * FROM `information_schema`.`global_status`'
METRICS_RE = re.compile(
    r'(ABORTED|BYTES|COM|CREATED|DELAYED|HANDLER|INNODB_BUFFER_POOL|INNODB_DATA'
    r'|INNODB_LOG|INNODB_OS_LOG|INNODB_PAGES|INNODB_ROW_LOCK|INNODB_ROWS|KEY'
    r'|OPEN|OPENED|QCACHE|SELECT|SLOW|SORT|TABLE_LOCKS|THREADS)_|CONNECTIONS'
    r'|MAX_USED_CONNECTIONS|NOT_FLUSHED_DELAYED_ROWS|QUERIES|QUESTIONS')


class MysqlStatus(MetricInput):
    '''mysql status fetcher / parser class
    '''
    options = ['db_host', 'db_port', 'db_user', 'db_pass', 'prefix']

    def __init__(self, section, queue):
        super(MysqlStatus, self).__init__(section, queue)
        self.prev_values = {}


    def fetch_data(self):
        '''Fetches data from service
        '''
        conn = cur = None
        try:
            conn = connect(
                host=self.cfg['db_host'], port=self.cfg['db_port'],
                user=self.cfg['db_user'], password=self.cfg['db_pass'],
                use_unicode=True, get_warnings=True)
        except Error as exc:
            LOG.warning('%s @ %s', repr(exc), repr(self.cfg))
        else:
            cur = conn.cursor()
            cur.execute(STATUS_QUERY)
            output = {}
            for key, val in cur.fetchall():
                try:
                    output[key] = int(val) if val.isdigit() else float(val)
                except ValueError:
                    pass
            return output
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()


    def iter_metrics(self, key, val, tstamp):
        match = METRICS_RE.match(key)
        if not match:
            return
        subkey = match.group(1)
        if subkey is None:
            metric = key.lower()
        else:
            metric = subkey.lower() + '.' + key[len(subkey) + 1:].lower()

        prev_val = self.prev_values.get(metric)
        self.prev_values[metric] = val
        if prev_val is not None:
            val -= prev_val
            yield (
                self.cfg['prefix'] + metric, val,
                MetricInput.METRIC_TYPE_COUNTER, tstamp)
