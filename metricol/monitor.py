#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Monitoring script
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import configparser
import logging
import os
import signal
import time
from queue import Queue

from metricol.inputs.auth_log_watch import AuthLogWatch
from metricol.inputs.disks_spaces import DisksSpaces
from metricol.inputs.load_info import LoadInfo
from metricol.inputs.log_watch import LogWatch
from metricol.inputs.memory import MemInfo
from metricol.inputs.mysql_status import MysqlStatus
from metricol.inputs.nginx import NginxStatus
from metricol.inputs.redis import RedisInfo
from metricol.inputs.sys_class_net import SysClassNet
from metricol.inputs.uwsgi import UwsgiStats
from metricol.outputs.graphite_gw import GraphiteGateway


LOG = logging.getLogger(__name__)

OUTPUT_PLUGINS = {
    'graphite_gw': GraphiteGateway,
}
INPUT_PLUGINS = {
    'auth_log_watch': AuthLogWatch,
    'disks_spaces': DisksSpaces,
    'load_info': LoadInfo,
    'log_watch': LogWatch,
    'meminfo': MemInfo,
    'mysql_status': MysqlStatus,
    'nginx_status': NginxStatus,
    'redis_info': RedisInfo,
    'sys_class_net': SysClassNet,
    'uwsgi_stats': UwsgiStats,
}
THREADS = []


def signal_recv(signum, _):
    '''Signal receiver
    '''
    LOG.info('Signal received: %s', signum)
    while THREADS:
        thr = THREADS.pop()
        thr.stop()


def config_logger(log_level):
    '''Configures logger
    '''
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s %(name)s %(levelname)s %(module)s:%(lineno)s'
        ' %(threadName)s:%(funcName)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %Z')


def load_config(cfg_fpath):
    '''Loads and parses config
    '''
    config = configparser.SafeConfigParser(strict=False, allow_no_value=True)
    parsed_files = config.read(cfg_fpath)
    if not parsed_files:
        raise RuntimeError('No config file!')

    return config


def main():
    '''Main method
    '''
    config_logger(logging.NOTSET)

    if len(os.sys.argv) != 2:
        LOG.critical('Usage: %s config_file', os.sys.argv[0])
        raise RuntimeError('Aborting...')

    cfg = load_config(os.sys.argv[1])
    output_found = False
    for section_name, _ in cfg.items():
        if section_name.startswith('output:'):
            output_found = True
            break

    if not output_found:
        LOG.critical('No "output:..." section(s) in config')
        raise RuntimeError('Aborting...')

    if 'DEFAULT' in cfg and cfg['DEFAULT'].get('log_level'):
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        config_logger(getattr(logging, cfg['DEFAULT']['log_level'], logging.NOTSET))

    signal.signal(signal.SIGTERM, signal_recv)
    output_queue = Queue()

    for section_name, section_proxy in cfg.items():
        if not section_name.startswith('output:') and \
                not section_name.startswith('input:'):
            continue

        plug_name = section_proxy['plugin']
        if plug_name in OUTPUT_PLUGINS:
            plug_cls = OUTPUT_PLUGINS[plug_name]
        elif plug_name in INPUT_PLUGINS:
            plug_cls = INPUT_PLUGINS[plug_name]
        else:
            raise RuntimeError('Unknown plugin: %s' % repr(plug_name))

        LOG.debug('Plugin: %s', plug_cls.__name__)
        plug_obj = plug_cls(section_proxy, output_queue)
        plug_obj.daemon = False
        plug_obj.start()

        THREADS.append(plug_obj)

    threads_num = len(THREADS)

    LOG.info('Started threads: %s', threads_num)

    # https://www.g-loaded.eu/2016/11/24/how-to-terminate-running-python-threads-using-signals/
    while THREADS:
        time.sleep(1.0)

    LOG.info('Finished threads: %s', threads_num)


if __name__ == '__main__':
    main()


# vim: ts=4:sw=4:et:fdm=indent:ff=unix
