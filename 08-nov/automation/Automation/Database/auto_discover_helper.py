# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing database related operations.

AutoDiscoverApp is the only class defined in this file.

AutoDiscoverApp:


AutoDiscoverApp:
    __init__()                          --  initialise object of AutoDiscoverApp object

    client_group_with_auto_discover()   -- runs required client group operations

    organization_with_auto_discover()   -- runs required company level operations

    add_client_to_client_group()        -- adds client to client group

    install_client()                    -- install FS ida

    uninstall_client()                  -- uninstall client


"""
import time
from base64 import b64encode
from AutomationUtils import logger
from AutomationUtils.machine import Machine
from cvpysdk.deployment.deploymentconstants import WindowsDownloadFeatures, UnixDownloadFeatures


class AutoDiscoverApp(object):
    """Class for performing operations generic to all the database iDAs"""

    def __init__(self, commcell):
        """Initialize the AutoDiscover helper object.

            Args:
                commcell             (obj)  --  Commcell object

            Returns:
                object - instance of AutoDiscover helper class

        """
        self.commcell = commcell
        self.log = logger.get_log()
        self.client_group_obj = None
        self.client_obj = None
        self.company_obj = None


    def client_group_with_auto_discover(self, client_group_name, delete_flag=True):
        """
        runs client group operation required for autodiscover feature

            Args:
                client_group_name             (str)  --  name of the client group

                delete_flag                  (bool)  --  default True

            Returns:
                if exception raises
        """
        try:
            group_dic = {'clientgroup_description': 'Automationcreated clientgroup for autodiscoverapplication'}
            if self.commcell.client_groups.has_clientgroup(client_group_name):
                if delete_flag:
                    self.log.info("Client group already exists, deleting it.")
                    self.commcell.client_groups.delete(client_group_name)
                    self.commcell.refresh()
                    self.client_group_obj = self.commcell.client_groups.add(
                        client_group_name, group_options=group_dic)
                    self.log.info("Created client group : {0}".format(self.client_group_obj))
                else:
                    self.client_group_obj = self.commcell.client_groups.get(client_group_name)
            else:
                self.log.info("Client group doesnot exists, creating fresh.")
                self.client_group_obj = self.commcell.client_groups.add(
                    client_group_name, group_options=group_dic)
                self.log.info("Created client group : {0}".format(self.client_group_obj))

            ####enable auto discover at client group level###################
            enable_auto_discovery = self.client_group_obj.is_auto_discover_enabled
            if enable_auto_discovery:
                self.log.info("autodiscover application feature is enabled and value is : {0}".
                              format(enable_auto_discovery))
            else:
                self.log.info("autodiscover application feature is not enabled and value is : {0}".
                              format(enable_auto_discovery))
                self.log.info("autodiscover option is not enabled.enable it")
                self.client_group_obj.enable_auto_discover()
        except Exception as exp:
            self.log.exception("An error occurred while creating client group with auto discover enabled")
            raise exp

    def organization_with_auto_discover(self, company_name, company_name_alias, email):
        """

        runs company level operation required for autodiscover feature

            Args:
                company_name             (str)  --  name of the company

                company_name_alias       (str)  --  company alias name

                email                    (str)  --  email for company creation

            Returns:
                if exception raises
        """
        try:
            if self.commcell.organizations.has_organization(company_name):
                self.log.info("companay name already exists, deleting it.")
                self.commcell.organizations.delete(company_name)
                self.log.info("companay is {0}:deactivated and deleted.".
                              format(company_name))
                self.log.info("companay is deleted...need to delete associated server ")
                if self.commcell.client_groups.has_clientgroup(company_name):
                    self.log.info("Client group already exists, deleting it.")
                    self.commcell.client_groups.delete(company_name)
                    self.log.info("Client group deleted {0} sucessfully.".format(company_name))
            self.commcell.refresh()
            self.log.info("creating new company with name {0}".format(company_name))
            self.company_obj = self.commcell.organizations.add(
                company_name, email, 'admin',
                company_name_alias, enable_auto_discover=True)

            enable_auto_discovery = self.company_obj.is_auto_discover_enabled
            if enable_auto_discovery:
                self.log.info("autodiscover application feature is enabled and value is : {0}".
                              format(enable_auto_discovery))
            self.client_group_with_auto_discover(company_name, delete_flag=False)
        except Exception as exp:
            self.log.exception("An error occurred while creating organization with auto discover enabled")
            raise exp

    def add_client_to_client_group(self, client_name):
        """
        Adds client to the client group

            Args:
                client_name             (str)  --  clientname

            Returns:
                if exception raises
        """
        try:
            update_client_group = self.client_group_obj.add_clients([client_name])
            self.log.info("sucessfully updated client group with client association: {0}".
                          format(update_client_group))
        except Exception as exp:
            self.log.exception("An error occurred while adding client to client group")
            raise exp

    def install_client(self, client_name, client_user_name, client_password, ostype="windows"):
        """
        Adds client to the client group

            Args:
                client_name             (str)  --  clientname

                client_user_name        (str)  --  remote machine username

                client_password         (str)  --  remote machine password

                ostype                  (str)  --  specify os type
                                        ex:windows or unix

            Returns:
                if exception raises
        """
        try:
            if self.commcell.clients.has_client(client_name):
                self.log.info("Client with name {0} already exists".format(client_name))
            else:
                self.log.info("client does not exists.. need to install FS package..\
                            and add client to client group...")
                if ostype.lower() == "windows":
                    install_job = self.commcell.install_software(
                        client_computers=[client_name],
                        windows_features=[WindowsDownloadFeatures.FILE_SYSTEM.value],
                        username=client_user_name,
                        password=b64encode(client_password.encode()).decode("utf-8")
                    )
                else:
                    install_job = self.commcell.install_software(
                        client_computers=[client_name],
                        unix_features=[UnixDownloadFeatures.FILE_SYSTEM.value],
                        username=client_user_name,
                        password=b64encode(client_password.encode()).decode("utf-8")
                    )
                self.log.info("Job {0} started for Installing Client".format(install_job.job_id))

                if not install_job.wait_for_completion():
                    raise Exception("Failed to run Install job with error: {0}".format(install_job.delay_reason))

                if install_job.status == "Completed w/ one or more errors":
                    raise Exception("Job Completed with one or more errors")
                else:
                    self.log.info("Successfully finished Installing Client")
            self.log.info("client exists...just refresh client...")
            self.commcell.clients.refresh()
            self.client_obj = self.commcell.clients.get(client_name)
        except Exception as exp:
            self.log.exception("An error occurred while installing client")
            raise exp

    def uninstall_client(self, client_name):
        """

        uninstalls the packages from client

        Returns:
                if exception raises
        """
        try:
            uninstall_job = self.client_obj.uninstall_software(force_uninstall=True)
            self.log.info("Job {0} started for unstalling Client".
                          format(uninstall_job.job_id))

            if not uninstall_job.wait_for_completion():
                raise Exception("Failed to run Install job with error: {0}".
                                format(uninstall_job.delay_reason))

            if uninstall_job.status == "Completed w/ one or more errors":
                raise Exception("Job Completed with one or more errors")
            else:
                self.log.info("Successfully finished UNInstalling Client")
            self.commcell.clients.delete(client_name)
        except Exception as exp:
            self.log.exception("An error occurred while uninstalling client")
            raise exp

    def validate_auto_discover(self, agent_name, patteren1, patteren2, patteren3):
        """
        Method for validating agent and required agents logs for autodiscover app

            Args:
                agent_name             (str)  --  agentname
                                       ex:oracle,mysql,sql,postgressql

                patteren1              (str)  --  search string to validate logs

                patteren2              (str)  --  search string to validate logs

                patteren2              (str)  --  search string to validate logs

            Returns:
                if exception raises
        :return:
        """
        try:

            ####check agents installed on client####
            if self.client_obj.agents.has_agent(agent_name):
                self.log.info(
                    "Agent with name {0} already exists".format(agent_name))
            else:
                self.log.info("Agent with name {0} does not exists".format(agent_name))
                time.sleep(600)
                if self.client_obj.agents.has_agent(agent_name):
                    self.log.info("Agent with name {0}  exists".format(agent_name))
                    agent = self.client_obj.agents.get(agent_name)
                    self.log.info("agents installed are : {0}".format(agent))
                else:
                    time.sleep(600)
                    if self.client_obj.agents.has_agent(agent_name):
                        self.log.info("Agent with name {0} already exists".format(agent_name))
                        agent = self.client_obj.agents.get(agent_name)
                        self.log.info("agents installed are : {0}".format(agent))
                    else:
                        raise Exception("Agent is not installed")

            ###Get commvalut logs and validate the app detected \n#####
            ###and install software job invoked for the specific app###
            self.log.info("##Getting commvault log location##")
            commvault_log_path = self.client_obj.log_directory
            machine_obj = Machine(self.client_obj)
            cvd_log = machine_obj.join_path(commvault_log_path, "cvd.log")
            cv_install_client_log = machine_obj.join_path(commvault_log_path, "CvInstallClient.log")
            self.log.info("##Validating for string from logs starts here##")
            read_patteren = machine_obj.read_file(cvd_log)
            if read_patteren.find(patteren1) >= 0:
                self.log.info("found correct  pattern {0} for app discover in cvd.log".format(patteren1))
                if read_patteren.find(patteren2) >= 0:
                    self.log.info("found correct package pattern {0} in cvd.log".format(patteren2))
                    if read_patteren.find(patteren3) >= 0:
                        self.log.info("found correct package pattern {0} in cvd.log".format(patteren3))
            if read_patteren.find("AutoDetectApp::PullInstall() - Pull and install succeeded") >= 0:
                self.log.info("found correct package  string in cvd.log")

            ###checking Install log for install job success or not###
            read_patteren = machine_obj.read_file(cv_install_client_log)
            if read_patteren.find("Received a request for [Auto discovery install task]") >= 0:
                self.log.info("found correct  string  in CvInstallClient.log")
        except Exception as exp:
            self.log.exception("An error occurred while uninstalling client")
            raise exp

