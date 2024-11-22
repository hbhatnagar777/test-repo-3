# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    source_vm_object_creation() --  To create basic VSA SDK objects
"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.idautils import CommonUtils
from VirtualServer.VSAUtils import OptionsHelper
from VirtualServer.VSAUtils.VirtualServerHelper import (
    AutoVSACommcell,
    AutoVSAVSClient,
    AutoVSAVSInstance,
    AutoVSABackupset,
    AutoVSASubclient
)
from VirtualServer.VSAUtils import VsaTestCaseUtils
from VirtualServer.VSAUtils.AutoScaleUtils import AutoScaleValidation


class TestCase(CVTestCase):
    """Class for executing VSA Azure Auto Scale validation with Multi Subclient"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Azure Auto Scale Validation - Multi Subclient Case"
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)
        self.client2 = None
        self.agent2 = None
        self.instance2 = None
        self.backupset2 = None
        self.subclient2 = None
        self.vsa_client2 = None
        self.vsa_instance2 = None
        self.vsa_backupset2 = None
        self.vsa_subclient2 = None
        self.result_string = ''

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.common_utils = CommonUtils(self.commcell)

    def source_vm_object_creation(self):
        """To create basic VSA SDK objects"""
        self.client2 = self.commcell.clients.get(self.tcinputs['ClientName2'])
        self.agent2 = self.client2.agents.get(self.tcinputs['AgentName'])
        self.instance2 = self.agent2.instances.get(self.tcinputs['InstanceName'])
        self.backupset2 = self.instance2.backupsets.get(self.tcinputs['BackupsetName2'])
        self.subclient2 = self.backupset2.subclients.get(self.tcinputs['SubclientName2'])
        self.vsa_commcell = AutoVSACommcell(self.commcell, self.csdb)
        self.vsa_client2 = AutoVSAVSClient(self.vsa_commcell, self.client2)
        self.vsa_instance2 = AutoVSAVSInstance(self.vsa_client2, self.agent2, self.instance2)
        self.vsa_backupset2 = AutoVSABackupset(self.vsa_instance2, self.backupset2)
        self.vsa_subclient2 = AutoVSASubclient(self.vsa_backupset2, self.subclient2)
        self.auto_scale_obj2 = AutoScaleValidation(self.vsa_subclient2)

    def run(self):
        """Main function for test case execution"""
        try:
            self.source_vm_object_creation()
            backup_option2 = OptionsHelper.BackupOptions(self.vsa_subclient2)
            backup_option2.backup_type = 'INCREMENTAL'
            self.auto_scale_obj2.start_backup_job(backup_option2)
            while not self.auto_scale_obj2.backup_job.is_finished:
                time.sleep(180)
                auto_scale_jobs = self.vsa_commcell.get_vm_management_jobs(
                    self.auto_scale_obj2.backup_job.job_id)
                if auto_scale_jobs:
                    self.log.info(
                        f"VMManagement jobs {auto_scale_jobs} has been "
                        f"started by job {self.auto_scale_obj2.backup_job.job_id}."
                        f"Waiting for jobs to completion.")
                    if not self.auto_scale_obj2.wait_for_vm_management_child_jobs_to_complete():
                        raise Exception("One or more VMManagement "
                                        "failed.Please check logs for more info")
                    break
                self.log.info(f"No VMManagement jog has been "
                              f"started by job {self.auto_scale_obj2.backup_job.job_id}."
                              f"Will re-try after 3 min.")
            else:
                raise Exception(f"No Auto-Scale job has been started by jon "
                                f"{self.auto_scale_obj2.backup_job.job_id}")
            self.tc_utils.initialize(self)
            max_wait_period = self.tcinputs.get('max_wait_period', 75)
            self.tc_utils.run_auto_scale_validation(self,
                                                    backup_type="FULL",
                                                    max_wait_period=int(max_wait_period))

        except Exception as err:
            self.log.error(err)
            self.result_string = str(err)
            self.status = constants.FAILED
            self.failure_msg = str(err)
