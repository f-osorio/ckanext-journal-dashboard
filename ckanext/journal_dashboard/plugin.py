import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckanext.journal_dashboard.views as view

import ckanext.journal_dashboard.helpers as helpers
from flask import Blueprint

from ckanext.journal_dashboard.command import send


class Journal_DashboardPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.ITemplateHelpers)
    plugins.implements(plugins.IBlueprint)
    plugins.implements(plugins.IClick)


    def get_commands(self):
        return [send]

    def update_config(self, config_):
        toolkit.add_public_directory(config_, 'assets')
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'journal-dashboard')
        toolkit.add_resource('assets', 'dashboard')


    def get_auth_functions(self):
        """ Auth function for new page """
        # Include check_access('dashboard_read') in route to page
        return {
                'dashboard_read': helpers.dashboard_read,
        }

    def get_helpers(self):
        """ template helper functions """
        return {
                'get_org': helpers.get_org,
                'is_published_': helpers.is_published_,
                'get_id_from_url': helpers.get_id_from_url,
                'get_data': helpers.get_data,
                'get_org': helpers.get_org,
        }


    def get_blueprint(self):
        dash = Blueprint(u'dash', self.__module__)
        dash.add_url_rule(u'/journals/<id>/stats',
                          view_func=view.dashboard_read,
                          methods=[u'GET'])

        return dash
