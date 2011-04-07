import os
import logging

from z3c.rml import pagetemplate
from trytond.report import Report
from trytond.transaction import Transaction

log = logging.getLogger(__name__)


class InvoiceTimesheetLinesReport(Report):
    _name='account.invoice.timesheet_lines_report'

    def parse(self, report, objects, data, localcontext):
        log.debug("parse %s %s %s %s" % (report, objects, data, localcontext))
        user_obj = self.pool.get('res.user')
        user = user_obj.browse(Transaction().user)

        invoice = objects[0]

        localcontext['company'] = user.company
        localcontext['invoice'] = invoice

        if not report.report:
            raise Exception('Error', 'Missing report file!')
        os.chdir(os.path.dirname(__file__))
        res = (report.extension, pagetemplate.RMLPageTemplateFile(report.report)(**localcontext))

        return res


InvoiceTimesheetLinesReport()

