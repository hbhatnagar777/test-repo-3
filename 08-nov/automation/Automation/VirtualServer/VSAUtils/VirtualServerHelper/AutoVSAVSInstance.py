# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Instance Helper Class

classes defined:
    AutoVSAVSInstance - wrapper for VSA Instance operation
"""
import xmltodict
import socket
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor
from VirtualServer.VSAUtils import VirtualServerConstants
from VirtualServer.VSAUtils.VirtualServerConstants import hypervisor_type
from AutomationUtils import cvhelper, config


class AutoVSAVSInstance(object):
    """
    Class for perfoming Instance operations. Act as wrapper for SDK and testcases

    Methods:
            get_instance_name()     - gets the isntnace name for the agent

            get_instance_id()       - get the instance id of the associated isntance

            get_proxy_list()        - gets the list of proxies associated with isntance

            _create_hyperviosr_object- Initialize objects for hypervisor helper

            _compute_credentials()   - computes the credentials for hyperviors

    """

    def __init__(self, auto_client, agent, instance, tcinputs=None, **kwargs):
        """
        Initialize all the class properties of AutoVSAVSInstance class

        Args:
                agent   (obj)   - object of Agent class in SDK

                instance(obj)   - object for Instance class in SDK
        """
        self.auto_vsaclient = auto_client
        self.csdb = auto_client.csdb
        self.auto_commcell = auto_client.auto_commcell
        self.vsa_agent = agent
        self.vsa_instance = instance
        self.is_metallic = kwargs.get('is_metallic', None)
        self.metallic_ring_info = kwargs.get("metallic_ring_info", None)
        self.kwargs = kwargs
        if not self.vsa_instance.server_host_name and self.vsa_instance.instance_name.lower() == VirtualServerConstants.hypervisor_type.Xen.value.lower():
            query = f"select attrVal from App_InstanceProp where componentNameId = \
                    {self.vsa_instance.instance_id} and attrName like 'Virtual Server Host'"
            try:
                self.csdb.execute(query)
                self.vsa_instance.server_host_name = self.csdb.fetch_one_row()
            except Exception as err:
                self.log.exception(f"An exception occurred while fetching server host name: {err}")
        self.vsa_instance.fbr_MA_unix = None
        self.oci_private_file_name = None
        self.server_host_name = None
        if tcinputs is None:
            self.tcinputs = {}
        else:
            self.tcinputs = tcinputs
        self.vsa_instance_name = self.vsa_instance.instance_name
        self.vsa_instance_id = self.vsa_instance._instance_id
        self.log = self.auto_vsaclient.log
        self.config = config.get_config()
        self.sc_proxy_esx_host = None
        self.vsa_co_ordinator = None
        self.host_name = None
        self.creds = {}
        self.admin_creds = {}
        self.region = kwargs.get('region', None)
        self.vsa_proxy_list = self.get_proxy_list()

        self.hvobj = self._create_hypervisor_object()

    @property
    def proxy_list(self):
        """Returns Proxy list associated with that VSInstance . Read only attribute"""
        return self.vsa_proxy_list

    @proxy_list.setter
    def proxy_list(self, value):
        """
        set the list of Proxies as Proxy list in Instance level

        Args:
            value     (list) -list of proxies need to be set at instance level
        """
        try:
            self.vsa_instance.associated_clients = value

        except Exception as err:
            self.log.exception("An exception {0} has occurred \
                                while setting coordinator client ".format(err))

    @property
    def co_ordinator(self):
        """Retuens Proxy list assocaited witht hat VSInstance . Read only attribute"""
        if self.vsa_co_ordinator is None:
            self.vsa_co_ordinator = self.vsa_instance.co_ordinator

        return self.vsa_co_ordinator

    @co_ordinator.setter
    def co_ordinator(self, coordinator):
        """
        set the proxy given as coordinator

        Args:
            Coordinator - Proxy that needs to be set as coordinator
        """
        try:

            coordinator_client = self.auto_commcell.commcell.clients.get(coordinator)
            temp_vsa_proxy_list = [coordinator_client.client_name] + self.vsa_proxy_list
            self.vsa_proxy_list = list(set(temp_vsa_proxy_list))

            self.proxy_list = self.vsa_proxy_list

        except Exception as err:
            self.log.exception("An exception {0} has occurred \
                               while setting coordinator client ".format(err))

    @property
    def fbr_ma(self):
        """Returns FBRMA assocaited witht hat VSInstance . Read only attribute"""
        if self.vsa_instance.fbr_MA_unix:
            return self.vsa_instance.fbr_MA_unix
        else:
            fbr_query = "select net_hostname from APP_Client where id in " \
                        "(select attrVal from APP_InstanceProp where componentNameId = " \
                        + self.vsa_instance_id + \
                        " and attrName like '%FBR Unix MA%')"
            self.csdb.execute(query=fbr_query)
            fbr_host = self.csdb.fetch_one_row()
            if fbr_host[0] != '':
                self.vsa_instance.fbr_MA_unix = fbr_host[0]
            return self.vsa_instance.fbr_MA_unix

    @fbr_ma.setter
    def fbr_ma(self, fbr_ma_name):
        """
        Set the Proxy as FBR Ma for that Instance

        Args:
            fbr_ma_name : Ma that needs to be set as FBR Ma
        """
        self.vsa_instance.fbr_MA_unix = fbr_ma_name

    @property
    def server_credentials(self):
        """Retuens Server Credentials assocaited witht hat VSInstance . Read only attribute"""
        return self.host_name, self.user_name

    def get_instance_name(self):
        """
        set Instance Id Provided Virtualization client name
        """
        try:
            return self.vsa_instance.instance_name

        except Exception as err:
            self.log.exception(
                "An Exception occurred in setting the Instance Type %s" % err)
            raise err

    def get_instance_id(self):
        """
        returns the Instance id of that instance

        Return:
            instnace_id - Instance id of Instance associated with VS isntance

        exception:
                If there is no Instance
        """
        try:
            return self.vsa_instance.instance_id

        except Exception as err:
            self.log.exception(
                "ERROR - exception while getting instance id Exception:" + str(err))
            raise err

    def get_proxy_list(self):
        """
        get the Proxy List for the instance

        returns
                v_proxy_list    (dict)-- dict with proxy name as key and its
                                                                        corresponding id as value

        Exception:
                if vsa_client does not exist in cs

                failed to get  Instance property
        """
        try:
            if not self.kwargs.get('BYOS', True):
                self.vsa_co_ordinator = None
                return []
            self.vsa_co_ordinator = self.vsa_instance.co_ordinator
            return self.vsa_instance._get_instance_proxies()

        except Exception as err:
            self.log.exception(
                "An Exception occurred in creating the Hypervisor object  %s" % err)
            raise err

    def _create_hypervisor_object(self, client_name=None):
        """
        Create Hypervisor Object

        Exception:
                if initialization fails in creating object
        """
        try:
            if client_name is None:
                client_name = self.auto_vsaclient.vsa_client_name
                instance = self.vsa_instance

            else:
                client = self.auto_commcell.commcell.clients.get(client_name)
                agent = client.agents.get('Virtual Server')
                instance_keys = next(iter(agent.instances._instances))
                instance = agent.instances.get(instance_keys)

            host_machine1 = socket.gethostbyname_ex(socket.gethostname())[2][0]
            host_machine2 = instance.co_ordinator
            server_host_name = instance.server_host_name
            self.password = ''
            self._compute_credentials(client_name)
            self.user_name = self.creds.get('Virtual Server User', "").strip()
            _password = self.creds.get('Virtual Server Password', None)
            if _password:
                if self.is_metallic:
                    self.password = cvhelper.format_string(self.metallic_commcell, _password.strip())
                else:
                    self.password = cvhelper.format_string(self.auto_commcell.commcell, _password.strip())

            if self.vsa_instance_name.lower() == hypervisor_type.AZURE.value.lower() or \
                    self.vsa_instance_name.lower() == hypervisor_type.AZURE_V2.value.lower():
                id1 = self.creds.get('Azure Subscription Id', '').strip()
                id2 = self.creds.get('Azure Tenant Id', '').strip()
                _password1 = (self.password, id1, id2)
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   _password1, self.vsa_instance_name,
                                   self.auto_commcell.commcell, host_machine2)
            elif self.vsa_instance_name.lower() == hypervisor_type.Alibaba_Cloud.value.lower():
                self.password = self.creds.get('Alibaba Cloud Secret Key')
                self.password = cvhelper.format_string(self.auto_commcell.commcell, self.password.strip())
                self.user_name = self.creds.get('Alibaba Cloud Access Key')
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   self.password, self.vsa_instance_name,
                                   self.auto_commcell.commcell, host_machine1)
            elif self.vsa_instance_name.lower() == hypervisor_type.Vcloud.value.lower() and int(self.creds.get('org_client')):
                server_host_name = self.creds.get('server_host_name')
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   self.password, self.vsa_instance_name,
                                   self.auto_commcell.commcell, host_machine1, org_client=self.creds.get('org_client'))
            elif self.vsa_instance_name.lower() == hypervisor_type.AMAZON_AWS.value.lower():
                _admin_password = None
                if self.is_metallic:
                    _password2 = (self.creds.get(
                        'Virtual Server User',
                        cvhelper.format_string(self.metallic_commcell,
                                               self.creds.get('Amazon Center Access Key', '').strip())),
                                  cvhelper.format_string(
                                      self.metallic_commcell,
                                      self.creds.get(
                                          'Virtual Server Password',
                                          self.creds.get('Amazon Center Secret Key', '')).strip()))
                else:
                    _password2 = (self.creds.get(
                        'Virtual Server User',
                        cvhelper.format_string(self.auto_commcell.commcell,
                                               self.creds.get('Amazon Center Access Key', '').strip())),
                                  cvhelper.format_string(
                                      self.auto_commcell.commcell,
                                      self.creds.get(
                                          'Virtual Server Password',
                                          self.creds.get('Amazon Center Secret Key', '')).strip()))
                    if self.admin_creds:
                        _admin_password = (self.admin_creds.get(
                        'Virtual Server User',
                        cvhelper.format_string(self.auto_commcell.commcell,
                                               self.admin_creds.get('Amazon Center Access Key', '').strip())),
                                  cvhelper.format_string(
                                      self.auto_commcell.commcell,
                                      self.admin_creds.get(
                                          'Virtual Server Password',
                                          self.admin_creds.get('Amazon Center Secret Key', '')).strip()))
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   _password2, self.vsa_instance_name,
                                   self.auto_commcell.commcell, host_machine1, admin_password=_admin_password,
                                   **self.kwargs)
                if self.tcinputs.get('Automatic'):
                    proxies = self.vsa_instance._get_instance_proxies()
                    regions = []
                    for proxy in proxies:
                        proxy_ip = self.auto_commcell.get_hostname_for_client(proxy)
                        regions.append(hvobj.get_proxy_location(proxy_ip))
                    if len(set(regions)) == 1:
                        raise Exception("All the proxies in the Hypervisor are in the same region. Please add "
                                        "proxies from different regions to validate Distribute Workload")
                    else:
                        self.log.info("Hypervisor is configured properly and has proxies from different regions")
            elif self.vsa_instance_name == hypervisor_type.Google_Cloud.value.lower():
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   self.password, self.vsa_instance_name,
                                   self.auto_commcell.commcell, host_machine2,
                                   project_id=self.tcinputs['ProjectID'], replica_zone=self.tcinputs.get('replicaZone'),
                                   public_ip_address=self.tcinputs.get('publicIPaddress', ""),
                                   private_ip_address=self.tcinputs.get('privateIPaddress', ""),
                                   vm_custom_metadata=self.tcinputs.get('vmCustomMetadata', []),
                                   service_account=self.tcinputs.get("serviceAccount"))
            elif self.vsa_instance_name == hypervisor_type.MS_VIRTUAL_SERVER.value.lower() or \
                    self.vsa_instance_name == hypervisor_type.OPENSTACK.value.lower():
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   self.password, self.vsa_instance_name,
                                   self.auto_commcell.commcell, host_machine2)
            elif self.vsa_instance_name.lower() == \
                    hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.value.lower():
                '''
                We are going to pass all variables as part of a dict in the username field
                itself since there are not enough fields to hypervisor class
                and password will be passed as an empty string.
                You can see the dict def below
                '''
                server_host_name = instance.server_name
                try:
                    oci_private_key_file_path = self.config.Virtualization.oci.private_key_file_path
                except Exception as exp:
                    self.log.warning(exp)
                    self.log.info("Unable to get oci_private_key_file_path from config.json, reading from testcase.json")
                    oci_private_key_file_path = self.tcinputs['oci_private_key_file_path']
                self.creds['Oracle Cloud Infrastructure Private File Path'] = oci_private_key_file_path
                self.server_host_name = server_host_name
                oci_dict = {'oci_tenancy_id': self.creds['Oracle Cloud Infrastructure Tenancy Id'].strip(),
                            'oci_user_id': self.creds['Oracle Cloud Infrastructure User Id'].strip(),
                            'oci_finger_print': self.creds['Oracle Cloud Infrastructure Finger Print'].strip(),
                            'oci_private_key_file_path': self.creds['Oracle Cloud Infrastructure Private File Path'].strip(),
                            'oci_private_key_password': self.password,
                            'oci_region_name': self.creds['Oracle Cloud Infrastructure Region Name'].strip()
                            }
                if self.is_metallic:
                    oci_dict['oci_private_key_password'] = cvhelper.format_string(
                        self.metallic_commcell,
                        self.creds['Oracle Cloud Infrastructure Private Key Password'].strip())
                hvobj = Hypervisor(server_host_name, oci_dict, '',
                                   self.vsa_instance_name, self.auto_commcell.commcell, host_machine1)
            elif self.vsa_instance_name == hypervisor_type.Nutanix.value.lower():
                _password3 = (self.password, self.creds['Virtual Server Host'].strip())
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   _password3, self.vsa_instance_name,
                                   self.auto_commcell.commcell, host_machine2)

            elif self.vsa_instance_name == 'kubernetes':
                hvobj = None
                '''yet to be implemented'''

            else:
                hvobj = Hypervisor(server_host_name, self.user_name,
                                   self.password, self.vsa_instance_name,
                                   self.auto_commcell.commcell, host_machine1)
            return hvobj

        except Exception as err:
            self.log.exception(
                "An Exception occurred in creating the Hypervisor object  %s" % err)
            raise err

    def _compute_credentials(self, client_name):
        """Compute the credentials required to call the Vcenter"""

        try:
            _query = "select attrName, attrVal from app_Instanceprop where componentNameid =( \
                                              select TOP 1 instance  from APP_Application where clientId= ( \
                                              Select TOP 1 id from App_Client where name = '%s') and appTypeId = '106' and \
                                             attrName in %s)" % (client_name, VirtualServerConstants.attr_name)
            if self.is_metallic:
                from cvpysdk.commcell import Commcell
                from AutomationUtils.database_helper import CommServDatabase
                if self.metallic_ring_info:
                    temp_commcell = Commcell(self.metallic_ring_info['commcell'],
                                             commcell_username=self.metallic_ring_info['user'],
                                             commcell_password=self.metallic_ring_info['password'])

                    temp_csdb = CommServDatabase(temp_commcell)
                    temp_csdb.execute(_query)
                    _results = temp_csdb.fetch_all_rows()
                    self.metallic_commcell = temp_commcell

            else:
                self.csdb.execute(_query)
                _results = self.csdb.fetch_all_rows()
            if not _results:
                raise Exception("An exception occurred getting server details")
            '''
            Added below code to differentiate in compute creds for OCI from others.
            Original was wihtout the if/else 
            '''
            for rows in _results:
                self.creds[rows[0]] = rows[1]
            self.creds['org_client'] = self.creds.get('Amazon Admin Instance Id', 0)
            if int(self.creds.get('Amazon Admin Instance Id', 0)) > 0:
                _query = '''select attrName, attrVal from app_Instanceprop where componentNameid=( 
                                          select TOP 1 attrVal from app_Instanceprop where componentNameid= 
                                          (select TOP 1 instance  from APP_Application where clientId=  
                                          (Select TOP 1 id from App_Client where name = '%s') and appTypeId = '106'  
                                          and attrName in ('Amazon Admin Instance Id')))  
                                          and attrName in %s''' % (client_name, VirtualServerConstants.attr_name)
                self.csdb.execute(_query)
                _results = self.csdb.fetch_all_rows()
                if not _results:
                    raise Exception("An exception occurred in getting admin hypervisor credentials")
                for rows in _results:
                    self.admin_creds[rows[0]] = rows[1]
                if self.get_instance_name() == hypervisor_type.Vcloud.value.lower():
                    self.creds['server_host_name'] = self.admin_creds['Virtual Server Host']

            if int(self.creds.get('Virtual Server Credential Assoc Id', 0)) > 0:
                if int(self.creds.get('Amazon Admin Instance Id', 0)) > 0:
                    _query = '''select userName, password, credentialInfo from APP_Credentials join APP_CredentialAssoc 
                                            on APP_Credentials.credentialId = APP_CredentialAssoc.credentialId and 
                                            APP_CredentialAssoc.assocId = %s''' % (
                                            self.admin_creds['Virtual Server Credential Assoc Id'])
                    self.csdb.execute(_query)
                    _results = self.csdb.fetch_all_rows()
                    if not _results:
                        raise Exception("An exception occurred in getting admin hypervisor credentials")
                    self.admin_creds['Virtual Server User'] = _results[0][0]
                    self.admin_creds['Virtual Server Password'] = _results[0][1]
                _query = '''select userName, password, credentialInfo from APP_Credentials join APP_CredentialAssoc 
                        on APP_Credentials.credentialId = APP_CredentialAssoc.credentialId and 
                        APP_CredentialAssoc.assocId = %s''' % (self.creds['Virtual Server Credential Assoc Id'])
                if self.is_metallic:
                    temp_csdb = CommServDatabase(self.metallic_commcell)
                    temp_csdb.execute(_query)
                    _results = temp_csdb.fetch_all_rows()
                else:
                    self.csdb.execute(_query)
                    _results = self.csdb.fetch_all_rows()
                if not _results:
                    raise Exception("An exception occurred in getting hypervisor credentials from "
                                    " the saved credentials")

                if self.get_instance_name() == hypervisor_type.AZURE_V2.value.lower() and _results[0][1] != '':
                    _cred_info_dict = xmltodict.parse(_results[0][2])
                    self.creds['Azure Tenant Id'] = _cred_info_dict['App_AdditionalCredInfo']['azureCredInfo'][
                        '@tenantId']
                elif self.get_instance_name() == hypervisor_type.ORACLE_CLOUD_INFRASTRUCTURE.value.lower() and _results[0][2] != '':
                    _cred_info_dict = xmltodict.parse(_results[0][2])
                    self.creds['Oracle Cloud Infrastructure Finger Print'] = _results[0][0]
                    self.creds['Oracle Cloud Infrastructure Tenancy Id'] = _cred_info_dict['App_AdditionalCredInfo']['oracleCredentialInfo']['@tenancyOCID']
                    self.creds['Oracle Cloud Infrastructure User Id'] = _cred_info_dict['App_AdditionalCredInfo']['oracleCredentialInfo'][
                        '@userOCID']
                self.creds['Virtual Server User'] = _results[0][0]
                self.creds['Virtual Server Password'] = _results[0][1]

        except Exception as err:
            self.log.exception(
                "An Exception occurred in getting credentials for Compute Credentials  %s" % err)
            raise err

    def cbt_checks(self):
        try:
            host_dict = {}
            instanceno_dict = {}
            for each_proxy in self.proxy_list:
                host_name = self.auto_commcell.get_hostname_for_client(each_proxy)
                host_dict[each_proxy] = host_name
                instance_number = self.auto_commcell.get_instanceno_for_client(each_proxy)
                instanceno_dict[each_proxy] = instance_number
            self.hvobj.check_cbt_driver_running(self.proxy_list, host_dict)
            cbtstat_folder = self.hvobj.check_or_set_cbt_registry(
                self.proxy_list, host_dict, instanceno_dict)
            return cbtstat_folder
        except Exception as err:
            self.log.exception(
                "An Exception occurred in getting CBT driver status %s" % err)
            raise err

    def power_on_proxies(self, proxy_list):
        """
        Powers on all proxies whose names are given
        Proxies must be present on the same hypervisor as the instance
        Args:
            proxy_list (list<str>):
        Returns: none
        """
        vms_list = self.hvobj.get_all_vms_in_hypervisor()
        for vm in proxy_list:
            if vm in vms_list:
                try:
                    self.hvobj.VMs = vm
                    vm_obj = self.hvobj.VMs[vm]
                    vm_obj.power_on()
                except Exception:
                    self.log.warn('Unable to power on proxy with name: %s', vm)
            else:
                self.log.info('VM name %s not found on hypervisor', vm)

    def power_off_proxies(self, proxy_list):
        """
        Powers off all proxies whose names are given
        Proxies must be present on the same hypervisor as the instance
        Args:
            proxy_list (list<str>):
        Returns: none
        """
        vms_list = self.hvobj.get_all_vms_in_hypervisor()
        for vm in proxy_list:
            if vm in vms_list:
                try:
                    self.hvobj.VMs = vm
                    vm_obj = self.hvobj.VMs[vm]
                    vm_obj.power_off()
                except Exception:
                    self.log.warn('Unable to power off proxy with name: %s', vm)
            else:
                self.log.info('VM name %s not found on hypervisor', vm)
