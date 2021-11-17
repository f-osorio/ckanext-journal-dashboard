from datetime import timedelta, date, datetime
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.common import config

import time

"""
# packages
# date: %(time)s::date
select p.name, p.title, ts.count, ts.running_total, ts.tracking_date
from "group" as g
join package as p
    on p.owner_org = g.id
join tracking_summary as ts
    on ts.url LIKE '%/dataset/' || p.name
where g.id = 'ffd970f3-110e-4247-91a4-21e4dc01b6d6'
    and ts.tracking_date >= '2021-10-17'
ORDER BY p.name, ts.tracking_date DESC;
"""

"""
# resources
select r.name, ts.running_total, ts.tracking_date
from "group" as g
join package as p
    on p.owner_org = g.id
join resource as r
    on r.package_id = p.id
join tracking_summary as ts
    on ts.url LIKE '%resource/' || r.id ||'/download/' || r.name
where g.id = 'ffd970f3-110e-4247-91a4-21e4dc01b6d6'
ORDER BY p.name, r.name, ts.tracking_date;
"""

class Organization:
    def __init__(self, id, source, date=date.today()):
        self.engine = model.meta.engine
        self.data = self._get_org(id)
        self.name = self.data['name']
        self.title = self.data['title']
        self.display_name = self.data['title']
        self.id = self.data['id']
        self.image_display_url = self.data['image_display_url']
        self.description = self.data['description']
        resources, count = self._get_resources()
        self.resources = resources
        self.resource_count = count
        self.packages = [Dataset(name, data) for name, data in  self._get_packages().items()]
        self.package_count = len(self.packages)
        self.total_views = sum([p.total_views for p in self.packages])
        self.total_downloads = sum(p.total_downloads for p in self.packages)


    def _get_org(self, id):
        print('_get_org')
        data = {'id': id, 'include_datasets': True}
        try:
            org = tk.get_action('organization_show')(None, data)
        except Exception:
            context = {'user': 'default', 'ignore_auth': True}
            org = tk.get_action('organization_show')(context, data)
        return org


    def _get_packages(self):
        packages = {}
        target_date = date.today() - timedelta(days=30)
        sql = """
            select p.name, p.title, p.url, p.id, p.state, p.private, p.owner_org,
                CASE when ts.count is NULL then 0 else ts.count END as count,
                CASE when ts.running_total is NULL then 0 else ts.running_total END as running_total,
                CASE when ts.tracking_date is NULL then '1900-01-01'::date else ts.tracking_date END as tracking_date
            from "group" as g
            join package as p
                on p.owner_org = g.id
            left join tracking_summary as ts
                on ts.url ILIKE '%%/dataset/' || p.name
            where g.id = %(id)s and p.state = 'active'
            ORDER BY p.name, ts.tracking_date DESC;
        """
        results = self.engine.execute(sql, id=self.id).fetchall()
        for package in results:
            name = package[0]
            if name in packages.keys():
                if packages[name]['total'] < package[8]:
                    packages[name]['total'] = package[8]
                if package[9] >= target_date:
                    packages[name]['recent'] += package[7]
            else:
                packages[name] = {'title': package[1],
                                  'url': package[2],
                                  'id': package[3],
                                  'state': package[4],
                                  'private': package[5],
                                  'owner': package[6],
                                  'total': package[8],
                                  'recent': 0 if package[9] < target_date else package[7],
                                  'resources': self.resources[name] if name in self.resources.keys() else None
                                    }

        return packages


    def _get_resources(self):
        resources = {}
        target_date = date.today() - timedelta(days=30)
        sql = """
            select p.name, r.name, r.url,
                CASE when ts.running_total is NULL then 0 else ts.running_total END as running_total,
                CASE when ts.count is NULL then 0 else ts.count END as count,
                CASE when ts.tracking_date is NULL then '1900-01-01'::date else ts.tracking_date END as tracking_date,
                r.id, r.format
            from "group" as g
            join package as p
                on p.owner_org = g.id
            join resource as r
                on r.package_id = p.id
            left join tracking_summary as ts
                on ts.url ILIKE '%%resource/' || r.id ||'/download/' || r.url
            where g.id = %(id)s and p.state = 'active' and r.state != 'deleted'
            ORDER BY p.name, r.name, ts.tracking_date;
        """
        results = self.engine.execute(sql, id=self.id).fetchall()
        count = 0
        for resource in results:
            name = resource[0]
            res_name = resource[1] if resource[1] != '' else resource[2]
            res_id = resource[6]
            if name in resources.keys():
                if res_id not in resources[name].keys():
                    count += 1
                    resources[name][res_id] = {
                        'name': res_name,
                        'id': resource[6],
                        'format': resource[7],
                        'url': resource[2],
                        'total': resource[3],
                        'recent': 0 if resource[5] < target_date else resource[4],
                    }
                else:
                    if resources[name][res_id]['total'] < resource[3]:
                        resources[name][res_id]['total'] = resource[3]
                    if resource[5] >= target_date:
                        resources[name][res_id]['recent'] += resource[4]
            else:
                count += 1
                resources[name] = {res_id: {
                        'name': res_name,
                        'id': resource[6],
                        'format': resource[7],
                        'url': resource[2],
                        'total': resource[3],
                        'recent': 0 if resource[5] < target_date else resource[4],
                }}

        return resources, count


    def __repr__(self):
        return f"<Journal: {self.name} {self.package_count} packages>"


