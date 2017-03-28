# -*- encoding: utf-8 -*-
import logging
from openerp import SUPERUSER_ID
from openerp.modules.registry import RegistryManager

uid = SUPERUSER_ID

__name__ = 'Get materials into a list'
_logger = logging.getLogger(__name__)


def migrate_bid_component_quantity(cr, registry):
    cr.execute("""SELECT column_name
            FROM information_schema.columns
            WHERE table_name='project_bid_component' AND
            column_name='quantity2'""")
    if not cr.fetchone():
        cr.execute("""
        ALTER TABLE project_bid_component ADD COLUMN quantity2 float
        """)
        cr.execute("""UPDATE project_bid_component SET quantity2
                        = quantity""")

def migrate(cr, version):
    if not version:
        # it is the installation of the module
        return
    registry = RegistryManager.get(cr.dbname)
    migrate_bid_component_quantity(cr, registry)
