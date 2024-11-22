# --------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    db_operations() --  Function to run database operations for this test case.

    restore_db()    --  Function to restore the database changes made during test case execution.

    ccm_export()    --  Function to perform CCM Export.

    import_setup()  --  Function to setup import options for CCM Import.

    ccm_import()    --  Function to perform CCM Import.

    verify_import() --  Function to verify entities migrated during Commcell Migration.

    tear_down()     --  tear down function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.CommcellMigration.ccmhelper import CCMHelper
from AutomationUtils.database_helper import MSSQL
from AutomationUtils import constants, config


class TestCase(CVTestCase):
    """Class for executing this test case."""

    def __init__(self):
        """Initializes test case class object.

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "CCM import with database errors"
        self.config_json = None
        self.sql_username = None
        self.sql_password = None
        self.tcinputs = {
            "ExportLocation": None,
            "ExportPathType": None,
            "ExportUserName": None,
            "ExportPassword": None,
            "ClientName": None,
            "ImportLocation": None,
            "DestinationCommcellHostname": None,
            "DestinationCommcellUsername": None,
            "DestinationCommcellPassword": None
        }

    def db_operations(self):
        """Function to run database operations for this test case."""
        try:
            instance_name = self._commcell.commserv_hostname
            if not self._commcell.is_linux_commserv:
                instance_name += "\\commvault"

            self.db_helper = MSSQL(instance_name,
                                   self.sql_username,
                                   self.sql_password,
                                   "CommServ")
        except:
            raise Exception("Unable to login to the the SQL Database")

        orig_query = "select origCCID from APP_Client where name = '{}'".format(self.client.client_name)
        try:
            self.oriCCID_value = self.db_helper.execute(orig_query)._rows[0][0]

        except:
            raise Exception("Unable to execute query on the commserv database\n {} \n".format(orig_query))

        max_value_for_int = constants.MAX_INT_SIZE_SQL  # large int value
        update_query = "update APP_Client set origCCId = {} where name = '{}'".format(max_value_for_int,
                                                                                      self.client.client_name)
        try:
            self.db_helper.execute(update_query)
            self.log.info("Successfully executed the query \n{} on the commserv database".format(update_query))

        except:
            raise Exception("Unable to exectute query on the commserv database\n {} \n".format(update_query))

    def restore_db(self):
        """Function to restore the database changes made during test case execution."""
        restore_query = """update APP_Client set origCCId = {} \
                            where name = '{}'""".format(self.oriCCID_value, self.client.client_name)
        try:
            self.db_helper.execute(restore_query)

        except:
            raise Exception("Unable to execute query on the commserv databse\n {} \n".format(restore_query))

    def ccm_export(self):
        """Function to run CCM Export."""
        try:
            options = {
                "pathType": self.tcinputs["ExportPathType"],
                "userName": self.tcinputs["ExportUserName"],
                "password": self.tcinputs["ExportPassword"],
                "captureMediaAgents": False
            }

            export_job = self.ccm_helper.run_ccm_export(self.tcinputs["ExportLocation"],
                                                        self.client.client_name, options=options)

            self.log.info("Started CCM Export Job: %s", export_job.job_id)

            if export_job.wait_for_completion():
                self.log.info("CCM Export Job id %s "
                              "completed sucessfully", export_job.job_id)
            else:
                self.log.error("CCM Export Job id %s "
                               "failed/ killed", export_job.job_id)
                raise Exception("CCM Export job failed")

        except Exception as excp:
            self.ccm_helper.server.fail(excp)

    def import_setup(self):
        """Function to setup import options requried to perform CCM import."""
        try:
            self.destination_cs = self.ccm_helper.create_destination_commcell(
                self.tcinputs["DestinationCommcellHostname"],
                self.tcinputs["DestinationCommcellUsername"],
                self.tcinputs["DestinationCommcellPassword"]
            )
            self.log.info("Successfully created and logged into destination commcell {}".format(
                self.destination_cs.commserv_name))

        except Exception as excp:
            self.ccm_helper.server.fail(excp)

    def ccm_import(self):
        """Function to perform CCM Import."""
        try:
            options = {
                'forceOverwrite': True
            }

            import_job = self.ccm_helper.run_ccm_import(
                self.tcinputs["ImportLocation"],
                options=options
            )
            self.log.info("Started CCM Import Job: %s", import_job.job_id)

            if import_job.wait_for_completion():
                self.log.info("CCM Import Job id %s "
                              "completed successfully", import_job.job_id)
            else:
                self.log.error("CCM Import Job id %s "
                               "failed/ killed", import_job.job_id)
                raise Exception("CCM Import job failed")

        except Exception as excp:
            self.ccm_helper.server.fail(excp)

        try:
            self.ccm_helper.set_libary_mapping(self.commcell.commserv_name)
            self.log.info("Library Mapping successfully completed")

        except:
            raise Exception("Failed to perform Library Mapping")

    def verify_import(self):
        """Function to verify entities migrated during Commcell Migration on destination commcell."""
        sub_client, backupset = self.ccm_helper.get_latest_subclient(self.tcinputs["ClientName"],
                                                                     self.destination_cs)

        try:
            self.ccm_helper.restore_by_job(backupset, self.ccm_helper.get_jobs_for_subclient(sub_client))
            self.log.info("Successfully restored jobs on migrated client on destination cs")

        except:
            raise Exception("Restore failed for jobs on migrated client on destination cs")

    def setup(self):
        """Setup function of this test case."""
        self.config_json = config.get_config()
        self.sql_username = self.config_json.SQL.Username
        self.sql_password = self.config_json.SQL.Password
        self.db_operations()
        self.ccm_helper = CCMHelper(self)

    def run(self):
        """Setup function of this test case."""
        self.ccm_export()
        self.import_setup()
        self.ccm_import()
        self.verify_import()

    def tear_down(self):
        """Tear down function of this test case."""
        self.restore_db()
