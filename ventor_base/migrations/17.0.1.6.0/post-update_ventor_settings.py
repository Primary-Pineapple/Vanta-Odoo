from odoo import SUPERUSER_ID, _, api


def migrate(cr, version):

    env = api.Environment(cr, SUPERUSER_ID, {})

    pack_all_items = env.ref("ventor_base.pack_all_items", False)
    if pack_all_items:
        pack_all_items.write(
            {
                "description": "Force to pack all items that have a quantity greater than zero"
            }
        )
