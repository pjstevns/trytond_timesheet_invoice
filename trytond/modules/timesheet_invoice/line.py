
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool

import logging
log = logging.getLogger(__name__)

class Line(ModelSQL, ModelView):
    'Timesheet Line'
    _name = 'timesheet.line'
    _description = __doc__

    billable = fields.Boolean('Billable', on_change_with=['work'])
    billed = fields.Boolean('Billed', readonly=True)

    def on_change_with_billable(self, vals):
        work_obj = Pool().get('timesheet.work')
        work = work_obj.browse([vals.get('work')])[0]
        return work.billable

Line()
