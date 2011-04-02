from trytond.model import ModelView, ModelSQL, fields
import logging
from trytond.pyson import Eval, Not, Equal, Get, In

log = logging.getLogger(__name__)

class Invoice(ModelSQL, ModelView):
    """Invoice"""
    _name = 'account.invoice'

    def writeoff_timesheet(self, ids, trigger_id):
        """ set timesheet lines on all invoice lines to state:billed"""
        invoice_obj = self.pool.get('account.invoice')
        invoice_line_obj = self.pool.get('account.invoice.line')
        timesheet_line_obj = self.pool.get('timesheet.line')

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
    timesheet_lines = fields.Many2Many('account_invoice_line-timesheet_line',
                                      'invoice_line', 'timesheet_line', 'Timesheet Lines')

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

class InvoiceLineTimesheetLine(ModelSQL, ModelView):
    """ many2many relation for timesheet_line and invoice_line """
    _name = 'account_invoice_line-timesheet_line'
    _description = __doc__

    timesheet_line = fields.Many2One('timesheet.line', 'Timesheet Line')
    invoice_line = fields.Many2One('account.invoice.line', 'Invoice Line')

InvoiceLineTimesheetLine()

class Line(ModelSQL, ModelView):                                                                                                                                              
    """Timesheet Line"""
    _name = 'timesheet.line'
    invoice_line = fields.Many2One('account.invoice.line', 'Invoice Line',
                                  readonly=True)

Line()


