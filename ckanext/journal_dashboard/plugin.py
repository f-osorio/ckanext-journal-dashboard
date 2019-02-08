import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit

import helpers

"""
TODO:
    * Finish arranging data
    X Add badges for unpublished/published
    * Make sortable
    * Rearrange data (tables?)
    * Double check how 'Total Views' is being created
            * doesn't seem to match what the individual views are
    * Visualization?
    *
    *
    *
"""

class Journal_DashboardPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IAuthFunctions)
    plugins.implements(plugins.IRoutes, inherit=True)
    plugins.implements(plugins.ITemplateHelpers)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic', 'journal-dashboard')


    def get_auth_functions(self):
        """ Auth function for new page """
        # Include check_access('dashboard_read') in route to page
        return {
                'dashboard_read': helpers.dashboard_read
        }

    def get_helpers(self):
        """ template helper functions """
        return {
                'get_org': helpers.get_org,
                'get_resources': helpers.get_resources,
                'resource_details': helpers.resource_details,
                'package_tracking': helpers.package_tracking,
                'journal_resource_downloads': helpers.journal_resource_downloads,
                'match_resource_downloads': helpers.match_resource_downloads,
                'is_published_': helpers.is_published_,
        }


    def before_map(self, map):
        """
            new route for journal dash boards
        """
        map.connect('journal_stats','/journals/{id}/stats',
                     controller='ckanext.journal_dashboard.controller:DashBoardController',
                     action='dash_show',
                     ckan_icon='bar-chart')
        return map
