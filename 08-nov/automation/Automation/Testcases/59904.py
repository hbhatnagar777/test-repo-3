# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import time
import os
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerUtils
from Kubernetes import KubernetesHelper
from Kubernetes.KubernetesHelper import KubernetesHelper
from AutomationUtils import constants, machine
from Server.Plans.planshelper import PlansHelper
from Server.SmartClientGroups.smartclient_helper import SmartClientHelper

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA k8s Autoscale  backup and Restore test case
        This test case does the following

        1) Create test bed
        2) Create Autoscale subclient
        3) Set RPO on plan to 10 mins
        4) Run Full backup
        5) check Auto scale proxy's spawned by validation log files
        6) Check Auto scale proxy's created and mapped to proxy client group
        7) Check DB status on Auto proxy as powered ON
        8) Sleep for 10 mins
        9) Set RPO on plan 50 mins
        9) Check DB status on Auto proxy as powered OFF post 10mins
        10) Run Incremental job
        11) Make sure the DB status on Auto proxy as powered ON.
        12) Sleep for 50 mins
        13) Check the Power status in DB is cleaned and all proxies cleaned

    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA Auto scale Validation"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.utils_path = VirtualServerUtils.UTILS_PATH
        self.pod_create = "poddeployment.yml"
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.show_to_user = True
        self.namespace = ''
        self.restore_namespace = ''
        self.master_machine = None
        self.planid = ''
        self.controller = None
        self.result_string = ''
        self.status = ''
        self.tcinputs = {}
        self.kubehelper = KubernetesHelper(TestCase)

    def run(self):
        """Main function for test case execution"""
        self.namespace = 'cvautomation'
        self.restore_namespace = 'restoretest-77773'
        self.tcinputs.update({"SubclientName": "automation-77773"})
        try:
            if 'VSAClient' in self.tcinputs:
                self.controller = self.commcell.clients.get(self.tcinputs['VSAClient'])
                self.controller_machine = machine.Machine(self.controller, self._commcell)
            self.log.info(" Checking client with name {0} already exists"
                          .format(self.tcinputs['ClientName']))
            if self.commcell.clients.has_client(self.tcinputs.get('ClientName')):
                self.log.info("Create client object for: %s", self.tcinputs['ClientName'])
                self._client = self.commcell.clients.get(self.tcinputs['ClientName'])

            pod_deployment_path = os.path.join(self.utils_path, self.pod_create)
            self.master_machine = machine.Machine(self.tcinputs.get('MasterNode'),
                                                  username=self.tcinputs.get('Username'),
                                                  password=self.tcinputs.get('Password'))
            VirtualServerUtils.decorative_log("Creating Class Objects")

            smartclient_helper = SmartClientHelper(commcell_object=self.commcell)
            plan_helper = PlansHelper(commserve='', username='', password='', commcell_obj=self.commcell)
            self.log.info("Setting rpo on plan as 10 mins")
            rpo_dict = {
                'minutes': 10
            }
            plan_helper.modify_rpo(str(self.tcinputs.get('ClientGroup')), rpo_dict)
            path = "/tmp/automation_{0}".format(self.id)
            VirtualServerUtils.decorative_log("Done Creating ")
            self.kubehelper.populate_tc_inputs(self)
            VirtualServerUtils.decorative_log("setting Kuberenetes Test Environment")
            if self.backupset.subclients.has_subclient(str(self.tcinputs.get('SubclientName'))):
                self.backupset.subclients.delete(str(self.tcinputs.get('SubclientName')))
            self.backupset.application_groups.create_application_group(content=self.namespace,
                                                                       plan_name=
                                                                       str(self.tcinputs.get('PlanName')),
                                                                       subclient_name=
                                                                       str(self.tcinputs.get('SubclientName')))
            self.log.info("Application Group Created  %s", str(self.tcinputs.get('SubclientName')))
            self.backupset = self._instance.backupsets.get(
                self.tcinputs['BackupsetName'])
            self.log.info("Creating subclient object for: %s",
                          self.tcinputs['SubclientName'])
            self.subclient = self._backupset.subclients.get(
                self.tcinputs['SubclientName'])

            self.kubehelper.source_vm_object_creation(self)
            VirtualServerUtils.decorative_log("Running Full Backup")
            self.kubehelper.source_vm_object_creation(self)
            self.kubehelper.backup('FULL')
            log_lines=self.get_logs_for_job_from_file\
                (log_file_name="vsbkp.log", search_term='Agents to be created')
            list_log_lines = log_lines.split('\r\n')
            temp1 = list_log_lines[-2]
            temp2 = temp1.split(',')
            temp3 = temp2[1]
            temp4 = temp3.split('[')
            temp5 = temp4[1]
            temp6 = temp5.split(']')
            count_proxys = int(temp6[0])
            list_of_clients = []
            list_of_clients = smartclient_helper.get_clients_list(self.tcinputs.get('ClientGroup'))
            if len(list_of_clients) == count_proxys:
                self.log.info("Autoscale worked and no.of spawn proxys are {}".format(list_of_clients))
            else:
                raise Exception("Autoscale didnt launch spawn proxys ")
            vm_status = self.autoscale_status()
            if vm_status == 3:
                self.log.info("Powerstatus of VM is Alive")
            else:
                raise Exception("AutoScale Powerstatus is not set")
            self.log.info("Setting rpo on plan as 50 mins")
            rpo_dict = {
                'minutes': 50
            }
            plan_helper.modify_rpo(str(self.tcinputs.get('ClientGroup')), rpo_dict)
            self.log.info("rpo on plan set 50 mins")
            self.log.info("waiting for 10mins")
            time.sleep(12*60)
            self.log.info("VM status should be VM ALive")
            vm_status = self.autoscale_status()
            if vm_status == 5:
                self.log.info("Power status of VM is Alive")
            else:
                raise Exception("AutoScale Powerstatus is not set")
            self.kubehelper.backup('INCREMENTAL')
            vm_status = self.autoscale_status()
            if vm_status == 3:
                self.log.info("Powerstatus of VM is powered on")
            else:
                raise Exception("AutoScale Powerstatus is not correct")
            time.sleep(35*60)
            vm_status = self.autoscale_status()
            if vm_status == 0:
                self.log.info("Power status of VM is poweroff")
            else:
                raise Exception("AutoScale VM's powered off")
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Failed with error: {0}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                rpo_dict = {
                    'minutes': 10
                }
                plan_helper.modify_rpo(str(self.tcinputs.get('ClientGroup')), rpo_dict)
                self.log.info("rpo on plan set 10 mins back")
                self.log.info("TEST CASE IN FINALLY")
            except Exception:
                self.log.warning("Testcase and/or Restore")


    def autoscale_status(self):
        """To Fetch autoscale status on pair"""
        # query = "select statusCode from BlrPair where subClientId ={}".format(self.scid)
        query = "select PowerStatus from MMPowerMgmtHost"
        self.csdb.execute(query)
        _results = self.csdb.fetch_all_rows()
        if int(_results[0][0]) > 0:
            self.status = int(_results[0][0])
        else:
            return 0
        return self.status

    def get_logs_for_job_from_file(self, job_id=None, log_file_name=None, search_term=None):
        """From a log file object only return those log lines for a particular job ID.
        Args:
            job_id          (str)   --  Job ID for which log lines need to be fetched.

            log_file_name   (bool)  --  Name of the log file.

            search_term     (str)   --  Only capture those log lines containing the search term.

        Returns:
            str     -   \r\n separated string containing the requested log lines.

            None    -   If no log lines were found for the given job ID or containing the given search term.

        Raises:
            None

        """
        # GET ONLY LOG LINES FOR A PARTICULAR JOB ID
        return self.controller_machine.get_logs_for_job_from_file(job_id, log_file_name, search_term)