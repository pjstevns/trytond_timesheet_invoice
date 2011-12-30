
from trytond.model import ModelView, ModelSQL, fields
from trytond.wizard import Wizard
from trytond.transaction import Transaction
from trytond.backend import TableHandler
from trytond.pool import Pool

import logging
import datetime

log = logging.getLogger(__name__)

class ProjectWork(ModelSQL, ModelView):
    'Work'
    _name = 'project.work'
    _description = __doc__

    def init(self, module_name):
        super(ProjectWork, self).init(module_name)
        cursor = Transaction().cursor
        table = TableHandler(cursor, self, module_name)
        log.debug(table)
        if table.column_exist('billable'):
            log.debug("drop billable from table")
            table.drop_column('billable', exception=True)

    def get_rec_name(self, ids, name):
        if not ids:
            return {}
        res = {}
        def _name(work):
            if work.parent:
                return _name(work.parent) + '\\' + work.name
            else:
                return work.name
        for work in self.browse(ids):
            res[work.id] = _name(work)
        return res


ProjectWork()

class Work(ModelSQL, ModelView):
    'Work'
    _name = 'timesheet.work'
    _description = __doc__
    
    billable = fields.Boolean('Billable')
    billable_hours = fields.Function(
        fields.Float('Billable Hours'),
        'get_billable_hours'
    )

    def get_billable_timesheet_lines(self, ids):
        res = {}
        line_obj = Pool().get('timesheet.line')
        line_ids = line_obj.search([('work','in',ids),('billable','=',True),('billed','=',False)])
        return line_obj.browse(line_ids)

    def _billable_hours(self, work):
        hours = 0.0
        for line in self.get_billable_timesheet_lines([work.id]):
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

class InvoiceBillableWork(Wizard):
    'Invoice Billable Timesheet lines on Billable Work'
    _name = 'project.invoice_billable_work'
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
        pw_obj = Pool().get('project.work')
        invoicedata = {}
        works = pw_obj.browse(data.get('ids'))
        # find all children
        def _descend(works):
            children = []
            for work in works:
                if work.children:
                    children = children + _descend(work.children)
                else:
                    children.append(work)
            return list(set(children))

        for work in _descend(works):
            party = self._get_party(work)
            product = self._get_product(work)

            if not party:
                log.warning("unable to find party for work: %s" % work)
                continue
            if not product:
                log.warning("unable to find product for work: %s" % work)
                continue
            if not invoicedata.get(party.id):
                invoicedata[party.id] = []
            invoicedata[party.id].append((work, product))
        for (party_id, data) in invoicedata.items():
            self._build_invoice(party_id, data)
        return {}

    def _build_invoice(self, party_id, data):
        log.debug('party_id: %s data: %s' %(party_id, data))
        if len(data) < 1: return None

        pool = Pool()
        config_obj = pool.get('timesheet_invoice.configuration')
        config = config_obj.browse(1)
        description = config.description

        party_obj = pool.get('party.party')
        journal_obj = pool.get('account.journal')
        invoice_obj = pool.get('account.invoice')
        line_obj = pool.get('account.invoice.line')

        party = party_obj.browse([party_id,])[0]
        company = data[0][0].company
        journal = journal_obj.search([('type','=','revenue')], limit=1)[0]
        invoice_date = datetime.date.today()

        invoice_id = invoice_obj.create(dict(
            company = company,
            type = 'out_invoice',
            description = description,
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
        log.debug("invoice: %s, data: %s" %( invoice, data))

        for (work, product) in data:
            billable_lines = work.get_billable_timesheet_lines([work.work.id])

            if not work.billable_hours > 0:
                log.debug("skip %s" % work)
                continue

            if not billable_lines:
                log.debug("skip %s" % work)
                continue

            log.debug("work, product: (%s, %s)" % (work, product))
            quantity = work.billable_hours
            unit_price = work.list_price or product.list_price

            linedata = dict(
                type='line',
                product=product.id,
                invoice = invoice.id,
                description = "[%s] %s" % (product.name, work.rec_name),
                quantity = work.billable_hours,
                unit = product.default_uom.id,
                unit_price = unit_price,
                taxes = [],
                timesheet_lines = [],
            )

            for timesheet_line in billable_lines:
                linedata['timesheet_lines'].append(('add',timesheet_line.id))

            account = product.get_account([product.id],'account_revenue_used')
            if account: 
                linedata['account'] = account.popitem()[1]

            tax_rule_obj = pool.get('account.tax.rule')
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


