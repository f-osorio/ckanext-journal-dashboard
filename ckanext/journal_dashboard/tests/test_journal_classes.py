"""
Unit Tests for `journal_classes`
"""
import ckan
import webtest
import datetime
import paste.fixture
import ckan.model as model
from ckan.tests import helpers
from ckan.lib.helpers import url_for
import pylons.test, pylons, pylons.config as c, ckan.model as model, ckan.tests as tests, ckan.plugins as plugins, ckan.tests.factories as factories

import ckanext.journal_dashboard.journal_classes as jc

import ckan.model as model
engine = model.meta.engine


class TestDatasetClass(helpers.FunctionalTestBase):
    def teardown(self):
        model.repo.rebuild_db()


    @classmethod
    def teardown_class(cls):
        if plugins.plugin_loaded('journal-dashboard'):
            plugins.unload('journal-dashboard')


    def _get_app(self):
        c['global_conf']['debug'] = 'true'
        app = ckan.config.middleware.make_app(c['global_conf'], **c)
        app = webtest.TestApp(app)
        if not plugins.plugin_loaded('journal-dashboard'):
            plugins.load('journal-dashboard')
        return app

    def _update_tracking_summary(self):
        '''Update CKAN's tracking summary data.
        This simulates calling `paster tracking update` on the command line.
        '''
        import ckan.lib.cli
        import ckan.model
        date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime(
            '%Y-%m-%d')
        ckan.lib.cli.Tracking('Tracking').update_all(
            engine=ckan.model.meta.engine, start_date=date)


    def _post_to_tracking(self, url, type_='page', ip='199.204.138.90',
                          browser='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'):
        '''Post some data to /_tracking directly.

        This simulates what's supposed when you view a page with tracking
        enabled (an ajax request posts to /_tracking).

        '''
        app = self._get_app()
        params = {'url': url, 'type': type_}
        extra_environ = {
            # The tracking middleware crashes if these aren't present.
            'HTTP_USER_AGENT': browser,
            'REMOTE_ADDR': ip,
            'HTTP_ACCEPT_LANGUAGE': 'en',
            'HTTP_ACCEPT_ENCODING': 'gzip, deflate',
        }

        app.post('/_tracking', params=params, extra_environ=extra_environ)


    def _create_package_resource(self, num_resources=1, resource=False, num_journals=1):
        user = factories.User(sysadmin=True)
        owner_org = factories.Organization(users=[{'name': user['id'], 'capacity': 'admin'}])

        datasets = []
        for _ in range(num_journals):
            if _ % 2 != 0:
                reviewed = 'reviewed'
                private = False
            else:
                reviewed = ''
                private = True
            datasets.append(factories.Dataset(owner_org=owner_org['id'], private=private, dara_edawax_review='reviewed'))

        resources = []
        if resource:
            for _ in range(num_resources):
                resources.append(factories.Resource(package_id=datasets[0]['id'], url='http://test.link/{}'.format(_)))
            return datasets, resources
        return datasets


    def test_1_populate_dataset_class_0_views_0_resources(self):
        dataset = self._create_package_resource()

        d = jc.Dataset(dataset[0]['id'])

        assert d.name == dataset[0]['title'], '"{}"" != "{}"'.format(d.name, dataset[0]['title'])
        assert len(d.resources) == 0, 'Should be 0 resoruces: {}'.format(len(d.resources))
        assert d.owner == dataset[0]['owner_org'], '"{}"" != "{}"'.format(d.owner, dataset[0]['owner_org'])
        assert d.views == 0, 'Should be 0 views: {}'.format(d.views)
        assert d.private == True, 'Should be private: {}'.format(d.private)


    def test_2_populate_dataset_class_1_view_0_resources(self):
        dataset = self._create_package_resource()
        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)

        url = url_for(controller='package', action='read',
                             id=package['name'])
        self._post_to_tracking(url)
        self._update_tracking_summary()

        d = jc.Dataset(dataset[0]['id'])

        assert d.name == dataset[0]['title'], '"{}"" != "{}"'.format(d.name, dataset[0]['title'])
        assert len(d.resources) == 0, 'Should be 0 resoruces: {}'.format(len(d.resources))
        assert d.owner == dataset[0]['owner_org'], '"{}"" != "{}"'.format(d.owner, dataset[0]['owner_org'])
        assert d.views == 1, 'Should be 1 views: {}'.format(d.views)
        assert d.private == True, 'Should be private: {}'.format(d.private)


    def test_3_populate_dataset_class_4_views_0_resources(self):
        dataset = self._create_package_resource()
        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)

        url = url_for(controller='package', action='read',
                             id=package['name'])
        for ip in ['44', '55', '66', '77']:
            self._post_to_tracking(url, ip='111.222.333.{}'.format(ip))
        self._update_tracking_summary()

        d = jc.Dataset(dataset[0]['id'])

        assert d.name == dataset[0]['title'], '"{}"" != "{}"'.format(d.name, dataset[0]['title'])
        assert len(d.resources) == 0, 'Should be 0 resoruces: {}'.format(len(d.resources))
        assert d.owner == dataset[0]['owner_org'], '"{}"" != "{}"'.format(d.owner, dataset[0]['owner_org'])
        assert d.views == 4, 'Should be 4 views: {}'.format(d.views)
        assert d.private == True, 'Should be private: {}'.format(d.private)


    def test_4_populate_dataset_class_1_view_1_resource(self):
        dataset, resources = self._create_package_resource(resource=True)
        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)
        url = url_for(controller='package', action='read',
                             id=package['name'])
        self._post_to_tracking(url)
        self._update_tracking_summary()

        d = jc.Dataset(dataset[0]['id'])

        assert d.name == dataset[0]['title'], '"{}"" != "{}"'.format(d.name, dataset[0]['title'])
        assert len(d.resources) == 1, 'Should be 1 resource: {}'.format(len(d.resources))
        assert d.owner == dataset[0]['owner_org'], '"{}"" != "{}"'.format(d.owner, dataset[0]['owner_org'])
        assert d.views == 1, 'Should be 1 views: {}'.format(d.views)
        assert d.private == True, 'Should be private: {}'.format(d.private)


    def test_5_populate_dataset_class_1_view_2_resource(self):
        dataset, resources = self._create_package_resource(resource=True, num_resources=2)
        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)
        url = url_for(controller='package', action='read',
                             id=package['name'])
        self._post_to_tracking(url)
        self._update_tracking_summary()

        d = jc.Dataset(dataset[0]['id'])

        assert d.name == dataset[0]['title'], '"{}" != "{}"'.format(d.name, dataset[0]['title'])
        assert len(d.resources) == 2, 'Should be 2 resource: {}'.format(len(d.resources))
        assert d.owner == dataset[0]['owner_org'], '"{}"" != "{}"'.format(d.owner, dataset[0]['owner_org'])
        assert d.views == 1, 'Should be 1 views: {}'.format(d.views)
        assert d.private == True, 'Should be private: {}'.format(d.private)


    def test_6_populate_resource_class_0_downloads(self):
        dataset, resource = self._create_package_resource(resource=True)

        r = jc.Dataset(dataset[0]['id']).resources

        assert r[0].name == resource[0][u'name'], '"{}" != "{}"'.format(r.name, resource[0][u'name'])
        assert r[0].url == resource[0][u'url'], '"{}" != "{}"'.format(r.url, resource[0][u'url'])
        assert r[0].format == resource[0][u'format'], '"{}" != "{}"'.format(r.format, resource[0][u'format'])
        assert r[0].total_downloads == 0, "Should be 0 downlaods: {}".format(r[0].total_downloads)

    def test_7_populate_resource_class_1_download(self):
        dataset, resource = self._create_package_resource(resource=True)
        url = resource[0]['url']

        self._post_to_tracking(url, type_='resource')
        self._update_tracking_summary()

        r = jc.Dataset(dataset[0]['id']).resources

        assert r[0].name == resource[0][u'name'], '"{}" != "{}"'.format(r.name, resource[0][u'name'])
        assert r[0].url == resource[0][u'url'], '"{}" != "{}"'.format(r.url, resource[0][u'url'])
        assert r[0].format == resource[0][u'format'], '"{}" != "{}"'.format(r.format, resource[0][u'format'])
        assert r[0].total_downloads == 1, "Should be 1 downlaods: {}".format(r[0].total_downloads)

    def test_8_populate_multi_resource_classes_multi_download(self):
        datasets, resources = self._create_package_resource(resource=True, num_resources=3)

        url1 = resources[0]['url']
        url2 = resources[1]['url']
        url3 = resources[2]['url']

        for ip in ['44', '55', '77', '88']:
            self._post_to_tracking(url1, ip='111.222.333.{}'.format(ip), type_='resource')
            self._post_to_tracking(url2, ip='111.222.333.{}'.format(ip), type_='resource')
        self._post_to_tracking(url3, type_='resource')
        self._update_tracking_summary()

        d = jc.Dataset(datasets[0]['id'])
        r = d.resources

        assert d.total_downloads == 9, 'Should be 9 downloads: {}'.format(d.total_downloads)
        assert r[0].total_downloads == 4, 'Should be 4: {}'.format(r[0].total_downlaods)
        assert r[1].total_downloads == 4, 'Should be 4: {}'.format(r[1].total_downlaods)
        assert r[2].total_downloads == 1, 'Should be : {}'.format(r[2].total_downlaods)


    def test_9_populate_dataset_class_4_views_previous(self):
        dataset = self._create_package_resource()
        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)

        url = url_for(controller='package', action='read',
                             id=package['name'])
        for ip in ['44', '55', '66', '77']:
            self._post_to_tracking(url, ip='111.222.333.{}'.format(ip))
        self._update_tracking_summary()

        target_date = datetime.date.today() + datetime.timedelta(days=30)
        d = jc.Dataset(dataset[0]['id'], target_date)
        assert d.previous_month_views == 4, "Previous views should be 4: {}".format(d.previous_month_views)

        target_date = datetime.date.today() + datetime.timedelta(days=60)
        d = jc.Dataset(dataset[0]['id'], target_date)
        assert d.previous_month_views == 0, "Previous views should be 0: {}".format(d.previous_month_views)


    def test_10_populate_dataset_class_4_downloads_previous(self):
        dataset, resources = self._create_package_resource(resource=True, num_resources=2)

        url1 = resources[0]['url']
        url2 = resources[1]['url']

        for ip in ['44', '55']:
            self._post_to_tracking(url1, ip='111.222.333.{}'.format(ip), type_='resource')
            self._post_to_tracking(url2, ip='111.222.333.{}'.format(ip), type_='resource')
        self._update_tracking_summary()

        target_date = datetime.date.today() + datetime.timedelta(days=30)
        d = jc.Dataset(dataset[0]['id'], target_date)
        r = d.resources
        assert r[0].previous_month_downloads == 2, "Previous dls should be 2: {}".format(r[0].previous_month_downloads)
        assert r[1].previous_month_downloads == 2, "Previous dls should be 2: {}".format(r[1].previous_month_downloads)

        target_date = datetime.date.today() + datetime.timedelta(days=60)
        d = jc.Dataset(dataset[0]['id'], target_date)
        r = d.resources
        assert r[0].previous_month_downloads == 0, "Previous dls should be 0: {}".format(r[0].previous_month_downloads)




