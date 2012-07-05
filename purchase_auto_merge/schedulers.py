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

    def _update_procurement(self, cr, uid, op, context=None):
        """This method may be overridden to implement custom
            procurement generation. By default OpenERP do not
            update procurement.
        """
        if not context: context={}
        qty = self. _get_qty_to_procure(cr, uid, op, context=context)
        if qty:
            total_qty = op.procurement_id.product_qty + qty
            ctx = context.copy()
            ctx['update_from_procurement'] = True
            op.procurement_id.write({'product_qty' : total_qty}, context=ctx)
        return True
