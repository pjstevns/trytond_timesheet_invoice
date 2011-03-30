
from trytond.pyson import Eval
from trytond.model import ModelView, ModelSQL, fields
from trytond.wizard import Wizard
import logging

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

class InvoiceBillableWorkInit(ModelView):
    'Select Billable Timesheet lines on Work'
    _name = 'timesheet.invoice_billable_work.init'
    _description = __doc__

    party = fields.Many2One('party.party', 'Party', required=True)
    work = fields.One2Many('timesheet.work', 'party', 'Work', 
                           readonly=True,
                           on_change=['timesheet_lines'],
                           on_change_with=['party'])

    timesheet_lines = fields.One2Many('timesheet.line', 'work', 'Timesheet Lines',
                                      readonly=True,
                                      on_change_with=['work','party']
                                     )

    def on_change_timesheet_lines(self, vals):
        print vals
        return []

    def on_change_with_work(self, vals):
        work_obj = self.pool.get('timesheet.work')
        project_work_obj = self.pool.get('project.work')
        work = project_work_obj.search([
            ('party','=',vals.get('party')),
        ])
        return work

    def on_change_with_timesheet_lines(self, vals):
        print "onchange_with", vals
        work_ids = [ x.get('id') for x in vals.get('work') ]
        print work_ids
        timesheet_lines_obj = self.pool.get('timesheet.line')
        lines = timesheet_lines_obj.search([
            ('work','in',work_ids),
            ('billable','=',True),
            ('billed','=',False)
        ])
        return lines

InvoiceBillableWorkInit()

class InvoiceBillableWork(Wizard):
    'Invoice Billable Timesheet lines on Billable Work'
    _name = 'timesheet.invoice_billable_work'
    states = {
        'init': {
            'result': {
                'actions': ['_init'],
                'type': 'form',
                'object': 'timesheet.invoice_billable_work.init',
                'state': [
                    ('end','Cancel','tryton-cancel'),
                    ('create','Create Invoice', 'tryton-ok', True),
                ],
            },
        },
        'create': {
            'actions': ['_create_invoice'],
            'result': {
                'type': 'state',
                'state': 'end',
            },
        },
    }

    def _create_invoice(self, data):
        log.debug('data: %s' % data)
        return {}

InvoiceBillableWork()


