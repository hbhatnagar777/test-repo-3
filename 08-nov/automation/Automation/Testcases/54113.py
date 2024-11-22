# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__() 		--  Initialize TestCase class

    setup()			-- 	setup function of this test case

    run() 			--  run function of this test case
"""
import sys, time
import random
from collections import defaultdict
from AutomationUtils import constants as cv_constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.Exchange.exchangepowershell_helper import ExchangePowerShell
from Application.Exchange.exchangedatabase_helper import ExchangeDbHelper
from Application.Exchange.ExchangeMailbox import constants
from AutomationUtils import database_helper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance
        test of Exchange Database backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Exchange DAG: recovery point "
        self.show_to_user = True
        self.exchangepowershell_object = None
        self.ex_object = None
        self.tcinputs = {
            "ClientName": None,
            "CASServerName": None,
            "DomainName": None,
            "ExchangeAdminName": None,
            "ExchangeAdminPassword": None,
            "PSTPath": None,
            "StoragePolicyName": None,
            "OOPPath": None
        }
        self.exchange_server = None
        self.exchange_powershell_objects = {}
        self.database_names = {}
        self.cas_server, self.domain_name, self.exchange_adminname = None, None, None
        self.exchange_pwd, self.pst_path, self.subclient_name = None, None, None
        self.member_servers, self.oop_path1, self.oop_path = None, None, None

    def setup(self):
        """Setup function for this test case"""
        self.cas_server = self.tcinputs['CASServerName']
        self.domain_name = self.tcinputs['DomainName']
        self.exchange_adminname = self.tcinputs['ExchangeAdminName']
        self.exchange_pwd = self.tcinputs['ExchangeAdminPassword']
        self.pst_path = self.tcinputs['PSTPath']
        self.oop_path = self.tcinputs['OOPPath']
        self.subclient_name = self.id
        self.ex_object = ExchangeDbHelper(self)
        self.member_servers = self.client.get_dag_member_servers()
        self.mailboxes = defaultdict(list)
        self.csdb = database_helper.CommServDatabase(self.commcell)

    def run(self):
        """Main function for test case execution"""
        try:
            for member_server in self.member_servers:
                self.exchange_powershell_objects[member_server] = ExchangePowerShell(
                    self.ex_object,
                    self.cas_server,
                    member_server,
                    self.exchange_adminname,
                    self.exchange_pwd,
                    member_server
                )
                self.log.info("Creating Database")
                database_name = f"AUTODBz_{member_server}"
                self.database_names[database_name] = member_server
                self.exchange_powershell_objects[member_server].create_database(database_name)
                self.log.info("Creating mailboxes")
                for i in range(0, constants.NUMBER_OF_MAILBOXES):
                    display_name = "AUTOMBz_" + database_name + "_" + str(i)
                    self.exchange_powershell_objects[member_server].create_mailboxes(
                        display_name,
                        database_name,
                        self.domain_name,
                        constants.NUMBER_OF_MAILBOXES
                    )
                    self.exchange_powershell_objects[member_server].import_pst(
                        display_name,
                        self.pst_path
                    )
                    self.mailboxes[database_name].append(display_name)
            self.log.info("Databases info:")
            self.log.info(self.database_names)
            self.log.info("Creating passive copies")
            for database, server in self.database_names.items():
                while True:
                    member_server = random.choice(self.member_servers)
                    if member_server != server:
                        break
                self.exchange_server = member_server
                self.exchange_powershell_objects[server].exdbcopy_operations(
                    database,
                    self.exchange_server,
                    "PASSIVE"
                )
            self.ex_object.create_exchdbsubclient(
                self.subclient_name,
                list(self.database_names.keys())
            )
            self.log.info('Adding property to backup from passive copy')
            self.subclient.set_exchangedb_subclient_prop(
                'backupFromPassiveCopy',
                True
            )
            self.log.info('Adding property to optimize for message level recovery')
            self.subclient.set_exchangedb_subclient_prop(
                "optimizeForMessageLevelRecovery",
                True
            )
            self.log.info("collecting mailbox properties before backup")
            job = self.ex_object.run_backup("full")
            backup_details = self.ex_object.get_db_server_backup_dict(job)
            for database, server in self.database_names.items():
                if backup_details[database] == server:
                    raise Exception('Backed up from active copy')
            self.log.info('Back up initiated from passive copies for the databases')

            self.log.info('Create recovery point')
            job_ids = {}
            for database, server in self.database_names.items():
                job = self.subclient.create_recovery_point(database, server)
                job_ids[database] = job.job_id
            self.log.info(f'Recovery Point Jobs: {job_ids}')

            mount_paths, recoverypoint_ids = self.ex_object.get_recovery_points(
                self.client.client_id,
                list(job_ids.values())
            )
            self.log.info(f'MountPaths : {mount_paths}')
            self.log.info(f'Recovery  point ids : {recoverypoint_ids}')
            session_IDs = {}
            for database, server in self.database_names.items():
                session_IDs = self.subclient.get_session(database, server, mount_paths, recoverypoint_ids)
            self.log.info(f'Session ids :{session_IDs}')
            mailbox_tags = {}
            self.log.info('Get mailbox tags')
            for database, server in self.database_names.items():
                mailbox_tags = self.subclient.get_mailbox_tags(database, server, mount_paths, session_IDs)
                self.log.info(f'Mailbox tags : {mailbox_tags}')
            self.log.info("Submitting livebrowse restore jobs")
            for database, server in self.database_names.items():
                job = job_ids[database]
                mp = mount_paths[int(job)]
                self.oop_path1 = self.oop_path+'\\'+job+".pst"
                self.log.info(self.oop_path1)
                response = self.subclient.run_restore_messages(
                    database,
                    server,
                    self.oop_path1,
                    session_IDs[mp],
                    mount_paths[int(job)],
                    mailbox_tags[mp]
                )

                self.log.info(response)
                time.sleep(100)
            src_client_id = self.client.client_id
            query = ("select top 2 jobid,status from JMRestoreStats where restoreOptions ='88' and srcClientId " \
                    "= '{0}' order by jobid DESC").format(src_client_id)
            self.log.info(query)
            self.csdb.execute(query)
            self.log.info(self.csdb.rows)
            if not (self.csdb.rows[0][1] == '1' and self.csdb.rows[1][1] == '1'):
                raise Exception("Status of livebrowse restore jobs is not valid")
            for value1 in job_ids.values():
                if not (value1 < self.csdb.rows[0][0] and value1 < self.csdb.rows[1][0]):
                    raise Exception("recovery point job id less than create recovery point job id")

        except Exception as excp:
            self.log.error(
                'Error %s on line %s. Error %s', type(excp).__name__,
                sys.exc_info()[-1].tb_lineno, excp
            )
            self.result_string = str(excp)
            self.status = cv_constants.FAILED
