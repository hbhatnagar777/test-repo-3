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

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper, VMHelper
from AutomationUtils import constants
from AutomationUtils.windows_machine import WindowsMachine
from AutomationUtils.unix_machine import UnixMachine
from AutomationUtils.idautils import CommonUtils
import time




class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Open Stack backup and Restore"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Openstack backup quota validation with reg key bUseProxyTenantForSnapshot"
        self.product = self.products_list.VIRTUALIZATIONOPENSTACK
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {}
        self.test_individual_status = True
        self.test_individual_failure_message = ""

    def run(self):
        """Main function for test case execution"""
        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            self.log.info(
                "-" * 25 + " Initialize helper objects " + "-" * 25)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(auto_client,
                                                                  self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)
            self.hvobj = auto_backupset.auto_vsainstance.hvobj
            client_name = self.tcinputs.get('ClientName')
            remoteclient = self.tcinputs.get('Remotemachine')
            agent = self.tcinputs.get('AgentName')
            subclient_name = self.tcinputs.get('SubclientName')
            InstanceName = self.tcinputs.get('InstanceName')
            backupset = self.tcinputs.get('BackupsetName')
            projectname = self.tcinputs.get(
                'destination_project_name', None)
            project_name = self.tcinputs.get(
                'project_name', None)
            subclient_obj = CommonUtils(self.commcell).get_subclient(client_name, agent, backupset, subclient_name)
            try:
                self.log.info('---Setting regkey on the proxy machine---')
                osType = self.hvobj.OpenStackHandler.get_os_type(self.subclient.subclient_proxy[0])
                if osType == 'Windows':
                    self.win_machine = WindowsMachine(self.subclient.subclient_proxy[0], self.commcell)
                    self.win_machine.create_registry('VirtualServer', 'bUseProxyTenantForSnapshot ', 1, reg_type='DWord')
                else:
                    self.unix_machine = UnixMachine(self.subclient.subclient_proxy[0], self.commcell)
                    self.unix_machine.create_registry('VirtualServer', 'bUseProxyTenantForSnapshot ', 1)
                self.log.info('---registry key successfully set on proxymachine---')
            except:
                self.log.error('----Failed to set registry key----')
                raise Exception
            self.log.info(
                '---Getting config values before setting quota----')
            try:
                vm_details1 = []
                for each_vm in self.subclient._vmContent['children']:
                    osobj = VMHelper.OpenStackVM(self.hvobj, each_vm['displayName'])
                    osobj.update_vm_info()
                    vm_details1.append(osobj.ram)
                    vm_details1.append(osobj.vmflavor)
                    vm_details1.append(osobj.vcpus)
                    vm_details1.append(osobj.DiskList)
                self.log.info('successfully got config values')
            except Exception as err:
                self.log.error('---getting config values failed---')
                raise Exception
            self.log.info('---Resetting  quota limits for a project to original limits----')
            try:
                self.hvobj.OpenStackHandler.reset_quota_limits(projectname)
                self.hvobj.OpenStackHandler.reset_volume_limits(projectname)
                self.hvobj.OpenStackHandler.reset_volumesnapshot_limits(projectname)
                self.hvobj.OpenStackHandler.reset_volumesnapsize_limits(projectname)
                self.hvobj.OpenStackHandler.reset_volume_limits(projectname)
                self.log.info('Reset  quota limits for the project successfully'+str(projectname))
            except Exception as err:
                self.log.error('Failed to reset  quota limits for the project'+str(projectname))
                raise Exception
            self.log.info(
                '-----Getting volume limits for a project-----')
            try:
                quotalimit1 = self.hvobj.OpenStackHandler.get_volume_limits(projectname)
                self.log.info('Got volume quota limits for the project'
                              +str(projectname))
            except Exception as err:
                self.log.error('Failed to get volume quota limits for the project'
                               +str(projectname))
                raise Exception
            self.log.info('-----setting volume quota limits for a project-----')
            try:
                self.hvobj.OpenStackHandler.set_quota_volume_diff(projectname)
                self.log.info(
                    'set volume quota limits for the project successfully'+str(projectname))
            except Exception as err:
                self.log.error(
                    'Failed to set volume quota limits for the project'+str(projectname))
                raise Exception
            self.log.info("-" * 25 + " Backup " + "-" * 25)
            try:
                job_obj = subclient_obj.backup("Incremental")
                self.log.info("-----Backup job triggered successfully-----")
            except Exception as err:
                self.log.exception("-----Triggering backup job failed-----")
                raise Exception
            time.sleep(1)
            job_obj._initialize_job_properties()
            if job_obj.wait_for_completion():
                self._log.error("Backup job {0} completed".format(job_obj.job_id))
                raise Exception
            self._log.info((
                "Failed to run Incremental backup which is expected with error: {0}".format(job_obj.delay_reason)))
            self.log.info(
                "---checking for failure reason on database---")
            for each_vm in auto_subclient.vm_list:
                query = "SELECT attrVal from APP_VMProp where attrName = 'vmFailureReason' " \
                     "and  jobId = "+job_obj.job_id+" and vmclientid = (select id from app_client where name = '"+each_vm+"')"
                self.csdb.execute(query)
                output = self.csdb.fetch_all_rows()
            failurereason = 'Insufficient cinder quota to create VM Snapshot'
            if output != ():
                if failurereason not in output[0][0]:
                    self.log.error(
                        '---Failed reason not updated on Database for job--'+str(job_obj.job_id))
                    raise Exception
            self.log.info(
                '--Failed reason updated on the Database for job'+str(job_obj.job_id))
            self.log.info(
                '---Reseting back volume quota limits for a project to original limits----')
            try:
                self.hvobj.OpenStackHandler.reset_volume_limits(projectname)
                self.hvobj.OpenStackHandler.reset_volumesnapshot_limits(projectname)
                self.log.info(
                    'Reseting volume quota limits for the project successfully'
                    +str(projectname))
            except Exception as err:
                self.log.error(
                    'Failed to reset volume quota limits for the project'
                    +str(projectname))
                raise Exception
            self.log.info('---checking source VM existence ----')
            try:
                listinstances = self.hvobj.OpenStackHandler.get_instance_list()
                for each_vm in self.subclient._vmContent['children']:
                    if each_vm['displayName'] not in listinstances.keys():
                        raise Exception
                self.log.info('---source VM  present on Openstack server----')
            except Exception as err:
                self.log.error('source VMs not on Openstack server')
                raise Exception
            self.log.info(
                '---Getting config values after restore job----')
            try:
                vm_details2 = []
                for each_vm in self.subclient._vmContent['children']:
                    time.sleep(5)
                    osobj = VMHelper.OpenStackVM(self.hvobj, each_vm['displayName'])
                    osobj.update_vm_info()
                    vm_details2.append(osobj.ram)
                    vm_details2.append(osobj.vmflavor)
                    vm_details2.append(osobj.vcpus)
                    vm_details2.append(osobj.DiskList)
                self.log.info('successfully got config values')
            except Exception as err:
                self.log.error('---getting config values failed---')
                raise Exception
            self.log.info('--config validation---')
            try:
                if  vm_details1 == vm_details2:
                    self.log.info("------config validation passed----")
            except Exception as err:
                self.log.error('---config validation failed---')
                raise Exception
            self.log.info(
                '---validating if volume quota limits are set to original limits----')
            try:
                quotalimit2 = self.hvobj.OpenStackHandler.get_volume_limits(projectname)
                if quotalimit1 == quotalimit2:
                    self.log.info('Validation successful')
            except Exception as err:
                self.log.error(
                    '---volume quota limits are not set to original limits---'
                    +str(projectname))
                raise Exception
            try:
                self.log.info('---Removing registry key on the proxy machine---')
                if osType == 'Windows':
                    self.win_machine.remove_registry('VirtualServer', 'bUseProxyTenantForSnapshot')
                else:
                    self.unix_machine.remove_registry('VirtualServer', 'bUseProxyTenantForSnapshot')
                self.log.info('---registry key removed on proxy machine successfully---')
            except:
                self.log.error('----Failed to remove registry key----')
                raise Exception
        except Exception as exp:
            self.test_individual_status = False
            self.test_individual_failure_message = str(exp)
        finally:
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED
