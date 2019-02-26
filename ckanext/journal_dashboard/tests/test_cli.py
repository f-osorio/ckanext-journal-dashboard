import ckan
import paste
import webtest
import datetime
import paste.fixture
import ckan.model as model
from ckan.tests import helpers
from ckan.lib.helpers import url_for
import pylons.test, pylons, pylons.config as c, ckan.model as model, ckan.tests as tests, ckan.plugins as plugins, ckan.tests.factories as factories

import ckanext.journal_dashboard.helpers as h
import ckanext.journal_dashboard.command as command

import ckan.model as model
engine = model.meta.engine

"""
TODO:
    * Add template to an email and send the email to someone.
"""

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
        user = factories.User(sysadmin=True)
        owner_org = factories.Organization(users=[{'name': user['id'], 'capacity': 'admin'}])

        datasets = []
        for _ in range(num_journals):
            if _ % 2 == 0:
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


    def _test_1_access_dataset_0_views(self):
        dataset = self._create_package_resource()

        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)
        tracking_summary = package['tracking_summary']

        assert tracking_summary['total'] == 0, 'Total should be 0, {}'.format(tracking_summary['total'])
        assert tracking_summary['recent'] == 0, 'Recent should be 0, {}'.format(tracking_summary['recent'])


    def _test_2_access_dataset_1_view(self):
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


    def _test_3_access_2_datasets_3_views(self):
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


    def _test_4_resource_download_1_real(self):
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


    def _test_5_resourcs_download_1_real(self):
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


    def _test_6_create_multiple_datasets(self):
        dataset, resources = self._create_package_resource(num_resources=3, resource=True)

        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)

        resources = package['resources']

        assert len(resources) == 3, "There should be 3 resources: {}".format(len(resources))


    def _test_7_download_mulitple_resources_one_dataset(self):
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


    def _test_8_total_downloads_journal(self):
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

        downloads = h.total_downloads_journal(package['owner_org'])

        assert downloads == 3, "Should be 3 downloads: {}".format(downloads)


    def _test_9_total_views_journal(self):
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


    def _test_10_count_datasets_in_journal(self):
        dataset = self._create_package_resource(num_journals=13,resource=False)
        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)

        org = h.get_org(package['owner_org'])

        assert org['package_count'] == 13, "Should be 13 datasets: {}".format(org)


    def _test_11_get_resource_downloads(self):
        dataset, resources = self._create_package_resource(num_resources=8, resource=True)
        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)

        url0 = url_for(controller='package', action='read',
                             id=package['name'])

        url1 = resources[0]['url']
        url2 = resources[1]['url']
        url3 = resources[2]['url']
        url4 = resources[3]['url']
        url5 = resources[4]['url']
        url6 = resources[5]['url']
        url7 = resources[6]['url']
        url8 = resources[7]['url']

        for ip in ['44', '55']:
            self._post_to_tracking(url0, ip='111.222.333.{}'.format(ip))
            self._post_to_tracking(url1, ip='111.222.333.{}'.format(ip), type_='resource')
        for ip in ['44', '55', '66', '77', '88']:
            self._post_to_tracking(url3, ip='111.222.333.{}'.format(ip), type_='resource')
            self._post_to_tracking(url4, ip='111.222.333.{}'.format(ip), type_='resource')
            self._post_to_tracking(url5, ip='111.222.333.{}'.format(ip), type_='resource')
        self._post_to_tracking(url2, type_='resource')
        self._post_to_tracking(url6, type_='resource')
        self._post_to_tracking(url7, type_='resource')
        self._update_tracking_summary()

        package = helpers.call_action('package_show', id=dataset[0]['id'], include_tracking=True)

        summary = h.journal_download_summary(package['owner_org'], package['id'])

        assert len(summary) == 8, 'Should be 8 resources: {}'.format(len(summary))
        assert sum([int(v['total']) for k, v in summary.items()]) == 20, 'Should be 20 total downloads: {}'.format(SUM([int(v['total']) for k, v in summary.items()]))


    def _test_12_create_email(self):
        dataset, resources = self._create_package_resource(num_resources=8, resource=True, num_journals=15)

        data = {
                    'journal': 'Test Journal Title',
                    'datasets': '15',
                    'total_views': '57',
                    'total_downloads': '20',
                    'organization': h.get_org(dataset[0]['owner_org']),
                }

        email = h.create_email(data)
        assert 'Access Summary for Test Journal Title' in email, 'Didn\'t find title in email body'

    def _test_13_create_email_template_full(self):
        count = 0
        dataset = self._create_package_resource(resource=False, num_journals=5)
        org = h.get_org(dataset[0]['owner_org'])
        packages = org['packages']

        # package 1 resources
        factories.Resource(package_id=packages[0]['id'], url='http://package1/1')
        factories.Resource(package_id=packages[0]['id'], url='http://package1/2')
        factories.Resource(package_id=packages[0]['id'], url='http://package1/3')
        factories.Resource(package_id=packages[0]['id'], url='http://package1/4')
        factories.Resource(package_id=packages[0]['id'], url='http://package1/5')
        factories.Resource(package_id=packages[0]['id'], url='http://package1/5', format='')

        # package 2 resources
        factories.Resource(package_id=packages[1]['id'], url='http://package2/1')
        factories.Resource(package_id=packages[1]['id'], url='http://package2/2')
        factories.Resource(package_id=packages[1]['id'], url='http://package2/3')

        # package 3 resources
        factories.Resource(package_id=packages[2]['id'], url='http://package3/1')

        # package 4 resources
        factories.Resource(package_id=packages[3]['id'], url='http://package4/1')
        factories.Resource(package_id=packages[3]['id'], url='http://package4/2')

        # package 5 resources
        factories.Resource(package_id=packages[4]['id'], url='http://package5/1')
        factories.Resource(package_id=packages[4]['id'], url='http://package5/2')
        factories.Resource(package_id=packages[4]['id'], url='http://package5/3')

        package1 = helpers.call_action('package_show', id=packages[0]['id'], include_tracking=True)
        package2 = helpers.call_action('package_show', id=packages[1]['id'], include_tracking=True)
        package3 = helpers.call_action('package_show', id=packages[2]['id'], include_tracking=True)
        package4 = helpers.call_action('package_show', id=packages[3]['id'], include_tracking=True)
        package5 = helpers.call_action('package_show', id=packages[4]['id'], include_tracking=True)

        # package/dataset views
        url1 = url_for(controller='package', action='read',
                             id=package1['name'])
        url2 = url_for(controller='package', action='read',
                             id=package2['name'])
        url3 = url_for(controller='package', action='read',
                             id=package3['name'])
        url4 = url_for(controller='package', action='read',
                             id=package4['name'])
        url5 = url_for(controller='package', action='read',
                             id=package5['name'])

        for ip in ['44', '55', '66', '77', '88', '99']:
            self._post_to_tracking(url1, ip='111.222.333.{}'.format(ip))
            self._post_to_tracking(url2, ip='111.222.333.{}'.format(ip))
            self._post_to_tracking(url3, ip='111.222.333.{}'.format(ip))

        self._post_to_tracking(url4, ip='111.222.333.{}'.format(66))
        self._post_to_tracking(url4, ip='111.222.333.{}'.format(77))
        self._post_to_tracking(url4, ip='111.222.333.{}'.format(89))

        self._post_to_tracking(url5, ip='111.222.333.{}'.format(99))


        # access package1
        resources = helpers.call_action('package_show', id=package1['id'], include_tracking=True)['resources']
        url1 = resources[0]['url']
        url2 = resources[1]['url']
        url3 = resources[2]['url']
        url4 = resources[3]['url']
        url5 = resources[4]['url']

        for ip in ['44', '55', '66', '77', '88']:
            self._post_to_tracking(url1, ip='111.222.333.{}'.format(ip), type_='resource')
            self._post_to_tracking(url2, ip='111.222.333.{}'.format(ip), type_='resource')
            self._post_to_tracking(url3, ip='111.222.333.{}'.format(ip), type_='resource')
        self._post_to_tracking(url4, ip='111.222.333.{}'.format(99), type_='resource')
        self._post_to_tracking(url5, ip='111.222.333.{}'.format(98), type_='resource')

        # package2
        resources = resources = helpers.call_action('package_show', id=package2['id'], include_tracking=True)['resources']
        url1 = resources[0]['url']
        url2 = resources[1]['url']
        url3 = resources[2]['url']

        for ip in ['44', '55', '66']:
            self._post_to_tracking(url1, ip='111.222.333.{}'.format(ip), type_='resource')
            self._post_to_tracking(url2, ip='111.222.333.{}'.format(ip), type_='resource')
            self._post_to_tracking(url3, ip='111.222.333.{}'.format(ip), type_='resource')

        # package3
        resources = helpers.call_action('package_show', id=package3['id'], include_tracking=True)['resources']
        url1 = resources[0]['url']
        self._post_to_tracking(url1, ip='111.222.333.{}'.format(99), type_='resource')

        # package 4
        resources = helpers.call_action('package_show', id=package4['id'], include_tracking=True)['resources']
        url1 = resources[0]['url']
        url2 = resources[1]['url']
        self._post_to_tracking(url1, ip='111.222.333.{}'.format(99), type_='resource')
        self._post_to_tracking(url1, ip='111.222.333.{}'.format(55), type_='resource')
        self._post_to_tracking(url2, ip='111.222.333.{}'.format(99), type_='resource')

        # package 5
        resources = helpers.call_action('package_show', id=package5['id'], include_tracking=True)['resources']
        url1 = resources[0]['url']
        url2 = resources[1]['url']
        url3 = resources[2]['url']

        for ip in ['44', '55', '66']:
            self._post_to_tracking(url1, ip='111.222.333.{}'.format(ip), type_='resource')
            self._post_to_tracking(url2, ip='111.222.333.{}'.format(ip), type_='resource')
            self._post_to_tracking(url3, ip='111.222.333.{}'.format(ip), type_='resource')
        self._post_to_tracking(url2, ip='111.222.333.{}'.format(88), type_='resource')
        self._post_to_tracking(url2, ip='111.222.333.{}'.format(99), type_='resource')

        self._update_tracking_summary()

        views = h.total_views_across_journal_datasets(package1['owner_org'])
        downloads = h.total_downloads_journal(package1['owner_org'])


        data = {
                    'journal': org['title'],
                    'datasets': len(packages),
                    'total_views': views,
                    'total_downloads': downloads,
                    'organization': h.get_org(dataset[0]['owner_org']),
                }

        email = h.create_email(data)

        assert data['journal'] == 'Test Organization', 'Wrong title: {}'.format(data['journal'])

        assert int(data['datasets']) == 5, 'Should be 5, {}'.format(data['datasets'])
        assert int(data['total_views']) == 22, 'Should be 22, {}'.format(data['total_views'])
        assert int(data['total_downloads']) == 41, 'Should be 41, {}'.format(data['total_downloads'])

        assert "<a href='/dataset/test_dataset_0'><span class=\"label label-published\">" in email
        assert "<a href='/dataset/test_dataset_1'><span class=\"label label-important\">" in email

        assert False, email


    def _test_14_command_line_interface(self):
        import os
        result = os.system('paster report send a-new-journal -c /etc/ckan/default/development.ini')
        assert False, '>>>{}'.format(result)

    def test_15_create_body(self):
        dataset, resources = self._create_package_resource(num_resources=8, resource=True, num_journals=15)

        data = {
                    'journal': 'Test Journal Title',
                    'datasets': '15',
                    'total_views': '57',
                    'total_downloads': '20',
                    'organization': h.get_org(dataset[0]['owner_org']),
                }

        body = h.create_email(data)

        assert False, body
