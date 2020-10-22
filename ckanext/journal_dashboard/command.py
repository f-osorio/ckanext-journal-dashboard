# -*- coding: utf-8 -*-
import csv
import smtplib
import logging
from time import time
from tabulate import tabulate

from email import utils
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ckan.common import config
import ckanext.journal_dashboard.emails as e
import ckanext.journal_dashboard.helpers as h
import ckanext.journal_dashboard.journal_classes as jc

import click


log = logging.getLogger(__name__)


""" Creates and sends a report to the journals for their journals items

Usage:
    /home/edawax/ckanenv/bin/paster --plugin=ckanext-journal-dashbaord...
    report send [journal-name] [recipient] -- gather summary information for a given journal and send a report to the journal editor/manager

Cron:
    --plugin=ckanext-journal-dashboard
"""
#summary = __doc__.split('\n')[0]
#usage = __doc__
max_args = 3
min_args = 3

import ckan.model as model
engine = model.meta.engine

"""
def command(self):
    self._load_config()
    import ckan.model as model
    engine = model.meta.engine

    if not self.args:
        # default to printing help
        print(self.usage)
        return

    cmd = self.args[0]
    # Do not run load_config yet
    if cmd == 'rebuild_fast':
        self.rebuild_fast()
        return

    self._load_config()
    if cmd == 'send':
        journal = self.args[1]
        address = self.args[2]
        self.send(engine, journal, address)
    else:
        print('Command {} not recognized'.format(cmd))
"""

def gather_data(engine, journal):
    org = h.get_org(journal)
    packages = org['packages']

    views_total = h.total_views_across_journal_datasets(packages[0]['owner_org'], engine_check=engine)
    downloads_total = h.total_downloads_journal(packages[0]['owner_org'], engine_check=engine)

    views_monthly = h.last_month_views_across_journal_datasets(packages[0]['owner_org'], engine_check=engine)
    downloads_monthly = h.total_downloads_journal(packages[0]['owner_org'], engine_check=engine, monthly=True)

    package_list = []
    for package in packages:
        package_list.append(jc.Dataset(engine, package['id']))
        package_list = sorted(package_list, key=lambda x: x.views, reverse=True)

    num_resources = sum([len(p.resources) for p in package_list])

    summary = [['Datasets', 'Resources', 'Total Views', 'Total Downloads'],
                [len(packages), num_resources, views_total, downloads_total]]

    data = {
                'prefix': config.get('ckan.site_url'),
                'journal': org['title'],
                'summary': summary,
                'packages_text': create_main_text(package_list),
                'packages': create_main_table(package_list),
                'package_num': len(packages),
                'package_resources': num_resources,
                'package_view_total': views_total,
                'package_download_total': downloads_total,
                'package_view_monthly': views_monthly,
                'package_download_monthly': downloads_monthly,
            }
    #'organization': h.get_org(packages[0]['owner_org']),
    return data

def create_main_text(packages):
    out = ""
    dataset_string = u"\n{dataset}\nViews: {views}\n"
    resource_string = u"\t{resource}\n\t\tDownloads (Last 30 Days): {days}\n\t\tDownloads (Total): {total}\n"
    resource_string_link = u'\t{resource}\n'

    for package in packages:
        out += dataset_string.format(dataset=package.name, views=package.views)
        if len(package.resources) > 0:
            out += 'Resources:\n'
            for resource in package.resources:
                if resource.total_downloads >= 0:
                    out += resource_string.format(resource=resource.name or resource.url, days=resource.previous_month_downloads, total=resource.total_downloads)
                else:
                    out += resource_string_link.format(resource=resource.url)
        else:
            out += '0 Resources\n'
    return out

def create_main_table(packages):
    headers = ['Published?*', 'Data Submission', 'Views', 'Resource', 'Downloads (Last 30 Days)', 'Downloads (Total)']
    data = []
    for package in packages:
        data += package.as_list()

    table = h.create_table({'headers': headers, 'data': data})

    return table

@click.command()
@click.argument('journal')
@click.argument('address')
def send(journal, address):
    data = gather_data(engine, journal)

    html = get_html()
    text = get_text()

    text = text.format(**data)
    html = html.format(summary_table=tabulate(data['summary'], headers='firstrow', tablefmt='html'), main_table=data['packages'], **data)

    message = MIMEMultipart('alternative', None, [MIMEText(text), MIMEText(html, 'html')])

    message['Subject'] = Header(u"JDA Journal Access Summary")
    message['From'] = config.get('smtp.mail_from')
    message['To'] = address  #Header(address, 'utf-8')
    message['Date'] = utils.formatdate(time())
    message['X-Mailer'] = "JDA Access Summary"

    mail_from = config.get('smtp.mail_from')

    try:
        smtp_server = config.get('smtp.test_server', config.get('smtp.server'))
        smtp_connection = smtplib.SMTP(smtp_server)
        smtp_connection.sendmail(mail_from, [address], message.as_string())
        log.info(f"Sent notification to {address}")
        smtp_connection.quit()
        return True
    except Exception as e:
        log.error(f"Mail to {address} could not be sent")
        log.error(e)
        return False


def get_html():
    return e.html


def get_text():
    return e.text
