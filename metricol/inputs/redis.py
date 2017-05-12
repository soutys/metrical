# -*- coding: utf-8 -*-

'''redis metrics input module
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

import redis

from metricol.inputs import MetricInput


LOG = logging.getLogger(__name__)

KEYSPACE_RE = re.compile(r'^db[0-9]+$')
METRICS_MAP = {
    'connected_clients': 'clients',
    'client_longest_output_list': 'clients',
    'client_biggest_input_buf': 'clients',
    'blocked_clients': 'clients',
    'used_memory': 'memory',
    'used_memory_rss': 'memory',
    'used_memory_peak': 'memory',
    'used_memory_lua': 'memory',
    'mem_fragmentation_ratio': 'memory',
    'loading': 'persistence',
    'rdb_changes_since_last_save': 'persistence',
    'rdb_bgsave_in_progress': 'persistence',
    'aof_rewrite_in_progress': 'persistence',
    'aof_rewrite_scheduled': 'persistence',
    'aof_current_size': 'persistence',
    'aof_base_size': 'persistence',
    'aof_pending_rewrite': 'persistence',
    'aof_buffer_length': 'persistence',
    'aof_rewrite_buffer_length': 'persistence',
    'aof_pending_bio_fsync': 'persistence',
    'aof_delayed_fsync': 'persistence',
    'total_connections_received': 'stats',
    'total_commands_processed': 'stats',
    'instantaneous_ops_per_sec': 'stats',
    'rejected_connections': 'stats',
    'sync_full': 'stats',
    'sync_partial_ok': 'stats',
    'sync_partial_err': 'stats',
    'expired_keys': 'stats',
    'evicted_keys': 'stats',
    'keyspace_hits': 'stats',
    'keyspace_misses': 'stats',
    'pubsub_channels': 'stats',
    'pubsub_patterns': 'stats',
    'latest_fork_usec': 'stats',
    'connected_slaves': 'replication',
    'master_repl_offset': 'replication',
    'repl_backlog_active': 'replication',
    'repl_backlog_size': 'replication',
    'repl_backlog_first_byte_offset': 'replication',
    'repl_backlog_histlen': 'replication',
    'used_cpu_sys': 'cpu',
    'used_cpu_user': 'cpu',
    'used_cpu_sys_children': 'cpu',
    'used_cpu_user_children': 'cpu',
}


class RedisInfo(MetricInput):
    '''redis info fetcher / parser class
    '''
    options = ['socket', 'prefix']
    counters_keys = [
        'evicted_keys',
        'expired_keys',
        'keyspace_hits',
        'keyspace_misses',
        'rejected_connections',
        'total_commands_processed',
        'total_connections_received',
    ]

    def __init__(self, section, queue):
        super(RedisInfo, self).__init__(section, queue)
        self.prev_values = {}


    def fetch_data(self):
        '''Fetches data from service
        '''
        sock_path = self.cfg['socket']
        try:
            cli = redis.StrictRedis(unix_socket_path=sock_path)
            return cli.info()
        except redis.exceptions.RedisError as exc:
            LOG.warning('%s @ %s', repr(exc), repr(sock_path))


    def iter_metrics(self, key, val, tstamp):
        match = KEYSPACE_RE.match(key)
        if match:
            for subkey in ['keys', 'expires', 'avg_ttl']:
                yield (
                    self.cfg['prefix'] + 'keyspace.' + key + '.' + subkey,
                    val[subkey], MetricInput.METRIC_TYPE_GAUGE, tstamp)
        elif key in METRICS_MAP and isinstance(val, (int, float)):
            metric_type = MetricInput.METRIC_TYPE_GAUGE
            if key in self.counters_keys:
                metric_type = MetricInput.METRIC_TYPE_COUNTER
                prev_val = self.prev_values.get(key)
                self.prev_values[key] = val
                if prev_val is not None:
                    val -= prev_val

            yield (
                self.cfg['prefix'] + METRICS_MAP[key] + '.' + key,
                val, metric_type, tstamp)
