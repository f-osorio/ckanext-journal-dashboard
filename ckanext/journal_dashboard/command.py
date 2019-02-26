import smtplib
import logging
import tabulate
from time import time

from email import Utils
from email.header import Header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from pylons import config
from ckan.lib.cli import CkanCommand
import ckanext.journal_dashboard.emails as e
import ckanext.journal_dashboard.helpers as h


log = logging.getLogger(__name__)


class JournalSummaryReport(CkanCommand):
    """ Creates and sends a report to the journals for their journals items

    Usage:
        summary-report send [journal-name] [recipient] -- gather summary information for a given journal and send a report to the journal editor/manager
    """
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 3
    min_args = 3

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


    def gather_data(self, engine, journal):
        org = h.get_org(journal)
        packages = org['packages']

        views = h.total_views_across_journal_datasets(packages[0]['owner_org'], engine_check=engine)
        downloads = h.total_downloads_journal(packages[0]['owner_org'], engine_check=engine)

        data = {
                  'prefix': config.get('ckan.site_url'),
                  'journal': org['title'],
                  'datasets': len(packages),
                  'total_views': views,
                  'total_downloads': downloads,
                  'organization': h.get_org(packages[0]['owner_org']),
                }

        return data



    def send(self, engine, journal, address):
        data = self.gather_data(engine, journal)
        data['engine'] = engine

        html = self.get_html()
        text = self.get_text()

        #html = html.format(table=tabulate(data, headers="firstrow", tablefmt="html"))
        #text = text.format(table=tabulate(data, headers="firstrow", tablefmt="grid"))

        html = html.format(**data)

        message = MIMEMultipart('alternative', None, [MIMEText(text), MIMEText(html, 'html')])
        message['Subject'] = Header(u"Journal Acess Summary")
        message['From'] = config.get('smtp.mail_from')
        message['To'] = Header(address, 'utf-8')
        message['Date'] = Utils.formatdate(time())
        message['X-Mailer'] = "JDA ???"

        mail_from = config.get('smtp.mail_from')

        try:
            smtp_server = config.get('smtp.test_server', config.get('smtp.server'))
            smtp_connection = smtplib.SMTP(smtp_server)
            smtp_connection.sendmail(mail_from, [address], message.as_string())
            log.info("Sent notification to {0}".format(address))
            smtp_connection.quit()
            return True
        except Exception as e:
            log.error("Mail to {} could not be sent".format(address))
            log.error(e)
            print('Failure')
            print(e)
            # raise Exception  # TODO raise more detailed exception
            return False


    def get_html(self):
        return e.html


    def get_text(self):
        return e.text
