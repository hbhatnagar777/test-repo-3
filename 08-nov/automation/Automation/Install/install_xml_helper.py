# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations for silent install

InstallXMLGenerator
===================

    __init__()                          --  initialize instance of the silent install class
    write_xml_to_file                   --  Write an Elemet Tree to an XML file
    silent_install_xml                    --  Helps to generate XML for fresh installations
    install_flags                       --  Installer Flags required for the client installation
    firewall_install_flag               --  Firewall Configuration required for generating XML
    create_xml_file_for_remote          --  Writes root object of the Element Tree to an XML file

    _set_client_auth_node               --  Details for the client authenticaion on XML for silent install
    _set_commserve_info_xml             --  Details for the commserve registration on XML for silent install
    _client_composition_node            --  Consist the information of the client info and packages to be installed
    _client_info_node                   --  Client group_name and log location info
    _client_node                        --  Fills XML with Client install directory, os info, certificate
    _components_node                    --  Fills the xml with list of packages to be installed and their depedencies
    _create_commserve_node              --  Sets the commserve information on the XML
    _oem_info_node                      --  Sets the OEM information on the XML
    _cs_db_info                         --  Sets the commserve Database information on the XML
    _cvsql_admin_node                   --  Sets the SQL databse sa password
    _dr_path_node                       --  Sets the Distaster Recovery Path
    _ftp_location_node                  --  FTP location of where the CS is being installed from
    _create_index_cache_dir             --  Sets the index store location for the media agent
    _create_dm2_webservice_node         --  Sets the flags and dump location for the DM2 Webservice
    _create_commcell_console_node       --  Sets the commcell information/flags on the XML
    _create_web_console_node            --  Sets the webconsole information/flags on the XML
    _configure_for_laptop_backups_node  --  Sets the laptop backups information on the XML
    _selected_subclient_policy_node     --  Sets the subclient policy information on the XM
    _create_workflow_engine_node        --  Sets the workflow information on the XML
    _create_cdr_logdir                  --  Sets the ContinuousDataReplicator information on the XML
    _create_tsa_login_node              --  Sets the Tivoli System Automation(TSA) information on the XML
    _create_obj_server_node             --  Sets the obj server node information on the XML
    _create_db2_path                    --  Sets the db2 node information on the XML
    _create_edc_groups                  --  Sets the edc group node information on the XML
    _create_oracle_sap_node             --  Sets the oracle sap node information on the XML
    _common_info_node                   --  Sets the common info/flags information on the XML
    _client_roles_node                  --  Sets the client roles node information on the XML
    _installer_flags_unix               --  Installer flags for Unix Installation
    _installer_flags_windows            --  Installer flags for Windows Installations
    _sql_install_node                   --  Sets the sql install node information on the XML

