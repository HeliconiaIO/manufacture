# Copyright 2014 Serv. Tec. Avanzados - Pedro M. Baeza
# Copyright 2018 Simone Rubino - Agile Business Group
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from . import models


def post_init_hook(env):
    # Create QC triggers
    picking_type_ids = env["stock.picking.type"].sudo().search([])
    for picking_type_id in picking_type_ids:
        picking_type_id.sudo()._create_qc_trigger()
