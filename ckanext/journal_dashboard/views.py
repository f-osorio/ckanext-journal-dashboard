from ckan.common import c, request, _, g
import ckan.lib.base as base
import ckan.model as model
import ckan.lib.helpers as h
import ckan.plugins.toolkit as tk
import ckanext.journal_dashboard.helpers as helpers
import ckan.lib.base as base
import ckan.logic as logic

import logging
log = logging.getLogger(__name__)


def dashboard_read(id):
    context = {'model': model, 'session': model.Session,
                'user': g.user or g.author, 'auth_user_obj': g.userobj,
                'save': 'save' in request.params}

    url_parts = request.url.split('/')
    journal_id = url_parts[-2]
    try:
        logic.check_access('dashboard_read', context)
        #return base.render('organization/dashboard.html', extra_vars={'id': id})
        return base.render('organization/test.html', extra_vars={'id': id})
    except logic.NotAuthorized as e:
        h.flash_error("You don't have access to view this page.")
        return h.redirect_to('journals.read', id=journal_id)
    except Exception as e:
        print(e)
        h.flash_error("Something went wrong loading the page, contact the admins.")
        return h.redirect_to('journals.read', id=journal_id)
