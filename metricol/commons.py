# -*- coding: utf-8 -*-

'''Common classes module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import importlib
import inspect
import logging
import sys
import threading
import time

import dateutil.parser as du_parser


LOG = logging.getLogger(__name__)


class ManageableThread(threading.Thread):
    '''Manageable thread class
    '''

    def __init__(self, *args, **kwargs):
        super(ManageableThread, self).__init__(*args, **kwargs)
        self.keep_running = True
        self.period = 10
        LOG.info('%s thread initialized', self.getName())


    def prepare_things(self):
        '''Prepare things
        '''
        raise NotImplementedError


    def do_things(self):
        '''Do things
        '''
        raise NotImplementedError


    def stop_things(self):
        '''Stop things
        '''
        raise NotImplementedError


    def stop(self):
        '''Starts thread stopping process
        '''
        self.keep_running = False
        self.stop_things()
        LOG.info('%s thread stopping...', self.getName())


    def run(self):
        self.prepare_things()
        while self.keep_running:
            LOG.debug('Running...')
            self.do_things()
            for _ in range(self.period):
                if not self.keep_running:
                    break
                time.sleep(1.0)

        LOG.info('%s thread exiting...', self.getName())


def get_method_by_path(method_path):
    '''Returns method by path (root_module.sub_module.(...).a_method)
    '''
    method_mod, method_name = method_path.rsplit('.', 1)
    try:
        importlib.import_module(method_mod)
    except ImportError:
        return None

    mod = sys.modules[method_mod]
    try:
        method_obj = mod.__dict__[method_name]
        if inspect.isfunction(method_obj):
            return method_obj
    except NameError:
        pass

    return None


def decode_time(value):
    '''Decodes time representation
    '''
    try:
        return int(du_parser.parse(value).timestamp())
    except (OverflowError, ValueError) as exc:
        LOG.warning('%s @ %s', repr(exc), repr(value))
