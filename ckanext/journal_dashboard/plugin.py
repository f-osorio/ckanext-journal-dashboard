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
                'get_resources': helpers.get_resources,
                'resource_details': helpers.resource_details,
                'package_tracking': helpers.package_tracking,
                'journal_resource_downloads': helpers.journal_resource_downloads,
                'is_published_': helpers.is_published_,
                'total_views_across_journal_datasets': helpers.total_views_across_journal_datasets,
                'total_downloads_journal': helpers.total_downloads_journal,
                'journal_download_summary': helpers.journal_download_summary,
                'count_org_resources': helpers.count_org_resources,
                'get_id_from_url': helpers.get_id_from_url,
                'get_packages': helpers.get_packages,
        }


    def get_blueprint(self):
        dash = Blueprint(u'dash', self.__module__)
        dash.add_url_rule(u'/journals/<id>/stats',
                          view_func=view.dashboard_read,
                          methods=[u'GET'])

        return dash
