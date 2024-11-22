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

    setup()         --  sets up the variables required for running the testcase

    run()           --  run function of this test case

    teardown()      --  tears down the things created for running the testcase

"""
import time
import datetime
from cvpysdk.commcell import Commcell
from AutomationUtils import machine
from AutomationUtils.cvtestcase import CVTestCase
from Application.AD import CVADHelper
from Reports.utils import TestCaseUtils
from Application.AD.exceptions import ADException
from Web.Common.page_object import TestStep
from cvpysdk.dashboard.ad_dashboard import AdDashboard
from cvpysdk.client import Clients



class TestCase(CVTestCase):
    """
    Class for verifying details on the AD Dashboard.
    Adding a new Azure AD Client.
    """

    TestStep=TestStep()
    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = ""
        self.app_type = None
        self.app_name = None
        self.utils = TestCaseUtils(self)
        self.subclient = None
        self.webconsole_hostname = None
        self.username = None
        self.password = None
        self.host_machine = None
        self.ad_comphelper = None
        self.server = None
        self.commcell_object=None
        self.server=None
        self.host_machine=None
        self.ad_comphelper=None
        self.client=None
        self.agent=None
        self.instance=None
        self.backupset=None
        self.client_obj=None
        self.agent_obj=None
        self.inst_obj=None
        self.backupset_obj =None
        self.backupset_id=None
        self.subclient_obj =None
        self.reponse=None
        self.apps_response=None
        self.azure_ad_name=None
        self.data=None
        self.plan_id=None
        self.plan_name=None
        self.application_Id=None
        self.application_Secret=None
        self.azure_Directory_Id=None
        self.AdDashboard_obj=None
        self.client_name = None

    @TestStep
    def get_ad_dashboard_details(self):
        """
        Function to generate response from the AD Dashboard API.
        """
        self.response=self.AdDashboard_obj.get_ad_dashboard_details()

    @TestStep
    def get_ad_apps_details(self):
        """
        Function to generate response from the AD Apps API
        """
        self.apps_response=self.AdDashboard_obj.get_ad_apps_details()

    @TestStep
    def check_configured(self):
        """
        Function to verify whether both the AD and Azure AD are configured or not.
        """
        configure_dict=self.AdDashboard_obj.is_configured

        if configure_dict["adconfigure"] and configure_dict["apps_adconfigure"] and configure_dict["aadconfigure"] and configure_dict["apps_aadconfigure"]:
            self.log.info('AD and Azure AD are configured')
        elif not configure_dict["adconfigure"] and not configure_dict["apps_adconfigure"] and not configure_dict["aadconfigure"]and not configure_dict["apps_aadconfigure"]:
            raise ADException('adpage', '204')
        elif not configure_dict["adconfigure"] and not configure_dict["apps_adconfigure"]:
            raise ADException('adpage', '205')
        else:
            raise ADException('adpage', '206')

    @TestStep
    def verify_domains_and_tenants(self):
        """
        Function to verify the number of domain controllers in AD and tenants in Azure AD.
        """
        domains_and_tenants_dict=self.AdDashboard_obj.domains_and_tenants


        self.log.info(f'Total entities from dashboard: {domains_and_tenants_dict["total_entities"]}')
        self.log.info(f'Total entities from apps: {domains_and_tenants_dict["apps_totalentities"]}')
        if domains_and_tenants_dict["total_entities"] == domains_and_tenants_dict["apps_totalentities"]:
            self.log.info('Total number of entities are verified')
        else:
            raise ADException('adpage', '207')
        self.log.info(' ')

        self.log.info(f'Total Domains {domains_and_tenants_dict["domain_controllers"]} and Tenants {domains_and_tenants_dict["tenants"]} from dashboard')
        self.log.info(f'Total Domains {domains_and_tenants_dict["apps_domain_controllers"]} and Tenants {domains_and_tenants_dict["apps_tenants"]} from apps')
        if (domains_and_tenants_dict["domain_controllers"] == domains_and_tenants_dict["apps_domain_controllers"] and domains_and_tenants_dict["tenants"] == domains_and_tenants_dict["apps_tenants"]):
            self.log.info('Number of Domain Contollers '
                              'and Tenents are verified sucessfully')
        else:
            raise ADException('adpage', '208')

        self.data.extend([domains_and_tenants_dict["total_entities"],domains_and_tenants_dict["domain_controllers"],domains_and_tenants_dict["tenants"]])


    @TestStep
    def verify_backup_health(self):
        """
        Function to verify the Backup Health Panel of AD Dashboard
        """
        backup_health_dict=self.AdDashboard_obj.backup_health

        self.log.info(f'Recently backedup from dashboard {backup_health_dict["recently_backedup"]} and Recently backedup from apps {backup_health_dict["apps_recently_backedup"]}')
        self.log.info(f'Recently backedup % from dashboard {backup_health_dict["recently_backedup_per"]} and Recently backedup % from apps {backup_health_dict["apps_recently_backedup_per"]}')
        self.log.info(f'Recently not backedup from dashboard {backup_health_dict["recently_not_backedup"]} and Recently not backedup from apps {backup_health_dict["apps_recently_not_backedup"]}')
        self.log.info(f'Recently not backedup % from dashboard {backup_health_dict["recently_not_backedup_per"]} and Recently not backedup % from apps {backup_health_dict["apps_recently_not_backedup_per"]}')
        self.log.info(f'Never backedup from dashboard {backup_health_dict["never_backedup"]} and Never backedup from apps {backup_health_dict["apps_never_backedup"]}')
        self.log.info(f'Never backedup % from dashboard {backup_health_dict["never_backedup_per"]} and never backedup % from apps {backup_health_dict["apps_never_backedup_per"]}')
        self.log.info(' ')
        if ((backup_health_dict["recently_backedup"],backup_health_dict["recently_backedup_per"],
             backup_health_dict["recently_not_backedup"],backup_health_dict["recently_not_backedup_per"],
             backup_health_dict["never_backedup"],backup_health_dict["never_backedup_per"])==(backup_health_dict["apps_recently_backedup"],backup_health_dict["apps_recently_backedup_per"],
                                                  backup_health_dict["apps_recently_not_backedup"],backup_health_dict["apps_recently_not_backedup_per"],
                                                 backup_health_dict["apps_never_backedup"],backup_health_dict["apps_never_backedup_per"])):
            self.log.info("Backup health Panel verified")
        else:
            raise ADException('adpage', '209')


    @TestStep
    def verify_data_distribution(self):
        """
        Function to verify the Data Distribution Panel of AD Dashboard
        """
        data_distribution_dict=self.AdDashboard_obj.data_distribution

        self.log.info(f'Backup size from dashboard {data_distribution_dict["backup_size"]} MB and Backup size from apps {data_distribution_dict["apps_backup_size"]} MB')
        self.log.info(f'Backup obj from dashboard {data_distribution_dict["backup_obj"]} K and Backup size from apps {data_distribution_dict["apps_backup_obj"]} K')
        self.log.info(' ')
        if data_distribution_dict["backup_size"]==data_distribution_dict["apps_backup_size"]:
            self.log.info("Backup Size in Data Distribution "
                          "is verified")
        else:
            raise ADException('adpage', '210')

        if data_distribution_dict["backup_obj"]==data_distribution_dict["apps_backup_obj"]:
            self.log.info("Backup Objects in Data Distribution "
                          "is verified")
        else:
            raise ADException('adpage', '211')

        self.data.extend([data_distribution_dict["backup_size"],data_distribution_dict["backup_obj"]])

    @TestStep
    def verify_application_panel(self):
        """
        Function to verify the Application Panel of AD Dashboard
        """
        application_panel_dict=self.AdDashboard_obj.application_panel

        self.log.info(f'Azure AD Tenants from dashboard {application_panel_dict["aad_tenant"]} and Azure AD Tenants from apps {application_panel_dict["apps_aad_tenant"]}')
        self.log.info(
            f'Azure AD size from dashboard {application_panel_dict["aad_backup_size"]} MB and Azure AD Tenants from apps {application_panel_dict["apps_aad_backup_size"]} MB')
        self.log.info(
            f'Azure AD Obj from dashboard {application_panel_dict["aad_backup_obj"]} K and Azure AD Tenants from appa {application_panel_dict["apps_aad_backup_obj"]} K')
        self.log.info(
            f'Azure AD SLA Met % from dashboard {application_panel_dict["aad_sla_per"]} and Azure AD SLA Met % from apps {application_panel_dict["apps_aad_sla_per"]}')
        self.log.info(
            f'Azure AD SLA Not Met % from dashboard {application_panel_dict["aad_not_sla_per"]} and Azure AD SLA Met % from apps {application_panel_dict["apps_aad_not_sla_per"]}')
        self.log.info(' ')
        if (application_panel_dict["aad_tenant"] == application_panel_dict["apps_aad_tenant"] and
                (application_panel_dict["aad_backup_size"] == application_panel_dict["apps_aad_backup_size"]) and
                (application_panel_dict["aad_backup_obj"] == application_panel_dict["apps_aad_backup_obj"])):
            self.log.info("Azure AD Data are verified")
        else:
            raise ADException('adpage', '212')
        self.log.info(' ')

        self.log.info(f'AD Domains from dashboard {application_panel_dict["ad_domains"]} and AD Domains from apps {application_panel_dict["apps_ad_domains"]}')
        self.log.info(f'AD size from dashboard {application_panel_dict["ad_backup_size"]} MB and AD size from apps {application_panel_dict["apps_ad_backup_size"]} MB')
        self.log.info(f'AD Obj from dashboard {application_panel_dict["ad_backup_obj"]} K and AD Obj from apps {application_panel_dict["apps_ad_backup_obj"]} K')
        self.log.info(f'AD SLA Met % from dashboard {application_panel_dict["ad_sla_per"]} and AD SLA Met % from apps {application_panel_dict["apps_ad_sla_per"]}')
        self.log.info(
            f'AD SLA Not Met % from dashboard {application_panel_dict["ad_not_sla_per"]} and AD SLA Not Met % from apps {application_panel_dict["apps_ad_not_sla_per"]}')
        self.log.info(' ')
        if (application_panel_dict["ad_domains"] == application_panel_dict["apps_ad_domains"] and
                (application_panel_dict["ad_backup_size"] == application_panel_dict["apps_ad_backup_size"]) and
                (application_panel_dict["ad_backup_obj"] == application_panel_dict["apps_ad_backup_obj"])):
            self.log.info("AD Data are verified")
        else:
            raise ADException('adpage', '213')


    @TestStep
    def add_azure_ad_client(self):
        """
        Function to create a new Azure AD client
        """
        self.client_name = datetime.datetime.now().strftime('AzureADAuto%d%b%H%M')
        client_obj = Clients(self._commcell)
        self.azure_ad_name = client_obj.add_azure_ad_client(client_name=self.client_name, plan_name=self.plan_name,
                                                            application_Id=self.application_Id,
                                                            application_Secret=self.application_Secret,
                                                            azure_directory_Id=self.azure_Directory_Id)
        self.log.info(f'New Azure AD Client {self.client_name} created')

    @TestStep
    def update_commcell(self):
        """
        Updating the Commcell
        """
        self.commcell_object = Commcell(webconsole_hostname=self.webconsole_hostname,
                                        commcell_username=self.username,
                                        commcell_password=self.password)
    @TestStep
    def value(self):
        """
        Function printing value before and after adding a client
        """
        self.log.info(f'Totalentities before adding client {self.data[0]} and Totalentities after adding client {self.data[5]}')
        self.log.info(f'Total Domain Controller before adding client {self.data[1]} and Total Domain Controller after adding client {self.data[6]} ')
        self.log.info(f'Total Tenants before adding client {self.data[2]} and Total Tenants after adding the client {self.data[7]}')
        self.log.info(' ')
        self.log.info(f'Backup size before adding client {self.data[3]} and Backup size after adding client {self.data[8]}')
        self.log.info(f'Backup object before adding client {self.data[4]} and Backup object after adding client {self.data[9]}')



    def setup(self):
        """
        Setup function for testcase
        """

        self.log.info("Login to CS, Setup function begins")
        self.log.info(' ')
        self.webconsole_hostname=self.inputJSONnode['commcell']['webconsoleHostname']
        self.username = self.inputJSONnode['commcell']['commcellUsername']
        self.password = self.inputJSONnode['commcell']['commcellPassword']
        ad_user = self.tcinputs['ServerUsername']
        ad_pass = self.tcinputs['ServerPassword']
        self.subclient = self.tcinputs['subclient']
        self.commcell_object = Commcell(webconsole_hostname=self.webconsole_hostname,
                                        commcell_username=self.username,
                                        commcell_password=self.password)
        self.server = self.tcinputs['ServerName']
        self.host_machine = machine.Machine(self.server, self.commcell)
        self.ad_comphelper = CVADHelper.CVADHelper(self.log,self.commcell_object,self.server,ad_username=ad_user,ad_password=ad_pass)
        self.AdDashboard_obj=AdDashboard(self._commcell)
        self.agent="Azure AD"
        self.instance="defaultInstanceName"
        self.backupset="defaultBackupSet"
        self.plan_id=self.tcinputs['PlanID']
        self.plan_name=self.tcinputs['PlanName']
        self.application_Id=self.tcinputs['applicationId']
        self.application_Secret=self.tcinputs['applicationSecret']
        self.azure_Directory_Id=self.tcinputs['azureDirectoryId']

        self.data=[]


    def run(self):
        """Main function for test case execution"""

        try:
            self.log.info("Login completed,Run function begins")
            # Getting AD Dashboard API Response
            self.get_ad_dashboard_details()

            # Getting AD Apps API Response
            self.get_ad_apps_details()

            # Calling funtion to verify the configuration of AD and Azure AD
            self.check_configured()
            #
            # Calling function to verify the number of domain controllers in AD and tenants in Azure AD
            self.verify_domains_and_tenants()

            # Calling function to verify the Backup Health Panel of AD Dashboard
            self.verify_backup_health()

            # Calling function to verify the Data Distribution Panel of AD Dashboard
            self.verify_data_distribution()

            # Calling function to verify the Application Panel of AD Dashboard
            self.verify_application_panel()

            # Calling function to create a new Azure AD client
            self.add_azure_ad_client()
            time.sleep(15)
            self.update_commcell()

            self.client_obj = self.commcell_object.clients.get(self.client_name)
            self.agent_obj = self.client_obj.agents.get(self.agent)
            self.inst_obj = self.agent_obj.instances.get(self.instance)
            self.backupset_obj = self.inst_obj.backupsets.get(self.backupset)
            self.subclient_obj = self.backupset_obj.subclients.get(self.subclient)

            # Backing up the New Azure AD Client
            self.log.info('Triggering the backup for new Azure AD client')
            self.ad_comphelper.do_backup(subclient_obj=self.subclient_obj)
            self.log.info('Backup Completed')

            # Getting AD Dashboard API Response
            self.get_ad_dashboard_details()

            # Getting AD Apps API Response
            self.get_ad_apps_details()

            # Calling funtion to verify the configuration of AD and Azure AD
            self.check_configured()

            # Calling function to verify the number of domain controllers in AD and tenants in Azure AD
            self.verify_domains_and_tenants()

            # Calling function to verify the Backup Health Panel of AD Dashboard
            self.verify_backup_health()

            # Calling function to verify the Data Distribution Panel of AD Dashboard
            self.verify_data_distribution()

            # Calling function to verify the Application Panel of AD Dashboard
            self.verify_application_panel()

            self.value()

        except ADException as exp:
            raise ADException('ad', '007',
                              exception_message="Exception in run function") from exp

    def tear_down(self):
        """Teardown function of this test case"""
        self.commcell_object.clients.delete(self.client_name)
        self.log.info("Teardown function")