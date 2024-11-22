# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing Metallic services related operations on Onprem/MSP Commcell

This file has the support for validations to Metallic operations like subscription, unsubscribe, cloud solutions,
switcher, Navigation settings etc.

MetallicHelper:

    __init__()                                  -- Intializing the metallic helper details

    add_CloudServiceUrl()                       -- Adds the metallicCloudServiceUrl key

    add_enableCompanyLinking()                  -- Adds the enableCompanyLinkingToMetallic key

    metallic_linking()                          -- Links MSP/onprem to metallic cell

    validate_linking()                          -- Validate if metallic linking/unlinking is successful or not

    validate_linking_on_cloud()                 -- Validates if linking is successful on metallic cell

    validate_linking_on_onprem()                -- Validates if linking is successful on Onprem/ MSP cell

    _cloud_service_details()                    -- Returns the cloud service details that are registered on MSP/Onprem

    _completed_solutions()                      -- Returns the completed solutions dict from MSP/Onprem cell

    metallic_unlink()                           -- UnSubscribe metallic for MSP/Onprem cell

    get_completed_solutions()                   -- Gets the list of completed solutions

    is_switcher_available()                     -- Validates if switcher is available for a user

    metallic_nav()                              -- Validates if Metallic nav is available for a user

"""
import json
from AutomationUtils import logger, database_helper


class MetallicHelper:
    """ Helper class for validating Metallic related operations"""

    def __init__(self, commcell_object):
        """Intializes object of the MetallicHelper class for validating related operations

            Args:
                commcell_object (object) -instance of the commcell class

            Returns:
                object - instance of the MetallicHelper class

        """
        self._commcell_object = commcell_object
        self.metallic_obj = self._commcell_object.metallic
        self.log = logger.get_log()

    def add_CloudServiceUrl(self, webconsole_url):
        """
            Deletes the key metallicCloudServiceUrl if already present and adds it with required value

            Args:
                webconsole_url  (str)       :   Cloud webconsole URL
        """
        key = 'metallicCloudServiceUrl'
        self._commcell_object.delete_additional_setting(category='WebConsole', key_name=key)
        self.log.info('Adding %s Additional Setting', key)
        self._commcell_object.add_additional_setting('webconsole',
                                                     key,
                                                     'STRING',
                                                     webconsole_url)

    def add_enableCompanyLinking(self):
        """
            Deletes the key enableCompanyLinkingToMetallic if already present and adds it with required value
        """
        key = 'enableCompanyLinkingToMetallic'
        self._commcell_object.delete_additional_setting(category='WebConsole',
                                                        key_name=key)
        self.log.info('Adding %s Additional Setting', key)
        self._commcell_object.add_additional_setting('webconsole',
                                                     key,
                                                     'BOOLEAN',
                                                     'true')

    def metallic_linking(self, cloud_hostname, cloud_username, cloud_user_pwd, onprem_company=None):
        """
            MSP or Onprem commcell linking to cloud company

            Args:
                 cloud_hostname (str)       :   cloud commcell hostname

                 cloud_username (str)       :   Cloud commcell company's tenant admin username

                 cloud_user_pwd (str)       :   Cloud commcell company's tenant admin password

                 onprem_company (str)       :   Name of the company created on onprem/MSP commcell

        """
        self.log.info("Linking MSP/Onprem cell to Metallic")
        self.metallic_obj.metallic_subscribe(cloud_hostname, cloud_username, cloud_user_pwd, onprem_company)

    def validate_linking(self, cloud_company, cloud_admin_helper_obj,
                         is_linking=True,
                         is_company_to_company_linking=False,
                         onprem_company=None,
                         onprem_ta_object=None):
        """
        Validate if onprem/MSP is successfully linked/unlinked to/from Metallic cell

        Args:
            cloud_company (str)                     :   Name of the company created on cloud

            cloud_admin_helper_obj (object)         :   MetallicHelper object for Cloud admin user

            is_linking  (bool)                      :   True if validating Linking
                                                        False if validating Unlinking

            is_company_to_company_linking   (bool)  :   True if it is onprem company to cloud company linking else False

            onprem_company  (str)                   :   Onprem Company name only in case of company to company linking

            onprem_ta_object   (object)             :   MetallicHelper object for Onprem Tenant admin user incase of
                                                        company to company linking

        """
        self.log.info("Validation at MSP/Onprem side when linking is %s", is_linking)
        self.csdb = database_helper.CommServDatabase(self._commcell_object)
        completed_solutions, cloud_service_details = self.validate_linking_on_onprem(is_company_to_company_linking,
                                                                                     is_linking,
                                                                                     onprem_company,
                                                                                     onprem_ta_object)

        self.log.info("METALLIC solution status: %s", completed_solutions)
        guid = self._commcell_object.commserv_guid

        '''During linking, proceeding to cloud validation only if completed solutions in Onprem/MSP side is True
           During Unlinking, proceeding to cloud validation only if completed solutions in Onprem/MSP side is False '''

        if completed_solutions ^ is_linking is False:
            self.log.info("Validation at MSP/onprem side is successful hence validating at cloud side")
            tpa = cloud_admin_helper_obj.validate_linking_on_cloud(cloud_company, guid, cloud_service_details)

            self.log.info("Third party app status on cloud : %s", tpa)

            if not is_linking:
                status = True if (tpa or completed_solutions) is False else False

            else:
                status = True if tpa and completed_solutions else False

            if not status:
                raise Exception("Validation Failed at cloud side")

            else:
                self.log.info("Validation successful")

        else:
            raise Exception("Validation Failed at MSP/ onprem side")

    def validate_linking_on_cloud(self, cloud_company, guid, cloud_details_registered_on_msp):
        """
        Validates the Thirdparty app created on Metallic

        Args:
            cloud_company (str)                     :   Name of the company created on cloud cell

            guid (str)                              :   Onprem/MSP commcell GUID

            cloud_details_registered_on_msp (dict)  :   Cloud service details that are registered on Onprem/MSP cell
            example dict:
            {
                'companyAlias': 'Company_900888',
                'GUID': '9BAB6F-3F0A-4E3C-89BA-111234567B'
                'redirectUrl': 'http://hostname:80/webconsole'
            }

        Returns:

             bool - Specifies whether validation at cloud is success or not

        """
        self.csdb = database_helper.CommServDatabase(self._commcell_object)
        query = "select longlongVal from APP_ComponentProp where componentType=1034 and propertyTypeId=61 and " \
                "componentId=(select id from App_ThirdPartyApp where appName='{0}')".format(guid)
        self.csdb.execute(query)
        associated_companies = self.csdb.fetch_all_rows()

        cloud_company = cloud_company.lower()
        cloud_guid = self._commcell_object.organizations.all_organizations_props[cloud_company]['GUID']
        cloud_company_id = self._commcell_object.organizations[cloud_company]

        self.log.info("Checking the associated companies for the thirdparty app")
        if str(cloud_company_id) in (item for sublist in associated_companies for item in sublist):
            if cloud_details_registered_on_msp:
                webconsole_hostname = 'http://' + self._commcell_object.commserv_hostname + ':80/webconsole'
                return True if cloud_company == cloud_details_registered_on_msp['companyAlias'].lower() and \
                               cloud_guid == cloud_details_registered_on_msp['GUID'] and \
                               webconsole_hostname == cloud_details_registered_on_msp['redirectUrl'] else False
            else:
                raise Exception("Cloud service details received are empty")

        else:
            self.log.info("Cloud company is not associated to the thirdparty app")
            return False

    def validate_linking_on_onprem(self, is_company_to_company_linking=False, is_linking=True,
                                   onprem_company=None, onprem_ta_object=None):
        """
        Validates if METALLIC service is present in completed solutions

        Args:
            is_company_to_company_linking   (bool)  :   True if it is onprem company to cloud company linking else False

            is_linking  (bool)                      :   True if validating Linking
                                                        False if validating unlinking

            onprem_company (str)                    :   Onprem Company name if company to cloud company linking

            onprem_ta_object (object)               :   MetallicHelper object for Onprem Tenant admin user incase of
                                                        company to company linking

        Returns :

            bool - Specifies whether validation at Onprem or MSP is success or not

            cloud_service_details   (dict)  :   registered cloud service details on MSP/Onprem

        """
        self.log.info("Fetching cloud service details when company to company linking is {0} and \nis_linking: {1}".
                      format(is_company_to_company_linking, is_linking))

        props = self._completed_solutions(is_company_to_company_linking, onprem_company)

        props = json.loads(props)
        if 'METALLIC' in props:
            if props['METALLIC'] is not True:
                raise Exception("Validation at MSP/onprem failed : METALLIC completed solution value is not True")

        if is_company_to_company_linking:
            cloud_service_details = onprem_ta_object._cloud_service_details(is_linking)
        else:
            cloud_service_details = self._cloud_service_details(is_linking)

        return True if 'METALLIC' in props else False, cloud_service_details

    def _cloud_service_details(self, is_linking):
        """
        Get cloud service details from MSP/Onprem

        Args:
            is_linking  (bool)      :   True if validating Linking
                                        False if validating unlinking
        Returns:

            cloud_service_details   (dict)  :   registered cloud service details on MSP/Onprem

        """
        try:
            flag = self.metallic_obj.is_metallic_registered()
            if flag:
                response = self.metallic_obj.cloudservices_details
                if response and not is_linking:
                    raise Exception("Cloud service details are available while validating Unlinking")

                cloud_service_details = {}
                cloud_service_details['companyAlias'] = response['cloudServices'][0]['associatedCompany'][
                    'companyAlias']
                cloud_service_details['GUID'] = response['cloudServices'][0]['associatedCompany']['GUID']
                cloud_service_details['redirectUrl'] = response['cloudServices'][0]['cloudService']['redirectUrl']

                return cloud_service_details

            else:
                if is_linking:
                    raise Exception("Metallic registered status is False during Linking is", is_linking)

                else:
                    self.log.info("As expected Metallic registered status is False during Linking is %s", is_linking)
                    return None

        except Exception as excp:
            if not is_linking:
                self.log.info("During validating Unlinking cloud service details %s", excp)
                return None

    def _completed_solutions(self, is_company_to_company_linking=False, onprem_company=None):
        """
        CSDB query to fetch the list of completed solutions

        Args:
            is_company_to_company_linking   (bool)  :   True if it is onprem company to cloud company linking else False

        Returns:
            props   (list)      :   completed solutions list from onprem/MSP

        """
        if is_company_to_company_linking:
            query = "select attrVal from App_CompanyProp where attrName= 'completedSetups' " \
                    "and componentNameId=(select id from UMDSProviders where domainName='{0}')".\
                format(onprem_company)
        else:
            query = "select value from gxGlobalParam where name = 'completedSetups'"

        self.csdb.execute(query)
        props = self.csdb.fetch_one_row()[0]

        self.log.info("commpleted solutions : %s", props)
        return props

    def get_completed_solutions(self, is_company_to_company_linking=False, commcell_object=None, onprem_company=None):
        """
        Validates the configured Metallic completed solutions

        Args:
            is_company_to_company_linking   (bool)  :   True if it is onprem company to cloud company linking else False

            commcell_object     (object)            :   Onprem tenant admin object if is_company_to_company_linking

            onprem_company  (str)                   :   Onprem Company name if is_company_to_company_linking

        Raises:

            If Completed solutions returned from API doesn't match with values from DB

        """
        self.log.info("Validating completed solutions when company to company linking is %s",
                      is_company_to_company_linking)
        if is_company_to_company_linking:
            completed_solutions = commcell_object.metallic.metallic_completed_solutions()
        else:
            completed_solutions = self.metallic_obj.metallic_completed_solutions()

        if completed_solutions == self._completed_solutions(is_company_to_company_linking, onprem_company):
            self.log.info("Completed solutions returned are valid")
        else:
            raise Exception("Completed solutions returned are not valid")

    def metallic_unlink(self):
        """
        Unsubscribe metallic
        """
        self.log.info("Unlinking Metallic subscription")
        self.metallic_obj.metallic_unsubscribe()

    def is_switcher_available(self, commcell_name, is_linking=True):
        """
        check if switcher is available for a user

        Args:
            commcell_name   (str)   :   Name of the commcell to check if present in the switcher for a logged in user

            is_linking (bool)       :   True if validating Linking
                                        False if validating Unlinking

        Raises:
            On linking if switcher is not available for user

            On unlinking if switcher is available for user

        """
        self.log.info("Validating if switcher is available for the user when is_linking is %s", is_linking)
        if commcell_name not in self._commcell_object.commcells_for_user:
            if not is_linking:
                self.log.info("Switcher is not available for user as expected")
            else:
                raise Exception("Switcher is not available for user")
        else:
            if is_linking:
                self.log.info("Switcher for %s is available for current logged-in user", commcell_name)
            else:
                raise Exception("Switcher is not available for user as expected")

    def metallic_nav(self, is_linking=True):
        """
        Checking if Metallic navigation is available

        Args:
            is_linking (bool)       :   True if validating Linking
                                        False if validating Unlinking

        Raises:
            On Linking if Metallic Navigation is not available

            On Unlinking if Metallic Navigation is available

        """
        self.log.info("Validating if Metallic navigation is available for the user when is_linking is", is_linking)
        flag = self.metallic_obj.is_metallic_registered()
        if flag:
            if not is_linking:
                raise Exception("On unlinking Metallic Nav is still available for user")
            else:
                self.log.info("Metallic Nav is available for the logged in user")

        else:
            if is_linking:
                raise Exception("Metallic nav is not available for the user")
            else:
                self.log.info("Metallic Nav is not available for the logged in user")