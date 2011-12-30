import os
import logging
import base64

from z3c.rml import pagetemplate
from trytond.report import Report
from trytond.transaction import Transaction
from trytond.pool import Pool

log = logging.getLogger(__name__)


class TimesheetLinesReport(Report):
    _name='project.work.timesheet_lines_report'

    def parse(self, report, objects, data, localcontext):
        log.debug("parse %s %s %s %s" % (report, objects, data, localcontext))
        pool = Pool()
        work_obj = pool.get('project.work')
        user_obj = pool.get('res.user')

        work = objects[0]

        user = user_obj.browse(Transaction().user)
        localcontext['company'] = user.company
        localcontext['work'] = work

        if not report.report:
            raise Exception('Error', 'Missing report file!')
        os.chdir(os.path.dirname(__file__))
        res = (report.extension, pagetemplate.RMLPageTemplateFile(report.report)(**localcontext))

        return res

TimesheetLinesReport()

class InvoiceTimesheetLinesReport(Report):
    _name='account.invoice.timesheet_lines_report'

    def __init__(self):
        super(InvoiceTimesheetLinesReport, self).__init__()
        self._rpc['execute'] = True

    def parse(self, report, objects, data, localcontext):
        log.debug("parse %s %s %s %s" % (report, objects, data, localcontext))
        pool = Pool()
        invoice_obj = pool.get('account.invoice')
        user_obj = pool.get('res.user')

        invoice = objects[0]
        if invoice.timesheet_report:
            return (invoice.timesheet_report_format, 
                    base64.decodestring(invoice.timesheet_report))

        user = user_obj.browse(Transaction().user)
        localcontext['company'] = user.company
        localcontext['invoice'] = invoice

        if not report.report:
            raise Exception('Error', 'Missing report file!')
        os.chdir(os.path.dirname(__file__))
        res = (report.extension, pagetemplate.RMLPageTemplateFile(report.report)(**localcontext))

        if invoice.state in ('open','paid'):
            invoice_obj.write(invoice.id, {
                'timesheet_report_format': res[0],
                'timesheet_report': base64.encodestring(res[1])
            })

        return res


InvoiceTimesheetLinesReport()

