import os
import ckan.model as model
import ckan.plugins.toolkit as tk
from datetime import datetime, timedelta
from ckan.common import request, c, config, g
from collections import OrderedDict, namedtuple
import ckanext.journal_dashboard.journal_classes as jc

import jinja2


engine = model.meta.engine


def get_id_from_url(url):
    parts = url.split('/')
    if 'stats' in parts:
        return parts[-2]
    return parts[-1]


def dashboard_read(context, data_dict=None):
    """ Only administrators should have access """
    user_id = context['auth_user_obj'].id
    user = tk.get_action('user_show')(None, {'id': user_id})
    admin_journals = tk.get_action('organization_list_for_user')(None, {'permission': 'admin'})

    for journal in admin_journals:
        if journal['name'] in request.url:
            return {'success': True}

    if user['sysadmin']:
        return {'success': True}

    return {'success': False,
            'msg': "Not authorized to view page."}


def get_org(id, source='cmd'):
    print('Getting')
    org = jc.Organization(id, source)
    print('Finished')
    return org


def is_published_(name):
    try:
        pck = tk.get_action('package_show')(None, {'id': name})
        if is_private(pck):
            return False
        return True
    except Exception as e:
        return False


def is_private(pkg):
    if not isinstance(pkg, dict):
        return True
    return pkg.get('private', True)


def create_table(data):
    dirc = os.path.dirname(os.path.abspath(__file__))
    path = '/templates/package/table.html'
    with open(dirc + path) as f:
        template = jinja2.Template(f.read())
    return template.render(data)


def get_data(id):
    return jc.Dataset(id)