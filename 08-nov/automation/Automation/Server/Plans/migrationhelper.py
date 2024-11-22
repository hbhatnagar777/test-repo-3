# -*- coding: utf-8 -*-
# pylint: disable=W1202

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for importing, running and validating the policy to plan conversion app

MigrationHelper is the only class defined in this file

MigrationHelper
    retrieve_eligible_subclients    -- retreives the list of subclients that will be
                                        impacted by the migration

    validate_after_step1            -- validates the output of the policy to plan conversion

    step1_complete                  -- checks if step 1 has already been run on the CS
"""
from AutomationUtils import logger, config
from AutomationUtils.database_helper import MSSQL
from Server.Plans import migrationconstants
import csv
import pandas


class MigrationHelper(object):
    "Helper class to perform validation of the validaiton report"

    def __init__(self, commcell_object, sql_pwd):
        """
        Initializes instance of MigrationValidation class

            Args:
                commcell_object     (object)    --  commcell object

                sql_pwd             (str)       --  decrypted password of the CSDB
        """
        self.log = logger.get_log()
        self._commcell = commcell_object
        self.db_obj = MSSQL(
            '{0}\\commvault'.format(self._commcell.webconsole_hostname),
            'sqladmin_cv',
            sql_pwd,
            'CommServ'
        )

    def retrieve_eligible_subclients(self):
        """
        Retreives the list of subclients that are eligible for conversion
        """
        query = migrationconstants.retrieve_eligible_subclients_query
        subclients = self.db_obj.execute(query)
        with open(r'.\\Server\\Plans\\before_run.csv', 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(('subclientId', 'storagePolicyId', 'schedulePolicyId'))
            for row in subclients.rows:
                writer.writerow(row)

    def validate_after_step1(self):
        """Retreive the list of policies associated with each of the eligible subclients."""
        query = """select subclientId, storagePolicyId, basePlanId from 
                    WFEngine.dbo.PolicyToPlanConversion order by subclientId"""
        subclients = self.db_obj.execute(query)
        csv_rows = pandas.read_csv('.\\Server\\Plans\\before_run.csv')
        for row1, row2 in zip(subclients.rows, csv_rows.index):
            if row1[0] == csv_rows['subclientId'][row2]:
                if row1[1] == csv_rows['storagePolicyId'][row2]:
                    self.log.info('Storage policy of has not changed after step 1 for subclientId - ' + str(row1[0]))
                else:
                    self.log.error('Storage policy of has changed by step 1 for subclientId - ' + str(row1[0]))

    def step1_complete(self):
        """Checks if step 1 WF has been run on the setup"""
        query = "select * from GXGlobalParam where name = 'PolicyToPlan'"
        response = self.db_obj.execute(query)
        if len(response.rows) == 0:
            self.log.info("Step 1 has not been run on the CS")
            return False
        else:
            self.log.info("Step 1 was previously run on the CS")
            return True
