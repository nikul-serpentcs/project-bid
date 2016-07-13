# -*- coding: utf-8 -*-
# © 2015 Eficent Business and IT Consulting Services S.L.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).

from openerp.osv import fields, orm
from openerp.tools.translate import _
import time


class project_bid_template(orm.Model):
    _name = 'project.bid.template'
    _description = "Project Bid Template"

    _columns = {
        'name': fields.char('Description', size=256, required=True),
        'default_component_labor': fields.many2many(
            'product.product',
            string='Default component labor',
            required=False),
        'profit_rate': fields.float('Profit (%)', help="Profit as % of COGS"),
        'overhead_rate': fields.float('Default overhead (%)'),
        'labor_uom_id': fields.many2one('product.uom', 'Default labor UoM',
                                        required=True),
    }

    def _check_labor_uom(self, cr, uid, ids, context=None):
        for template in self.browse(cr, uid, ids, context=context):
            for labor in template.default_component_labor:
                if labor.uom_id.id is not template.labor_uom_id.id:
                    return False

        return True

    _constraints = [(_check_labor_uom, 'Error ! The labor must be entered '
                                       'in the default labor unit of measure.',
                     ['labor_uom_id', 'default_component_labor'])]