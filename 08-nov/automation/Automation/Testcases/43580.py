# --------------------------------------------------------------------------
# -*- coding: utf-8 -*-
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case.

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    export_setup()  --  Function to setup export options for CCM Export.

    ccm_export()    --  Function to perform CCM Export.

    import_setup()  --  Function to setup import options for CCM Import.

    ccm_import()    --  Function to perform CCM Import.

    verify_import() --  Function to verify entities migrated during Commcell Migration.

    tear_down()     --  tear down function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.CommcellMigration.ccmhelper import CCMHelper
from AutomationUtils.database_helper import MSSQL
from ast import literal_eval


class TestCase(CVTestCase):
    """Class for executing this test case."""

    def __init__(self):
        """Initializes test case class object.

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super().__init__()
        self.name = "Export using other SQL instance and verifying migration"
        self.tcinputs = {
            "ExportLocation": None,
            "ExportPathType": None,
            "ExportUserName": None,
            "ExportPassword": None,
            "OtherSqlInstance": None,
            "sqlInstanceName": None,
            "SqlUserName": None,
            "SqlPassword": None,
            "clients": [],
            "CsName": None,
            "ImportLocation": None,
            "ImportPathType": None,
            "ImportUserName": None,
            "ImportPassword": None,
            "DestinationCommcellHostname": None,
            "DestinationCommcellUsername": None,
            "DestinationCommcellPassword": None
        }

    def export_setup(self):
        """Function to setup export options for CCM Export."""
        try:
            self.db_helper = MSSQL(self.tcinputs["sqlInstanceName"],
                                   self.tcinputs["SqlUserName"],
                                   self.tcinputs["SqlPassword"],
                                   "CommServ")
            self.log.info("Successfully connected to SQL Database")

        except:
            raise Exception("Couldn't connect to the SQL server")

        self.client_ids = []
        for client in self.clients_list:
            query = "select id from APP_Client where name = '{}'".format(client)

            try:
                client_id = self.db_helper.execute(query).rows[0][0]
                self.client_ids.append(client_id)

            except:
                raise Exception("Given client {} doesn't exist".format(client))

        self.log.info("DB queries successfully executed")

    def ccm_export(self):
        """Function to perform CCM Export."""
        export_options = {
            "pathType": "Local" if self.tcinputs["ExportPathType"] in {None, "", "Local"} else self.tcinputs[
                "ExportPathType"],
            "userName": "" if self.tcinputs["ExportUserName"] in {None, ""} else self.tcinputs["ExportUserName"],
            "password": "" if self.tcinputs["ExportPassword"] in {None, ""} else self.tcinputs["ExportPassword"],
            "otherSqlInstance": True if self.tcinputs["OtherSqlInstance"] == "True" else False,
            "sqlInstanceName": self.tcinputs["sqlInstanceName"],
            "sqlUserName": self.tcinputs["SqlUserName"],
            "sqlPassword": self.tcinputs["SqlPassword"],
            "captureMediaAgents": False,
            "csName": self.tcinputs["CsName"],
            "clientIds": self.client_ids
        }

        export_job = self.ccm_helper.run_ccm_export(self.tcinputs["ExportLocation"],
                                                    self.clients_list,
                                                    other_entities=None,
                                                    options=export_options)

        self.log.info("Started CCM Export Job: %s", export_job.job_id)

        if export_job.wait_for_completion():
            self.log.info("CCM Export Job id %s "
                          "completed successfully", export_job.job_id)

        else:
            self.log.error("CCM Export Job id %s "
                           "failed/ killed", export_job.job_id)
            raise Exception("CCM Export job failed")

    def import_setup(self):
        """Function to setup import options requirted for CCM Import."""
        self.destination_cs = self.ccm_helper.create_destination_commcell(
            self.tcinputs["DestinationCommcellHostname"],
            self.tcinputs["DestinationCommcellUsername"],
            self.tcinputs["DestinationCommcellPassword"]
        )
        self.log.info("Successfully created and logged in to destination commcell {}".format(
            self.tcinputs["DestinationCommcellHostname"]))

    def ccm_import(self):
        """Function to perform CCM Import."""
        import_options = {
            "forceOverwrite": True,
            "pathType": "Local" if self.tcinputs["ImportPathType"] in {None, "", "Local"} else self.tcinputs[
                "ImportPathType"],
            "userName": "" if self.tcinputs["ImportUserName"] in {None, ""} else self.tcinputs["ImportUserName"],
            "password": "" if self.tcinputs["ImportPassword"] in {None, ""} else self.tcinputs["ImportPassword"]
        }

        import_job = self.ccm_helper.run_ccm_import(self.tcinputs["ImportLocation"], import_options)

        self.log.info("Started CCM Import Job: %s", import_job.job_id)

        if import_job.wait_for_completion():
            self.log.info("CCM Import Job id %s "
                          "completed successfully", import_job.job_id)
        else:
            self.log.error("CCM Import Job id %s "
                           "failed/ killed", import_job.job_id)
            raise Exception("CCM Import job failed")

        try:
            self.ccm_helper.set_libary_mapping(self.commcell.commserv_name)
            self.log.info("Library Mapping successfully completed")

        except:
            raise Exception("Failed to perform Library Mapping")

    def verify_import(self):
        """Function to verify entities migrated during Commcell Migration."""
        sub_client, backupset = self.ccm_helper.get_latest_subclient(self.clients_list[0],
                                                                     self.destination_cs)

        try:
            self.ccm_helper.restore_by_job(backupset, self.ccm_helper.get_jobs_for_subclient(sub_client))
            self.log.info("Successfully restored jobs on migrated client on destination cs")

        except:
            raise Exception("Restore failed for jobs on migrated client on destination cs")

    def setup(self):
        """Setup function of this test case."""
        self.ccm_helper = CCMHelper(self)
        self.clients_list = literal_eval(self.tcinputs["clients"])

    def run(self):
        """Run function of this test case."""
        self.export_setup()
        self.ccm_export()
        self.import_setup()
        self.ccm_import()
        self.verify_import()
