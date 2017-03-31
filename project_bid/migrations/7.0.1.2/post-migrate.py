# -*- encoding: utf-8 -*-
import logging
from openerp import SUPERUSER_ID
from openerp.modules.registry import RegistryManager

uid = SUPERUSER_ID

__name__ = 'Get materials into a list'
_logger = logging.getLogger(__name__)


def migrate_bid_component_materials(cr, registry):
    print "\n\n post migration script working, hurrah! \n\n\ "
    cr.execute("""INSERT INTO project_bid_component_material (bid_component_id,
                    product_id, quantity, default_code, unit_cost)
                    SELECT id, product_id, quantity2, default_code, unit_cost
                    FROM project_bid_component
                    WHERE product_id IS NOT null""")


def migrate(cr, version):
    if not version:
        # it is the installation of the module
        return
    registry = RegistryManager.get(cr.dbname)
    migrate_bid_component_materials(cr, registry)