class Dataset:
    def __init__(self, name, data):
        self.name = name
        self.title  = data['title']
        self.url = data['url']
        self.id = data['id']
        self.state = data['state']
        self.private = data['private']
        self.owner = data['owner']
        self.total_views = data['total']
        self.recent_views = data['recent']
        if data['resources'] is not None:
            self.resources = [Resource(id, d) for id, d in  data['resources'].items()]
            self.total_downloads = sum([resource.total_downloads for resource in self.resources if type(resource.total_downloads) == int])
        else:
            self.resources = None
            self.total_downloads = 0

    def __repr__(self):
        return f"<Dataset: {self.name}>"


class Resource:
    def __init__(self, id, data):
        self.data = data
        self.id = data['id']
        self.url = data['url']
        self.name = data['name']
        self.format = data['format']
        self.total_downloads = data['total']
        self.recent_downloads = data['recent']


    def __repr__(self):
        return f"<Resource: {self.name} {self.url} -- total: {self.total_downloads}, recent: {self.recent_downloads}>"


"""
The following classes took too long to populate if there are a lot of resources
"""
class _Organization:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, id, source, date=date.today()):
        print('ORG')
        self.data = self._get_org(id)
        self.name = self.data['name']
        self.title = self.data['title']
        self.display_name = self.data['title']
        self.id = self.data['id']
        self.image_display_url = self.data['image_display_url']
        self.description = self.data['description']
        self.packages = self._get_packages(source)
        self.package_count = len(self.packages)
        self.resource_count = sum([len(p.resources) for p in self.packages])
        self.total_views = sum([p.views for p in self.packages])
        self.total_downloads = sum(p.total_downloads for p in self.packages)


    def _get_org(self, id):
        data = {'id': id, 'include_datasets': True}
        try:
            org = tk.get_action('organization_show')(None, data)
        except Exception:
            context = {'user': 'default', 'ignore_auth': True}
            org = tk.get_action('organization_show')(context, data)
        return org


    def _get_packages(self, source):
        out = []
        org_id = self.id
        d1 = {'facet': 'false',
            'fq': f'+owner_org:"{org_id}"',
            'rows': 1000,
            'sort': 'metadata_created desc',
            'include_private': True}
        results = tk.get_action('package_search')({'ignore_auth': True}, d1)

        for result in results['results']:
            out.append(Dataset(result['id'], source))
        return out


    def __repr__(self):
        return f"<Organization: {self.name}, Packages: {self.package_count}>"