"""
import os
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring
from AutomationUtils import logger
from AutomationUtils import constants
from AutomationUtils import config
from base64 import b64encode


class InstallXMLGenerator:

    def __init__(self, client_name, machine_obj, inputs):
        """
            Initialize instance of the InstallXMLGenerator class.
                Args:
                    client_name -- Client Name provided for installation

                    machine_obj -- machine object

                    inputs (dict)
                    --  Inputs for Installation should be in a dictionary
                        Supported key / value for inputs:

                            Mandatory:
                                csClientName        (str)        Commserve Client Name
                                csHostname          (str)        Commserve Hostname
                                commservePassword:  (str)        Commserve encrypted login password

                            Optional:
                                oem_id               (str)        OEM id to be installed
                                commserveUsername   (str)        Commserve Username
                                useExistingDump     (str)        Use existing dump for Dm2 / Workflow Engine
                                useExsitingCSdump   (str)        Use CS dump ("0" or "1")
                                CommservDumpPath    (str)        Dump path for Commserve
                                install32base       (str)        install 32bit software on 64bit Machine
                                restoreOnlyAgents   (str)       "0 or "1"
                                DM2DumpPath         (str)        Dump path for DM2 webservice
                                WFEngineDumpPath    (str)        Dump path for Workflow Engine
                                decoupledInstall    (str)        "0 or "1"
                                enableFirewallConfig (str)       "0 or "1"
                                firewallConnectionType (str)     "1" or "2"
                                httpProxyConfigurationType(str)  "0" or "1" or "2"
                                httpProxyPortNumber (str)        Port Number eg: "6256"
                                httpProxyHostName   (str)        Hostname of the proxy machine
                                portNumber          (str)        Port number to connect to the CVD eg:8410
                                enableProxyClient   (str)        Enable Client as a proxy "0" or "1"
                                proxyClientName     (str)        Proxy Client Name / Client Name on the commcell
                                proxyHostname       (str)        Proxy Client Hostname eg: Exp1.cmvt.com;exp2.cmvt.com
                                proxyPortNumber     (str)        Proxy client Port Number eg: 8403;8408;8412
                                sqlSaPassword       (str)        Sa (user) password for SQL access
                                installDirectoryUnix(str)        Path on which software to be installed on Unix Client
                                installDirectoryWindows(str)     Path on which software to be installed on Win Client
                                clientGroupName(str)             Client Group on the CS
                                networkGateway(str)              Network Gateway flag - client uses to connect to CS
                                mediaPath           (str)        Filer Path required for Unix installations (Path till CVMedia)
                                launchRolesManager  (str)        "0" or "1"
                                selectedRoles       (list)       List of roles to be installed with roles manager
                                runServiceAsRoot            (str)        "0" or "1" (Default is "1" - root user)

        """
        self.log = logger.get_log()
        self.inputs = inputs
        self.client_name = client_name
        self.machine_obj = machine_obj
        self.os_type = self.machine_obj.os_info.lower()
        self.xml_flags = None
        self.config_json = config.get_config()
        self.install_new_cs = False

    def write_xml_to_file(self, element, file_name="install_XML.xml"):
        """
            Module that helps to write the generated XML to file (file.xml)
        :param
            element: (root) -- Root Node of an XMl / ELement Tree

        :return:
            Path of the XML  file
        """
        try:
            oem_id = element.attrib.get("OEMID", 1)
            if isinstance(oem_id, int):
                element.attrib["OEMID"] = str(oem_id)
            rough_string = tostring(element, encoding='utf-8')
            reparsed = minidom.parseString(rough_string)
            parsed_string = (reparsed.toprettyxml(indent="\t", encoding='UTF-8').decode("utf-8")).replace(
                '<?xml version="1.0" encoding="UTF-8"?>', '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>')
            final_xml_string = '\n'.join([line for line in parsed_string.split('\n') if line.strip()])
            xml_path = self.create_xml_file_for_remote(final_xml_string, file_name)
            return xml_path

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in writing XML to a file")

    def get_xml_flags(self):
        if "windows" in self.os_type:
            flags = {
                "Focus": self.inputs.get("instance", "New"),
                "LocaleID": "0",
                "Operationtype": "0",
                "requestType": "1",
                "requestFlags": "0",
                "oemId": self.inputs.get("oem_id", "1"),
                "RemoteClient": "0",
                "byteOrder": "Little-endian",
                "installDirectory": self.inputs.get("installDirectoryWindows", ""),
                "GalaxyBuildNumber": "BUILD80",
                "ReleaseString": "11.0",
                "OSName": "",
                "OSBuild": "9200",
                "cvdPort": "",
                "jobResultsPath": r"%InstallFolder%\iDataAgent\JobResults",
                "cvSQLPassword": "||#05!M2Y5ZDc0YzM1OGZlMTk0MjUyYjRlMmVhMmI3NGM2MmE4MmQ0MDljODU4NjAy" +
                                 "ZTQ4YTU4NzIxOTIyOGE5YzRhNDhhMWNiNWU3ZjY0Yzg4MWE3NzU1N2Q3NGI2MmRlZmE0ZQ==",
                "drPath": "c:\\DR",
                "indexCachePath": r"%InstallFolder%\IndexCache",
                "xmlViewWebAlias": "xmlview",
                "searchSvcWebAlias": "'SearchSvc",
                "dm2WebSitePort": "0",
                "apachePortNumber": "0",
                "dm2DataFileInstallPath": r"%InstallFolder%\Data\Data",
                "webConsoleURL": f"http://{self.machine_obj.machine_name}/webconsole/clientDetails/fsDetails.do?clientName=CLIENTNAME",
                "webConsolePort": "0",
                "webURL": f"http://{self.machine_obj.machine_name}/webconsole",
                "webServerClientId": self.inputs.get("webserverClientID", ''),
                "messagequeueAMQPPort": "",
                "messagequeueDataDir": "",
                "messagequeueWebconsolePort": "0",
                "messagequeueTCPPort": "0",
                "messagequeueMaxJvm": "0",
                "messagequeueMinJvm": "0",
                "messagequeueMQTTPort": "0",
                "messagequeueWSPort": "0",
                "commonInfoGlobalFilters": "0",
                "useExistingStoragePolicy": "0",
                "storagePolicyId": "1",
                "storagePolicyName": "CV_DEFAULT"
            }

        else:
            flags = {
                "Focus": self.inputs.get("instance", "New"),
                "LocaleID": "0",
                "Operationtype": "0",
                "requestType": "1",
                "requestFlags": "0",
                "oemId": self.inputs.get("oem_id", "1"),
                "RemoteClient": "0",
                "logFilesLocation": "/var/log",
                "installDirectory": self.inputs.get("installDirectoryUnix", "/opt"),
                "clientCertificate": self.inputs.get("clientCertificate", ""),
                "cvdPort": "",
                "evmgrcPort": "",
                "jobResultsPath": "",
                "indexCachePath": "",
                "xmlViewWebAlias": "xmlview",
                "searchSvcWebAlias": "'SearchSvc",
                "dm2WebSitePort": "5000",
                "apachePortNumber": "80",
                "dm2DataFileInstallPath": "/opt/Data/DM2",
                "webConsoleURL": f"http://{self.machine_obj.machine_name}/webconsole/clientDetails/fsDetails.do?clientName=CLIENTNAME",
                "webConsolePort": "0",
                "webURL": f"http://{self.machine_obj.machine_name}/webconsole",
                "webServerClientId": self.inputs.get("webserverClientID"),
                "messagequeueAMQPPort": "",
                "messagequeueDataDir": "",
                "messagequeueWebconsolePort": "",
                "messagequeueTCPPort": "",
                "messagequeueMaxJvm": "",
                "messagequeueMinJvm": "",
                "messagequeueMQTTPort": "",
                "messagequeueWSPort": "",
                "messagequeueStompPort": "",
                "commonInfoGlobalFilters": "0",
                "useExistingStoragePolicy": "0",
                "storagePolicyId": "1",
                "storagePolicyName": "CV_DEFAULT"
            }

        return flags

    def silent_install_xml(self, pkg_dict):
        """
            Helps to generate XML for fresh installations
                :param
                    pkg_dict: Dictionary of packages to be installed and which is to be written on XML

                :return:
                    root - (root)  -- root of an XML generated by Element Tree Module
        """
        try:
            self.xml_flags = self.get_xml_flags()
            root = Element('CVInstallManager_ClientSetup')
            root.set('Focus', self.xml_flags.get("Focus"))
            root.set('LocaleID', self.xml_flags.get("LocaleID"))
            root.set('Operationtype', self.xml_flags.get("Operationtype"))
            root.set('requestType', self.xml_flags.get("requestType"))
            root.set('requestFlags', self.xml_flags.get("requestFlags"))
            root.set('OEMID', self.xml_flags.get("oemId"))
            root.set('RemoteClient', self.xml_flags.get("RemoteClient"))
            self.log.info("Root Element Created Successfully")
            if "20" in pkg_dict.keys() or "1020" in pkg_dict.keys():
                self.install_new_cs = True

            else:
                use_authcode = False
                if self.inputs.get("authCode") is not None and self.inputs.get("authCode") != "":
                    use_authcode = True
                root.append(self._set_client_auth_node(use_authcode=use_authcode))
                self.log.info("Client Authentication Node is done")

            root.append(self._set_commserve_info_xml())
            self.log.info("Commserve Info Node is done")
            root.append(self._client_composition_node(pkg_dict))
            self.log.info("Client Composition Node is done")
            root.append(self.install_flags())
            usernode = Element('User')
            usernode.set('userId', '1')
            root.append(usernode)

            self.log.info("Install Flags Node is done")
            return root

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("An Exception occurred while generating an XML")

    def _set_client_auth_node(self, use_authcode=False):
        """
            Details for the client authenticaion on XML for silent install
            For Client Authentication, password should be v3 encoded
            :param
                use_authcode: Flag to use Authcode for registration with CS
                    default: False

            :return:
                Client Authentication Element Tree Node
        """
        try:
            if use_authcode:
                org_properties = Element('organizationProperties')
                org_properties.set("authCode", self.inputs.get("authCode", ""))
                return org_properties

            else:
                client_auth_node = Element('ClientAuthentication')
                client_auth_info_node = SubElement(client_auth_node, 'userAccountToLogin')
                if "commserveUsername" in self.inputs.keys():
                    client_auth_info_node.set("userName", self.inputs.get("commserveUsername"))

                else:
                    client_auth_info_node.set("userName", "admin")

                if self.inputs.get("decoupledInstall") == "1":
                    cs_password = ""
                else:
                    if "commservePassword" in self.inputs.keys():
                        cs_password = self.inputs.get("commservePassword")
                    else:
                        raise Exception("commservePassword not found. PLease provide commservePassword input")

                if "windows" in self.os_type:
                    encrypted_password = b64encode(cs_password.encode()).decode()
                    encrypted_password = "||#05!" + encrypted_password
                    client_auth_info_node.set("password", encrypted_password)
                else:
                    client_auth_info_node.set("plainTextPwd", cs_password)

                return client_auth_node

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Client Authentication failed")

    def _set_commserve_info_xml(self):
        """
            Details for the commserve registration on XML for silent install
        :return:
            Commserve creds Element Tree Node
        """
        try:
            commserve_info = Element('CommServeInfo')
            commserve_host = SubElement(commserve_info, 'CommserveHostInfo')
            cs_name = self.inputs.get("csClientName", "@@COMMSERVE@@")
            cs_hostname = self.inputs.get("csHostname", "@@COMMSERVE@@")
            cs_networkgateway = self.inputs.get("networkGateway", "")
            commserve_info.set('networkGateway', cs_networkgateway)
            commserve_host.set('clientName', self.client_name if self.install_new_cs else cs_name)
            commserve_host.set('hostName',
                               self.machine_obj.machine_name if self.install_new_cs else cs_hostname)

            if not self.install_new_cs:
                if self.inputs.get("csClientName") is None or self.inputs.get("csHostname") is None:
                    if self.inputs.get("networkGateway") is None:
                        if self.inputs.get("enableFirewallConfig", "0") == "0":
                            if self.inputs.get("decoupledInstall", "0") == "0":
                                raise Exception("Failed to fetch Commserve Details - CS Client Name and Hostname")
            return commserve_info

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in generating Commserve Info XML")

    def _client_composition_node(self, pkg_dict):
        """
            Node which consists of the information of the client info and as well as what packages are to be installed
        :param pkg_dict: Dictionary of packages to installed (eg:- 1 : File System Core)
        :return:

        """
        clientcompositionnode = Element('clientComposition')
        clientcompositionnode.append(self._client_info_node())
        clientcompositionnode.set('overWriteClientHostName', '1')
        clientcompositionnode.append(self._components_node(pkg_dict))
        clientcompositionnode.append(self._client_roles_node())
        return clientcompositionnode

    def _client_info_node(self):
        """
            Client group_name and log location info
        :return:
            client info node
        """
        try:
            clientinfonode = Element('clientInfo')
            clientpropsnode = SubElement(clientinfonode, 'clientProps')
            if "unix" in self.os_type:
                clientpropsnode.set('logFilesLocation', self.xml_flags.get("logFilesLocation"))
                clientinfonode.append(self._client_node())

            else:
                clientpropsnode.set('ClientInterface', '')
                proc_type = self.machine_obj.execute_command('(gwmi win32_computersystem).SystemType').formatted_output

                if "x64-based" in proc_type:
                    clientpropsnode.set('BinarySetID', '3')
                else:
                    clientpropsnode.set('BinarySetID', '1')

                clientinfonode.append(self._client_node(proc_type))
                clientpropsnode.set('byteOrder', self.xml_flags.get("byteOrder"))

            clientgroupsnode = SubElement(clientinfonode, 'clientGroups')
            clientgroup = self.inputs.get("clientGroupName", '')
            clientgroupsnode.set('clientGroupName', clientgroup)

            return clientinfonode

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in generating Client Info XML")

    def _client_node(self, proc_type=None):
        """
            Fills XML with Client install directory, os info, certificate
        :param proc_type: 32bit and 64bit Processor
        :return: Client node which contains the infomation in Element Tree object
        """
        try:
            clientnode = Element('client')
            clientnode.set('installDirectory', self.xml_flags.get("installDirectory"))

            if "unix" in self.os_type:
                clientnode.set('clientCertificate', self.xml_flags.get("clientCertificate", ""))
                clientnode.set('evmgrcPort', self.xml_flags.get("evmgrcPort"))

            elif "windows" in self.os_type:
                versioninfonode = Element('versionInfo')
                versioninfonode.set('GalaxyBuildNumber', self.xml_flags.get("GalaxyBuildNumber"))
                releasenode = SubElement(versioninfonode, 'GalaxyRelease')
                releasenode.set('ReleaseString', self.xml_flags.get("ReleaseString"))
                clientnode.append(versioninfonode)
                osinfo = Element('osInfo')
                osdisplaynode = SubElement(osinfo, 'OsDisplayInfo')
                if "x64-based" in proc_type:
                    osinfo.set('PlatformType', 'X64')
                    osdisplaynode.set('ProcessorType', 'WinX64')

                else:
                    osinfo.set('PlatformType', 'X86')
                    osdisplaynode.set('ProcessorType', 'Win32')

                osdisplaynode.set("OSName", self.xml_flags.get("OSName"))
                osdisplaynode.set('OSBuild', self.xml_flags.get("OSBuild"))
                clientnode.append(osinfo)
                clientnode.set("clientPassword", "3e063aba7c1693bf34026114bfea2006ff26698aef707031095f69758" +
                               "bab9a2710527370618067f09e1ec0633fee6e63e")

            clientnode.set('cvdPort', self.xml_flags.get("cvdPort"))
            cliententitynode = Element('clientEntity')
            cliententitynode.set('clientName', self.client_name)
            if "force_ipv4" in self.inputs.keys() and self.inputs['force_ipv4'] == 2:
                cliententitynode.set('hostName', self.config_json.Install.unix_client.ip6address)
            else:
                cliententitynode.set('hostName', self.machine_obj.machine_name)
            clientnode.append(cliententitynode)
            jobresultsdirnode = Element('jobResulsDir')
            jobresultsdirnode.set('path', self.xml_flags.get("jobResultsPath"))
            clientnode.append(jobresultsdirnode)
            return clientnode

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in generating Commserve Info XML")

    def _components_node(self, pkg_dict):
        """
            Fills the xml with list of packages to be installed and their depedencies
        :param pkg_dict: Dictionary of packahes with their names
        :return:
            Element Tree - components node
        """
        try:
            componentsnode = Element('components')
            for pkgid in pkg_dict:

                componentinfonode = Element('componentInfo')
                componentinfonode.set('ComponentId', pkgid)
                componentinfonode.set('ComponentName', pkg_dict[pkgid])
                componentinfonode.set('consumeLicense', '1')
                if "unix" in self.os_type:
                    componentinfonode.set('osType', 'Unix')
                componentsnode.append(componentinfonode)

                if int(pkgid) in [20, 1020]:
                    componentsnode.append(self._create_commserve_node())

                if int(pkgid) in [51, 1301]:
                    componentsnode.append(self._create_index_cache_dir())

                if int(pkgid) in [252, 1174]:
                    componentsnode.append(self._create_dm2_webservice_node())

                if int(pkgid) == 23:
                    dump_file_path = None
                    if self.inputs.get("useExistingDump") is not None and self.inputs.get("useExistingDump") == "1":
                        if self.inputs.get("WFEngineDumpPath"):
                            dump_file_path = self.inputs.get("WFEngineDumpPath")
                    componentsnode.append(self._create_workflow_engine_node(dump_file_path))

                if int(pkgid) in [701, 1118]:
                    componentsnode.append(self._create_commcell_console_node())

                if int(pkgid) == 726:
                    componentsnode.append(self._create_web_console_node())

                if int(pkgid) == 952:
                    componentsnode.append(self._mongodb_node())

                if int(pkgid) in [263, 1156]:
                    componentsnode.append(self._configure_index_gateway_node())

                if int(pkgid) in [954, 1602]:
                    componentsnode.append(self._message_queue_node())

                if int(pkgid) == 809:
                    diagnosticserver = Element("diagnosticsAndUsageServer")
                    diagnosticserver.set("commservMetricsReportingServerEnabled", "")
                    componentsnode.append(diagnosticserver)

                if int(pkgid) == 1135:
                    componentsnode.append(self._command_center_info())

                if int(pkgid) == 1002:
                    componentsnode.append(self._configure_for_laptop_backups_node())

                if int(pkgid) == 1051:
                    componentsnode.append(self._create_domino_partition_node("DB"))

                if int(pkgid) == 1052:
                    componentsnode.append(self._create_domino_partition_node('Doc'))

                if int(pkgid) == 1053:
                    componentsnode.append(self._create_domino_partition_node('DataArchiver'))

                if int(pkgid) == 1114:
                    componentsnode.append(self._create_cdr_logdir())

                if int(pkgid) == 1124:
                    componentsnode.append(self._create_tsa_login_node('novellFS'))

                if int(pkgid) == 1129:
                    componentsnode.append(self._create_obj_server_node())

                if int(pkgid) == 1207:
                    componentsnode.append(self._create_db2_path())

                if int(pkgid) == 1204:
                    componentsnode.append(self._create_edc_groups('9', ''))

                if int(pkgid) == 1205:
                    componentsnode.append(self._create_oracle_sap_node())

                if int(pkgid) == 1128:
                    componentsnode.append(self._create_edc_groups('8', ''))
                    componentsnode.append(self._create_edc_groups('1', ''))

            componentsnode.append(self._common_info_node(pkg_dict))
            return componentsnode

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in generating Commserve Info XML")

    def _create_commserve_node(self):
        """
            Sets the Commserve database information
        :return:
            Element Tree - CSDB Node
        """
        commserveNode = Element('commserve')
        commserveNode.append(self._cs_db_info())
        commserveNode.append(self._oem_info_node())
        return commserveNode

    def _oem_info_node(self):
        """
            Sets the OEM information
        :return:
            Element Tree - OEM info Node
        """
        oemInfoNode = Element('oemInfo')
        oemInfoNode.set('OEMId', "1" if not self.inputs.get("oem_id") else str(self.inputs.get("oem_id")))
        return oemInfoNode

    def _cs_db_info(self):
        """
            Sets the Commserve database information
        :return:
            Element Tree - CSDB Node
        """
        csdb_info_node = Element('csdbInfo')
        if "unix" in self.os_type:
            commserve_dump = self.inputs.get("CommservDumpPath", "")
            csdb_info_node.set('CommservDBdumpPath', commserve_dump)
            csdb_info_node.append(self._commcell_user_node())

        else:
            csdb_info_node.set('CommcellPasswordExists', '0')
            csdb_info_node.set('CommservSurveyEnabled', '1')
            install_mode = '1'
            if self.inputs.get("useExsitingCSdump"):
                if self.inputs.get("CommservDumpPath"):
                    csdb_info_node.set('useDBDump', '1')
                    csdb_info_node.set('dumpFilePath', self.inputs.get("CommservDumpPath"))
                    install_mode = '2'
            csdb_info_node.set('installMode', install_mode)
            csdb_info_node.append(self._commcell_user_node())
            csdb_info_node.append(self._cvsql_admin_node())
            csdb_info_node.append(self._dr_path_node())
            csdb_info_node.append(self._ftp_location_node())

        return csdb_info_node

    def _commcell_user_node(self):
        """
            Sets the commserve user information
        :return:
            Element Tree - Commcell user Node
        """
        commcellUserNode = Element('CommCellUser')
        commcellUserNode.set('userName', 'admin')
        if self.inputs.get("commservePassword"):
            commserve_password = self.inputs.get("commservePassword")
            encrypted_password = b64encode(commserve_password.encode()).decode()
            if "windows" in self.os_type:
                encrypted_password = "||#05!" + encrypted_password

            commcellUserNode.set('password', encrypted_password)

        else:
            commcellUserNode.set('password', '3bee62aff88ee7e864029c0a007a7fa53b18a24e4ac702843')

        return commcellUserNode

    def _cvsql_admin_node(self):
        """
            Sets the SQL information
        :return:
            Element Tree - SQL Database Node
        """
        try:
            cvSQLAdminNode = Element('cvSQLAdmin')
            if self.inputs.get("cvSQLAdminPassword"):
                cvsql_admin_password = self.inputs.get("cvSQLAdminPassword")
                encrypted_password = b64encode(cvsql_admin_password.encode()).decode()
                cvSQLAdminNode.set('password', encrypted_password)

            else:
                cvSQLAdminNode.set('password', '3b2b8c6e6819b92e03fc0062a2f51ef46f365a3371009e' +
                                   '233d942bf95bc00999bcae47cdadccf81c073bd722d2e37d9ff')

            return cvSQLAdminNode

        except Exception as exp:
            self.log.exception(str(exp))
            raise Exception("Exception in generating CV SQL Info XML")

    def _dr_path_node(self):
        """
            Sets the Disaster Recovery Path for the Commserve
        :return:
            Element Tree - DR Node
        """
        try:
            erPathNode = Element('ERPath')
            erPathNode.set('path', 'c:\\DR')
            userAccountNode = SubElement(erPathNode, 'userAccount')
            userAccountNode.set('password', '')
            userAccountNode.set('userName', '')
            return erPathNode

        except Exception as exp:
            self.log.exception(str(exp))
            raise Exception("Exception in generating Disaster Recovery Info XML")

    def _ftp_location_node(self):
        """
            Sets the FTP location for the Commserve installation
        :return:
                   Element Tree - FTP Node
        """
        try:
            ftp_location = Element("FTPLocation")
            ftp_location.set("path", "")
            return ftp_location

        except Exception as exp:
            self.log.exception(str(exp))
            raise Exception("Exception in generating Disaster Recovery Info XML")

    def _create_index_cache_dir(self):
        """
            Sets the index store location for the media agent
        :return:
            Element Tree - mediaAgent node
        """
        ma_node = Element('mediaAgent')
        indexcachedirnode = SubElement(ma_node, 'indexCacheDirectory')
        indexcachedirnode.set('path', self.xml_flags.get("indexCachePath"))
        return ma_node

    def _create_dm2_webservice_node(self):
        """
            Sets the flags and dump location for the DM2 Webservice
            :return:
                Element Tree - dm2_webservice node
        """
        try:
            dm2_webservice = Element('dm2WebService')
            if self.inputs.get("useExistingDump") is not None:
                if self.inputs.get("DM2DumpPath"):
                    dm2_webservice.set('useDBDump', '1')
                    dm2_webservice.set('dumpFilePath', self.inputs.get("DM2DumpPath"))

            dm2_webservice.set('xmlViewWebAlias', self.xml_flags.get("xmlViewWebAlias"))
            dm2_webservice.set('searchSvcWebAlias', self.xml_flags.get("searchSvcWebAlias"))
            dm2_webservice.set('dm2WebSitePort', self.xml_flags.get("dm2WebSitePort"))
            dm2_webservice.set('apachePortNumber', self.xml_flags.get("apachePortNumber"))
            dm2_webservice.set('dm2DataFileInstallPath', self.xml_flags.get("dm2DataFileInstallPath"))
            sqlServerInfoNode = SubElement(dm2_webservice, 'sqlServerInfo')
            sqlServerInfoNode.set('pAccess', '')
            sqlServerInfoNode.set('sqlServerName', '\Commvault')
            return dm2_webservice

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in generating DM2 WebService Node - XML")

    def _create_commcell_console_node(self):
        """
            Sets the commcell information/flags on the XML
        :return:
            Element Tree - commcell console node
        """
        try:
            commcell_console_node = Element('commcellConsole')
            if "unix" in self.os_type:
                commcell_console_node.set('configureWebAlias', '1')
                commcell_console_node.set('reportsWebAliasURL', '')
                commcell_console_node.set('webAliasURL', '')

            else:
                commcell_console_node.set('configureWebAlias', '0')

            return commcell_console_node

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in generating Commcell Console Node - XML")

    def _create_web_console_node(self):
        """
                Sets the webconsole information on the XML
        :return:
                Element Tree - web console node
        """
        try:
            webconsolenode = Element('webConsole')
            webconsolenode.set('webConsoleURL', self.xml_flags.get("webConsoleURL"))
            webconsolenode.set('webConsolePort', self.xml_flags.get("webConsolePort"))
            webconsolenode.set('webURL', self.xml_flags.get("webURL"))
            webconsolenode.set('webServerClientId', self.xml_flags.get("webServerClientId"))
            return webconsolenode

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in generating WebConsole Node - XML")

    def _mongodb_node(self):
        mongodbinfo = Element('mongoDBInfo')
        mongodbinfo.set("nMongoPort", "")
        mongodbinfo.set("sMongoInstance", self.machine_obj.machine_name)
        mongodbinfo.set("pMongoAccess", "")
        return mongodbinfo

    def _configure_index_gateway_node(self):
        try:
            indexgateway = Element('indexGateway')
            indexgateway.set('webAliasName', 'IndexGateway')
            indexgateway.set('webSitePort', '')
            return indexgateway

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in generating indexGateway Node - XML")

    def _message_queue_node(self):
        messagequeue = Element("messageQueue")
        messagequeue.set("messagequeueAMQPPort", self.xml_flags.get("messagequeueAMQPPort"))
        messagequeue.set("messagequeueDataDir", self.xml_flags.get("messagequeueDataDir"))
        messagequeue.set("messagequeueWebconsolePort", self.xml_flags.get("messagequeueWebconsolePort"))
        messagequeue.set("messagequeueTCPPort", self.xml_flags.get("messagequeueTCPPort"))
        messagequeue.set("messagequeueMaxJvm", self.xml_flags.get("messagequeueMaxJvm"))
        messagequeue.set("messagequeueMinJvm", self.xml_flags.get("messagequeueMinJvm"))
        messagequeue.set("messagequeueMQTTPort", self.xml_flags.get("messagequeueMQTTPort"))
        messagequeue.set("messagequeueWSPort", self.xml_flags.get("messagequeueWSPort"))
        if "unix" in self.os_type:
            messagequeue.set("messagequeueStompPort", self.xml_flags.get("messagequeueStompPort"))

        return messagequeue

    def _command_center_info(self):
        webservers = Element("availableWebServers")
        webservers.set("webSitePortNumber", "")
        dm2webserver = SubElement(webservers, "dm2WebServer")
        dm2webserver.set("clientName", self.client_name)
        dm2webserver.set("hostName", self.machine_obj.machine_name)
        return webservers

    def _configure_for_laptop_backups_node(self):
        """
            Sets the laptop backups information on the XML
         :return:
            Element Tree - laptopbackup node
         """
        filesystemnode = Element('fileSystem')
        filesystemnode.set('configureForLaptopBackups', '0')
        filesystemnode.append(self._selected_subclient_policy_node())
        return filesystemnode

    def _selected_subclient_policy_node(self):
        """
            Sets the subclient policy information on the XML
        :return:
                Element Tree - subclient policy node
         """
        try:
            selectedsubclientpolicynode = Element('selectedSubclientPolicy')
            selectedsubclientpolicynode.set('subclientPolicyId', '')
            selectedsubclientpolicynode.set('subclientPolicyName', '')
            return selectedsubclientpolicynode

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in generating subclient policy Node - XML")

    def _create_workflow_engine_node(self, exisiting_dump_path=None):
        """
            Sets the workflow information on the XML
        :return:
            Element Tree - Workflow Engine node
        """
        try:
            workflowenginenode = Element('workflowEngine')
            if exisiting_dump_path is not None:
                workflowenginenode.set('useDBDump', '1')
                workflowenginenode.set('dumpFilePath', exisiting_dump_path)

            return workflowenginenode

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in generating WorkFlow Engine Node - XML")

    def _create_domino_partition_node(self, lotusnotesagent_type):
        try:
            dpnode = Element('lotusNotes' + lotusnotesagent_type)
            instancenode = SubElement(dpnode, 'instanceList')
            instancenode.set('binaryPath', '')
            instancenode.set('instanceName', '')
            instancenode.set('path', '')
            return dpnode

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in generating domino partition Node - XML")

    def _create_cdr_logdir(self):
        """
            Sets the ContinuousDataReplicator information on the XML
            :return:
                Element Tree - cdrdriver node
        """
        try:
            cdrdrivernode = Element('cdrDriver')
            cdrdrivernode.set('logFileLocation', '')
            cdrdrivernode.set('RolCacheMaxDiskSize', '')
            return cdrdrivernode

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in generating CDR LogicDir Node - XML")

    def _create_tsa_login_node(self, agentnode):
        """
            Sets the Tivoli System Automation(TSA) information on the XML
            :return:
                Element Tree - cdrdriver node
        """
        try:
            tsaloginnode = Element(agentnode)
            tsauseraccountnode = SubElement(tsaloginnode, 'userAccount')
            tsauseraccountnode.set('userName', '')
            tsauseraccountnode.set('password', '')
            if agentnode == 'novellDirectoryServices':
                tsauseraccountnode.set('domainName', '')
            return tsaloginnode

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in generating TSA login Node - XML")

    def _create_obj_server_node(self):
        """
            Sets the server node information on the XML
            :return:
                Element Tree - objectserver node
        """
        try:
            objservernode = Element('objectServer')
            objservernode.set('objSrvWebServiceURL', '')
            objservernode.set('objSrvWebServicePort', '')
            return objservernode

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Failed to insert Object Server Node")

    def _create_db2_path(self):
        """
            Sets the db2 node information on the XML
            :return:
                Element Tree - db2 node
        """
        try:
            db2node = Element('db2')
            db2node.set('db2ArchivePath', '')
            db2node.set('db2AuditErrorPath', '')
            db2node.set('db2RetrievePath', '')
            return db2node

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Failed to insert DB2 Node")

    def _create_edc_groups(self, instance_type, instance_name):
        """
            Sets the edc group node information on the XML
            :return:
                Element Tree - edc group node
        """
        try:
            edcgroupnode = Element('edcGroups')
            edcgroupnode.set('instanceType', instance_type)
            edcgroupnode.set('instanceName', instance_name)
            return edcgroupnode

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Failed to create EDC groups Node")

    def _create_oracle_sap_node(self):
        """
            Sets the oracle sap node information on the XML
            :return:
                Element Tree - oracle sap node
        """
        try:
            oracleSAPNode = Element('oracleSAP')
            oracleSAPNode.set('sapExeDirectory', '')
            return oracleSAPNode

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Failed to create oracle SAP Node")

    def _common_info_node(self, pkg_dict):
        """
            Sets the common info/flags information on the XML
            :return:
                Element Tree - common info node
        """
        try:
            commoninfonode = Element('commonInfo')
            commoninfonode.set('globalFilters', self.xml_flags.get("commonInfoGlobalFilters"))
            commoninfonode.set('useExistingStoragePolicy', self.xml_flags.get("useExistingStoragePolicy"))
            storagepolicytousenode = Element('storagePolicyToUse')
            storagepolicytousenode.set('storagePolicyId', self.xml_flags.get("storagePolicyId"))
            storagepolicytousenode.set('storagePolicyName', self.xml_flags.get("storagePolicyName"))
            commoninfonode.append(storagepolicytousenode)

            if "726" in pkg_dict.keys():
                webservers = Element("availableWebServers")
                webservers.set("webSitePortNumber", "")
                dm2webserver = SubElement(webservers, "dm2WebServer")
                dm2webserver.set("clientName", self.client_name)
                dm2webserver.set("hostName", self.machine_obj.machine_name)
                commoninfonode.append(webservers)

            return commoninfonode

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Failed to commonInfo  Node")

    def _client_roles_node(self):
        """
            Sets the client roles node information on the XML
            :return:
                Element Tree - common info node
        """
        client_roles_node = Element('clientRoles')
        if self.inputs.get("bNetworkProxy") == "1":
            client_roles_node.set('bNetworkProxy', '1')

        else:
            client_roles_node.set('bNetworkProxy', '0')

        client_roles_node.set('bLaptopBackup', "0" if self.inputs.get("bLaptopBackup") != "1" else "1")
        return client_roles_node

    def install_flags(self):
        """
            Common installer flags that has to be used for installation
        :return:
            Installer flag node where all the flags are mentioned under the xml
        """
        try:
            base_installer_flags = {"stopOracleServices": "0", "ignoreJobsRunning": "0", "unixOtherAccess": "7",
                                    "useExsitingCSdump": "0", "install32Base": "0", "useNewOS": "0",
                                    "install64Base": "0",
                                    "disableOSFirewall": "0", "installLatestServicePac": "1", "upgradeMode": "0",
                                    "preferredIPFamily": "1", "forceReboot": "0", "deletePackagesAfterInstall": "0",
                                    "launchRegisterMe": "0", "allowMultipleInstances": "1", "autoRegister": "0",
                                    "decoupledInstall": "0", "unixGroupAccess": "7", "overrideClientInfo": "0",
                                    "addToFirewallExclusion": "0", "restoreOnlyAgents": "0",
                                    "killBrowserProcesses": "0",
                                    "showFirewallConfigDialogs": "0", "sqlDataFilePath": "%InstallFolder%",
                                    "launchRolesManager": "0", "runServiceAsRoot": "1",
                                    "selectedRoles": ""}

            if self.inputs.get("install32base") == "1":
                base_installer_flags['install32Base'] = "1"

            if self.inputs.get("restoreOnlyAgents") == "1":
                base_installer_flags['restoreOnlyAgents'] = "1"

            if self.inputs.get("launchRolesManager") == "1":
                base_installer_flags['launchRolesManager'] = "1"

            if self.inputs.get("runServiceAsRoot") == "0":
                base_installer_flags['runServiceAsRoot'] = "0"

            if 'selectedRoles' in self.inputs:
                roles = ','.join(str(i) for i in list(self.inputs.get('selectedRoles')))
                base_installer_flags['selectedRoles'] = roles

            if "useExsitingCSdump" in self.inputs.keys():
                # Path has to be given along with the dump
                if "CommservDumpPath" in self.inputs.keys():
                    if "DM2DumpPath" in self.inputs.keys():
                        if "WFEngineDumpPath" in self.inputs.keys():
                            base_installer_flags['useExsitingCSdump'] = "1"

            if self.inputs.get("decoupledInstall") == "1":
                base_installer_flags["decoupledInstall"] = "1"

            if "unix" in self.os_type:
                install_flag_node = self._installer_flags_unix(base_installer_flags)

            else:
                install_flag_node = self._installer_flags_windows(base_installer_flags)

            install_flag_node.append(self._sql_install_node())
            install_flag_node.append(self.firewall_install_flag())
            return install_flag_node

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Failed to insert Installer Flags Node")

    def _installer_flags_unix(self, installer_flags):
        """
            Installer flags for Unix Installations

            :arg
                installer_flags (dict) -- Dictionary of common installer flags used for installation

            :return:
                Install flag node where all the flags are mentioned under the xml
        """
        try:
            install_flag = Element('installFlags')
            install_flag.set('install32Base', installer_flags['install32Base'])
            install_flag.set('install64Base', installer_flags['install64Base'])
            install_flag.set('decoupledInstall', installer_flags['decoupledInstall'])
            install_flag.set('allowNewerCommserve', '0')
            install_flag.set('allowMultipleInstances', installer_flags['allowMultipleInstances'])
            install_flag.set('numberOfStreams', '10')
            install_flag.set('unixGroup', '')
            install_flag.set('unixGroupAccess', installer_flags['unixGroupAccess'])
            install_flag.set('unixOtherAccess', installer_flags['unixOtherAccess'])
            install_flag.set('unixTempDirectory', '/tmp/.gxsetup')
            install_flag.set('restoreOnlyAgents', installer_flags['restoreOnlyAgents'])
            install_flag.set('ignoreJobsRunning', installer_flags['ignoreJobsRunning'])
            install_flag.set('autoRegister', installer_flags['autoRegister'])
            if "force_ipv4" in self.inputs.keys() and self.inputs['force_ipv4'] == 2:
                install_flag.set('forceIPV4', '2')
            else:
                install_flag.set('forceIPV4', '1')
            install_flag.set('singleInterfaceBinding', '0')
            install_flag.set('installLatestServicePack', '0')
            install_flag.set('loadWAToKernel', '0')
            install_flag.set('forceReboot', installer_flags['forceReboot'])
            install_flag.set('useNewOS', installer_flags['useNewOS'])
            if self.inputs.get("useExsitingCSdump"):
                install_flag.set("dbDumpFolder", self.inputs.get("CommservDumpPath", ""))
            install_flag.set('launchRolesManager', installer_flags['launchRolesManager'])
            install_flag.set('selectedRoles', installer_flags['selectedRoles'])
            install_flag.set('runServiceAsRoot', installer_flags['runServiceAsRoot'])
            # install_flag.set('launchProcessManager', '0')
            # $install_flag.set('hideApps', '0')
            return install_flag

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Failed to insert Unix Installer Flags Node")

    def _installer_flags_windows(self, installer_flags):
        """
            Installer flags for Windows Installations

            :arg
                installer_flags (dict) -- Dictionary of common installer flags used for installation

            :return:
                    Install flag node where all the flags are mentioned under the xml
        """
        try:
            install_flag = Element('installFlags')
            install_flag.set('installLatestServicePack', '1')
            install_flag.set('showFirewallConfigDialogs', installer_flags['showFirewallConfigDialogs'])
            install_flag.set('autoRegister', installer_flags['autoRegister'])
            install_flag.set('unixGroupAccess', installer_flags['unixGroupAccess'])
            install_flag.set('allowMultipleInstances', installer_flags['allowMultipleInstances'])
            install_flag.set('useNewOS', installer_flags['useNewOS'])
            install_flag.set('restoreOnlyAgents', installer_flags['restoreOnlyAgents'])
            install_flag.set('killBrowserProcesses', installer_flags['killBrowserProcesses'])
            install_flag.set('install32Base', installer_flags['install32Base'])
            install_flag.set('disableOSFirewall', installer_flags['disableOSFirewall'])
            install_flag.set('decoupledInstall', installer_flags['decoupledInstall'])
            install_flag.set('RepairMode', '0')
            install_flag.set('launchConsole', '0')
            install_flag.set('deletePackagesAfterInstall', installer_flags['deletePackagesAfterInstall'])
            install_flag.set('useExistingDump', installer_flags['useExsitingCSdump'])
            install_flag.set('unixOtherAccess', installer_flags['unixOtherAccess'])
            install_flag.set('stopOracleServices', installer_flags['stopOracleServices'])
            install_flag.set('install64Base', installer_flags['install64Base'])
            install_flag.set('upgradeMode', installer_flags['upgradeMode'])
            install_flag.set('preferredIPFamily', installer_flags['preferredIPFamily'])
            install_flag.set('launchRegisterMe', installer_flags['launchRegisterMe'])
            install_flag.set('addToFirewallExclusion', installer_flags['addToFirewallExclusion'])
            install_flag.set('ignoreJobsRunning', installer_flags['ignoreJobsRunning'])
            install_flag.set('forceReboot', installer_flags['forceReboot'])
            install_flag.set('overrideClientInfo', installer_flags['overrideClientInfo'])
            install_flag.set('activateAllUserProfiles', '0')
            install_flag.set('launchRolesManager', installer_flags['launchRolesManager'])
            install_flag.set('selectedRoles', installer_flags['selectedRoles'])
            # install_flag.set('launchProcessManager', '0')
            # $install_flag.set('hideApps', '0')
            return install_flag

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Failed to insert Windows Installer Flags Node")

    def firewall_install_flag(self):
        """
            Helps to create an xml for Firewall configurations
            :return:
                Firewall node
        """
        try:
            firewall_node = Element('firewallInstall')
            if self.inputs.get("enableFirewallConfig") != "1":
                firewall_node.set('enableFirewallConfig', '0')
                firewall_node.set('certificatePath', '')
                firewall_node.set('firewallConnectionType', '0')
                firewall_node.set('firewallConfigFile', '')
                firewall_node.set('proxyClientName', '')
                firewall_node.set('proxyHostName', '')
                firewall_node.set('portNumber', '')

            else:
                firewall_node.set('enableFirewallConfig', '1')
                if "firewallConnectionType" in self.inputs.keys():
                    firewall_node.set('firewallConnectionType', str(self.inputs.get("firewallConnectionType")))

                else:
                    firewall_node.set('firewallConnectionType', '0')

                if "httpProxyConfigurationType" in self.inputs.keys():
                    firewall_node.set('httpProxyConfigurationType', str(self.inputs.get("httpProxyConfigurationType")))

                else:
                    firewall_node.set('httpProxyConfigurationType', '0')

                if "httpProxyPortNumber" in self.inputs.keys():
                    firewall_node.set('httpProxyPortNumber', str(self.inputs.get("httpProxyPortNumber")))

                if "httpProxyHostName" in self.inputs.keys():
                    firewall_node.set('httpProxyHostName', str(self.inputs.get("httpProxyHostName")))

                if "portNumber" in self.inputs.keys():
                    firewall_node.set('portNumber', str(self.inputs.get("portNumber")))

                if "enableProxyClient" in self.inputs.keys() and self.inputs.get("enableProxyClient") == "1":
                    proxies = self.inputs.get("proxyHostname").split(';')
                    ports = self.inputs.get("proxyPortNumber").split(';')
                    for idx, value in enumerate(proxies):
                        proxyInfo = Element('proxyInfo')
                        proxyInfo.set('hostName', value)
                        if len(ports) > idx:
                            proxyInfo.set('portNumber', ports[idx])
                        else:
                            proxyInfo.set('portNumber', '8403')
                        firewall_node.append(proxyInfo)
            return firewall_node

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Failed to Configure Firewall Node")

    def _sql_install_node(self):
        """
            Sets the sql install node information on the XML
                :return:
                    Element Tree - sql install node
         """
        try:
            sql_install_node = Element('sqlInstall')
            sql_filepath = "" if "unix" in self.os_type else "%InstallFolder%"
            sql_install_node.set('sqlDataFilePath', sql_filepath)
            sqlSaUserAccountNode = SubElement(sql_install_node, 'sqlSaUserAccount')

            if "sqlSaPassword" in self.inputs.keys():
                sql_password = self.inputs.get("sqlSaPassword")

            else:
                sql_password = self.inputs.get("commservePassword", "")

            encrypted_password = b64encode(sql_password.encode()).decode()
            if "windows" in self.os_type:
                encrypted_password = "||#05!" + encrypted_password

            sqlSaUserAccountNode.set("password", encrypted_password)
            return sql_install_node

        except Exception as err:
            self.log.exception(str(err))
            raise Exception("Exception in writing XML to a file")

    def create_xml_file_for_remote(self, xml=None, file_name="install_XML.xml"):
        """
            Writes root object of the Element Tree to an XML file

                Args:
                    xml     (root)  --  Element Tree Object
                        default: None

                    file_name    (str)   --  Name of the XML File
                        default: temp_installXML.xml

                Returns:
                    The File Path where XMl file is created.

        """
        try:
            _path = constants.TEMP_DIR
            xmlfilepath = os.path.join(_path, file_name)
            with open(xmlfilepath, 'w') as fd:
                fd.write(xml)
            self.log.info("Created xml file [{0}]".format(xmlfilepath))
            return xmlfilepath

        except Exception as err:
            self.log.exception("Exception raised at createXMLfileForRemote: %s", str(err))
            raise err
