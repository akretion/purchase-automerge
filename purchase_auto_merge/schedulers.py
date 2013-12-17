# -*- encoding: utf-8 -*-
###############################################################################
#                                                                             #
#   purchase_advanced for OpenERP                                             #
#   Copyright (C) 2012 Akretion Sébastien BEAU <sebastien.beau@akretion.com>  #
#                                                                             #
#   This program is free software: you can redistribute it and/or modify      #
#   it under the terms of the GNU Affero General Public License as            #
#   published by the Free Software Foundation, either version 3 of the        #
#   License, or (at your option) any later version.                           #
#                                                                             #
#   This program is distributed in the hope that it will be useful,           #
#   but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the             #
#   GNU Affero General Public License for more details.                       #
#                                                                             #
#   You should have received a copy of the GNU Affero General Public License  #
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.     #
#                                                                             #
###############################################################################

from osv import osv

class procurement_order(osv.osv):
    _inherit = 'procurement.order'

    def _check_existing_locked_purchase(self, cr, uid, op, context=None):
        """Check if a locked purchase order has already been created 
            :param browse_record op: the orderpoint to check
            :rtype: boolean
            :return: True if a purchase exists
        """
        return (op.procurement_id.purchase_line_id 
            and op.procurement_id.purchase_line_id.order_id.lock)

    def _process_one_procurement(self, cr, uid, op, prods, context=None):
        """This method may be overridden to implement custom
            procurement generation. By default OpenERP do not
            update procurement.
        """
        orderpoint_obj = self.pool['stock.warehouse.orderpoint']
        if not context: context={}
        if self._check_existing_locked_purchase(cr, uid, op, context=context):
            qty = self._get_qty_to_procure(cr, uid, op, prods, context=context)
            if qty:
                op = orderpoint_obj.browse(cr, uid, op.id, context=context)
                total_qty = op.procurement_id.product_qty + qty
                ctx = context.copy()
                ctx['update_from_procurement'] = True
                op.procurement_id.write({'product_qty' : total_qty}, context=ctx)
        else:
            super(procurement_order, self)._process_one_procurement(cr, uid, op, prods, context=context)
        return True


