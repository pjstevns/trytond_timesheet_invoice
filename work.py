
from trytond.model import ModelView, ModelSQL, fields
from trytond.wizard import Wizard
import logging
import datetime

from trytond.pyson import Eval, Not, Equal

log = logging.getLogger(__name__)

class Work(ModelSQL, ModelView):
    'Work'
    _name = 'timesheet.work'
    _description = __doc__

    billable = fields.Boolean('Billable')
    billable_hours = fields.Function(fields.Float('Billable Hours'),
                                     'get_billable_hours')

    def _billable_hours(self, work):
        hours = 0.0
        line_obj = self.pool.get('timesheet.line')
        line_ids = line_obj.search([('work','=',work.id),('billable','=',True),('billed','=',False)])
        for line in line_obj.browse(line_ids):
            hours += line.hours
        for child in work.children:
            hours += self._billable_hours(child)
        return hours

    def get_billable_hours(self, ids, name):
        res = {}
        for work in self.browse(ids):
            res[work.id] = self._billable_hours(work)

        return res

Work()

class InvoiceLine(ModelSQL, ModelView):
    """Invoice Line"""
    _name = 'account.invoice.line'
    timesheet_lines = fields.One2Many('timesheet.line', 'invoice_line',
                                      'Timesheet Lines')

    quantity = fields.Float('Quantity',
                            digits=(16, Eval('unit_digits', 2)),
                            states={
                                'invisible': Not(Equal(Eval('type'), 'line')),
                                'required': Equal(Eval('type'), 'line'),
                            }, on_change_with=['timesheet_lines'])

    def on_change_with_quantity(self, vals):
        hours = 0.0
        for line in vals.get('timesheet_lines'):
            hours = hours + line.get('hours')
        return hours

InvoiceLine()

class Line(ModelSQL, ModelView):                                                                                                                                              
    """Timesheet Line"""
    _name = 'timesheet.line'
    invoice_line = fields.Many2One('account.invoice.line', 'Invoice Line',
                                  readonly=True)

Line()


class InvoiceBillableWork(Wizard):
    'Invoice Billable Timesheet lines on Billable Work'
    _name = 'timesheet.invoice_billable_work'
    states = {
        'init': {
            'result': {
                'type': 'action',
                'action': '_create_invoice',
                'state': 'end',
            },
        },
    }

    def _create_invoice(self, data):
        log.debug('data: %s' % data)
        work_obj = self.pool.get('project.work')
        works = work_obj.browse(data.get('ids'))
        invoicedata = {}
        for work in works:
            log.debug('work: %s' % work)
            work_party = self._get_party(work)
            work_product = self._get_product(work)

            if not work_party:
                log.warning("unable to find party for work: %s" % work)
                continue
            if not work_product:
                log.warning("unable to find product for work: %s" % work)
                continue

            if not invoicedata.get(work_party.id):
                invoicedata[work_party.id] = []

            invoicedata[work_party.id].append((work, work_product))

            log.debug('party: %s' % work_party.name)
            log.debug('product: %s' % work_product.name)

        log.debug("invoices: %s" % invoicedata)
    
        for (party_id, data) in invoicedata.items():
            self._build_invoice(party_id, data)

        return {}


    def _build_invoice(self, party_id, data):
        if len(data) < 1: return None

        party_obj = self.pool.get('party.party')
        journal_obj = self.pool.get('account.journal')
        invoice_obj = self.pool.get('account.invoice')
        line_obj = self.pool.get('account.invoice.line')

        party = party_obj.browse([party_id,])[0]
        company = data[0][0].company
        journal = journal_obj.search(['code','=','DEB'])[0]
        invoice_date = datetime.date.today()

        invoice_id = invoice_obj.create(dict(
            company = company,
            type = 'out_invoice',
            description = 'Test Invoice',
            state = 'draft',
            currency = company.currency.id,
            journal = journal,
            account = party.account_receivable.id or company.account_receivable.id,
            payment_term = party.payment_term.id or company.payment_term.id,
            party = party.id,
            invoice_address = party.address_get(party.id, type='invoice'),
            invoice_date=invoice_date,
        ))
        invoice = invoice_obj.browse([invoice_id])[0]
        log.debug("invoice: %s", invoice)

        for (work, product) in data:
            log.debug("work, product: (%s, %s)" % (work, product))
            quantity = work.billable_hours
            unit_price = work.list_price or product.list_price

            log.debug("timesheet_lines: %s" % [ x.id for x in
                                               work.timesheet_lines] )
            linedata = dict(
                type='line',
                product=product.id,
                invoice = invoice.id,
                description = "%s %s" % (work.name, product.name),
                quantity = work.billable_hours,
                unit = product.default_uom.id,
                unit_price = unit_price,
                taxes = [],
                timesheet_lines = [],
            )

            for timesheet_line in work.timesheet_lines:
                linedata['timesheet_lines'].append(('add',timesheet_line.id))

            account = product.get_account([product.id],'account_revenue_used')
            if account: 
                linedata['account'] = account.popitem()[1]

            tax_rule_obj = self.pool.get('account.tax.rule')
            taxes = product.get_taxes([product.id], 'customer_taxes_used')
            for tax in taxes[product.id]:
                pattern = {}
                if party.customer_tax_rule:
                    tax_ids = tax_rule_obj.apply(party.customer_tax_rule, tax, pattern)
                    if tax_ids:
                        for tax_id in tax_ids:
                            linedata['taxes'].append(('add',tax_id))
                        continue
                linedata['taxes'].append(('add',tax))

            line_obj.create(linedata)

    def _get_party(self, work):
        if work.party: return work.party
        if work.parent: return self._get_party(work.parent)
        return None

    def _get_product(self, work):
        if work.product: return work.product
        if work.parent: return self._get_product(work.parent)
        return None

InvoiceBillableWork()


