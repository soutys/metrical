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

import logging
import threading
import time


LOG = logging.getLogger(__name__)


class ManageableThread(threading.Thread):
    '''Manageable thread class
    '''

    def __init__(self, *args, **kwargs):
        super(ManageableThread, self).__init__(*args, **kwargs)
        self.keep_running = True
        self.period = 10
        LOG.info('Initialized')


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
        LOG.info('Stopping...')


    def run(self):
        self.prepare_things()
        while self.keep_running:
            LOG.debug('Running...')
            self.do_things()
            for _ in range(self.period):
                if not self.keep_running:
                    break
                time.sleep(1.0)

        LOG.info('Exiting...')
