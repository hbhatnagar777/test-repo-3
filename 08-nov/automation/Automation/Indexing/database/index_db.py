# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main module to get the index DB object of the backupset or subclient"""

from cvpysdk.backupset import Backupset
from cvpysdk.subclient import Subclient

from AutomationUtils import logger
from AutomationUtils.database_helper import get_csdb

from .ctree import CTreeDB
from Indexing.misc import MetallicConfig


def get(entity_obj):
    """Gets the Index DB object for the given entity

        Args:
            entity_obj     (obj)   --      The backupset/subclient CvPySDK object for which
            Index DB is required.

        Returns:
            (obj)       -       CTreeDB object, if the entity's DB is using ctree engine

        Raises:
             Exception  -       If the entity's DB engine is not CTree

         Usage:
            >>> from Indexing.database import index_db
            >>> idx_db = index_db.get('<backupset/subclient_pysdk_object>')
            >>> idx_db.compact_db()
            >>> idx_db.delete_db()

    """

    log = logger.get_log()
    commcell = entity_obj._commcell_object

    cs_db = get_csdb()

    metallic = MetallicConfig(commcell)
    if metallic.is_configured:
        cs_db = metallic.csdb

    if isinstance(entity_obj, Backupset):
        backupset_obj = entity_obj
        subclient_id = ''

    elif isinstance(entity_obj, Subclient):
        backupset_obj = entity_obj._backupset_object
        subclient_id = entity_obj.subclient_id

    else:
        raise Exception('Please provide backupset/subclient object to get Index DB')

    backupset_id = backupset_obj.backupset_id

    # If subclient ID is provided, then return the index DB at subclient level
    # else return the index DB at backupset level

    log.info('Getting Index DB object for the entity backupset [{0}] subclient [{1}]'.format(
        backupset_id, subclient_id))

    cs_db.execute("""
        select
            top 1
            backupsetGUID as backupset_guid,
            dbName as db_guid,
            (select name from app_client where id = currentIdxServer) as indexserver,
            idxDbEngineType as indexdb_engine

        from App_IndexDBInfo dbinfo
            left join APP_BackupSetName bkset on bkset.guid = dbinfo.dbName
            left join app_application sc on sc.guid = dbinfo.dbName

        where
            bkset.id = (case when '{0}' <> '' then null else {1} end)
            or sc.id = '{0}'
    """.format(
        subclient_id, backupset_id
    ))

    row = cs_db.fetch_one_row()

    if len(row) == 1:
        raise Exception('There is no Index DB information for the given entity')

    backupset_guid = row[0]
    db_guid = row[1]
    index_server_name = row[2]
    index_db_engine = row[3]
    index_server = commcell.clients.get(index_server_name)

    if index_db_engine == '1':
        return CTreeDB(
            commcell,
            index_server,
            backupset_guid,
            db_guid,
            entity_obj
        )

    else:
        raise Exception('Helpers for Index DB other than CTree is not supported right now')