class _Dataset:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, id, source, date=date.today()):
        start = time.time()
        data = self._get_dataset(id)
        self.engine = model.meta.engine
        self.date = date
        self.id = id
        self.state = getattr(data, 'dara_edawax_review', False)
        self.name = data['name']
        self.title = data['title']
        self.resources = self._populate_resources(data, source)
        self.owner = data['owner_org']
        self.views = data['tracking_summary']['total']
        self.views_recent = data['tracking_summary']['recent']
        self.private = data['private']
        self.total_downloads = self._get_total_downloads()
        self.previous_month_views = self._get_previous_views(id, date)
        end = time.time()
        print(f"\tDuration: {end-start}")

    def _get_dataset(self, id):
        data = {'id': id, 'include_tracking': True}
        try:
            dataset = tk.get_action('package_show')(None, data)
        except Exception:
            context = {'user': 'default', 'ignore_auth': True}
            dataset = tk.get_action('package_show')(context, data)
        return dataset

    def _populate_resources(self, data, source):
        out = []
        if source == 'cmd' or len(data['resources']) < 11:
            for resource in data['resources']:
                out.append(Resource(self.engine, resource['id'], self.date))
            out = sorted(out, key=lambda x: x.total_downloads, reverse=True)
        return out


    def _get_total_downloads(self):
        return sum([resource.total_downloads for resource in self.resources if type(resource.total_downloads) == int ])

    def _get_previous_downloads(self):
        return sum([resource.previous_month_downloads for resource in self.resources if type(resource.previous_month_downloads) == int ])


    def _get_previous_views(self, id, today):
        target_period = today - timedelta(days=30)
        sql = """
                SELECT sum(count)
                FROM tracking_summary
                WHERE tracking_date >= %(time)s::date
                    AND package_id = %(id)s;
              """
        results = self.engine.execute(sql,id=id, time=target_period).fetchall()
        return results[0][0] or 0


    def as_list(self):
        """
            Combine the dataset and resource information into a list of
            lists. The first row is for the dataset, the following for resources.
            Need to add empty spaces in the lists soo they line up.
                Dataset: published, name, empty, empty, empty
                Resources: empty, empty, name, last month, total
        """
        # TODO: finish this VVV
        out=[[self.private, self.name, self.views, len(self.resources),'','']]
        if self.private:
            return out

        for resource in self.resources:
            tmp = resource.as_list()
            tmp.insert(0, '')
            tmp.insert(0, '')
            tmp.insert(0, '')
            out.append(tmp)
        return out


class _Resource:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, engine, id, date=date.today()):
        data = self._get_resource(id)
        self.id = id
        self.engine = engine
        self.url = data['url']
        self.name = self.get_name(data['name'])
        self.format = data['format']
        self.total_downloads = data['tracking_summary']['total']
        self.recent_downloads = data['tracking_summary']['recent']
        self.previous_month_downloads = self._get_last_month_downloads(self.url, date)
        if config.get('ckan.site_url', '') not in self.url:
            self.total_downloads = 0
            self.recent_downloads = 0
            self.previous_month_downloads = 0


    def get_name(self, name):
        try:
            if name == '':
                parts = self.url.split('/')
                name = parts[-1]
        except Exception:
            pass
        return name


    def _get_resource(self, id):
        data = {'id': id, 'include_tracking': True}
        try:
            res = tk.get_action('resource_show')(None, data)
        except Exception as e:
            context = {'user': 'default', 'ignore_auth': True}
            res = tk.get_action('resource_show')(context, data)
        return res


    def _get_last_month_downloads(self, url, today):
        target_period = today - timedelta(days=30)
        sql = """
                SELECT sum(count)
                FROM tracking_summary
                WHERE tracking_date >= %(time)s::date
                    AND url = %(url)s;
              """
        results = self.engine.execute(sql, url=url, time=target_period).fetchall()
        return results[0][0] or 0


    def as_list(self):
        return [self.name, self.url, self.format, self.previous_month_downloads, self.total_downloads]


    def __repr__(self):
        return f"<Resource: {self.name} {self.total_downloads} {self.url}>"
