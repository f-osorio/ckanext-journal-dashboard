import ckan.model as model
from urlparse import urlparse
from ckan.common import request
import ckan.plugins.toolkit as tk

engine = model.meta.engine


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
    org = tk.get_action('organization_show')(None, data)
    return org


def package_tracking(id):
    tracking_summary = tk.get_action('package_show')(None, {'id': id, 'include_tracking': True})['tracking_summary']
    return tracking_summary


def get_resources(id):
    resources = tk.get_action('package_show')(None, {'id': id})['resources']
    return resources


def resource_details(id):
    resource = tk.get_action('resource_show')(None, {'id': id, 'include_tracking': True})
    return resource


def journal_resource_downloads(journal_id):
    return_dict = {}
    sql = """
        SELECT r.id, r.url, ts.running_total, ts.recent_views, ts.tracking_date, ts.url
        FROM package as p
        JOIN resource as r
            ON r.package_id = p.id
        JOIN tracking_summary as ts
            ON ts.url = r.url
        WHERE p.owner_org = %(id)s;
        """
    results = engine.execute(sql, id=journal_id).fetchall()
    for result in results:
        return_dict[result[1]] = [result[2], result[3]]
    return return_dict


def match_resource_downloads(url, stats):
    for k,v in stats.items():
        if url in k:
            return v


def is_published_(name):
    try:
        pck = tk.get_action('package_show')(None, {'id': name})
        if is_private(pck) or in_review(pck) != 'reviewed':
            return False
        return True
    except Exception as e:
        return False


def in_review(pkg):
    if not isinstance(pkg, dict):
        return False
    return pkg.get('dara_edawax_review', False)


def is_private(pkg):
    if not isinstance(pkg, dict):
        return True
    return pkg.get('private', True)


def total_views_across_journal_datasets(journal_id):
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

    results = engine.execute(sql, id=journal_id).fetchall()
    return results[0][1]


def total_downloads_journal(journal_id):
    data = journal_resource_downloads(journal_id)
    total = 0
    for k,v in data.items():
        total += v[0]
    return total
