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
import socket

from .inputs.nginx import NginxStatus
from .inputs.redis import RedisInfo
from .inputs.uwsgi import UwsgiStats
from .inputs.memory import MemInfo
from .inputs.load_info import LoadInfo


LOG = logging.getLogger(__name__)

INPUTS = {
    'nginx_status': NginxStatus,
    'redis_info': RedisInfo,
    'uwsgi_stats': UwsgiStats,
    'meminfo': MemInfo,
    'load_info': LoadInfo,
}


def load_config(cfg_fpath):
    '''Loads and parses config
    '''
    config = configparser.SafeConfigParser(strict=False, allow_no_value=True)
    parsed_files = config.read(cfg_fpath)
    if not parsed_files:
        raise RuntimeError('No config file!')

    return config


def get_metrics(section_name, section_proxy):
    '''Gets metrics for specified config
    '''
    section_name = section_name.split(':')[0]
    if section_name in INPUTS:
        input_cls = INPUTS[section_name]
        return input_cls(section_proxy).get_metrics()

    return []


def _create_socket(cfg):
    '''Creates a socket and connects to the service
    '''
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((cfg['host'], int(cfg['port'])))
    except (IOError, OSError, socket.timeout, socket.error) as exc:
        LOG.error(
            'Failed to connect to %s @ %s:%s', repr(exc), cfg['host'], cfg['port'])
        sock = None

    return sock


def send_metrics(cfg, metrics):
    '''Sends metrics
    '''
    if not metrics:
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
                LOG.error('Failed to write metric: %s @ %s', repr(exc), repr(metrics))
        sock = _create_socket(statsite_cfg)

    if sock:
        sock.close()


def main():
    '''Main method
    '''
    logging.basicConfig(
        level=logging.NOTSET,
        format='%(asctime)s %(name)s %(levelname)s %(module)s:%(lineno)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S %Z')

    if len(os.sys.argv) != 2:
        LOG.critical('Usage: %s config_file', os.sys.argv[0])
        raise RuntimeError('Aborting...')

    cfg = load_config(os.sys.argv[1])
    if 'statsite' not in cfg:
        LOG.critical('No "statsite" section in config')
        raise RuntimeError('Aborting...')

    metrics = []
    for section_name, section_proxy in cfg.items():
        if not section_proxy.getboolean('enabled', fallback=False):
            continue
        metrics.extend(get_metrics(section_name, section_proxy))
    send_metrics(cfg, metrics)


if __name__ == '__main__':
    main()
