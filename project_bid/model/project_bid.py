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

from openerp import models, fields, api
import time
import openerp.addons.decimal_precision as dp


class project_bid_total_labor(models.TransientModel):
    _name = 'project.bid.total.labor'
    _description = "Project Bid Labor Totals"

    bid_id = fields.Many2one('project.bid', string='Bid',
                                  required=True)
    name = fields.Char('Description', size=256)
    quantity = fields.Float('Hours')
    cogs = fields.Float('COGS')
    overhead = fields.Float('Overhead cost')
    cost = fields.Float('Total cost')
    profit = fields.Float('Profit')
    sell = fields.Float('Revenue')


class project_bid_totals(models.TransientModel):
    _name = 'project.bid.totals'
    _description = "Project Bid Totals"

    bid_id = fields.Many2one('project.bid', string='Bid', required=True)
    name = fields.Char('Description', size=256)
    cogs = fields.Float('COGS')
    overhead = fields.Float('Overhead cost')
    cost = fields.Float('Total cost')
    profit = fields.Float('Profit')
    sell = fields.Float('Revenue')

class project_bid(models.Model):
    _name = 'project.bid'
    _description = "Project Bid"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.multi
    def _get_child_bids(self):
        result = {}
        curr_ids = []
        for curr_id in self:
            result[curr_id.id] = True
            curr_ids.append(curr_id.id)
        # Now add the children
        self.env.cr.execute('''
        WITH RECURSIVE children AS (
        SELECT parent_id, id
        FROM project_bid
        WHERE parent_id IN %s
        UNION ALL
        SELECT a.parent_id, a.id
        FROM project_bid a
        JOIN children b ON(a.parent_id = b.id)
        )
        SELECT * FROM children order by parent_id
        ''', (tuple(curr_ids),))
        res = self.env.cr.fetchall()
        for x, y in res:
            result[y] = True
        return result

    @api.multi
    def get_child_bids(self):
        res = self._get_child_bids()
        return res.keys()

    @api.multi
    def _get_totals_labor(self):
        for bid in self:
            costs_line_obj = self.env['project.bid.total.labor']
            vals = []
            items = {}
            for component in bid.components:
                for labor in component.labor:
                    if labor.product_id.id not in items:
                        items[labor.product_id.id] = {
                            'name': labor.product_id.name,
                            'quantity': labor.quantity,
                            'cogs': labor.cogs,
                            'overhead': labor.overhead,
                            'cost': labor.cost,
                            'profit': labor.profit,
                            'sell': labor.sell,
                        }
                    else:
                        items[labor.product_id.id]['quantity'] \
                            += labor.quantity
                        items[labor.product_id.id]['cogs'] \
                            += labor.cogs
                        items[labor.product_id.id]['overhead'] \
                            += labor.overhead
                        items[labor.product_id.id]['cost'] \
                            += labor.cost
                        items[labor.product_id.id]['profit'] \
                            += labor.profit
                        items[labor.product_id.id]['sell'] \
                            += labor.sell

            for labor in bid.other_labor:
                if labor.product_id.id not in items:
                    items[labor.product_id.id] = {
                        'name': labor.product_id.name,
                        'quantity': labor.quantity,
                        'cogs': labor.cogs,
                        'overhead': labor.overhead,
                        'cost': labor.cost,
                        'profit': labor.profit,
                        'sell': labor.sell,
                    }
                else:
                    items[labor.product_id.id]['quantity'] \
                        += labor.quantity
                    items[labor.product_id.id]['cogs'] \
                        += labor.cogs
                    items[labor.product_id.id]['overhead'] \
                        += labor.overhead
                    items[labor.product_id.id]['cost'] \
                        += labor.cost
                    items[labor.product_id.id]['profit'] \
                        += labor.profit
                    items[labor.product_id.id]['sell'] \
                        += labor.sell
            for val in items.values():
                val['bid_id'] = bid.id
                line_id = costs_line_obj.create(val)
                vals.append(line_id.id)
            bid.totals_non_material = vals

    @api.multi
    def _get_wbs_totals_labor(self):
        bid_ids = []
        costs_line_obj = self.env['project.bid.total.labor']
        for bid in self:
            if bid.id and type(bid.id) == int:
                bid_ids = bid.get_child_bids()
            vals = []
            items = {}
            for bid_2 in self.browse(bid_ids):
                for component in bid_2.components:
                    for labor in component.labor:
                        if labor.product_id.id not in items:
                            items[labor.product_id.id] = {
                                'name': labor.product_id.name,
                                'quantity': labor.quantity,
                                'cogs': labor.cogs,
                                'overhead': labor.overhead,
                                'cost': labor.cost,
                                'profit': labor.profit,
                                'sell': labor.sell,
                            }
                        else:
                            items[labor.product_id.id]['quantity'] \
                                += labor.quantity
                            items[labor.product_id.id]['cogs'] \
                                += labor.cogs
                            items[labor.product_id.id]['overhead'] \
                                += labor.overhead
                            items[labor.product_id.id]['cost'] \
                                += labor.cost
                            items[labor.product_id.id]['profit'] \
                                += labor.profit
                            items[labor.product_id.id]['sell'] \
                                += labor.sell

                for labor in bid_2.other_labor:
                    if labor.product_id.id not in items:
                        items[labor.product_id.id] = {
                            'name': labor.product_id.name,
                            'quantity': labor.quantity,
                            'cogs': labor.cogs,
                            'overhead': labor.overhead,
                            'cost': labor.cost,
                            'profit': labor.profit,
                            'sell': labor.sell,
                        }
                    else:
                        items[labor.product_id.id]['quantity'] \
                            += labor.quantity
                        items[labor.product_id.id]['cogs'] \
                            += labor.cogs
                        items[labor.product_id.id]['overhead'] \
                            += labor.overhead
                        items[labor.product_id.id]['cost'] \
                            += labor.cost
                        items[labor.product_id.id]['profit'] \
                            += labor.profit
                        items[labor.product_id.id]['sell'] \
                            += labor.sell
            for val in items.values():
                val['bid_id'] = bid.id
                line_id = costs_line_obj.create(val)
                vals.append(line_id.id)
            bid.totals_non_material = vals

    @api.multi
    def _get_totals_all(self):
        if self.ids:
            for bid in self:
                vals=[]
                items = {}
                material_cogs = 0.0
                material_overhead = 0.0
                material_cost = 0.0
                material_profit = 0.0
                material_sell = 0.0
                # Total labor
                labor_cogs = 0.0
                labor_overhead = 0.0
                labor_cost = 0.0
                labor_profit = 0.0
                labor_sell = 0.0
                costs_line_obj = self.env["project.bid.totals"]
                for component in bid.components:
                    material_cogs += component.material_cogs
                    material_overhead += component.material_overhead
                    material_cost += component.material_cost
                    material_profit += component.material_profit
                    material_sell += component.material_sell

                for labor in bid.totals_non_material:
                    labor_cogs += labor.cogs
                    labor_overhead += labor.overhead
                    labor_cost += labor.cost
                    labor_profit += labor.profit
                    labor_sell += labor.sell

                # Other expenses
                for expense in bid.other_expenses:
                    if expense.product_id.id not in items:
                        items[expense.product_id.id] = {
                            'name': expense.product_id.name,
                            'quantity': expense.quantity,
                            'cogs': expense.cogs,
                            'overhead': expense.overhead,
                            'cost': expense.cost,
                            'profit': expense.profit,
                            'sell': expense.sell
                        }
                    else:
                        items[expense.product_id.id]['quantity'] \
                            += expense.quantity
                        items[expense.product_id.id]['cogs'] \
                            += expense.cogs
                        items[expense.product_id.id]['overhead'] \
                            += expense.overhead
                        items[expense.product_id.id]['cost'] \
                            += expense.cost
                        items[expense.product_id.id]['profit'] \
                            += expense.profit
                        items[expense.product_id.id]['sell'] \
                            += expense.sell

                val = {
                    'bid_id': bid.id,
                    'name': 'Total material',
                    'cogs': material_cogs,
                    'overhead': material_overhead,
                    'cost': material_cost,
                    'profit': material_profit,
                    'sell': material_sell,
                }
                line_id = costs_line_obj.create(val)
                vals.append(line_id.id)

                val = {
                    'bid_id': bid.id,
                    'name': 'Total labor',
                    'cogs': labor_cogs,
                    'overhead': labor_overhead,
                    'cost': labor_cost,
                    'profit': labor_profit,
                    'sell': labor_sell,
                    }
                line_id = costs_line_obj.create(val)
                vals.append(line_id.id)
                self.env['project.bid.totals'].create(val)
                for val in items.values():
                    val['bid_id'] = bid.id
                    line_id = costs_line_obj.create(val)
                    vals.append(line_id.id)

                bid.totals_all = vals

    @api.multi
    def _get_wbs_totals_all(self):
        costs_line_obj = self.env['project.bid.totals']
        bid_ids = []
        if self.ids:
            for bid in self:
                vals = []
                if bid.id and type(bid.id) == int:
                    bid_ids = bid.get_child_bids()
                items = {}
                material_cogs = 0.0
                material_overhead = 0.0
                material_cost = 0.0
                material_profit = 0.0
                material_sell = 0.0
                # Total labor
                labor_cogs = 0.0
                labor_overhead = 0.0
                labor_cost = 0.0
                labor_profit = 0.0
                labor_sell = 0.0
                for bid_2 in self.browse(bid_ids):
                    for component in bid_2.components:
                        material_cogs += component.material_cogs
                        material_overhead += component.material_overhead
                        material_cost += component.material_cost
                        material_profit += component.material_profit
                        material_sell += component.material_sell

                    for labor in bid_2.totals_non_material:
                        labor_cogs += labor.cogs
                        labor_overhead += labor.overhead
                        labor_cost += labor.cost
                        labor_profit += labor.profit
                        labor_sell += labor.sell

                    # Other expenses
                    for expense in bid_2.other_expenses:
                        if expense.product_id.id not in items:
                            items[expense.product_id.id] = {
                                'name': expense.product_id.name,
                                'quantity': expense.quantity,
                                'cogs': expense.cogs,
                                'overhead': expense.overhead,
                                'cost': expense.cost,
                                'profit': expense.profit,
                                'sell': expense.sell
                            }
                        else:
                            items[expense.product_id.id]['quantity'] \
                                += expense.quantity
                            items[expense.product_id.id]['cogs'] \
                                += expense.cogs
                            items[expense.product_id.id]['overhead'] \
                                += expense.overhead
                            items[expense.product_id.id]['cost'] \
                                += expense.cost
                            items[expense.product_id.id]['profit'] \
                                += expense.profit
                            items[expense.product_id.id]['sell'] \
                                += expense.sell
                val = {
                    'bid_id': bid.id,
                    'name': 'Total material',
                    'cogs': material_cogs,
                    'overhead': material_overhead,
                    'cost': material_cost,
                    'profit': material_profit,
                    'sell': material_sell,
                }
                line_id = costs_line_obj.create(val)
                vals.append(line_id.id)
                val = {
                    'bid_id': bid.id,
                    'name': 'Total labor',
                    'cogs': labor_cogs,
                    'overhead': labor_overhead,
                    'cost': labor_cost,
                    'profit': labor_profit,
                    'sell': labor_sell,
                    }
                line_id = costs_line_obj.create(val)
                vals.append(line_id.id)
                for val in items.values():
                    val['bid_id'] = bid.id
                    line_id = costs_line_obj.create(val)
                    vals.append(line_id.id)

                bid.wbs_totals_all = vals


    @api.multi
    def _get_totals(self):
        for bid in self:
            total_cogs = 0.0
            total_overhead = 0.0
            total_cost = 0.0
            total_profit = 0.0
            total_sell = 0.0
            for total in bid.totals_all:
                total_cogs += total.cogs
                total_overhead += total.overhead
                total_cost += total.cost
                total_profit += total.profit
                total_sell += total.sell

            # Gross profit and gross margin
            total_gp = total_sell - total_cogs
            try:
                total_gm_percent = round((total_gp/total_sell)*100, 2)
            except ZeroDivisionError:
                total_gm_percent = 0.0

            # Profit Margin
            total_npm = total_sell - total_cost
            try:
                total_npm_percent = round((total_npm/total_sell)*100, 2)
            except ZeroDivisionError:
                total_npm_percent = 0.0

            bid.total_income = total_sell
            bid.total_cogs = total_cogs
            bid.total_gm_percent = total_gm_percent
            bid.total_gp = total_gp
            bid.total_overhead = total_overhead
            bid.total_npm = total_npm
            bid.total_npm_percent = total_npm_percent

    @api.multi
    def _get_wbs_totals(self):
        bid_ids = []
        for bid in self:
            if bid.id and type(bid.id) == int:
                bid_ids = bid.get_child_bids()
            total_cogs = 0.0
            total_overhead = 0.0
            total_cost = 0.0
            total_profit = 0.0
            total_sell = 0.0
            for bid2 in self.browse(bid_ids):
                for total in bid2.totals_all:
                    total_cogs += total.cogs
                    total_overhead += total.overhead
                    total_cost += total.cost
                    total_profit += total.profit
                    total_sell += total.sell

            # Gross profit and gross margin
            total_gp = total_sell - total_cogs
            try:
                total_gm_percent = round((total_gp/total_sell)*100, 2)
            except ZeroDivisionError:
                total_gm_percent = 0.0

            # Profit Margin
            total_npm = total_sell - total_cost
            try:
                total_npm_percent = round((total_npm/total_sell)*100, 2)
            except ZeroDivisionError:
                total_npm_percent = 0.0

            bid.wbs_total_income = total_sell
            bid.wbs_total_cogs = total_cogs
            bid.wbs_total_gm_percent= total_gm_percent
            bid.wbs_total_gp= total_gp
            bid.wbs_total_overhead= total_overhead
            bid.wbs_total_npm= total_npm
            bid.wbs_total_npm_percent= total_npm_percent

    @api.multi
    def _get_gm_percent(self):
        res = {}
        for bid in self:
            gm_percent = 0.0
            if bid.total_cost:
                try:
                    gm_percent = \
                        round(((bid.total_sell - bid.total_cost)
                               / bid.total_cost)*100, 2)
                except ZeroDivisionError:
                    gm_percent = 0.0
            bid.gm_percent = gm_percent

    @api.multi
    def _complete_bid_hierarchy_code_calc(self):
        res = []
        for bid in self:
            data = []
            b = bid
            while b:
                if b.code:
                    data.insert(0, b.code)
                else:
                    data.insert(0, '')

                b = b.parent_id
            data = ' / '.join(data)
            data = '[' + data + '] '

            res.append((bid.id, data))
            bid.complete_code = data

    @api.model
    def _get_current_user(self):
        return self.env.uid

    _track = {
        'state': {
            'project_bid.mt_bid_confirmed':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'confirm',
            'project_bid.mt_bid_approved':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'approve',
            'project_bid.mt_bid_draft':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'draft',
            'project_bid.mt_bid_cancel':
                lambda self, cr, uid, obj, ctx=None: obj['state'] == 'cancel',
        },
    }

    state = fields.Selection(
            [('draft', 'Draft'),
             ('confirm', 'Awaiting approval'),
             ('approve', 'Approved'),
             ('cancel', 'Cancelled')], 'Status',
            select=True, required=True, readonly=True,
            default = 'draft',
            help=' * The \'Draft\' status is used when a user is encoding '
                 'a new bid. '
                 '\n* The \'Confirmed\' status is used to confirm the '
                 'bid by the user.'
                 '\n* The \'Approved\' status is used to approve the '
                 'bid by an authorized user.'
                 '\n* The \'Cancelled\' status is used to cancel '
                 'the bid.')
    bid_template_id = fields.Many2one('project.bid.template',
                                           'Bid Template', required=True,
                                           ondelete='cascade', select=True,
                                           readonly=True,
                                           states={
                                               'draft': [('readonly', False)]
                                           })
    parent_id = fields.Many2one('project.bid', 'Parent Bid',
                                     required=False, ondelete='set null',
                                     readonly=True,
                                     states={
                                         'draft': [('readonly', False)]
                                     })
    partner_id = fields.Many2one('res.partner',
                                      'Customer', required=True, readonly=True,
                                      states={
                                          'draft': [('readonly', False)]
                                      })
    code = fields.Char('Reference', select=True, required=True)
    complete_code = fields.Char(
            compute= '_complete_bid_hierarchy_code_calc',
            string='Complete Reference',
            help='Describes the full path of this '
                 'bid hierarchy.',
            store=True)
    name = fields.Char('Name', size=256, required=True,
                            readonly=True,
                            states={'draft': [('readonly', False)]})
    created_on = fields.Date('Creation date',
                             default = fields.Date.context_today)
    created_by = fields.Many2one('res.users', 'Created by',
                                      required=True,
                                      readonly=True,
                                      default = _get_current_user,
                                      states={
                                          'draft': [('readonly', False)]
                                      })
    approved_by = fields.Many2one('res.users', 'Approved by',
                                       required=False,
                                       readonly=True)
    approved_on = fields.Date('Approval date', readonly=True)
    due_by = fields.Date('Due by', required=False, readonly=True,
                              states={
                                  'draft': [('readonly', False)]
                              })
    components = fields.One2many('project.bid.component', 'bid_id',
                                      'Bid Lines',
                                      readonly=True,
                                      states={'draft': [('readonly', False)]})
    notes = fields.Text('Notes', readonly=True,
                             states={'draft': [('readonly', False)]})
    totals_non_material = fields.One2many(
            compute='_get_totals_labor',
            comodel_name='project.bid.total.labor',
            string='Non material costs')
    totals_all = fields.One2many(
            compute='_get_totals_all', string='Totals',
            comodel_name='project.bid.totals')

    wbs_totals_non_material = fields.One2many(
            compute='_get_wbs_totals_labor',
            comodel_name='project.bid.total.labor',
            string='WBS Non material costs')
    wbs_totals_all = fields.One2many(
            comodel_name='project.bid.totals',
            compute='_get_wbs_totals_all',
            string='WBS Totals')
    other_labor = fields.One2many('project.bid.other.labor', 'bid_id',
                                'Other labor', readonly=True,
                                states={'draft': [('readonly',
                                False)]})
    other_expenses = fields.One2many('project.bid.other.expenses',
                                    'bid_id',
                                    'Other expenses', readonly=True,
                                    states={'draft': [('readonly',
                                    False)]})
    total_income = fields.Float(compute='_get_totals',
                                        multi='totals', string='Revenue')
    total_cogs = fields.Float(compute='_get_totals',
                                      multi='totals', string='Cost of Sales')
    total_gm_percent = fields.Float(compute='_get_totals',
                                            multi='totals',
                                            string='Gross Margin (%)')
    total_gp =  fields.Float(compute='_get_totals',
                                    multi='totals', string='Gross Profit')
    total_overhead = fields.Float(compute='_get_totals',
                                          multi='totals',
                                          string='Total Overhead')
    total_npm = fields.Float(compute='_get_totals',
                                     multi='totals',
                                     string='Net Profit Margin')
    total_npm_percent = fields.Float(compute='_get_totals',
                                             multi='totals',
                                             string='Net Profit Margin (%)')
    wbs_total_income = fields.Float(compute='_get_wbs_totals',
                                            multi='wbs_totals',
                                            string='WBS Total Revenue')
    wbs_total_cogs = fields.Float(compute='_get_totals',
                                    multi='wbs_totals',
                                    string='WBS Cost of sales')
    wbs_total_gm_percent= fields.Float(compute='_get_wbs_totals',
                                    multi='wbs_totals',
                                    string='WBS Gross Margin (%)')
    wbs_total_gp= fields.Float(compute='_get_wbs_totals',
                                    multi='wbs_totals',
                                    string='WBS Gross Profit')
    wbs_total_overhead= fields.Float(compute='_get_wbs_totals',
                                    multi='wbs_totals',
                                    string='WBS Total Overhead')
    wbs_total_npm= fields.Float(compute='_get_wbs_totals',
                                    multi='wbs_totals',
                                    string='WBS Net profit Margin')
    wbs_total_npm_percent= fields.Float(compute='_get_wbs_totals',
                                    multi='wbs_totals',
                                    string='WBS Net Profit Margin %')
    overhead_rate = fields.Float(
            'Default Overhead %', digits=dp.get_precision('Account'))
    profit_rate = fields.Float(
            'Default Profit (%) over COGS', digits=dp.get_precision(
                'Account'),
            help="Profit % over COGS")

    _order = 'complete_code'

    @api.onchange('bid_template_id')
    def on_change_bid_template_id(self):
        if self.bid_template_id:
            self.bid_template_id.overhead_rate = self.bid_template_id.overhead_rate
            self.bid_template_id.profit_rate = self.bid_template_id.profit_rate

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        bid = self.browse(cr, uid, id, context=context)
        default.update({
            'state': 'draft',
            'name': ("%s (copy)") % (bid.name or ''),
        })

        return super(project_bid, self).copy(cr, uid, id, default,
                                             context=context)

    @api.multi
    def copy(self, default = None):
        self.ensure_one()
        if default is None:
            default = {}
        default.update({
            'state': 'draft',
            'name': ("%s (copy)") % (self.name or ''),
        })
        return super(project_bid, self).copy(default)

    @api.multi
    def action_button_confirm(self):
        self.ensure_one()
        self.write({'state': 'confirm'})
        return True

    @api.multi
    def action_button_approve(self):
        self.ensure_one()
        vals = {
            'state': 'approve',
            'approved_on': time.strftime('%Y-%m-%d'),
            'approved_by': self.env.uid,
        }
        self.write(vals)
        return True

    @api.multi
    def action_button_draft(self):
        self.ensure_one()
        vals = {
            'state': 'draft',
            'approved_on': False,
            'approved_by': False,
        }
        self.write(vals)
        return True

    @api.multi
    def action_button_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancel'})
        return True

    @api.multi
    def code_get(self):
        if len(self) < 1:
            return []
        res = []
        for item in self:
            data = []
            bid = item
            while bid:
                if bid.code:
                    data.insert(0, bid.code)
                else:
                    data.insert(0, '')
                bid = bid.parent_id
            data = ' / '.join(data)
            res.append((item.id, data))
        return res

    @api.multi
    def name_get(self):
        ids = self
        if type(self) is int:
            ids = [self]
        new_list = []
        for i in ids:
            if i not in new_list:
                new_list.append(i)
        ids = new_list

        res = []
        for item in ids:
            data = []
            bid = item
            while bid:
                if bid.name:
                    data.insert(0, bid.name)
                else:
                    data.insert(0, '')
                bid = bid.parent_id
            data = ' / '.join(data)
            res2 = item.code_get()
            if res2:
                data = '[' + res2[0][1] + '] ' + data

            res.append((item.id, data))
        return res


