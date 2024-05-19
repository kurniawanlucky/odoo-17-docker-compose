from odoo import api, fields, models, _


class MasterPeriod(models.Model):
    _name = 'master.period'

    name = fields.Char('Period', required=True)
