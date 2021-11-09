from datetime import timedelta, date
import ckan.model as model
import ckan.plugins.toolkit as tk
from ckan.common import config


class Organization:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, id, date=date.today()):
        self.data = self._get_org(id)
        self.name = self.data['name']
        self.title = self.data['title']
        self.display_name = self.data['title']
        self.id = self.data['id']
        self.image_display_url = self.data['image_display_url']
        self.description = self.data['description']
        self.packages = self._get_packages()
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


    def _get_packages(self):
        out = []
        org_id = self.id
        d1 = {'facet': 'false',
            'fq': f'+owner_org:"{org_id}"',
            'rows': 1000,
            'sort': 'metadata_created desc',
            'include_private': True}
        results = tk.get_action('package_search')({'ignore_auth': True}, d1)

        for result in results['results']:
            out.append(Dataset(result['id']))
        return out


    def __repr__(self):
        return f"<Organization: {self.name}, Packages: {self.package_count}>"


class Dataset:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, id, date=date.today()):
        data = self._get_dataset(id)
        self.engine = model.meta.engine
        self.date = date
        self.id = id
        self.state = getattr(data, 'dara_edawax_review', False)
        self.name = data['name']
        self.title = data['title']
        self.resources = self._populate_resources(data)
        self.owner = data['owner_org']
        self.views = data['tracking_summary']['total']
        self.views_recent = data['tracking_summary']['recent']
        self.private = data['private']
        self.total_downloads = self._get_total_downloads()
        self.previous_month_views = self._get_previous_views(id, date)


    def _get_dataset(self, id):
        data = {'id': id, 'include_tracking': True}
        try:
            dataset = tk.get_action('package_show')(None, data)
        except Exception:
            context = {'user': 'default', 'ignore_auth': True}
            dataset = tk.get_action('package_show')(context, data)
        return dataset

    def _populate_resources(self, data):
        out = []
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



class Resource:
    # pylint: disable=too-many-instance-attributes
    def __init__(self, engine, id, date=date.today()):
        data = self._get_resource(id)
        self.id = id
        self.engine = engine
        self.name = data['name']
        self.url = data['url']
        self.format = data['format']
        self.total_downloads = data['tracking_summary']['total']
        self.recent_downloads = data['tracking_summary']['recent']
        self.previous_month_downloads = self._get_last_month_downloads(self.url, date)
        if config.get('ckan.site_url', '') not in self.url:
            self.total_downloads = 0
            self.recent_downloads = 0
            self.previous_month_downloads = 0


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