class project_bid_component(models.Model):
    _name = 'project.bid.component'
    _description = "Project Bid Component"

    @api.multi
    def _get_totals(self):
        for record in self:
            labor_cogs = 0.0
            labor_overhead = 0.0
            labor_cost = 0.0
            labor_profit = 0.0
            labor_sell = 0.0

            material_cogs = 0.0
            material_overhead = 0.0
            material_cost = 0.0
            material_profit = 0.0
            material_sell = 0.0
            quantity = 0.0

            for labor in record.labor:
                labor_cogs += labor.cogs
                labor_overhead += labor.overhead
                labor_cost += labor.cost
                labor_profit += labor.profit
                labor_sell += labor.sell

            for material in record.material_ids:
                material_cogs += material.cogs
                material_overhead += material.overhead
                material_cost += material.cost
                material_profit += material.profit
                material_sell += material.sell
                quantity += material.quantity

            total_cogs = material_cogs + labor_cogs
            total_overhead = material_overhead + labor_overhead
            total_cost = labor_cost + material_cost
            total_profit = material_profit + labor_profit
            total_sell = total_cogs + total_overhead + total_profit
            gross_profit = total_sell - total_cogs

            record.quantity = quantity
            record.material_cogs = material_cogs
            record.material_overhead = material_overhead
            record.material_cost = material_cost
            record.material_profit = material_profit
            record.material_sell = material_sell
            record.labor_cogs = labor_cogs
            record.labor_overhead = labor_overhead
            record.labor_cost = labor_cost
            record.labor_profit = labor_profit
            record.labor_sell = labor_sell
            record.total_cogs = total_cogs
            record.total_overhead = total_overhead
            record.total_cost = total_cost
            record.total_profit = total_profit
            record.total_sell = total_sell
            record.gross_profit = gross_profit

    @api.model
    def _default_labor(self):
        res = []
        bid_template_obj = self.env['project.bid.template']
        bid_template_id = self.env.context.get('bid_template_id')
        if bid_template_id:
            bid_template = bid_template_obj.browse([bid_template_id])
            for product in bid_template.default_component_labor:
                val = {
                    'product_id': product.id,
                    'quantity': 0.0
                }
                res.append(val)

            bid_template.labor=res

    @api.model
    def _default_profit_rate(self):
        return self.env.context.get('profit_rate') or 0.0

    @api.model
    def _default_overhead_rate(self):
        return self.env.context.get('overhead_rate') or 0.0

    @api.model
    def _default_bid_id(self):
        return self.env.context.get('bid_id') or 0.0

    bid_id = fields.Many2one('project.bid', 'Project Bid',
                              select=True, required=True,
                              ondelete='cascade',
                             default=_default_bid_id)
    bid_template_id = fields.Many2one(related='bid_id.bid_template_id',
                                      string="Bid Template",
                                      readonly=True)
    labor = fields.One2many('project.bid.component.labor',
                             'bid_component_id', 'Labor',
                            default=_default_labor)
    bid_component_template_id = fields.Many2one('project.bid.component',
                                                 'Project Bid Component Template',
                                                 required=False,
                                                 ondelete='set null')
    material_ids = fields.One2many('project.bid.component.material',
                                    'bid_component_id',
                                    'Materials')
    name = fields.Char('Description', size=256, required=True)
    quantity = fields.Float('Quantity', compute="_get_totals",multi='totals')
    overhead_rate = fields.Float(
        'Overhead %', digits=dp.get_precision('Account'),
        default =_default_overhead_rate)
    profit_rate = fields.Float(
        'Profit (%) over COGS', digits=dp.get_precision('Account'),
        help="Profit % over COGS",
        default = _default_profit_rate)
    material_cogs = fields.Float(
        compute=_get_totals, string='Material COGS',
        multi='totals')
    material_overhead = fields.Float(
        compute='_get_totals',string='Material overhead',
        multi='totals')
    material_cost = fields.Float(
        compute='_get_totals', string='Material cost',
        multi='totals')
    material_profit = fields.Float(
        compute='_get_totals', string='Material profit',
        multi='totals')
    material_sell = fields.Float(
        compute='_get_totals', string='Material sell',
        multi='totals')
    labor_cogs = fields.Float(
        compute='_get_totals',string='Labor COGS',
        multi='totals')
    labor_overhead = fields.Float(
        compute='_get_totals', type='float', string='Labor overhead',
        multi='totals')
    labor_cost = fields.Float(
        compute='_get_totals', type='float', string='Labor cost',
        multi='totals')
    labor_profit = fields.Float(
        compute = '_get_totals', type='float', string='Labor profit',
        multi='totals')
    labor_sell = fields.Float(
        compute='_get_totals', string='Labor profit',
        multi='totals')
    total_cogs = fields.Float(
        compute = '_get_totals', string='Total COGS',
        multi='totals')
    gross_profit = fields.Float(
        compute = '_get_totals', string='Gross profit',
        multi='totals')
    total_overhead = fields.Float(
        compute = '_get_totals', string='Total overhead',
        multi='totals')
    total_cost = fields.Float(
        compute = '_get_totals', string='Total cost',
        multi='totals')
    total_profit = fields.Float(
        compute = '_get_totals', string='Net profit',
        multi='totals')
    total_sell = fields.Float(
        copute = '_get_totals', string='Revenue',
        multi='totals')

    @api.multi
    def _check_overhead(self):
        for record in self:
            if record.overhead_rate < 0.0:
                return False
        return True

    _constraints = [(_check_overhead, 'Error ! The overhead % must be > 0. ',
                     ['overhead'])]

    @api.multi
    @api.onchange('bid_template_id')
    def on_change_bid_template_id(self):
        if self.bid_component_template_id:
            bid_component_template = self.bid_component_template_id
            on_write = False
            if self.id:
                bid_component = self
                on_write = True

            material_list = []
            labor_list = []
            if on_write:
                for material in bid_component.material_ids:
                    material_list.append((2, material.id, 0))

            for material in bid_component_template.material_ids:
                materialdicc = {
                    'bid_component_id': bid_component.id if on_write else None,
                    'name': material.name,
                    'quantity': material.quantity,
                    'product_id': material.product_id.id,
                    'default_code': material.default_code,
                    'uom_id': material.uom_id.id,
                    'bid_id': material.bid_id.id,
                    'unit_cost': material.unit_cost,
                    'cogs': material.cogs,
                    'overhead': material.overhead,
                    'cost': material.cost,
                    'profit': material.profit,
                    'sell': material.sell,
                }
                material_list.append((0, 0, materialdicc))

            if on_write:
                for labor in bid_component.labor:
                    labor_list.append((2, labor.id, 0))

            for labor in bid_component_template.labor:
                labordicc = {
                    'bid_component_id': bid_component.id if on_write else None,
                    'name': labor.name,
                    'quantity': labor.quantity,
                    'product_id': labor.product_id.id,
                    'uom_id': labor.uom_id.id,
                    'bid_id': labor.bid_id.id,
                    'unit_cost': labor.unit_cost,
                    'cogs': labor.cogs,
                    'overhead': labor.overhead,
                    'cost': labor.cost,
                    'profit': labor.profit,
                    'sell': labor.sell,
                }
                labor_list.append((0, 0, labordicc))

            bid_component.name = bid_component_template.name
            bid_component.material_ids = material_list
            bid_component.labor = labor_list
            bid_component.bid_component_template_id = False


