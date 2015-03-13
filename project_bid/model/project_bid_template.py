# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Eficent (<http://www.eficent.com/>)
#              Jordi Ballester <jordi.ballester@eficent.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

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
        'material_markup': fields.float('Material markup'),
        'labor_markup': fields.float('Labor markup'),
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