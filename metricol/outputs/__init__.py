# -*- coding: utf-8 -*-

'''Common metrics output module
'''

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals,
    with_statement,
)

import logging


from metricol.commons import ManageableThread


LOG = logging.getLogger(__name__)


class MetricOutput(ManageableThread):
    '''Metrics pusher class
    '''
    options = []

    def __init__(self, section, queue):
        self._section = section
        self.queue = queue
        self.cfg = {}
        super(MetricOutput, self).__init__(name=self._section.name)


    def prepare_things(self):
        for field in self.options:
            self.cfg[field] = self._section[field]
        self.period = int(self._section.get('period', self.period))


    def do_things(self):
        pass


    def stop_things(self):
        pass
