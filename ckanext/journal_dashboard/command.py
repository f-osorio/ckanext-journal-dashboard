# -*- coding: utf-8 -*-
import smtplib
import logging
from time import time

from email import utils
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from tabulate import tabulate

import ckanext.journal_dashboard.emails as e
import ckanext.journal_dashboard.helpers as h
import click
from ckan.common import config


log = logging.getLogger(__name__)


""" Creates and sends a report to the journals for their journals items

Usage:
    report send [journal-name] [recipient]
        -- gather summary information for a given
           journal and send a report to the journal editor/manager

Cron:
    --plugin=ckanext-journal-dashboard
"""
#summary = __doc__.split('\n')[0]
#usage = __doc__
max_args = 3
min_args = 3


def gather_data(journal):
    org = h.get_org(journal)
    packages = org.packages
    packages = sorted(packages, key=lambda x: x.total_views, reverse=True)


    num_resources = sum([len(p.resources) for p in packages])

    views_total = 0
    downloads_total = 0
    views_monthly = 0
    downloads_monthly = 0

    summary = [['Datasets', 'Resources', 'Total Views', 'Total Downloads'],
                [len(packages), num_resources, views_total, downloads_total]]

    for package in packages:
        views_total += package.total_views
        views_monthly += package.recent_views
        for resource in package.resources:
            downloads_total += resource.total_downloads
            downloads_monthly += resource.recent_downloads

    data = {
                'prefix': config.get('ckan.site_url'),
                'journal': org.title,
                'summary': summary,
                'packages_text': create_main_text(packages),
                'packages': create_main_table(packages),
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
        out += dataset_string.format(dataset=package.name, views=package.total_views)
        if len(package.resources) > 0:
            out += 'Resources:\n'
            for resource in package.resources:
                if resource.total_downloads >= 0:
                    out += resource_string.format(resource=resource.name or resource.url, days=resource.recent_downloads, total=resource.total_downloads)
                else:
                    out += resource_string_link.format(resource=resource.url)
        else:
            out += '0 Resources\n'
    return out

def create_main_table(packages):
    headers = ['Published?*', 'Data Submission', 'Views',
               'Resource', 'Downloads (Last 30 Days)', 'Downloads (Total)']
    data = []
    for package in packages:
        data += package.as_list()

    table = h.create_table({'headers': headers, 'data': data})

    return table

@click.command()
@click.argument('journal')
@click.argument('address')
def send(journal, address):
    data = gather_data(journal)

    html = get_html()
    text = get_text()

    text = text.format(**data)
    html = html.format(summary_table=tabulate(data['summary'],
                        headers='firstrow', tablefmt='html'),
                        main_table=data['packages'], **data)

    message = MIMEMultipart('alternative', None, [MIMEText(text), MIMEText(html, 'html')])

    message['Subject'] = Header(u"JDA Journal Access Summary")
    message['From'] = config.get('smtp.mail_from')
    message['To'] = address  #Header(address, 'utf-8')
    message['Date'] = utils.formatdate(time())
    message['X-Mailer'] = "JDA Access Summary"

    mail_from = config.get('smtp.mail_from')

    #"""
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
    #"""


def get_html():
    return e.html


def get_text():
    return e.text
