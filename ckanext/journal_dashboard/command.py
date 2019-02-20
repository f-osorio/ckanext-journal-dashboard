from ckan.lib.cli import CkanCommand

class JournalSummaryReport(CkanCommand):
    """ Creates and sends a report to the journals for their journals items

    Usage:
        summary-report send [journal-name] [receipiant] -- gather summary information for a given journal and send a report to the journal editor/manager
    """
    summary = __doc__.split('\n')[0]
    usage = __doc__
    max_args = 2
    min_args = 2

    def command(self):
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
            self.send()
        else:
            print('Command {} not recognized'.format(cmd))

    def send(self, journal, who):
        return False
