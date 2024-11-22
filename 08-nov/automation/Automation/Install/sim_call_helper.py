# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file for performing install operations

SimCallHelper: Helper class to perform Install operations

SimCallHelper:

    generate_xml()          -- To generate xml for simCall and store it in the given path

    execute_sim_call()      -- To generate the XML for the sim call operation and execute the sim call

    install_new_client()    -- To install a new client on the commcell machine

    register_to_cs()        -- To register a decoupled client to the CS

    deregister_to_cs()      -- To de-register a client locally, client entries continue
                                to exist on the commserver

"""

import re
import xml.etree.ElementTree as ET
from AutomationUtils.machine import Machine
from AutomationUtils import constants
from AutomationUtils.logger import get_log
from AutomationUtils.options_selector import OptionsSelector
from Install.installer_constants import DEFAULT_INSTALL_DIRECTORY_WINDOWS
from Install.installer_constants import DEFAULT_INSTALL_DIRECTORY_UNIX
from Install.installer_constants import SIM_CALL_WRAPPER_EXE, SIM_CALL_WRAPPER_EXE_UNIX


class SimCallHelper:
    """
    Helper file for Sim call to perform install operations

    """

    def __init__(self, commcell):
        """
        Initialize the SimCallHelper object

        Args:
            commcell    (object)    -- object of commcell class

        """
        self.commcell = commcell
        self.log = get_log()
        self.temp_dir = constants.TEMP_DIR
        self.commcell_install_directory = self.commcell.commserv_client.install_directory

        self.controller_machine = Machine()
        self.commcell_machine = Machine(self.commcell.commserv_client)
        self.options = OptionsSelector(self.commcell)

    def generate_xml(
            self,
            path=None,
            commserv_hostname=None,
            client_name=None,
            client_hostname=None,
            username=None,
            password=None,
            auth_code=None,
            overwrite_client=False,
            unix_os=False):
        """
            To generate the XML for the sim call operation

            path                    (str)       -- Full path to generate the XML file

                default : None

            commserv_hostname       (str)       -- Full hostname of the commserv machine

                default : None

            client_name             (str)       -- Name of the client to be created

                default : None

            client_hostname         (str)       -- Full hostname of the client machine

                default : None

            username                (str)       -- Username for the commcell

                default : None

            password                (str)       -- Encrypted password for the commcell machine

                default : None

            auth_code               (str)       -- Organization authcode to be used for installation

                default : None

            overwrite_client        (str)       -- Whether to overwrite existing client during reinstall

                default : False

        """

        # Changing the OS information based on Unix or Windows
        _PlatformType = "X64"
        _SubType = "Server" if not unix_os else "Linux"
        _Type = "Windows" if not unix_os else "Unix"
        _Version = "6.2" if not unix_os else "glibc2.6"
        _OSBuild = "9200" if not unix_os else "2.6.32-431.el6.x86_64"
        _OSName = "Windows Server 2016 Datacenter" if not unix_os else "Linux"
        _ProcessorType = "WinX64" if not unix_os else "x86_64"
        _installDirectory = "C:\Program Files\Commvault\ContentStore" if not unix_os else "/opt/commvault"
        _jobResultsDir = "C:\Program Files\Commvault\ContentStore\iDataAgent\JobResults" \
            if not unix_os else "/opt/commvault/iDataAgent/jobResults"
        _componentinfo = 'ComponentId="1" ComponentName="File System Core" _type_="60" clientSidePackage="1"\
                      consumeLicense="1"' if not unix_os else ' ComponentId="1002" \
                      ComponentName="File System Core" clientSidePackage="1" consumeLicense="1" osType="Unix"'

        xml = fr"""
            <CVInstallManager_ClientSetup Focus="Instance001" Operationtype="0" RemoteClient="1"
            requestFlags="{"22024192" * overwrite_client + "4096" * (1 - overwrite_client)}" requestType="1">
               <CommServeInfo>
                  <CommserveHostInfo _type_="3" clientName="" hostName="{commserv_hostname}" />
               </CommServeInfo>
               <ClientAuthentication AuthenticationEnabled="1" DomainConfigured="1" PrincipalName=""
                ProviderID="1" SSOEnabled="0">
                  <userAccountToLogin domainName="" password="{password}"
                   userName="{username}" />
               </ClientAuthentication>
               <clientComposition overWriteClientHostName="{int(overwrite_client)}" activateClient="1" packageDeliveryOption="0">
                  <clientInfo>
                     <client clientPassword="{password}"
                      cvdPort="8400" installDirectory="{_installDirectory}">
                        <clientEntity _type_="3" clientName="{client_name}" hostName="{client_hostname}" />
                        <osInfo PlatformType="{_PlatformType}" SubType="{_SubType}" Type="{_Type}" Version="{_Version}">
                           <OsDisplayInfo OSBuild="{_OSBuild}" OSName="{_OSName}"
                            ProcessorType="{_ProcessorType}" />
                        </osInfo>
                        <jobResulsDir path="{_jobResultsDir}" />
                        <versionInfo GalaxyBuildNumber="BUILD80">
                           <GalaxyRelease ReleaseString="11.0" _type_="58" />
                        </versionInfo>
                     </client>
                     <clientProps BinarySetID="3" ClientInterface=""
                      byteOrder="Little-endian" />
                  </clientInfo>
                  <clientError ErrorCode="" ErrorString="" errorLevel=""/>
                  <components>
                     <componentInfo {_componentinfo} />
                     <commonInfo>
                        <storagePolicyToUse _type_="17" storagePolicyId="1" storagePolicyName="CV_DEFAULT" />
                     </commonInfo>
                     <fileSystem/>
                  </components>
                  <patchInformation friendlyName="" spVersion="{self.commcell.commserv_version}">
                     <packagePatches pkgId="1"/>
                  </patchInformation>                  
               </clientComposition>
               <installFlags activateAllUserProfiles="0" />
                <organizationProperties/>
                <SimError ErrorCode=""/>
            </CVInstallManager_ClientSetup>
        """

        xml = ET.fromstring(xml)

        # To convert to an ElementTree
        xml_tree = ET.ElementTree(xml)

        # To set Authcode if given
        if auth_code:
            xml_tree.find('organizationProperties').set('authCode', auth_code)

        # To store it in the given path
        xml_tree.write(path)

    def generate_1touch_recovery_client_xml(
            self,
            path=None,
            commserv_hostname=None,
            client_name=None,
            client_hostname=None,
            username=None,
            password=None,
            auth_code=None,
            overwrite_client=False):
        """
                   To generate the XML for the sim call operation for generation of recovery client

                   path                    (str)       -- Full path to generate the XML file

                       default : None

                   commserv_hostname       (str)       -- Full hostname of the commserv machine

                       default : None

                   client_name             (str)       -- Name of the client to be created

                       default : None

                   client_hostname         (str)       -- Full hostname of the client machine

                       default : None

                   username                (str)       -- Username for the commcell

                       default : None

                   password                (str)       -- Encrypted password for the commcell machine

                       default : None

                   auth_code               (str)       -- Organization authcode to be used for installation

                       default : None

                   overwrite_client        (str)       -- Whether to overwrite existing client during reinstall

                       default : False

        """

        self.generate_xml(
            path=path,
            commserv_hostname=commserv_hostname,
            client_name=client_name,
            client_hostname=client_hostname,
            username=username,
            password=password,
            auth_code=auth_code,
            overwrite_client=overwrite_client,
        )

        xml_string = self.controller_machine.read_file(path)
        xml = ET.fromstring(xml_string)
        for element in xml.findall("clientComposition"):
            for child in element.findall("components"):
                child.find('componentInfo').attrib.update({
                    'ComponentName': 'Base Client',
                    'consumeLicense': '0'
                })

            element.find('patchInformation').attrib.update({
                'spVersion': f'{float(self.commcell.commserv_version)}'
            })
        xml_tree = ET.ElementTree(xml)
        xml_tree.write(path)

    def execute_sim_call(
            self,
            input_path=None,
            output_path=None,
            recovery_client=False):
        """
            To generate the XML for the sim call operation and execute the sim call

            input_path              (str)       -- Full path to generate the XML file

                default : None

            output_path             (str)       -- Full path to store the response

                default : None

            recovery_client         (bool)      -- Whether to execute for creating a recovery client

                default : False

        Returns:
            None

        Raises:
            Exception

                If sim call failed

        """
        if self.commcell_machine.os_info.lower() == "windows":
            sim_path = self.commcell_machine.join_path(self.commcell_install_directory,
                                                       'Base',
                                                       SIM_CALL_WRAPPER_EXE)
        else:
            sim_path = self.commcell_machine.join_path(self.commcell_install_directory,
                                                       'Base',
                                                       SIM_CALL_WRAPPER_EXE_UNIX)

        # Command to execute simcall
        command = f'"{sim_path}" -input "{input_path}" -output "{output_path}"'
        if recovery_client:
            command += ' -1touchClient'

        # To execute the command on the controller machine
        output = self.commcell_machine.execute_command(command)

        # To read the output file for error level
        file_output = self.commcell_machine.read_file(output_path)

        # Raise exceptions to catch clientErrors
        if 'ErrorCode="0"' not in file_output:
            error = re.search('<(.*)clientError (.*?)/>', file_output, re.I)
            if error:
                self.log.error('clientError: %s', error.group(2))
                raise Exception(f'clientError: {error.group(2)}')

        # Raise exceptions to catch simErrors
        if 'SimCallWrapper completed' not in output.formatted_output:
            error = re.search('<(.*)SimError (.*?)/>', file_output, re.I)
            if error:
                self.log.error('SimError: %s', error.group(2))
                raise Exception(f'SimError: {error.group(2)}')

    def install_new_client(
            self,
            client_name=None,
            client_hostname=None,
            username=None,
            password=None,
            auth_code=None,
            overwrite_client=False,
            recovery_client=False,
            unix_os=False):
        """
            To install a new client on the commcell machine

            client_name             (str)   -- Name of the client to be created

                default : None

            client_hostname         (str)   -- Hostname of the client machine

                default : None

            auth_code               (str)   -- Organization authcode to be used for installation

                default : None

            username                (str)   -- Username to install the new client

                default : None

            password                (str)   -- Password to be used to install the new client

                default : None

            overwrite_client        (bool)  -- Whether to overwrite existing client during reinstall

                default : False

            recovery_client         (bool)  -- Whether to create a recovery client

                default : False

        Returns:
            (str,str)     -- (clientname, hostname)

        """
        if not client_name and not client_hostname:
            # To get a randomly generated client name and hostname
            client_name = client_hostname = self.options.get_custom_str('client')
        self.log.info('client name: "%s" \n client hostname: "%s"', client_name, client_hostname)

        # To create temp directory in Automation folder if not present on controller machine
        if not self.controller_machine.check_directory_exists(self.temp_dir):
            self.controller_machine.create_directory(self.temp_dir)
            self.log.info('Successfully created temporary directory for Automation on controller machine')

        # Path to save the generated xml file on the controller machine
        path = f"{self.controller_machine.join_path(self.temp_dir, 'Simcall.xml')}"

        # To generate xml for sim call
        if recovery_client:
            self.generate_1touch_recovery_client_xml(
                path=path,
                commserv_hostname=self.commcell.commserv_hostname,
                client_name=client_name,
                client_hostname=client_hostname,
                username=username,
                password=password,
                auth_code=auth_code,
                overwrite_client=overwrite_client
            )
        else:
            self.generate_xml(
                path=path,
                commserv_hostname=self.commcell.commserv_hostname,
                client_name=client_name,
                client_hostname=client_hostname,
                username=username,
                password=password,
                auth_code=auth_code,
                overwrite_client=overwrite_client,
                unix_os=unix_os)

        # To generate input path for the sim call
        input_path = self.commcell_machine.join_path(self.commcell_install_directory, 'Temp')
        self.log.info('Input path for the Sim call: %s', input_path)

        # To copy the xml file form the controller machine to the commcell machine
        self.commcell_machine.copy_from_local(path, input_path)

        # Full Path of the input path
        input_path = self.commcell_machine.join_path(input_path, 'Simcall.xml')

        # To generate output path for the sim call
        output_path = self.commcell_machine.join_path(self.commcell_install_directory,
                                                      'Temp',
                                                      'Simcall_output.xml')
        self.log.info('Output path for the Sim call: %s', output_path)

        # To use sim call to install a new client
        self.execute_sim_call(input_path=input_path, output_path=output_path, recovery_client=recovery_client)
        self.log.info('Successfully installed Client: %s on Commserv: %s',
                      client_name,
                      self.commcell.commserv_name)

        # To delete the xml file from the controller machine
        self.controller_machine.delete_file(
            f"{self.controller_machine.join_path(self.temp_dir, 'Simcall.xml')}")

        # To delete the input path
        self.commcell_machine.delete_file(input_path)

        # To delete the output path
        self.commcell_machine.delete_file(output_path)

        return client_name, client_hostname

    def register_to_cs(
            self,
            machine_object=None,
            client_name="",
            **kwargs):
        """
            To register client to cs

            machine                 (object)    -- Machine object of the client which
                                                        has to be registered
                default : None

            client_name              (str)      -- Client Name to refer client in the
                                                            commcell.
                default : ""

            **kwargs: (dict) -- Key value pairs for supporting conditional initializations
            Supported -

            url                     (str)       -- Command Center Url
                default : None

            user                    (str)       -- commcell username to register the client
                default : None

            password                (str)       -- commcell password to register the client
                default : None


            Note:   registrations are done either using the url or cs details
                        --url if url is passed
                        --cs details if url is not passed
                    If username and password are given, registraion will be
                        done using username and password

            Returns:
                None

        """

        # check if client machine is passed or not
        if not machine_object:
            self.log.error("machine object is not passed. Cannot proceed with registration")
            raise Exception("Machine Object not passed")

        # checking if commcell object is passed or not
        if not self.commcell:
            self.log.error("commcell object is not passed")
            raise Exception("Commcell Object Not passed")

        # checking if client_name is passed or not
        if not client_name:
            self.log.error("Client Name cannot be empty")
            raise Exception("Client Name cannot be empty")

        # registers using the CSHostName from the commcell object
        cs_details = f"-CSHost {self.commcell.webconsole_hostname}"

        url = kwargs.get("url")
        # registers using url if url is provided
        if url:
            cs_details = f"-url {url}"
            self.log.info(f"Registering using URL : {url}")

        # replacing " " by "_" in client_name
        client_name = client_name.replace(" ", "_")

        # checking if httpProxy is passed
        proxy = ""
        httpProxy = kwargs.get("httpProxy")
        if httpProxy:
            proxy = f"-HttpProxyInfo {httpProxy}"

        # checking if useHttpProxyTypeWPAD flag is passed
        httpProxyTypeWPAD = ""
        if kwargs.get("useHttpProxyTypeWPAD"):
            httpProxyTypeWPAD = "-HttpProxyTypeWPAD"

        # using authcode to register
        cs_creds = f"-authcode {self.commcell.enable_auth_code()}"

        user = kwargs.get("user")
        password = kwargs.get("password")

        # using username and password, if both are passed
        if user and password:
            cs_creds = f"-user {user} -password {password}"

        elif user:
            self.log.error("Password not given, cannot proceed with registration")
            raise Exception("Password is not passed")

        elif password:
            self.log.error("Username not given, cannot proceed with registration")
            raise Exception("Username is not passed")

        # checking if machine is Windows machine
        if machine_object.os_info.lower() == "windows":
            # storing base path
            base_path = machine_object.join_path(DEFAULT_INSTALL_DIRECTORY_WINDOWS, "Base")
            if not machine_object.check_directory_exists(base_path):
                self.log.error("Base Folder does not exist")
                raise Exception("Base Folder does not exist")
            base_path = base_path.replace(" ", "` ")

        # the machine is Unix machine
        else:
            # storing base path
            base_path = machine_object.join_path(DEFAULT_INSTALL_DIRECTORY_UNIX, "Base")
            base_path = base_path.replace(" ", "\\ ")

            if not machine_object.check_directory_exists(base_path):
                self.log.error("Base folder does not exist")
                raise Exception("Base Folder does not exist")

        sim_path = machine_object.join_path(base_path, "SIMCallWrapper")
        sim_output_path = machine_object.join_path(base_path, "SIMCallOutput.xml")

        command = f"{sim_path} -OpType 1000 {cs_details} {cs_creds} {proxy} {httpProxyTypeWPAD} " \
                  f"-clientname {client_name} -ClientHostName {machine_object.machine_name} " \
                  f"-output {sim_output_path}"

        # Executing SIM Command
        self.log.info("Executing SIM Command")
        output = machine_object.execute_command(command)
        self.log.info("Executed command")

        if output.exception_message:
            self.log.error(output.exception_message)
            raise Exception(output.exception_message)

        if "failed" in output.output.lower():
            message = output.output.split("\r\n")[-3]
            self.log.error(message)
            raise Exception(message)

        self.log.info("Registration to CS successfull")

    def deregister_to_cs(
            self,
            machine_object=None):
        """

            To register client to cs

            machine                 (object)    -- Machine Object which should be
                                                            registered to the cs.
                default : None

            Returns:
                None

        """

        # check if client machine is passed or not
        if not machine_object:
            self.log.error("machine object is not passed. Cannot proceed with de-registration.")
            raise Exception("Machine Object not passed")

        # checking if commcell object is passed or not
        if not self.commcell:
            self.log.error("commcell object is not passed")
            raise Exception("Commcell Object Not passed")

        # checking if machine is Windows machine
        if machine_object.os_info.lower() == "windows":
            # storing base path
            base_path = machine_object.join_path(DEFAULT_INSTALL_DIRECTORY_WINDOWS, "Base").replace(" ", "` ")

        # the machine is Unix machine
        else:
            # storing base path
            base_path = machine_object.join_path(DEFAULT_INSTALL_DIRECTORY_UNIX, "Base")
            base_path = base_path.replace(" ", "\\ ")

        if not machine_object.check_directory_exists(base_path):
            self.log.error("Base folder does not exist")
            raise Exception("Base Folder does not exist")

        sim_path = machine_object.join_path(base_path, "SIMCallWrapper")
        command = f"{sim_path} -OpType 106"

        # Executing SIM Command
        self.log.info("Executing SIM Command")
        output = machine_object.execute_command(command)
        self.log.info("Executed command")

        if output.exception_message:
            self.log.error(output.exception_message)
            raise Exception(output.exception_message)

        self.log.info("Deregistration of client successfull")
