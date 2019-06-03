from ckan.common import c, request, _
import ckan.lib.base as base
import ckan.model as model
import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk
import ckanext.journal_dashboard.helpers as helpers
import ckan.lib.base as base
import ckan.logic as logic


import logging
log = logging.getLogger(__name__)


class DashBoardController(base.BaseController):

    def dashboard_read(self, id):
        print('Getting access?')
        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author, 'auth_user_obj': c.userobj,
                   'save': 'save' in request.params}
        return base.render('organization/dashboard.html', extra_vars={'id': id})
        try:
            logic.check_access('dashboard_read', context)

            return base.render('organization/dashboard.html', extra_vars={'id': id})
        except logic.NotAuthorized as e:
            url_parts = request.url.split('/')
            journal_id = url_parts[-2]
            h.flash_error("You don't have access to view this page.")
            tk.redirect_to(controller='organization', action='read', id=journal_id)
        except Exception as e:
            print('***')
            print(e)
            #base.abort(401, _('Not authorized to access this page'))
