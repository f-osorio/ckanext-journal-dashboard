import os
from pylons import config
import ckan.model as model
from urlparse import urlparse
import ckan.plugins.toolkit as tk
from datetime import datetime, timedelta
from ckan.common import request, c, response
from collections import OrderedDict, namedtuple

import jinja2


engine = model.meta.engine


def get_id_from_url(url):
    parts = url.split('/')
    return parts[-2]


def count_org_resources(org):
    sql = """
        SELECT COUNT(r.name)
        FROM resource as r
        JOIN package as p
            ON r.package_id = p.id
        WHERE p.owner_org = %(org)s
            AND r.state = 'active'
            AND p.state = 'active';
    """
    results = engine.execute(sql, org=org).fetchall()
    return results[0][0]


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


def get_org(id):
    data = {
                'id': id,
                'include_datasets': True
            }
    try:
        org = tk.get_action('organization_show')(None, data)
    except:
        context = {'user': 'default'}
        org = tk.get_action('organization_show')(context, data)

    return org


def package_tracking(id):
    try:
        tracking_summary = tk.get_action('package_show')(None, {'id': id, 'include_tracking': True})['tracking_summary']
    except TypeError:
        context = {'user': 'default'}
        tracking_summary = tk.get_action('package_show')(context, {'id': id, 'include_tracking': True})['tracking_summary']
    return tracking_summary


def get_resources(id):
    try:
        resources = tk.get_action('package_show')(None,{'id':id})['resources']
    except TypeError:
        context = {'user': 'default'}
        resources = tk.get_action('package_show')(context, {'id': id})['resources']

    return sorted(resources, key=lambda k: k['url'])


def resource_details(id):
    resource = tk.get_action('resource_show')(None, {'id': id, 'include_tracking': True})
    return resource


def journal_resource_downloads(journal_id, engine_check=None, monthly=False):
    """
    A new row is added to the database each time there is a download.
    This is the reason for the looping at the bottom - findind only the most
    recent values
    """
    today = datetime.now()
    target_period = today - timedelta(days=30)
    return_dict = {}
    sql_total = """
        SELECT r.id, r.url, ts.running_total, ts.recent_views, ts.tracking_date, ts.url, r.format
        FROM package as p
        JOIN resource as r
            ON r.package_id = p.id
        JOIN tracking_summary as ts
            ON ts.url = r.url
        WHERE p.owner_org = %(id)s;
        """

    sql_monthly = """
        SELECT r.id, r.url, ts.running_total, ts.recent_views, ts.tracking_date, ts.url, r.format
        FROM package as p
        JOIN resource as r
            ON r.package_id = p.id
        JOIN tracking_summary as ts
            ON ts.url = r.url
        WHERE p.owner_org = %(id)s
            AND ts.tracking_date >= %(time)s::date;
        """
    if engine_check is None:
        if not monthly:
            results = engine.execute(sql_total, id=journal_id).fetchall()
        else:
            results = engine.execute(sql_monthly, id=journal_id, time=target_period).fetchall()
    else:
        if not monthly:
            results = engine_check.execute(sql_total, id=journal_id).fetchall()
        else:
            results = engine_check.execute(sql_monthly, id=journal_id, time=target_period).fetchall()

    for result in results:
        if result[1] in return_dict.keys():
            if return_dict[result[1]][3] < result[4]:
                return_dict[result[1]] = [result[2], result[3], result[6], result[4]]
        else:
            return_dict[result[1]] = [result[2], result[3], result[6], result[4]]
    # values: total, recent, format, date
    return return_dict



def journal_download_summary(id, package, engine_check=None):
    """
        id: of owner org
        package: id
    """
    today = datetime.now()
    target_period = today - timedelta(days=30)
    return_dict = OrderedDict()
    sql = """
        SELECT r.id, r.url, ts.running_total, ts.recent_views, ts.tracking_date, ts.url, r.format
        FROM package as p
        JOIN resource as r
            ON r.package_id = p.id
        JOIN tracking_summary as ts
            ON ts.url = r.url
        WHERE p.owner_org = %(id)s;
        """
    if engine_check is None:
        results = engine.execute(sql, id=id).fetchall()
    else:
        results = engine_check.execute(sql, id=id).fetchall()
    package_resources = get_resources(package)
    match = False
    for item in package_resources:
        if item['id'] in [result[0] for result in results]:
            for result in results:
                if item['id'] == result[0]:
                    if item['id'] in return_dict.keys():
                        if return_dict[item['id']]['date'] < result[4]:
                            return_dict[item['id']] = {'name': item['name'], 'package_id': item['package_id'], 'id': item['id'], 'url': item['url'], 'format': item['format'], 'total': result[2], 'recent': result[3], 'date': result[4]}
                    else:
                        return_dict[item['id']] = {'name': item['name'], 'package_id': item['package_id'], 'id': item['id'], 'url': item['url'], 'format': item['format'], 'total': result[2], 'recent': result[3], 'date': result[4]}
        else:
            return_dict[item['id']] = {'name': item['name'], 'package_id': item['package_id'], 'id': item['id'], 'url': item['url'], 'format': item['format'], 'total': 0}

    # sort values based on total
    return OrderedDict(sorted(return_dict.items(),key=lambda x: x[1]['total'], reverse=True))



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


def total_views_across_journal_datasets(journal_id, engine_check=None):
    sql = """
            SELECT g.id, SUM(ts.count)
            FROM "group" as g
            JOIN package as p
                ON g.id = p.owner_org
            JOIN tracking_summary as ts
                ON ts.package_id = p.id
            WHERE p.state = 'active'
                AND p.owner_org = %(id)s
            GROUP BY g.id;
        """
    if engine_check is None:
        results = engine.execute(sql, id=journal_id).fetchall()
    else:
        results = engine_check.execute(sql, id=journal_id).fetchall()

    return results[0][1]


def last_month_views_across_journal_datasets(journal_id, engine_check=None):
    target_period = datetime.now() - timedelta(days=30)

    sql = """
            SELECT g.id, SUM(ts.count)
            FROM "group" as g
            JOIN package as p
                ON g.id = p.owner_org
            JOIN tracking_summary as ts
                ON ts.package_id = p.id
            WHERE p.state = 'active'
                AND p.owner_org = %(id)s
                AND ts.tracking_date >= %(time)s::date
            GROUP BY g.id;
        """
    if engine_check is None:
        results = engine.execute(sql, id=journal_id, time=target_period).fetchall()
    else:
        results = engine_check.execute(sql, id=journal_id, time=target_period).fetchall()

    try:
        return results[0][1]
    except IndexError:
        return 0


def total_downloads_journal(journal_id, engine_check=None, monthly=False):
    if engine_check is None:
        if not monthly:
            data = journal_resource_downloads(journal_id, monthly=monthly)
    else:
        data = journal_resource_downloads(journal_id, engine_check, monthly=monthly)
    total = 0
    print('total')
    for k,v in data.items():
        if not monthly:
            total += v[0]
        else:
            total += v[1]
    return total


def create_email(data):
    with open('./ckanext/journal_dashboard/templates/package/text.html') as file:
        template = jinja2.Template(file.read())
    return template.render(data, is_published=is_published_, package_tracking=package_tracking, journal_download_summary=journal_download_summary)


def create_table(data):
    dirc = os.path.dirname(os.path.abspath(__file__))
    path = '/templates/package/table.html'
    with open(dirc + path) as f:
        template = jinja2.Template(f.read())
    return template.render(data)