class project_bid_component_material(models.Model):
    _name = 'project.bid.component.material'
    _description = "Project Bid Component Material"

    @api.multi
    def _get_totals(self):
        for record in self:
            total_cogs = record.quantity * record.unit_cost
            total_overhead = \
                record.bid_component_id.overhead_rate/100*total_cogs
            total_cost = total_cogs + total_overhead
            total_gross_profit = \
                record.bid_component_id.profit_rate/100*total_cogs
            total_sell = total_cost + total_gross_profit

            record.cogs = total_cogs
            record.overhead = total_overhead
            record.cost = total_cost
            record.profit = total_gross_profit
            record.sell = total_sell

    @api.onchange('product_id')
    def on_change_product_id(self):
        material = self
        material.name = material.product_id.name
        material.default_code = material.product_id.default_code
        material.unit_cost = material.product_id.standard_price

    bid_component_id = fields.Many2one('project.bid.component',
                                            'Project Bid Component',
                                            select=True, required=True,
                                            ondelete='cascade')
    bid_id = fields.Many2one(comodel_name = 'project.bid',
                             realted = 'bid_component_id.bid_id', string="Bid",
                             readonly=True)
    product_id = fields.Many2one('product.product','Material product')
    name = fields.Char(related='product_id.name', string="Description",
                       readonly=True)
    quantity =  fields.Float('Quantity')
    default_code = fields.Char('Part #', help="Material Code")
    uom_id = fields.Many2one(comodel_name='product.uom',
                             related='product_id.uom_id', string="UoM",
                             readonly=True)
    unit_cost = fields.Float('unit_cost', required=True)
    cogs = fields.Float(compute = '_get_totals', multi='totals',
                                string='Total labor COGS')
    overhead = fields.Float(compute='_get_totals', multi='totals',
                        string='Total overhead')
    cost = fields.Float(compute='_get_totals', multi='totals',
                        string='Total costs')
    profit = fields.Float(compute='_get_totals', multi='totals',
                        string='Net profit')
    sell = fields.Float(compute='_get_totals', multi='totals',
                        string='Revene')


