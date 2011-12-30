
import logging

from trytond.model import ModelWorkflow, ModelView, ModelSQL, fields
from trytond.pyson import Eval, Not, Equal, Get, In
from trytond.pool import Pool

log = logging.getLogger(__name__)

class Invoice(ModelWorkflow, ModelSQL, ModelView):
    """Invoice"""
    _name = 'account.invoice'

    timesheet_report = fields.Binary('Timesheet Report', readonly=True)
    timesheet_report_format = fields.Char('Timesheet Report Format', readonly=True)

    def __init__(self):
        super(Invoice, self).__init__()
        self._check_modify_exclude.append('timesheet_report')
        self._check_modify_exclude.append('timesheet_report_format')

    def copy(self, ids, default=None):
        if default is None:
            default={}
        default=default.copy()
        default['timesheet_report'] = False
        default['timesheet_report_format'] = False
        return super(Invoice, self).copy(ids, default)

    def writeoff_timesheet(self, ids, trigger_id):
        """ set timesheet lines on all invoice lines to state:billed"""

        pool = Pool()
        invoice_obj = pool.get('account.invoice')
        invoice_line_obj = pool.get('account.invoice.line')
        timesheet_line_obj = pool.get('timesheet.line')

        invoices = invoice_obj.browse(ids)
        for invoice in invoices:
            for invoice_line in invoice.lines:
                for timesheet_line in invoice_line.timesheet_lines:
                    timesheet_line_obj.write(timesheet_line.id, {'billed': True})
        return

Invoice()

class InvoiceLine(ModelSQL, ModelView):
    """Invoice Line"""
    _name = 'account.invoice.line'

    work = fields.Many2One('timesheet.work','Work')
    timesheet_lines = fields.One2Many(
        'timesheet.line', 
        'invoice_line',
        'Timesheet Lines',
        add_remove = [
            ('invoice_line','=',False),
            ('work','=',Eval('work')),
            ('billable','=',True),
            ('hours','>',0),
        ],
    )


    # add timesheet_lines to on_change_with list on parent
    quantity = fields.Float('Quantity',
                            digits=(16, Eval('unit_digits', 2)),
                            states={
                                'invisible': Not(Equal(Eval('type'), 'line')),
                                'required': Equal(Eval('type'), 'line'),
                            }, on_change_with=['timesheet_lines'])

    # add timesheet_lines to on_change_with list on parent
    amount = fields.Function(fields.Numeric('Amount',
                                            digits=(16, Get(Eval('_parent_invoice', {}), 
                                                            'currency_digits', 
                                                            Eval('currency_digits', 2))),
                                            states={ 
                                                'invisible': Not(In(Eval('type'), ['line', 'subtotal'])), 
                                            }, on_change_with=[
                                                'type', 'quantity', 'unit_price', 
                                                '_parent_invoice.currency',
                                                'currency','timesheet_lines',
                                            ]),
                             'get_amount')

    def on_change_with_quantity(self, vals):
        hours = 0.0
        for line in vals.get('timesheet_lines'):
            hours = hours + line.get('hours')
        return hours

InvoiceLine()

# o2m target
class Line(ModelSQL, ModelView):
    """Timesheet Line"""
    _name = 'timesheet.line'
    invoice_line = fields.Many2One(
        'account.invoice.line', 
        'Invoice Line',
        readonly=True
    )
Line()


# deprecated storage using m2m
class InvoiceLineTimesheetLine(ModelSQL, ModelView):
    """ many2many relation for timesheet_line and invoice_line """
    _name = 'account_invoice_line-timesheet_line'
    _description = __doc__

    timesheet_line = fields.Many2One('timesheet.line', 'Timesheet Line')
    invoice_line = fields.Many2One('account.invoice.line', 'Invoice Line')

InvoiceLineTimesheetLine()

