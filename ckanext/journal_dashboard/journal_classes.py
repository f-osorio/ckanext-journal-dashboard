"""

"""
from pylons import config
import ckan.model as model
import ckan.plugins.toolkit as tk

from datetime import datetime, timedelta, date

engine = model.meta.engine


class Dataset:
    def __init__(self, engine, id, date=date.today()):
        data = self._get_dataset(id)
        self.engine = engine
        self.date = date
        self.name = data['title']
        self.resources = self._populate_resources(data)
        self.owner = data['owner_org']
        self.views = data['tracking_summary']['total']
        self.private = data['private']
        self.total_downloads = self._get_total_downloads()
        self.previous_month_views = self._get_previous_views(id, date)


    def _get_dataset(self, id):
        data = {'id': id, 'include_tracking': True}
        try:
            org = tk.get_action('package_show')(None, data)
        except:
            context = {'user': 'default'}
            org = tk.get_action('package_show')(context, data)
        return org


    def _populate_resources(self, data):
        out = []
        for resource in data['resources']:
            out.append(Resource(self.engine, resource['id'], self.date))
        out = sorted(out, key=lambda x: x.total_downloads, reverse=True)
        return out


    def _get_total_downloads(self):
        return sum([resource.total_downloads for resource in self.resources if type(resource.total_downloads) == int ])


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
            lists. The first row is for the dataset the follow for resources.
            Need to add empty spaces in the lists soo they line up.
                Dataset: published, name, empty, empty, empty
                Resources: empty, empty, name, last month, total
        """
        # TODO: finish this VVV
        out=[[self.private, self.name, self.views,'','','']]
        for resource in self.resources:
            tmp = resource.as_list()
            tmp.insert(0, '')
            tmp.insert(0, '')
            tmp.insert(0, '')
            out.append(tmp)
        return out



class Resource:
    def __init__(self, engine, id, date=date.today()):
        data = self._get_resource(id)
        self.engine = engine
        self.name = data['name']
        self.url = data['url']
        self.format = data['format']
        self.total_downloads = data['tracking_summary']['total']
        self.recent_downlaods = data['tracking_summary']['recent']
        self.previous_month_downloads = self._get_last_month_downloads(self.url, date)
        if config.get('ckan.site_url', '') not in self.url:
            self.total_downloads = -1
            self.recent_downlaods = -1
            self.previous_month_downloads = -1


    def _get_resource(self, id):
        data = {'id': id, 'include_tracking': True}
        try:
            res = tk.get_action('resource_show')(None, data)
        except Exception as e:
            context = {'user': 'default'}
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
        return "<Resource: {} {} {}>".format(self.name, self.total_downloads, self.url)
