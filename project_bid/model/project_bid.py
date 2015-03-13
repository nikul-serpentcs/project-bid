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
import openerp.addons.decimal_precision as dp


class project_bid_total_costs_line(orm.TransientModel):
    _name = 'project.bid.total.costs.line'
    _description = "Project Bid Totalization Line"

    def _get_cost_total(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = record.quantity * record.unit_cost
        return res

    _columns = {
        'bid_id': fields.many2one('project.bid', string='Bid',
                                  required=True),
        'name': fields.char('Description', size=256),
        'quantity': fields.float('Hours'),
        'unit_cost': fields.float(
            'Unit Cost', digits_compute=dp.get_precision('Account')),
        'total_cost': fields.function(
            _get_cost_total, type='float', string='Total labor cost',
            digits_compute=dp.get_precision('Account')),
    }


class project_bid_totals(orm.TransientModel):
    _name = 'project.bid.totals'
    _description = "Project Bid Totals"

    def _get_sell_total(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, 0.0)
        total_costs = {}
        for record in self.browse(cr, uid, ids, context=context):
            if record.bid_id.id in total_costs:
                total_costs[record.bid_id.id] += record.cost
            else:
                total_costs[record.bid_id.id] = record.cost
        for record in self.browse(cr, uid, ids, context=context):
            if not record.is_markup_over_costs:
                res[record.id] = record.cost * record.markup
            else:
                res[record.id] = total_costs[record.bid_id.id] * record.markup
        return res

    _columns = {
        'bid_id': fields.many2one('project.bid', string='Bid', required=True),
        'name': fields.char('Description', size=256),
        'cost': fields.float('Cost'),
        'markup': fields.float('Markup'),
        'is_markup_over_costs': fields.boolean('Markup over costs'),
        'sell_total': fields.function(_get_sell_total,
                                      type='float', string='Sell Total'),
    }

    _defaults = {
        'is_markup_over_costs': False
    }


class project_bid(orm.Model):
    _name = 'project.bid'
    _description = "Project Bid"

    def _get_totals_non_material(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        costs_line_obj = self.pool.get('project.bid.total.costs.line')
        for bid in self.browse(cr, uid, ids, context=context):
            vals = []
            items = {}
            for component in bid.components:
                for labor in component.labor:
                    if labor.product_id.id not in items:
                        items[labor.product_id.id] = {
                            'name': labor.product_id.name,
                            'quantity': labor.quantity,
                            'unit_cost': labor.unit_cost,
                        }
                    else:
                        items[labor.product_id.id]['quantity'] \
                            += labor.quantity
            for labor in bid.other_labor:
                if labor.product_id.id not in items:
                    items[labor.product_id.id] = {
                        'name': labor.product_id.name,
                        'quantity': labor.quantity,
                        'unit_cost': labor.unit_cost,
                    }
                else:
                    items[labor.product_id.id]['quantity'] \
                        += labor.quantity
            for val in items.values():
                val['bid_id'] = bid.id
                line_id = costs_line_obj.create(cr, uid, val, context=context)
                vals.append(line_id)
            res[bid.id] = vals
        return res

    def _get_totals(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        costs_line_obj = self.pool.get('project.bid.totals')
        bid_template_obj = self.pool.get('project.bid.template')

        for bid in self.browse(cr, uid, ids, context=context):
            bid_template = bid_template_obj.browse(cr, uid,
                                                   bid.bid_template_id.id,
                                                   context=context)
            vals = []
            # Total materials
            total_material_cost = 0.0
            avg_markup = 0.0
            items = 0
            for component in bid.components:
                items += 1
                total_material_cost += component.component_cost
                avg_markup = (component.markup + avg_markup) / items

            val = {
                'bid_id': bid.id,
                'name': 'Total material cost',
                'cost': total_material_cost,
                'markup': round(avg_markup, 2),
            }
            line_id = costs_line_obj.create(cr, uid, val, context=context)
            vals.append(line_id)

            # Total labor
            total_labor_cost = 0.0
            for labor_totals in bid.totals_non_material:
                total_labor_cost += labor_totals.total_cost
            val = {
                'bid_id': bid.id,
                'name': 'Total labor',
                'cost': total_labor_cost,
                'markup': bid_template.labor_markup,
            }
            line_id = costs_line_obj.create(cr, uid, val, context=context)
            vals.append(line_id)

            # Other expenses
            for expense in bid.other_expenses:
                val = {
                    'bid_id': bid.id,
                    'name': expense.product_id.name,
                    'cost': expense.total_cost,
                    'markup': expense.markup,
                }
                line_id = costs_line_obj.create(cr, uid, val, context=context)
                vals.append(line_id)

            for markup in bid.markup_over_costs:
                val = {
                    'bid_id': bid.id,
                    'name': markup.name,
                    'cost': 0.0,
                    'is_markup_over_costs': True,
                    'markup': markup.markup,
                }
                line_id = costs_line_obj.create(cr, uid, val, context=context)
                vals.append(line_id)
            res[bid.id] = vals
        return res

    def _get_total_cost(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for bid in self.browse(cr, uid, ids, context=context):
            total_cost = 0.0
            for total in bid.totals_all:
                total_cost += total.cost
            res[bid.id] = total_cost
        return res

    def _get_total_sell(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for bid in self.browse(cr, uid, ids, context=context):
            total_sell = 0.0
            for total in bid.totals_all:
                total_sell += total.sell_total
            res[bid.id] = total_sell
        return res

    def _get_gm_percent(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for bid in self.browse(cr, uid, ids, context=context):
            res[bid.id] = 0.0
            if bid.total_cost:
                res[bid.id] = \
                    round(((bid.total_sell - bid.total_cost)
                           / bid.total_cost)*100, 2)
        return res

    _columns = {
        'state': fields.selection(
            [('draft', 'Draft'),
             ('confirm', 'Awaiting approval'),
             ('approve', 'Approved'),
             ('cancel', 'Cancelled')], 'Status',
            select=True, required=True, readonly=True,
            help=' * The \'Draft\' status is used when a user is encoding '
                 'a new bid. '
                 '\n* The \'Confirmed\' status is used to confirm the '
                 'bid by the user.'
                 '\n* The \'Approved\' status is used to approve the '
                 'bid by an authorized user.'
                 '\n* The \'Cancelled\' status is used to cancel '
                 'the bid.'),
        'bid_template_id': fields.many2one('project.bid.template',
                                           'Bid Template', required=True,
                                           ondelete='cascade', select=True,
                                           readonly=True,
                                           states={
                                               'draft': [('readonly', False)]
                                           }),
        'project_id': fields.many2one('project.project',
                                      'Project', required=True,
                                      ondelete='cascade', select=True,
                                      domain=[('type', '<>', 'view')],
                                      readonly=True,
                                      states={
                                          'draft': [('readonly', False)]
                                      }),
        'partner_id': fields.related('project_id', 'partner_id',
                                     type='many2one',
                                     relation='res.partner',
                                     string='Customer',
                                     store=True, readonly=True),
        'user_id': fields.related('project_id', 'user_id', type='many2one',
                                  relation='res.users',
                                  string='Project Manager',
                                  store=True,
                                  readonly=True),
        'name': fields.char('Name', size=256, required=True,
                            readonly=True,
                            states={'draft': [('readonly', False)]}),
        'created_on': fields.date('Creation date'),
        'created_by': fields.many2one('res.users', 'Created by',
                                      required=True,
                                      readonly=True,
                                      states={
                                          'draft': [('readonly', False)]
                                      }),
        'approved_by': fields.many2one('res.users', 'Approved by',
                                       required=False,
                                       readonly=True),
        'approved_on': fields.date('Approval date', readonly=True),
        'due_by': fields.date('Due by', required=False, readonly=True,
                              states={
                                  'draft': [('readonly', False)]
                              }),
        'components': fields.one2many('project.bid.component', 'bid_id',
                                      'Bid Lines',
                                      readonly=True,
                                      states={'draft': [('readonly', False)]}),
        'notes': fields.text('Notes', readonly=True,
                             states={'draft': [('readonly', False)]}),
        'totals_non_material': fields.function(
            _get_totals_non_material, type='one2many',
            obj='project.bid.total.costs.line', string='Non material costs'),
        'totals_all': fields.function(
            _get_totals, type='one2many',
            obj='project.bid.totals', string='Totals'),
        'other_labor': fields.one2many('project.bid.other.labor', 'bid_id',
                                       'Other labor', readonly=True,
                                       states={'draft': [('readonly',
                                                          False)]}),
        'other_expenses': fields.one2many('project.bid.other.expenses',
                                          'bid_id',
                                          'Other expenses', readonly=True,
                                          states={'draft': [('readonly',
                                                             False)]}),
        'markup_over_costs': fields.one2many('project.bid.markup.over.costs',
                                             'bid_id', 'Markup over costs',
                                             readonly=True,
                                             states={'draft': [('readonly',
                                                                False)]}),
        'total_cost': fields.function(_get_total_cost, type='float',
                                      string='Total cost'),
        'total_sell': fields.function(_get_total_sell, type='float',
                                      string='Total revenue'),
        'gm_percent': fields.function(_get_gm_percent, type='float',
                                      string='% Gross Margin'),

    }

    _defaults = {
        'state': 'draft',
        'created_on': lambda *a: time.strftime('%Y-%m-%d'),
        'created_by': lambda obj, cr, uid, ctx=None: uid,
    }

    def action_button_confirm(self, cr, uid, ids, form, context=None):
        if context is None:
            context = {}
        self.write(cr, uid, ids, {'state': 'confirm'}, context=context)
        return True

    def action_button_approve(self, cr, uid, ids, form, context=None):
        if context is None:
            context = {}
        vals = {
            'state': 'approve',
            'approved_on': time.strftime('%Y-%m-%d'),
            'approved_by': uid,
        }
        self.write(cr, uid, ids, vals, context=context)
        return True

    def action_button_draft(self, cr, uid, ids, form, context=None):
        if context is None:
            context = {}
        vals = {
            'state': 'draft',
            'approved_on': False,
            'approved_by': False,
        }
        self.write(cr, uid, ids, vals, context=context)
        return True

    def action_button_cancel(self, cr, uid, ids, form, context=None):
        if context is None:
            context = {}
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)
        return True


class project_bid_component(orm.Model):
    _name = 'project.bid.component'
    _description = "Project Bid Component"

    def _get_default_labor(self, cr, uid, context=None):
        if context is None:
            context = {}
        res = []
        bid_template_obj = self.pool.get('project.bid.template')
        if 'bid_template_id' in context and context['bid_template_id']:
            bid_template = bid_template_obj.browse(
                cr, uid, context['bid_template_id'], context=context)
            for product in bid_template.default_component_labor:
                val = {
                    'product_id': product.id,
                    'quantity': 0.0
                }
                res.append(val)
        return res

    def _get_default_markup(self, cr, uid, context=None):
        if context is None:
            context = {}
        markup = 0.0
        bid_template_obj = self.pool.get('project.bid.template')
        if 'bid_template_id' in context and context['bid_template_id']:
            bid_template = bid_template_obj.browse(
                cr, uid, context['bid_template_id'], context=context)
            markup = bid_template.material_markup
        return markup

    def _get_sale_price(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = record.unit_cost * record.markup
        return res

    def _get_total_line_sell(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = 1
        return res

    def _get_total_material_cost(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = record.quantity*record.unit_cost
        return res

    def _get_component_cost(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            discount_cost = record.quantity*record.discount_cost
            if discount_cost:
                res[record.id] = discount_cost
            else:
                res[record.id] = record.quantity*record.unit_cost
        return res

    def _get_component_sell(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = record.markup*record.component_cost
        return res

    def _get_labor_sell(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            labor_markup = record.bid_id.bid_template_id.labor_markup
            labor_cost = 0.0
            for labor in record.labor:
                labor_cost += labor.total_cost
            res[record.id] = labor_markup*labor_cost
        return res

    def _get_total_sell(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = record.labor_sell + record.component_sell
        return res

    _columns = {
        'bid_id': fields.many2one('project.bid', 'Project Bid',
                                  select=True, required=True,
                                  ondelete='cascade'),
        'product_id': fields.many2one('product.product', 'Material',
                                      required=False),
        'uom_id': fields.related('product_id', 'uom_id', string="UoM",
                                 type='many2one', relation='product.uom',
                                 readonly=True),
        'name': fields.char('Description', size=256, required=True),
        'default_code': fields.char('Part #', help="Material Code"),
        'quantity': fields.float('Quantity'),
        'unit_cost': fields.float(
            'Unit Cost', digits_compute=dp.get_precision('Account')),
        'discount_cost': fields.float(
            'Discount Cost', digits_compute=dp.get_precision('Account')),
        'markup': fields.float('Markup',
                               digits_compute=dp.get_precision('Account')),
        'sale_price': fields.function(
            _get_sale_price, type='float', string='Material unit sale price',
            digits_compute=dp.get_precision('Account')),
        'labor': fields.one2many('project.bid.component.labor',
                                 'bid_component_id',
                                 'Labor'),
        'component_cost': fields.function(
            _get_component_cost, type='float',
            string='Total material cost'),
        'component_sell': fields.function(_get_component_sell, type='float',
                                          string='Material sell price'),
        'labor_sell': fields.function(_get_labor_sell, type='float',
                                      string='Labor sell price'),
        'total_sell': fields.function(_get_total_sell, type='float',
                                      string='Total sell price'),
    }

    _defaults = {
        'labor': _get_default_labor,
        'markup': _get_default_markup,
    }

    def on_change_product_id(self, cr, uid, ids, product_id, context=None):
        values = {}
        if product_id:
            product = self.pool.get('product.product').browse(cr, uid,
                                                              product_id,
                                                              context=context)
            values = {
                'name': product.name,
                'default_code': product.default_code,
                'unit_cost': product.standard_price,
            }
        return {'value': values}


class project_bid_component_labor(orm.Model):
    _name = 'project.bid.component.labor'
    _description = "Project Bid Component Labor"

    def _get_total(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = record.quantity * record.unit_cost
        return res

    _columns = {
        'bid_component_id': fields.many2one('project.bid.component',
                                            'Project Bid Component',
                                            select=True, required=True,
                                            ondelete='cascade'),
        'bid_id': fields.related('bid_component_id', 'bid_id', string="Bid",
                                 type='many2one', relation='project.bid',
                                 readonly=True),
        'product_id': fields.many2one('product.product',
                                      'Labor product', required=True),
        'name': fields.related('product_id', 'name', string="Description",
                               type='char', readonly=True),
        'quantity': fields.float('Quantity'),
        'uom_id': fields.related('product_id', 'uom_id', string="UoM",
                                 type='many2one', relation='product.uom',
                                 readonly=True),
        'unit_cost': fields.related('product_id', 'standard_price',
                                    string='Unit cost', type='float',
                                    store=False, readonly=True),
        'total_cost': fields.function(_get_total, type='float',
                                      string='Total labor cost')
    }


class project_bid_other_labor(orm.Model):
    _name = 'project.bid.other.labor'
    _description = "Project Bid Other Labor"

    def _get_total(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = record.quantity * record.unit_cost
        return res

    def _check_labor_uom(self, cr, uid, ids, context=None):
        for record in self.browse(cr, uid, ids, context=context):
            template = record.bid_id.bid_template_id
            if record.uom_id.id is not template.labor_uom_id.id:
                return False
        return True

    _columns = {
        'bid_id': fields.many2one('project.bid', 'Project Bid',
                                  select=True, required=True,
                                  ondelete='cascade'),
        'product_id': fields.many2one('product.product',
                                      'Labor product', required=True),
        'name': fields.related('product_id', 'name', string="Description",
                               type='char', readonly=True),
        'quantity': fields.float('Quantity'),
        'uom_id': fields.related('product_id', 'uom_id', string="UoM",
                                 type='many2one', relation='product.uom',
                                 readonly=True),
        'unit_cost': fields.related('product_id', 'standard_price',
                                    string='Unit cost',
                                    store=False, readonly=True),
        'total_cost': fields.function(_get_total, type='float', string='Total')
    }

    _constraints = [(_check_labor_uom, 'Error ! The labor must be entered '
                                       'in the default labor unit of measure.',
                     ['uom_id', 'bid_id'])]


class project_bid_other_expenses(orm.Model):
    _name = 'project.bid.other.expenses'
    _description = "Project Bid Other Expenses"

    def _get_total_cost(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = record.quantity*record.unit_cost
        return res

    def _get_total_sell(self, cr, uid, ids, name, args, context=None):
        res = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = record.total_cost*record.markup
        return res

    _columns = {
        'bid_id': fields.many2one('project.bid', 'Project Bid',
                                  select=True, required=True,
                                  ondelete='cascade'),
        'product_id': fields.many2one('product.product',
                                      'Expenses product', required=True),
        'name': fields.related('product_id', 'name', string="Description",
                               type='char', readonly=True),
        'quantity': fields.float('Quantity', required=True),
        'unit_cost': fields.related(
            'product_id', 'standard_price', string='Unit cost',
            store=False, readonly=True,
            digits_compute=dp.get_precision('Account')),
        'uom_id': fields.related('product_id', 'uom_id', string="UoM",
                                 type='many2one', relation='product.uom',
                                 readonly=True),
        'total_cost': fields.function(
            _get_total_cost, type='float', string='Total cost',
            digits_compute=dp.get_precision('Account')),
        'markup': fields.float('Markup', required=True,
                               digits_compute=dp.get_precision('Account')),
        'total_sell': fields.function(_get_total_sell, type='float',
                                      string='Total Sell'),
    }


class project_bid_markup_over_costs(orm.Model):
    _name = 'project.bid.markup.over.costs'
    _description = "Project Bid Markup Over Costs"

    _columns = {
        'bid_id': fields.many2one('project.bid', 'Project Bid',
                                  select=True, required=True,
                                  ondelete='cascade'),
        'name': fields.char('Description', size=256, required=True),
        'markup': fields.float('Markup', required=True,
                               help='Indicate the markup over '
                                    'total costs in %',
                               digits_compute=dp.get_precision('Account')),
    }