# -*- coding: utf-8 -*-
# © 2015-17 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from openerp import api, fields, models


class ProjectBidTemplate(models.Model):
    _inherit = 'project.bid.template'

    version_id = fields.Many2one('account.analytic.plan.version',
                                 'Planning Version', required=True,),
    revenue_product_id = fields.Many2one('product.product',
                                         'Revenue product',
                                          required=True)
    expense_product_id = fields.Many2one('product.product',
                                         'Default material expenses product',
                                         required=True)
