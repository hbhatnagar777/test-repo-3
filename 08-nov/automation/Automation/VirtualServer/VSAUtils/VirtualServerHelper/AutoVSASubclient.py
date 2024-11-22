# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Class for Subclient
classes defined:
    AutoVSASubclient  - Wrapper for VSA Subclient operations

"""

import json
import os
import re
import socket
import time
import datetime
import pprint
import random
import threading
import requests
import xmltodict
from urllib.request import urlopen
from cvpysdk.client import Client
from AutomationUtils.machine import Machine
from VirtualServer.VSAUtils import VirtualServerConstants
from VirtualServer.VSAUtils.VirtualServerConstants import ServiceIds, ServiceOperationEntity, SmbRestoreChecks, \
    hypervisor_type, RestoreType
from VirtualServer.VSAUtils import VirtualServerUtils
from VirtualServer.VSAUtils.VsaDiscovery import VsaDiscovery
from cvpysdk.job import Job
from AutomationUtils import logger, config, constants
from AutomationUtils.idautils import CommonUtils
from cvpysdk.constants import VSAObjects
from Server.Scheduler.schedulerhelper import SchedulerHelper
from . import AutoVSAVSClient, AutoVSAVSInstance
from Install.installer_constants import BaselineStatus
import xml.etree.ElementTree as ET
from lxml import etree
from VirtualServer.VSAUtils.VirtualServerConstants import VMBackupType
from AutomationUtils.options_selector import OptionsSelector
from cvpysdk.policies.storage_policies import StoragePolicy

UTILS_PATH = os.path.dirname(os.path.realpath(__file__))


class AutoVSASubclient(object):
    """
    class for performing subclient operations. It act as wrapper for Testcase and SDK
    """

    def __init__(self, backupset_obj, subclient):
        """
        Initialize subclient SDK objects

        Args:
            subclient (obj) - object of subclient class of SDK
        """

        self.auto_vsa_backupset = backupset_obj
        self.log = self.auto_vsa_backupset.log
        self.auto_vsainstance = self.auto_vsa_backupset.auto_vsainstance
        self.auto_vsaclient = self.auto_vsainstance.auto_vsaclient
        self.vsa_agent = self.auto_vsainstance.vsa_agent
        self.auto_commcell = self.auto_vsainstance.auto_commcell
        self.csdb = self.auto_commcell.csdb
        self.hvobj = self.auto_vsainstance.hvobj
        self.subclient = subclient
        self.subclient_name = self.subclient.subclient_name
        self.subclient_id = self.subclient.subclient_id
        self._browse_ma_id = self.subclient.storage_ma_id
        self._browse_ma = self.subclient.storage_ma
        self.config = config.get_config()
        self.quiesce_file_system = True
        self._disk_filter = self.subclient.vm_diskfilter
        self._disk_filter_input = None
        self._vm_record = {}
        self.vm_filter = None
        self._vm_content = None
        self.vm_group_disk_filters = None
        self.vm_list = None
        self.backup_folder_name = None
        self.testdata_path = None
        self.testdata_paths = []
        self.disk_restore_dest = None
        self._is_live_browse = False
        self.ma_machine = None
        self.exe_file_path = None
        self._controller_machine = None
        self._is_live_browse = False
        self.restore_obj = None
        self.timestamp = None
        self.backup_option = None
        self.set_content_details()
        self.restore_proxy_client = None
        self.current_job = None
        self.destination_client_hvobj = None
        self._vm_restore_prefix = 'del'
        self.testcase_id = ''
        self.proxy_obj = {}
        self.restore_validation_options = {}
        self._sleep_timer = 0
        self.proxies_list = None
        if not self.auto_vsainstance.kwargs.get('BYOS', True):
            pass
        else:
            self.ips_of_proxies = self.generate_ips_of_proxies()
            self.utility = OptionsSelector(self.auto_commcell.commcell)
            if getattr(self.hvobj,"power_on_proxies",None) and callable(getattr(self.hvobj,"power_on_proxies",None)):
                self.hvobj.power_on_proxies(self.ips_of_proxies)
            else:
                self.log.warning("Hypervisor object does not have power_on_proxies method")
            if self.config.Virtualization.update_clients:
                self.update_proxies()

    class VmValidation(object):
        def __init__(self, vmobj, vm_restore_options, **kwargs):
            self.vm = vmobj
            self.vm_restore_options = vm_restore_options
            self.kwargs_options = kwargs

        def __eq__(self, other):
            """compares the source vm and restored vm"""

            config_val = (int(self.vm.disk_count) == int(other.vm.disk_count))

            self.log = logger.get_log()
            self.log.info("Source VM:{0}::\nCPU:{1}\nDisk count:{2}\nMemory:{3}".format(
                self.vm.vm_name, self.vm.no_of_cpu, self.vm.disk_count, self.vm.memory
            ))
            self.log.info("Destination VM:{0}::\nCPU:{1}\nDisk count:{2}\nMemory:{3}".format(
                other.vm.vm_name, other.vm.no_of_cpu, other.vm.disk_count, other.vm.memory
            ))
            if config_val:
                if type(self.vm) == type(other.vm):
                    config_val = (float(self.vm.memory) == float(other.vm.memory) and
                                  int(self.vm.no_of_cpu) == int(other.vm.no_of_cpu))
                    if config_val:
                        source = self.vm.VmValidation(self, self.vm_restore_options,
                                                      backup_option=self.kwargs_options.get('backup_option', None))
                        dest = self.vm.VmValidation(other, self.vm_restore_options,
                                                    backup_option=other.kwargs_options.get('backup_option', None))
                        config_val = (source == dest)
                else:
                    dest = other.vm.VmConversionValidation(other.vm, self.vm_restore_options)
                    config_val = dest.__eq__(dest)

            return config_val

        def vm_workload_validation(self, proxy_obj):
            vmvalidation_obj = self.vm.VmValidation(self.vm, self.vm_restore_options)
            vmvalidation_obj.validate_restore_workload(proxy_obj)

    class BackupValidation(object):
        def __init__(self, vmobj, backup_option, **kwargs):
            self.vm = vmobj
            self.backup_option = backup_option
            self.backup_validation_option = kwargs

        def validate(self):
            validate_obj = self.vm.BackupValidation(self.vm, self.backup_option)
            result = validate_obj.validate()
            if self.backup_validation_option.get("proxy_obj"):
                result = validate_obj.validate_workload(self.backup_validation_option["proxy_obj"])
            return result

    class LiveSyncVmValidation(object):
        def __init__(self, vmobj, schedule=None, replicationjob=None, live_sync_options=None):
            self.vm = vmobj
            self.schedule = schedule
            self.replicationjob = replicationjob
            self.live_sync_options = live_sync_options

        def __eq__(self, other):
            """ performes hypervisor specific live sync validation"""
            source = self.vm.LiveSyncVmValidation(self, self.schedule, self.replicationjob, self.live_sync_options)
            if isinstance(self.vm, type(other.vm)):
                dest = self.vm.LiveSyncVmValidation(other, self.schedule, self.replicationjob)
                config_val = (source == dest)
            else:
                dest = other.vm.LiveSyncVmValidation(other, self.schedule, self.replicationjob)
                config_val = dest.__eq__(dest)
            return config_val

    class DrValidation(object):
        def __init__(self, vmobj, rt_details, op_type=None):
            """ Initializes the DRValidation class"""
            self.vm = vmobj
            self.rt_details = rt_details
            self.op_type = op_type

        def __eq__(self, other):
            """ Checks if the source and the destination vms match """
            source = self.vm.DrValidation(self, self.op_type)
            dest = self.vm.DrValidation(other, self.op_type)
            return source == dest

    def get_proxies(self, job_type="backup", **kwargs):
        """
            Creating a dictionary of proxy name as key and proxy location details as value
            Args:
                job_type        (str): Type of job - backup/restore

        """
        self.log.info("Creating a dictionary of proxy name as key and proxy location details as value")
        sub_proxies = self.subclient.subclient_proxy
        instance_proxies = self.auto_vsainstance.get_proxy_list()
        vm_restore_options = kwargs.get('vm_restore_options', None)
        if vm_restore_options:
            # Attribute for destination client name mapped from the adminconsolehelper - restore_client
            if vm_restore_options.restore_client:
                dest_client = vm_restore_options.restore_client
            else:
                dest_client = vm_restore_options._dest_client_name
            destination_client = self.auto_commcell.commcell.clients.get(dest_client)
            _agent = destination_client.agents.get('Virtual Server')
            _instance = _agent.instances.get(vm_restore_options.dest_client_hypervisor.instance_type)
            dest_auto_vsaclient = AutoVSAVSClient(self.auto_commcell, destination_client)
            dest_auto_vsa_instance = AutoVSAVSInstance(dest_auto_vsaclient, _agent, _instance,
                                                       self.auto_vsainstance.tcinputs)
            dest_instance_proxies = dest_auto_vsa_instance.proxy_list

        self.proxy_obj = {}

        if job_type.lower() == "backup":
            if not sub_proxies:
                for proxy in instance_proxies:
                    proxy_ip = self.auto_commcell.get_hostname_for_client(proxy)
                    self.proxy_obj[proxy] = self.hvobj.get_proxy_location(proxy_ip)
            else:
                for proxy in sub_proxies:
                    proxy_ip = self.auto_commcell.get_hostname_for_client(proxy)
                    self.proxy_obj[proxy] = self.hvobj.get_proxy_location(proxy_ip)
        else:
            # Restore to same hypervisor
            if vm_restore_options.destination_client.lower() == self.auto_vsainstance.auto_vsaclient.vsa_client_name:
                for proxy in instance_proxies:
                    proxy_ip = self.auto_commcell.get_hostname_for_client(proxy)
                    self.proxy_obj[proxy] = self.hvobj.get_proxy_location(proxy_ip)
                for proxy in sub_proxies:
                    proxy_ip = self.auto_commcell.get_hostname_for_client(proxy)
                    self.proxy_obj[proxy] = self.hvobj.get_proxy_location(proxy_ip)
            else:
                # Restore to different hypervisor
                for proxy in dest_instance_proxies:
                    proxy_ip = self.auto_commcell.get_hostname_for_client(proxy)
                    self.proxy_obj[proxy] = vm_restore_options.dest_client_hypervisor.get_proxy_location(proxy_ip)

        self.proxy_obj = {key.lower(): value for key, value in self.proxy_obj.items()}

    def get_distribute_workload(self, job_id, **kwargs):
        """
        Args:
            job_id: Backup/Restore job ID

        """
        hypervisor_obj = kwargs.get("hypervisor_obj", self.hvobj)
        query = """SELECT * FROM App_VMProp WHERE jobid = '{0}' and attrName = 'vmAgent' """.format(job_id)
        self.log.info("EXECUTING QUERY %s", query)
        self.csdb.execute(query)
        result = self.csdb.fetch_all_rows()
        self.log.info(f"{len(result)} is the result size and result = {result}")
        self.log.info("Assigning vm object with its proxy name")
        for each_row in result:
            vm_id = int(each_row[2])
            vm_name_query = """SELECT displayName FROM app_client WHERE id = {0}""".format(vm_id)
            self.csdb.execute(vm_name_query)
            result_name_query = self.csdb.fetch_one_row()
            vm_name = result_name_query[0]
            proxy_name = each_row[5]
            hypervisor_obj.VMs[vm_name].proxy_name = proxy_name.lower()

    @property
    def vm_restore_prefix(self):
        """
        Returns the prefix to be attached to the restore VM name

        Returns:
            vm_restore_prefix  (str)   --  the prefix to tbe attached to the restore VM name

        """
        return self._vm_restore_prefix

    @vm_restore_prefix.setter
    def vm_restore_prefix(self, value):
        """
        Sets the prefix to be attached to the restore VM name

        Args:
            value   (str)    --  the prefix to be attached to the restore VM name

        """
        self._vm_restore_prefix = value

    @property
    def sleep_timer(self):
        """
        Returns the sleep timer in seconds

        Returns:
            _sleep_timer  (int)   --  sleep timer in seconds

        """
        return self._sleep_timer

    @sleep_timer.setter
    def sleep_timer(self, value):
        """
        Sets the sleep timer value

        Args:
            value   (int)    --  Time in seconds to be set

        """
        self._sleep_timer = value

    @property
    def controller_machine(self):
        """
        Returns:
            Controller Machine machine class object
        """
        if not self._controller_machine:
            _controller_client_name = self.auto_commcell.get_client_name_from_hostname(
                socket.gethostbyname_ex(socket.gethostname())[2][0])
            self._controller_machine = Machine(
                _controller_client_name, self.auto_commcell.commcell)
        return self._controller_machine

    @property
    def storage_policy(self):
        """Returns storage policy associated with subclient.Read only attribute"""
        return self.subclient.storage_policy

    @storage_policy.setter
    def storage_policy(self, value):
        """
        Set the Specified Storage Policy

        Args:
            value - storage policy name

        Exception:
            if storage policy does not exist
        """
        self.subclient.storage_policy = value

    @property
    def storage_policy_id(self):
        """Returns storage policy id associated with subclient. Read only attribute"""
        sp_name = self.auto_commcell.commcell.storage_policies.get(
            self.storage_policy)
        return sp_name.storage_policy_id

    @property
    def vm_content(self):
        """
             Returns content  associated with subclient in the form of dict.Read only attribute

             Return:
                 content    (dict)  - with keys
                 {
                'allOrAnyChildren': True,
                'equalsOrNotEquals': True,
                'name': anme of the VM,
                'displayName': display name of the VM,
                'path': source path of the VM,
                'type': 9(VM),1(Host)
                        }

        """

        return self.subclient.content

    @vm_content.setter
    def vm_content(self, content):
        """
        set the specified content as content in subclient

        Args:
            content (str)   -   like [VM]=startswith=test*,test1
                                                        [VM] - represent type
                                                                        like [DNS],[HN]

                                                        startswith  represent equality in GUI
                                                                like endswith,equals

                                                        test* - include all VM starts with test
                                                               adding dyanamic contetn in GUI

                                                        , - to include multiple content

                                                        test1 -  non-dynamic content
        """
        self._vm_content = content
        self.set_content_details()

    @property
    def browse_ma(self):
        """
        Returns the browse MA from which the disk restore is perfomed
        It is read only attribute
        """
        return self._browse_ma, self._browse_ma_id

    def __deepcopy__(self, tempobj):
        """
        over ride deepcopy method to copy every attribute of an objevt to other
        """
        try:
            cls = tempobj.__class__
            result = cls.__new__(cls, tempobj.hvobj, tempobj.vm_name)
            for k, v in tempobj.__dict__.items():
                setattr(result, k, v)
            return result

        except Exception as err:
            self.log.exception("Failed to deepcopy Exception:" + str(err))
            raise err

    def generate_ips_of_proxies(self):
        """
        collects the proxies and FBR in the setup

        return:
                (dict) which contain hostname as keys and ips as values
        """
        ips = {}
        proxy_list = []
        try:
            fbr_query = "select net_hostname from APP_Client where id in " \
                        "(select attrVal from APP_InstanceProp where componentNameId = " \
                        + str(self.auto_vsainstance.vsa_instance_id) + " and attrName like '%FBR Unix MA%')"
            self.csdb.execute(query=fbr_query)
            fbr_host = self.csdb.fetch_one_row()[0]
            if fbr_host:
                proxy_list.append(fbr_host)
        except Exception as err:
            self.log.exception("Failed to get FBR :" + str(err))
            self.log.info("the setup might not have any FBR")
        if self.subclient.subclient_proxy:
            for proxy in self.subclient.subclient_proxy:
                proxy_list.append(proxy)
        if not self.subclient.subclient_proxy:
            instance_proxies = self.auto_vsainstance.vsa_instance._get_instance_proxies()
            if instance_proxies:
                for proxy in instance_proxies:
                    if proxy not in proxy_list:
                        proxy_list.append(proxy)
        self.proxies_list = proxy_list
        import socket
        for proxy in proxy_list:
            d_name = self.auto_commcell.get_hostname_for_client(proxy)
            try:
                ips[d_name] = socket.gethostbyname(d_name)
            except:
                pass
        # removing the controller in the proxies list, if controller is also a proxy
        ips.pop(self.controller_machine.ip_address, None)
        return ips

    def update_client(self, client_name):
        """
        update the client to the latest service pack
        Args:
            client_name: name of the client

        Returns:
            None
        """
        client = self.auto_commcell.commcell.clients.get(client_name)
        update_job_object = None
        if client.properties['client']['versionInfo']['UpdateStatus'] == BaselineStatus.NEEDS_UPDATE.value:
            self.log.info(f'client : {client_name} is not up to date, trying to start updates')
            if not client.is_ready:
                self.log.warning(f"check readiness is failing for the client : {client_name} so skipping the update")
                return
            update_job_object = client.push_servicepack_and_hotfix(reboot_client=True)
            self.log.info(f'update job for the client : {client_name} : {update_job_object.job_id} is in progress')
            self.log.info("waiting for the job completion")
            update_job_object.wait_for_completion()
            time.sleep(60)
        else:
            self.log.info(f'client : {client_name} is already up-to-date')
            return
        while not client.is_ready:
            self.log.info("sleeping for 2 mins as the client may be booting after upgrade")
            time.sleep(120)

        client = self.auto_commcell.commcell.clients.get(client_name)
        if client.properties['client']['versionInfo']['UpdateStatus'] != BaselineStatus.NEEDS_UPDATE.value:
            self.log.info(f'update successful for the client : {client_name}')
        else:
            if 'part of another running job' in update_job_object.delay_reason:
                self.log.warning(f'{client_name} is part of another running job')
                return
            self.log.exception(f'the proxy client : {client_name} failed to update to the latest version')
            raise Exception(f'the proxy client : {client_name} failed to update to the latest version')

    def update_proxies(self):
        """
        update the proxies of the hypervisor instance
        """
        for proxy in self.proxies_list:
            self.update_client(proxy)

    def get_previous_full_backup(self, job_id):
        """
        Get the Previous full backup  for this subclient

        args:
                job_id  (int) - for which previous full has to be fetched

        Exception:
                if failed to get app id


        returns:
            job id  (int) - job id of the previous full backup of given current backup

        """
        try:
            _job_list = []
            _query = "Select id from APP_Application where instance = %s and \
                        backupSet = %s and subclientName = '%s'" % \
                     (self.auto_vsainstance.vsa_instance_id,
                      self.auto_vsa_backupset.backupset_id, self.subclient_name)

            self.csdb.execute(_query)
            _results = self.csdb.fetch_one_row()
            if not _results:
                raise Exception(
                    "An exception occurred in getting previous full backup")

            _AppId = _results[0]

            _query1 = "Select jobId  from JMBkpStats where appId = %s and appType = %s \
                                    and bkpLevel = 1 order by jobId DESC" % \
                      (_AppId, VirtualServerConstants.APP_TYPE)

            self.csdb.execute(_query1)
            _results = self.csdb.fetch_all_rows()
            if not _results:
                raise Exception(
                    "An exception occurred in getting previous full backup")

            for each_result in _results:
                tempval = each_result[0]
                if tempval != job_id:
                    _job_list.append(tempval)
                    break

            # _job_list.sort(reverse=True)

            return _job_list[0]

        except Exception as err:
            self.log.exception(
                "Failed to get Previous Full Job Exception:" + str(err))
            raise Exception("ERROR - exception while GetPreviousFULLBackup")

    def get_auto_scale_config_info(self):
        """
        Get auto scale configuration info by executing stored procedure

        Returns (dict): dictionary containing auto scale info
        """
        cs_mssql_obj = self.auto_commcell.get_cs_mssql(use_pyodbc=False, force=True)
        query = f'<Ida_GetAutoScaleConfigInfoReq subclientId="{self.subclient_id}" />'
        output = cs_mssql_obj.execute_stored_procedure('GetAutoScaleOptions', tuple([query]))
        return xmltodict.parse(output.rows[0]['o_xml'])

    def get_recent_incr_backup(self, job_id):
        """
        Get the Previous incr backup  for this subclient
        args:
                job_id  (int) - for which previous incr has to be fetched
        Exception:
                if failed to get app id
        returns:
            job id  (int) - job id of the previous incr backup of given current backup
        """
        try:
            _job_list = []
            _query = "Select id from APP_Application where instance = %s and \
                        backupSet = %s and subclientName = '%s'" % \
                     (self.auto_vsainstance.vsa_instance_id,
                      self.auto_vsa_backupset.backupset_id, self.subclient_name)

            self.csdb.execute(_query)
            _results = self.csdb.fetch_one_row()
            if not _results:
                raise Exception(
                    "An exception occurred in getting previous incr backup")

            _AppId = _results[0]

            _query1 = "Select jobId  from JMBkpStats where appId = %s and appType = %s \
                                    and bkpLevel = 2 order by jobId DESC" % \
                      (_AppId, VirtualServerConstants.APP_TYPE)

            self.csdb.execute(_query1)
            _results = self.csdb.fetch_all_rows()
            if not _results:
                raise Exception(
                    "An exception occurred in getting previous incr backup")

            for each_result in _results:
                tempval = each_result[0]
                if tempval != job_id:
                    _job_list.append(tempval)
                    break

            return _job_list[0]

        except Exception as err:
            self.log.exception(
                "Failed to get Previous Incremental Job Exception:" + str(err))
            raise Exception("ERROR - exception while GetPreviousINCREMENTALBackup")

    def check_snapshot_entry_for_job(self, jobid):
        """ Checks if there is an entry for snapshot in db for the Jobid
        args:
            jobid (str):   job id of job to for which check has to performed
            return (bool):   true if db entry exists else false
            raises exception :
                if error occurs
        """
        try:
            _query = f"Select * from SMMetaData where RefId in (Select SMVolumeID from" \
                     f" SMVolume where JobId in ('{jobid}') ) "
            self.csdb.execute(_query)
            result = self.csdb.fetch_one_row()
            self.log.info("DB query result : {0}".format(result))
            if result:
                if result[0] == '':
                    return False
                else:
                    return True
            else:
                raise Exception("An exception occurred while checking snapshot entry"
                                " in db !")
        except Exception as err:
            raise Exception("An exception occurred while checking snapshot entry"
                            " in db :%s" % err)

    def set_content_details(self):
        """
        Update the subclient details in subclient and prepares VM List

        Exception:
                if failed to update subclient
        """
        try:

            if self._vm_content is None:
                vsdiscovery = VsaDiscovery(self.hvobj)
                _content = vsdiscovery.fetch_subclient_content(self.subclient.content)
                _vm_filter = vsdiscovery.fetch_subclient_content(self.subclient.vm_filter)
                self.vm_list = vsdiscovery.merge_rules(_content, _vm_filter, 'not')
            else:
                raise Exception("Failed in setting Subclient Content")
            for each_vm in self.vm_list:
                if not hasattr(self.hvobj.VMs, each_vm):
                    if self.hvobj.instance_type != hypervisor_type.Google_Cloud.value.lower():
                        self.hvobj.VMs = each_vm
                    else:
                        for data in self.subclient.content:
                            if data['display_name'] == each_vm:
                                # self.hvobj.VMs = data['id']
                                self.hvobj.VMs = data['display_name']
        except Exception as err:
            self.log.exception(
                "Failed to SetContentDetails Exception:" + str(err))
            raise err

    def get_maname_from_policy(self):
        """
        Get the MA Name from policy associated with subclient

        return:
                ma_name     (str)   - ma client name associated with SP

        Exception:
                if failed to get ma name
        """
        try:
            _query = "select DISTINCT AC.name  from MMDataPath MDP, APP_Client AC where \
                        MDP.HostClientId = AC.id AND MDP.CopyId in \
                    (select id from archGroupCopy where archGroupId = %s)" % self.storage_policy_id

            self.csdb.execute(_query)
            _results = self.csdb.fetch_one_row()
            if not _results:
                raise Exception(
                    "An exception occurred in getting ma from policy")

            ma_name = _results[0]
            return ma_name

        except Exception as err:
            self.log.exception(
                "Failed to GetStoragePolicy Exception:" + str(err))
            raise err

    def _process_disk_filter_string(self, controller_string):
        """
        process the filter string to split it into controller , type number

        controller_string: Filter string that is from CS DB
        :return:
            controller_type (str) : it is scsi or ide
            number  (int)          : ilocation of scsi or ide

        """
        try:
            self.log.info("The Controller string is %s" % controller_string)
            _opening_bracket = None
            _possible_brackets = {
                "[": "]",
                "(": ")"
            }
            _brackets_type = list(
                _bracket for _bracket in _possible_brackets.keys() if _bracket in controller_string)
            _total_brackets = len(_brackets_type)
            if _total_brackets == 1:
                _opening_bracket = _brackets_type[0]
                _slot_saperator = "-" if _opening_bracket == "[" else ":"
                if _opening_bracket is not None:
                    controller_string = controller_string.strip()
                    _controller_type = (controller_string.split(_opening_bracket)[0]).strip()
                    _temp = (controller_string.split(_opening_bracket)[1]).strip()
                    _controller_location_string = _temp.split(
                        _possible_brackets[_opening_bracket])[0]
                    _number, _location = _controller_location_string.split(_slot_saperator)
            else:
                _single_slot = [int(slot_value)
                                for slot_value in controller_string.split() if slot_value.isdigit()]
                if len(_single_slot) != 1:
                    raise Exception('Received unformatted slot values')
                _controller_type = controller_string.split(str(_single_slot[0]))[0]
                _number = _single_slot[0]
                _location = _single_slot[0]

            return _controller_type, _number, _location

        except Exception as err:
            self.log.exception(
                "An exception occurred in  process_diks_filter_string %s" % err)
            raise err

    def prepare_disk_filter_list(self):
        """
        Prepares the disk filter list by processing the pattern
        """
        try:

            def process_repository_filters(vm, repository_name):
                return self.hvobj.VMs[vm].get_disks_by_repository(repository_name)

            def process_control_filters(vm, controller_detail):
                if self.hvobj.instance_type in (hypervisor_type.VIRTUAL_CENTER.value.lower(),
                                                hypervisor_type.Xen.value.lower()):
                    return self.hvobj.VMs[vm].get_disk_in_controller(controller_detail)
                else:
                    controller_type, number, location = self._process_disk_filter_string(
                        controller_detail)
                    return self.hvobj.VMs[vm].get_disk_in_controller(controller_type, number,
                                                                     location)

            def process_disk_path_filters(vm, disk_path):
                return self.hvobj.VMs[vm].get_disk_path_from_pattern(disk_path)

            def process_datastore_uri_filters(vm, datastore_uri):
                return self.hvobj.VMs[vm].get_datastore_uri_by_pattern(datastore_uri)

            def process_disk_by_ostype_filters(vm, _disk_type):
                return self.hvobj.VMs[vm]._get_disks_by_os_type()

            def process_by_disk_tag_filters(vm, tag_name, tag_value):
                return self.hvobj.VMs[vm].get_disks_by_tag(tag_name, tag_value)

            def process_by_disk_label(vm, disk_number):
                return self.hvobj.VMs[vm].get_disk_by_label(disk_number)

            disks_filter_process = {
                "1": process_datastore_uri_filters,
                "2": process_disk_path_filters,
                "3": process_control_filters,
                "4": process_repository_filters,
                "5": process_by_disk_label,
                "6": process_disk_by_ostype_filters,
                "9": process_by_disk_tag_filters
            }

            '''
                Apply Datastore/repository filters first since
                there is good chance of all the disks getting filtered out
            '''
            if self._disk_filter is None:
                self._disk_filter = []
            _disk_filter_sorted = sorted(
                self._disk_filter,
                key=lambda _filter: _filter['filterTypeId'],
                reverse=True)
            # Datastore filter check
            if _disk_filter_sorted:
                if _disk_filter_sorted[-1]['filterTypeId'] == '1':
                    _data_store_filter = _disk_filter_sorted.pop()
                    _disk_filter_sorted.insert(0, _data_store_filter)

            for each_vm in self.vm_list:
                self.log.info("Disk Details before filtering are : {0}".format(
                    self.hvobj.VMs[each_vm].disk_dict))

                if self.auto_vsaclient.isIndexingV2:
                    VirtualServerUtils.discovered_client_initialize(self, each_vm)
                    child_sub_vm_disk_filters = self.hvobj.VMs[each_vm].subclient.vm_diskfilter
                    include_vm_group_disk_filters = self.hvobj.VMs[each_vm].subclient.include_vm_group_disk_filters
                    if include_vm_group_disk_filters is not None:
                        if include_vm_group_disk_filters and child_sub_vm_disk_filters:
                            _disk_filter_sorted.extend(child_sub_vm_disk_filters)
                            _disk_filter_sorted = sorted(
                                _disk_filter_sorted,
                                key=lambda _filter: _filter['filterTypeId'],
                                reverse=True)
                            if _disk_filter_sorted[-1]['filterTypeId'] == '1':
                                _data_store_filter = _disk_filter_sorted.pop()
                                _disk_filter_sorted.insert(0, _data_store_filter)
                            self.log.info("[VM : {0}] Using Disk Filters set at the VM and VM Group level".format(each_vm))
                        elif not include_vm_group_disk_filters and child_sub_vm_disk_filters:
                            _disk_filter_sorted = child_sub_vm_disk_filters
                            self.log.info("[VM : {0}] Using Disk Filters set at the VM level".format(each_vm))
                        else:
                            self.log.info(
                                "[VM : {0}] Using Disk Filters set on the VM Group level since no VM level filters "
                                "are set".format(each_vm))

                disk_filter_list = []
                for each_filter in _disk_filter_sorted:
                    if each_filter['filterTypeId'] == '9':
                        disk_path = disks_filter_process[(each_filter['filterTypeId'])](
                            each_vm, each_filter['filter'], each_filter['value'])
                    else:
                        disk_path = disks_filter_process[(each_filter['filterTypeId'])](
                            each_vm, each_filter['filter'])
                    if disk_path is None or disk_path == "" or disk_path == []:
                        self.log.info("the criteria filter %s does not match this VM %s" %
                                      (each_filter['filter'], each_vm))
                    else:
                        if isinstance(disk_path, list):
                            for disk in disk_path:
                                if disk not in disk_filter_list:
                                    disk_filter_list = disk_filter_list + [disk]
                        else:
                            disk_filter_list.append(disk_path)
                    # Do not apply any more filters if all the disks are filtered out
                    if len(disk_filter_list) == len(self.hvobj.VMs[each_vm].disk_dict):
                        break

                lun_disk_dict = {disk: lun for lun, disk in self.hvobj.VMs[each_vm].disk_lun_dict.items()}
                disk_filter_list = list(set(disk_filter_list))
                for each_disk in disk_filter_list:
                    del self.hvobj.VMs[each_vm].disk_dict[each_disk]
                    del self.hvobj.VMs[each_vm].disk_sku_dict[lun_disk_dict[each_disk]]
                self.hvobj.VMs[each_vm].filtered_disks = disk_filter_list

                self.hvobj.VMs[each_vm].disk_count = len(self.hvobj.VMs[each_vm].disk_dict)
                self.log.info("Disk Details after filtering are : {0}".format(self.hvobj.VMs[each_vm].disk_dict))

        except Exception as err:
            self.log.exception("Failed to PrepareDiskFilterListContent Exception:" + str(err))
            raise Exception("ERROR - exception while PrepareDiskFilterListContent")

    def _get_browse_ma(self, fs_restore_options):
        """
        Get the browse Ma for the browse
        Args:
            fs_restore_options: Fs restore options object

        Returns:
            ma_machine - machine object of MA
        """
        try:

            ma_machine = Machine(fs_restore_options._browse_ma_client_name,
                                 self.auto_commcell.commcell)
            if fs_restore_options.is_ma_specified:
                sp_ma_machine = Machine(self._browse_ma, self.auto_commcell.commcell)
                if ma_machine.os_info.lower() != sp_ma_machine.os_info.lower() and \
                        not (fs_restore_options.browse_from_snap and
                             self.hvobj.instance_type == hypervisor_type.MS_VIRTUAL_SERVER.value.lower()):
                    raise Exception(
                        "Browse MA specifies {0} is of difference flavour {1} than SP MA {2} flavour {3}".format(
                            ma_machine, ma_machine.os_info, sp_ma_machine, sp_ma_machine.os_info
                        ))
            else:
                if ma_machine.os_info.lower() == "unix":
                    windows_proxy = None
                    self.log.info("SP MA is unix so setting proxy as browse MA")
                    sub_proxies = self.subclient.subclient_proxy
                    if sub_proxies:
                        self.log.info(
                            "Checking windows in subclientProxy {0}".format(",".join(sub_proxies)))
                        for each_proxy in sub_proxies:
                            temp_ma = Machine(each_proxy, self.auto_commcell.commcell)
                            if temp_ma.os_info.lower() == "windows":
                                ma_machine = temp_ma
                                windows_proxy = each_proxy
                                break
                    else:
                        if not windows_proxy:
                            instance_proxies = self.auto_vsainstance.proxy_list
                            self.log.info("Checking windows in InstanceProxy {0}".format(
                                ",".join(instance_proxies)))
                            for each_proxy in instance_proxies:
                                temp_ma = Machine(each_proxy, self.auto_commcell.commcell)
                                if temp_ma.os_info == "WINDOWS":
                                    ma_machine = temp_ma
                                    windows_proxy = each_proxy
                                    break

                    if not windows_proxy:  # if no windows proxies and no browse ma in JSON
                        self.log.info("No windows proxies at subclient/instance level")
                        _cs_machine = Machine(self.auto_commcell.commcell.commserv_name,
                                              self.auto_commcell.commcell)
                        if _cs_machine.check_registry_exists("VirtualServer", "bEnableCSForVSALiveBrowse") \
                                and str(_cs_machine.get_registry_value("VirtualServer",
                                                                       "bEnableCSForVSALiveBrowse")) == '1':
                            self.log.info("bEnableCSForVSALiveBrowse regkey present. CS used as browse MA")
                            ma_machine = _cs_machine
                            fs_restore_options.browse_ma = self.auto_commcell.commcell.commserv_name
                        else:
                            self.log.info("Unix MA used as browse MA")
                            fs_restore_options.browse_ma = ma_machine.machine_name
                    else:
                        fs_restore_options.browse_ma = windows_proxy

                    # this would slve forcing browse ma for second VM
                    fs_restore_options.is_ma_specified = False

            return ma_machine
        except Exception as err:
            self.log.exception("Failed to _get_browse_ma Exception:" + str(err))
            raise Exception("ERROR - exception while _get_browse_ma")

    def _check_if_live_browse(self, metadata_collected):
        """
        Decides Live browse validation need to be performed or not.

        Args:
                metadata_collected   (bool)  - True on metadata collected , false on not collected

        return:
                True    - If live browse validation needs to be performed
                False   - if live browse validation need notto be performed

        """
        try:
            if not metadata_collected:
                return True
            else:
                return False

        except BaseException:
            self.log.exception(
                "An exception occurred in checking live browse validation needed")
            return False

    def vsa_discovery(self, backup_option, extra_options):
        """
        Creates testdata path and generate testdata and copy the test data to each drive in VM .
        Args:
            backup_option           (object):   object of Backup Options class in options
                                            helper contains all backup options

            extra_options        (dict):     Extra options for testdata creation
        """
        try:

            """
            TODO: Map Disknames with drive letters and stop copying 
                  data to the filtered disks
            """
            for _vm in self.vm_list:
                self.hvobj.VMs[_vm].update_vm_info('All', os_info=True, force_update=True)
                
            if backup_option.run_pre_backup_config_checks:
                # Check configuration before backup
                self.check_configuration_before_backup(backup_option.pre_backup_config_checks)

            self.backup_folder_name = backup_option.backup_type
            self.testdata_path = backup_option.testdata_path

            if not self.testdata_path:
                self.testdata_path = VirtualServerUtils.get_testdata_path(
                    self.controller_machine)
                self.timestamp = os.path.basename(os.path.normpath(self.testdata_path))
                self.auto_vsaclient.timestamp = self.timestamp
            if self.testdata_path not in self.testdata_paths:
                self.testdata_paths.append(self.testdata_path)
            if backup_option.cleanup_testdata_before_backup:
                extra_options['cleanup_before_backup'] = True
                self.cleanup_testdata(backup_option, extra_options)

            if not self.backup_option.validation and self.backup_option.validation_skip_all:
                VirtualServerUtils.decorative_log('Validation set to skip all: skipping testdata creation and copying')
                return

            self.log.info("TesdataPath provided is {}".format(self.testdata_path))
            self.log.info("creating test data directory {}".format(self.testdata_path))
            self.log.info("Generating Test data folders")
            if backup_option.advance_options.get("testdata_size"):
                testdata_size = backup_option.advance_options["testdata_size"]
                if isinstance(testdata_size, tuple):
                    testdata_size = random.randint(*testdata_size)
            else:
                testdata_size = random.randint(40000, 60000)
            zero_size_file = extra_options.get('zero_kb_files', True)
            attempt = 1
            while attempt < 5:
                try:
                    generate = self.controller_machine.generate_test_data(self.testdata_path, 3, 5,
                                                                          testdata_size, zero_size_file=zero_size_file)
                    break
                except Exception as exp:
                    attempt = attempt + 1
                    time.sleep(60)
            if attempt >= 5:
                generate = self.controller_machine.generate_test_data(self.testdata_path, 3, 5,
                                                                      testdata_size, zero_size_file=zero_size_file)

            if not generate:
                raise Exception(generate)
            for _vm in self.vm_list:
                self.log.info("VM selected is {0}".format(_vm))
                '''If all the disks are filtered out
                    avoiding copying test data to all the drives'''
                if len(self.hvobj.VMs[_vm].disk_list) > 0:
                    for _drive in self.hvobj.VMs[_vm].drive_list.values():
                        self.log.info("Copying Testdata to Drive {0}".format(_drive))
                        self.hvobj.timestamp = self.timestamp
                        self.hvobj.copy_test_data_to_each_volume(
                            _vm, _drive, self.backup_folder_name, self.testdata_path)
            special_vm_drive = extra_options.get('special_vm_drive')
            problematic_vm_drive = extra_options.get('problematic_vm_drive')
            if special_vm_drive:
                if backup_option.advance_options.get("big_data_size"):
                    testdata_size = backup_option.advance_options["big_data_size"]
                    if isinstance(testdata_size, tuple):
                        testdata_size = random.randint(*testdata_size)
                else:
                    testdata_size = random.randint(500000, 600000)
                special_testdata = self.testdata_path + "special_testdata"
                attempt = 1
                while attempt < 5:
                    try:
                        generate = self.controller_machine.generate_test_data(special_testdata, 3, 4,
                                                                              testdata_size,
                                                                              hlinks=True,
                                                                              slinks=True)
                        break
                    except Exception as exp:
                        attempt = attempt + 1
                        time.sleep(60)
                if attempt >= 5:
                    generate = self.controller_machine.generate_test_data(special_testdata, 3, 4,
                                                                          testdata_size,
                                                                          hlinks=True,
                                                                          slinks=True)
                if not generate:
                    raise Exception(generate)
                for _vm, _drive in special_vm_drive.items():
                    self.hvobj.copy_test_data_to_each_volume(
                        _vm, _drive, 'special_testdata', special_testdata)

            if problematic_vm_drive:
                problematic_testdata = self.testdata_path + "problematic_testdata"
                attempt = 1
                while attempt < 5:
                    try:
                        generate = self.controller_machine.generate_test_data(problematic_testdata, problematic=True)
                        break
                    except Exception as exp:
                        attempt = attempt + 1
                        time.sleep(60)
                if attempt >= 5:
                    generate = self.controller_machine.generate_test_data(problematic_testdata, problematic=True)
                if not generate:
                    raise Exception(generate)
                for _vm, _drive in problematic_vm_drive.items():
                    if self.hvobj.VMs[_vm].guest_os.lower() == 'windows':
                        self.hvobj.copy_test_data_to_each_volume(
                            _vm, _drive, 'problematic_testdata', problematic_testdata)
                    else:
                        _timestamp = os.path.basename(os.path.normpath(problematic_testdata))
                        _dest_base_path = self.hvobj.VMs[_vm].machine.join_path(_drive, "problematic_testdata",
                                                                                "TestData", _timestamp)
                        attempt = 1
                        while attempt < 5:
                            try:
                                generate = self.hvobj.VMs[_vm].machine.generate_test_data(_dest_base_path,
                                                                                          problematic=True)
                                break
                            except Exception as exp:
                                attempt = attempt + 1
                                time.sleep(60)
                        if attempt >= 5:
                            generate = self.hvobj.VMs[_vm].machine.generate_test_data(_dest_base_path, problematic=True)
                        if not generate:
                            raise Exception(generate)
            if backup_option.modify_data:
                self.modify_data()
            if backup_option.delete_data:
                self.delete_data()

        except Exception as err:
            self.log.exception("Exception while doing VSA Discovery :{0}".format(err))
            raise err

    def cleanup_testdata(self, backup_option, extra_options=None):
        """
        Cleans up testdata that is copied from each vm in the subclient

        Args:
            backup_option           (object):   object of Backup Options class in options
                                                helper contains all backup options

            extra_options           (dict):      Extra options for cleanup
        """
        try:
            self.log.info("Testdata cleanup from subclient started")
            if not self.backup_folder_name:
                self.backup_folder_name = backup_option.backup_type
            for _vm in self.vm_list:
                self.hvobj.VMs[_vm].get_drive_list(drives="all")
                self.log.info("VM selected is: {}".format(_vm))
                if backup_option.cleanup_testdata_before_backup:
                    for _drive in self.hvobj.VMs[_vm].drive_list.values():
                        for folder_name in ['FULL', 'INCREMENTAL', 'DIFFERENTIAL', 'SYNTHETIC_FULL']:
                            _testdata_path = self.hvobj.VMs[_vm].machine.join_path(_drive,
                                                                                   folder_name)
                            self.log.info("Cleaning up {}".format(_testdata_path))
                            if self.hvobj.VMs[_vm].machine.check_directory_exists(_testdata_path):
                                self.hvobj.VMs[_vm].machine.remove_directory(_testdata_path)
                else:
                    for _drive in self.hvobj.VMs[_vm].drive_list.values():
                        _testdata_path = VirtualServerConstants.get_folder_to_be_compared(
                            folder_name=self.backup_folder_name, _driveletter=_drive,
                            timestamp=self.timestamp)
                        self.log.info("Cleaning up {}".format(_testdata_path))
                        if self.hvobj.VMs[_vm].machine.check_directory_exists(_testdata_path):
                            self.hvobj.VMs[_vm].machine.remove_directory(_testdata_path)
                if extra_options:
                    special_vm_drive = extra_options.get('special_vm_drive')
                    problematic_vm_drive = extra_options.get('problematic_vm_drive')
                else:
                    special_vm_drive = None
                    problematic_vm_drive = None
                if special_vm_drive and _vm in special_vm_drive:
                    _testdata_path = self.hvobj.VMs[_vm].machine.join_path(special_vm_drive[_vm],
                                                                           'special_testdata')
                    if self.hvobj.VMs[_vm].machine.check_directory_exists(_testdata_path):
                        self.hvobj.VMs[_vm].machine.remove_directory(_testdata_path)
                if problematic_vm_drive and _vm in problematic_vm_drive:
                    _testdata_path = self.hvobj.VMs[_vm].machine.join_path(problematic_vm_drive[_vm],
                                                                           'problematic_testdata')
                    if self.hvobj.VMs[_vm].machine.check_directory_exists(_testdata_path):
                        if self.hvobj.VMs[_vm].guest_os.lower() == 'windows':
                            self.hvobj.VMs[_vm].machine.remove_directory("\\\\?\\" + _testdata_path)
                        else:
                            self.hvobj.VMs[_vm].machine.remove_directory(_testdata_path)
            self.log.info("clearing Testdata in controller: {}".format(self.testdata_path))
            if not self.testdata_paths:
                self.testdata_paths = [self.testdata_path]
            for _path in self.testdata_paths:
                self.controller_machine.remove_directory(_path)
            if special_vm_drive:
                self.log.info("clearing Testdata in controller: {}".format(self.testdata_path))
                special_testdata = self.testdata_path + "special_testdata"
                self.log.info("clearing Testdata in controller: {}".format(special_testdata))
                self.controller_machine.remove_directory(special_testdata)
            if problematic_vm_drive:
                problematic_testdata = self.testdata_path + "problematic_testdata"
                self.log.info("clearing Testdata in controller: {}".format(problematic_testdata))
                self.controller_machine.remove_directory("\\\\?\\" + problematic_testdata)
        except Exception as err:
            self.log.exception(
                "Exception while doing cleaning up testdata Discovery: {}".format(err))
            raise err

        finally:
            if self.hvobj.power_off_proxies_flag:
                try:
                    if extra_options and 'cleanup_before_backup' in extra_options.keys():
                        if not extra_options['cleanup_before_backup']:
                            self.hvobj.power_off_proxies(self.ips_of_proxies)
                    else:
                        self.hvobj.power_off_proxies(self.ips_of_proxies)
                except Exception as exp:
                    self.log.exception(exp)
            else:
                self.log.warning("power of proxies flag is to false, please enable as required")

    def check_configuration_before_backup(self, validations=None):
        """
        Validates the configuration before starting the backup process.

        Args:
            validations (dict): Dictionary containing the validation checks to be performed.
                                If None, default validations will be performed.

        Returns:
            bool: True if all validations pass.

        Raises:
            Exception: If any validation fails, an exception is raised indicating
                       pre-backup configuration validation failure.
        """
        self.log.info("Performing pre-backup configuration checks.")
        status = True
        validations = validations if validations else VirtualServerConstants.get_pre_backup_validation_checks(
            self.auto_vsainstance.vsa_instance_name)

        # Check VM count
        if validations.get("min_vm_count", {}).get("validate", False):
            min_vm_count = validations.get("min_vm_count", {}).get("count", 2)
        else:
            min_vm_count = 1
        if len(self.vm_list) < min_vm_count:
            status = False
            self.log.error(
                f"There is only {len(self.vm_list)} source VM(s). The correct configuration for automation is to have "
                f"at least {min_vm_count} source VM(s).")

        # Check VM OS
        if validations.get("min_vm_os", {}).get("validate", False) and min_vm_count > 1:
            expected_os = validations.get("vm_os", {}).get("os_list", ["windows", "unix"])
            vm_with_win_os = [vm for vm in self.vm_list if self.hvobj.VMs[vm].guest_os.lower() == "windows"]
            vm_with_unix_os = [vm for vm in self.vm_list if self.hvobj.VMs[vm].guest_os.lower() != "windows"]

            if "windows" in expected_os and not vm_with_win_os:
                status = False
                self.log.error("No VMs with Windows OS found, but Windows OS is expected.")

            if ("unix" in expected_os or "linux" in expected_os) and not vm_with_unix_os:
                status = False
                self.log.error("No VMs with Unix OS found, but Unix OS is expected.")

        # Check Proxy OS
        if validations.get("min_proxy_os", {}).get("validate", False):
            proxy_list = self.subclient.subclient_proxy if self.subclient.subclient_proxy else self.auto_vsainstance.proxy_list
            if len(proxy_list) < validations.get("min_proxy_os").get("count", 2):
                status = False
                self.log.error(f"Min {validations.get('min_proxy_os').get('count', 2)} "
                               f"proxies were expected but only {len(proxy_list)} are present.")
            expected_os_list = validations.get("min_proxy_os").get("os_list")
            win_proxies = [proxy for proxy in proxy_list if "win" in self.auto_commcell.get_client_os_type(
                proxy).lower()]
            unix_proxies = set(proxy_list) - set(win_proxies)
            if 'windows' in expected_os_list and not win_proxies:
                status = False
                self.log.error("No proxies with Windows OS found, but Windows OS is expected.")
            if 'windows' not in expected_os_list and win_proxies:
                status = False
                self.log.error(
                    "Only Unix/Linux proxies were supposed to be configured, but Windows proxy is found.")
            if 'unix' in expected_os_list and not unix_proxies:
                status = False
                self.log.error("No proxies with Unix/Linux OS found, but Unix/Linux proxy is expected.")
            if 'unix' not in expected_os_list and unix_proxies:
                status = False
                self.log.error("Only Windows proxies were supposed to be configured, but Unix/Linux proxy is found.")

        # Check Media Agent (MA) OS
        if validations.get("ma_os", {}).get("validate", False):
            ma_list = self.subclient._commonProperties['storageDevice']['performanceMode']["perfCRCDetails"]
            expected_ma_os = validations.get("ma_os").get("os_list")
            win_ma = []
            unix_ma = []
            if len(ma_list) < validations['ma_os']['count']:
                self.log.error(
                    f"Minimum {validations['ma_os']['count']} MA was expected"
                    f" to be associated with the storage policy.")
                status = False
            for ma in ma_list:
                if "win" in self.auto_commcell.get_client_os_type(ma.get("perfMa")).lower():
                    win_ma.append(ma)
                else:
                    unix_ma.append(ma)

            if "windows" in expected_ma_os and not win_ma:
                self.log.error("Storage policy was supposed to use Windows MA.")
                status = False
            if "windows" not in expected_ma_os and win_ma:
                self.log.error("Storage policy was not supposed to use Windows MA but Windows MA is being used.")
                status = False
            if "unix" in expected_ma_os and not unix_ma:
                self.log.error("Storage policy was supposed to use Unix MA.")
                status = False
            if "unix" not in expected_ma_os and unix_ma:
                self.log.error("Storage policy was not supposed to use Unix MA but Unix MA is being used.")
                status = False

        # Check minimum disk count
        if validations.get("min_disks_count", {}).get("validate", False):
            min_disk_count = validations.get("min_disks_count", {}).get("count", 2)
            vm_with_expected_disk_count = [vm for vm in self.vm_list if self.hvobj.VMs[vm].disk_count >= min_disk_count]
            if validations.get("min_disks_count", {}).get("all_vm", True) and len(vm_with_expected_disk_count) < len(
                    self.vm_list):
                self.log.error(f"All VMs do not have a minimum of {min_disk_count} disks."
                               f" VMs without minimum disk count: {set(self.vm_list) - set(vm_with_expected_disk_count)}")
                status = False
            elif not vm_with_expected_disk_count:
                self.log.error(f"At least 1 VM with a minimum of {min_disk_count} disks was expected.")
                status = False

        # Hypervisor specific validations
        if self.auto_vsainstance.vsa_instance_name.lower() == hypervisor_type.AZURE_V2.value.lower():
            if not self.validate_azure_vm_config(validations):
                status = False

        if not status:
            raise Exception("Pre-Backup configuration validation failed.")
        self.log.info("Pre-Backup configuration validation passed.")
        return status

    def validate_azure_vm_config(self, validation, **kwargs):
        """Validate if azure source vm have required configurations

            Args:
                validation  (dict): dictionary containing required validation
                    Ex: {
                    'vm_encryption_info': {'all_vm': False},
                    'tags': {'vm': {'all_vm'}},
                    'disk_encryption': {'disk_encryption_type': 'EncryptionAtRestWithPlatformKey', 'all_disk': True}
                    'availability_zone': {'all_vm': False},
                    'proximity_placement_group': {'all_vm': True}
                    }
        """
        status = True
        managed_vm_list = [vm for vm in self.vm_list if self.hvobj.VMs[vm].managed_disk]
        unmanaged_vm_list = [vm for vm in self.vm_list if not self.hvobj.VMs[vm].managed_disk]
        if not managed_vm_list:
            self.log.error("No managed vm found in subclient content")
            status = False
        if not unmanaged_vm_list:
            self.log.error("No unmanaged vm found in subclient content")
            status = False
        if validation.get('vm_encryption_info', {}).get('validate', False):
            encrypted_vms = [vm for vm in self.vm_list if self.hvobj.VMs[vm].auto_vm_config.get('vm_encryption_info')]
            if len(encrypted_vms) == 0 or \
                    (validation.get('vm_encryption_info').get('all_vm', False) and len(encrypted_vms) != self.vm_list):
                self.log.error(f"VMs encrypted does not match the input. Encrypted vms {encrypted_vms}")
                status = False
        if validation.get('tags', {}).get('validate', False):
            vm_with_tags = [vm for vm in self.vm_list if self.hvobj.VMs[vm].auto_vm_config['tags']['vm']]
            vm_with_nic_tags = [vm for vm in self.vm_list if self.hvobj.VMs[vm].auto_vm_config['tags']['nic']]
            vm_with_disk_tags = [vm for vm in self.vm_list if self.hvobj.VMs[vm].\
                                    auto_vm_config['tags']['disk']['tags_set']]
            vm_with_disk_tags_all = [vm for vm in self.vm_list if self.hvobj.VMs[vm].\
                                    auto_vm_config['tags']['disk']['all']]
            if not validation['tags'].get("all_tags", False):
                vm_with_any_tag = set(vm_with_disk_tags + vm_with_nic_tags + vm_with_tags)
                if not vm_with_any_tag or \
                        (validation['tags'].get("all_vm", False) and len(vm_with_any_tag) != len(self.vm_list)):
                    self.log.error(f"Tag validation configuration validation failed. VM with tags {vm_with_tags}")
                    status = False
            else:
                if validation.get('tags').get('vm', {}).get('validate', False) and not vm_with_tags \
                        or (validation.get('tags').get('vm', {}).get('validate', False) and
                            validation['tags'].get("all_vm", False) and len(vm_with_tags) != len(self.vm_list)):
                    self.log.error(f"VM tag validation configuration validation failed. VM with tags {vm_with_tags}")
                    status = False
                if (validation.get('tags').get('disk', {}).get('validate', False) and not vm_with_disk_tags) \
                        or (validation.get('tags').get('disk', {}).get('validate', False) and
                            validation.get('tags').get('disk', {}).get('all_disk',
                                                                       False) and not vm_with_disk_tags_all):
                    self.log.error(f"Disk tag configuration validation failed. VM with tags {vm_with_disk_tags}")
                    status = False
                if validation.get('tags').get('disk', {}).get('validate', False) and \
                        validation.get('tags').get('disk', {}).get('all_vm', False) and \
                        len(vm_with_disk_tags) != len(managed_vm_list):
                    self.log.error(f"Disk tag configuration validation failed. VM with tags {vm_with_disk_tags}")
                    status = False
                if validation.get('tags').get('disk', {}).get('validate', False) and \
                        validation.get('tags').get('disk', {}).get('all_vm', False) and validation.get('tags'). \
                        get('disk', {}).get('all_disk', False) \
                        and len(vm_with_disk_tags_all) != len(managed_vm_list):
                    self.log.error(
                        f"Disk tag configuration validation failed. VM with tags {vm_with_disk_tags_all}")
                    status = False
                if validation.get('tags').get('nic', {}).get('validate', False) and not vm_with_nic_tags \
                        or (validation['tags'].get('nic', {}).get("all_vm", False)
                            and len(vm_with_nic_tags) != len(self.vm_list)):
                    self.log.error(
                        f"NIC tag configuration validation failed. VM with tags {vm_with_disk_tags_all}")
                    status = False
        if validation.get('availability_zone', {}).get('validate', False):
            vm_with_availability_zone = [vm for vm in self.vm_list if self.hvobj.VMs[vm].availability_zone != "None"]
            if not vm_with_availability_zone or (
                    validation.get('availability_zone').get('all_vm', False)
                    and len(vm_with_availability_zone) != self.vm_list):
                self.log.error(
                    f"Availability Zone validation configuration validation failed."
                    f" VM with availability zone {vm_with_availability_zone}")
                status = False
        if validation.get('proximity_placement_group', {}).get('validate', False):
            vm_with_ppg = [vm for vm in self.vm_list if self.hvobj.VMs[vm].proximity_placement_group]
            if not vm_with_ppg or (
                    validation.get('proximity_placement_group').get('all_vm', False)
                    and len(vm_with_ppg) != self.vm_list):
                self.log.error(
                    f"Proximity placement group validation failed for vm configuration. VM with PPG {vm_with_ppg}")
                status = False
        if validation.get('multiple_disk_encryption', {}).get('validate', False):
            vm_with_multiple_disk_encryption_types = []
            for vm in managed_vm_list:
                encryption_types = set()
                for disk, encryption in self.hvobj.VMs[vm].auto_vm_config["disk_encryption_type"].items():
                    encryption_types.add(encryption)
                if len(encryption_types) > 1:
                    vm_with_multiple_disk_encryption_types.append(vm)

            if not vm_with_multiple_disk_encryption_types:
                self.log.error("At least one VM with multiple disk encryption types was expected")

            if validation["multiple_disk_encryption"].get("all_vm", False):
                if len(vm_with_multiple_disk_encryption_types) != len(managed_vm_list):
                    vm_with_single_encryption_type = set(managed_vm_list) - set(vm_with_multiple_disk_encryption_types)
                    self.log.error(f"All VMs were expected to have multiple disk encryption types. "
                                   f"VMs without multiple disk encryption: {vm_with_single_encryption_type}")

        if validation.get('disk_in_multiple_storage_account', {}).get('validate', False):
            validate_all_vms = validation['disk_in_multiple_storage_account'].get('all_vm', False)

            for vm in unmanaged_vm_list:
                storage_account_set = {resource_id.split("/")[2] for name, resource_id in
                                       self.hvobj.VMs[vm].disk_info.items()}

                if validate_all_vms:
                    if len(storage_account_set) < 2:
                        self.log.error(f"Storage account validation for disk configuration on vm {vm} "
                                       f"failed. Disk storage account list: {storage_account_set}")
                        status = False
                else:
                    if len(storage_account_set) >= 2:
                        break
            else:
                if not validate_all_vms:
                    self.log.error("Storage account validation for disk configuration. "
                                   "No VM with disk in different storage account found.")
                    status = False

        if validation.get('generation', {}).get('validate', False):
            present_generation = [self.hvobj.VMs[vm].auto_vm_config['generation'] for vm in self.vm_list]
            if len(set(present_generation)) < 2:
                self.log.error(f"VM generation configuration validation failed. Present vm generation"
                               f"{set(present_generation)}")
                status = False

        if validation.get('sku', {}).get('validate', False):
            if validation.get('sku', {}).get('all_vm', False):
                for vm in managed_vm_list:
                    sku_set = set()
                    for lun, details in self.hvobj.VMs[vm].disk_sku_dict.items():
                        sku_set.add(self.hvobj.VMs[vm].disk_sku_dict[lun]['storageAccountType'])
                    if len(sku_set) < 2:
                        self.log.error(f"SKU validation for vm configuration on vm {vm} failed. SKU list : {sku_set}")
                        status = False
            else:
                for vm in managed_vm_list:
                    sku_set = set()
                    for lun, details in self.hvobj.VMs[vm].disk_sku_dict.items():
                        sku_set.add(self.hvobj.VMs[vm].disk_sku_dict[lun]['storageAccountType'])
                    if len(sku_set) >= 2:
                        break
                else:
                    self.log.error(f"SKU configuration validation failed. No VM with 2 different SKU found.")
                    status = False

        if validation.get('disk_in_multiple_rg', {}).get('validate', False):
            if validation['disk_in_multiple_rg'].get('all_vm', False):
                for vm in managed_vm_list:
                    rg_set = set()
                    for name, resource_id in self.hvobj.VMs[vm].disk_info.items():
                        rg_set.add(resource_id.split("/")[4])
                    if len(rg_set) < 2:
                        self.log.error(f"Resource group validation for disk configuration on vm {vm} "
                                       f"failed. Disk RG list : {rg_set}")
                        status = False
            else:
                for vm in managed_vm_list:
                    rg_set = set()
                    for name, resource_id in self.hvobj.VMs[vm].disk_info.items():
                        rg_set.add(resource_id.split("/")[4])
                    if len(rg_set) >= 2:
                        break

                else:
                    self.log.error(
                        f"Resource group validation for disk configuration. No VM with disk in different RG found.")
                    status = False
        if validation.get('multiple_vm_architecture', {}).get("validate", False):
            present_vm_architecture = [self.hvobj.VMs[vm].vm_architecture for vm in self.vm_list]
            if len(set(present_vm_architecture)) < 2:
                self.log.error(f"VM architecture validation failed for vm configurations. Present vm architecture"
                               f"{set(present_vm_architecture)}")
                status = False

        if validation.get('multiple_security_type', {}).get("validate", False):
            present_security_type = [self.hvobj.VMs[vm].security_profile_info['Type'] for vm in self.vm_list]
            if len(set(present_security_type)) < 2:
                self.log.error(f"VM security type validation failed for vm configurations. Present vm security types"
                               f"{set(present_security_type)}")
                status = False

        if validation.get('secure_boot', {}).get('validate', False):
            secure_boot_vms = [vm for vm in self.vm_list if
                               self.hvobj.VMs[vm].security_profile_info["secureBootEnabled"]]
            if validation['secure_boot'].get("all_vm") and len(secure_boot_vms) != len(self.vm_list):
                self.log.error(f"VM secure boot validation failed during vm configurations validation."
                               f" VMs with secure boot: {set(secure_boot_vms)}")
                status = False

            elif len(secure_boot_vms) == 0:
                self.log.error(
                    f"VM secure boot validation failed during vm configurations validation. VMs with secure boot: "
                    f"{set(secure_boot_vms)}")
                status = False

        if validation.get("extensions", {}).get("validate", False):
            vms_with_extensions = [vm for vm in self.vm_list if self.hvobj.VMs[vm].extensions]
            if validation["extensions"].get("all_vm", False):
                if len(vms_with_extensions) != len(self.vm_list):
                    self.log.error(
                        f"VM extensions validation failed during vm configurations validation."
                        f" VMs with extensions: {set(vms_with_extensions)}")
                    status = False
            elif len(vms_with_extensions) == 0:
                self.log.error(
                    f"VM extensions validation failed during vm configurations validation."
                    f" VMs with extensions: {set(vms_with_extensions)}")
                status = False

        if validation.get("sys_assigned_identity", {}).get("validate", False):
            for vm in self.vm_list:
                identity_type = self.hvobj.VMs[vm].auto_vm_config["identity"]
                if "SystemAssigned" in identity_type:
                    break
            else:
                self.log.error("No vm with system assigned identity found")
                status = False

        if validation.get("usr_assigned_identity", {}).get("validate", False):
            for vm in self.vm_list:
                identity_type = self.hvobj.VMs[vm].auto_vm_config["identity"]
                if "UserAssigned" in identity_type:
                    break
            else:
                self.log.error("No vm with user assigned identity found")
                status = False
        if not status:
            self.log.error("VM config validation failed. Please the logs for more info")
            return False
        self.log.info("Azure vm configuration validation successful")
        return True

    def post_restore_clean_up(self, vm_restore_options, source_vm=False, status=False, **kwargs):

        """
            Cleans up VM and its resources after out of place restore

            Args:
                    vm_restore_options              (str):  options that need to be set while
                                                            performing vm restore
                    source_vm                       (bool): whether  source vm has to be powered
                                                            off or not
                    status                          (bool) : whether the tc has passed ot failed
            Raises:
             Exception:
                If unable to clean up VM and its resources
        """
        try:
            vm_list = kwargs.get('source_vm_list', self.vm_list)
            for each_vm in vm_list:
                if self.hvobj.VMs.get(each_vm, None):
                    if source_vm:
                        self.log.info("Powering off VM {0}".format(each_vm))
                        self.hvobj.VMs[each_vm].power_off()
                    if vm_restore_options and vm_restore_options.dest_client_hypervisor:
                        restore_vm_name = self.vm_restore_prefix + each_vm
                        if restore_vm_name in vm_restore_options.dest_client_hypervisor.VMs:
                            if status:
                                self.log.info("Deleting VM {0}".format(restore_vm_name))
                                vm_restore_options.dest_client_hypervisor.VMs[restore_vm_name].clean_up()
                            else:
                                self.log.info("Powering off VM {0}".format(restore_vm_name))
                                vm_restore_options.dest_client_hypervisor.VMs[restore_vm_name].power_off()
                        else:
                            self.log.info("Skipping the VM {} as it's not present".format(restore_vm_name))

        except Exception as err:
            self.log.exception(
                "Exception while doing cleaning up VM resources: " + str(err))
            raise err

    def modify_data(self):
        """
        Modifies the data on controller machine and then copies to all VM's drives

        Raise Exception:
                if directory does not exists or fails to modify data
        """
        try:
            if self.controller_machine.check_directory_exists(self.testdata_path):
                self.controller_machine.modify_test_data(self.testdata_path, modify=True)
            for _vm in self.vm_list:
                if len(self.hvobj.VMs[_vm].disk_list) > 0:
                    for _drive in self.hvobj.VMs[_vm].drive_list.values():
                        _dest_path = self.hvobj.VMs[_vm].machine.join_path \
                            (_drive, self.backup_folder_name, "TestData", self.timestamp)
                        if self.hvobj.VMs[_vm].machine.check_directory_exists(_dest_path):
                            self.hvobj.VMs[_vm].machine.remove_directory(_dest_path)
                            self.hvobj.copy_test_data_to_each_volume \
                                (_vm, _drive, self.backup_folder_name, self.testdata_path)
                        else:
                            self.log.error("Failed to modify, directory {} does not exists".
                                           format(_dest_path))
        except Exception as err:
            self.log.exception(
                "Exception while modifying data " + str(err))
            raise err

    def check_jobstatus_to_stop_services(self, name):
        """

        Fetch running job for vms and stop the CVD services on proxy or MA after one VM got completed

        Args:
            name(str)          --  client name to stop services

        Returns:
            job_ids   (dict)  --  Dictionary containing job IDs

        Raise Exception:
                fail to get the running job

        """
        try:
            VirtualServerUtils.decorative_log('checking Database for child job complete status')
            jobvmdict = {}
            for each_vm in self.vm_list:
                query1 = "select jobId from JMBkpJobInfo where applicationId in" \
                   " (select id from APP_Application where subclientName = '"+self.subclient.subclient_name+"' " \
                   "and clientid in (select id from APP_Client where name = '"+each_vm+"')) "
                self.csdb.execute(query1)
                query1output = self.csdb.fetch_all_rows()
                jobvmdict[each_vm] = query1output[0][0]
                for key in sorted(jobvmdict):
                    self.log.info('-sorting dict-')
            VirtualServerUtils.decorative_log('sorted in dictionary format' + str(jobvmdict))
            joblist = jobvmdict.values()
            VirtualServerUtils.decorative_log('getting child job completed status from DB')
            childjobstatus = 0
            while childjobstatus <= 0:
                for eachjob in joblist:
                    query = "select status from JMBkpStats where jobid = " + eachjob + ""
                    self.csdb.execute(query)
                    queryoutput = self.csdb.fetch_all_rows()
                    queryoutput = queryoutput[0][0]
                    if queryoutput != None and queryoutput != '':
                        childjobstatus = 1
                        VirtualServerUtils.decorative_log(
                            "successfully got child job completed status from DB-" + str(eachjob))
                        break
                if queryoutput == '1' or queryoutput == '3':
                    self.stop_service(name, 'GxCVD(Instance001)')
            return joblist
        except Exception as err:
            self.log.exception(
                "-----Failed to get individual job IDs of VMs from database-----")
            raise Exception

    def delete_data(self):
        """
        Deletes the first file on controller machine and on all VM's drives

        Raise Exception:
                if directory does not exists or fails to delete data
        """
        try:
            if self.controller_machine.check_directory_exists(self.testdata_path):
                file_list = sorted(self.controller_machine.get_files_in_path(self.testdata_path))
                self.controller_machine.delete_file(file_list[0])
            for _vm in self.vm_list:
                if len(self.hvobj.VMs[_vm].disk_list) > 0:
                    for _drive in self.hvobj.VMs[_vm].drive_list.values():
                        _dest_path = self.hvobj.VMs[_vm].machine.join_path \
                            (_drive, self.backup_folder_name, "TestData", self.timestamp)
                        if self.hvobj.VMs[_vm].machine.check_directory_exists(_dest_path):
                            _file_list = sorted(self.hvobj.VMs[_vm].machine.get_files_in_path(_dest_path))
                            self.hvobj.VMs[_vm].machine.delete_file(_file_list[0])
                        else:
                            self.log.error("Failed to delete, directory {} does not exists".
                                           format(_dest_path))
        except Exception as err:
            self.log.exception(
                "Exception while deleting data " + str(err))
            raise err

    def get_vm_lastcompleted_job(self):
        """

        Fetch last job ran on the vm
        Returns:
        job IDs    (dict)  --  Dictionary containing  job IDs

        Raise Exception:
                fail to get last job on the vm
        """
        try:
            lastjob = {}
            for each_vm in self.vm_list:
                query = "select TOP 1 PERCENT jobId from JMBkpStats where appid =" \
                       " (select id from APP_Application where subclientName = '"+self.subclient.subclient_name+"' " \
                       "and clientid in (select id from APP_Client where name = '"+each_vm+"')) " \
                       "ORDER by jobid DESC"
                self.csdb.execute(query)
                queryoutput = self.csdb.fetch_all_rows()
                lastjob[each_vm] = queryoutput[0][0]
            for key in sorted(lastjob):
                VirtualServerUtils.decorative_log('sorting dict')
                lastjob = lastjob.values()
                VirtualServerUtils.decorative_log(
                    'JOB and VM details sorted in dictionary format ' + str(lastjob))
                return lastjob
        except Exception as err:
            self.log.exception(
                "-----Failed to get child job completed status from DB-----")
            raise Exception

    def backup(self, backup_option, **kwargs):
        """
        Submit VSA backup job

        Args:
                backup_option           (object):   object of Backup Options class in options
                                                    helper contains all backup options

                **kwargs                (dict):   Optional arguments
                    - skip_backup_job_type_check (bool): Skips backup job type check

        Raise Exception:
                if job does not complete successfully

        """
        try:
            if kwargs.get('msg'):
                VirtualServerUtils.decorative_log(kwargs.get('msg'))
            self.backup_option = backup_option
            if not kwargs.get('skip_discovery', False):
                 self.vsa_discovery(self.backup_option, kwargs)
            common_utils = CommonUtils(self.auto_commcell.commcell)
            if backup_option.power_off_unused_vms:
                for vm in self.hvobj.VMs:
                    self.log.info("powering off source vm: {}".format(vm))
                    self.hvobj.VMs[vm].power_off()
            if kwargs.get('template'):
                self.log.info("Converting VMs to template")
                for vm in self.hvobj.VMs:
                    self.hvobj.VMs[vm].convert_vm_to_template()
            if kwargs.get('rdm'):
                self.log.info("calculating the details about rdm disks")
                for vm in self.hvobj.VMs:
                    if not self.hvobj.VMs[vm].rdm_details:
                        self.log.error("Error in getting disk details for the vm")
            self.log.info("Starting Backup Job")
            if 'SYNTHETIC_FULL' in backup_option.backup_type and "BEFORE" in backup_option.incr_level:
                _backup_type = ['INCREMENTAL', 'SYNTHETIC_FULL']
            elif 'SYNTHETIC_FULL' in backup_option.backup_type and "AFTER" in backup_option.incr_level:
                _backup_type = ['SYNTHETIC_FULL', 'INCREMENTAL']
            elif 'SYNTHETIC_FULL' in backup_option.backup_type and "BOTH" in backup_option.incr_level \
                    and self.auto_vsainstance.vsa_instance._instance_name == hypervisor_type.AZURE_V2.value.lower():
                _backup_type = ['INCREMENTAL', 'SYNTHETIC_FULL', 'INCREMENTAL']
            else:
                _backup_type = [self.backup_option.backup_type]
            if backup_option.set_disk_props:
                if backup_option.disk_props_dict:
                    self.log.info("Setting disk props")
                    # Set provided disk properties for all VMs
                    for vm in self.hvobj.VMs:
                        self.hvobj.VMs[vm].set_disk_props(backup_option.disk_props_dict)
                else:
                    raise Exception("disk_props_dict not provided to set disk props")
            for _bc_type in _backup_type:
                _backup_jobs = self.subclient.backup(_bc_type,
                                                     self.backup_option.run_incr_before_synth,
                                                     self.backup_option.incr_level,
                                                     self.backup_option.collect_metadata,
                                                     self.backup_option.advance_options)


                if not (isinstance(_backup_jobs, list)):
                    _backup_jobs = [_backup_jobs]
                for _backup_job in _backup_jobs:
                    self.backup_job = _backup_job

                    # In case of synthetic full, entries are added to JMJobDataLink table
                    # only when all jobs are complete. This table is accessed later to get parent job ID
                    if (_bc_type == 'SYNTHETIC_FULL'
                            and self.auto_vsaclient.isIndexingV2
                            and self.auto_vsainstance.vsa_instance_name != "kubernetes"):
                        self.log.info(
                            'Waiting for child job [%s] to complete first in case of synthetic full',
                            _backup_job.job_id
                        )
                        if not _backup_job.wait_for_completion(**kwargs):
                            raise Exception("Failed to run backup with error: {0}".format(_backup_job.delay_reason))
                        self.log.info('Child job [%s] is complete', _backup_job.job_id)

                self.backup_option.backup_job = self.backup_job
                self.log.info("Submitted '{0}' backup Job : {1}".format(_bc_type, self.backup_job.job_id))

                if (_bc_type == 'SYNTHETIC_FULL'
                        and self.auto_vsaclient.isIndexingV2
                        and self.auto_vsainstance.vsa_instance_name != "kubernetes"):
                    parent_job_id = self.auto_commcell.get_vm_parentjob(self.backup_job.job_id, 7)
                    self.log.info('Synthetic full parent job is [%s]', parent_job_id)
                    self.backup_job = self.auto_commcell.commcell.job_controller.get(parent_job_id)

                if kwargs.get('job_status'):
                    VirtualServerUtils.decorative_log("check job status")
                    _op_id = kwargs.get('op_id')
                    _entity_id = kwargs.get('entity_id')
                    self.current_job = self.backup_job.job_id
                    self.check_job_status_fromDB(_op_id, _entity_id)
                if not _backup_job.wait_for_completion(**kwargs):
                    raise Exception("Failed to run backup with error: {0}"
                                    .format(_backup_job.delay_reason))
                if _backup_job.status.lower() != 'completed':
                    raise Exception("Job {} did not complete sucessfully. Error: {}"
                                    .format(_backup_job.job_id, _backup_job.delay_reason))
                self.log.info("Backup Job {0} completed successfully"
                              "Checking if Job type is Expected for job ID {0}".
                              format(self.backup_job.job_id))
                self.setting_archfileid_vmguid(self.backup_option.backup_job)
                self.current_job = self.backup_job.job_id
                if _bc_type == 'SYNTHETIC_FULL':
                    _bc_type = 'Synthetic Full'
                self.auto_commcell.check_backup_job_type_expected(
                    self.backup_job.job_id, _bc_type)

                if not self.auto_vsainstance.vsa_instance_name == "kubernetes" and self.auto_vsaclient.isIndexingV2:
                    self.vm_childJobs = self.get_childjob_foreachvm(self.current_job)
                    self.log.info(
                        "Checking if Job type is Expected for Child jobs of job ID {0}".format(self.current_job))
                    # override needed for special case when subclient intellisnap property toggles, incremental backup
                    # is converted to full for all child jobs but for parent it still shows as incremental
                    if not kwargs.get('skip_backup_job_type_check', False):
                        self.validate_child_job_type(self.vm_childJobs.values(), _bc_type,
                                                     override_child_bc_type=kwargs.get("override_child_bc_type", None))

                # computation for Backup Copy job

                _bkpcopy_enabled = self.backup_option.advance_options.get("create_backup_copy_immediately")
                if self.backup_option.backup_method == "SNAP" \
                        and _bkpcopy_enabled \
                        and _bc_type != 'Synthetic Full':

                    self.log.info("Backup Type is not Synthfull, looking for backup copy job")
                    retry = 0
                    while retry < 5:
                        try:
                            time.sleep(10)
                            self.backupcopy_job_id = common_utils.get_backup_copy_job_id(
                                self.backup_job.job_id)
                            self.backupcopy_job = Job(self.auto_commcell.commcell, self.backupcopy_job_id)
                            self.log.info("Backup Copy Job ID : {0}".format(self.backupcopy_job_id))
                            break
                        except Exception as e:
                            self.log.info(e)
                            time.sleep(10)
                            retry = retry + 1
                    self.backupcopy_job = Job(self.auto_commcell.commcell, self.backupcopy_job_id)
                    self.log.info("Backup Copy Job {0} :".format(self.backupcopy_job))
                    if kwargs.get('bkpcopy_job_status'):
                        VirtualServerUtils.decorative_log("check backup copy job status")
                        _op_id = kwargs.get('op_id')
                        _entity_id = kwargs.get('entity_id')
                        self.current_job = self.backupcopy_job.job_id
                        self.check_job_status_fromDB(_op_id, _entity_id)
                    if not self.backupcopy_job.wait_for_completion(**kwargs):
                        raise Exception("Failed to run backup copy job with error:{0} "
                                        .format(self.backupcopy_job.details['jobDetail']['clientStatusInfo']
                                                ['vmStatus'][0]['FailureReason']))
                    if self.backupcopy_job.status.lower() != 'completed':
                        raise Exception("Job {} did not complete sucessfully. Error: {}"
                                        .format(self.backupcopy_job.job_id, self.backupcopy_job.delay_reason))
                        # self.setting_archfileid_vmguid(self.backupcopy_job)
                if hasattr(self.backup_option,
                           "Application_aware") and self.backup_option.Application_aware:
                    self.log.info("It is application Aware backup so checking for other jobs")
                    if self.auto_vsaclient.isIndexingV2:
                        self.log.info(f"The client : {self.auto_vsaclient.vsa_client_name} is using V2 indexing")
                        for each_vm in self.vm_childJobs:
                            ida_job_id, workflow_job_id = self.auto_commcell.find_app_aware_jobs(
                                self.vm_childJobs[each_vm])
                    else:
                        self.log.info(f"The client : {self.auto_vsaclient.vsa_client_name} is using V1 indexing")
                        ida_job_id, workflow_job_id = self.auto_commcell.find_app_aware_jobs(
                            self.backup_job.job_id)
                    ida_job = Job(self.auto_commcell.commcell, ida_job_id)
                    workflow_job = Job(self.auto_commcell.commcell, workflow_job_id)
                    if "Completed" not in (ida_job.status and workflow_job.status):
                        raise Exception(
                            "Ida job {0} or Workflow Job {1} failed , please check the logs".format(
                                ida_job, workflow_job))

        except Exception as err:
            self.log.exception(
                "Exception while submitting Backup job:" + str(err))
            raise err

    def setting_archfileid_vmguid(self, job_obj):
        """
        Setting up Arch file id to be used for the vm during browse
        Args:
            job_obj         (string):    backup job id

        Raises:
            Exception
                Raises exception when not able to set archfile id

        """
        try:
            time.sleep(10)
            for _status in \
                    job_obj.details['jobDetail'][
                        'clientStatusInfo'][
                        'vmStatus']:
                if _status['Status'] == 1:
                    self.log.info('VM:{} failed to backup'.format(_status['vmName']))
                    raise Exception
                if _status['jobID'] == 0:
                    archive_file_list = self.auto_commcell.get_backup_job_archive_files(
                        job_obj.job_id)
                else:
                    archive_file_list = self.auto_commcell.get_backup_job_archive_files(
                        _status['jobID'])
                self.backup_option.arch_file_id_used[_status['GUID']] = archive_file_list[0][0]

            self.log.info("Done setting arch file id for the backup jobs")
        except Exception:
            self.log.exception(
                "Exception when in getting job status and archive file id")

    def smbrestorecheck(self, fs_restore_options, op_id, Indextype='V2', dest_vm=None, job_id=None, sourcevm=None):
        """
        Perform checks to know what approach guest file restore used.
        It must be either SMB or guest tools approach.

        Args:

            fs_restore_options      (object) -  options that need to be set while
                                                performing guest file restore

            op_id                   (int)     -  operation id (op_id) user input passed for smbchecks

            Indextype               (string) -  Type of Index. V1 or V2.Default V2

            dest_vm                (object)  -  Destination VM machine object

            job_id                 (string)  -  Restore job

            sourcevm               (string)  - Source VM

        Exception:
                        if validation fails
        """
        if op_id == SmbRestoreChecks.smbsupportcheck.value:
            if fs_restore_options.client_machine.os_info.lower() != "windows":
                raise Exception("Proxy machine is not windows. For SBM proxy should always windows")
        else:
            log_file_name = 'clRestore.log'
            search_term = []
            if op_id == SmbRestoreChecks.smbapproachcheck.value:
                if dest_vm.os_info.lower() == "windows":
                    search_term.append('CVWinGuestAPI interface')
                else:
                    search_term.append('CVUnixGuestAPI interface')
            if op_id == SmbRestoreChecks.vmwaretoolcheck.value:
                search_term = 'CVVMInfoGuestAPI interface'
            password_check = []
            if op_id == SmbRestoreChecks.passwordcheck.value:
                passval = VirtualServerUtils.get_details_from_config_file('password')
                passval = passval.split()
                for eachitem in passval:
                    search_term.append(VirtualServerUtils.decode_password(eachitem))
                password_check = search_term
            for each_item in search_term:
                smbcheck = fs_restore_options.client_machine.get_logs_for_job_from_file(job_id,
                                                                                        log_file_name,
                                                                                        search_term)
                if each_item in password_check and smbcheck is not None:
                    raise Exception(
                        "Password printed and SMB check failed")
                else:
                    if each_item not in password_check and each_item not in smbcheck:
                        raise Exception("SMB approach not used for restore")
            if op_id == SmbRestoreChecks.performancecheck.value:
                query = "SELECT top 1 duration FROM JMRestoreStatS where srcclientid =" \
                        "(select id from app_client where name = '" + sourcevm + "')ORDER BY jobId DESC"
                self.csdb.execute(query)
                jobtime = self.csdb.fetch_all_rows()
                jobtime = jobtime[0][0]
                return jobtime

    def agentless_file_restore(self, fs_restore_options, msg="", discovered_client=None, dest_vm=None, Indextype=None):
        """

        perform Agentless file restore for specific subclient

        Args:
                fs_restore_options      (object):   options that need to be set while
                                                    performing guest file restore

                msg                     (string):  Log line to be printed

                discovered_client       (string):   Pass the discovered client name if restore has to be performed from
                                                    discovered client.

                dest_vm                 (string):  Destination VM for restore

                Indextype               (string): Type of the Index. V1 or V2

        Exception:
                        if job fails
                        if validation fails

        """

        try:
            VirtualServerUtils.decorative_log(msg)
            if not self.backup_option.validation and self.backup_option.validation_skip_all:
                VirtualServerUtils.decorative_log('Validation set to skip all: skipping agenteless File level restore')
                return
            if discovered_client:
                temp_vmlist = [discovered_client]
                VirtualServerUtils.discovered_client_initialize(self, discovered_client)
            else:
                temp_vmlist = self.vm_list
            for _vm in temp_vmlist:
                self.log.info("Guest file restore from {0} VM".format(_vm))
                _path_dict = {}
                flr_options, btrfs_drive_list, btrfs_fs = self.file_level_path(fs_restore_options, _vm)
                fs_restore_options = flr_options['fs_restore_options']
                VirtualServerUtils.decorative_log("Its Agentless restore")
                if dest_vm == None:
                    dest_vm = _vm
                flr_options['dest_machine'] = fs_restore_options.auto_subclient.hvobj.VMs[
                    dest_vm].machine
                if fs_restore_options.smbrestore:
                    self.smbrestorecheck(fs_restore_options, 1, None, flr_options['dest_machine'])
                _drive = next(
                    iter(fs_restore_options.auto_subclient.hvobj.VMs[dest_vm].drive_list.values()))
                _restore_folder = flr_options['dest_machine'].join_path(_drive, 'agentless')
                if flr_options['dest_machine'].check_directory_exists(_restore_folder):
                    flr_options['dest_machine'].remove_directory(_restore_folder)
                self.fs_restore_dest = flr_options['dest_machine'].join_path(_restore_folder,
                                                                             self.backup_folder_name, _vm)
                agentless_option = {
                    "vm_user": fs_restore_options.auto_subclient.hvobj.VMs[dest_vm].user_name,
                    "vm_pass": (VirtualServerUtils.encode_base64(
                        fs_restore_options.auto_subclient.hvobj.VMs[dest_vm].password)).decode(),
                    "vm_name": fs_restore_options.auto_subclient.hvobj.VMs[dest_vm].vm_name,
                    "vm_guid": fs_restore_options.auto_subclient.hvobj.VMs[dest_vm].guid,
                    "vserver": fs_restore_options.auto_subclient.hvobj.server_host_name}
                self.log.info("Restore dest path {}".format(self.fs_restore_dest))
                fs_restore_job = self.subclient. \
                    guest_file_restore(vm_name=_vm,
                                       folder_to_restore=flr_options['_fs_path_to_browse_list'],
                                       destination_client=fs_restore_options.destination_client,
                                       destination_path=self.fs_restore_dest,
                                       copy_precedence=fs_restore_options.copy_precedence,
                                       preserve_level=flr_options['_preserve_level'],
                                       unconditional_overwrite=fs_restore_options.unconditional_overwrite,
                                       browse_ma=flr_options['browse_ma'],
                                       fbr_ma=fs_restore_options.fbr_ma,
                                       agentless=agentless_option)
                self.log.info(" Running restore Job {0} :".format(fs_restore_job))
                if not fs_restore_job.wait_for_completion():
                    raise Exception(
                        "Failed to run file level restore job {0} with error:{1} ".format(
                            fs_restore_job.job_id, fs_restore_job.delay_reason))
                self.log.info("file level restore Job got complete JOb Id:{0}".format(
                    fs_restore_job.job_id))
                if self.backup_option.validation:
                    self.file_level_validation(flr_options)
                else:
                    self.log.info("Validation is being skipped")
            self.log.info(
                "Ran file level restore from all the VMs and its drives")
            # To check the type of restore approach used. Restore approach would be either Guest tools or SMB
            if fs_restore_options.smbrestore:
                self.smbrestorecheck(fs_restore_options, 2, Indextype, None, fs_restore_job.job_id)
            if fs_restore_options.smbrestore == False:
                self.smbrestorecheck(fs_restore_options, 3, Indextype, None, fs_restore_job.job_id)
        except Exception as err:
            self.log.exception(
                "Exception at restore job please check logs for more details {0}".format(err))
            self.log.error("Restore: FAIL - File level files Restore Failed")
            raise err

    def get_childjob_foreachvm(self, parentJob):
        """

        return dict {'vm': 'child_jobid'}child job of each vm for parent job

        Args:
            parent job          (list)   --  parent job id

        Raise Exception:
                if no valid data retrieved

        """

        vm_childJobs = {}
        for each_vm in self.vm_list:
            vm_childJobs[each_vm] = str(self.auto_commcell.get_vm_childjob(each_vm, parentJob))
        self.log.info("Parent Jobid :{0} -> Child job per VMs :{1}".format(parentJob, vm_childJobs))
        return vm_childJobs

    def validate_child_job_type(self, joblist, parentjobtype, override_child_bc_type=None):
        """

        validate backup job type for child job. Backup job type should be same as parent job type
        special case: when intellisnap property for subclient toggles, parent/child can be of different types

        Args:
            joblist          (list)   --  job of child vm

            parentjobtype     (str)   --   parent job type

            override_child_bc_type  (str)   --   optional override backup type of child job for special case
        Raise Exception:
                if child job backup type is not same as parent job

        """
        try:
            jobtypevmlist = []
            for eachjob in joblist:
                query = f"select bkpLevel from JMBkpStats where jobId = '{eachjob}'"
                self.csdb.execute(query)
                queryoutput = self.csdb.fetch_all_rows()
                jobtypevmlist.append(queryoutput)
                if override_child_bc_type == 'NoChildJob':
                    VirtualServerUtils.decorative_log('Special case: No child job Id was generated so skipping '
                                                      'child job type validation')
                elif parentjobtype == 'INCREMENTAL' and all(i == [['2']] for i in jobtypevmlist):
                    VirtualServerUtils.decorative_log('Child and parent job type are incremental-' + str(eachjob))
                elif parentjobtype == 'FULL' and all(i == [['1']] for i in jobtypevmlist):
                    VirtualServerUtils.decorative_log('Child and parent job type are full -' + str(eachjob))
                elif parentjobtype == 'Synthetic Full' and all(i == [['64']] for i in jobtypevmlist):
                    VirtualServerUtils.decorative_log('Child and parent job type are Synthetic full -' + str(eachjob))
                elif override_child_bc_type and parentjobtype == 'INCREMENTAL' and all(
                        i == [['1']] for i in jobtypevmlist):
                    VirtualServerUtils.decorative_log('Special case: Child job is Full and parent '
                                                      'is Incremental-' + str(eachjob))
                elif parentjobtype == 'DIFFERENTIAL' and all(i == [['4']] for i in jobtypevmlist):
                    VirtualServerUtils.decorative_log('Child and parent job type are differential-' + str(eachjob))
                else:
                    self.log.exception("---Child job type is not same as parent job type---")
                    raise Exception
        except Exception as err:
            raise Exception

    def restore_path(self, restore_object, _vm):
        """
        Append the correct folder names for creating restore path
        Args:
            restore_object                      (object): disklevel or filelevel restore object

            _vm                                 (str): backup vm name

        Returns:
            Complete restore path

        Exception:
             if it fails to get the restore path

        """
        try:
            if restore_object.testcase_no_path and self.testcase_id:
                return restore_object.client_machine.join_path(
                    restore_object.restore_path,
                    self.backup_folder_name, self.testcase_id, _vm)
            return restore_object.client_machine.join_path(
                restore_object.restore_path,
                self.backup_folder_name, _vm)
        except Exception as err:
            self.log.exception(
                "Exception at getting restore path {}".format(err))
            self.log.error("Exception at getting restore path")
            raise err

    def skip_unix_restore_from_snap(self, fs_restore_options, _vm):
        """
          Return true if Guest file restore of unix vm from snap is not supported

        Args:
            fs_restore_options      (object):   options that need to be set while
                                                        performing guest file restore
            _vm                     (string):   vm to be restored
        """
        return (fs_restore_options.browse_from_snap and
                self.hvobj.instance_type == hypervisor_type.MS_VIRTUAL_SERVER.value.lower()
                and self.hvobj.VMs[_vm].guest_os.lower() != 'windows ')

    def guest_file_restore(self, fs_restore_options, special_vm_drive=None, problematic_vm_drive=None,
                           discovered_client=None, **kwargs):
        """

        perform Guest file restore for specific subclient

        Args:
                fs_restore_options      (object):   options that need to be set while
                                                    performing guest file restore

                discovered_client       (string):   Pass the discovered client name if restore has to be performed from
                                                    discovered client.

                special_vm_drive        (dict):     Vm and drive where more data needs to be copied

                problematic_vm_drive    (dict):     VM and drive from which problematic data needs to be restored

                **kwargs                    : Arbitrary keyword arguments
        Exception:
                        if job fails
                        if validation fails

        """

        try:
            if kwargs.get('msg'):
                VirtualServerUtils.decorative_log(kwargs.get('msg'))
            if not self.backup_option.validation and self.backup_option.validation_skip_all:
                VirtualServerUtils.decorative_log('Validation set to skip all: skipping File level restore')
                return
            if discovered_client:
                temp_vmlist = [discovered_client]
                VirtualServerUtils.discovered_client_initialize(self, discovered_client)
            else:
                temp_vmlist = self.vm_list
            for _vm in temp_vmlist:
                def clean_folder(before_restore=True):
                    if dest_client.check_directory_exists(self.fs_restore_dest):
                        if before_restore:
                            self.log.info(
                                "Directory already exist on Restore proxy, Performing cleanup ")
                        else:
                            self.log.info(
                                "Validation Completed, performing post restore cleanup on Restore proxy")
                        if fs_restore_options.is_part_of_thread:
                            _folders_in_path = dest_client.get_folders_in_path(self.fs_restore_dest,
                                                                               recurse=False)
                            for _folder in _folders_in_path:
                                dest_client.remove_directory(_folder)
                        else:
                            if dest_client.os_info.lower() == 'windows':
                                dest_client.remove_directory("\\\\?\\" + self.fs_restore_dest)
                            else:
                                dest_client.remove_directory(self.fs_restore_dest)

                if self.skip_unix_restore_from_snap(fs_restore_options, _vm):
                    self.log.info(
                        "File restore from Snap for unix machine is not supported for hyper-V and Azure"
                        " skipping restore for VM {0}".format(_vm))
                    continue
                self.log.info("Guest file restore from {0} VM".format(_vm))
                _path_dict = {}
                if fs_restore_options.metadata_collected and \
                        self.hvobj.VMs[_vm].guest_os.lower() != 'windows':
                    drive_list = self.convert_drive_to_volume(_vm)
                else:
                    drive_list = self.hvobj.VMs[_vm].drive_list
                million_files_path = kwargs.get('million_files_path')
                _special_vm_drive = special_vm_drive.get(_vm) if special_vm_drive else None
                _problematic_vm_drive = problematic_vm_drive.get(_vm) if problematic_vm_drive else None
                if _special_vm_drive or _problematic_vm_drive or million_files_path:
                    flr_options, btrfs_drive_list, btrfs_fs = self.file_level_path(fs_restore_options,
                                                                                   _vm, drive_list,
                                                                                   _special_vm_drive,
                                                                                   _problematic_vm_drive,
                                                                                   million_files_path
                                                                                   )
                else:
                    flr_options, btrfs_drive_list, btrfs_fs = self.file_level_path(fs_restore_options,
                                                                                   _vm, drive_list)
                fs_restore_options = flr_options['fs_restore_options']
                self.fs_restore_dest = self.restore_path(fs_restore_options, _vm)
                agentless_option = ""
                if special_vm_drive:
                    _dest_client_os = "windows" if "windows" in fs_restore_options.client_machine.os_info.lower() \
                        else "unix"
                    sections = VirtualServerUtils.get_details_from_config_file(_dest_client_os)
                    user_list = sections.split(",")
                    for each_user in user_list:
                        user_name = each_user.split(":")[0]
                        password = VirtualServerUtils.decode_password(each_user.split(":")[1])
                        try:
                            dest_client = Machine(fs_restore_options._dest_host_name,
                                                  username="\\" + user_name,
                                                  password=password)
                            break
                        except Exception as e:
                            self.log.warning(e)
                else:
                    dest_client = Machine(fs_restore_options.destination_client,
                                          self.auto_commcell.commcell)
                flr_options['dest_machine'] = dest_client
                self.log.info("Restore dest path {}".format(self.fs_restore_dest))
                clean_folder()
                if not fs_restore_options.metadata_collected and \
                        self.hvobj.VMs[_vm].guest_os.lower() == 'windows' and not fs_restore_options.browse_from_snap:
                    cleanup_time = fs_restore_options.cleanup_time * 60
                    self.block_level_clean_registry(cleanup_time)
                fs_restore_job = self.subclient. \
                    guest_file_restore(vm_name=_vm,
                                       folder_to_restore=flr_options['_fs_path_to_browse_list'],
                                       destination_client=fs_restore_options.destination_client,
                                       destination_path=self.fs_restore_dest,
                                       copy_precedence=fs_restore_options.copy_precedence,
                                       preserve_level=flr_options['_preserve_level'],
                                       unconditional_overwrite=fs_restore_options.unconditional_overwrite,
                                       browse_ma=flr_options['browse_ma'],
                                       fbr_ma=fs_restore_options.fbr_ma,
                                       agentless=agentless_option,
                                       from_date=kwargs.get('from_date', 0),
                                       to_date=kwargs.get('to_date', 0))
                self.log.info(" Running restore Job {0} :".format(fs_restore_job))
                if not fs_restore_job.wait_for_completion():
                    raise Exception(
                        "Failed to run file level restore job {0} with error:{1}".format(
                            fs_restore_job.job_id, fs_restore_job.delay_reason))
                self.log.info("file level restore Job got complete JOb Id:{0}".format(
                    fs_restore_job.job_id))
                job_time_end = fs_restore_job.end_timestamp
                if self.backup_option.validation:
                    if _special_vm_drive or _problematic_vm_drive or million_files_path:
                        if btrfs_fs:
                            self.file_level_validation(flr_options, btrfs_drive_list, _special_vm_drive,
                                                       _problematic_vm_drive,
                                                       job_time_end=job_time_end,
                                                       rest_job_id=fs_restore_job.job_id,
                                                       multi_stream=1,
                                                       million_files_path=million_files_path)
                        else:
                            self.file_level_validation(flr_options, drive_list, _special_vm_drive,
                                                       _problematic_vm_drive,
                                                       job_time_end=job_time_end,
                                                       rest_job_id=fs_restore_job.job_id,
                                                       multi_stream=1,
                                                       million_files_path=million_files_path)
                    elif btrfs_fs is True:
                        self.file_level_validation(flr_options, btrfs_drive_list,
                                                   job_time_end=job_time_end,
                                                   rest_job_id=fs_restore_job.job_id,
                                                   multi_stream=1)
                    else:
                        self.file_level_validation(flr_options, drive_list, job_time_end=job_time_end)
                else:
                    self.log.info("Validation is being skipped")
                clean_folder(before_restore=False)
            self.log.info(
                "Ran file level restore from all the VMs and its drives")
        except Exception as err:
            self.block_level_clean_registry()
            self.log.exception(
                "Exception at restore job please check logs for more details {0}".format(err))
            self.log.error("Restore: FAIL - File level files Restore Failed")
            raise err

    def file_level_path(self, fs_restore_options, vm, drive_list=None, special_vm_drive=None,
                        problematic_vm_drive=None, million_files_path=None):
        """
        Fetch the source location for restore
        Args:
            fs_restore_options              (object):   options that need to be set while
                                                        performing guest file restore

            vm                              (string):   name of the vm whose path needs to be
                                                        fetched

            drive_list                      (dict) :    Dict of drives for the vm

            special_vm_drive                (string):     Drive where more data needs to be copied

            problematic_vm_drive            (string):   Drive which has the problematic data

            million_files_path              (string):   Path which has a million files

        Returns:
            flr_options                      (dict):    Options needed to be used during file level
                                                        restore

            btrfs_drive_list                 (dict):   Modified drive list if the source VM

            btrfs_fs                         (bool):   Returns true if source VM has btrfs fs.

        Raises:
            Exception:
                If it fails to fetch the path
        """
        try:
            _path_dict = {}
            if not self.backup_folder_name:
                self.backup_folder_name = fs_restore_options.backup_folder_name
            if not self.testdata_path:
                self.testdata_path = fs_restore_options.testdata_path
                self.timestamp = fs_restore_options.timestamp
                self.testdata_paths.append(self.testdata_path)
            if not drive_list:
                drive_list = self.hvobj.VMs[vm].drive_list
            _fs_path_to_browse_list = []
            if self.hvobj.VMs[vm].guest_os.lower() != 'windows':
                _preserve_level = 10
            else:
                _preserve_level = fs_restore_options.preserve_level
            million_files_drive = None
            if million_files_path:
                _preserve_level = 15
                if self.hvobj.VMs[vm].machine.os_info.lower() == "windows":
                    million_files_path_folders = million_files_path.split(self.hvobj.VMs[vm].machine.os_sep)
                    million_files_drive = million_files_path_folders[0]
                else:
                    million_files_drive = \
                        self.hvobj.VMs[vm].machine.execute_command(f'df -h {million_files_path}').formatted_output[1][5]
            for label, _drive in drive_list.items():
                if fs_restore_options.browse_from_snap \
                        and self.hvobj.VMs[vm].machine.os_info.lower() == "windows":
                    _temp_vm, _temp_vmid = self.subclient._get_vm_ids_and_names_dict_from_browse()
                    _browse_request = self.subclient.guest_files_browse(_temp_vmid[vm],
                                                                        media_agent=fs_restore_options.browse_ma if
                                                                        fs_restore_options.is_ma_specified else "",
                                                                        copy_precedence=fs_restore_options.copy_precedence
                                                                         )
                    self.log.info("Browse request for guest file restore : %s" % str(_browse_request))
                    _path = self.find_snap_guest_file_path(_browse_request[1], label)
                    _path_dict[label] = _path
                    _fs_path_to_browse = [_path, self.backup_folder_name, "TestData",
                                          self.timestamp]
                else:
                    if _drive == "/":
                        _fs_path_to_browse = [self.backup_folder_name, "TestData", self.timestamp]
                    else:
                        _fs_path_to_browse = [label, self.backup_folder_name, "TestData",
                                              self.timestamp]
                _fs_path_to_browse = "\\".join(_fs_path_to_browse)
                _fs_path_to_browse_list.append(_fs_path_to_browse)
                if special_vm_drive or problematic_vm_drive or million_files_path:
                    if special_vm_drive == _drive:
                        _fs_path_to_browse = [_fs_path_to_browse.split('\\')[0],
                                              "special_testdata", "TestData",
                                              self.timestamp + "special_testdata"]
                        _fs_path_to_browse = "\\".join(_fs_path_to_browse)
                        _fs_path_to_browse_list.append(_fs_path_to_browse)
                    elif problematic_vm_drive == _drive:
                        _fs_path_to_browse = [_fs_path_to_browse.split('\\')[0],
                                              "problematic_testdata", "TestData",
                                              self.timestamp + "problematic_testdata"]
                        _fs_path_to_browse = "\\".join(_fs_path_to_browse)
                        _fs_path_to_browse_list.append(_fs_path_to_browse)
                    elif _drive == million_files_drive:
                        if fs_restore_options.browse_from_snap and \
                                self.hvobj.VMs[vm].machine.os_info.lower() == "windows":
                            _fs_path_to_browse = "\\".join(million_files_path.split("\\")[1:])
                            _fs_path_to_browse = "\\".join([_path, _fs_path_to_browse])
                        else:
                            _fs_path_to_browse = million_files_path.strip(self.hvobj.VMs[vm].machine.os_sep).\
                                replace('/', '\\')
                        _fs_path_to_browse_list.append(_fs_path_to_browse)
            if self.hvobj.VMs[vm].machine.os_info.lower() != "windows":
                self.log.info("Checking if unix vms has btrfs FS")
                _source_blk_id = self.hvobj.VMs[vm].machine.execute('blkid')
                _source_blk_id = _source_blk_id.formatted_output
                if any('TYPE="btrfs"' in _mounts for _mounts in _source_blk_id):
                    btrfs_drive_list = drive_list.copy()
                    self.log.info('VM {} has btrfs FS. Changing the source BTRFS path'.format(
                        self.hvobj.VMs[vm].vm_name))
                    _fs_path_to_browse_list, btrfs_drive_list = self.manage_btrfs_uuid(_fs_path_to_browse_list,
                                                                                       fs_restore_options,
                                                                                       _source_blk_id, vm,
                                                                                       btrfs_drive_list)
            if fs_restore_options.is_ma_specified is False:
                browse_ma = ""
            else:
                browse_ma = fs_restore_options.browse_ma

            self._is_live_browse = self._check_if_live_browse(fs_restore_options.metadata_collected)

            if not fs_restore_options.metadata_collected:
                if self._is_live_browse:
                    ma_machine = self._get_browse_ma(fs_restore_options)
                    self.ma_machine = ma_machine
                    self.ma_client_name = self.auto_commcell.commcell.clients.get(
                        fs_restore_options._browse_ma_client_name)

            flr_options = {"fs_restore_options": fs_restore_options,
                           "_fs_path_to_browse_list": _fs_path_to_browse_list,
                           "_preserve_level": _preserve_level,
                           "browse_ma": browse_ma,
                           "_path_dict": _path_dict,
                           "vm": vm}
            self.log.info(pprint.pformat(vars(fs_restore_options)))
            self.log.info("flr_options: {}".format(flr_options))
            if self.hvobj.VMs[vm].machine.os_info.lower() != "windows":
                if any('TYPE="btrfs"' in _mounts for _mounts in _source_blk_id):
                    return flr_options, btrfs_drive_list, True
                else:
                    return flr_options, None, None
            else:
                return flr_options, None, None
        except Exception as err:
            self.log.exception(
                "An exception occurred in getting file level source path: {0}".format(err))
            raise err

    def get_browse_time(self, media_agent, subclient_id, copy_precedence, vm_id, reg_key=True):
        """"
        Gets the browse time took to show drive letters during guest file browse

        Args:

            media_agent  (str)     -    Mediaagent name used for browse

            subclient_id  (int)    -    Id of the subclient

            copy_precedence (int) -     copy id

            vm_id (int)           -     VM guid

            reg_key (bool)       -     Reg key bEnablePerDiskMountForLiveBrowse True by default

        Raise:
              Exception:

                If unable to browse

        """
        try:
            vmobj = Machine(media_agent, self.auto_commcell.commcell)
            val = vmobj.get_registry_value('VirtualServer', 'bEnablePerDiskMountForLiveBrowses')
            if reg_key == True:
                if val != 1:
                    vmobj.update_registry('VirtualServer', 'bEnablePerDiskMountForLiveBrowse', 1, reg_type='DWord')
            else:
                vmobj.update_registry('VirtualServer', 'bEnablePerDiskMountForLiveBrowse', 0, reg_type='DWord')
            virtual_server_dict = {'show_deleted': False,
                       'restore_index': True,
                       'vm_disk_browse': False,
                       'from_time': 0, 'to_time': 0,
                       'copy_precedence': copy_precedence,
                       'path': '\\' + vm_id,
                       'vs_file_browse': True, 'media_agent': media_agent,
                       '_subclient_id': subclient_id, 'retry_count': 0}
            begin = time.time()
            self.auto_vsa_backupset.backupset._do_browse(virtual_server_dict)
            end = time.time()
            vmobj.update_registry('VirtualServer', 'nBackupIdleCleanupInterval', 10, reg_type='DWord')
            browsetime = end - begin
            self.log.info('Successfully got browse time and set back key to enable if disable')
            vmobj.update_registry('VirtualServer', 'bEnablePerDiskMountForLiveBrowse', 1, reg_type='DWord')
            return (browsetime)
        except Exception as err:
            self.log.exception(
                "Exception while getting browse time" + str(err))
            raise err

    def validate_backup_pref_time(self, backup_job_id, proxy):
        """"
        Validates backup performance against disk collection

        Args:
            backup_job_id  (str)     -    backup job id
            proxy          (str)     -    proxy name machine
        Returns:
            Percent       (float)    -    disk collection time percentage against total job time
        Raise:
              Exception:
                If unable to validate backup performance
        """
        try:
            vmobj = Machine(proxy, self.auto_commcell.commcell)
            final_time = []
            servtime = ['servEndDate', 'servStartDate']
            for eachtime in servtime:
                query = "select " + eachtime + " from JMBkpStats where jobid = " \
                        "(select childjobid from JMJobDataLink where parentjobid = " + backup_job_id + " and linkType = 7)"
                self.csdb.execute(query)
                queryoutput = self.csdb.fetch_all_rows()
                final_time.append(queryoutput[0][0])
            tol = int(final_time[0]) - int(final_time[1])
            self.log.info("Time took for child job to complete" + str(tol))
            log_file_name = ("vsbkp.log")
            search_term = 'Total time to collect VM disk/volume information'
            disktime = vmobj.get_logs_for_job_from_file(backup_job_id, log_file_name, search_term)
            if disktime == None:
                self.log.info("disk collection took less than 15 Secs")
            else:
                disk_fintime = disktime.split('] seconds')[-2].split('[')[-1]
                self.log.info("Time took for disk collection" + str(disk_fintime))
                if float(disk_fintime) < float(60):
                    self.log.info("Time took for disk collection is under 1 min")
                else:
                    percent = float(disk_fintime) / float(tol) * 100
                    if percent <= float(5):
                        self.log.info("Disk collection performance %s which is under 5 percent" % str(round(percent, 2)))
                    else:
                        raise Exception("Disk collection performance %s is more than 5 percent" % str(round(percent, 2)))
                    return percent
        except Exception as err:
            self.log.exception(
                "Exception while validating backup performance" + str(err))
            raise err

    def file_level_validation(self, flr_options, drive_list=None, special_vm_drive=None, problematic_vm_drive=None,
                              **kwargs):
        """

        Args:
            flr_options                         (dict):     Options needed to be used during file level
                                                            restore

            drive_list                          (dict) :    Dict of drives for the vm

            special_vm_drive                    (string):   Drive where more data is copied

            problematic_vm_drive            (string):   Drive which has the problematic data

            **kwargs                            :   Arbitrary keyword arguments

        Raises:
            Exception:
                If it fails in performing file level validation

        """

        try:
            if self.auto_vsaclient.isIndexingV2 and kwargs.get('multi_stream'):
                self.auto_commcell.multi_stream_restore(kwargs.get('rest_job_id'))
            fs_restore_options = flr_options['fs_restore_options']
            vm = flr_options['vm']
            if not drive_list:
                drive_list = self.hvobj.VMs[vm].drive_list
            if self.hvobj.VMs[
                vm].machine.os_info.lower() != 'windows' and not self.backup_option.collect_metadata:
                try:
                    _restore_dest = flr_options['dest_machine'].get_folders_in_path(
                        self.fs_restore_dest, recurse=False)
                    if flr_options['dest_machine'].os_info.lower() != 'windows':
                        _restore_dest = _restore_dest[1:]
                    if not _restore_dest or len(_restore_dest) != 1:
                        raise Exception
                    else:
                        _restore_dest = _restore_dest[0]
                except Exception as err:
                    self.log.exception(
                        "Error in Destination location. Multiple/No folders in {}. please check and rerun".format(
                            self.fs_restore_dest))
                    raise err
            else:
                _restore_dest = self.fs_restore_dest
            if self.hvobj.VMs[vm].machine.os_info.lower() == "windows" and flr_options['_preserve_level'] > 4:
                _restore_dest = flr_options['dest_machine'].join_path(_restore_dest, self.hvobj.VMs[vm].guid)
            self.log.info("Restore destination: {}".format(_restore_dest))
            self.sleep_timer = 720
            for label, _drive in drive_list.items():
                if fs_restore_options.browse_from_snap \
                        and self.hvobj.VMs[vm].machine.os_info.lower() == "windows":
                    label = flr_options['_path_dict'][label]
                self.log.info("Validating {0} of vm: {1}".format(_drive, vm))
                if self.hvobj.VMs[vm].machine.os_info.lower() != "windows":
                    label = label.strip().split("/", 1)[-10:][1].split("/") if label.startswith(
                        '/') else label.strip().split("/")[-10:]
                    label = (flr_options['dest_machine'].join_path(*label)).strip("\\")
                _restore_folder = flr_options['dest_machine'].join_path(_restore_dest,
                                                                        label) if _drive != '/' else _restore_dest
                _restore_folder = flr_options['dest_machine'].join_path(_restore_dest,
                                                                        label) if _drive != '/' else _restore_dest
                _final_restore_path = flr_options['dest_machine'].join_path(_restore_folder, self.backup_folder_name,
                                                                            "TestData",
                                                                            self.timestamp)
                self.log.info('Validation on drive: {}, final restore folder: {}'.format(_drive, _final_restore_path))
                self.fs_testdata_validation(
                    flr_options['dest_machine'],
                    flr_options['dest_machine'].join_path(_restore_folder, self.backup_folder_name,
                                                          "TestData",
                                                          self.timestamp))
                million_files_path = kwargs.get('million_files_path')
                million_files_drive = None
                if million_files_path:
                    if self.hvobj.VMs[vm].machine.os_info.lower() == "windows":
                        million_files_path_folders = million_files_path.split(self.hvobj.VMs[vm].machine.os_sep)
                        million_files_drive = million_files_path_folders[0]
                    else:
                        million_files_drive = \
                            self.hvobj.VMs[vm].machine.execute_command(f'df -h {million_files_path}').formatted_output[
                                1][5]
                if special_vm_drive or problematic_vm_drive or million_files_path:
                    if special_vm_drive == _drive:
                        special_path = self.testdata_path + "special_testdata"
                        dest_path = flr_options['dest_machine'].join_path(
                            _restore_folder, "special_testdata",
                            "TestData", self.timestamp + "special_testdata")
                        self.log.info("Verifying testdata for huge size source:{0}, Destination: {1}".
                                      format(special_path, dest_path))
                        self.auto_vsaclient.fs_testdata_validation(
                            flr_options['dest_machine'], special_path, dest_path, self.controller_machine)
                    elif problematic_vm_drive == _drive and self.hvobj.VMs[vm].machine.os_info.lower() == "windows":
                        problematic_path = self.testdata_path + "problematic_testdata"
                        dest_path = flr_options['dest_machine'].join_path(
                            _restore_folder, "problematic_testdata",
                            "TestData", self.timestamp + "problematic_testdata")
                        self.log.info("Verifying problematic testdata for source:{0}, Destination: {1}".
                                      format(problematic_path, dest_path))
                        self.auto_vsaclient.fs_testdata_validation(
                            flr_options['dest_machine'], problematic_path, dest_path, self.controller_machine)
                    elif million_files_drive == _drive:
                        source_machine = self.hvobj.VMs[vm].machine
                        dest_machine = flr_options['dest_machine']
                        if self.hvobj.VMs[vm].machine.os_info.lower() == "windows":
                            _folder_path = f"{dest_machine.os_sep}".join(
                                million_files_path.split("\\")[1:])
                            cmd = 'Get-ChildItem -Path {} | Get-Random -Count 10 | Select-Object -ExpandProperty Name'. \
                                format(million_files_path)
                        else:
                            _folder_path = f"{dest_machine.os_sep}".join(
                                million_files_path[len(_drive) + 1:].split("/"))
                            cmd = 'find {} -maxdepth 1 -type f | shuf -n 10 | xargs -n 1 basename'.format(million_files_path)
                        dest_path = dest_machine.join_path(_restore_folder, _folder_path)
                        self.log.info("Verifying random files out of million files for source:{0}, Destination: {1}".
                                      format(million_files_path, dest_path))
                        # Select 10 random files out of million files for checksum validation
                        validation_files = source_machine.execute_command(cmd).output.splitlines()
                        self.log.info('Files selected for checksum validation: {}'.format(validation_files))
                        source_hash_values = []
                        dest_hash_values = []
                        for file in validation_files:
                            source_hash_values.append(
                                source_machine._get_file_hash(source_machine.join_path(million_files_path, file)))
                            dest_hash_values.append(
                                dest_machine._get_file_hash(dest_machine.join_path(dest_path, file)))
                        self.log.info('Source Hash : {}'.format(source_hash_values))
                        self.log.info('Destination Hash : {}'.format(dest_hash_values))
                        mismatch_files = []
                        for idx, src_hash in enumerate(source_hash_values):
                            diff = (src_hash == dest_hash_values[idx])
                            if not diff:
                                mismatch_files.append(validation_files[idx])
                        if mismatch_files:
                            raise Exception("Checksum mismatched for files {}.".format(mismatch_files))
                        else:
                            self.log.info("Checksum validation completed successfully for million files")
            if not fs_restore_options.skip_block_level_validation and not fs_restore_options.metadata_collected and not fs_restore_options.browse_from_snap:
                if self.hvobj.VMs[vm].machine.os_info.lower() == "windows":
                    if self.controller_machine.os_info.lower() != 'windows':
                        self.log.info("Skipping the block level validation for Unix controller. "
                                      "Cross OS executable generation not supported. Support will be added. "
                                      "Sleeping for 12 minutes")
                        time.sleep(self.sleep_timer)
                    elif self.ma_machine.os_info.lower() == "windows" or fs_restore_options.is_ma_specified:
                        self.block_level_validation(vm, fs_restore_options._browse_ma_client_name,
                                                    job_time_end=kwargs.get('job_time_end', None),
                                                    cleanup_time=fs_restore_options.cleanup_time)
                    else:
                        _dest_machine = Machine(fs_restore_options.destination_client,
                                                self.auto_commcell.commcell)
                        if _dest_machine.os_info.lower() == "windows":
                            self.log.info("Browse is done in Windows Proxy. Pseudomount validation "
                                          "will be done on {}".format(
                                fs_restore_options.destination_client))
                            self.block_level_validation(vm, fs_restore_options.destination_client,
                                                        job_time_end=kwargs.get('job_time_end', None),
                                                        cleanup_time=fs_restore_options.cleanup_time)
                        else:
                            _cs_machine = Machine(self.auto_commcell.commcell.commserv_name,
                                                  self.auto_commcell.commcell)
                            if _cs_machine.check_registry_exists("VirtualServer", "bEnableCSForVSALiveBrowse"):
                                self.log.info("Browse must be done on CS so skipping Pseudomount validation"
                                              "please pass the Windows MA in the JSON input if "
                                              "validation is required. sleeping for 12 minutes")
                                time.sleep(self.sleep_timer)
                            elif _cs_machine.check_registry_exists("VirtualServer", "bEnableNTFSLiveBrowseInLinuxMA"):
                                self.log.info("Browse must be done on FREL so skipping Pseudomount validation"
                                              "please pass the Windows MA in the JSON input if "
                                              "validation is required. sleeping for 12 minutes")
                                time.sleep(self.sleep_timer)
                            else:
                                self.block_level_validation(vm, fs_restore_options._browse_ma_client_name,
                                                            job_time_end=kwargs.get('job_time_end', None),
                                                            cleanup_time=fs_restore_options.cleanup_time)

            elif fs_restore_options.skip_block_level_validation and not fs_restore_options.browse_from_snap:
                self.log.info("Sleeping for 5 minutes")
                time.sleep(300)

            # vmware live file cleanup validation
            if fs_restore_options.browse_from_snap:
                if self.hvobj.instance_type == hypervisor_type.VIRTUAL_CENTER.value.lower():
                    self.vmware_live_browse_validation(
                        vm, self.backup_job.job_id, self.backupcopy_job_id, fs_restore_options,
                        fs_restore_options.copy_precedence)
                else:
                    self.log.info("Sleeping for 12 minutes for the snap to unmount")
                    time.sleep(self.sleep_timer)
        except Exception as err:
            self.log.exception("An exception occurred in doing file level validation {0}".format(err))
            raise err

    def get_mount_point_from_uuid(self, vm, uuid):
        """
        Returns the mount point corresponding to UUID for the VM

        Args:
            vm      (string):   VM name
            uuid    (string):   Device UUID

        Returns:
            Mount point string
        """
        disks = self.hvobj.VMs[vm].machine.execute('lsblk -o UUID,MOUNTPOINT').formatted_output
        for disk in disks:
            try:
                if disk[0] == uuid:
                    return disk[1]
            except IndexError:
                pass
        raise Exception("Failed to find mount point for UUID {}".format(uuid))

    def manage_btrfs_uuid(self, _fs_path_to_browse_list, fs_restore_options, _source_blk_id, vm,
                          btrfs_drive_list):
        """
        Manages the path for btrfs uuid as per the FBR MA
        Args:
            _fs_path_to_browse_list             (list) :    Restore path list

            fs_restore_options                  (object):   FS restore object

            _source_blk_id                        (list):    source vm's blkid list

            vm                                  (string):   Source vm name

            btrfs_drive_list                      (dict):   Drive list for modification if source
                                                            VM has btrfs fs

        Returns:
            _fs_path_to_browse_list             (list) :    Restore path list

            btrfs_drive_list                    (dict) :    Modified drive list

        """
        try:
            btrfs_mount_ids = {}
            for _disks in _source_blk_id:
                if 'TYPE="btrfs"' in _disks:
                    btrfs_mount_ids[[s for i, s in enumerate(_disks) if 'UUID_SUB=' in s][0]] = \
                        [s for i, s in enumerate(_disks) if 'UUID=' in s][0]
            btrfs_mount_uuid_sub = [*btrfs_mount_ids]

            _temp_vm, _temp_vmid = self.subclient._get_vm_ids_and_names_dict_from_browse()
            _browse_request = self.subclient.guest_files_browse(_temp_vmid[vm],
                                                                media_agent=fs_restore_options.browse_ma if
                                                                fs_restore_options.is_ma_specified else "",
                                                                copy_precedence=fs_restore_options.copy_precedence)
            if fs_restore_options.fbr_ma:
                _fbr = fs_restore_options.fbr_ma
            else:
                _fbr = self.auto_vsainstance.fbr_ma
            _fbr_obj = Machine(_fbr, self.auto_commcell.commcell)
            _fbr_output = _fbr_obj.execute_command('blkid')
            _fbr_output = _fbr_output.formatted_output
            for _disks in _fbr_output:
                if [s for s in sorted(set(_disks)) if s.startswith("LABEL=")]:
                    old_uuid = None
                    new_uuid = None
                    for drive in _disks:
                        if 'boot' in drive.lower():
                            break
                        if drive.startswith("LABEL="):
                            old_uuid = '-'.join(drive.split('_')[1].split('-')[1:]).split('"')[0]
                        if drive.startswith("UUID="):
                            new_uuid = drive.split('=')[1].lstrip('"').rstrip('"')
                    matching_entries = [(k, v) for k, v in btrfs_drive_list.items() if
                                        old_uuid and k.__contains__(self.get_mount_point_from_uuid(vm, old_uuid))]
                    for disk in matching_entries:
                        btrfs_drive_list.__delitem__(disk[0])
                        new_val = '/cvlostandfound/' + new_uuid
                        btrfs_drive_list[new_val] = disk[1]
                    self.log.info(btrfs_drive_list)
                if set(_disks).intersection(btrfs_mount_uuid_sub):
                    uuid_sub = \
                        [(s.split('=')[1]).strip('\"') for i, s in enumerate(_disks) if
                         'UUID_SUB=' in s][0]
                    uuid_source = btrfs_mount_ids['UUID_SUB="' + uuid_sub + '"'].split('=')[1].strip(
                        '\"')
                    uuid_fbr = \
                        [(s.split('=')[1]).strip('\"') for i, s in enumerate(_disks) if 'UUID=' in s][0]
                    mount_point = self.get_mount_point_from_uuid(vm, uuid_source)
                    _path = [s for s in _fs_path_to_browse_list if mount_point in s]
                    _new_path = []
                    for s in _path: _new_path.append('/cvlostandfound/' + uuid_fbr + s.split(mount_point)[1])
                    for s in _path: _fs_path_to_browse_list.remove(s)
                    for s in _new_path: _fs_path_to_browse_list.append(s)

                    btrfs_mount_uuid_sub.remove('UUID_SUB="' + uuid_sub + '"')

            return _fs_path_to_browse_list, btrfs_drive_list
        except Exception as err:
            self.log.exception("Failed in changing path for btrfs")
            raise err

    def block_level_clean_registry(self, cleanup_time: int = 0):
        """
        Sets and removes the registry on the media agent for the cleanup
        Args:

            cleanup_time            (int)   :   cleanup time in seconds

        Raises:
            Exception:
                When block level validation fails

        """
        try:
            if cleanup_time != 0:
                if self.ma_machine.check_registry_exists('VirtualServer', 'nBackupIdleCleanupInterval'):
                    self.ma_machine.update_registry('VirtualServer', 'nBackupIdleCleanupInterval', cleanup_time)
                else:
                    self.ma_machine.create_registry('VirtualServer', 'nBackupIdleCleanupInterval', cleanup_time,
                                                    'DWord')
            else:
                if self.ma_machine.check_registry_exists('VirtualServer', 'nBackupIdleCleanupInterval'):
                    self.ma_machine.remove_registry('VirtualServer', 'nBackupIdleCleanupInterval')
        except Exception as err:
            self.log.exception("Failed in setting/modifying/removing registry for block level cleanup time")
            raise err

    def block_level_cleanup_check(self, os_type: str, cleanup_path: str, cleanup_time: int, **kwargs):
        """
        Cleanup check after block level browse
        Args:
            os_type                         (str): type of os

            cleanup_path                    (str):  live browse cleanup path

            cleanup_time                    (int): cleanup time in seconds

            **kwargs                        (dict):  extra argument
                                            eg: adr_id

        Raises:
            Exception:
                When block level cleanup check fails

        """
        try:
            if os_type == 'windows':
                all_paths = self.ma_machine.get_folders_in_path(
                    self.ma_machine.os_sep.join(cleanup_path.split(self.ma_machine.os_sep)[:-1]), False)
                cleanup_paths = [i for i in all_paths if cleanup_path in i]
            else:
                cleanup_paths = [cleanup_path]
            self.log.info("Live browse mount paths: " + str(cleanup_paths))
            cleanup_wait_time = cleanup_time/2
            adr_id = kwargs.get('adr_id', None)
            if cleanup_time > cleanup_wait_time:
                VirtualServerUtils.wait_for_timer(int(cleanup_wait_time))
                cleanup_time -= cleanup_wait_time
                self.log.info("checking if the mounted path still exists")
                for c_path in cleanup_paths:
                    if self.ma_machine.check_directory_exists(c_path):
                        files_in_path = self.ma_machine.get_folders_in_path(c_path, recurse=False)
                        if os_type.lower() == 'windows':
                            files_test = files_in_path
                        else:
                            files_test = adr_id in str(files_in_path)
                        if not files_test:
                            self.log.info(f"files are cleaned before timeout time {c_path}")
                            raise Exception("Staging Path CleanUp happened before time timeout")
                    else:
                        self.log.info(f"Folder is deleted before timeout time {c_path}")
                        raise Exception("Staging Path CleanUp happened before time timeout")
            if cleanup_time > 0:
                self.log.info(
                    "sleeping for another {} seconds and then cleanup will be validated".format(
                        cleanup_time))
                VirtualServerUtils.wait_for_timer(cleanup_time)
            for c_path in cleanup_paths:
                if self.ma_machine.check_directory_exists(c_path):
                    files_in_path = self.ma_machine.get_folders_in_path(c_path, recurse=False)
                    if os_type.lower() == 'windows':
                        files_test = files_in_path
                    else:
                        files_test = adr_id in str(files_in_path)
                    if files_test:
                        self.log.info(f"Not all files are cleaned after Live browse, "
                                      f"please check the folder: {c_path}")
                        raise Exception("Staging Path CleanUp Failed")
                    else:
                        self.log.info(f"Staging Path: {c_path} was cleaned successfully")
                else:
                    self.log.info(
                        f"Staging Path was cleaned successfully along with the mount path "
                        f"directory: {c_path}")
        except Exception as err:
            self.log.exception("Failed in performing Block Level cleanup check")
            raise err

    def block_level_validation(self, _vm, browse_ma, **kwargs):
        """
        Performs Windows Block level validation

        Args:

            _vm                                     (str):  backup Vm for which guest level
                                                            restore is performed

            browse_ma                               (str):  Ma used for guest file restore
                                                            browse

            **kwargs                            :   Arbitrary keyword arguments

        Raises:
            Exception:
                When block level validation fails
        """

        try:
            _browse_ma_jr_dir = self.auto_commcell.get_job_results_dir(browse_ma)
            if self.hvobj.VMs[_vm].guest_os.lower() == "windows":
                cleanup_time = kwargs.get('cleanup_time', 0) * 60
                if cleanup_time == 0:
                    cleanup_time = 1920
                else:
                    cleanup_time += 120
                if kwargs.get('job_time_end'):
                    time_diff = int(time.time() - kwargs.get('job_time_end'))
                    if time_diff >= cleanup_time:
                        cleanup_time = 0
                        self.log.info(
                            "{} seconds passed since job completion. will only check for folders cleanup".format(
                                cleanup_time))
                    else:
                        cleanup_time -= time_diff
                self.log.info("total cleanup wait time: {}".format(cleanup_time))
                if self.ma_machine.os_info.lower() == "windows":
                    live_browse_mount_path = VirtualServerConstants.get_live_browse_mount_path(
                        _browse_ma_jr_dir,
                        self.hvobj.VMs[_vm].guid,
                        self.ma_machine.os_info)
                    self.block_level_cleanup_check('windows', live_browse_mount_path, cleanup_time)
                else:  # linux MA
                    client_ = Client(self.auto_commcell.commcell, self.ma_machine.machine_name)
                    job_res_directory = client_.job_results_directory
                    self.log.info("Job result directory: " + job_res_directory)
                    self.log.info("Navigate to the Proxy's Job Results directory to read Live browse xml "
                                  "file for VM " + _vm)
                    vm_dict = {}
                    for vm_element in self.vm_content:
                        if vm_element["path"] == _vm or vm_element["display_name"] == _vm:
                            vm_dict = vm_element
                            break
                    adr_file_path = self.ma_machine.join_path(job_res_directory,
                                                              (str(vm_dict["id"]) + "*LiveBrowse.xml"))
                    self.log.info("ADR file path: " + adr_file_path)
                    adr_content = self.ma_machine.read_file(adr_file_path)
                    match = re.search('''fbrRequestId="(\d*)"''', adr_content)
                    adr_id = re.sub(re.compile('\D'), '', match.group())
                    live_browse_mount_path = VirtualServerConstants.get_linux_live_browse_mount_path(
                        self.ma_machine, adr_id)
                    self.block_level_cleanup_check('unix', live_browse_mount_path, cleanup_time, adr_id=adr_id)
                self.block_level_clean_registry()
            else:
                self.log.info("Skipping the block level validation because Backup vm is a linux machine")
            self.log.info("performing Post un-mount validation")
            if self.ma_machine.os_info.lower() == "windows":
                self.disk_unmount_validation(_vm)
            else:
                self.disk_unmount_validation(_vm, adr_id)
        except Exception as err:
            self.log.exception("Failed in performing Block Level Validation")
            raise err

    def fs_testdata_validation(self, dest_client, dest_location, no_ip=False):
        """
        Does Validation of Backed up and data restored from file level

        Args:
                dest_client     (obj)   -   Machine class object of Destination client

                dest_location   (str)   - destination location of file level restore job

                no_ip           (bool)  - Destination vm's validation is via IP or not

        Exception
                if folder comparison fails


        """

        if no_ip:
            _source_hash = self.controller_machine.get_folder_hash(self.testdata_path)
            _desh_hash = dest_client.calculate_hash_no_ip(dest_location)
            difference = _source_hash - _desh_hash
            self.log.info("Difference : {0}".format(difference))
            if difference:
                self.log.info("checksum mismatched for files {0}".format(difference))
                raise Exception(
                    "Folder Comparison Failed for Source: {0} and destination: {1}".format(
                        self.testdata_path, dest_location))
            self.log.info("Validation completed successfully")
        else:
            self.auto_vsaclient.fs_testdata_validation(dest_client=dest_client,
                                                       source_location=self.testdata_path,
                                                       dest_location=dest_location,
                                                       controller_machine=self.controller_machine)

    def disk_restore(self, disk_restore_options, _skip_validation=False, discovered_client=None, **kwargs):
        """

        perform Disk restore for specific subclinet

        Args:
                disk_restore_options    (object):   represent options that need to be set
                                                    while performing disk  restore

                _skip_validation        (bool): Set to true to skip disk validation

                discovered_client       (string):   Pass the discovered client name if restore has to be performed from
                                                    discovered client.

                **kwargs                         : Arbitrary keyword arguments

        Exception:
                        if job fails
                        if validation fails

        """
        try:
            if kwargs.get('msg'):
                VirtualServerUtils.decorative_log(kwargs.get('msg'))
            if discovered_client:
                temp_vmlist = [discovered_client]
                VirtualServerUtils.discovered_client_initialize(self, discovered_client)
            else:
                temp_vmlist = self.vm_list
            for _vm in temp_vmlist:

                dest_client = Machine(machine_name=disk_restore_options.destination_client,
                                      commcell_object=self.auto_commcell.commcell)
                self.disk_restore_dest = self.restore_path(disk_restore_options, _vm)

                # """
                disk_restore_job = self.subclient.disk_restore(
                    _vm, proxy_client=disk_restore_options.destination_client,
                    destination_path=self.disk_restore_dest,
                    copy_precedence=disk_restore_options.copy_precedence,
                    media_agent=disk_restore_options.disk_browse_ma,
                    snap_proxy=disk_restore_options.snap_proxy)

                self.log.info("Started Disk Restore job {0}".format(
                    disk_restore_job.job_id))

                if not disk_restore_job.wait_for_completion():
                    raise Exception(
                        "Failed to run disk level restore job {0} with error:{1}".format(
                            disk_restore_job.job_id, disk_restore_job.delay_reason))
                self.log.info("Disk restore job completed successfully with job id {0}".format(
                    disk_restore_job.job_id))
                # """
                if self.hvobj.VMs[_vm].guest_os.lower() == "windows":
                    # Commenting out validation for vmware disk level restore for now
                    if not self.hvobj.instance_type == hypervisor_type.VIRTUAL_CENTER.value.lower() and \
                            self.backup_option.validation:
                        _vm_disk_list = self.hvobj.VMs[_vm].disk_list
                        for each_disk in _vm_disk_list:
                            if True in list(map(each_disk.__contains__,
                                                [".avhdx", ".avhd", ".AVHDX", ".AVDH"])):
                                self.log.info("Skipping validation as there are snapsots in VM")
                                _skip_validation = True
                                break

                        if not _skip_validation:
                            self.disk_validation(
                                self.hvobj.VMs[_vm],
                                disk_restore_options._destination_pseudo_client,
                                self.disk_restore_dest,
                                disk_restore_options.client_machine)

                if disk_restore_options.is_part_of_thread:
                    _files_in_path = dest_client.get_files_in_path(self.disk_restore_dest, recurse=False)
                    for _file in _files_in_path:
                        self.log.info("Deleting file {}".format(_file))
                        dest_client.delete_file(_file)
                else:
                    self.log.info("Deleting Folder {}".format(self.disk_restore_dest))
                    dest_client.remove_directory(self.disk_restore_dest)

        except Exception as err:
            self.log.exception("Exception occurred please check logs")
            raise Exception("Disk Restore Job failed, please check agent logs {0}".format(err))

    def disk_validation(
            self,
            vm_obj,
            destination_client_name,
            disk_restore_destination,
            dest_machine):
        """
        Performs Disk Validation by mounting the restored disk on the Host

        Args:

        _vm                     (str)   - object of VMHelper class

        destination_client_name    (str)   - Pseudo  client name of the destination client

        disk_restore_destination    (str)   - restore path of all the disk

        dest_machine    (obj) - destimation client where disk restores are performed

        Exception:
                        if job fails
                        if validation fails

        """
        try:

            self.log.info("Performed Restore in client %s" %
                          destination_client_name)
            dest_client_hypervisor = self.auto_vsainstance._create_hypervisor_object(
                destination_client_name)

            _list_of_disks = dest_client_hypervisor.get_disk_in_the_path(disk_restore_destination,
                                                                         dest_machine)

            _vm_disk_list = vm_obj.disk_list
            if not _vm_disk_list:
                self.log.info(
                    "Cannot validate the Disk as we cannot find the disk attached to the VM")
                return False

            if not ((_list_of_disks is None) or (_list_of_disks == [])):
                _final_mount_disk_list = []
                for each_disk in _vm_disk_list:
                    each_disk_name = os.path.basename(each_disk).split(".")[0]
                    for disk_path in _list_of_disks:
                        if each_disk_name.lower() in disk_path.lower():
                            _final_mount_disk_list.append(disk_path)

            else:
                self.log.info(
                    "the Disk cannot be validated as we cannot find disk with Hypervisor extension,\
                                                                could be converted disk")
                return False

            if not _final_mount_disk_list:
                _final_mount_disk_list = _list_of_disks

            for _file in _final_mount_disk_list:

                _file = disk_restore_destination + "\\" + _file
                self.log.info("Validation Started For Disk :[%s]" % _file)
                _drive_letter = dest_client_hypervisor.mount_disk(vm_obj, _file, dest_machine)
                if _drive_letter != -1:
                    for each_drive in _drive_letter:
                        dest_folder_path = VirtualServerConstants.get_folder_to_be_compared(
                            self.backup_folder_name, each_drive, self.timestamp)
                        self.log.info("Folder comparison started...")
                        time.sleep(5)
                        self.fs_testdata_validation(
                            dest_machine, dest_folder_path)
                else:
                    self.log.error("ERROR - Error mounting VMDK " + _file)
                    raise Exception("Exception at Mounting Disk ")
                if dest_client_hypervisor.instance_type == hypervisor_type.MS_VIRTUAL_SERVER.value.lower():
                    dest_client_hypervisor.un_mount_disk(vm_obj, _file, dest_machine)
                else:
                    dest_client_hypervisor.un_mount_disk(vm_obj, _file)

        except Exception as err:
            self.log.exception("Exception occurred please check logs")
            if dest_client_hypervisor.instance_type == hypervisor_type.MS_VIRTUAL_SERVER.value.lower():
                dest_client_hypervisor.un_mount_disk(vm_obj, _file, dest_machine)
            else:
                dest_client_hypervisor.un_mount_disk(vm_obj, _file)
            raise err

    def attach_disk_restore(self, attach_disk_restore_options, discovered_client=None, **kwargs):
        """

        perform Attach disk restore for specific subclinet

        Args:
                attach_disk_restore_options    (object):   represent options that need to be set
                                                    while performing attach disk  restore

                discovered_client       (string):   Pass the discovered client name if restore has to be performed from
                                                    discovered client.

                **kwargs                         : Arbitrary keyword arguments

        Exception:
                        if job fails
                        if validation fails

        """
        try:
            if kwargs.get('msg'):
                VirtualServerUtils.decorative_log(kwargs.get('msg'))
            if discovered_client:
                temp_vmlist = [discovered_client]
                VirtualServerUtils.discovered_client_initialize(self, discovered_client)
            else:
                temp_vmlist = self.vm_list
            for _vm in temp_vmlist:
                _before_restore = len(self.hvobj.VMs[_vm].disk_list)
                self.log.info("Number of disk in vm {0} before restore is {1}".
                              format(_vm, _before_restore))

                def vmware(**kwargs_):
                    self.hvobj.VMs[_vm].update_vm_info(force_update=True,
                                                       power_off_unused_vms=self.backup_option.power_off_unused_vms)
                    datastore = self.hvobj.VMs[_vm].datastore
                    disk_restore_job = self.subclient.attach_disk_restore(
                        _vm, vcenter=attach_disk_restore_options.vcenter,
                        proxy_client=attach_disk_restore_options._dest_client_name,
                        esx=self.hvobj.VMs[_vm].esx_host,
                        datastore=datastore,
                        copy_precedence=attach_disk_restore_options.copy_precedence,
                        media_agent=attach_disk_restore_options.disk_browse_ma,
                        snap_proxy=attach_disk_restore_options.snap_proxy)
                    return disk_restore_job

                def amazon(**kwargs_):
                    nonlocal _vm
                    source_vm = _vm
                    _vm = None
                    if not kwargs_.get('new_instance'):
                        _vm = self.vm_restore_prefix + source_vm
                        if not self.hvobj.check_vms_exist(_vm):
                            self.log.error("attach disk restore is run after full vm restore for Amazon")
                            raise Exception("{} is not preset to attach disk".format(_vm))
                        if _vm not in self.hvobj.VMs:
                            self.hvobj.VMs = _vm
                        else:
                            self.hvobj.VMs[_vm].update_vm_info('Basic', force_update=True)
                        if not self.hvobj.VMs[_vm].delete_disks(ignore=True):
                            self.log.exception("Restored disk already present. clean the disks manually")
                            raise Exception("Failed to delete the already present restored disks")
                    else:
                        if self.hvobj.VMs[source_vm].guest_os != 'windows':
                            kwargs_['ami_id'] = kwargs_.get('ami_linux', None)
                        else:
                            kwargs_['ami_id'] = kwargs_.get('ami_win', None)
                        _query = "select simOperatingSystemId from app_client where name='%s'" % (source_vm)
                        self.csdb.execute(_query)
                        _results = self.csdb.fetch_all_rows()
                        if not _results or len(_results) > 1:
                            raise Exception("An exception occurred getting vm's OS ID")
                        kwargs_['os_id'] = int(_results[0][0])
                    disk_restore_job = self.subclient.attach_disk_restore(
                        source_vm,
                        proxy_client=attach_disk_restore_options._dest_client_name,
                        copy_precedence=attach_disk_restore_options.copy_precedence,
                        media_agent=attach_disk_restore_options.disk_browse_ma,
                        destination_vm=_vm,
                        destination_vm_guid=self.hvobj.VMs[_vm].guid if _vm else None,
                        **kwargs_)
                    return disk_restore_job

                hv_dict = {hypervisor_type.VIRTUAL_CENTER.value.lower(): vmware,
                           hypervisor_type.AMAZON_AWS.value.lower(): amazon}

                disk_restore_job = (
                    hv_dict[self.auto_vsainstance.vsa_instance_name.lower()])(**kwargs)

                if disk_restore_job:
                    self.log.info("Disk Restore job started : " + str(disk_restore_job.job_id))
                    if not disk_restore_job.wait_for_completion():
                        raise Exception(
                            "Failed to run disk level restore job {0} with error:{1}".format(
                                disk_restore_job.job_id, disk_restore_job.delay_reason))
                    self.log.info("Attach Disk restore job completed successfully with job id {0}"
                                  .format(disk_restore_job.job_id))
                    self.log.info("Validating the disks count")
                if kwargs.get('new_instance'):
                    try:
                        _vm = self.vm_restore_prefix + _vm
                        self.hvobj.VMs[_vm].update_vm_info('All', True, True)
                        # add more validation
                        # vm is booted
                        if self.hvobj.VMs[_vm].power_state == 16 and len(
                                self.hvobj.VMs[_vm].disk_list) == _before_restore:
                            self.log.info("Validation after attach disk completed")
                        else:
                            self.log.exception("Validation failure after attach disk restore")
                    except Exception as err:
                        self.log.exception("Attach Disk Restore Job as a new instance failed. please check logs")
                    finally:
                        self.log.info("Deleting the restored vm")
                        self.hvobj.VMs[_vm].delete_vm()

                else:
                    _after_restore = len(self.hvobj.VMs[_vm].disk_list)
                    self.log.info("Number of disk in vm {0} After restore is {1}".
                                  format(_vm, _after_restore))
                    if _after_restore / _before_restore == 2:
                        self.log.info("Disk restore validation complete")
                    else:
                        self.log.error("Disk restore validation failed")
                    self.log.info("Deleting the attached disks and updating the disk count")
                    if 'completed' in disk_restore_job.status.lower():
                        if not self.hvobj.VMs[_vm].delete_disks():
                            self.log.exception("Deletion of attached disk failed. clean the disks manually")
                            raise Exception("Failed to delete the disks")

        except Exception as err:
            self.log.exception("Attach Disk Restore Job failed. please check logs")
            raise Exception(
                "Attach Disk Restore Job failed, please check agent logs {0}".format(err))

    def virtual_machine_restore(self, vm_restore_options, discovered_client=None, **kwargs):
        """
        perform Full VM restore for specific subclient

        Args:
                vm_restore_options      (object):   options that need to be set
                                                    while performing vm  restore

                discovered_client       (string):   Pass the discovered client name if restore has to be performed from
                                                    discovered client.

                **kwargs                         : Arbitrary keyword arguments
        Exception:
                        if job fails
                        if validation fails

        """
        try:
            self.vm_restore_prefix = vm_restore_options.vm_restore_prefix
            if kwargs.get('msg'):
                VirtualServerUtils.decorative_log(kwargs.get('msg'))
            vm_to_restore = None
            if discovered_client:
                vm_to_restore = discovered_client
                # VirtualServerUtils.discovered_client_initialize(self, discovered_client)
                vm_restore_obj = self.auto_commcell.commcell.clients.get(discovered_client)
                self.log.info("Performing restore for discovered client {0}".format(vm_to_restore))
            else:
                vm_restore_obj = self.subclient

            if vm_restore_options.in_place_overwrite:
                def hyperv():
                    vm_restore_job = vm_restore_obj.full_vm_restore_in_place(
                        vm_to_restore=vm_to_restore,
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence,
                        add_to_failover=vm_restore_options.register_with_failover,
                        snap_proxy=vm_restore_options.snap_proxy)
                    return vm_restore_job

                def vmware():
                    if self.subclient.is_intelli_snap_enabled:
                        if self.subclient.snapshot_engine_name.lower() == 'virtual server agent snap':
                            self.log.info("Inplace full vm restore is not supported for vvol")
                            return None
                    vm_restore_job = vm_restore_obj.full_vm_restore_in_place(
                        vm_to_restore=vm_to_restore,
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence,
                        to_time=vm_restore_options._end_time,
                        revert=vm_restore_options.revert)
                    return vm_restore_job

                def oraclevm():
                    vm_restore_job = vm_restore_obj.full_vm_restore_in_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        destination_client=vm_restore_options.proxy_client,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                def azureRM():
                    vm_restore_job = vm_restore_obj.full_vm_restore_in_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                def fusion_compute():
                    vm_restore_job = vm_restore_obj.full_vm_restore_in_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        proxy_client=vm_restore_options.proxy_client,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                def azurestack():
                    vm_restore_job = vm_restore_obj.full_vm_restore_in_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                def openstack():
                    vm_restore_job = vm_restore_obj.full_vm_restore_in_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        proxy_client=vm_restore_options.proxy_client,
                        copy_precedence=vm_restore_options.copy_precedence,
                        datastore=vm_restore_options.restoreObj["Datastore"],
                        esx_host=vm_restore_options.restoreObj["esxHost"],
                        esx_server=vm_restore_options.restoreObj["esxServerName"],
                        datacenter=vm_restore_options.restoreObj["Datacenter"],
                        cluster=vm_restore_options.restoreObj["Cluster"])
                    return vm_restore_job

                def red_hat():
                    vm_restore_job = vm_restore_obj.full_vm_restore_in_place(
                        power_on=vm_restore_options.power_on_after_restore,
                        proxy_client=vm_restore_options.proxy_client,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                def amazon():
                    vm_restore_job = vm_restore_obj.full_vm_restore_in_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                def oci():
                    vm_restore_job = vm_restore_obj.full_vm_restore_in_place(
                        source_vm_details=vm_restore_options.source_vm_details,
                        vm_to_restore=vm_restore_options.auto_subclient.vm_list[0],
                        power_on=vm_restore_options.power_on_after_restore,
                        proxy_client=vm_restore_options.proxy_client,
                        copy_precedence=vm_restore_options.copy_precedence,
                        indexing_v2=True)
                    return vm_restore_job

                def nutanix():
                    vm_restore_job = vm_restore_obj.full_vm_restore_in_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                def googlecloud():
                    vm_restore_job = vm_restore_obj.full_vm_restore_in_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        proxy_client=vm_restore_options.proxy_client,
                        copy_precedence=vm_restore_options.copy_precedence,
                        zone=vm_restore_options.zone
                    )
                    return vm_restore_job

                def xen():
                    vm_restore_job = vm_restore_obj.full_vm_restore_in_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                hv_dict = {hypervisor_type.MS_VIRTUAL_SERVER.value.lower(): hyperv,
                           hypervisor_type.VIRTUAL_CENTER.value.lower(): vmware,
                           hypervisor_type.Fusion_Compute.value.lower(): fusion_compute,
                           hypervisor_type.ORACLE_VM.value.lower(): oraclevm,
                           hypervisor_type.AZURE_V2.value.lower(): azureRM,
                           hypervisor_type.Azure_Stack.value.lower(): azurestack,
                           hypervisor_type.OPENSTACK.value.lower(): openstack,
                           hypervisor_type.Rhev.value.lower(): azureRM,
                           hypervisor_type.AMAZON_AWS.value.lower(): amazon,
                           hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.value.lower(): oci,
                           hypervisor_type.Nutanix.value.lower(): nutanix,
                           hypervisor_type.Google_Cloud.value.lower(): googlecloud,
                           hypervisor_type.Xen.value.lower(): xen}
                vm_restore_job = (
                    hv_dict[vm_restore_options.dest_auto_vsa_instance.vsa_instance_name.lower()])()

            else:

                def hyperv():
                    if self.backup_folder_name and self.backup_folder_name not in vm_restore_options.destination_path:
                        vm_restore_dest = os.path.join(vm_restore_options.destination_path,
                                                       self.backup_folder_name)
                    else:
                        vm_restore_dest = vm_restore_options.destination_path
                    vm_restore_options.destination_path = vm_restore_dest
                    vm_restore_job = vm_restore_obj.full_vm_restore_out_of_place(
                        vm_to_restore=vm_to_restore,
                        destination_client=vm_restore_options._destination_pseudo_client,
                        network=vm_restore_options.network,
                        proxy_client=vm_restore_options.proxy_client,
                        destination_path=vm_restore_options.destination_path,
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence,
                        add_to_failover=vm_restore_options.register_with_failover,
                        snap_proxy=vm_restore_options.snap_proxy,
                        media_agent=vm_restore_options.restore_browse_ma
                    )
                    return vm_restore_job

                def fusion_compute():
                    vm_restore_job = vm_restore_obj.full_vm_restore_out_of_place(
                        destination_client=vm_restore_options._destination_pseudo_client,
                        proxy_client=vm_restore_options.proxy_client,
                        datastore=vm_restore_options.datastore,
                        host=vm_restore_options.host,
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                def vmware():
                    vm_restore_job = vm_restore_obj.full_vm_restore_out_of_place(
                        vm_to_restore=vm_to_restore,
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        proxy_client=vm_restore_options.proxy_client,
                        copy_precedence=vm_restore_options.copy_precedence,
                        disk_option=vm_restore_options.disk_option,
                        vcenter_client=vm_restore_options._dest_client_name,
                        datastore=vm_restore_options._datastore,
                        esx_host=vm_restore_options._host[0],
                        source_ip=vm_restore_options.source_ip,
                        destination_ip=vm_restore_options.destination_ip,
                        network=vm_restore_options._network,
                        to_time=vm_restore_options._end_time,
                        revert=vm_restore_options.revert,
                        destComputerName=vm_restore_options.dest_computer_name,
                        volume_level_restore=vm_restore_options.volume_level_restore,
                        delayMigrationMinutes=vm_restore_options.delayMigrationMinutes,
                        redirectWritesToDatastore=vm_restore_options.redirectWritesToDatastore,
                        source_subnet=vm_restore_options.source_subnet if hasattr(
                            vm_restore_options, 'source_subnet') else None,
                        source_gateway=vm_restore_options.source_gateway if hasattr(
                            vm_restore_options, 'source_gateway') else None,
                        destination_subnet=vm_restore_options.destination_subnet if hasattr(
                            vm_restore_options, 'destination_subnet') else None,
                        destination_gateway=vm_restore_options.destination_gateway if hasattr(
                            vm_restore_options, 'destination_gateway') else None)

                    if vm_restore_options.validate_restore_workload:
                        for _vm in self.vm_list:
                            self.restore_validation_options[_vm] = {'host': vm_restore_options._host[0],
                                                                    'datastore': vm_restore_options._datastore}

                    return vm_restore_job

                def azure():
                    vm_restore_job = vm_restore_obj.full_vm_restore_out_of_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence,
                        resource_group=vm_restore_options.Resource_Group,
                        storage_account=vm_restore_options.Storage_account,
                        datacenter=vm_restore_options.datacenter,
                        disk_type=vm_restore_options.disk_type_dict,
                        destination_client=vm_restore_options.destination_client,
                        subnet_id=vm_restore_options.subnet_id,
                        restore_option=vm_restore_options.advanced_restore_options)
                    return vm_restore_job

                def azurestack():
                    vm_restore_job = vm_restore_obj.full_vm_restore_out_of_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence,
                        resource_group=vm_restore_options.Resource_Group,
                        storage_account=vm_restore_options.Storage_account,
                        restore_option=vm_restore_options.advanced_restore_options)
                    return vm_restore_job

                def oraclevm():
                    vm_restore_job = vm_restore_obj.full_vm_restore_out_of_place(
                        virtualization_client=vm_restore_options._destination_pseudo_client,
                        destination_client=vm_restore_options.proxy_client,
                        repository=vm_restore_options.datastore,
                        server=vm_restore_options.host,
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                def openstack():
                    vm_restore_job = vm_restore_obj.full_vm_restore_out_of_place(
                        vm_to_restore=vm_restore_options.auto_subclient.vm_list,
                        power_on=vm_restore_options.power_on_after_restore,
                        destination_client=vm_restore_options._destination_pseudo_client,
                        proxy_client=vm_restore_options.proxy_client,
                        copy_precedence=vm_restore_options.copy_precedence,
                        datastore=vm_restore_options.restoreObj["Datastore"],
                        securityGroups=vm_restore_options.restoreObj["securityGroups"],
                        esx_host=vm_restore_options.restoreObj["esxHost"],
                        esx_server=vm_restore_options.restoreObj["esxServerName"],
                        datacenter=vm_restore_options.restoreObj["Datacenter"],
                        cluster=vm_restore_options.restoreObj["Cluster"])

                    return vm_restore_job

                def red_hat():
                    vm_restore_job = vm_restore_obj.full_vm_restore_out_of_place(
                        power_on=vm_restore_options.power_on_after_restore,
                        destination_client=vm_restore_options._destination_pseudo_client,
                        proxy_client=vm_restore_options.proxy_client,
                        cluster=vm_restore_options.cluster,
                        storage=vm_restore_options.storage,
                        copy_precedence=vm_restore_options.copy_precedence)
                    return vm_restore_job

                def amazon():
                    vm_restore_job = vm_restore_obj.full_vm_restore_out_of_place(
                        vm_to_restore=vm_to_restore,
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        proxy_client=vm_restore_options.proxy_client,
                        copy_precedence=vm_restore_options.copy_precedence,
                        destComputerName=vm_restore_options.dest_computer_name)
                    if vm_restore_options.validate_restore_workload:
                        for _vm in self.vm_list:
                            self.restore_validation_options[_vm] = {
                                'data_center': vm_restore_options.data_center}
                    return vm_restore_job

                def oci():
                    vm_restore_job = vm_restore_obj.full_vm_restore_out_of_place(
                        source_vm_details=vm_restore_options.source_vm_details,
                        vm_to_restore=vm_restore_options.auto_subclient.vm_list[0],
                        new_name=vm_restore_options.new_name,
                        destination_client=vm_restore_options._destination_pseudo_client,
                        proxy_client=vm_restore_options.proxy_client,
                        power_on=vm_restore_options.power_on_after_restore,
                        indexing_v2=True)
                    return vm_restore_job

                def nutanix():
                    vm_restore_job = vm_restore_obj.full_vm_restore_out_of_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        proxy_client=vm_restore_options.proxy_client,
                        copy_precedence=vm_restore_options.copy_precedence,
                        container=vm_restore_options.container,
                        restore_option=vm_restore_options.advanced_restore_options)
                    return vm_restore_job

                def googlecloud():
                    service_account = self.hvobj.get_specified_service_account(vm_restore_options.project_id,
                                                                               vm_restore_options.vm_service_account)
                    vm_restore_job = vm_restore_obj.full_vm_restore_out_of_place(
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        proxy_client=vm_restore_options.proxy_client,
                        copy_precedence=vm_restore_options.copy_precedence,
                        zone=vm_restore_options.zone,
                        project_id=vm_restore_options.project_id,
                        restore_option=vm_restore_options.advanced_restore_options,
                        destination_network=vm_restore_options.destination_network,
                        networks_nic=vm_restore_options.networks_nic,
                        replica_zone=vm_restore_options.replica_zone,
                        subnetwork_nic=vm_restore_options.subnetwork_nic,
                        vmCustomMetadata=vm_restore_options.vm_custom_metadata,
                        createPublicIP=vm_restore_options.create_public_ip,
                        publicIPaddress=vm_restore_options.public_ip_address,
                        privateIPaddress=vm_restore_options.private_ip_address,
                        serviceAccount=service_account
                    )
                    return vm_restore_job

                def xen():
                    vm_restore_job = vm_restore_obj.full_vm_restore_out_of_place(
                        destination_client=vm_restore_options._dest_client_name,
                        overwrite=vm_restore_options.unconditional_overwrite,
                        power_on=vm_restore_options.power_on_after_restore,
                        proxy_client=vm_restore_options.proxy_client,
                        copy_precedence=vm_restore_options.copy_precedence,
                        storage=vm_restore_options.storage,
                        xen_server=vm_restore_options.xen_server)
                    return vm_restore_job

                hv_dict = {hypervisor_type.MS_VIRTUAL_SERVER.value.lower(): hyperv,
                           hypervisor_type.VIRTUAL_CENTER.value.lower(): vmware,
                           hypervisor_type.Fusion_Compute.value.lower(): fusion_compute,
                           hypervisor_type.ORACLE_VM.value.lower(): oraclevm,
                           hypervisor_type.AZURE_V2.value.lower(): azure,
                           hypervisor_type.Azure_Stack.value.lower(): azurestack,
                           hypervisor_type.OPENSTACK.value.lower(): openstack,
                           hypervisor_type.Rhev.value.lower(): red_hat,
                           hypervisor_type.AMAZON_AWS.value.lower(): amazon,
                           hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.value.lower(): oci,
                           hypervisor_type.Nutanix.value.lower(): nutanix,
                           hypervisor_type.Google_Cloud.value.lower(): googlecloud,
                           hypervisor_type.Xen.value.lower(): xen}

                vm_restore_job = (
                    hv_dict[vm_restore_options.dest_auto_vsa_instance.vsa_instance_name.lower()])()

            if vm_restore_job:
                self.restore_proxy_client = vm_restore_options.proxy_client
                if isinstance(vm_restore_job, tuple):
                    self.log.info("Restore job is :{} ".format(vm_restore_job[0].job_id))
                    if not vm_restore_job[0].wait_for_completion():
                        raise Exception("Failed to run VM restore job {0} with error: {1}".format(
                            vm_restore_job[0].job_id, vm_restore_job[0].delay_reason))
                    vm_restore_options.restore_job = vm_restore_job[0]
                else:
                    self.log.info("Restore job is : " + str(vm_restore_job.job_id))
                    if not vm_restore_job.wait_for_completion():
                        raise Exception("Failed to run VM restore job {0} with error: {1}".format(
                            vm_restore_job.job_id, vm_restore_job.delay_reason))
                    vm_restore_options.restore_job = vm_restore_job
                self.log.info("Job Status : {0}".format(vm_restore_options.restore_job.status))
                if 'one or more errors' in vm_restore_job.status:
                    self.log.exception("Restore Job Completed with one or more errors")

                if self.hvobj.instance_type == VirtualServerConstants.hypervisor_type.Google_Cloud.value.lower():
                    self.hvobj.update_hosts()

                if self.backup_option.validation:
                    self.vm_restore_validator(vm_restore_options, discovered_vm=discovered_client)

        except Exception as err:
            self.log.error("Exception while submitting Restore job:" + str(err))
            raise err

    def verify_cbt_restore(self, vm_restore_job_id, restore_proxy):
        """
        Verify that CBT is used during In-Place VM restore
        Args:
            vm_restore_job_id    (string):     job ID of the full vm restore
            restore_proxy        (string):     proxy to do restore
        Raises:
            Exception:
                if any exception when reading log file
        """
        try:
            machine_ = Machine(machine_name=restore_proxy,
                               commcell_object=self.auto_commcell.commcell)
            client_ = Client(self.auto_commcell.commcell, restore_proxy)
            log_directory = client_.log_directory
            self.log.info("Navigate to the Proxy's Log Files directory to read vsrst log")
            vsrst_log = machine_.join_path(log_directory, "vsrst.log")
            self.log.info("Restore Log: %s", vsrst_log)
            log_line = machine_.read_file(vsrst_log, search_term=vm_restore_job_id)
            list_of_lines = log_line.split("\n")
            self.log.info("Looking for the logline that contains seek optimization")
            seek_percentage = -1
            seek_optimization_line = ""
            for line in list_of_lines:
                if "SeekDecisionVMWare::printStats() - Number of restored items skipped by SEEK optimization".lower() \
                        in line.lower():
                    self.log.info("Found Seek Optimization in line: %s", line)
                    seek_optimization_line = line
                    seekline = re.search("[0-9]*\%", line)
                    self.log.info("Seek Line :" + seekline.group())
                    if seekline:
                        seek_percentage = int(seekline.group().split('%')[0])
                        break
            if seek_percentage != -1 and seek_percentage > 0:
                self.log.info("Seek Optimization Validation  Succeeded with Percentage: %s " % str(
                    seek_percentage))
            else:
                raise Exception("Seek Optimization validation failed: %s" % seek_optimization_line)
        except Exception as exp:
            self.log.exception("CBT was not used during Restore: %s", str(exp))
            raise exp

    def verify_crash_consistent_backup(self, job_id, proxy, snap_job=True):
        """
        Verify that crash consistent is being used during the backup
        Args:
            job_id    (string):     job ID of the backup

            proxy        (string):     proxy used for backup

            snap_job    (bool):     Snap backup job or backup copy/streaming job

        Returns:
              bool:         True if log if its crash consistent job else false

        Raises:
            Exception:
                if any exception when reading log file
        """
        _machine = Machine(machine_name=proxy,
                           commcell_object=self.auto_commcell.commcell)
        client_ = Client(self.auto_commcell.commcell, proxy)
        log_directory = client_.log_directory
        self.log.info("Navigate to the Proxy's Log Files directory to read vsbkp log")
        vsbkp_log = _machine.join_path(log_directory, "vsbkp.log")
        self.log.info("Backup Log: %s", vsbkp_log)
        log_line = _machine.read_file(vsbkp_log, search_term=job_id)
        list_of_lines = log_line.split("\n")
        if snap_job:
            _search_string = 'this is crash consistent snap backup'
        else:
            _search_string = 'since the backup was crash consistent'
        self.log.info("Looking for the logline: {}".format(_search_string))
        for line in list_of_lines:
            if _search_string in line.lower():
                self.log.info("Search string found: {}".format(line))
                return True
        self.log.info("Search string not found")
        return False

    def verify_direct_hottadd(self, proxy, job_id, job_type):
        """
        Verify if direct hotadd was used during the job

        Args:

            proxy                       (string):   Proxy client used during the job

            job_id                      (int):      Job Id

            job_type                    (string):   Backup or resotre job

        Returns:

        """

        try:
            _log_file = eval('VirtualServerConstants.LogFilesMapper.{}.value'.format(job_type))
            search_term = 'Opening direct hotadd disk handle'
            if not VirtualServerUtils.find_log_lines(cs=self.auto_commcell.commcell, client_name=proxy,
                                                     log_file=_log_file, search_term=search_term, job_id=job_id)[0]:
                self.log.error('Job was not run using direct hotadd mode')
                return False
            return True
        except Exception as exp:
            self.log.exception("job was not run using direct hotadd: %s", str(exp))
            raise exp

    def verify_data_pruned(self, vm_name):
        """
        Args:
            vm_name         (str): VM that gets checked if data is pruned
        Raises:
            Exception
                if there's any exception while accessing VM's directory
        """
        try:
            for each_drive in self.source_obj.drive_list:
                dest_location = self.source_obj.machine.join_path(
                    self.source_obj.drive_list[each_drive],
                    "Differential")
                self.log.info("Destination Location: %s" % dest_location)
                if self.hvobj.VMs[vm_name].machine.check_directory_exists(dest_location):
                    raise Exception(
                        "Data copied after backup was not deleted after doing Full VM In-Place Restore")
                else:
                    self.log.info("Data copied after backup was successfully pruned.")
        except Exception as ex:
            raise Exception("Exception while validating if data copied after Backup was pruned.")

    def vm_restore_validator(self, vm_restore_options, discovered_vm=None):
        """

        Args:
            vm_restore_options              (str):  options that need to be set while performing vm restore

            discovered_vm                   (string): Restored discovered vm that has to be validated

        Returns:

        """
        try:
            self.log.info("sleeping 4 mintues for the vms to be up")
            time.sleep(240)
            if discovered_vm:
                self.temp_vm_list = [discovered_vm]
            else:
                self.temp_vm_list = self.vm_list
            for vm in self.temp_vm_list:
                if vm_restore_options.in_place_overwrite:
                    restore_vm_name = vm
                else:
                    restore_vm_name = self.vm_restore_prefix + vm
                if vm_restore_options.restore_backup_job is not None:
                    self.vm_restore_validation(vm, restore_vm_name, vm_restore_options, 'Basic')
                else:
                    self.vm_restore_validation(vm, restore_vm_name, vm_restore_options)
        except Exception as err:
            self.log.error("Exception while submitting Restore job:" + str(err))
            raise err

    def vm_restore_validation(self, vm, restore_vm, vm_restore_options, prop='Advanced'):
        """
        Param:
             vm:                     -  Source Vm name
             restore_vm:             -  Restored VM Name
             vm_restore_options      -  options of VM restore options class
             prop                    -  only validate basic or advanced properties
        Exception:
            if validation fails

        """
        try:
            self.vm_restore_prefix = vm_restore_options.vm_restore_prefix
            if vm_restore_options.validate_restore_workload:
                self.log.info("Performing post restore Workload validation")
                self.get_proxies("restore", vm_restore_options=vm_restore_options)
                self.validate_invoked_proxies(vm_restore_options.restore_job.job_id, self.proxy_obj)
                self.get_distribute_workload(vm_restore_options.restore_job.job_id)
                if vm_restore_options.restore_validation_options:
                    restore_validation_options = vm_restore_options.restore_validation_options
                else:
                    restore_validation_options = self.restore_validation_options
                self.hvobj.VMs[vm].compute_distribute_workload(self.proxy_obj,
                                                               vm,
                                                               job_type='restore',
                                                               restore_validation_options=restore_validation_options,
                                                               vm_restore_options=vm_restore_options,
                                                               restore_vm=restore_vm)
                restore_workload_validation = self.VmValidation(self.hvobj.VMs[vm], vm_restore_options)
                restore_workload_validation.vm_workload_validation(self.proxy_obj)
                vm_restore_options.proxy_client = self.hvobj.VMs[vm].proxy_name

            if vm_restore_options.validate_browse_ma_and_cp:
                self.browse_ma_and_cp_validation(vm, RestoreType.FULL_VM.value, vm_restore_options)
                self.log.info(
                    'Browse MA and Copy Validation Passed for MA [{}] and Copy [{}]'.format(
                        vm_restore_options._browse_ma_client_name, vm_restore_options.copy_precedence))

            self.log.info(
                "-----Validating Source VM : {0} and Restore VM : {1}----".format(str(vm), str(restore_vm)))
            vm_restore_options.dest_client_hypervisor.update_hosts()
            if not self.backup_folder_name:
                self.backup_folder_name = vm_restore_options.backup_folder_name
            if not self.testdata_path:
                self.testdata_path = vm_restore_options.testdata_path
                self.timestamp = vm_restore_options.timestamp
                self.testdata_paths.append(self.testdata_path)
            if not self.timestamp:
                self.timestamp = os.path.basename(os.path.normpath(self.testdata_path))
            if vm_restore_options.in_place_overwrite:
                self.log.info("It is Inplace restore")
                self.source_obj = self.__deepcopy__((self.hvobj.VMs[vm]))
            else:
                self.source_obj = self.hvobj.VMs[vm]

            _time_elapsed = 0
            if vm_restore_options.is_part_of_thread:
                while _time_elapsed < 1800:
                    threads = threading.enumerate()
                    try:
                        _find = next(item for item in threads if "attach_disk_restore" in item.name)
                        if _find.is_alive():
                            self.log.info("Attach disk restore is not finished yet."
                                          "Sleeping for 1 minute")
                            time.sleep(60)
                            _time_elapsed += 60
                            self.log.info("Total time elapsed {}".format((_time_elapsed / 60)))
                        else:
                            break
                    except StopIteration:
                        self.log.info("Attach disk restore thread is completed")
                        break

            on_premise = VirtualServerConstants.on_premise_hypervisor(
                vm_restore_options.dest_client_hypervisor.instance_type)

            # Adding floating IP for openstack VM
            if vm_restore_options.dest_auto_vsa_instance.vsa_instance_name == 'openstack':
                self.hvobj.VMs[vm].backup_job = self.backup_job
                if not vm_restore_options.in_place:
                    self.hvobj.OpenStackHandler.projectName = vm_restore_options.restoreObj[
                        'Datacenter']
                    self.hvobj.OpenStackHandler.add_floating_ip(restore_vm)
                    time.sleep(30)
            if vm_restore_options.in_place_overwrite:
                self.hvobj.VMs = restore_vm
            else:
                vm_restore_options.dest_client_hypervisor.VMs = restore_vm
            if vm_restore_options.power_on_after_restore:
                if (
                        vm_restore_options.dest_auto_vsa_instance.vsa_instance_name == hypervisor_type.AZURE_V2.value.lower()
                        and not vm_restore_options.in_place_overwrite):
                    vm_restore_options.dest_client_hypervisor.VMs[
                        restore_vm].resource_group_name = vm_restore_options.Resource_Group
                if not vm_restore_options.in_place_overwrite:
                    self.restore_obj = vm_restore_options.dest_client_hypervisor.VMs[restore_vm]
                else:
                    self.restore_obj = self.hvobj.VMs[restore_vm]
                self.restore_obj.wait_for_vm_to_boot()
                self.restore_obj.update_vm_info(prop="All", os_info=True)

                if self.hvobj.instance_type.lower() == hypervisor_type.VIRTUAL_CENTER.value.lower():
                    if vm_restore_options.is_destination_host_cluster:
                        esx = self.hvobj.get_esx_from_cluster(vm_restore_options.host)
                        if esx != self.restore_obj.esx_host:
                            raise Exception(
                                "VM [{0}] restored to host [{1}]. Host with most amount of free memory [{2}]".format(
                                    vm, self.restore_obj.esx_host, esx))
                        else:
                            self.log.info("VM [{0}] restored to host [{1}] under host cluster [{2}]".format(
                                vm, esx, vm_restore_options.host))

                    if vm_restore_options.is_destination_ds_cluster:
                        ds = self.hvobj.get_datastore_from_cluster(vm_restore_options.datastore)
                        if ds != self.restore_obj.datastore:
                            raise Exception(
                                "VM [{0}] restored to datastore [{1}]. Datastore with most amount of free space [{2}]".
                                format(vm, self.restore_obj.datastore, ds))
                        else:
                            self.log.info("VM [{0}] restored to datastore [{1}] under datastore cluster [{2}]".format(
                                vm, ds, vm_restore_options.datastore))

                    if vm_restore_options.disk_ds_options:
                        restored_disk_ds_map = self.restore_obj.disk_datastore
                        input_disk_ds_map = vm_restore_options.disk_ds_options.get(vm)
                        source_disk_ds_map = self.source_obj.disk_datastore
                        self.log.info(restored_disk_ds_map, input_disk_ds_map, source_disk_ds_map)
                        # Compare base datastore
                        if self.restore_obj.datastore != vm_restore_options.datastore:
                            raise Exception(
                                'Base datastore mismatched - input_datastore [{}] restored_datastore [{}]'
                                .format(vm_restore_options.datastore, self.restore_obj.datastore))
                        # Compare disk datastore
                        for disk, ds in restored_disk_ds_map.items():
                            disk = disk[len(vm_restore_options.vm_restore_prefix):]
                            if disk in input_disk_ds_map:
                                input_ds = input_disk_ds_map[disk]
                            else:
                                input_ds = source_disk_ds_map[disk]
                            if input_ds != ds:
                                raise Exception(
                                    'Disk datastore mismatched - disk [{}] input_datastore [{}] restored_datastore [{}]'
                                    .format(disk, input_ds, ds))
                        self.log.info("Disk to datastore mapping validation completed successfully")
                self.log.info("Disk Details for restored vm are : {}".format(
                    self.restore_obj.disk_dict))
                if (self.hvobj.instance_type.lower() == hypervisor_type.AMAZON_AWS.value.lower() and
                        vm_restore_options.dest_auto_vsa_instance.vsa_instance_name.lower() ==
                        hypervisor_type.AMAZON_AWS.value.lower()):
                    if not vm_restore_options.in_place_overwrite:
                        self.source_obj.validate_name_tag = False
                        self.restore_obj.validate_name_tag = False
                    else:
                        self.source_obj.validate_name_tag = True
                        self.restore_obj.validate_name_tag = True

                if self.hvobj.instance_type.lower() == hypervisor_type.Vcloud.value.lower() and \
                    vm_restore_options.dest_auto_vsa_instance.vsa_instance_name.lower() == \
                        hypervisor_type.VIRTUAL_CENTER.value.lower():
                    
                    # Check that all source controllers are present in restored VM.
                    for src_ctrl in self.source_obj.disk_controller_map.values():
                        if not self.restore_obj.find_scsi_controller(src_ctrl.type):
                            raise Exception("Controller {} not found in restored VM.".format(src_ctrl))
                        else:
                            self.log.info("Controller {} found in restored VM".format(src_ctrl.type))
                    
                    # Check that the disks are attached with the correct configuration on the restored VM.
                    for disk in self.source_obj.disk_config.values():
                        if not self.restore_obj.get_disk_in_controller(disk.config):
                            raise Exception("Disk {} not found in restored VM ".format(disk.config))
                        else:
                            self.log.info("Disk {} found in restored VM".format(disk.config))

                _source = self.VmValidation(self.source_obj, vm_restore_options,
                                            backup_option=self.backup_option)
                _dest = self.VmValidation(self.restore_obj, vm_restore_options,
                                          backup_option=self.backup_option)
                if _source == _dest:
                    self.log.info("Config validation is successful")
                else:
                    self.log.error("Error while configuration validation")
                    raise Exception
                if vm_restore_options.in_place_overwrite and on_premise and \
                        not self.hvobj.instance_type.lower() == hypervisor_type.ORACLE_VM.value.lower():
                    if not self.restore_obj.guid == self.source_obj.guid:
                        raise Exception(
                            "The GUID id of the in place restored VM does not match the source VM")

                if prop == 'Basic':
                    if re.match(VirtualServerConstants.Ip_regex, "%s" % self.restore_obj.ip):
                        raise Exception(
                            "The IP address of the restored VM is not of the proper format"
                            ". Boot validation failed.")
                else:
                    def test_data_validation(no_ip=False):
                        self.log.info("Testdata validation")
                        if self._disk_filter:
                            drive_list = self.restore_obj.drive_list
                        else:
                            drive_list = self.source_obj.drive_list
                        for each_drive in drive_list:
                            dest_location = self.source_obj.machine.join_path(
                                drive_list[each_drive],
                                self.backup_folder_name, "TestData",
                                self.timestamp)
                            self.fs_testdata_validation(
                                self.restore_obj.machine if self.restore_obj.machine else self.restore_obj,
                                dest_location, no_ip)

                    if ((VirtualServerUtils.validate_ip(self.restore_obj.ip)) and (
                            not (self.restore_obj.machine is None))):
                        test_data_validation()
                    elif hasattr(self.restore_obj, 'no_ip_state') and self.restore_obj.no_ip_state:
                        test_data_validation(True)
                    else:
                        self.log.info(
                            "Skipping test data validation ,"
                            "because the VM might be running a UNIX OS or the provided"
                            " subclient have filters applied")
                    if self.hvobj.instance_type == hypervisor_type.MS_VIRTUAL_SERVER.value.lower() \
                            and not vm_restore_options.in_place_overwrite:
                        dest_location = os.path.join(vm_restore_options.destination_path, restore_vm,
                                                     "Virtual Hard Disks")
                        self.restore_obj.delete_vm()
                        if hasattr(vm_restore_options, 'dest_machine'):
                            vm_restore_options.dest_machine.remove_directory(dest_location)
                        else:
                            self.restore_obj.machine.remove_directory(dest_location)
                    if self.hvobj.instance_type == hypervisor_type.Google_Cloud.value.lower() \
                            and not vm_restore_options.in_place_overwrite:
                        self.restore_obj.delete_vm()
            elif ((self.hvobj.VMs[vm].guest_os.lower() == "windows") and (
                    not vm_restore_options.in_place_overwrite) and
                  on_premise) and self.hvobj.instance_type == hypervisor_type.MS_VIRTUAL_SERVER.value.lower():
                self.restore_obj = vm_restore_options.dest_client_hypervisor.VMs[restore_vm]
                _source = self.VmValidation(self.source_obj, vm_restore_options)
                _dest = self.VmValidation(self.restore_obj, vm_restore_options)
                if _source == _dest:
                    self.log.info("config validation is successful")
                else:
                    self.log.error("error while configuration validation")
                    raise Exception
                time.sleep(120)
                self.restore_obj.power_off()
                dest_location = os.path.join(vm_restore_options.destination_path, restore_vm,
                                             "Virtual Hard Disks")
                self.disk_validation(self.restore_obj,
                                     vm_restore_options._destination_pseudo_client,
                                     dest_location, vm_restore_options.dest_machine)
                self.restore_obj.delete_vm()
                vm_restore_options.dest_machine.remove_directory(dest_location)
            else:
                self.log.info("The Destination IP is not proper and the VM seems to be powered off,"
                              " so no Data Validation cannot be performed")
                if self.hvobj.instance_type == hypervisor_type.MS_VIRTUAL_SERVER.value.lower() \
                        and not vm_restore_options.in_place_overwrite:
                    dest_location = os.path.join(vm_restore_options.destination_path, restore_vm,
                                                 "Virtual Hard Disks")
                    self.hvobj.VMs[vm].delete_vm(restore_vm)
                    vm_restore_options.dest_machine.remove_directory(dest_location)

        except Exception as err:
            self.log.exception("Exception occurred in VM restore validation " + str(err))
            raise Exception("Exception in VM restore validation")

    def _get_all_backup_jobs(self):
        """
        Get all the backup jobs for the subclient
        :return:
            job_history     (dict)  -   all the unaged jobs for that subclient
                Ex:
                    {'job_cycle_1': {'bkp_level_full':  {'job_id':['aux_copy_jobid_1','aux_2']},
                                     'bkp_level_incr': {'job_id1':['aux1','aux2'],
                                                        'job_id2':['aux1','aux2']}
                                    },
                     'job_cycle_2': {'bkp_level_synth': {'job_id':['aux1','aux2']}
                                    }
                    }
        """
        job_history = {}

        _query = "select distinct BS.jobID, BS.bkpLevel, BS.fullCycleNum, DS.auxCopyJobId " \
                 "from JMBkpStats as BS join JMJobDataStats as DS ON BS.jobId = DS.jobId " \
                 "where BS.agedTime = 0 and BS.appId={0}".format(self.subclient_id)
        self.csdb.execute(_query)

        _results = self.csdb.fetch_all_rows()

        for result in _results:
            cycle_num = result[2].strip()
            job_id = result[0].strip()
            level = result[1].strip()
            aux_copy = result[3].strip()
            if cycle_num in job_history.keys():
                if level in job_history[cycle_num].keys():
                    if job_id in job_history[cycle_num][level].keys():
                        aux_jobs = job_history[cycle_num][level][job_id]
                        aux_jobs.append(aux_copy)
                        aux_jobs = list(set(aux_jobs))
                        try:
                            aux_jobs.remove('0')
                        except ValueError:
                            pass
                        job_history[cycle_num][level][job_id] = aux_jobs
                    else:
                        job_history[cycle_num][level][job_id] = [aux_copy]
                else:
                    job_history[cycle_num][level] = {job_id: [aux_copy]}
            else:
                job_history[cycle_num] = {level: {}}
                job_history[cycle_num][level] = {job_id: [aux_copy]}

        return job_history

    def reset_subclient_content(self):

        """"
        This is used to set the contents back to the subclient with
        updated GUID of every VM after In place restore in case of Azure

        Raise:
              Exception:
                If unable to set contents in the subclient

        """

        try:
            list = []
            for _vm in self.vm_list:
                self.hvobj.VMs[_vm].update_vm_info('All', True)
                list1 = {'type': VSAObjects.VM, 'display_name': _vm, 'name': self.hvobj.VMs[_vm].guid}
                list.append(list1)

            self.subclient.content = list


        except Exception as err:
            self.log.exception(
                "Exception while setting contents of subclient" + str(err))
            raise err

    def verify_vmfilter_backedup_vms(self):

        """"
        This is used to verify that only non-filtered VMs are backed up

        Raise:
              Exception:
                If filtered VMs are backed up

        """

        try:
            backedup_vms, _vm_ids = self.subclient._get_vm_ids_and_names_dict_from_browse()
            self.log.info(
                "Check if only following VMs {0} got backed up after applying filter ".format(
                    self.vm_list))
            for vm in backedup_vms:
                if vm not in self.vm_list:
                    self.log.info("The VM = {0} should not be backed up".format(vm))
                    raise Exception("VM filter is backing up non-expected VMs")
            if len(self.vm_list) != len(backedup_vms):
                self.log.info(
                    "The VMs {0} should have backed up, but actual backed up VMs are {1}".format(
                        self.vm_list, backedup_vms))
                raise Exception("VM filter is not backing up the expected VMs")
            self.log.info(
                "The VM filter is working properly, it backed up {0}".format(backedup_vms))
        except Exception as err:
            self.log.exception(
                "An Exception occurred while verifying vm filter backed up VMs" % err)
            raise err

    def create_ini_files(self):
        """
        Create a temp folder and files for storing and verifying changeID

        Raises:
             Exception:
                If unable to create temp folder and files

        """
        try:
            _vserver_path = os.path.dirname(VirtualServerUtils.UTILS_PATH)
            path_dir = self.controller_machine.join_path(_vserver_path, "TestCases", "CBT")
            if not self.controller_machine.check_directory_exists(path_dir):
                self.controller_machine.create_directory(path_dir)

            current_date = self.controller_machine.create_current_timestamp_folder(
                path_dir, "date")
            current_time = self.controller_machine.create_current_timestamp_folder(
                current_date, "time")
            self.controller_machine.create_file(
                os.path.join(current_time, "cbtStats.ini"), "$null")
            self.controller_machine.create_file(os.path.join(
                current_time, "usedChangeIDStatus.ini"), "$null")
        except Exception as err:
            self.log.exception(
                "Exception while creating files" + str(err))
            raise err

    def get_changeid_from_metadata(self, backup_type, backupjobid=None):
        """
        Get changeID generated for given backup job

        Args:
                backup_type    (str):    FULL/INCR/DIFF/SYNTH_FULL
                backupjobid    (int):    job ID of the backup job

        Raises:
             Exception:
                If unable to get change ID from metadata

        """
        try:
            _vserver_path = os.path.dirname(VirtualServerUtils.UTILS_PATH)
            path_dir = self.controller_machine.join_path(_vserver_path, "TestCases", "CBT")
            curfolder = self.controller_machine.get_latest_timestamp_file_or_folder(path_dir)
            curfolder = self.controller_machine.get_latest_timestamp_file_or_folder(curfolder)
            if self.auto_vsainstance.vsa_instance._instance_name == hypervisor_type.MS_VIRTUAL_SERVER.value.lower():
                for each_vm in self.vm_list:
                    vmguid = self.hvobj.VMs[each_vm].guid
                    pathtoBrowse = "\\" + vmguid
                    fileToWriteTo = open(curfolder + "\\cbtStats.ini", "a")
                    fileToWriteTo.write("\n[" + backup_type + "_" + each_vm + "]\n")
                    fileToWriteTo.close()
                    if backupjobid is None:
                        backupjobid = self.subclient.find_latest_job(include_active=False)
                    response_json = self.get_metadata(backupjobid._job_id, pathtoBrowse)
                    self.write_changeid_tofile(response_json)
            else:
                pathtoBrowse = "\\"
                fileToWriteTo = open(curfolder + "\\cbtStats.ini", "a")
                fileToWriteTo.write("\n[" + backup_type + "]\n")
                fileToWriteTo.close()
                if backupjobid is None:
                    backupjobid = self.subclient.find_latest_job(include_active=False)
                response_json = self.get_metadata(backupjobid._job_id, pathtoBrowse)
                self.write_changeid_tofile(response_json)
        except Exception as err:
            self.log.exception(
                "Exception while getting changeID from Metadata" + str(err))
            raise err

    def get_metadata(self, backupjobid, Pathtobrowse):
        """
        Get metadata for given backup job using browse request

        Args:
                backupjobid    (int):   job ID of the backup job
                Pathtobrowse   (int):   corressponding path for browsing

        Raises:
             Exception:
                If unable to get metdata from browse request

        """
        try:
            options = {}
            options['path'] = Pathtobrowse
            options['_subclient_id'] = self.subclient_id
            _backup_job = Job(self.auto_commcell.commcell, backupjobid)
            from datetime import timezone, datetime
            temp_time = datetime.strptime(_backup_job.start_time, "%Y-%m-%d %H:%M:%S")
            from_time = temp_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
            from_time = datetime.strftime(from_time, "%Y-%m-%d %H:%M:%S")
            temp_time = datetime.strptime(_backup_job._end_time, "%Y-%m-%d %H:%M:%S")
            end_time = temp_time.replace(tzinfo=timezone.utc).astimezone(tz=None)
            end_time = datetime.strftime(end_time, "%Y-%m-%d %H:%M:%S")
            options['from_time'] = from_time
            options['to_time'] = end_time
            options['media_agent'] = self._browse_ma
            options['show_deleted'] = True
            if self.auto_vsainstance.vsa_instance._instance_name == hypervisor_type.MS_VIRTUAL_SERVER.value.lower():
                options['vm_disk_browse'] = True
            paths, response_json = self.auto_vsa_backupset.backupset.browse(options)
            return response_json
        except Exception as err:
            self.log.exception(
                "Exception while getting metadata using browse request" + str(err))
            raise err

    def write_changeid_tofile(self, response_json):
        """
        Find and write changeID generated for given backupjob to cbtStats.ini file

        Args:
                response_json    (str):     Browse response received for given VM

        Raises:
             Exception:
                If unable to find and write changeID

        """
        try:
            # Open the file to write to
            _vserver_path = os.path.dirname(VirtualServerUtils.UTILS_PATH)
            path_dir = self.controller_machine.join_path(_vserver_path, "TestCases", "CBT")
            curfolder = self.controller_machine.get_latest_timestamp_file_or_folder(path_dir)
            curfolder = self.controller_machine.get_latest_timestamp_file_or_folder(curfolder)
            fileToWriteTo = open(curfolder + "\\cbtStats.ini", "a")
            if self.auto_vsainstance.vsa_instance._instance_name == hypervisor_type.AZURE_V2.value.lower():
                for value in response_json.values():
                    for key1, value1 in value.items():
                        if 'name' in key1:
                            path_name = value1
                        if 'advanced_data' in key1:
                            for key2, value2 in value1.items():
                                if 'browseMetaData' in key2:
                                    for key3, value3 in value2.items():
                                        if 'virtualServerMetaData' in key3:
                                            for key4, value4 in value3.items():
                                                if 'changeId' in key4:
                                                    import xml.etree.ElementTree as ET
                                                    tree = ET.ElementTree(ET.fromstring(value4))
                                                    tree_ID = tree.getroot().attrib[
                                                        'recentFullReferencePoint']
                                                    fileToWriteTo.write(
                                                        value['name'] + ":" + tree_ID + "\n")
                full_job_id = self.subclient.find_latest_job(include_active=False)
                job_info = Job(self.auto_commcell.commcell, full_job_id._job_id)
                total_time = int(job_info._summary['jobEndTime']) - int(
                    job_info._summary['jobStartTime'])
                fileToWriteTo.write("[TIME]" + "\n" + "FULL : " + str(total_time))
                fileToWriteTo.close()
            else:
                for key, value in response_json.items():
                    for key1, value1 in value.items():
                        if 'name' in key1:
                            path_name = value1
                        if 'advanced_data' in key1:
                            for key2, value2 in value1.items():
                                if 'browseMetaData' in key2:
                                    for key3, value3 in value2.items():
                                        if 'virtualServerMetaData' in key3:
                                            for key4, value4 in value3.items():
                                                if 'changeId' in key4:
                                                    fileToWriteTo.write(
                                                        path_name + ":" + value4 + "\n")
                fileToWriteTo.close()
        except Exception as err:
            self.log.exception(
                "Exception while finding and writing changeID to file " + str(err))
            raise err

    def parse_diskcbt_stats(self, cbtstat_folder, backup_type):
        """
        Find and copy cbt_stat file from hyperv to controller machine.
        And write changedID used by given backup to usedChangeIDStatus.ini file

        Args:
                cbtstat_folder    (str):     Folder to which CBT stats are stored on HyperV
                backup_type      (str):      FULL/INCR/DIFF/SYNTH_FULL

        Raises:
             Exception:
                If unable to find and write changeID

        """
        try:
            for each_vm in self.vm_list:
                # get CBTstat file and copy it on local system
                vmguid = self.hvobj.VMs[each_vm].guid
                vmcbtstat_folder = os.path.join(cbtstat_folder, str(vmguid).upper())
                for each_proxy in self.auto_vsainstance.proxy_list:
                    proxy_machine = Machine(each_proxy, self.auto_commcell.commcell)
                    if proxy_machine.check_directory_exists(vmcbtstat_folder):
                        break
                _vserver_path = os.path.dirname(VirtualServerUtils.UTILS_PATH)
                cbt_folder = os.path.join(_vserver_path, "TestCases", "CBT")
                cbt_stat = os.path.join(_vserver_path, "TestCases", "CBTStats")
                destvmcbt_stat = os.path.join(cbt_stat, str(vmguid).upper())
                if proxy_machine.is_local_machine:
                    if not proxy_machine.check_directory_exists(destvmcbt_stat):
                        proxy_machine.remove_directory(destvmcbt_stat)
                    proxy_machine.copy_folder(vmcbtstat_folder, destvmcbt_stat)
                else:
                    _dest_base_path = os.path.splitdrive(vmcbtstat_folder)
                    host_name = self.auto_commcell.get_hostname_for_client(each_proxy)
                    remote_vmcbtstat_folder = "\\\\" + host_name + "\\" + _dest_base_path[
                        0].replace(
                        ":", "$") + _dest_base_path[-1]
                    if self.controller_machine.check_directory_exists(destvmcbt_stat):
                        self.controller_machine.remove_directory(destvmcbt_stat)
                    self.controller_machine.copy_from_network_share(remote_vmcbtstat_folder,
                                                                    cbt_stat,
                                                                    self.auto_vsainstance.user_name,
                                                                    self.auto_vsainstance.password)
                proxy_machine.remove_directory(vmcbtstat_folder)
                self.log.info("Copied CBTstat folder at {0}".format(destvmcbt_stat))

                # Find and write changeID used
                curfolder = self.controller_machine.get_latest_timestamp_file_or_folder(cbt_folder)
                curfolder = self.controller_machine.get_latest_timestamp_file_or_folder(curfolder)
                fileToWriteTo = open(curfolder + "\\usedChangeIDStatus.ini", "a")
                fileToWriteTo.write("\n[" + backup_type + "_" + each_vm + "]\n")
                paths1 = [os.path.join(destvmcbt_stat, fn) for fn in
                          next(os.walk(destvmcbt_stat))[2]]
                paths = []
                for element in paths1:
                    if "avhdx.txt" not in element.lower() and (
                            ".vhd" in element.lower() or ".vhdx" in element.lower()):
                        paths.append(element)
                previousChangedIDUsed = {}
                diskName = ""
                for file in paths:
                    statsFile = open(file, "r")
                    lines = statsFile.readlines()
                    for line in lines:
                        if "ChangeId from previous job : " in line:
                            changeIDLine = line
                            subStrChangeID = changeIDLine.index("[")
                            subStrChangeID2 = changeIDLine.index("]")
                            changeID = changeIDLine[subStrChangeID + 1:subStrChangeID2]
                            indexDash = file.rfind("-")
                            diskName = file[indexDash + 1:len(file) - 4]
                            previousChangedIDUsed[diskName] = changeID
                            fileToWriteTo.write(diskName + ":" + changeID + "\n")
                    statsFile.close()
                    os.remove(file)
                fileToWriteTo.close()
        except Exception as err:
            self.log.exception(
                "Exception while parsing and writing used changeID to file " + str(err))
            raise err

    def parse_diskcbt_stats_azure(self, backup_options):
        """
        Find the changedID from the log files on the proxy and copy it to the controller
        And write changedID used by given backup to usedChangeIDStatus.ini file

        Args:
                backup_type      (str):      FULL/INCR/DIFF/SYNTH_FULL

        Raises:
             Exception:
                If unable to find and write changeID

        """
        try:
            log_dirc = self.auto_commcell.log_dir.rstrip('Automation')
            vmlog_file = os.path.join(log_dirc, 'vsbkp.log')
            job_id = self.subclient.find_latest_job(include_active=False)

            for each_proxy in self.auto_vsainstance.proxy_list:
                proxy_machine = Machine(each_proxy, self.auto_commcell.commcell)
                if proxy_machine.check_directory_exists(vmlog_file):
                    break
            _vserver_path = os.path.dirname(VirtualServerUtils.UTILS_PATH)
            cbt_folder = self.controller_machine.join_path(_vserver_path, "TestCases", "CBT")
            cbt_stat = self.controller_machine.join_path(_vserver_path, "TestCases", "CBTStats")
            destvmcbt_stat = self.controller_machine.join_path(cbt_stat, job_id._job_id)
            if proxy_machine.is_local_machine:
                if not proxy_machine.check_directory_exists(destvmcbt_stat):
                    proxy_machine.create_directory(destvmcbt_stat)
                proxy_machine.copy_folder(vmlog_file, destvmcbt_stat)
            else:
                _dest_base_path = os.path.splitdrive(vmlog_file)
                host_name = self.auto_commcell.get_hostname_for_client(each_proxy)
                remote_vmcbtstat_folder = "\\\\" + host_name + "\\" + _dest_base_path[0].replace(
                    ":", "$") + _dest_base_path[-1]
                if not self.controller_machine.check_directory_exists(destvmcbt_stat):
                    self.controller_machine.create_directory(destvmcbt_stat)
                    self.controller_machine.copy_files_from_network_share(
                        destvmcbt_stat,
                        remote_vmcbtstat_folder,
                        self.auto_vsainstance.user_name,
                        self.auto_vsainstance.password)

            self.log.info("Copied log file at {0}".format(destvmcbt_stat))

            # Find and write changeID used
            curfolder = self.controller_machine.get_latest_timestamp_file_or_folder(cbt_folder)
            curfolder = self.controller_machine.get_latest_timestamp_file_or_folder(curfolder)

            if backup_options.backup_type == 'FULL':
                fileToWriteTo = open(curfolder + "\\cbtStats.ini", "a")
                fileToWriteTo.write("\n[" + backup_options.backup_type + "]\n")

                err_occur = []
                pattern = re.compile(str(job_id._job_id) + " " + 'VSBkpWorker::BackupVMDisk()')
                pattern1 = re.compile(str(job_id._job_id) + " " + 'CAzureInfo::InitCBT()')

                with open(vmlog_file, 'rt') as in_file:
                    for linenum, line in enumerate(in_file):
                        if pattern.search(line) is not None or pattern1.search(line):
                            err_occur.append(line.rstrip('\n'))
                    for line in err_occur:
                        if "No change Id supplied" in line:
                            changeIDLine = line
                            subStrChangeID = changeIDLine.index("[")
                            subStrChangeID2 = changeIDLine.index("]")
                            vm_name = changeIDLine[subStrChangeID + 1:subStrChangeID2]
                        if "Saving change Id " in line:
                            changeIDLine = line
                            subStrChangeID = changeIDLine.index("[")
                            subStrChangeID2 = changeIDLine.index("]")
                            changeID = changeIDLine[subStrChangeID + 1:subStrChangeID2]
                            fileToWriteTo.write(vm_name + ":" + changeID + "\n")
                fileToWriteTo.close()

            else:
                fileToWriteTo = open(curfolder + "\\usedChangeIDStatus.ini", "a")
                fileToWriteTo.write("\n[" + backup_options.backup_type + "]\n")

                err_occur = []
                pattern = re.compile(str(job_id._job_id) + " " + 'VSBkpWorker::BackupVMDisk()')

                with open(vmlog_file, 'rt') as in_file:
                    for linenum, line in enumerate(in_file):
                        if pattern.search(line) != None:
                            err_occur.append(line.rstrip('\n'))
                    for line in err_occur:
                        if "Change Id has been supplied" in line:
                            changeIDLine = line
                            subStrChangeID = changeIDLine.index("[")
                            subStrChangeID2 = changeIDLine.index("]")
                            vm_name = changeIDLine[subStrChangeID + 1:subStrChangeID2]
                        if "Saving change Id " in line:
                            changeIDLine = line
                            subStrChangeID = changeIDLine.index("[")
                            subStrChangeID2 = changeIDLine.index("]")
                            changeID = changeIDLine[subStrChangeID + 1:subStrChangeID2]
                            fileToWriteTo.write(vm_name + ":" + changeID + "\n")
                fileToWriteTo.close()

        except Exception as err:
            self.log.exception(
                "Exception while parsing and writing used changeID to file " + str(err))
            raise err

    def verify_changeid_used(self, backup_type):
        """
        Compare and verify if changeID generated by previous backupjob is used by next
        backup job

        Args:
                backup_type      (str):      FULL/INCR/DIFF/SYNTH_FULL

        Returns:
                True            (boolean): if change ID is matched
                False           (boolean): if change id mismatch

        Raises:
             Exception:
                If unable to verify the changeID

        """
        try:
            import configparser
            _vserver_path = os.path.dirname(VirtualServerUtils.UTILS_PATH)
            cbt_folder = self.controller_machine.join_path(_vserver_path, "TestCases", "CBT")
            currentfolder = self.controller_machine.get_latest_timestamp_file_or_folder(cbt_folder)
            currentfolder = self.controller_machine.get_latest_timestamp_file_or_folder(
                currentfolder)
            changeid_generatedfile = self.controller_machine.join_path(
                currentfolder, "cbtStats.ini")
            changeid_usedfile = self.controller_machine.join_path(
                currentfolder, "usedChangeIDStatus.ini")
            Config_Curr = configparser.ConfigParser(strict=False)
            Config_Curr.read(changeid_usedfile)
            Config_Prev = configparser.ConfigParser(strict=False)
            Config_Prev.read(changeid_generatedfile)
            if backup_type == "DIFFERENTIAL":
                cmp_bk_type = "FULL"
            else:
                cmp_bk_type = "INCREMENTAL"
            if self.auto_vsainstance.vsa_instance._instance_name == hypervisor_type.MS_VIRTUAL_SERVER.value.lower():
                for each_vm in self.vm_list:
                    if not Config_Prev.has_section(cmp_bk_type + "_" + each_vm):
                        cmp_bk_type = "FULL"
                    currentDict = Config_Prev[cmp_bk_type + "_" + each_vm]
                    previousDict = Config_Curr[backup_type + "_" + each_vm]
                    for curKey in currentDict:
                        new_key = re.sub(r'^ide\w+\-\w\-', '', curKey)
                        new_key = re.sub(r'^scsi\w+\-\w\-', '', new_key)
                        if currentDict[curKey].strip() != previousDict[new_key].strip():
                            self.log.info(
                                "Used incorrect change IDs for {0} backup for Disk {1}".format(
                                    backup_type,
                                    curKey))
                            return False
                        else:
                            self.log.info(
                                "Used correct change IDs for {0} backup Disk {1}".format(
                                    backup_type, curKey))

                return True

            else:
                if not Config_Prev.has_section(cmp_bk_type):
                    cmp_bk_type = "FULL"
                currentDict = Config_Prev[cmp_bk_type]
                previousDict = Config_Curr[backup_type]
                bkp_time = Config_Prev["TIME"]
                full_backup_time = bkp_time[cmp_bk_type].strip()
                for curKey in currentDict:
                    new_key = re.sub(r'^ide\w+\-\w\-', '', curKey)
                    new_key = re.sub(r'^scsi\w+\-\w\-', '', new_key)
                    if currentDict[curKey].strip() != previousDict[new_key].strip():
                        self.log.info(
                            "Used incorrect change IDs for {0} backup for VM {1}".format(
                                backup_type,
                                curKey))
                        return False, full_backup_time
                    else:
                        self.log.info(
                            "Used correct change IDs for {0} backup VM {1}".format(backup_type,
                                                                                   curKey))

                return True, full_backup_time

        except Exception as err:
            self.log.exception(
                "Exception while verifying changeID used by job " + str(err))
            raise err

    def check_migrate_vm(self):
        """
        Check if more than one proxy/node is available and migrate to best possible node

        Raise Exception:
                If unable to check/migrate the vm

        """
        try:
            if len(self.auto_vsainstance.proxy_list) > 1:
                self.log.info("More than one node available to migrate the VM")
                for each_vm in self.vm_list:
                    self.hvobj.VMs[each_vm].migrate_vm()
                    self.hvobj.VMs[each_vm].recheck_vm_host()
            else:
                self.log.info("No other host is available for migration")
        except Exception as err:
            self.log.exception(
                "An Exception occurred while checking and if possible migrating VM to other node %s" %
                err)
            raise err

    def find_snap_guest_file_path(self, _browse_result, _drive_letter):
        """
        Get the Drive's Serial number
        Args:
            _browse_result                      (dict):     guest file browse for vm from snap at vm level

            _drive_letter                       (string):   drive for which the serial number is evaluated

        Returns:
            _browse_result['snap_display_name'] (string):   Serial number of the _drive_letter

        Raise Exception:
                If unable to verify the changeID
        """
        try:
            if "name" in _browse_result:
                if _browse_result['name'] == _drive_letter:
                    return _browse_result['snap_display_name']
            for v in _browse_result.values():
                if isinstance(v, dict):
                    item = self.find_snap_guest_file_path(v, _drive_letter)
                    if item is not None:
                        return item
        except Exception as err:
            self.log.exception(
                "Exception while getting guest file path for snap " + str(err))
            raise err

    def disk_count_validation(self, disk_count_before_restore):
        """
        Comparing the total number of disks before and after browse
        Args:
            disk_count_before_restore (int) :       Number of disk in the MA before Browse

        Returns:

        """
        try:
            self.log.info("Calculating the disk-count of the MA after restore")
            disk_count_after_restore = self.ma_machine.get_disk_count()
            self.log.info("Performing Live Browse Un-mount Validation")
            if (int(disk_count_before_restore)) >= (int(disk_count_after_restore)):
                self.log.info("Disk Unmounted Successfully")
            else:
                self.log.info(
                    "Failed to unmount disk, Number of Disk before restore:%s and Number of disk after restore:%s" %
                    (disk_count_before_restore, disk_count_after_restore))
                raise Exception("Failed to Un-mount Disk")
        except Exception as err:
            self.log.exception(
                "Exception while disk count validation " + str(err))
            raise err

    def vmware_live_browse_validation(
            self,
            vm,
            snap_backup_job,
            backup_copy_job,
            fs_restore_options,
            copy_precedence):
        """
        Validation for live browse from snap
        Args:
            vm                         (str):  Name of the vm which was browsed and restored

            snap_backup_job             (int):  Snap backup job id

            backup_copy_job             (int):  Backup copy job id

            fs_restore_options          (object): FS restore object

            copy_precedence             (int): Copy precedence value of a copy

        Raises:
            Exception:
                if it fails to do live browse validation
        """
        try:
            _guest_vm_os = self.hvobj.VMs[vm].guest_os
            _dest_client = Machine(fs_restore_options.destination_client,
                                  self.auto_commcell.commcell)
            _ma_machine = self._get_browse_ma(fs_restore_options)
            storage_policy = StoragePolicy(self.auto_commcell.commcell, self.storage_policy)
            _copy_id = ""
            for _copyname, _values in storage_policy.copies.items():
                if copy_precedence == _values['copyPrecedence']:
                    _copy_id = _values['copyId']
            if self.auto_commcell.check_v2_indexing(
                    self.subclient._subClientEntity['clientName']):
                snap_job = self.auto_commcell.get_vm_childjob(vm, snap_backup_job)
            else:
                snap_job = snap_backup_job
            snap_mount_status = self.auto_commcell.get_snap_proxy_mount_status(snap_job, _copy_id)
            mount_type = self.auto_commcell.mount_type_esxmount_or_proxylessmount(snap_job, _copy_id)
            if snap_mount_status == '59' and mount_type not in ['1','2']:  # if value is 1,2 then it is esx mount else proxy mount
                self.log.info("It was proxyless browse. Sleeping for 30 minutes")
                time.sleep(2000)
                if not fs_restore_options.metadata_collected:
                    self.log.info("Disk unmount validation")
                    self.disk_unmount_validation(vm)
            elif self.subclient.snapshot_engine_name == 'Virtual Server Agent Snap':
                self.log.info("VVOL engine. Sleeping for 11 minutes.")
                time.sleep(700)
                self.log.info("More Validation will be added for vvol")
            elif self.subclient.snapshot_engine_name == 'Cisco HyperFlex Snap':
                self.log.info("CISCO engine. Sleeping for 11 minutes.")
                time.sleep(700)
                self.log.info("More Validation will be added for CISCO snap engine")
            else:
                self.log.info("Validating Live Browse for Traditional method")
                _flag = False
                if self.auto_commcell.check_v2_indexing(
                        self.subclient._subClientEntity['clientName']):
                    snap_backup_job = self.auto_commcell.get_vm_childjob(vm, snap_backup_job)
                    if self.auto_commcell.get_snap_mount_status(snap_backup_job) != '59':
                        raise Exception("Snap is not mounted")
                vmname = vm + "_" + str(snap_backup_job) + "_GX_BACKUP"
                if not fs_restore_options.metadata_collected:
                    _list_of_mounted_ds = self.auto_commcell.live_browse_get_ds_info(
                        snap_backup_job)
                    if self.hvobj.check_vms_exist([vmname]):
                        self.log.info(" Sleeping for 11 minutes")
                        time.sleep(700)
                        if not self.hvobj.check_vms_exist([vmname]):
                            self.log.info(" Sleeping for 1 minutes")
                            time.sleep(100)
                            if not self.hvobj.check_ds_exist(_list_of_mounted_ds):
                                _flag = True
                else:
                    if not self.hvobj.check_vms_exist([vmname]):
                        _flag = True
                if _flag:
                    self.log.info("Live browse cleanup Validation successful")
                else:
                    raise Exception("Live Browse Validation failed during cleanup")
        except Exception as err:
            self.log.exception(
                "Exception at Live browse validation %s", str(err))
            raise err

    def validate_all_disks_present(self):
        """Validating all disks related to RDM testcases are present

        Raises:
            Exception:
                if all required disks are not present in the vm

        """
        _disks_needed = ['Flat_persistent', 'virtualMode_persistent', 'virtualMode_independent_persistent',
                         'physicalMode_independent_persistent', 'Flat_independent_persistent']

        for _vm in self.vm_list:
            for value in self.hvobj.VMs[_vm].rdm_details.values():
                _disk = value[1] + '_' + value[2]
                if _disk in _disks_needed:
                    _disks_needed.remove(_disk)
        if _disks_needed:
            raise Exception("All disks needed for RDM and independent testcase is not present")
        self.log.info("All disks needed for RDM and independent are present")

    def validate_rdm_disks(self, copy_precedence, rdm_type=3):
        """
        Validation for RDM disks

        Args:
            copy_precedence                    (int):   Copy precedence to browse

            rdm_type                           (int):    Options passed at the subclient level
                                                            0 -> No options selected
                                                            1 -> No Raw only independent
                                                            2 -> Raw only, no independent
                                                            3 -> Raw and independent

        Raises:
            Exception:
                if it fails to do rdm disks validation
        """
        try:
            self._disk_filter = True
            for _vm in self.vm_list:
                _temp_vm, _temp_vmid = self.subclient._get_vm_ids_and_names_dict_from_browse()
                _browse_request = self.subclient.disk_level_browse(
                    _temp_vmid[_temp_vm[0]],
                    copy_precedence=copy_precedence)
                disk_names = []
                self.hvobj.VMs[_vm].update_vm_info(force_update=True,
                                                   power_off_unused_vms=self.backup_option.power_off_unused_vms)
                for value in self.hvobj.VMs[_vm].rdm_details.values():
                    if rdm_type == 0:
                        if 'flat' in value[1].lower() and value[2].lower() == 'persistent':
                            disk_names.append(value[0])
                    elif rdm_type == 1:
                        if 'flat' in value[1].lower():
                            disk_names.append(value[0])
                    elif rdm_type == 2:
                        if value[1].lower() in ('flat', 'virtualmode') and value[
                            2].lower() == 'persistent':
                            disk_names.append(value[0])
                    else:
                        disk_names.append(value[0])
                self.log.info("total number of disks qualified: {}".format(len(disk_names)))
                self.log.info(
                    "total no of disks got via browse: {}".format(len(_browse_request[1].items())))
                if len(disk_names) != len(_browse_request[1].items()):
                    self.log.error("RDM disk validation failure")
                    raise Exception("RDM disk count mismatch")

                vm_folder = self.hvobj.VMs[_vm].get_vm_folder
                complete_disk_names = []
                for value1 in _browse_request[1].values():
                    if re.search(r"[\[\]]+", value1['name']):
                        complete_disk_names.append(value1['name'])
                    else:
                        complete_disk_names.append(vm_folder + value1['name'])
                if set(disk_names) == set(complete_disk_names):
                    self.log.info("RDM disks verified successfully for vm {}".format(_vm))
                    self.hvobj.VMs[_vm].disk_count = len(complete_disk_names)
                else:
                    self.log.exception("RDM disks verification Failed for vm {}".format(_vm))
        except Exception as err:
            self.log.exception(
                "Exception at Validating RDM disks {0}".format(err))
            raise err

    def validate_inputs(self, proxy_os="", ma_os="", vm_os="", update_qa=False, vm_check=False, **kwargs):
        """
        validate the OS configuring for the testcase

        Args:
            proxy_os                (str):  expected os of the proxy

            ma_os                   (str):  expected os of the Media agent

            vm_os                   (str):  expected os of the backup vm

            update_qa               (bool): if set to true, inputs will be validated for QA purpose

            vm_check                (bool): if true, check that there is more than one source vm in subclient content

            **kwargs                (dict):   Optional arguments
                       - validation (dict): Required argument for azure vm config validation


        Raises:
            Exception:
                if it fails to match os details

        """
        try:
            if vm_check:
                if len(self.vm_list) == 1:
                    raise Exception(
                        "There is only one source vm, Correct configuration for automation is to have "
                        "2 source vms atleast")
            if update_qa:
                if proxy_os != "":
                    self.log.info("Validating proxy OS")
                    _proxies = self.subclient.subclient_proxy
                    if _proxies:
                        for _proxy in _proxies:
                            if proxy_os.lower() not in self.auto_commcell.get_client_os_type(
                                    _proxy).lower():
                                raise Exception("OS of Proxy doesn't match")
                    else:
                        if proxy_os.lower() not in self.auto_commcell.get_client_os_type \
                                    (self.subclient.instance_proxy).lower():
                            raise Exception("OS of Proxy doesn't match")
                else:
                    self.log.info("Validating OS of proxy is not required here")
                if ma_os != "":
                    self.log.info("Validating MA OS")
                    if ma_os.lower() not in self.auto_commcell.get_client_os_type(
                            self.subclient.storage_ma).lower():
                        raise Exception("OS of MA doesn't match")
                else:
                    self.log.info("Validating OS of MA is not required here")
                if vm_os != "":
                    self.log.info("validating backup vm OS")
                    for _vm in self.hvobj.VMs:
                        if self.hvobj.VMs[_vm].guest_os.lower() != vm_os:
                            raise Exception("OS of backup vm doesn't match")
                else:
                    self.log.info("Validating OS of backup vm is not required here")

                if self.hvobj.instance_type == hypervisor_type.AZURE_V2.value.lower():
                    if not kwargs.get('validation'):
                        self.log.warning(f"Source instance is Azure but required vm config validation not provided."
                                         f" Skipping validation.")
                    else:
                        self.validate_azure_vm_config(kwargs.get('validation'))
            else:
                self.log.info("Validating inputs is not required here")

        except Exception as err:
            self.log.exception(
                "Exception at Validating inputs   %s", str(err))
            raise err

    def assign_browse_ma(self, proxy_os, ma_os, vm_os):
        """

        Assigning the correct browse ma for the subclient automatically

        Args:
            proxy_os                (str):  os of the proxy

            ma_os                   (str):  os of the Media agent

            vm_os                   (str):  os of the backup vm

        Raises:
            Exception:
                if it fails to assign browse MA

                """
        try:
            self.log.info("Assigning the Browse MA")
            if vm_os.lower() == 'windows' and ma_os.lower() == 'linux':
                if proxy_os.lower() == 'linux':
                    self.browse_ma = self.hvobj.commcell.commserv_name
                else:
                    if bool(self.subclient.subclient_proxy):
                        self.browse_ma = self.subclient.subclient_proxy[0]
                    else:
                        self.browse_ma = self.subclient.instance_proxy

        except Exception as err:
            self.log.exception(
                "Exception at assigning browse MA   %s", str(err))
            raise err

    def validate_tags(self):
        """

        Validates Tags and category are intact after restores

        Raises:
            Exception:
                if it fails to validate tags and category

        """
        try:
            for vm in self.vm_list:
                restore_vm = self.vm_restore_prefix + vm
                self.hvobj.VMs[vm].get_vm_tags()
                self.hvobj.VMs[restore_vm].get_vm_tags()
                for tag_category in self.hvobj.VMs[vm].tags:
                    if tag_category not in self.hvobj.VMs[restore_vm].tags:
                        self.log.exception("Restored VM doesn't have the category %s", tag_category)
                        raise Exception("Restored VM doesn't have all tags")
                    for tag in self.hvobj.VMs[vm].tags[tag_category]:
                        if tag not in self.hvobj.VMs[restore_vm].tags[tag_category]:
                            self.log.error("Restored VM doesn't have the tag %s", tag)
                            raise Exception("Restored VM doesn't have all tags")
                self.log.info("Source VM and Restored VM have same tags")
                self.log.info("Deleting VM %s", restore_vm)
                self.hvobj.VMs[restore_vm].delete_vm()
        except Exception as err:
            self.log.exception(
                "Exception at Tags validation %s", str(err))
            raise err

    def validate_vcenter(self, version):
        """
        Validates VCenter version is correct for the test

        Args:
            version                     (int):  Version of the VCenter expected

        Raises:
            Exception:
                if it fails to validate VCenter version

        """
        try:
            _proxies = self.subclient.subclient_proxy
            if _proxies:
                _proxy = _proxies[0]
            else:
                _proxy = self.subclient.instance_proxy
            _proxy_machine = Machine(_proxy, self.auto_commcell.commcell)
            if version < 6.5:
                self.log.info("The VCenter version should be either less than 6.5 or registery keys"
                              "should be present")
                if self.hvobj.vcenter_version >= 6.5:
                    if not _proxy_machine.get_registry_value('VirtualServer',
                                                             'bUsePowerCLiForTags') == '1':
                        raise Exception("This testcase requires vcenter 6.0 or the registry key")
            else:
                self.log.info("The VCenter version should be more than 6.5 and no registey keys"
                              "should be present")
                if _proxy_machine.get_registry_value('VirtualServer',
                                                     'bUsePowerCLiForTags') == '1' or \
                        self.hvobj.vcenter_version < 6.5:
                    raise Exception(
                        "This testcase requires VCenter above 6.5 and no the registry key")
            self.log.info("VCenter and registry key verified")
        except Exception as err:
            self.log.exception(
                "Exception at comparing VCenter version {}".format(err))
            raise err

    def validate_content(self, content):
        """
        Validates the content if of correct type

        Args:
            content                 (str):  Type of content required for the testcase

        Raises:
            Exception:
                if it fails to validate subclient content

        """
        try:
            if isinstance(content, str):
                content = [content]
            for ctype in self.vm_content:
                if ctype['type'] not in content:
                    raise Exception("Expected type of content is: %s", content)
            self.log.info("Content matches the requirement of the testcase")
        except Exception as err:
            self.log.exception(
                "Exception at comparing subclient content %s", str(err))
            raise err

    def disk_unmount_validation(self, vm, adr_id=None):
        """
               Checking if the disks are unmounted
        Args:
            vm           (str) :       Name of the vm which needs to be validated

            adr_id       (str) :       Attach disk request id for VM Browse on Linux MA

        Raises:
            Exception:
                if it fails to validate disks unmount

               """
        try:
            self.log.info("Calculating the disk-count of the MA after restore")
            if self.ma_machine.os_info.lower() == 'windows':
                _names_of_disks = self.ma_machine.get_mounted_disks()
                if self.hvobj.VMs[vm].guid in _names_of_disks:
                    _list_of_disks = _names_of_disks.split('\r\n')
                    self.log.info("mounted disks are: {}".format(_list_of_disks))
                    self.log.exception("Disks of the vm {} are still mounted".format(vm))
                else:
                    self.log.info("Disk unmount validation completed successfully")
            else:
                mounted_disks = self.ma_machine.execute_command('''lsblk | grep cvblk_mounts''')
                if adr_id in mounted_disks.output:
                    self.log.info("mounted disks are: {}".format(mounted_disks.output))
                    self.log.exception("Disks of the VM(s) are still mounted")
                else:
                    self.log.info("Disk unmount validation completed successfully")

        except Exception as err:
            self.log.exception(
                "Exception while disk unmount validation " + str(err))
            raise err

    def configure_live_sync(self, live_sync_options, pattern_dict=None):
        """
        To configure Live Sync on the subclient

        Args:
            live_sync_options   (obj)   -- Object of LiveSyncOptions class in OptionsHelper module

            pattern_dict        (dict)  -- Dictionary to generate the live sync schedule

                Sample:

                    for after_job_completes :
                    {
                        "freq_type": 'after_job_completes',
                        "active_start_date": date_in_%m/%d/%y (str),
                        "active_start_time": time_in_%H/%S (str),
                        "repeat_days": days_to_repeat (int)
                    }

                    for daily:
                    {
                         "freq_type": 'daily',
                         "active_start_time": time_in_%H/%S (str),
                         "repeat_days": days_to_repeat (int)
                    }

                    for weekly:
                    {
                         "freq_type": 'weekly',
                         "active_start_time": time_in_%H/%S (str),
                         "repeat_weeks": weeks_to_repeat (int)
                         "weekdays": list of weekdays ['Monday','Tuesday']
                    }

                    for monthly:
                    {
                         "freq_type": 'monthly',
                         "active_start_time": time_in_%H/%S (str),
                         "repeat_months": weeks_to_repeat (int)
                         "on_day": Day to run schedule (int)
                    }

                    for yearly:
                    {
                         "active_start_time": time_in_%H/%S (str),
                         "on_month": month to run schedule (str) January, Febuary...
                         "on_day": Day to run schedule (int)
                    }

        Returns:
            object - instance of the Schedule class for this Live sync

        In  config.json  file  give  credentials  "cs_machine_uname" , "cs_machine_password"  for  Schedule

        """

        def hyperv():
            return self.subclient.live_sync.configure_live_sync(
                schedule_name=live_sync_options.schedule_name,
                destination_client=live_sync_options.destination_client,
                proxy_client=live_sync_options.proxy_client,
                copy_precedence=live_sync_options.copy_precedence,
                destination_path=live_sync_options.destination_path,
                destination_network=live_sync_options.network,
                power_on=live_sync_options.power_on,
                overwrite=live_sync_options.unconditional_overwrite,
                distribute_vm_workload=live_sync_options.distribute_vm_workload,
                pattern_dict=pattern_dict
            )

        def azure():
            return self.subclient.live_sync.configure_live_sync(
                schedule_name=live_sync_options.schedule_name,
                destination_client=live_sync_options.destination_client,
                proxy_client=live_sync_options.proxy_client,
                copy_precedence=live_sync_options.copy_precedence,
                power_on=live_sync_options.power_on,
                resource_group=live_sync_options.Resource_Group,
                storage_account=live_sync_options.Storage_account,
                networkdisplayname=live_sync_options.network,
                region=live_sync_options.region,
                unconditional_overwrite=live_sync_options.unconditional_overwrite,
                restoreasmanagedvm=live_sync_options.restoreAsManagedVM,
                createpublicip=live_sync_options.createPublicIP,
                instancesize=live_sync_options.instanceSize,
                networkrsg=live_sync_options.networkrsg,
                destsubid=live_sync_options.subscripid,
                pattern_dict=pattern_dict
            )

        def vmware():
            return self.subclient.live_sync.configure_live_sync(
                schedule_name=live_sync_options.schedule_name,
                destination_client=live_sync_options.destination_client,
                proxy_client=live_sync_options.proxy_client,
                copy_precedence=live_sync_options.copy_precedence,
                destination_network=live_sync_options.network_info,
                power_on=live_sync_options.power_on,
                overwrite=live_sync_options.unconditional_overwrite,
                distribute_vm_workload=live_sync_options.distribute_vm_workload,
                datastore=live_sync_options.datastore_info,
                pattern_dict=pattern_dict
            )

        def amazon():
            return self.subclient.live_sync.configure_live_sync(
                schedule_name=live_sync_options.schedule_name,
                destination_client=live_sync_options.destination_client,
                proxy_client=live_sync_options.proxy_client,
                copy_precedence=live_sync_options.copy_precedence,
                power_on=live_sync_options.power_on,
                unconditional_overwrite=live_sync_options.unconditional_overwrite,
                pattern_dict=pattern_dict,
                networkdisplayname=live_sync_options.network,
                region=live_sync_options.region,
                data_center=live_sync_options.data_center,
                network=live_sync_options.network,
                security_groups=live_sync_options.security_groups,
                volume_type=live_sync_options.volume_type
            )

        hv_dict = {hypervisor_type.MS_VIRTUAL_SERVER.value.lower(): hyperv,
                   hypervisor_type.VIRTUAL_CENTER.value.lower(): vmware,
                   hypervisor_type.AMAZON_AWS.value.lower(): amazon}

        return hv_dict[live_sync_options.auto_subclient.auto_vsainstance.vsa_instance_name]()

    def get_live_sync_destination_subclient(self, schedule_name):
        """

        Get Live Sync Destination Auto Subclient

        Args:
            auto_subclient (AutoVSASubclient): Source AutoVSASubclient for Live Sync

            schedule_name (str):    Schedule name for Live sync

        Returns:
            dest_auto_subclient (AutoVSASubclient): Destination AutoVSASubclient for Live Sync

        """
        self.subclient.live_sync.refresh()
        live_sync_pair = self.subclient.live_sync.get(schedule_name)
        vm_pairs = live_sync_pair.vm_pairs
        vm_pair = live_sync_pair.get(next(iter(vm_pairs)))

        destination_client = self.auto_commcell.commcell.clients.get(vm_pair.destination_client)
        agent = destination_client.agents.get('virtual server')
        instance = agent.instances.get(vm_pair.destination_instance)

        dest_auto_client = AutoVSAVSClient(self.auto_commcell, destination_client)
        dest_auto_vsa_instance = AutoVSAVSInstance(dest_auto_client, agent, instance)

        # Initialize destination VMs if they exist
        destination_vms = [live_sync_pair.get(vm_pair).destination_vm for vm_pair in vm_pairs]

        # Check if VMs exist
        initialize_vms = dest_auto_vsa_instance.hvobj.check_vms_exist(destination_vms)

        if initialize_vms:
            for dest_vm_name in destination_vms:
                dest_auto_vsa_instance.hvobj.VMs = dest_vm_name
        return dest_auto_vsa_instance

    def get_live_sync_destination_vms(self, schedule_name):
        """

        Get Live Sync Destination VMs

        Args:
            schedule_name (str): Schedule name for Live sync

        Returns:
            dest_vm_names (list): Destination VM Names

        """
        self.subclient.live_sync.refresh()
        live_sync_pair = self.subclient.live_sync.get(schedule_name)
        vm_pairs = live_sync_pair.vm_pairs

        dest_vm_names = []
        for vm_pair in vm_pairs:
            dest_vm_names.append(live_sync_pair.get(vm_pair).destination_vm)
        return dest_vm_names

    def get_recent_replication_job(self, schedule_name):
        """

        Returns latest replication job, given schedule name

        Args:
            schedule_name   (str) : Name of schedule

        Returns:
            replication_job (Job) : Job Object for latest replication job

        """

        self.auto_vsaclient.vsa_client.schedules.refresh()
        schedule = self.auto_vsaclient.vsa_client.schedules.get(schedule_name)
        schedule_helper = SchedulerHelper(schedule, self.auto_commcell.commcell)

        # Get latest replication job from schedule helper
        replication_job = schedule_helper.get_jobid_from_taskid()
        return replication_job

    def validate_live_sync(self, live_sync_name, replication_run=True, check_replication_size=True,
                           schedule=None, live_sync_options=None):
        """To validate VSA live sync

        Args:
            live_sync_name  (str)   -- Name of the live sync

            replication_run (bool)  -- Set to True to check if replication job is triggered for the backup, else False
                                        default: True

            check_replication_size (bool) -- Set to False if incremental jo is coverted to full replication

            schedule(object) -- schedule object for replication schedule to be validated

            live_sync_options(object) -- A LiveSyncOptions object for replication options used.

        Raises:
            Exception

                -- If validation fails

        """
        self.subclient.live_sync.refresh()
        live_sync_pair = self.subclient.live_sync.get(live_sync_name)
        vm_pairs = live_sync_pair.vm_pairs
        vm_pair = live_sync_pair.get(next(iter(vm_pairs)))

        destination_client = self.auto_commcell.commcell.clients.get(vm_pair.destination_client)
        dest_auto_client = AutoVSAVSClient(self.auto_commcell, destination_client)

        agent = destination_client.agents.get('virtual server')
        instance = agent.instances.get(vm_pair.destination_instance)

        dest_auto_vsa_instance = AutoVSAVSInstance(dest_auto_client, agent, instance)

        for vm_pair in vm_pairs:
            self.log.info('validating VM pair: "%s"', vm_pair)

            source_vm = self.hvobj.VMs[vm_pair]
            time.sleep(60)
            source_vm.update_vm_info('All', os_info=True, force_update=True)

            dest_vm_name = live_sync_pair.get(vm_pair).destination_vm
            dest_auto_vsa_instance.hvobj.VMs = dest_vm_name
            dest_vm = dest_auto_vsa_instance.hvobj.VMs[dest_vm_name]

            dest_vm.power_on()
            self.log.info('Successfully powered on VM: "%s"', dest_vm_name)

            # Wait for IP to be generated
            wait = 10

            while wait:
                self.log.info('Waiting for 60 seconds for the IP to be generated')
                time.sleep(60)
                try:
                    dest_vm.update_vm_info('All', os_info=True, force_update=True)
                except Exception:
                    pass

                if dest_vm.ip and VirtualServerUtils.validate_ip(dest_vm.ip):
                    break
                wait -= 1
            else:
                self.log.error('Valid IP not generated within 10 minutes')
                raise Exception(f'Valid IP for VM: {dest_vm_name} not generated within 5 minutes')
            self.log.info('IP is generated')

            _source = self.VmValidation(source_vm)
            _dest = self.VmValidation(dest_vm)
            self.log.info(
                "Source validation object {0} and destination validation object is {1}".format(
                    vars(_source), vars(_dest)))

            time.sleep(120)
            vm_pair_obj = live_sync_pair.get(vm_pair)
            self.log.info("Vm pair object is {0}".format(vars(vm_pair_obj)))
            self.log.info("Replicatio job is {0}".format(vm_pair_obj.latest_replication_job))
            if isinstance(vm_pair_obj.latest_replication_job, int):
                replication_job = self.auto_commcell.commcell.job_controller.get(
                    vm_pair_obj.latest_replication_job)
            else:
                replication_job = self.get_recent_replication_job(schedule_name=live_sync_name)

            if replication_run:
                # To validate if replication job completed successfully
                assert str(vm_pair_obj.last_synced_backup_job) == str(self.backup_job.job_id), \
                    f"Replication job failed to sync latest backup job {self.backup_job.job_id}"
                self.log.info('Backup job sync successfull')

                backup_job = self.auto_commcell.commcell.job_controller.get(self.backup_job.job_id)
                if backup_job.backup_level == 'Incremental' and check_replication_size:
                    assert replication_job.size_of_application < (
                            backup_job.size_of_application + 1048576), \
                        "Replication job has replicated more data than expected for Incremental backup"
                    self.log.info('Data replicated for incremental job validation successful')
            else:
                # To validate if replication job never started
                assert str(vm_pair_obj.last_synced_backup_job) != str(self.backup_job.job_id), \
                    f"Replication Job started for Synthetic full, failing case"
                self.log.info('Replication run not started for Synthetic, validation successful')

            # To validate sync status
            assert vm_pair_obj.status == 'IN_SYNC', \
                f'VM pair : "{vm_pair}" \n Status: "{vm_pair_obj.status} \n Validation failed"'
            self.log.info('Sync status validation successful')

            # To validate Configuration
            assert _source == _dest, "error while configuration validation"
            self.log.info("config validation is successful")

            if live_sync_options:
                live_sync_options.destination_client = destination_client
                live_sync_options.live_sync_name = live_sync_name

            _livesyncsource = self.LiveSyncVmValidation(source_vm, schedule, replication_job, live_sync_options)
            _livesyncdest = self.LiveSyncVmValidation(dest_vm, schedule, replication_job)

            self.log.info(
                "Source validation object {0} and destination validation object is {1}".format(
                    vars(_livesyncsource), vars(_livesyncdest)))
            # hypervisor specific validation
            assert _livesyncsource == _livesyncdest, "error while validation  "

            # To validate test data between source and destination
            if replication_run:
                for drive in dest_vm.drive_list.values():
                    dest_path = dest_vm.machine.join_path(drive, self.backup_folder_name,
                                                          "TestData", self.timestamp)
                    self.fs_testdata_validation(dest_vm.machine, dest_path)
                self.log.info('Testdata validation successful')

            dest_vm.power_off()
            self.log.info('Successfully powered off VM: "%s"', dest_vm_name)

            self.log.info('Validation successful for VM pair: "%s"', vm_pair)

    def cleanup_live_sync(self, live_sync_name):
        """To clean up live sync operations

        Args:
             live_sync_name  (str)   -- Name of the live sync

        Raises:
            Exception

                -- If cleanup operation fails

        """
        live_sync_pair = self.subclient.live_sync.get(live_sync_name)
        vm_pairs = live_sync_pair.vm_pairs
        vm_pair = live_sync_pair.get(next(iter(vm_pairs)))

        destination_client = self.auto_commcell.commcell.clients.get(vm_pair.destination_client)

        dest_auto_client = AutoVSAVSClient(self.auto_commcell, destination_client)

        agent = destination_client.agents.get('virtual server')
        instance = agent.instances.get(vm_pair.destination_instance)

        dest_auto_vsa_instance = AutoVSAVSInstance(dest_auto_client, agent, instance)

        for vm_pair in vm_pairs:
            dest_vm_name = live_sync_pair.get(vm_pair).destination_vm
            dest_auto_vsa_instance.hvobj.VMs = dest_vm_name
            dest_vm = dest_auto_vsa_instance.hvobj.VMs[dest_vm_name]

            # To delete the replicated VM
            output = dest_vm.delete_vm(dest_vm_name)
            if output:
                self.log.info('Successfully deleted the replicated VM : "%s"', dest_vm_name)
            else:
                raise Exception(f'Failed to delete the VM {dest_vm_name} please check the logs')

        # To delete the created live sync configuration
        self.subclient._client_object.schedules.delete(live_sync_name)
        self.log.info('Successfully deleted the Live sync configuration schedule %s',
                      live_sync_name)

        self.log.info('Live sync cleanup operation is successful')

    def verify_cbt_backup(self, backup_type, backup_method='Streaming'):
        """
        Verifies CBT validation
        Args:
            backup_type                 (string):   Backup type of the job
            backup_method               (string):   Backup Method of the job

        Raises:
                Exception:
                    if it fails to get cbt details of the backup job

        """
        try:
            if backup_method == 'SNAP':
                backup_job = self.backupcopy_job
            else:
                backup_job = self.backup_job
            for cbt_status in backup_job.details['jobDetail']['clientStatusInfo']['vmStatus']:
                if backup_type in ['FULL']:
                    if cbt_status['CBTStatus'] in ['Enabled', 'Started', 'Not Supported']:
                        self.log.info("CBT is {0} for {1} backup job for vm {2}".
                                      format(cbt_status['CBTStatus'], backup_type,
                                             cbt_status['vmName']))
                        continue
                elif backup_type in ['INCREMENTAL', 'DIFFERENTIAL']:
                    if cbt_status['CBTStatus'] in ['Used', 'Not Supported']:
                        self.log.info(" CBT is Used for {0} backup job for vm {1}".
                                      format(backup_type, cbt_status['vmName']))
                        continue
                self.log.error("CBT is not used/enabled for {0} backup job for vm {1}".
                               format(backup_type, cbt_status['vmName']))
                raise Exception("CBT is not used/enabled")
        except Exception as err:
            self.log.exception(
                "Exception at Validating CBT backup {0}".format(err))
            raise err

    def validate_special_vm(self, advanced_config=False, **kwargs):
        """
        Validates the configuration of the special vm

        Args:

            advanced_config                (bool): Validate advanced config along with problematic testdata copy

        Returns:

            special_vm_drive               (dict):     Dict of VM and drive of big data

        Raises:
                Exception:
                    if it fails to fetch all details of the vm

        """
        try:
            special_vm_drive = {}
            problematic_vm_drive = {}
            for vm in self.vm_list:
                self.hvobj.VMs[vm].update_vm_info(prop='All', force_update=True)
                if self.hvobj.VMs[vm].guest_os.lower() != 'windows':
                    VirtualServerUtils.decorative_log("Checking the File systems of the Drives.")
                    command = "df -Th"
                    output = self.hvobj.VMs[vm].machine.execute_command(command)
                    tmp = ['/dev/mapper', 'xfs', 'ext2', 'ext3', 'ext4', 'btrfs']
                    if all(x in output.output for x in tmp):
                        self.log.info("{0} File systems found in the VM.".format(str(tmp)))
                    else:
                        self.log.exception("All types of File system is not found in the VM")
                        raise Exception
                    VirtualServerUtils.decorative_log(
                        "Checking if the Disk is mapped as UUID in fstab")
                    command = "cat /etc/fstab"
                    output = self.hvobj.VMs[vm].machine.execute_command(command)
                    if output.output.count("UUID") <= 1:
                        self.log.exception("Data Disk is not mapped with UUID in fstab")
                        raise Exception
                    self.log.info("Data Disk mapped with UUID in fstab")
                    VirtualServerUtils.decorative_log(
                        "Checking If the Drives are of 2GB and 1GB free space.")
                    tmp = self.hvobj.VMs[vm].machine.get_storage_details()
                    max_size = 0
                    problematic_max_size = 0
                    selected_drive = ''
                    problematic_drive = ''
                    for drive, size in tmp.items():
                        if drive != 'tmpfs' and drive != 'devtmpfs':
                            if isinstance(size, dict):
                                if size['mountpoint'] != '/boot':
                                    if size['total'] > 2048 and size['available'] > 1024:
                                        if size['available'] > max_size:
                                            problematic_drive = selected_drive
                                            problematic_max_size = max_size
                                            selected_drive = size['mountpoint']
                                            max_size = size['available']
                                        elif size['available'] > problematic_max_size:
                                            problematic_drive = size['mountpoint']
                                            problematic_max_size = size['available']
                                        continue
                                    else:
                                        self.log.exception("Not All drives are more than 2GB "
                                                           "and/or have free space more than 1 GB")
                                        raise Exception
                else:
                    if not self.windows_file_system_check(vm):
                        self.log.exception("All types of File system is not found in the VM")
                        raise Exception
                    if not self.windows_gpt_disk_check(vm, True):
                        self.log.exception("No GPT disk found in the VM or boot disk is not GPT")
                        raise Exception
                    if not self.windows_dynamic_disks_check(vm, True):
                        self.log.exception(
                            "There are no dynamic disks or not all types of dynamic disks")
                        raise Exception
                    if not self.windows_uninitialized_disk_check(vm):
                        self.log.exception("There is no uninitialized disk in the vm:{}".format(vm))
                        raise Exception
                    VirtualServerUtils.decorative_log(
                        "Checking If the Drives are of 2GB and 1GB free space.")
                    tmp = self.hvobj.VMs[vm].machine.get_storage_details()
                    max_size = 0
                    problematic_max_size = 0
                    selected_drive = ''
                    problematic_drive = ''
                    for drive, size in tmp.items():
                        if isinstance(size, dict):
                            if size['total'] > 2048 and size['available'] > 1024:
                                if size['available'] > max_size:
                                    problematic_drive = selected_drive
                                    problematic_max_size = max_size
                                    selected_drive = drive
                                    max_size = size['available']
                                elif size['available'] > problematic_max_size:
                                    problematic_drive = drive
                                    problematic_max_size = size['available']
                                continue
                            else:
                                self.log.exception("Not All drives are more than 2GB "
                                                   "and/or have free space more than 1 GB")
                                raise Exception
                self.log.info("All drives are minimum of 2GB in size and 1 GB free space")

                VirtualServerUtils.decorative_log("Checking the disk space for big data.")
                self.log.info("drive should have minimum 20 GB free space")
                if selected_drive != '' and max_size >= 20480:
                    self.log.info("Drive to be used on VM {0} for copying big data: {1}:".
                                  format(vm, selected_drive))
                    if self.hvobj.VMs[vm].guest_os.lower() == 'windows':
                        selected_drive = selected_drive + ":"
                        special_vm_drive[vm] = selected_drive
                    else:
                        special_vm_drive[vm] = selected_drive
                else:
                    self.log.exception("No Drive to copy data")
                    raise Exception

                if advanced_config:
                    if self.hvobj.VMs[vm].guest_os.lower() == 'windows':
                        if not self.windows_compressed_disk_check(vm):
                            self.log.exception("Compressed disk not found")
                            raise Exception
                        if not self.windows_dedup_disk_check(vm):
                            self.log.exception("Dedup disk not found")
                            raise Exception
                        if not self.windows_fragmented_disk_check(vm):
                            self.log.exception("Fragmented disk not found")
                            raise Exception
                        if not self.windows_encrypted_files_check(vm):
                            self.log.exception("Encrypted files not found")
                            raise Exception
                    if problematic_drive != '' and problematic_drive != selected_drive:
                        self.log.info("Drive to be used on VM {0} for copying problematic data: {1}:".
                                      format(vm, problematic_drive))
                        if self.hvobj.VMs[vm].guest_os.lower() == 'windows':
                            problematic_drive = problematic_drive + ":"
                            problematic_vm_drive[vm] = problematic_drive
                        else:
                            problematic_vm_drive[vm] = problematic_drive
                    else:
                        self.log.exception("No Drive to copy problematic data")
                        raise Exception

                    if len(self.hvobj.VMs[vm].drive_list) < 12:
                        self.log.exception("No. of drives on the VM {} are less than 12".format(vm))
                        raise Exception

                    million_files_path = kwargs.get("path_to_million_files")
                    vm_machine = self.hvobj.VMs[vm].machine
                    if million_files_path:
                        if vm_machine.check_directory_exists(million_files_path):
                            number_of_files = vm_machine.number_of_items_in_folder(million_files_path)
                            if number_of_files < 1000000:
                                self.log.exception("No. of files at path {0} for VM {1} is less than 10M".
                                                   format(million_files_path, vm))
                                raise Exception

                            path_depth = len(million_files_path.strip(vm_machine.os_sep).split(vm_machine.os_sep))
                            if path_depth < 10:
                                self.log.exception("Depth of path {} is less than 10.".format(million_files_path))
                                raise Exception

                    return special_vm_drive, problematic_vm_drive

            return special_vm_drive
        except Exception as err:
            self.log.exception(
                "Exception at checking special details of the VM: {0}".format(err))
            raise err

    def windows_file_system_check(self, vm):
        """
        To check if all file system are available or not
        Args:
            vm:                     (string):   name of the vm

        Returns:
                                    (boolean): True if all FS are present
                                                False if all FS are not present

        """
        VirtualServerUtils.decorative_log("Checking the File systems of the Drives.")
        command = "get-ciminstance Win32_logicaldisk | where mediatype -match '12' | select filesystem"
        output = self.hvobj.VMs[vm].machine.execute_command(command)
        tmp = ['NTFS', 'FAT', 'FAT32', 'ReFS']
        if all(x in output.output for x in tmp):
            self.log.info("{0} File systems found in the VM.".format(str(tmp)))
            return True
        else:
            self.log.error("All types of File system is not found in the VM")
            return False

    def windows_gpt_disk_check(self, vm, boot_disk=False):
        """
        To check if GPT disks is present and optionally to check if boot disk is GPT
        Args:
            vm:                                 (string): name of the vm

            boot_disk:                          (boolean):  False -> will not check boot disk
                                                            True -> Will check the boot disk

        Returns:
                                                (boolean): True if GPT disk is present
                                                            False if GPT disk is not present

        """
        VirtualServerUtils.decorative_log("Looking for GPT Disks")
        command = "gwmi -query 'Select * from Win32_DiskPartition WHERE Index = 0' |" \
                  "Select-Object DiskIndex, @{Name='GPT';Expression={$_.Type.StartsWith('GPT')}}"
        output = self.hvobj.VMs[vm].machine.execute_command(command)
        if output.output:
            output = self.hvobj.VMs[vm].machine.execute_command(command)
            count = output.output.count('True')
            if count > 0:
                self.log.info("There are {} GPT disks in the vm {}".format(count, vm))
                if boot_disk:
                    VirtualServerUtils.decorative_log("Checking if boot disk is GPT")
                    command = 'gwmi -query "Select * from Win32_DiskPartition WHERE Type like \'%GPT%\'' \
                              ' and Bootable = True" | Select-Object DiskIndex'
                    output = self.hvobj.VMs[vm].machine.execute_command(command)
                    if output.output:
                        self.log.info("Boot Disk is GPT")
                        return True
                    else:
                        self.log.error("Boot Disk is not GPT or issue in fetching disks")
                        return False
                else:
                    return True
            else:
                self.log.error("There are no GPT disks")
                return False
        else:
            self.log.error("Exception in fetching GPT disks")
            return False

    def windows_dynamic_disks_check(self, vm, all_types=False):
        """
        To check if dynamic disks are present in the vm and optionally if all type of dynamic disks are present
        Args:
            vm:                                 (string): name of the vm

            all_types:                          (boolean):  False -> will not check all type of dynamic disks
                                                            True -> Will check all types of dynamic disks
        Returns:
                                                (boolean): True if Dynamic disk is present
                                                            False if dynamic disk is not present
        """
        VirtualServerUtils.decorative_log("Looking for Dynamic Disks")
        command = "gwmi -query 'Select * from Win32_DiskPartition WHERE Index = 0' |" \
                  "Select-Object DiskIndex, @{Name='dynamic';" \
                  "Expression={$_.Type.Contains('Logical Disk Manager')}}"
        output = self.hvobj.VMs[vm].machine.execute_command(command)
        count = output.output.count('True')
        if count > 0:
            self.log.info("There are {} Dynamic disks".format(count))
            if all_types:
                VirtualServerUtils.decorative_log("Verifying for all Types of Dynamic Disks")
                command = "'list volume' | diskpart"
                output = self.hvobj.VMs[vm].machine.execute_command(command)
                if self.subclient.is_intelli_snap_enabled:
                    tmp = ['Mirror', 'Stripe', 'Spanned']
                else:
                    tmp = ['RAID-5', 'Mirror', 'Stripe', 'Spanned']
                if all(x in output.output for x in tmp):
                    self.log.info("{0} Dynamic Disks are Present in the VM".format(str(tmp)))
                    return True
                else:
                    self.log.error("All types of Dynamic Disks are not present in the VM")
                    return False
            else:
                return True
        else:
            self.log.error("There are no Dynamic disks")
            return False

    def windows_uninitialized_disk_check(self, vm):
        """
        To check if the vm has uninitialized disk
        Args:
            vm:                     (string):   name of the vm

        Returns:
                                    (boolean): True if the vm has uninitialized disk
                                                False if the vm doesn't have uninitialized disk

        """
        VirtualServerUtils.decorative_log("Checking if the VM has uninitialized disk")
        command = "get-disk | where partitionstyle -eq 'raw' | where OperationalStatus -eq 'Online'"
        output = self.hvobj.VMs[vm].machine.execute_command(command)
        if output.output:
            self.log.info("VM:{} has uninitialized disk".format(vm))
            return True
        else:
            self.log.error("There is no uninitialized disk in the vm:{}".format(vm))
            return False

    def windows_compressed_disk_check(self, vm):
        """
         To check if the vm has compressed disks
         Args:
             vm:                     (string):   name of the vm

         Returns:
                                     (boolean): True if the vm has compressed disks
                                                 False if the vm doesn't have compressed disks

         """
        VirtualServerUtils.decorative_log("Checking if the VM has compressed disks")
        command = "gwmi -query 'Select * from Win32_Volume' | select-object Compressed"
        output = self.hvobj.VMs[vm].machine.execute_command(command)
        count = output.output.count('True')
        if count > 0:
            self.log.info("VM:{} has compressed disks".format(vm))
            return True
        else:
            self.log.error("There is no compressed disk in the vm:{}".format(vm))
            return False

    def windows_dedup_disk_check(self, vm):
        """
          To check if the vm has dedup disks
          Args:
              vm:                     (string):   name of the vm

          Returns:
                                      (boolean): True if the vm has dedup disks
                                                  False if the vm doesn't have dedup disks

          """
        VirtualServerUtils.decorative_log("Checking if the VM has dedup disks")
        command = "Get-DedupVolume"
        output = self.hvobj.VMs[vm].machine.execute_command(command)
        if output.output:
            self.log.info("VM:{} has dedup disks".format(vm))
            return True
        else:
            self.log.error("There is no dedup disk in the vm:{}".format(vm))
            return False

    def windows_fragmented_disk_check(self, vm):
        """
          To check if the vm has fragmented disks
          Args:
              vm:                     (string):   name of the vm

          Returns:
                                      (boolean): True if the vm has fragmented disks
                                                  False if the vm doesn't have fragmented disks

          """
        VirtualServerUtils.decorative_log("Checking if the VM has fragmented disks")
        command = "gwmi -query 'Select * from Win32_Volume' | foreach-object {$_.DefragAnalysis().DefragRecommended}"
        output = self.hvobj.VMs[vm].machine.execute_command(command)
        count = output.output.count('True')
        if count > 0:
            self.log.info("VM:{} has fragmented disks".format(vm))
            return True
        else:
            self.log.error("There is no fragmented disk in the vm:{}".format(vm))
            return False

    def windows_encrypted_files_check(self, vm):
        """
          To check if the vm has encrypted files
          Args:
              vm:                     (string):   name of the vm

          Returns:
                                      (boolean): True if the vm has encrypted files
                                                  False if the vm doesn't have encrypted files

          """
        VirtualServerUtils.decorative_log("Checking if the VM has encrypted files")
        command = "Get-volume | foreach-object {" \
                  "$volpath=$_.DriveLetter + ':\\'; " \
                  "Get-childitem -path $volpath -recurse -force -include * -Attributes Encrypted}"
        output = self.hvobj.VMs[vm].machine.execute_command(command)
        if output.output:
            self.log.info("VM:{} has encrypted files".format(vm))
            return True
        else:
            self.log.error("There is no encrypted file in the vm:{}".format(vm))
            return False

    def add_registry_key(self, key, vm=None, folder="VirtualServer", key_val=1, key_type='DWord'):
        """
        Add registry to enable the feature

        Args:

            key    (string):   registry key name

            vm     (string): client machine where registry needs to be set

            folder (string): relative path

            key_val (int)  : value of the key

            key_type (string) : data type definition

        Raises:
            exception:
                if failed to set the registry on client machine

        """

        try:
            if vm:
                _proxy = Machine(vm, self.auto_commcell.commcell)
            else:
                _proxy = Machine(socket.gethostbyname_ex(socket.gethostname())[2][0])

            _proxy.create_registry(folder, key, key_val, key_type)

        except Exception as err:
            self.log.exception(
                "Exception while adding the registry : {0}".format(err))
            raise err

    def delete_registry_key(self, key, vm="None", folder="VirtualServer"):
        """
         Remove registry to disable the feature

         Args:

            key    (string):   registry key name

            vm     (string): client machine where registry needs to be removed

            folder (string): relative path

        Raises:
            exception:
                if failed to delete the registry on client machine
        """

        try:
            if vm:
                _proxy = Machine(vm, self.auto_commcell.commcell)
            else:
                _proxy = Machine(socket.gethostbyname_ex(socket.gethostname())[2][0])

            _proxy.remove_registry(folder, key)

        except Exception as err:
            self.log.exception(
                "Exception while deleting the registry: {0}".format(err))
            raise err

    def get_min_space_prune_val(self, ma_obj, job_result_dir):
        """
        Calculates the min disk space value for pruning to happen

        Args:

            ma_obj    (object):   Browse MA object
            job_result_dir    (string):   Job result directory

        Return:
            min_space_prune_value   (float):    Min disk space value for pruning
        """
        storage_details = ma_obj.get_storage_details()
        min_space_prune_value = 0
        for _drive, _size in storage_details.items():
            if isinstance(_size, dict) and _drive == job_result_dir[0]:
                total = _size['total']
                available = _size['available']
                min_space_prune_value = (available / total) * 100
                min_space_prune_value = min_space_prune_value + (min_space_prune_value * 5) / 100
                if int(min_space_prune_value) == 10:
                    min_space_prune_value = 9
        return min_space_prune_value

    def set_registry_key_for_pruning(self, browse_ma):
        """
        Sets the required registry key from pruning to happen

        Args:

            browse_ma    (string):   Media agent name

        Raises:
            exception:
                if failed to add the registry on media agent

        """
        try:
            ma_obj = Machine(commcell_object=self.auto_commcell.commcell, machine_name=browse_ma)
            ma_client = Client(commcell_object=self.auto_commcell.commcell, client_name=browse_ma)
            min_space_prune_value = self.get_min_space_prune_val(ma_obj, ma_client.job_results_directory)
            self.add_registry_key(key="nPseudoMountPrunerMinFreeSpace", vm=browse_ma,
                                  key_val=int(min_space_prune_value))
            self.add_registry_key(key="nExtentPruneInterval", vm=browse_ma, key_val=60)
            ma_client.restart_services()
            time.sleep(120)
            self.log.info("Sleeping for 120 seconds")
            sleep_count = 0
            while not ma_client.is_ready:
                sleep_count = sleep_count + 1
                time.sleep(30)
                self.log.info("Services are not up.Sleeping for 30 seconds")
                if sleep_count > 3:
                    raise Exception("Services are not up and running")
        except Exception as err:
            self.log.exception(
                "Exception while setting the registry key for pruning: {0}".format(err))
            raise err

    def del_registry_key_for_pruning(self, browse_ma):
        """
        Deletes the required registry key added for pruning to happen

        Args:

            browse_ma    (string):   Media agent name

        Raises:
            exception:
                if failed to delete the registry on media agent

        """
        try:
            ma_client = Client(commcell_object=self.auto_commcell.commcell, client_name=browse_ma)
            self.delete_registry_key(key="nPseudoMountPrunerMinFreeSpace", vm=browse_ma)
            self.delete_registry_key(key="nExtentPruneInterval", vm=browse_ma)
            ma_client.restart_services()
            time.sleep(120)
            self.log.info("Sleeping for 120 seconds")
            sleep_count = 0
            while not ma_client.is_ready:
                sleep_count = sleep_count + 1
                time.sleep(30)
                self.log.info("Services are not up.Sleeping for 30 seconds")
                if sleep_count > 3:
                    raise Exception("Services are not up and running")
        except Exception as err:
            self.log.exception(
                "Exception while deleting the registry key added for pruning: {0}".format(err))
            raise err

    def vm_conversion_validation(self, auto_subclient, vm_restore_options, backup_type):
        self.vm_restore_prefix = vm_restore_options.vm_restore_prefix
        vm_names_dict = {}
        for each_vm in auto_subclient.vm_list:
            auto_subclient.hvobj.VMs = each_vm
            vm_names_dict[each_vm] = self.vm_restore_prefix + each_vm

        self.hvobj.update_hosts()
        self.hvobj.VMs.clear()
        self.hvobj.VMs = list(vm_names_dict.values())
        for source_vm, dest_vm in vm_names_dict.items():
            restore_obj = self.hvobj.VMs[dest_vm]
            source_obj = auto_subclient.hvobj.VMs[source_vm]
            source_obj.update_vm_info('All', os_info=True, force_update=True)
            attempt = 0
            while attempt < 5:
                time.sleep(120)
                try:
                    restore_obj.update_vm_info(prop='All', os_info=True, force_update=True)
                    if restore_obj.ip is None or restore_obj.ip == "":
                        self.log.info("Attempt number %d failed. "
                                      "Waiting for 2 minutes for VM to come up" % attempt)
                        raise Exception
                    else:
                        break

                except Exception as ex:
                    attempt = attempt + 1

            # """
            for each_drive in restore_obj.drive_list:
                dest_testdata_path = restore_obj.machine.join_path(
                    restore_obj.drive_list[each_drive],
                    backup_type, "TestData",
                    auto_subclient.timestamp)

                auto_subclient.fs_testdata_validation(restore_obj.machine,
                                                      dest_testdata_path)
            # """

            _source = self.VmValidation(source_obj, vm_restore_options)
            _dest = self.VmValidation(restore_obj, vm_restore_options)
            if _source == _dest:
                self.log.info("config validation is successful")
            else:
                self.log.error("error while configuration validation")
                raise Exception("Error while configuration validation")

    def check_cbt_backup_time(self, backup_type, backup_method='Streaming'):
        """
        Check if the time taken for CBT incremental backup is less than
        full backup
        Args:
            backup_type                 (string):   Backup type of the job
            backup_method               (string):   Backup Method of the job

        Raises:
                Exception:
                    If it fails to get job details of the backup job
                    :param backup_type:
        """
        try:
            if backup_method == 'SNAP':
                backup_job = self.backupcopy_job
            else:
                backup_job = self.backup_job
            if backup_type == "INCREMENTAL":
                __cur_job_info = self.auto_commcell.get_job_start_end_time(backup_job.job_id)
                incremental_time_diff = int(__cur_job_info[1]) - int(__cur_job_info[0])

            else:
                _recent_incr_bkp_job_id = self.get_recent_incr_backup(backup_job.job_id)
                __recent_job_info = self.auto_commcell.get_job_start_end_time(
                    _recent_incr_bkp_job_id)
                incremental_time_diff = int(__recent_job_info[1]) - int(__recent_job_info[0])

            _prev_full_bkp_job_id = self.get_previous_full_backup(backup_job.job_id)
            __prev_job_info = self.auto_commcell.get_job_start_end_time(_prev_full_bkp_job_id)
            full_time_diff = int(__prev_job_info[1]) - int(__prev_job_info[0])
            self.log.info("Time taken for previous FULL backup {0} sec".format(full_time_diff))
            self.log.info("Time taken for latest INC backup {0} sec".format(incremental_time_diff))

            if full_time_diff > incremental_time_diff:
                self.log.info(
                    "Validation successful. Time taken to complete CBT incremental backup "
                    "is less than that time taken for full backup")
            else:
                self.log.exception(
                    "Validation failed. Time taken to complete CBT incremental backup"
                    "is more")

        except Exception as err:
            self.log.exception(
                "Exception while fetching job details")
            raise err

    def get_total_backupsize_for_parent_job(self, job_id):
        """
            Gets sum of backup size of all associated child job
         Args:
            job_id  (str):  parent job Id

        Returns:
            total_size  (int): tatal backup size
        Raise:
            Exception:
                If No child job is associated to job id provided

        """
        child_jobs = self.auto_commcell.get_child_jobs(job_id)
        if len(child_jobs) == 0:
            raise Exception("No child jobs associated")
        total_size = 0
        for each_job in child_jobs:
            total_size += int(self.auto_commcell.get_job_backup_size(each_job)[0])

        return total_size

    def check_cbt_backup_sizes(self, backup_type, backup_method='Streaming'):
        """
        Verify backup size of CBT incremental backup is less than
        full backup
        Args:
            backup_type                 (string):   Backup type of the job
            backup_method               (string):   Backup Method of the job

        Raises:
                Exception:
                    If it fails to get job details of the backup job
        """
        try:
            if backup_method == 'SNAP':
                backup_job = self.backupcopy_job
            else:
                backup_job = self.backup_job
            if not self.auto_commcell.check_v2_indexing(self.auto_vsaclient.vsa_client.client_name):
                if backup_type == "INCREMENTAL":
                    __cur_job_info = self.auto_commcell.get_job_backup_size(backup_job.job_id)
                    incremental_backup_size = __cur_job_info[0]

                else:
                    _recent_incr_bkp_job_id = self.get_recent_incr_backup(backup_job.job_id)
                    __recent_job_info = self.auto_commcell.get_job_backup_size(_recent_incr_bkp_job_id)
                    incremental_backup_size = __recent_job_info[0]

                _prev_full_bkp_job_id = backup_job.job_id
                if backup_type != "FULL":
                    _prev_full_bkp_job_id = self.get_previous_full_backup(backup_job.job_id)
                __prev_job_info = self.auto_commcell.get_job_backup_size(_prev_full_bkp_job_id)
                full_backup_size = __prev_job_info[0]
            else:
                if backup_type == "INCREMENTAL":
                    incremental_backup_size = self.get_total_backupsize_for_parent_job(backup_job.job_id)

                else:
                    _recent_incr_bkp_job_id = self.get_recent_incr_backup(backup_job.job_id)
                    incremental_backup_size = self.get_total_backupsize_for_parent_job(_recent_incr_bkp_job_id)
                _prev_full_bkp_job_id = backup_job.job_id
                if backup_type != "FULL":
                    _prev_full_bkp_job_id = self.get_previous_full_backup(backup_job.job_id)
                full_backup_size = self.get_total_backupsize_for_parent_job(_prev_full_bkp_job_id)

            self.log.info("Recent INC Backup Job size %s Last Full backup Size %s", incremental_backup_size,
                          full_backup_size)
            if int(full_backup_size) > int(incremental_backup_size):
                self.log.info("Validation successful. Backup size of CBT incremental backup "
                              "is less than that of full backup")
            else:
                self.log.exception("Validation failed. Backup size of CBT incremental backup"
                                   "is more")
                raise Exception
        except Exception as err:
            self.log.exception(
                "Exception while fetching job details")
            raise err

    def cbt_check_snapshot(self, backup_type, backup_method='Streaming'):
        """
        Checks if previous full backup job's snapshot is deleted after incremental job

        Args:
            backup_type                 (string):   Backup type of the job
            backup_method               (string):   Backup Method of the job

        Raises:
                Exception:
                    If it fails to get job details of the backup job
        """
        try:
            if backup_method == 'SNAP':
                self.log.info("No CBT Snapshot validation for snap and backup copy")

            else:
                backup_job = self.backup_job
                app_consistent_backup = self.subclient.quiesce_file_system
                if backup_type in 'INCREMENTAL':
                    _prev_full_bkp_job_id = self.get_previous_full_backup(backup_job.job_id)
                    _prev_full_bkp_job_obj = Job(self.auto_commcell.commcell,
                                                 str(_prev_full_bkp_job_id))
                    self.log.info("Previous Full backup job id is {0}".format(_prev_full_bkp_job_id))
                    for _vm in self.vm_list:
                        if not self.auto_vsainstance.vsa_instance_name == "kubernetes" \
                                and self.auto_vsaclient.isIndexingV2:
                            # Snapshots are retrieved in azure based on child backup job id
                            _prev_full_bkp_child_job_id = self.get_childjob_foreachvm(_prev_full_bkp_job_id)[_vm]
                            _prev_full_bkp_job_obj = Job(self.auto_commcell.commcell,
                                                         _prev_full_bkp_child_job_id)
                            self.log.info(
                                "Created child job object for previous full backup job {0} for Indexing V2".format(
                                    _prev_full_bkp_child_job_id))
                            self.log.info("Validating CBT snapshots/restore points for VM: {0}".format(_vm))
                            self.hvobj.VMs[_vm].validate_cbt_snapshots(_prev_full_bkp_job_obj,
                                                                        backup_method,
                                                                        snapshot_rg=self.backup_option.snapshot_rg,
                                                                        appConsistentBackup=app_consistent_backup)
                else:
                    self.log.info("Verifying previous Snapshots only for Streaming Incremental Job")
                    raise Exception
        except Exception as err:
            self.log.exception("Exception in cbt_check_snapshot : %s" % str(err))

    def attach_volume_restore(self, attach_volume_restore_options, msg=""):
        """

        perform Attach Volume to existing instance restore for specific Openstack subclient

        Args:
                attach_volume_restore_options    (object):   represent options that need to be set
                                                    while performing attach volume  restore

                msg                     (string):  Log line to be printed

        Exception:
                        if job fails
                        if validation fails

        """
        try:
            VirtualServerUtils.decorative_log(msg)
            for _vm in self.vm_list:
                self.log.info(
                    "Restoring the volume in Datastore: {}".format(
                        attach_volume_restore_options.datastore))

                def openstack():
                    volume_restore_job = self.subclient.attach_disk_restore(
                        _vm, vcenter=attach_volume_restore_options.vcenter,
                        proxy_client=attach_volume_restore_options._dest_client_name,
                        esx=attach_volume_restore_options.esxHost,
                        datastore=attach_volume_restore_options.datastore,
                        copy_precedence=attach_volume_restore_options.copy_precedence,
                        media_agent=attach_volume_restore_options.disk_browse_ma,
                        snap_proxy=attach_volume_restore_options.snap_proxy,
                        destinationVM=attach_volume_restore_options.dest_vm,
                        destinationVMGUID=attach_volume_restore_options.dest_vm_guid,
                        datacenter=attach_volume_restore_options.datacenter,
                        cluster=attach_volume_restore_options.cluster
                    )
                    return volume_restore_job

                hv_dict = {"openstack": openstack}

                volume_restore_job = (hv_dict[attach_volume_restore_options.dest_auto_vsa_instance.
                vsa_instance_name.lower()])()

                if not volume_restore_job.wait_for_completion():
                    raise Exception(
                        "Failed to run volume level restore job {0} with error:{1}".format(
                            volume_restore_job.job_id, volume_restore_job.delay_reason))
                self.log.info("Attach Disk restore job completed successfully with job id {0}"
                              .format(volume_restore_job.job_id))
                self.log.info("Performing basic 'Attach Volume to Existing Instance Validation'")
                source_volume_details = self.hvobj.VMs[_vm].disk_list
                destination_volume_details = self.hvobj.OpenStackHandler.get_volume_attachments(
                    attach_volume_restore_options.dest_vm_guid)
                self.hvobj.VMs[_vm].attach_volume_validation(attach_volume_restore_options,
                                                             source_volume_details,
                                                             destination_volume_details)
                self.log.info(
                    "Now..... Detaching and deleting the newly attached volume in destination VM")
                self.hvobj.OpenStackHandler.detach_and_delete_volume(
                    attach_volume_restore_options.dest_vm_guid,
                    attach_volume_restore_options.dest_servers,
                    destination_volume_details)
                self.log.info("Detach and Delete completed successfully")
                self.log.info("Verifying cleanup of attached volumes in the proxy machine")
                self.hvobj.VMs[_vm].backup_job = self.backup_job
                self.hvobj.VMs[_vm].verify_if_snapshots_and_volume_attached()
                self.log.info("All types of Validation completed successfully")
        except Exception as err:
            self.log.exception(
                "Attach Volume to existing instance Restore Process failed. please check logs")
            raise Exception(
                "Attach Volume to existing instance Restore Process failed, please check agent logs {0}".format(
                    err))

    def validate_rfc_files(self, Indexservername, jobid, source_list, delete_rfc=False, skip_parent_validation=False,
                           skip_child_validation=False):
        """
        Function to validate Remote file cache with the backup and restore

        Args:
            Indexservername       (str) --  Index server name
            jobid                (str)  --  Job ID of backup  .

            source_list         (list)  --  list of RFC files to be validated .

            delete_rfc           (bool) --  True: Deletes RFC path
                                            Default :False

            skip_parent_validation (bool) -- Skip Validation of Parent Job

            skip_child_validation  (bool) -- Skip Validation of Child Job(s)

        Raises:
            Exception if file not available in media agent RFC paths
        """
        self.indexpath = self.auto_commcell.get_IndexCache_location(Indexservername)
        self.log.info("Media Agent (Index Server) Cache Path: %s", self.indexpath)

        media_agent_machine = Machine(machine_name=Indexservername,
                                      commcell_object=self.auto_commcell.commcell)
        if not skip_parent_validation:
            self.log.info("Begin: Validation of RFC files in IndexCache for Parent Job %s", jobid)
            rfc_path = media_agent_machine.join_path(self.indexpath,
                                                     'RemoteFileCache', '2',
                                                     self.subclient.subclient_guid, str(jobid))
            self.log.info(
                "Media Agent (Index Server) RFC Path for Parent Job {0}: {1}".format(jobid,
                                                                                     rfc_path))
            compare_result = self.compare_rfc_files(Indexservername, rfc_path, source_list)
            if compare_result:
                self.log.info("All files validated in RFC")
            else:
                self.log.info("Failed to validate All files in RFC")
            self.log.info("End: Validation of RFC files in IndexCache for Parent Job %s", jobid)

            if skip_child_validation:
                return

            if delete_rfc:
                self.log.info("Deleting RFC Folder for Parent Job {0}: {1}".format(jobid, rfc_path))
                media_agent_machine.remove_directory(rfc_path)
                self.log.info("RFC Folder %s deleted ", rfc_path)

        if skip_child_validation:
            return

        child_guid_list = self.auto_commcell.get_Child_subclient_GUID_list(jobid)

        for _ChildGUID in child_guid_list:
            self.log.info("Begin: Validation of RFC files in IndexCache for Child Job %s",
                          _ChildGUID[1])
            rfc_path = media_agent_machine.join_path(self.indexpath,
                                                     'RemoteFileCache', '2', _ChildGUID[0],
                                                     str(_ChildGUID[1]))
            self.log.info(
                "Media Agent (Index Server) RFC Path for Child Job {0}: {1}".format(_ChildGUID[1],
                                                                                    rfc_path))
            self.log.info("VM GUID : {0}".format(_ChildGUID[2].lower()))
            rfc_item_list = [_ChildGUID[2].lower() + '_LiveBrowsePrefetchExtents.xml.rfczip']
            self.log.info("RFC Item: %s", rfc_item_list)
            compare_result = self.compare_rfc_files(Indexservername, rfc_path, rfc_item_list)
            if compare_result:
                self.log.info("All files validated in RFC")
            else:
                self.log.info("Failed to validate files in RFC")
            self.log.info("End: Validation of RFC files in IndexCache for Child Job %s",
                          _ChildGUID[1])

            self.log.info("Begin: Validate RFC Arch file in DB for Child Job %s", _ChildGUID[1])
            rfc_archfile_cnt = self.auto_commcell.get_rfc_archfile_count(_ChildGUID[1])
            if (int(rfc_archfile_cnt)) >= 1:
                self.log.info("RFC Arch file got created with backup job %s ", str(_ChildGUID[1]))
            else:
                self.log.info("RFC Arch file failed to create with backup job %s ",
                              str(_ChildGUID[1]))
                raise Exception("RFC Arch file failed to create with backup job %s ",
                                str(_ChildGUID[1]))
            self.log.info("End: Validate RFC Arch file in DB for Child Job %s", _ChildGUID[1])

            if delete_rfc:
                self.log.info(
                    "Deleting RFC Folder for Child Job {0}: {1}".format(_ChildGUID[1], rfc_path))
                media_agent_machine.remove_directory(rfc_path)
                self.log.info("RFC Folder %s deleted ", rfc_path)

    def compare_rfc_files(self, ma_machine, rfc_path, source_list):
        """
        Function to Compare Remote file cache from the list to RFC location

        Args:
            ma_machine        (str)  --  IndexServer Machine name

            rfc_path          (str)  --    RFC location

            source_list       (list) --    List of file to compare with

        Return:
            (Bool) as result of comparison

        Raises:
            Exception if file not available in media agent RFC paths
        """
        compare_flag = True
        media_agent_machine = Machine(machine_name=ma_machine,
                                      commcell_object=self.auto_commcell.commcell)
        rfc_list = media_agent_machine.get_files_in_path(rfc_path)
        self.log.info(rfc_list)
        rfc_files = []
        for file in rfc_list:
            rfc_list_fol, rfc_list_file = os.path.split(file)
            rfc_files.append(rfc_list_file.lower())
        self.log.info(rfc_files)

        for rfc_item in source_list:
            if rfc_item.lower() in rfc_files:
                self.log.info("File %s Exists  in RFC Index Cache  ", rfc_item)
            else:
                regexp = [x for x in rfc_files if re.search(rfc_item, x)]
                if len(regexp) != 0:
                    self.log.info("File %s Exists in RFC Index Cache  ", rfc_item)
                else:
                    compare_flag = False
                    self.log.info("File %s is not in RFC Index Cache  ", rfc_item)
                    raise Exception("File %s is not in RFC Index Cache  ", rfc_item)

        return compare_flag

    def verify_if_solr_used(self, child_backup_job, vm_guid):
        """
        Verify that SOLR is used during Guest File Level Browse

        Args:
            child_backup_job    (string):     job ID of the child backup job

            vm_guid             (string):     VM Guid of the VM part of the VM Group

        Raises:
            Exception:
                if Live Browse is used for Browse instead of SOLR
        """
        try:
            machine_ = Machine(machine_name=self.auto_commcell.commserv_name,
                               commcell_object=self.auto_commcell.commcell)
            client_ = Client(self.auto_commcell.commcell, self.auto_commcell.commserv_name)
            install_dir = client_.install_directory
            browse_log = install_dir + "\\Log Files\\Browse.log"
            self.log.info("Browse Log: %s", browse_log)
            log_line = machine_.read_file(browse_log, search_term=child_backup_job)
            self.log.info(log_line)
            if log_line.rfind('idxDbEngineType="2"') > 0 and log_line.rfind(vm_guid) > 0:
                self.log.info("SOLR is used for Browse.")
            else:
                raise Exception("Live Browse is used for Browse.")
        except Exception as exp:
            self.log.exception(
                "Exception occurred while verifying if SOLR was used during Browse. %s", str(exp))
            raise exp

    def validate_file_indexing_archive_files(self, child_backup_job_id):
        """
        Validate archive files after running File Indexing by making sure backup job archive file with 64 or 65600 flag
        is committed in SOLR

        Args:
            child_backup_job_id    (string):     child backup job ID

        Raises:
            Exception:
                if there's any exception while validating archive files
        """
        try:
            if self.auto_vsaclient.isIndexingV2:
                archive_file_list = self.auto_commcell.get_backup_job_archive_files(child_backup_job_id,

                                                                                    '(fileType = 9)')
                if len(archive_file_list) != 0:
                    self.log.info("VM got indexing via Ctree Indexing ")
                    return True
                else:
                    self.log.error("CTREE indexing didn't run on the VM")
                    return False
            else:
                archive_file_list = self.auto_commcell.get_backup_job_archive_files(child_backup_job_id,
                                                                                    '(flags&64) = 64')
                self.log.info("Got Archive Files")
                for archive_id in archive_file_list:
                    solr_url = self.auto_commcell.formulate_solr_query(self.subclient.subclient_name,
                                                                       self._browse_ma) + archive_id
                    self.log.info("SOLR Query URL: %s", solr_url)
                    if "multinode" in solr_url:
                        self.log.info("SOLR Query URL: %s", solr_url)
                        connection = requests.get(solr_url)
                        print(connection.content)
                        if bytes(archive_id, encoding="ascii") in connection.content:
                            self.log.info("Archive File ID %s is committed to SOLR", archive_id)
                            return True
                    else:
                        self.log.info("Cloud SOLR Query URL: %s", solr_url)
                        connection = urlopen(solr_url)
                        response = json.load(connection)
                        if int(response["response"]["numFound"]) > 0:
                            self.log.info("Archive File ID %s is committed to SOLR", archive_id)
                            return True
                    self.log.error(
                        "Archive ID validation failed. Didn't find archive files in SOLR: %s",
                        archive_file_list)
                    return False
        except Exception as exp:
            self.log.exception("There was an exception in validating archive file IDs in SOLR.%s",
                               str(exp))

    def get_in_line_file_indexing_job(self):
        """
        Get the File Indexing job ID that immediately runs after a Backup

        Raises:
            Exception:
                if there's any exception when getting the File Indexing Job ID
        """
        try:
            job_controller = self.auto_commcell.commcell.job_controller
            running_jobs = job_controller.active_jobs(
                client_name=self.auto_vsaclient.vsa_client_name, lookup_time=1,
                job_type="Data Analytics", operation="File Indexing")
            self.log.info(running_jobs)
            subclientId = self.subclient.subclient_id
            self.log.info("Subclient ID: %s" % subclientId)
            for job_id in list(running_jobs.keys()):
                self.log.info("job id: %s" % job_id)
                if str(running_jobs[job_id]['subclient_id']) == str(subclientId) and \
                        running_jobs[job_id]["operation"] == "File Indexing":
                    file_indexing_job_id = job_id
                    return file_indexing_job_id
        except Exception as exp:
            self.log.exception("Exception when getting in-line File Indexing Job ID. %s", str(exp))
            raise exp

    def get_file_indexing_job_details(self, file_indexing_job_id, synthfull=False):
        """
        Get the child Backup job for VMs in the File Indexing job as well as their GUIDs

        Args:
            file_indexing_job_id    (string):     job ID of the File Indexing job

            synthfull (bool) : when true then file indexing job_id will be same as backup job id.

        Returns:
            a Dictionary of VM GUID as key and a list of child backup job & proxy name as the value

        Raises:
            Exception:
                if there's any exception while getting File Indexing job details
        """
        try:
            job_controller = self.auto_commcell.commcell.job_controller
            file_indexing_job_details = job_controller.get(file_indexing_job_id)
            file_indexing_job_details_dict = file_indexing_job_details._get_job_details()
            self.log.info("Here is the File Indexing job details:")
            self.log.info(file_indexing_job_details_dict)
            child_backup_job_info = file_indexing_job_details_dict['jobDetail']['clientStatusInfo'][
                'vmStatus']
            vm_guid_child_job_dict = {}
            for vm in child_backup_job_info:
                child_backup_job_id = vm['jobID']
                proxy_utilized = vm['Agent']
                self.log.info("Got the Child Backup Job ID: %s", child_backup_job_id)
                vm_guid = vm['GUID']
                self.log.info("Got the VM GUID: %s", vm_guid)
                if synthfull:
                    vm_guid_child_job_dict[str(vm_guid)] = [str(file_indexing_job_id),
                                                            proxy_utilized]
                else:
                    vm_guid_child_job_dict[str(vm_guid)] = [str(child_backup_job_id),
                                                            proxy_utilized]
            return vm_guid_child_job_dict
        except Exception as exp:
            self.log.exception("Exception when getting File Indexing Job details. %s", str(exp))
            raise exp

    def check_status_file_indexing(self, job_id):

        """
                Get the status of File Indexing job.

                Args:
                    job_id    (int):   File Indexing jobID

                Raises:
                    Exception:
                        if there's any exception while getting File Indexing job details
                """

        try:

            self.log.info("File Indexing Job: %s", job_id)
            file_indexing_job = Job(self.auto_commcell.commcell, job_id)
            file_indexing_job.wait_for_completion()
            if file_indexing_job.status == "Completed":
                self.log.info("File Indexing Job %s completed.", job_id)
            else:
                raise Exception("File Indexing Job did not complete successfully %s", job_id)
        except Exception as exp:
            self.log.error("Exception when running File Indexing: %s" % str(exp))
            raise exp

    def post_backup_validation(self, **kwargs):
        """
        Performs Post Backup Validation

        Args:

        **kwargs                         : Arbitrary keyword arguments

        Raises:
            Exception:
            If Validation fails
        """
        try:
            self.log.info("Performing Post Backup Validation")
            vm_list = kwargs.get('vm_list')
            if not vm_list:
                vm_list = self.vm_list
            if isinstance(self.backup_option.backup_type, str):
                backup_type = self.backup_option.backup_type
            else:
                backup_type = self.backup_option.backup_type.value
            if not self.auto_vsainstance.vsa_instance_name == "kubernetes" and self.auto_vsaclient.isIndexingV2:
                self.backup_job.childJobObj = {}
                self.log.info("sleeping for 2 minutes")
                time.sleep(120)
                # Creating backupcopy child job object for Snap since that is validated
                if self.backup_option.backup_method == "SNAP":
                    self.vm_childJobs = self.get_childjob_foreachvm(self.backupcopy_job.job_id)
                else:
                    self.vm_childJobs = self.get_childjob_foreachvm(self.backup_job.job_id)
                for each_vm in self.hvobj.VMs:
                    self.log.info("Creating Child job object for VM {0}".format(each_vm))
                    _childJobid = self.vm_childJobs[each_vm]
                    self.backup_job.childJobObj[each_vm] = Job(self.auto_commcell.commcell, _childJobid)

            if (self.hvobj.instance_type == hypervisor_type.AZURE_V2.value.lower() or
                    self.hvobj.instance_type == hypervisor_type.AZURE.value.lower()):
                _azure_backup_validation = {"validate_cbt": True,
                                            "skip_snapshot_validation": False,
                                            "validate_workload": True}
                kwargs.update(_azure_backup_validation)

            if kwargs.get("validate_cbt", False):
                self.verify_cbt_backup(backup_type, self.backup_option.backup_method)
                if backup_type in 'INCREMENTAL':
                    self.log.info("Incremental Backup.. Proceeding with CBT validations")
                    self.check_cbt_backup_time(backup_type, self.backup_option.backup_method)
                    self.check_cbt_backup_sizes(backup_type, self.backup_option.backup_method)
                if not kwargs.get("skip_snapshot_validation", False):
                    self.validate_snapshot(backup_type, self.backup_option.backup_method)

            if not self.backup_option.backup_method == "SNAP":
                for each_vm in vm_list:
                    vm_obj = self.hvobj.VMs[each_vm]
                    if 'BackupValidation' not in dir(vm_obj):
                        continue
                    backup_validation = self.BackupValidation(vm_obj, self.backup_option)
                    backup_validation.validate()

            # Workload Validation
            if kwargs.get("validate_workload", False):
                self.log.info("Proceeding with backup workload validation")
                self.get_proxies()
                self.get_distribute_workload(self.backup_option.backup_job.job_id)
                for each_vm in self.vm_list:
                    self.hvobj.VMs[each_vm].compute_distribute_workload(self.proxy_obj, each_vm)
                    backup_workload_validation = self.BackupValidation(self.hvobj.VMs[each_vm], self.backup_option,
                                                                       proxy_obj=self.proxy_obj)
                    backup_workload_validation.validate()

            if kwargs.get("disk_filters", False):
                disk_filters = kwargs.get("disk_filters")
                self.log.info("Checking if disks were skipped: {}".format(disk_filters))

                if self.hvobj.instance_type.lower() == hypervisor_type.Vcloud.value.lower():
                    self.log.info("Checking disk filter rules for vCloud Director")

                    prefixes = VirtualServerUtils.vcloud_df_to_disks(disk_filters)

                    for each_vm in self.vm_list:
                        vm_guid = self.hvobj.VMs[each_vm].guid.split(":")[-1]

                        vm_disks, _ = self.subclient.disk_level_browse(vm_path="\\" + vm_guid)
                        for disk in vm_disks:
                            for prefix in prefixes:
                                if prefix in disk:
                                    raise Exception("Backup of VM {} did not skip disk {} as defined by a disk filter"
                                                    .format(each_vm, disk))

                        for disk in disk_filters.get("Content",{}).get(each_vm, []):
                            if disk in vm_disks:
                                raise Exception("Backup of VM {} did not skip disk {} as defined by a disk filter"
                                                .format(each_vm, disk))

                self.log.info("Validated disk filters successfully")

            if self.backup_option.vm_setting_options:
                self.validate_vm_backup_settings()

            self.log.info("Post backup validation completed")
        except Exception as err:
            self.log.error(str(err))
            raise Exception("Error in post backup validation")

    def validate_disk_filtering(self, copy_precedence=0, **kwargs):
        """
        Validation for Disk Filtering

        Args:
            copy_precedence                    (int):   Copy precedence to browse
            **kwargs                           (dict):   Optional arguments

        Raises:
            Exception:
                if it fails to do disk filter validation
        """
        try:
            snapshot_dict = {}
            for _vm in self.vm_list:
                self.hvobj.VMs[_vm].update_vm_info('All', os_info=True, force_update=True,
                                                   power_off_unused_vms=self.backup_option.power_off_unused_vms)
                if kwargs.get("validate_snapshot"):
                    snapshot_dict[_vm] = \
                        self.hvobj.VMs[_vm].check_disk_snapshots_by_jobid(self.backup_job, True)[1]
                    self.log.info("Snapshot dict before filtering is {0}".format(str(snapshot_dict[_vm])))
            self.prepare_disk_filter_list()
            for _vm in self.vm_list:
                self.log.info("Browsing for VM {0}".format(_vm))
                browsed_list = []
                flag = 0
                _temp_vm, _temp_vmid = self.subclient._get_vm_ids_and_names_dict_from_browse()
                _browse_request = self.subclient.disk_level_browse(
                    _temp_vmid[_vm],
                    copy_precedence=copy_precedence)
                self.log.info("Disk Browse Response : {0}".format(str(_browse_request[1])))
                self.log.info(
                    "No. of disks after filter in source VM: {} and no of disks in browse response: {}".format(
                        str(len(self.hvobj.VMs[_vm].disk_dict)),
                        str(len(_browse_request[1].items()))))
                if len(self.hvobj.VMs[_vm].disk_dict) != len(_browse_request[1].items()):
                    self.log.error("Disk Filter validation failure. Disk count mismatch")
                    self.log.error(
                        "Disks in Browse are : {0}".format(str(_browse_request[1].values())))
                    raise Exception("Disk count mismatch")
                self.log.info("Comparing the disk names")
                if self.hvobj.instance_type in (hypervisor_type.VIRTUAL_CENTER.value.lower(),
                                                hypervisor_type.Xen.value.lower()):
                    if self.hvobj.instance_type == hypervisor_type.VIRTUAL_CENTER.value.lower():
                        vm_folder = self.hvobj.VMs[_vm].get_vm_folder
                        for disk in _browse_request[1].values():
                            if re.search(r"[\[\]]+", disk['name']):
                                browsed_list.append(disk['name'])
                            else:
                                browsed_list.append(vm_folder + disk['name'])
                        self.hvobj.VMs[_vm].disk_validation = False
                    else:
                        for value in _browse_request[1].values():
                            browsed_list.append(value['snap_display_name'].lower())
                    if set(browsed_list).issubset(set(self.hvobj.VMs[_vm].filtered_disks)):
                        self.log.exception("Error in validating disk filter for vm {}".format(_vm))
                        raise Exception("Error in validating disk filter")
                else:
                    for value in _browse_request[1].values():
                        browsed_list.append(value['name'].lower())
                    for disk in self.hvobj.VMs[_vm].filtered_disks:
                        if disk.lower() in browsed_list:
                            flag = -1
                            break
                        if snapshot_dict:
                            self.log.info("Snapshot Validation")
                            if snapshot_dict[_vm][disk]:
                                flag = -1
                                break
                if flag != 0:
                    self.log.error("Filtered disk found in browse response")
                    raise Exception("Error in validating disk filter")
                self.log.info("Disk filter verified successfully")

        except Exception as err:
            self.log.exception(
                "Exception at Validating disk filter {0}".format(err))
            raise err

    def get_final_ma(self):
        """
        Get Media agents names associated with storage policy and which are not index server

        Returns:
            MA (list)  --  List of MA's
            If Indexsever, removes indexsever MA from the list
        Raise Exception:
                if unable to get MA names
        """
        try:
            finalma = self.subclient.get_ma_associated_storagepolicy()
            indexservername = self.get_index_name()
            if indexservername in finalma:
                finalma.remove(indexservername)
                self.log.info("successfully got finalma " + str(finalma))
            return finalma
        except Exception as err:
            self.log.exception(
                "Failed to Get Index name Exception:" + str(err))
            raise err

    def validate_collect_file(self, jobid, subclientid, machinesobj, csdbobj):
        """
        Validate collect file copied between source and destination machine are same

        args:

        job_id  (list)   -   Backup job id

        subclientid -  subclient id

        machineobj (list) - machine objects of source and destination machines

        csdbobj- sql object to connect to CS Data base

        Raise Exception:

        Failed to validate the vmcollect file
        """
        hashValues = []
        pathlist = VirtualServerUtils.get_vm_collectfile_path(csdbobj, machinesobj, jobid, subclientid)
        for eachpath in pathlist:
            for eachmachineobj in machinesobj:
                hashValues.append(eachmachineobj.get_file_hash(eachpath))
        if hashValues[0] != hashValues[1]:
            raise Exception
        self.log.info("Collect file copied onto all the nodes successful")

    def invalidate_archfile_id(self, jobid, archfiles1, archfiles2):
        """
        Verifying if archfiles getting invalidate

        args:

        job_id  (list)   -   Backup job id

        archfiles1 (dict)- archivefiles id before backup job

        archfiles2 (dict)- archivefiles id after backup job completed

        Raise Exception:

                Fails to invalidate
        """
        for eachjob in jobid:
            archids1 = archfiles2[eachjob]
            for eachArchid in archids1:
                if '-1' in eachArchid:
                    archids2 = archfiles1[eachjob]
                    for eachid in archids2:
                        if eachid[0] == eachArchid[0]:
                            if eachid[1] == eachArchid[1]:
                                raise Exception
        self.log.info("invalidate archive files successful" + str(archfiles2))

    # Chirag's code
    def create_azure_vm(self, subnet_resource, subnet_network, subnet_name):
        """
        Creates a new VM in the current resource group on Azure

        Args:
            subnet_resource (str): Name of subnet resource group
            subnet_network  (str): Name of subnet network
            subnet_name     (str): Name of subnet

        Raises :
            Exception on failure
        """
        try:
            for _vm in self.vm_list:
                self.hvobj.VMs[_vm].create_vm(subnet_resource, subnet_network, subnet_name)

        except Exception as err:
            self.log.exception(
                "Exception while creating a new VM")
            raise err

    def validate_network_security_group(self, vm_restore_options):
        """
        Validates if the restored VM is in the same NSG as the original VM

        Args:
                vm_restore_options			  (str):  options that need to be set while
                                                        performing vm restore
        Raises:
         Exception:
            If validation fails
        """
        try:
            for each_vm in self.vm_list:
                nsg = self.hvobj.VMs[each_vm].nsg
                if vm_restore_options.dest_client_hypervisor.VMs.get(each_vm, None):
                    restore_vm_name = self.vm_restore_prefix + each_vm
                    rnsg = self.hvobj.VMs[restore_vm_name].nsg
                    if nsg != rnsg:
                        self.log.error("NSG validation failed. NSG of restore VM is "
                                       "not same as that of original VM")
                        raise Exception
            self.log.info("NSG validation successful on restored VM.")

        except Exception as err:
            self.log.exception(
                "Exception while validating NSG on restored VM")
            raise err

    def parallel_browse_same_vm(self, vm, browse_ma='', thread_count=4):
        """
        does file level browse for a vm in parallel
        Args:
            vm                          (string):   name of the vm to browse

            browse_ma                   (string):   name of the MA

            thread_count                  (int):      no of thread for the browse

        Raises:
            Exception:
                If fails during multiple browse in parallel for a vm

        """

        try:
            drive_list = self.hvobj.VMs[vm].drive_list

            def browse(name):
                random_drive = random.choice(list(drive_list.keys()))
                _temp_vm, _temp_vmid = self.subclient._get_vm_ids_and_names_dict_from_browse()
                random_drive = _temp_vmid[vm] if random_drive == "/" else \
                    _temp_vmid[vm] + "\\" + random_drive
                self.log.info("Browse Thread {} starting for path {}".format(name, random_drive))
                _browse_request = self.subclient.guest_files_browse(random_drive,
                                                                    media_agent=browse_ma)
                if not _browse_request:
                    self.log.exception("Exception in browse in Browse thread {}"
                                       "for path{}".format(name, random_drive))
                    raise
                self.log.info("Browse Thread {}: {}".format(name, _browse_request))
                self.log.info("Browse Successful for Tread {0} for path {1}".
                              format(name, random_drive))

            threads = []
            for index in range(thread_count):
                VirtualServerUtils.decorative_log("Starting threads {} for vm {}"
                                                  .format(index, vm))
                browse_thread = threading.Thread(target=browse, args=(index,))
                threads.append(browse_thread)
                time.sleep(2)
                browse_thread.start()
            for index, thread in enumerate(threads):
                time.sleep(2)
                thread.join()

        except Exception as exp:
            self.log.exception("failed during parallel_browse_same_vm {}".format(exp))
            raise exp

    def parallel_browse_multiple_vm(self, browse_ma=''):
        """
        does file level browse for multiple vm in parallel
        Args:
            browse_ma                   (string):   name of the MA

        Raises:
            Exception:
                If fails during parallel browse of file level browse of multiple vms

        """

        try:
            vm_path_dict = {}
            for _vm in self.vm_list:
                _temp_vm, _temp_vmid = self.subclient._get_vm_ids_and_names_dict_from_browse()
                drive_list = self.hvobj.VMs[_vm].drive_list
                random_drive = random.choice(list(drive_list.keys()))
                random_drive = _temp_vmid[_vm] if random_drive == "/" else \
                    _temp_vmid[_vm] + "\\" + random_drive
                vm_path_dict[_vm] = random_drive

            def browse(name, vm, path):
                self.log.info(
                    "Browse Thread {} starting for vm {} for path {}".format(name, vm, path))
                _browse_request = self.subclient.guest_files_browse(path, media_agent=browse_ma)
                if not _browse_request:
                    self.log.exception("Exception in browse in browse thread {}"
                                       "for vm {} for path{}".format(name, vm, path))
                    raise
                self.log.info("Thread {}: {}".format(name, _browse_request))
                self.log.info("Browse Successful for Browse thread {} for vm {} for path {}".
                              format(name, vm, path))

            threads = []
            index = 0
            for _vm, _path in vm_path_dict.items():
                VirtualServerUtils.decorative_log("Starting threads {0} for vm {1}"
                                                  .format(index, _vm))
                browse_thread = threading.Thread(target=browse, args=(index, _vm, _path,))
                index += 1
                threads.append(browse_thread)
                time.sleep(2)
                browse_thread.start()
            for index, thread in enumerate(threads):
                time.sleep(2)
                thread.join()

        except Exception as exp:
            self.log.exception("failed during parallel_browse_multiple_vm {}".format(exp))
            raise exp

    def get_index_name(self):
        """
        Get Index server name

        return:
                Index server name     (str)   - Index server name

        Exception:
                if failed to get Index server ID
        """
        try:
            query = "select currentIdxServer from App_IndexDBInfo where backupsetid=" \
                    "(select ChildBackupSetId from app_vmbackupset where VMClientId =" \
                    "(select id from app_client where name = '" + self.subclient.content[0]['display_name'] + "'))"

            self.csdb.execute(query)
            inderserverid = self.csdb.fetch_all_rows()
            inderserverid = inderserverid.pop(0)
            inderserverid = inderserverid.pop(0)
            query = "select name from app_client where id = " + inderserverid + ""
            self.csdb.execute(query)
            inderservername = self.csdb.fetch_all_rows()
            inderservername = inderservername.pop(0)
            inderservername = inderservername.pop(0)
            self.log.info("successfully got indexservername " + str(inderservername))
            return inderservername
        except Exception as err:
            self.log.exception(
                "Failed to Get Index name Exception:" + str(err))
            raise err

    def convert_drive_to_volume(self, vm):
        """
        Converts drive name to volume name for linux with metadata

        Args:
            vm              (string):   Name of teh vm

        Returns:
            _temo_dict      (dict):     New Dict for volume drives for linux vms with metadata
        """
        _temp_dict = {}
        _vol = 1
        for _drive, _label in self.hvobj.VMs[vm].drive_list.items():
            if _label == "/":
                _temp_dict[_drive] = _drive
            else:
                _temp_dict['Volume-{}'.format(_vol)] = 'Volume-{}'.format(_vol)
                _vol += 1
        return _temp_dict

    def get_vms_from_backup_job(self, job_id):
        """
        Fetches VMs from Backup Job

        Args:
            job_id  (int/str)   -   Backup job id to check VMs involved

        Returns:
            List of VMs

        """
        backedup_vms = []
        job = Job(self.auto_commcell.commcell, job_id)
        for vm_detail in job.details['jobDetail']['clientStatusInfo']['vmStatus']:
            backedup_vms.append(vm_detail['vmName'])
        return backedup_vms

    def get_vm_app_size_from_parent_job(self, job_obj):
        """
        Fetches VMs from Backup Job

        Args:
            job_obj (object)   -   Parent Backup job obj to check VMs involved

        Returns:
            dictionary of VMs size

        """
        backedup_vms = {}
        for vm_detail in job_obj.get_vm_list():
            backedup_vms.update({vm_detail['vmName']: vm_detail['UsedSpace']})
        return backedup_vms

    def check_for_snapshot(self, snapshot_name=None, snapshot_time=None):
        """
        Checks for snapshot

        Args:
            snapshot_name  (str)   -   Snapshot name to be checked for managed disk
            snapshot_time  (str)   -   Snapshot time to be checked for unmamanged disk
        Raises
            Exception:
                If snapshot does not exists
        """
        try:
            for vm in self.vm_list:
                self.log.info("Looking for manually created auto_snapshot for vm {0} ".format(vm))
                if self.hvobj.VMs[vm].managed_disk:
                    snapshot_dict = self.hvobj.VMs[vm].get_disk_snapshots()
                    for disk, details in snapshot_dict.items():
                        flag = 0
                        self.log.info("Looking for manually created auto_snapshot for disk {0} ".format(disk))
                        for each_snapshot in details:
                            if re.match(snapshot_name, each_snapshot[0].get('name'), re.IGNORECASE):
                                flag = 1
                                break
                else:
                    snapshot_dict = self.hvobj.VMs[vm].get_snapshotsonblobs()
                    for disk, details in snapshot_dict.items():
                        flag = 0
                        self.log.info("Looking for manually created snapshot for disk {0} ".format(disk))
                        for each_snapshot in details:
                            if snapshot_time in each_snapshot:
                                flag = 1
                                break
                if flag == 0:
                    raise Exception("Manually created snapshot doesn't exist for VM {0} ".format(vm))

        except Exception as exp:
            raise Exception("Manually created snapshot doesn't exist for VM {0} ".format(vm))

    def validate_restart_extents(self, username=None, password=None, operation=None, clientname=None,
                                 jobmgr=None, streaming_job=None):
        """
        Validates extents restart
        Gets the restart string form the DB and validates against the log lines from Vsbkp
        Example - Job backed up until extent 100.
        After suspend/Resume or services restart or job pending,
        upon resuming job should continue backup from extent 100

        Args:
            username       (str)   - Username of the machine on which operation performed
            password       (str)   - Password of the machine on which operation performed
            operation      (str)   - Operation type to start/stop/restart/suspend services
            clientname     (str)   - client name to start services
            jobmgr         (str)   - Jobmgr service to restart.Value is None by default.
            streaming_job  (str)   - Streaming job id
        """
        if not streaming_job:
            _backup_job = self.auto_commcell.run_backup_copy(self.storage_policy, True)
            self.log.info("backup copy job started successfully")
            time.sleep(20)
            parent_job = self.auto_commcell.get_parentjob_using_wf(_backup_job.job_id)
        else:
            parent_job = streaming_job
        job = Job(self.auto_commcell.commcell, parent_job)
        machines = [self.subclient.storage_ma, self.auto_vsainstance.proxy_list[0]]
        machine_obj = []
        for each_server in machines:
            obj = Machine(machine_name=each_server, commcell_object=self.auto_commcell.commcell)
            machine_obj.append(obj)
        extent = None
        while extent == None:
            extent = machine_obj[0].get_logs_for_job_from_file(parent_job, 'cvd.log',
                                                                        'Updating the Job Manager that the chunk has been committed')
        if jobmgr != None:
            self.auto_commcell.commcell.commserv_client.restart_service('JobMgr')
            self.log.info('JM services restarted successfully')
        if operation == 'suspend':
            self.service_operation(4, 1, job)  # For op_id refer ServiceIds in virtualservercontstans.py
        if operation == 'stop':
            if clientname == self.subclient.storage_ma:
                self.service_operation(3, 3)  # For entity id refer ServiceOperationEntity in virtualservercontstans.py
            else:
                self.service_operation(3, 1)
            while job.status == 'Waiting' or job.status == 'Running':
                self.log.info('Waiting  5 min for the job to go to pending state')
                time.sleep(300)
            if job.status == 'Pending':
                self.log.info('job is in pending state. Start services')
                self.start_service(clientname, username, password)
        # getting restart string from DB
        query2_output = [['']]
        while query2_output == [['']]:
            query2_output = self.auto_commcell.get_job_extent_restarbility(parent_job)
        if not streaming_job:
            if not _backup_job.wait_for_completion():
                raise Exception("Failed to run job with error: "
                                +str(_backup_job.delay_reason))
        extent_info = query2_output[0][0].split("@")[1].replace('-o', '').split("   ")
        extent_list = []
        for each_extent in extent_info:
            extent_list.append(each_extent.split('|')[1])
        time.sleep(150)
        self.log.info('sleeping for 2.5 minutes')
        for eachitem in extent_list:
            extent2 = machine_obj[1].get_logs_for_job_from_file(parent_job, 'vsbkp.log',
                                                          'from extent: [' + (eachitem) + ']')
            self.log.info(
                "backup job resumed from expected extent".format(extent_list))
            if extent2 == '':
                self.log.error('backup didnot resume from expected extent'.format(extent_list))
                raise Exception

    def service_operation(self, op_id, entity_id, jobidobj=None, **kwargs):
        """
        Call start/stop service function based on user input

        Args:
            op_id  (int)   -   operation id (op_id) user input passed in test case file
                                to start/stop/restart/suspend services

            entity_id (int)   -   entity_id passed in test case file to determine machine
                                    is coordinator/worker proxy or MA
            jobidobj - job id object for job which needs to be suspend/resume

        Raise Exception:
                if failed to perform service operation

        """
        try:
            self.proxy_list = self.subclient.subclient_proxy
            user = kwargs.get('username', None)
            pswd = kwargs.get('password', None)
            if entity_id == ServiceOperationEntity.Co_ordinator.value:
                entity_name = kwargs.get("co_ordinator_node", self.proxy_list[0])
                if op_id == ServiceIds.Stop.value:
                    self.stop_service(entity_name)
                if op_id == ServiceIds.Start.value:
                    self.start_service(entity_name, user, pswd)
                if op_id == ServiceIds.Suspend.value:  # Create job object with current job
                    job_obj = Job(self.auto_commcell.commcell, self.current_job)
                    if jobidobj == None:
                        job_obj.pause(True)
                        self.log.info("Job is suspended")
                        time.sleep(300)
                        job_obj.resume(True)
                        self.log.info("Job is resumed")
                    else:
                        jobidobj.pause(True)
                        self.log.info("Job is Suspended")
                        time.sleep(300)
                        jobidobj.resume(True)
                        self.log.info("Resumed")
                if op_id == ServiceIds.Restart.value:
                    proxy_client = Client(self.auto_commcell.commcell, entity_name)
                    proxy_client.restart_services()
                    time.sleep(60)
                    VirtualServerUtils.decorative_log("All Services were restarted successfully on {}".
                                                      format(entity_name))
            if entity_id == ServiceOperationEntity.Worker.value:
                entity_name = kwargs.get("worker_node", self.proxy_list[1])
                if op_id == ServiceIds.Stop.value:
                    self.stop_service(entity_name)
                if op_id == ServiceIds.Start.value:
                    self.start_service(entity_name, user, pswd)
            if entity_id == ServiceOperationEntity.MA.value:
                if op_id == ServiceIds.Stop.value:
                    entity_name = self.subclient.storage_ma
                    self.ma_name = entity_name
                    self.stop_service(entity_name)
                if op_id == ServiceIds.Start.value:
                    self.start_service(self.ma_name, user, pswd)
            if entity_id == ServiceOperationEntity.Other.value:
                entity_name = kwargs.get("client_name")
                if op_id == ServiceIds.Stop.value:
                    self.stop_service(entity_name)
                if op_id == ServiceIds.Start.value:
                    self.start_service(entity_name, user, pswd)

        except Exception as exp:
            self.log.error('Failed to perform service operation: ' + str(exp))
            raise Exception

    def meditech_quiece_unquiece(self, job_id, search_term, quiece_time):
        """
        Validates if quiece and unquiece ran in expected time
          Args:
            job_id         (str)   - Parent snap job id
            search_term    (list)  - Only capture those log lines containing the search term
            quiece_time    (str)   - time to compare with Quiesce and UnQuiesce time
        Raise Exception:
                if quiece and unquiece took more time than expected time
        """
        try:
            vm_obj = Machine(self.auto_vsainstance.proxy_list[0], commcell_object=self.auto_commcell.commcell)
            job_list = self.auto_commcell.get_child_jobs(job_id)
            job_list.append(job_id)
            search_list = []
            for each_search_term in search_term:
                for each_job in job_list:
                    quiesce = vm_obj.get_logs_for_job_from_file(each_job,
                                                                 'vsbkp.log',
                                                                 each_search_term)
                    if quiesce:
                        if each_search_term in quiesce:
                            search_list.append(quiesce)
                            break
            VirtualServerUtils.decorative_log(search_list)
            time1 = search_list[0].split(' ')[5]
            time2 = search_list[1].split(' ')[5]
            start_dt = datetime.datetime.strptime(time1, '%H:%M:%S')
            end_dt = datetime.datetime.strptime(time2, '%H:%M:%S')
            diff = (end_dt - start_dt)
            diff = diff.total_seconds()
            if diff < int(quiece_time):
                VirtualServerUtils.decorative_log("Quiesce and unQuiesce took less time as expected")
        except Exception as exp:
            self.log.exception(
                "Quiesce and unQuiesce took less time as expected %s", str(exp))
            raise Exception

    def check_job_status_fromDB(self, op_id, entity_id):
        """
        Check job status by running DB query until it is completed for some of the VM's

        Args:
            op_id  (int)   -   operation id (op_id) user input passed in test case file
                                to start/stop/restart/suspend services. This will be
                                passed on to service_operation()
            entity_id (int)   -   entity_id passed in test case file to determine machine
                                    is coordinator/worker proxy or MA. This will be
                                    passed on to service_operation()

        Raise Exception:
                if failed to check job status

         """
        try:
            job_status = '4'
            while True:  # check the status of all vm's until one of them is complete
                if [js for js in job_status if js in ['0', '3']]:
                    self.log.info("Some VM's completed")
                    self.service_operation(op_id, entity_id)
                    break
                query = "select status from JMQinetixUpdateStatus " \
                        "where jobId='" + self.current_job + "'"
                self.csdb.execute(query)
                job_status = self.csdb.fetch_all_rows()
                job_status = [item for sublist in job_status for item in sublist]

        except Exception as exp:
            self.log.error('Failed to check job status: ' + str(exp))
            raise Exception

    def start_service(self, name, username, password, commcell_object=None):
        """
        Creates object of proxy/MA and then starts services on that machine

         Args:
            name (str)  -   name of the machine proxy/MA on which we have to start services
            username (str)  -   username of the machine
            password (str)  -   password of the machine
            commcell_object -   commcell object

        Raise Exception:
                if failed to start services

         """
        try:
            self.log.info("Starting services on {}".format(name))
            _machine = Machine(machine_name=name, commcell_object=None,
                               username=username, password=password)
            _instance = _machine.instance
            command_list = [f'start-Service -Name "GxCVD({_instance})"',
                            f'start-Service -Name "GxClMgrS({_instance})"',
                            f'start-Service -Name "GXMMM({_instance})"',
                            f'start-Service -Name "GxBlr({_instance})"']
            for each_command in command_list:
                _machine.execute_command(each_command)
            time.sleep(30)
            VirtualServerUtils.decorative_log("Services started successfully on {}".format(name))

        except Exception as exp:
            self.log.error('Failed to start services: ' + str(exp))
            raise Exception

    def stop_service(self, name, service_name=None):
        """
          Stop service on the machine

           Args:
              name (str)  -   name of the machine proxy/MA on which we have to stop services
              service_name (str) - name of the service to stop service

          Raise Exception:
                  if failed to stop the service

           """
        try:
            _machine = Client(self.auto_commcell.commcell, client_name=name)
            instance = _machine.instance
            if service_name:
                _machine.stop_service(service_name)
                VirtualServerUtils.decorative_log("{0} service stopped successfully on {1}".
                                                  format(service_name, name))
            else:
                _machine.stop_service(f"GxCVD({instance})")
                VirtualServerUtils.decorative_log("CVD service stopped successfully on {}".format(name))

        except Exception as exp:
            self.log.error('Failed to stop service: ' + str(exp))
            raise Exception

    def validate_ip_hostname(self, vm, ip=None, host_name=None):
        """
        Validate hostname and IP of the restored vm
        Args:
            vm                  (str)  -   name of the vm

            ip                  (str)  -   ip to be matched

            host_name           (str)  -   host name to be matched

        Raise Exception:
                if failed to validate IP and/or Host name
        """
        try:
            if ip:
                self.log.info("---___comparing IP of restored vm: {}---___".format(vm))
                self.log.info('IP passed in input: {}'.format(ip))
                self.log.info('IP of the restored vm: {}'.format(self.hvobj.VMs[vm].ip))
                if ip == self.hvobj.VMs[vm].ip:
                    self.log.info('IP given in input and restored vm are same')
                else:
                    raise Exception('IP of the Destination vm doesnt matches')
            if host_name:
                self.log.info("---___comparing Hostname of restored vm: {}---___".format(vm))
                self.log.info('Host name passed in input: {}'.format(host_name))
                _vm_host_name = self.hvobj.VMs[vm].machine.execute_command(
                    'hostname').formatted_output
                self.log.info('Hostname of the restored vm: {}'.format(_vm_host_name))
                if host_name == _vm_host_name:
                    self.log.info('Hostname given in input and restored vm are same')
                else:
                    raise Exception('Hostname of the Destination vm doesnt matches')
        except Exception as exp:
            self.log.error('Failed to Validate IP and/or Hostname ' + str(exp))
            raise Exception

    def validate_invoked_proxies(self, job_id, proxy_obj):
        """
                Validate the proxies invoked by StartRestore
                Args:
                    job_id      (str): Job Id of the restore operation

                    proxy_obj   (dict): Proxy location details

                Raise Exception:
                        If validation fails
        """

        try:
            self.log.info("Performing StartRestore Validation")
            cs_name = self.auto_commcell.commserv_name
            cs_client = self.auto_commcell.commcell.clients.get(cs_name)
            cs_machine = Machine(cs_client)
            log_directory = cs_client.log_directory
            start_restore_log = cs_machine.join_path(log_directory, 'StartRestore.log')
            log_line = cs_machine.read_file(start_restore_log, search_term=job_id)
            list_of_lines = log_line.split("\n")
            invoked_proxies = []

            for line in list_of_lines:
                if 'Powering on client '.lower() in line.lower():
                    proxy_status = re.search("\[\d+\]/\[(.+)\] (\w+)", line)
                    proxy_powered_on = True if proxy_status.group(2).lower() == 'succeeded' else False
                    if proxy_powered_on:
                        invoked_proxies.append(proxy_status.group(1))
                    else:
                        self.log.warning("Failed to power on proxy {} in StartRestore".format(proxy_status.group(1)))

            invoked_proxies = set([proxy.lower() for proxy in invoked_proxies])
            self.log.info('Proxies invoked by StartRestore : {}'.format(invoked_proxies))

            expected_proxies = set([proxy.lower() for proxy in proxy_obj.keys()])
            self.log.info('Expected proxies : {}'.format(expected_proxies))

            if invoked_proxies == expected_proxies:
                self.log.info('Validation of StartRestore invoked proxies completed successfully')
            else:
                raise Exception('Validation of StartRestore invoked proxies failed')

        except Exception as err:
            self.log.exception("Exception occurred in StartRestore validation " + str(err))
            raise Exception("StartRestore Validation failed")

    def toggle_intellisnap(self, snap_engine_name="Virtual Server Agent Snap"):
        """
        Toggle Intellisnap property for the subclient
        Args:
            snap_engine_name   (str): Name of snap engine for subclient

        Raise Exception:
            If failed to toggle intellisnap property
        """

        try:
            self.log.info("Toggling Intellisnap property for subclient")
            if self.subclient.is_intelli_snap_enabled:
                self.subclient.disable_intelli_snap()
            else:
                self.subclient.enable_intelli_snap(snap_engine_name)

        except Exception as err:
            self.log.exception("Exception occurred in Changing Intellisnap property " + str(err))
            raise Exception("Intellisnap toggle failed")

    def browse_ma_and_cp_validation(self, vm, restore_type, vm_restore_options=None, **kwargs):
        """
        Validates the Browse MA and Copy for Restores
        Args:
            vm                          (str) : VM name

            restore_type                (int) : Type of restore
                                                0 = Guest files restore
                                                1 = Full VM Restore

            vm_restore_options          (obj) : Restore Options

            **kwargs                    (dict) : Required keyword arguments if vm_restore_options is not provided
                                                proxy , job_id , browse_ma , browse_ma_id , copy_precedence

        Raises:
            Exception:
                If Browse MA and Copy validation failed
        """

        if restore_type == RestoreType.GUEST_FILES.value:
            xml_search_string = 'FclRestore::GetJobOption()'
            log_file = 'clRestore.log'
            copy_log_string = 'FclRestore::OnMsgOpenArchive() - Opening archive'
            copy_search_string = r'Opening archive <.+> with copy = (\d)'
            ma_connection_log_string = 'Connected to'
            ma_connection_search_string = r'Connected to (.+?):'

        else:
            xml_search_string = 'vsJobMgr::LoadJobOptions()'
            log_file = 'vsrst.log'
            copy_log_string = 'VSRstArchiveReader::OpenArchiveFile() - Opening Archive File'
            copy_search_string = r'Opening Archive File <.+> with CopyPrecedence:\[(\d)\]'
            ma_connection_log_string = 'VSRstWorker::PrepareBrowseRequest() - Setting the MA as client id'
            ma_connection_search_string = r'Setting the MA as client id :\[(\d+)\]'

        try:
            proxy = kwargs.get('proxy') or vm_restore_options.restore_proxy
            job_id = kwargs.get('job_id') or vm_restore_options.restore_job_id
            preferred_ma = kwargs.get('browse_ma') or vm_restore_options._browse_ma_client_name
            preferred_ma_id = kwargs.get('browse_ma_id') or str(vm_restore_options._browse_ma_id)
            preferred_copy_id = kwargs.get('copy_precedence') or str(vm_restore_options.copy_precedence)
        except Exception as err:
            self.log.exception("Missing parameters for browse ma and cp validation " + str(err))
            raise Exception("Browse ma and cp validation failed")

        # 1. Check the Browse MA and Copy from Restore Job xml

        found, log_line = VirtualServerUtils.find_log_lines(cs=self.auto_commcell.commcell, client_name=proxy,
                                                            log_file=log_file, search_term=xml_search_string,
                                                            job_id=job_id)
        if found:
            restore_xml = re.search("(<.+>)", log_line).group(1)
            parser = etree.XMLParser(recover=True)
            root = ET.fromstring(restore_xml, parser=parser)

            actual_ma_id = None
            actual_copy_id = None

            ma_tag = root.find('./restoreOptions/browseOption/mediaOption/mediaAgent')
            copy_tag = root.find('./restoreOptions/browseOption/mediaOption/copyPrecedence')

            if ma_tag is None or (not ma_tag.attrib.get('mediaAgentId')):
                raise Exception('Input MA is not passed in the restore XML')

            if copy_tag is None or (not copy_tag.attrib.get('copyPrecedence')):
                raise Exception('Input Copy is not passed in the restore XML')

            for child in root.iter('mediaAgent'):
                actual_ma_id = child.attrib['mediaAgentId']

            if actual_ma_id:
                if actual_ma_id != preferred_ma_id:
                    raise Exception(
                        'Invalid Browse MA in Restore xml. Preferred MA : [{0}] Used MA : [{1}]'.format(preferred_ma_id,
                                                                                                        actual_ma_id))

            for child in root.iter('copyPrecedence'):
                actual_copy_id = child.attrib['copyPrecedence']

            if actual_copy_id:
                if actual_copy_id != preferred_copy_id:
                    raise Exception(
                        'Invalid Copy Precedence in Restore xml. Preferred Copy : [{0}] Used Copy : [{1}]'.format(
                            preferred_copy_id, actual_copy_id))
        else:
            raise Exception('Unable to find Restore xml in the logs')

        # 2.
        # Guest files restore : Checks the MA used in Pipeline Connection for data transfer.
        # Full VM Restore : Checks the MA used in Index Browse.

        # Select the client used for mount based on guest OS
        if restore_type == RestoreType.GUEST_FILES.value:
            if self.hvobj.VMs[vm].guest_os.lower() == "windows":
                browse_ma_machine = Machine(preferred_ma, self.auto_commcell.commcell)
                if browse_ma_machine.os_info.lower() != "windows":
                    sub_proxies = self.subclient.subclient_proxy
                    windows_proxy = None
                    if sub_proxies:
                        self.log.info(
                            "Checking windows client in Subclient proxies {0}".format(",".join(sub_proxies)))
                        for each_proxy in sub_proxies:
                            temp_ma = Machine(each_proxy, self.auto_commcell.commcell)
                            if temp_ma.os_info.lower() == "windows":
                                windows_proxy = each_proxy
                                break
                    else:
                        if not windows_proxy:
                            instance_proxies = self.auto_vsainstance.proxy_list
                            self.log.info("Checking windows client in Instance proxies {0}".format(
                                ",".join(instance_proxies)))
                            for each_proxy in instance_proxies:
                                temp_ma = Machine(each_proxy, self.auto_commcell.commcell)
                                if temp_ma.os_info.lower() == "windows":
                                    windows_proxy = each_proxy
                                    break

                    if windows_proxy:
                        preferred_ma_id = self.auto_commcell.get_client_id(windows_proxy)

            else:
                preferred_ma_id = self.auto_commcell.get_client_id(self.auto_vsainstance.fbr_ma)

        found, log_line = VirtualServerUtils.find_log_lines(cs=self.auto_commcell.commcell, client_name=proxy,
                                                            log_file=log_file,
                                                            search_term=ma_connection_log_string,
                                                            job_id=job_id)

        if found:
            ma = re.search(ma_connection_search_string, log_line).group(1)

            if restore_type == RestoreType.GUEST_FILES.value:
                ma_id = self.auto_commcell.get_client_id(ma)
            else:
                ma_id = ma

            if ma_id != preferred_ma_id:
                raise Exception(
                    'Connection established to wrong MA. Preferred MA : [{0}] Used MA : [{1}]'.format(
                        preferred_ma_id,
                        ma_id))
        else:
            raise Exception('Unable to find required log for Browse MA Validation')

        # 3. Check the Copy used while opening the archive file

        found, log_line = VirtualServerUtils.find_log_lines(cs=self.auto_commcell.commcell, client_name=proxy,
                                                            log_file=log_file, search_term=copy_log_string,
                                                            job_id=job_id)
        if found:
            copy_id = re.search(copy_search_string, log_line).group(1)

            if copy_id != preferred_copy_id:
                raise Exception(
                    'Invalid Copy Precedence used. Preferred Copy : [{0}] Used Copy : [{1}]'.format(preferred_copy_id,
                                                                                                    copy_id))
        else:
            raise Exception('Unable to find required log for Copy Precedence Validation')

    def disk_cleanup_before_backup(self):
        """
        Delete disks with prefix del before backup
        Returns:
                    (bool):     True --> Deleted the disk
                                False/Exception --> failed to delete the disk

        """
        for vm in self.hvobj.VMs:
            if not self.hvobj.VMs[vm].delete_disks(ignore=True):
                raise Exception("Failed to delete the del disk from vm {}".format(vm))
        return True

    def validate_vm_backup_settings(self):
        """
        Validates the backup settings configured for each VM

        raises:
            Exception:
                If validation fails

        """
        try:
            self.log.info("Validating VM Backup Settings")
            parent_sub_bkp_type = VMBackupType.APP_CONSISTENT.name if self.subclient.quiesce_file_system \
                else VMBackupType.CRASH_CONSISTENT.name
            self.log.info("Parent Subclient Backup Type: [{0}]".format(parent_sub_bkp_type))
            self.get_distribute_workload(self.backup_job.job_id)

            for vm in self.hvobj.VMs:
                backup_proxy = self.hvobj.VMs[vm].proxy_name
                vm_quiesce_log_line = f'CVMWareInfo::CreateVMSnapshot() - Creating Snapshot of VM [{vm}]'
                vm_quiesce_search_string = r'Quiesce VM file system=\[(.+?)\]'

                VirtualServerUtils.discovered_client_initialize(self, vm)
                child_sub_bkp_type = self.hvobj.VMs[vm].subclient.quiesce_file_system

                # Check if the backup type setting is overridden from the VM level or not
                if child_sub_bkp_type is None:
                    # INHERITED MODE
                    preferred_vm_backup_type = parent_sub_bkp_type
                    self.log.info("[VM : {0}] Using backup type setting from the VM group level: [{1}]".
                                  format(vm, preferred_vm_backup_type))
                else:
                    # OVERRIDDEN MODE
                    # Apply the setting from child subclient instead of the parent
                    preferred_vm_backup_type = VMBackupType.APP_CONSISTENT.name if child_sub_bkp_type \
                        else VMBackupType.CRASH_CONSISTENT.name
                    self.log.info("[VM : {0}] Using backup type setting from the VM level: [{1}]".
                                  format(vm, preferred_vm_backup_type))

                found, log_line = VirtualServerUtils.find_log_lines(cs=self.auto_commcell.commcell,
                                                                    client_name=backup_proxy,
                                                                    log_file='vsbkp.log',
                                                                    search_term=vm_quiesce_log_line,
                                                                    job_id=self.backup_job.job_id)

                if found:
                    vm_quiesce = re.search(vm_quiesce_search_string, log_line).group(1)
                    vm_backup_type = VMBackupType.APP_CONSISTENT.name if vm_quiesce == 'ON' \
                        else VMBackupType.CRASH_CONSISTENT.name

                    if preferred_vm_backup_type != vm_backup_type:
                        raise Exception('VM [{0}] backed up with [{1}] mode instead of [{2}]'.
                                        format(vm, vm_backup_type, preferred_vm_backup_type))
                else:
                    raise Exception('Failed to find the log line : {}'.format(vm_quiesce_log_line))

            self.log.info('VM Backup settings validation completed')
        except Exception as exp:
            raise Exception('Failed to validate VM backup settings'.format(exp))

    def vcloud_attach_disk_validation(self, destination_vm=None, disks_to_attach=None, pre_restore_disks=None, disk_storage_policy=None):
        """
        Validates an attach disk restore job for vCloud Jobs

        Args:
            destination_vm           (str)    --      Name of the destination VM for the restore job
            pre_restore_disks        (dict)   --      Dictionary of { instance_id : <VMwareDisk object> } before restore
            disk_storage_policy      (str)    --      Name of the storage policy selected during restore.

        Raises:
            Exception:
                If unable to validate attach disk restore.
                If there's a mismatch in the disk count or storage policy.

        """

        self.log.info("Attempting to validate attach disk restore job")

        self.log.info("Disks before restore on destination VM {}: [{}]".format(destination_vm, len(pre_restore_disks)))

        self.hvobj.VMs = destination_vm
        self.hvobj.VMs[destination_vm].get_disk_info()
        current_disks = self.hvobj.VMs[destination_vm].disk_config

        new_disks = []

        for disk in current_disks.keys():
            if disk not in pre_restore_disks.keys():
                new_disks.append(current_disks[disk])

        for disk in disks_to_attach:
            if disk not in new_disks:
                raise Exception("Disk {} not found in newly attached disks".format(disk))

        # Check if new disks were attached to the destination VM.
        if len(new_disks) == 0:
            raise Exception("Error in attach_disk_validation: No new disk attached to the destination VM.")
        
        self.hvobj.VMs[destination_vm].attached_disks += [i.instance_id for i in new_disks]

        self.log.info("Newly attached disks are:\n {}".format("\n".join([str(i) for i in new_disks])))

        # Check if new disks have the correct storage policy
        for new_disk in new_disks:
            if disk_storage_policy and (new_policy := new_disk.storage_profile["name"]) != disk_storage_policy:
                self.log.info("Disk {} attached wih incorrect storage profile. Expected '{}' Found '{}'"
                         .format(new_disk, disk_storage_policy, new_policy))
                raise Exception("Error in attach_disk_validation: Disk attached with incorrect storage profile")

        self.log.info("Successfully validated attach disk restore on destination VM {}".format(destination_vm))
        self.hvobj.VMs[destination_vm].delete_disk()

    def delete_subclient_attribute(self, attribute_name, client_name=None):
        """
        Deletes the given attribute from the Subclient Properties in the DB
        Args:
            attribute_name  (str):  Attribute name

            client_name     (str):  VM Client name  (Optional)
                                    Hypervisor client is default
        Raises:
            Exception:
                If failed to execute the query
        """
        if not client_name:
            client_id = self.auto_vsaclient.vsa_client_id
        else:
            client_id = self.auto_commcell.commcell.clients.get(client_name).client_id
        _query = "delete from App_SubclientProp where componentNameId = (select TOP 1 id from " \
                 "App_Application where subclientName = '%s' and clientId = %d) and " \
                 "attrName = '%s'" % (self.subclient_name, int(client_id), attribute_name)
        self.utility.update_commserve_db(_query)

    def validate_diskrestorepoint(self, job_obj, vm_name, appconsistent_backup_enabled):
        """
        Args:
            job_obj (Job object) : Job object for which disk has to be validated

            vm_name (str) : name of vm to be validated

            appconsistent_backup_enabled (Boolean) : True if App consistent backup enabled at vmgroup

        Raises:
            Exception:
                IF Disk restore point validation Failed
        """
        try:
            backup_method = self.backup_option.backup_method
            checkdrp = self.hvobj.VMs[vm_name].validate_restorepoints_by_jobid(job_obj, backup_method,
                                                                               appconsistent_backup_enabled,
                                                                               custom_snapshotrg=self.backup_option.snapshot_rg)

            if checkdrp:
                self.log.info("Disk restore point validation is Successful")
            else:
                raise Exception("Disk restore point validation Failed")
        except Exception as err:
            self.log.exception("Exception in validating disks in application consistent backup : %s" % str(err))


    def check_customrg_snapshot(self):
        """
        Azure:
        Checks if snapshots are created under custom Resource group if self.backup_option.snapshot_rg is defined
        If self.backup_option.snapshot_rg = None
        Checks if snapshots are in disk resource group(disks present in different resource group but same region case)

        Raises:
                Exception: In validating custom snapshot resource group
        """
        try:
            if self.backup_option.snapshot_rg:
                self.log.info("Verifying custom RG for SNAP in resource group : {0}".format(
                    self.backup_option.snapshot_rg))
                custom_snapshot_rg = self.backup_option.snapshot_rg
            else:
                self.log.info("Custom Resource group for snapshot not defined, validating snaps in disk resource group")
                custom_snapshot_rg = None
            job_obj = self.backup_job
            for _vm in self.vm_list:
                if not self.auto_vsainstance.vsa_instance_name == "kubernetes" \
                        and self.auto_vsaclient.isIndexingV2:
                    _child_snap_job_id = self.get_childjob_foreachvm(self.backup_job.job_id)[_vm]
                    job_obj = Job(self.auto_commcell.commcell, _child_snap_job_id)
                    self.log.info("Created child job object for SNAP Job ID {0} for Indexing V2".format(
                        _child_snap_job_id))

                self.hvobj.VMs[_vm].verify_snapshot_rg(job_obj,
                                                       snapshot_rg=custom_snapshot_rg)

        except Exception as err:
            self.log.exception("Exception in Verifying custom RG for SNAP : %s" % str(err))

    def validate_snapshot(self, backup_type, backup_method):
        """
        Validations :
        Restore point: Disk restore point validation
                       Consistency mode validation
                       Custom Resource group validation
                       CBT snapshot deletion validation
        Snapshot: Custom Resource group validation
                  CBT snapshot deletion validation

        Args:
            backup_type                 (string):   Backup type of the job
            backup_method               (string):   Backup Method of the job

        Raises:
                Exception: In validating Snapshot/Restore point
        """
        try:

            if self.hvobj.instance_type in (hypervisor_type.AZURE_V2.value.lower(),
                                            hypervisor_type.AZURE.value.lower()):

                _appconsistent = self.subclient.quiesce_file_system

                #Validating disk restore points against disk for streaming and snap backup for Azure V2

                if _appconsistent:
                    self.vm_childJobs_restorepoint = self.get_childjob_foreachvm(self.backup_job.job_id)
                    for each_vm in self.vm_list:
                        self.log.info("Creating Child job object for VM {0}".format(each_vm))
                        _childJobid = self.vm_childJobs_restorepoint[each_vm]
                        _vm_client_obj = Client(self.auto_commcell.commcell, each_vm)
                        self.hvobj.VMs[each_vm].vm_subclientid = \
                            _vm_client_obj.properties['vmStatusInfo']['vmSubClientEntity']['subclientId']
                        job_obj = Job(self.auto_commcell.commcell, _childJobid)
                        self.validate_diskrestorepoint(job_obj, each_vm, _appconsistent)
                else:
                    # Check if snapshots are created under correct resource group
                    self.check_customrg_snapshot()

                #Checking previous full cbt snapshot/restorepoints exist for incremental backups
                self.cbt_check_snapshot(backup_type, backup_method)
            else:
                self.log.info("Snapshot Validation not applicable for this vendor")

        except Exception as err:
            self.log.exception("Exception in Snapshot / Restore Point Validation : %s" % str(err))

    def get_transport_mode(self):
        """
        Get the transport mode for the backup job

        Returns:
            transport_mode              (string):   Transport mode of the backup job
        """
        try:
            query = f"SELECT TOP 1 attrVal from App_subclientProp WHERE componentNameId = {self.subclient_id} \
            AND attrName LIKE 'Virtual Server Transport Mode' ORDER BY ID DESC"
            self.csdb.execute(query)

            transport_mode = {
                0: 'auto',
                1: 'san',
                2: 'hotadd',
                3: 'nas',
                4: 'nbdssl',
                5: 'nbd'
            }

            return transport_mode.get(int(self.csdb.fetch_one_row()[0]))

        except Exception as err:
            self.log.exception(f"Exception in getting transport mode : {str(err)}")