class project_bid_component_labor(models.Model):
    _name = 'project.bid.component.labor'
    _description = "Project Bid Component Labor"

    @api.multi
    def _get_totals(self):
        for record in self:
            total_cogs = record.quantity * record.unit_cost
            total_overhead = \
                record.bid_component_id.overhead_rate/100*total_cogs
            total_cost = total_cogs + total_overhead
            total_gross_profit = \
                record.bid_component_id.profit_rate/100*total_cogs
            total_sell = total_cost + total_gross_profit

            record.cogs = total_cogs
            record.overhead = total_overhead
            record.cost = total_cost
            record.profit = total_gross_profit
            record.sell = total_sell

    bid_component_id = fields.Many2one('project.bid.component',
                                        'Project Bid Component',
                                        select=True, required=True,
                                        ondelete='cascade')
    bid_id = fields.Many2one(related='bid_component_id.bid_id',
                             string="Bid",
                             readonly=True)
    product_id = fields.Many2one('product.product',
                                  'Labor product', required=True)
    name = fields.Char(related ='product_id.name',
                            string="Description",
                            readonly=True)
    quantity = fields.Float('Quantity')
    uom_id = fields.Many2one(related='product_id.uom_id', string="UoM",
                             readonly=True)
    unit_cost = fields.Float(related='product_id.standard_price',
                                string='Unit cost',
                                store=False, readonly=True)
    cogs = fields.Float(compute= '_get_totals', type='float',
                            multi='totals',
                            string='Total labor COGS')
    overhead = fields.Float(compute='_get_totals',
                                multi='totals', string='Total overhead')
    cost = fields.Float(compute='_get_totals',
                            multi='totals', string='Total costs')
    profit = fields.Float(compute = '_get_totals',
                              multi='totals', string='Net profit')
    sell = fields.Float(compute='_get_totals',
                            multi='totals', string='Revenue')


