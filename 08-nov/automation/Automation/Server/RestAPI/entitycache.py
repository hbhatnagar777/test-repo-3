# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing EntityCache API  related operations

EntityCacheHelper is the only class defined in this file

EntityCacheHelper: Helper class to perform EntityCache API operations

EntityCacheHelper:

 __init__()                      --  initializes EntityCache API helper object

validatelogs()                   --  validates the log file for entity cache

calculate()                      -- Sends api request to server and calcualtes response times

stop_service()                   -- Stop mongodb service on commserv

construct_query()                -- constructs query required for server

send_validate_log_count()        -- find and return log lines with required string.

validate_device_response()       -- Validates response json based on constraints
                                    passed for laptop page

validate_server_response()       -- Validates response json based on constraints
                                    passed for server page

validate_vmgroup_response()      --  Validates response json based on constraints
                                    passed for vmgroup page

"""

import http.client as httplib
import requests
from AutomationUtils.machine import Machine


class EntityCacheHelper():
    """Helper class to perform EntityCache API operations"""

    def __init__(self, commcell, client, webconsole, page='device', log=None):
        """Initializes Entitycache object """
        self.log = log
        self.page = page
        self.commcell = commcell
        self.client = client
        self.csmachine = Machine(self.client)
        self.logfile_to_check = 'CVEntityCache.log'
        self.validatelog = self.csmachine.join_path(
            self.client.log_directory, self.logfile_to_check)
        self.responsetimes = []
        self.failed_requests = []
        if self.page == 'device':
            self.browser_urls = "http://{}/webconsole/api/{}?".format(webconsole, self.page)
            self.constraint_dict = {'client': '', 'plan': '', 'owners': '', 'search': ''}
            self.client_query = """fq=deviceSummary.clientName%3Acontains%3A{}&"""
            self.plan_query = """fq=deviceSummary.planName%3Acontains%3A{}&"""
            self.owners_query = """fq=deviceSummary.clientOwners%3Acontains%3A{}&"""
            self.search_query = ("Search=clientsFileSystem.subClient.clientName," +
                                 "clientsFileSystem.plan.planName," +
                                 "clientsFileSystem.clientOwners.owners.userName%3Acontains%3A{}&")
            self.fl_query = "Fl=clientsFileSystem.subClient&"
            self.sort = 'Sort=deviceSummary.clientName:-1&'
            self.sort_des_query = "sort=clientsFileSystem.subClient.clientName:-1&"
            self.sort_asc_query = "sort=clientsFileSystem.subClient.clientName:1&"
            self.fl_sub_query = "Fl=clientsFileSystem.subClient.clientName&"
            self.string_to_search = r'Processing GET request on Cache. Entity : \[DEVICE\]'
            self.string_to_search_python = 'Processing GET request on Cache. Entity : [DEVICE]'

        if self.page == 'vmgroup':
            self.constraint_dict = {'subclient': '', 'client': '', 'instance': '', 'search': ''}
            self.browser_urls = ("http://{}/webconsole/api/Subclient?".format(webconsole) +
                                 "clientId=0&applicationId=106&" +
                                 "PropertyLevel=20&includeVMPseudoSubclients=false&")
            self.responsetimes = []
            self.subclient_query = ("fq=subClientProperties.subClientEntity." +
                                    "subclientName%3Acontains%3A{}&")
            self.client_query = ("fq=subClientProperties.subClientEntity." +
                                 "clientName%3Acontains%3A{}&")
            self.instance_query = ("fq=subClientProperties.subClientEntity." +
                                   "instanceName%3Acontains%3A{}&")
            self.search_query = (
                "Search=subClientProperties.subClientEntity.subclientName," +
                "subClientProperties.subClientEntity.clientName," +
                "sc.planEntity.planName," +
                "subClientProperties.subClientEntity.instanceName%3Acontains%3A{}&")
            self.sort = 'Sort=subClientProperties.subClientEntity.subclientName:-1&'
            self.fl_query = "Fl=overview,subClientProperties.subClientEntity"
            self.sort_des_query = "sort=subClientProperties.subClientEntity.subclientName:-1&"
            self.sort_asc_query = "sort=subClientProperties.subClientEntity.subclientName:1&"
            self.fl_sub_query = "Fl=overview,subClientProperties.subClientEntity.subclientName&"
            self.string_to_search = r'Processing GET request on Cache. Entity : \[VMGROUP\]'
            self.string_to_search_python = 'Processing GET request on Cache. Entity : [VMGROUP]'

        if self.page == 'server':
            self.browser_urls = (
                "http://{}/webconsole/api/Client?Hiddenclients=false&".format(webconsole) +
                "includeIdaSummary=true&propertylevel=10&includevm=true&" +
                "excludeInfrastructureClients=false&start=0&")
            self.constraint_dict = {'subclient': '', 'client': '', 'instance': '', 'search': ''}
            self.client_query = """fq=client.clientEntity.displayName%3Acontains%3A{}&"""
            self.plan_query = """fq=deviceSummary.planName%3Acontains%3A{}&"""
            self.search_query = ("Search=clientProperties.client.clientEntity.displayName," +
                                 "clientProperties.client.idaList.idaEntity.appName," +
                                 "clientProperties.client.osInfo.OsDisplayInfo.OSName," +
                                 "clientProperties.client.versionInfo.version," +
                                 "clientProperties.client.clientEntity.hostName%3Acontains%3A{}&")
            self.fl_query = "Fl=clientsFileSystem.subClient"
            self.sort = 'sort=clientProperties.client.clientName:-1&'
            self.sort_des_query = "sort=clientProperties.client.clientName:-1&"
            self.sort_asc_query = "sort=clientProperties.client.clientName:1&"
            self.fl_sub_query = "Fl=clientProperties.client.clientName&"
            self.string_to_search = r'Processing GET request on Cache. Entity : \[SERVER\]'
            self.string_to_search_python = 'Processing GET request on Cache. Entity : [SERVER]'

        self.start_5 = "start=5&"
        self.start_0 = "start=0&"
        self.limit = "Limit=20&"
        self.hf_refresh = "hardRefresh=1&"
        self.iter = 0

    @property
    def validatelogs(self):
        '''
        checks the log for specified string.
        @args
            client_machine (Machine)      -- Client machine object
            validatelog (string)           -- full path of the log to validate
            logstrings_to_verify  (string) -- log string to verify

        '''
        if self.csmachine.check_file_exists(self.validatelog):
            qscript = "Select-String -Path {} -Pattern \"{}\"".format(
                self.validatelog.replace(" ", "' '"), self.string_to_search)
            #self.log.info("Executing qscript [{0}]".format(qscript))
            response = self.csmachine.execute_command(qscript)
            data = self.string_to_search.replace("\\", "").replace("Cache", "\r\nCache")
            count = 0
            lines = response.output.split("Api_CommcellEntityListReq")
            for line in lines:
                if line.find(data) >= 0:
                    count = count + 1
            return count
        else:
            self.log.info("file {} not found".format(self.validatelog))
            return 0

    def calculate(self, url, ret_data=True):
        '''
        Sends api request to server and calcualtes response times
        @args:
            url (string): url to send to server
            ret_data (boolean): returns response data based on boolean value passed

        '''
        headers = None
        url = url
        if headers is None:
            headers = self.commcell._headers.copy()
            if self.page == 'device':
                headers['LookupNames'] = 'false'
                headers['FormatOutput'] = 'false'
            elif self.page == 'server':
                headers['mode'] = 'EdgeMode'
        response = requests.get(url, headers=headers, stream=False)
        if response.status_code == httplib.UNAUTHORIZED:
            self.failed_requests.append(url)
        if response.status_code == httplib.OK and response.ok:
            self.responsetimes.append(response.elapsed.total_seconds())
        if ret_data:
            return response.json()

    def stop_service(self, stop=False):
        """
        Stop mongodb service on commserv

        @args:
            stop (boolean) : if True, it stops services otherwise starts service.
        """

        if stop:
            self.log.info("Stopping Time Service")
            service_command = 'net stop "GxMONGO(Instance001)"'
            expected_output = ["stopped successfully", "not started"]
        else:
            self.log.info("Starting Time Service")
            service_command = ('net start "GxMONGO(Instance001)"')
            expected_output = ["started successfully", "already been started"]
        service_output = self.csmachine.execute_command(service_command)
        if not any(x in service_output.output for x in expected_output):
            if service_output.exception_message.find(
                    "The requested service has already been started") < 0:
                if service_output.exception_message.find(
                        "The requested service has already been stopped") < 0:
                    raise Exception(
                        "Mongodb service could not be stopped with exception: {0}".format(
                            service_output.exception_message))

    def construct_query(self, values):
        """
        constructs query required for server
        @args:
            values (dict) : pass values in dictionary format.
        """

        fq_query = ""
        for key in values.keys():
            if values[key] and key == 'client':
                fq_query = fq_query + self.client_query.format(values[key])
            elif values[key] and key == 'subclient':
                fq_query = fq_query + self.subclient_query.format(values[key])
            elif values[key] and key == 'plan':
                fq_query = fq_query + self.plan_query.format(values[key])
            elif values[key] and key == 'instance':
                fq_query = fq_query + self.instance_query.format(values[key])
            elif values[key] and key == 'search':
                fq_query = fq_query + self.search_query.format(values[key])
            elif values[key] and key == 'owners':
                fq_query = fq_query + self.owners_query.format(values[key])
        return fq_query

    def send_validate_log_count(self, url):
        """
        find and return log lines with required string.
        """
        cachecount_before = self.validatelogs
        response = self.calculate(url, True)
        cachecount_after = self.validatelogs
        if cachecount_after > cachecount_before:
            self.log.info("Request is sent to EntityCache")
        else:
            raise Exception("""Number of log lines before {%s} and after {%s}
             request are same or less. Means request is not sent to
              Cache""" % cachecount_before, cachecount_after)
        return response

    def validate_device_response(self, res_json, constraint=None, complete=False):
        '''
        Validates response json based on constraints passed for laptop page

        @args:

        res_json (dictonary) : response Json.
        constraint (dictionary) : Pass constraint in dictionary format
        complete (boolean): validate complete response based on boolean value passed

        '''

        client_constraint = constraint['client']
        plan_constraint = constraint['plan']
        owners_constraint = constraint['owners']
        search_constraint = constraint['search']
        invalid_dict = {'client': [], 'plan': [], 'owners': [], 'search': []}
        if 'clientsFileSystem' in res_json:
            vmgroup_info = res_json['clientsFileSystem']
        else:
            return False, invalid_dict
        flag = False
        search_flag = 0

        for grp_info in vmgroup_info:
            entity = grp_info['subClient']
            if search_constraint:
                search_flag = 1

            if client_constraint or search_flag == 1:
                clientname = grp_info['subClient']['clientName']
                if clientname.lower().find(client_constraint.lower()) >= 0 or search_flag == 1:
                    if search_flag == 1 and clientname.lower().find(
                            search_constraint.lower()) >= 0:
                        search_flag = 2
                    if complete:
                        pass
                    else:
                        break
                else:
                    invalid_dict['client'].append(grp_info)
                    flag = True
            if plan_constraint or search_flag == 1:
                if 'plan' in grp_info:
                    entity = grp_info['plan']
                else:
                    invalid_dict['plan'].append(grp_info)
                    flag = True
                    continue
                try:
                    planname = grp_info['plan']['planName']
                    if planname.lower().find(plan_constraint.lower()) >= 0 or search_flag == 1:
                        if search_flag == 1 and planname.lower().find(
                                search_constraint.lower()) >= 0:
                            search_flag = 2
                        if complete:
                            pass
                        else:
                            break
                    else:
                        invalid_dict['plan'].append(grp_info)
                        flag = True
                except Exception as excp:
                    self.log.error("Exception in validating response %s" % excp)
            if owners_constraint or search_flag == 1:
                if 'clientOwners' in grp_info:
                    entity = grp_info['clientOwners']
                else:
                    invalid_dict['owners'].append(grp_info)
                    flag = True
                    continue
                try:
                    all_owners = entity['owners']
                    found_owner = 0
                    for owner in all_owners:
                        if 'userName' in owner:
                            if owner['userName'].lower().find(
                                    owners_constraint.lower()) >= 0 or search_flag == 1:
                                if search_flag == 1 and owner['userName'].lower(
                                ).lower().find(search_constraint) >= 0:
                                    search_flag = 2
                                if complete:
                                    pass
                                else:
                                    break
                            found_owner = 1
                    if found_owner == 0:
                        invalid_dict['owners'].append(grp_info)
                        flag = True
                except Exception as excp:
                    self.log.error("Exception raised %s" % excp)
            if search_constraint and search_flag != 2:
                invalid_dict['search'].append(entity)
                flag = True
        if self.iter == 0:
            if len(vmgroup_info) > 0 and flag:
                flag = False
        return flag, invalid_dict

    def validate_vmgroup_response(self, res_json, constraint=None, complete=False):
        '''
        Validates response json based on constraints passed for vmgroup page

        @args:

        res_json (dictonary) : response Json.
        constraint (dictionary) : Pass constraint in dictionary format
        complete (boolean): validate complete response based on boolean value passed

        '''

        subclient_constraint = constraint['subclient']
        client_constraint = constraint['client']
        insance_constraint = constraint['instance']
        search_constraint = constraint['search']
        invalid_dict = {'subclient': [], 'client': [], 'instance': [], 'search': []}
        if 'subClientProperties' in res_json:
            vmgroup_info = res_json['subClientProperties']
        else:
            return False, invalid_dict
        flag = False
        search_flag = 0

        for grp_info in vmgroup_info:
            entity = grp_info['subClientEntity']
            if search_constraint:
                search_flag = 1

            if subclient_constraint or search_flag == 1:
                subclientname = grp_info['subClientEntity']['subclientName']
                if subclientname.lower().find(
                        subclient_constraint.lower()) >= 0 or search_flag == 1:
                    if search_flag == 1 and subclientname.lower().find(
                            search_constraint.lower()) >= 0:
                        search_flag = 2
                    if complete:
                        pass
                    else:
                        break
                else:
                    invalid_dict['subclient'].append(entity)
                    flag = True
            if client_constraint or search_flag == 1:
                clientname = grp_info['subClientEntity']['clientName']
                if clientname.lower().find(client_constraint.lower()) >= 0 or search_flag == 1:
                    if search_flag == 1 and clientname.lower().find(
                            search_constraint.lower()) >= 0:
                        search_flag = 2
                    if complete:
                        pass
                    else:
                        break
                else:
                    invalid_dict['client'].append(entity)
                    flag = True
            if insance_constraint or search_flag == 1:
                instancename = grp_info['subClientEntity']['instanceName']
                if instancename.lower().find(
                        insance_constraint.lower()) >= 0 or search_flag == 1:
                    if search_flag == 1 and instancename.lower().find(
                            search_constraint.lower()) >= 0:
                        search_flag = 2
                    if complete:
                        pass
                    else:
                        break
                else:
                    invalid_dict['instance'].append(entity)
                    flag = True
            if search_constraint and search_flag != 2:
                invalid_dict['search'].append(entity)
                flag = True
        if self.iter == 0:
            if len(vmgroup_info) > 0 and flag:
                flag = False
        return flag, invalid_dict

    def validate_server_response(self, res_json, constraint=None, complete=False):
        ''''
        Validates response json based on constraints passed for server page

        @args:

        res_json (dictonary) : response Json.
        constraint (dictionary) : Pass constraint in dictionary format
        complete (boolean): validate complete response based on boolean value passed

        '''

        client_constraint = constraint['client']
        appname_constraint = constraint['appname']
        os_constraint = constraint['osname']
        version_constraint = constraint['version']
        hostname_constraint = constraint['hostname']
        search_constraint = constraint['search']
        invalid_dict = {
            'appname': [],
            'client': [],
            'osname': [],
            'hostname': [],
            'version': [],
            'search': []}
        vmgroup_info = res_json['clientProperties']
        flag = False
        search_flag = 0

        for grp_info in vmgroup_info:

            if search_constraint:
                search_flag = 1

            if hostname_constraint or search_flag == 1:
                hosstname = grp_info['client']['clientEntity']['hostName']
                if hostname_constraint.lower().find(hosstname.lower()) >= 0 or search_flag == 1:
                    if search_flag == 1 and search_constraint.lower().find(hosstname.lower()) >= 0:
                        search_flag = 2
                    if complete:
                        pass
                    else:
                        break
                else:
                    invalid_dict['hostname'].append(grp_info)
                    flag = True
            if version_constraint or search_flag == 1:
                versionname = grp_info['client']['versionInfo']['version']
                if version_constraint.lower().find(
                        versionname.lower()) >= 0 or search_flag == 1:
                    if search_flag == 1 and search_constraint.lower().find(
                            versionname.lower()) >= 0:
                        search_flag = 2
                    if complete:
                        pass
                    else:
                        break
                else:
                    invalid_dict['osname'].append(grp_info)
                    flag = True
            if os_constraint or search_flag == 1:
                osname = grp_info['client']['osInfo']['OsDisplayInfo']['OSName']
                if os_constraint.lower().find(osname.lower()) >= 0 or search_flag == 1:
                    if search_flag == 1 and search_constraint.lower().find(
                            osname.lower()) >= 0:
                        search_flag = 2
                    if complete:
                        pass
                    else:
                        break
                else:
                    invalid_dict['osname'].append(grp_info)
                    flag = True
            if client_constraint or search_flag == 1:
                clientname = grp_info['client']['clientEntity']['displayName']
                if client_constraint.lower().find(clientname.lower()) >= 0 or search_flag == 1:
                    if search_flag == 1 and search_constraint.lower().find(
                            clientname.lower()) >= 0:
                        search_flag = 2
                    if complete:
                        pass
                    else:
                        break
                else:
                    invalid_dict['client'].append(grp_info)
                    flag = True
            if appname_constraint or search_flag == 1:
                if 'idaEntity' in grp_info['client']['idaList']:
                    appname = grp_info['client']['idaList']['idaEntity']['appName']
                else:
                    appname = grp_info['client']['idaList']['appName']
                if appname_constraint.lower().find(appname.lower()) >= 0 or search_flag == 1:
                    if search_flag == 1 and search_constraint.lower().find(appname.lower()) >= 0:
                        search_flag = 2
                    if complete:
                        pass
                    else:
                        break
                else:
                    invalid_dict['appname'].append(grp_info)
                    flag = True
            if appname_constraint or search_flag == 1:

                appname = grp_info['client']['idaList']['appName']
                if appname_constraint.lower().find(appname.lower()) >= 0 or search_flag == 1:
                    if search_flag == 1 and search_constraint.lower().find(appname.lower()) >= 0:
                        search_flag = 2
                    if complete:
                        pass
                    else:
                        break
                else:
                    invalid_dict['appname'].append(grp_info)
                    flag = True

            if search_constraint and search_flag != 2:
                invalid_dict['search'].append(grp_info)
                flag = True
        if self.iter == 0:
            if len(vmgroup_info) > 0 and flag:
                flag = False
        return flag, invalid_dict
