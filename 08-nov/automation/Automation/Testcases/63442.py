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
from VirtualServer.VSAUtils import VsaTestCaseUtils, VirtualServerUtils
from AutomationUtils import constants


class TestCase(CVTestCase):
    """Class for executing Direct San testcase for vmware"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'VSA VMWARE Direct SAN testcase'
        self.tc_utils = VsaTestCaseUtils.VSATestCaseUtils(self,
                                                          self.products_list.VIRTUALIZATIONVMWARE,
                                                          self.features_list.DATAPROTECTION)

    def run(self):
        """Main function for test case execution"""

        try:
            _ = self.tc_utils.initialize(self)

            VirtualServerUtils.decorative_log("Checking the vm count. it should be minimum 4")
            if len(self.tc_utils.sub_client_obj.vm_list) >= 4:
                self.log.info("The subclient has {} vms".format(len(self.tc_utils.sub_client_obj.vm_list)))
            else:
                self.ind_status = False
                self.failure_msg = "The subclient has {} vms. its less than 4 vms".format(
                    len(self.tc_utils.sub_client_obj.vm_list))
                raise Exception(self.failure_msg)

            VirtualServerUtils.decorative_log("checking if the subclient has 2 vms each of windows and linux")
            _lin_vm_count = 0
            _win_vm_count = 0
            for vm in self.tc_utils.sub_client_obj.vm_list:
                if self.tc_utils.sub_client_obj.hvobj.VMs[vm].guest_os.lower() != 'windows':
                    _lin_vm_count += 1
                else:
                    _win_vm_count += 1
            if _lin_vm_count >= 2 and _win_vm_count >= 2:
                self.log.info('There are {} winodws vm and {} unix vms'.format(_win_vm_count, _lin_vm_count))
            else:
                self.ind_status = False
                self.failure_msg = "There Should be atlest 2 vms for windows and unix." \
                                   "There are {} winodws vm and {} unix vms".format(
                    _win_vm_count, _lin_vm_count)
                raise Exception(self.failure_msg)

            VirtualServerUtils.decorative_log("Checking if the proxy should be unix for this testcase")
            _proxies = self.subclient.subclient_proxy
            if _proxies:
                for _proxy in _proxies:
                    if 'windows' in self.tc_utils.sub_client_obj.auto_commcell.get_client_os_type(
                            _proxy).lower():
                        self.ind_status = False
                        self.failure_msg = "OS of the Proxy should be linux"
                        raise Exception(self.failure_msg)
            else:
                if 'windows' in self.tc_utils.sub_client_obj.auto_commcell.get_client_os_type(
                        self.subclient.instance_proxy).lower():
                    self.ind_status = False
                    self.failure_msg = "OS of the Proxy should be linux"
                    raise Exception(self.failure_msg)
            self.log.info("Proxy OS is linux")

            VirtualServerUtils.decorative_log("Checking if the windows have GPT and mbr boot disks")
            _mbr = 0
            _gpt = 0
            for vm in self.tc_utils.sub_client_obj.vm_list:
                self.tc_utils.sub_client_obj.hvobj.VMs[vm].update_vm_info('All', True, True)
                if self.tc_utils.sub_client_obj.hvobj.VMs[vm].guest_os.lower() == 'windows':
                    if self.tc_utils.sub_client_obj.windows_gpt_disk_check(vm, True):
                        _gpt += 1
                    else:
                        _mbr += 1
            if _mbr < 1 or _gpt < 1:
                self.ind_status = False
                self.failure_msg = "windows VMs does not have GPT or MBR boot disk"
                raise Exception(self.failure_msg)
            self.log.info("Windows vms are a mix of GPT and MBR boot disks")

            VirtualServerUtils.decorative_log("checking if the vms are spread across SAN5 and SAN6")
            _combination = ['w5', 'w6', 'l5', 'l6']
            for vm in self.tc_utils.sub_client_obj.vm_list:
                _data_stores = self.tc_utils.sub_client_obj.hvobj.VMs[vm].datastores
                _esx = self.tc_utils.sub_client_obj.hvobj.VMs[vm].esx_host
                _esx_objects = self.tc_utils.sub_client_obj.hvobj.get_content(
                    [self.tc_utils.sub_client_obj.hvobj.vim.HostSystem])
                _esx_obj = list(_esx_objects.keys())[list(_esx_objects.values()).index(_esx)]
                _storage = _esx_obj.configManager.storageSystem
                sys_vol_mount_info = _storage.fileSystemVolumeInfo.mountInfo
                _vmfs_version = None
                for _ds in _data_stores:
                    _ds_vol_info = None
                    for vol in sys_vol_mount_info:
                        if vol.volume.name == _ds:
                            _ds_vol_info = vol.volume
                    if _ds_vol_info.type == 'VMFS' and not _ds_vol_info.local:
                        if _vmfs_version:
                            if not _vmfs_version == _ds_vol_info.majorVersion:
                                self.ind_status = False
                                self.failure_msg = "VMFS version of datastores of the " \
                                                   "individual vm should be of same version"
                                raise Exception(self.failure_msg)
                        else:
                            _vmfs_version = _ds_vol_info.majorVersion
                    else:
                        self.ind_status = False
                        self.failure_msg = "Datastore should be VMFS and Local"
                        raise Exception(self.failure_msg)
                try:
                    _combination.remove(
                        self.tc_utils.sub_client_obj.hvobj.VMs[vm].guest_os[0].lower() + str(_vmfs_version))
                except ValueError:
                    self.log.info('{} is already removed or not rquired for test'.format(
                        self.tc_utils.sub_client_obj.hvobj.VMs[vm].guest_os[0].lower()))
            if _combination:
                self.ind_status = False
                self.failure_msg = "some combination is not present in the vms {}".format(_combination)
                raise Exception(self.failure_msg)
            self.log.info("All combination of VMFs 5 and 6 with windows and linux vms are verified")

            self.tc_utils.run_backup(self)

            VirtualServerUtils.decorative_log("Checking if backup used San tranport mode or not")
            _tranport_mode = self.tc_utils.sub_client_obj.auto_commcell.find_job_transport_mode(
                self.tc_utils.sub_client_obj.backup_job.job_id)
            if _tranport_mode == 'san':
                self.log.info("Backup used San transport mode")
            else:
                self.ind_status = False
                self.failure_msg = "Backup was not run via {} mode. it should be via san mode".format(_tranport_mode)
                raise Exception(self.failure_msg)

            VirtualServerUtils.decorative_log("verifying direct san mode via vsbkp log")
            for _job in self.tc_utils.sub_client_obj.backup_job.details['jobDetail']['clientStatusInfo']['vmStatus']:
                found = None
                found, log_line = VirtualServerUtils.find_log_lines(
                    cs=self.tc_utils.sub_client_obj.auto_commcell.commcell,
                    client_name=_job['Agent'],
                    log_file='vsbkp.log',
                    search_term='GetDiskBlockInfoList',
                    job_id=self.tc_utils.sub_client_obj.backup_job.job_id)
                if found:
                    self.log.info("Direct san used for backup for vm {}".format(_job['vmName']))
                else:
                    self.ind_status = False
                    self.failure_msg = "Backup was not via direct san"
                    raise Exception(self.failure_msg)

            self.tc_utils.run_guest_file_restore(self,
                                                 child_level=True,
                                                 msg='Guest Files restores from Child')
            self.tc_utils. \
                run_virtual_machine_restore(self,
                                            power_on_after_restore=True,
                                            unconditional_overwrite=True,
                                            msg='FULL VM out of Place restores from Parent')

        except Exception:
            self.ind_status = False

        finally:
            try:
                self.tc_utils.sub_client_obj.cleanup_testdata(self.tc_utils.backup_options)
                self.tc_utils.sub_client_obj.post_restore_clean_up(self.tc_utils.vm_restore_options,
                                                                   status=self.ind_status)
            except Exception:
                self.log.warning("Testcase and/or Restored vm cleanup was not completed")
            if not self.ind_status:
                self.result_string = self.failure_msg
                self.status = constants.FAILED
