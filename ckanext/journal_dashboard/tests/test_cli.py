import ckan
import paste
import webtest
import datetime
import paste.fixture
from ckan.tests import helpers
from ckan.lib.helpers import url_for
import pylons.test, pylons, pylons.config as c, ckan.model as model, ckan.tests as tests, ckan.plugins as plugins, ckan.tests.factories as factories

import ckanext.journal_dashboard.helpers as h
import ckanext.journal_dashboard.command as command


class TestCli(helpers.FunctionalTestBase):
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
        user = factories.User()
        owner_org = factories.Organization(users=[{'name': user['id'], 'capacity': 'admin'}])

        datasets = []
        for _ in range(num_journals):
            datasets.append(factories.Dataset(owner_org=owner_org['id']))

        resources = []
        if resource:
            for _ in range(num_resources):
                resources.append(factories.Resource(package_id=datasets[0]['id'], url='http://test.link/{}'.format(_)))
            return datasets, resources
        return datasets


    def test_1_access_dataset_0_views(self):
        dataset = self._create_package_resource()

        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)
        tracking_summary = package['tracking_summary']

        assert tracking_summary['total'] == 0, 'Total should be 0, {}'.format(tracking_summary['total'])
        assert tracking_summary['recent'] == 0, 'Recent should be 0, {}'.format(tracking_summary['recent'])


    def test_2_access_dataset_1_view(self):
        dataset = self._create_package_resource()

        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)

        url = url_for(controller='package', action='read',
                             id=package['name'])
        self._post_to_tracking(url)
        self._update_tracking_summary()

        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)

        tracking_summary = package['tracking_summary']

        assert tracking_summary['total'] == 1, 'Total should be 1, {}'.format(tracking_summary['total'])
        assert tracking_summary['recent'] == 1, 'Recent should be 1, {}'.format(tracking_summary['recent'])


    def test_3_access_2_datasets_3_views(self):
        dataset1 = self._create_package_resource()
        dataset2 = self._create_package_resource()

        package1 = helpers.call_action('package_show', id=dataset1[0]['id'], include_tracking=True)
        package2 = helpers.call_action('package_show', id=dataset2[0]['id'], include_tracking=True)

        url1 = url_for(controller='package', action='read',
                             id=package1['name'])
        url2 = url_for(controller='package', action='read',
                             id=package2['name'])

        for ip in ['44', '55']:
            self._post_to_tracking(url1, ip='111.222.333.{}'.format(ip))
        self._post_to_tracking(url2)

        self._update_tracking_summary()

        package1 = helpers.call_action('package_show', id=dataset1[0]['id'], include_tracking=True)
        tracking_summary1 = package1['tracking_summary']

        package2 = helpers.call_action('package_show', id=dataset2[0]['id'], include_tracking=True)
        tracking_summary2 = package2['tracking_summary']

        assert tracking_summary1['total'] == 2, 'Total should be 2, {}'.format(tracking_summary['total'])
        assert tracking_summary1['recent'] == 2, 'Recent should be 2, {}'.format(tracking_summary['recent'])

        assert tracking_summary2['total'] == 1, 'Total should be 1, {}'.format(tracking_summary['total'])
        assert tracking_summary2['recent'] == 1, 'Recent should be 1, {}'.format(tracking_summary['recent'])


    def test_4_resource_download_1_real(self):
        """ Download from 1 user """
        dataset, resources = self._create_package_resource(resource=True)
        url = resources[0]['url']

        self._post_to_tracking(url, type_='resource')
        self._update_tracking_summary()

        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)

        resource = package['resources'][0]

        tracking_summary = resource['tracking_summary']

        assert tracking_summary['total'] == 1, 'Total should be 1, {}'.format(tracking_summary['total'])
        assert tracking_summary['recent'] == 1, 'Recent should be 1, {}'.format(tracking_summary['recent'])


    def test_5_resourcs_download_1_real(self):
        """ Download from 1 user """
        dataset1, resources1 = self._create_package_resource(resource=True)
        url1 = resources1[0]['url']

        dataset2, resources2 = self._create_package_resource(resource=True)
        url2 = resources2[0]['url']

        dataset3, resources3 = self._create_package_resource(resource=True)
        url3 = resources3[0]['url']

        self._post_to_tracking(url1, type_='resource')
        self._post_to_tracking(url2, type_='resource')
        self._post_to_tracking(url3, type_='resource')
        self._update_tracking_summary()

        package1 = helpers.call_action('package_show', id=dataset1[0]['id'], include_tracking=True)
        package2 = helpers.call_action('package_show', id=dataset2[0]['id'], include_tracking=True)
        package3 = helpers.call_action('package_show', id=dataset3[0]['id'], include_tracking=True)

        resource1 = package1['resources'][0]
        resource2 = package2['resources'][0]
        resource3 = package3['resources'][0]

        tracking_summary1 = resource1['tracking_summary']
        tracking_summary2 = resource2['tracking_summary']
        tracking_summary3 = resource3['tracking_summary']

        assert tracking_summary1['total'] == 1, 'Total should be 1, {}'.format(tracking_summary1['total'])
        assert tracking_summary1['recent'] == 1, 'Recent should be 1, {}'.format(tracking_summary1['recent'])

        assert tracking_summary2['total'] == 1, 'Total should be 1, {}'.format(tracking_summary2['total'])
        assert tracking_summary2['recent'] == 1, 'Recent should be 1, {}'.format(tracking_summary2['recent'])

        assert tracking_summary3['total'] == 1, 'Total should be 1, {}'.format(tracking_summary3['total'])
        assert tracking_summary3['recent'] == 1, 'Recent should be 1, {}'.format(tracking_summary3['recent'])


    def test_6_create_multiple_datasets(self):
        dataset, resources = self._create_package_resource(num_resources=3, resource=True)

        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)

        resources = package['resources']

        assert len(resources) == 3, "There should be 3 resources: {}".format(len(resources))


    def test_7_download_mulitple_resources_one_dataset(self):
        dataset, resources = self._create_package_resource(num_resources=3, resource=True)
        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)

        url0 = url_for(controller='package', action='read',
                             id=package['name'])

        url1 = resources[0]['url']
        url2 = resources[1]['url']
        url3 = resources[2]['url']

        for ip in ['44', '55']:
            self._post_to_tracking(url0, ip='111.222.333.{}'.format(ip))
            self._post_to_tracking(url1, ip='111.222.333.{}'.format(ip), type_='resource')
        self._post_to_tracking(url2, type_='resource')
        self._update_tracking_summary()

        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)

        resource1 = package['resources'][0]
        resource2 = package['resources'][1]
        resource3 = package['resources'][2]

        tracking_summary = package['tracking_summary']
        resource_summary1 = resource1['tracking_summary']
        resource_summary2 = resource2['tracking_summary']
        resource_summary3 = resource3['tracking_summary']

        assert tracking_summary['total'] == 2, 'Total should be 2, {}'.format(tracking_summary['total'])
        assert resource_summary1['total'] == 2, 'Total should be 2, {}'.format(resource_summary1['total'])
        assert resource_summary2['total'] == 1, 'Total should be 1, {}'.format(resource_summary2['total'])
        assert resource_summary3['total'] == 0, 'Total should be 0, {}'.format(resource_summary3['total'])


    def test_8_total_downloads_journal(self):
        dataset, resources = self._create_package_resource(num_resources=3, resource=True)
        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)

        url0 = url_for(controller='package', action='read',
                             id=package['name'])

        url1 = resources[0]['url']
        url2 = resources[1]['url']
        url3 = resources[2]['url']

        for ip in ['44', '55']:
            self._post_to_tracking(url1, ip='111.222.333.{}'.format(ip))
            self._post_to_tracking(url1, ip='111.222.333'.format(ip), type_='resource')
        self._post_to_tracking(url2, type_='resource')
        self._update_tracking_summary()

        downloads = h.total_downloads_journal(package['owner_org'])

        assert downloads == 4, "Should be 4 downloads: {}".format(downloads)


    def test_9_total_views_journal(self):
        dataset = self._create_package_resource(num_journals=5, resource=False)

        package1 = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)
        package2 = helpers.call_action('package_show', id=dataset[1]['id'], include_tracking=True)
        package3 = helpers.call_action('package_show', id=dataset[2]['id'], include_tracking=True)
        package4 = helpers.call_action('package_show', id=dataset[3]['id'], include_tracking=True)
        package5 = helpers.call_action('package_show', id=dataset[4]['id'], include_tracking=True)

        url1 = url_for(controller='package',action='read',id=package1['name'])
        url2 = url_for(controller='package',action='read',id=package2['name'])
        url3 = url_for(controller='package',action='read',id=package3['name'])
        url4 = url_for(controller='package',action='read',id=package4['name'])
        url5 = url_for(controller='package',action='read',id=package5['name'])

        for ip in ['44', '55', '66', '77']:
            self._post_to_tracking(url1, ip='111.222.333.{}'.format(ip))
            self._post_to_tracking(url5, ip='111.222.333.{}'.format(ip))

        for ip in ['44', '55']:
            self._post_to_tracking(url3, ip='111.222.333.{}'.format(ip))
            self._post_to_tracking(url4, ip='111.222.333.{}'.format(ip))

        self._post_to_tracking(url2, ip='111.222.333.{}'.format(ip))

        self._update_tracking_summary()

        views = h.total_views_across_journal_datasets(package1['owner_org'])

        assert views == 13, "Should be 13 views: {}".format(views)


    def test_10_count_datasets_in_journal(self):
        dataset = self._create_package_resource(num_journals=13, resource=False)
        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)

        org = h.get_org(package['owner_org'])

        assert org['package_count'] == 13, "Should be 13 datasets: {}".format(org)


    def test_11_get_resource_downloads(self):
        assert False, "This is False"
