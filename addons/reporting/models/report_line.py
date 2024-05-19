from collections import defaultdict
from datetime import timedelta
from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, float_round, format_date, groupby


class ReportLine(models.Model):
    _name = 'report.line'
    _inherit = 'analytic.mixin'
    _description = "Sales Order Line"
    _rec_names_search = ['name', 'order_id.name']
    _order = 'order_id, sequence, id'
    _check_company_auto = True

    order_id = fields.Many2one(
        comodel_name='report',
        string="Reference",
        required=True, ondelete='cascade', index=True, copy=False)
    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product",
        change_default=True, ondelete='restrict', index='btree_not_null',
        domain="[('sale_ok', '=', True)]")
    name = fields.Text(
        string="Description",
        compute='_compute_name',
        store=True, readonly=False, required=True, precompute=True)
    sequence = fields.Integer(string="Sequence", default=10)
    company_id = fields.Many2one(
        related='order_id.company_id',
        store=True, index=True, precompute=True)
    attachment_ids = fields.One2many('ir.attachment', 'res_id',
                                     domain=[('res_model', '=', 'report.line')],
                                     string='Attachments')
    state = fields.Selection(
        related='order_id.state',
        string="Order Status",
        copy=False, store=True, precompute=True)

    def _get_sale_order_line_multiline_description_sale(self):
        """ Compute a default multiline description for this sales order line.

        In most cases the product description is enough but sometimes we need to append information that only
        exists on the sale order line itself.
        e.g:
        - custom attributes and attributes that don't create variants, both introduced by the "product configurator"
        - in event_sale we need to know specifically the sales order line as well as the product to generate the name:
          the product is not sufficient because we also need to know the event_id and the event_ticket_id (both which belong to the sale order line).
        """
        self.ensure_one()
        return self.product_id.get_product_multiline_description_sale()


    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            if not line.product_id:
                continue
            name = line._get_sale_order_line_multiline_description_sale()
            line.name = name