class project_bid_other_labor(models.Model):
    _name = 'project.bid.other.labor'
    _description = "Project Bid Other Labor"

    @api.multi
    def _get_totals(self):
        for record in self:
            cogs = record.quantity * record.unit_cost
            overhead = cogs*record.overhead_rate/100
            cost = cogs+overhead
            profit = cogs*record.profit_rate/100
            sell = cost + profit
            gross_profit = sell - cogs

            record.cogs = cogs
            record.overhead = overhead
            record.cost = cost
            record.profit = profit
            record.sell = sell
            record.gross_profit = gross_profit

    @api.model
    def _default_profit_rate(self):
        return self.env.context.get('profit_rate') or 0.0

    @api.model
    def _default_overhead_rate(self):
        return self.env.context.get('overhead_rate') or 0.0

    @api.multi
    def _check_labor_uom(self):
        for record in self:
            template = record.bid_id.bid_template_id
            if record.uom_id.id is not template.labor_uom_id.id:
                return False
        return True

    bid_id = fields.Many2one('project.bid', 'Project Bid',
                              select=True, required=True,
                              ondelete='cascade')
    product_id = fields.Many2one('product.product',
                                  'Labor product', required=True)
    name = fields.Char(related= 'product_id.name',
                       string="Description",
                       readonly=True)
    quantity = fields.Float('Quantity')
    uom_id = fields.Many2one(related='product_id.uom_id', string="UoM",
                             readonly=True)
    unit_cost = fields.Float(related ='product_id.standard_price',
                                string='Unit cost',
                                store=False, readonly=True)
    overhead_rate = fields.Float(
        'Overhead %', digits=dp.get_precision('Account'),
        default=_default_overhead_rate)
    profit_rate = fields.Float(
        'Profit (%) over COGS', digits=dp.get_precision('Account'),
        help="Profit (%) over COGS",
        default=_default_profit_rate)
    cogs = fields.Float(compute= '_get_totals', multi='totals',
                            string='Total COGS')
    overhead = fields.Float(compute='_get_totals',
                                multi='totals',
                                string='Total overhead')
    cost = fields.Float(compute='_get_totals', type='float',
                            multi='totals', string='Total cost')
    gross_profit = fields.Float(compute='_get_totals',
                                    multi='totals',
                                    string='Gross profit')
    profit = fields.Float(compute='_get_totals',
                              multi='totals',
                              string='Net profit')
    sell = fields.Float(compute='_get_totals',
                            multi='totals', string='Revenue')

    _constraints = [(_check_labor_uom, 'Error ! The labor must be entered '
                                       'in the default labor unit of measure.',
                     ['uom_id', 'bid_id'])]


