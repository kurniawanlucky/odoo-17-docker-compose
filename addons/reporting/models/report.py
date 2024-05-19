from collections import defaultdict
from datetime import timedelta
from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.fields import Command
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, float_round, format_date, groupby


class Report(models.Model):
    _name = 'report'
    _inherit = ['portal.mixin', 'product.catalog.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Reports"
    _order = 'date_order desc, id desc'

    @api.model
    def year_selection(self):
        year = 2000  # replace 2000 with your a start year
        year_list = []
        while year != 2030:  # replace 2030 with your end year
            year_list.append((str(year), str(year)))
            year += 1
        return year_list

    name = fields.Char(
        string="Reference",
        required=True, copy=False, readonly=False,
        index='trigram',
        default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', 'Partner', default=lambda self: self.env.user.partner_id)
    validity_date = fields.Date(
        string="Expiration",
        compute='_compute_validity_date',
        store=True, readonly=False, copy=False, precompute=True)
    order_line = fields.One2many(
        comodel_name='report.line',
        inverse_name='order_id',
        string="Order Lines",
        copy=True, auto_join=True)
    date_order = fields.Datetime(
        string="Order Date",
        required=True, copy=False,
        help="Creation date of draft/sent orders,\nConfirmation date of confirmed orders.",
        default=fields.Datetime.now)
    period_id = fields.Many2one('master.period')
    year = fields.Selection(
        year_selection,
        string="Year",
        default="2019",  # as a default value it would be 2019
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)
    user_id = fields.Many2one(
        comodel_name='res.users',
        string="Salesperson",
        compute='_compute_user_id',
        store=True, readonly=False, precompute=True, index=True,
        tracking=2,
        domain=lambda self: "[('groups_id', '=', {}), ('share', '=', False), ('company_ids', '=', company_id)]".format(
            self.env.ref("sales_team.group_sale_salesman").id
        ))
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ],
        string='Status',
        required=True,
        readonly=True,
        copy=False,
        tracking=True,
        default='draft',
    )

    @api.depends('partner_id')
    def _compute_user_id(self):
        for order in self:
            if order.partner_id and not (order._origin.id and order.user_id):
                # Recompute the salesman on partner change
                #   * if partner is set (is required anyway, so it will be set sooner or later)
                #   * if the order is not saved or has no salesman already
                order.user_id = (
                        order.partner_id.user_id
                        or order.partner_id.commercial_partner_id.user_id
                        or (self.user_has_groups('sales_team.group_sale_salesman') and self.env.user)
                )

    def _can_be_confirmed(self):
        self.ensure_one()
        return self.state in {'draft'}

    def _prepare_confirmation_values(self):
        """ Prepare the sales order confirmation values.

        Note: self can contain multiple records.

        :return: Sales Order confirmation values
        :rtype: dict
        """
        return {
            'state': 'posted',
            'date_order': fields.Datetime.now()
        }

    def action_confirm(self):
        """ Confirm the given quotation(s) and set their confirmation date.

        If the corresponding setting is enabled, also locks the Sale Order.

        :return: True
        :rtype: bool
        :raise: UserError if trying to confirm cancelled SO's
        """
        if not all(order._can_be_confirmed() for order in self):
            raise UserError(_(
                "The following orders are not in a state requiring confirmation: %s",
                ", ".join(self.mapped('display_name')),
            ))

        self.write(self._prepare_confirmation_values())

        return True

    # @api.model_create_multi
    # def create(self, vals_list):
    #     for vals in vals_list:
    #         if 'company_id' in vals:
    #             self = self.with_company(vals['company_id'])
    #         if vals.get('name', _("New")) == _("New"):
    #             vals['name'] = self.env['ir.sequence'].next_by_code('report') or _("New")

    @api.depends('company_id')
    def _compute_validity_date(self):
        today = fields.Date.today()
        for order in self:
            days = order.company_id.quotation_validity_days
            if days > 0:
                order.validity_date = today + timedelta(days)
            else:
                order.validity_date = False
