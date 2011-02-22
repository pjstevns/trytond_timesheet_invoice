
from trytond.model import ModelView, ModelSQL, fields

class Line(ModelSQL, ModelView):
    'Timesheet Line'
    _name = 'timesheet.line'
    _description = __doc__

    billable = fields.Boolean('Billable')
    billed = fields.Boolean('Billed', readonly=True)

Line()



