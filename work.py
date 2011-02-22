
from trytond.model import ModelView, ModelSQL, fields
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