class project_bid_other_expenses(models.Model):
    _name = 'project.bid.other.expenses'
    _description = "Project Bid Other Expenses"

    @api.multi
    def _get_totals(self):
        for record in self:
            cogs = record.quantity*record.unit_cost
            overhead = cogs * record.overhead_rate/100
            cost = cogs + overhead
            profit = cogs*record.profit_rate/100
            sell = cost + profit
            gross_profit = sell - cogs
            record.cogs = cogs
            record.overhead = overhead
            record.cost = cost
            record.profit = profit
            record.sell = sell
            record.gross_profit = gross_profit

    @api.model
    def _default_profit_rate(self):
        return self.env.context.get('profit_rate') or 0.0

    @api.model
    def _default_overhead_rate(self):
        return self.env.context.get('overhead_rate') or 0.0

    bid_id = fields.Many2one('project.bid', 'Project Bid',
                              select=True, required=True,
                              ondelete='cascade')
    product_id = fields.Many2one('product.product',
                                  'Expenses product', required=True)
    name = fields.Char(related='product_id.name', string="Description",
                           readonly=True)
    quantity = fields.Float('Quantity', required=True)
    unit_cost = fields.Float(
        related = 'product_id.standard_price', string='Unit cost',
        store=False, readonly=True,
        digits=dp.get_precision('Account'))
    uom_id = fields.Many2one(related = 'product_id.uom_id', string="UoM",
                             readonly=True)
    overhead_rate = fields.Float(
        'Overhead %', required=True,
        digits=dp.get_precision('Account'),
        default = _default_overhead_rate)
    profit_rate = fields.Float(
        'Profit (%) over COGS', required=True,
        digits=dp.get_precision('Account'),
        help="Profit % over COGS",
        default = _default_profit_rate)
    cogs = fields.Float(
        compute='_get_totals', multi='totals',
        string='Total COGS')
    overhead = fields.Float(
        compute ='_get_totals', multi='totals',
        string='Total overhead cost')
    cost = fields.Float(
        compute = '_get_totals', multi='totals',
        string='Total cost')
    gross_profit = fields.Float(compute = '_get_totals',
                                    multi='totals',
                                    string='Gross profit')
    profit = fields.Float(
        compute='_get_totals', multi='totals',
        string='Net profit')
    sell = fields.Float(
        compute='_get_totals', multi='totals',
        string='Revenue')
