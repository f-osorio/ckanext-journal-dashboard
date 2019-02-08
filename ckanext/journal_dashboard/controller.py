from ckan.common import c
import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk
import ckanext.journal_dashboard.helpers as helpers
import ckan.lib.base as base


import logging
log = logging.getLogger(__name__)


class DashBoardController(base.BaseController):

    def dash_show(self, id):
        print("DASHBOARD: {}".format(id))
        return base.render('organization/dashboard.html', extra_vars={'id': id})
