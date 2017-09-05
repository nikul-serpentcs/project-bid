# -*- coding: utf-8 -*-
# © 2015-17 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from openerp import models, fields, api
from openerp.tools.translate import _
import time
from openerp.exceptions import ValidationError


class ProjectBidTemplate(models.Model):
    _name = 'project.bid.template'
    _description = "Project Bid Template"

    name = fields.Char('Description', size=256, required=True)
    default_component_labor = fields.Many2many(
            'product.product',
            'project_bid_product_rel',
            'product_id',
            'project_bid_template_id',
            string='Default component labor',
            required=False)
    profit_rate = fields.Float('Profit (%)', help="Profit as % of COGS")
    overhead_rate = fields.Float('Default overhead (%)')
    labor_uom_id = fields.Many2one('product.uom', 'Default labor UoM',
                                        required=True)

    @api.multi
    @api.constrains('default_component_labor', 'labor_uom_id')
    def _check_labor_uom(self):
        for template in self:
            for labor in template.default_component_labor:
                if labor.uom_id.id is not template.labor_uom_id.id:
                    raise ValidationError (_('The labor must be entered in the '
                                           'default labor unit of measure.'))
        return True
