from selenium.webdriver.common.by import By
# -**- coding: utf-8 -**-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file to maintain all the constants used by License test cases"""

"""
This module provides the function or operations that can be performed on
the License page on the AdminConsole

Class:

    LicenseGenerator

Attributes:
    commcell (obj)    --      Commcell object

    log (obj)        --     Log object

    lic_response(dict)    --    License information of commcell

    browser(obj)    --    Browser object

    driver(obj)    --    Browser driver object

    inputjsonnode(obj)    --     JSON node object

    _license_type(str)    --    Type of license

    lic_individual_details(dict) -- Details for the license summaries

    _sku(str)    --     sku numbers delimited by colon

    _sku_quantity(str)     --    sku number quantities

    evaluation_date(date obj)     --     The license expiry date foe New License

    expiry_date(date obj)    --     The license expiry date if Permanent with Expiry license

    operation_dict (dict)    --    The dictionary to store the hypervisor operation information

    _license_url (str)    --        URL for license generation

    _username (str)  --     Username for license generation

    _password  (str)   --    Password for license generation

    license_types (dict)    --    Dictionary for all license types





Functions:
    __init__()    --    Initialization license generator object for license create / update and apply on commserver

    license_url     --      Return the url for license generation


    license_url()   --       Set the license url

    license_type    --    Return the license type

    license_type()    --    Set the license type

    username    --    Return the username value

    username()    --    Set user name

    password    --    Return the password value

    password()    --    Set the password


    license_details    --    Function to get the license details

    apply_license()    --    Function to apply license on commserver

    get_license_individual_details    --    FFunction to get the report of license summary details of all tables


    open_ac_licensepage()    --    Open adminconsole and navigate to License

    applyfrom_ac_licensepage()    --    Function to apply license from admin console page

    close()    --    Function to close Adminconsole and Licensing site

    openlicensingsite()    --    Function to open license site


    modify_license()    --     Function to modify generated License


    create_newlicense()    --    Function to generate new License in webconsole


    __enter_evaluation_days()    --    Pick the evaluation date for New License Type


    __enter_termend_date()    --    Select the term end date for sku number using date picker


    __enter_expiration_date()    --    Select the expiration date of Pure Subscription/Permanent with Expiry type

    __enter_sku()    --    Enter all sku numbers applied for license

    __find_sku_row()    --     Function to find the text input box with corresponding sku number and return it
        with the add button. Otherwise, the function will return None

    __result_found()    --     Function will return True if sku found otherwise return False

    update_license()    --    Function to update license

    delete_license()    --    Function to delete license

    hyperv_operation()    --    create/delete/Revert snap of the virtual machine

    validate_license_details()    --     Validates the details on the License page

    __validate_capacity_license()    --    Check the quantity of capacity license details is correct

    __validate_complete_oi_license()    --    Check the quantity of complete oi license details is correct

    __validate_activate_license()    --     Check the quantity of activate license details is correct

    __validate_metallic_license()    --    Check the quantity of metallic license details is correct

    change_time_date()    --    Change commserver date and time and restart services

    license_calendar_date_picker()    --    Picks date from the date picker calendar

    validate_warning_popup()    --    Validate the expiry date on warning windows is correct


"""
from datetime import datetime, timedelta
import glob
import os.path
import re
import time
from cvpysdk.license import LicenseDetails
from AutomationUtils import config
from AutomationUtils import constants as automation_constants
from AutomationUtils.machine import Machine
import VirtualServer.VSAUtils.VirtualServerUtils as vsutil
from Web.AdminConsole.AdminConsolePages.License import License
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.WebConsole.License import licensegenerator
from Web.WebConsole.webconsole import WebConsole


class LicenseGenerator:
    """Class for generating License"""

    def __init__(self, commcell, log, inputjsonnode,
                 hyperv_host_name=None, hypervusername=None, hypervpassword=None, vmname=None):
        """
        License generator class for license create / update and apply on commserver

        Args:
            commcell (object)     -- commcell object of the monitoring commcell
            log (object)          -- log object
            inputjsonnode(dict)   -- input values
            hyperv_host_name(str) -- hyperv hostname where commserv is located
            hypervusername(str)   -- hyperv administrator username
            hypervpassword (str)  -- hyperv administrator user password
            vmname (str)          -- Commserver VMName on hyperv
        """
        self.commcell = commcell
        self.log = log
        self.lic_response = None
        self.browser = None
        self.driver = None
        self.inputjsonnode = inputjsonnode
        self._license_type = None
        self.lic_individual_details = None
        self._license_sku_eval = None
        self._license_sku_quantity_eval = None
        self._license_sku_perm = None
        self._license_sku_quantity_perm = None
        self.evaluation_date = None
        self.expiry_date = None
        self.hyperv_host_name = None
        self.lic_object = None
        self.adminconsole = None
        self.webconsole = None
        self.licgen = None
        self.lic_details = None
        self.loginpage = None
        self.operation_dict = {
            "server_name": hyperv_host_name,
            "extra_args": "$null",
            "vm_name": vmname,
            "vhd_name": "$null"
        }
        if hyperv_host_name is not None:
            self.hyperv_host_name = Machine(hyperv_host_name, None, username=hypervusername, password=hypervpassword)
            self.hyperv_operation(optype="DELETE")
            self.hyperv_operation()

        _constants = config.get_config()
        self._license_url = _constants.license.url
        self._username = _constants.license.username
        self._password = _constants.license.password
        self.license_types = {'New License': 'Pilot', 'Pilot Extension': 'Pilot Extension', 'Permanent': 'Permanent',
                              'Pure Subscription/Permanent with Expiry': 'Permanent with Expiry',
                              'Permanent Eval Extension': 'Permanent Eval Extension'}

    def license_details(self):
        """
        Function to get the license details
        """
        try:
            lic_response = LicenseDetails(self.commcell)
            list_response = {}
            list_response['commcell_id'] = lic_response.commcell_id
            list_response['cs_hostname'] = lic_response.cs_hostname
            list_response['license_ipaddress'] = lic_response.license_ipaddress
            list_response['oem_name'] = lic_response.oem_name
            list_response['commcell_id'] = lic_response.license_mode
            list_response['serial_number'] = lic_response.serial_number
            list_response['registration_code'] = lic_response.registration_code
            self.lic_response = list_response
        except Exception as err:
            self.log.error("Exception raised while getting License details %s" % err)
            raise Exception("Exception raised while getting licensing site %s" % err)

    def get_license_individual_details(self):
        """
        Function to get the report of license summary details of all tables
        """
        try:
            lic_response = LicenseDetails(self.commcell)
            lic_response._get_detailed_licenses()
            list_response = {}
            list_response['capacity_licenses'] = lic_response.capacity_licenses
            list_response['complete_oi_licenses'] = lic_response.complete_oi_licenses
            list_response['virtualization_licenses'] = lic_response.virtualization_licenses
            list_response['user_licenses'] = lic_response.user_licenses
            list_response['activate_licenses'] = lic_response.activate_licenses
            list_response['metallic_licenses'] = lic_response.metallic_licenses
            list_response['other_licenses'] = lic_response.other_licenses
            self.lic_individual_details = list_response
        except Exception as err:
            self.log.error("Exception raised while getting License details %s" % err)
            raise

    def open_ac_licensepage(self, validate_popup=False):
        """ Open adminconsole and navigate to License
        args:

        validate_popup (boolean) : True if you want to close the popup in adminconsole

        """

        try:
            if self.browser is None:
                self.browser = BrowserFactory().create_browser_object()
                self.browser.open()
            else:
                self.browser.open(maximize=False)
            self.adminconsole = AdminConsole(self.browser, self.commcell.webconsole_hostname)

            if validate_popup:
                self.adminconsole.login(self.inputjsonnode['commcell']['commcellUsername'],
                                        self.inputjsonnode['commcell']['commcellPassword'], close_popup=False)
                self.validate_warning_popup()

            else:
                self.adminconsole.login(self.inputjsonnode['commcell']['commcellUsername'],
                                        self.inputjsonnode['commcell']['commcellPassword'], close_popup=True)
                self.adminconsole.wait_for_completion()
                self.adminconsole.navigator.navigate_to_license()
                self.lic_object = License(self.adminconsole)

        except Exception as exception:
            raise CVTestCaseInitFailure(exception)from exception

    def applyfrom_ac_licensepage(self, filepath, license_sku_perm="", license_sku_eval="", validate_popup=False):
        """
        function to apply license from admin console page
        args:
            filepath (str): provide the license file path 
            validate_popup (boolean) : True if you want to close the popup in adminconsole
            license_sku_perm (str)  : provide skus for permanent
            license_sku_eval (str)  : provide skus for evaluation
        """
        self.open_ac_licensepage(validate_popup)
        sku = []
        if license_sku_perm != "":
            sku.extend(license_sku_perm.split(","))
        if license_sku_eval != "":
            sku.extend(license_sku_eval.split(","))
        if len(sku) == 0:
            sku = None
        else:
            sku = ",".join(sku)
        if sku is not None and "MTL-MCSS-A1-TB" in sku:
            metallic = True
        else:
            metallic = False

        self.lic_object.apply_update_license(filepath, sku, metallic)
        if sku is not None:
            self.adminconsole.navigator.navigate_to_license()

    @property
    def close(self):
        """
        Function to close Adminconsole and Licensing site
        """
        AdminConsole.logout_silently(self.adminconsole)
        Browser.close_silently(self.browser)

    @property
    def openlicensingsite(self):
        """
        Function to open license site
        """
        try:
            # remove old licenses from temp directory
            filelist = glob.glob(os.path.join(automation_constants.TEMP_DIR, "*.*"))
            for file in filelist:
                os.remove(file)
            login_required = False
            if self.browser is None:
                self.browser = BrowserFactory().create_browser_object()
                self.browser.open()
                login_required = True
            self.driver = self.browser.driver
            self.driver.get(self._license_url)
            if login_required:
                self.webconsole = WebConsole(self.browser, self._license_url)
                self.webconsole.base_url = self._license_url
                self.webconsole.login(self._username, self._password, auto_open_login_page=False)
                self.licgen = licensegenerator.LicenseGenerator(self.webconsole)
                self.adminconsole = AdminConsole(self.browser, self._license_url)
        except Exception as err:
            self.log.error("Exception raised while opening licensing site %s" % err)
            raise Exception("Exception raised while opening licensing site %s" % err)

    def __validateinput(
            self,
            licensetype,
            license_sku_perm,
            license_sku_quantity_perm,
            license_sku_eval,
            license_sku_quantity_eval):
        """

        """

        if licensetype not in self.license_types.keys():
            raise Exception("Not a valid License type %s" % licensetype)
        self.license_type = licensetype
        if license_sku_perm:
            try:
                '''If the perm sku is not None, the string will be split and
                license_sku_quantity_perm value will be assigned'''
                self._license_sku_perm = license_sku_perm.split(',')
                self._license_sku_quantity_perm = int(license_sku_quantity_perm)
            except Exception as err:
                raise Exception("Invalid input type for license_sku_perm/license_sku_quantity_perm %s" % err)

        if license_sku_eval:
            try:
                '''If the eval sku is not None, the string will be split and
                 license_sku_quantity_eval value will be assigned'''
                self._license_sku_eval = license_sku_eval.split(',')
                self._license_sku_quantity_eval = int(license_sku_quantity_eval)
            except Exception as err:
                raise Exception("Invalid input type for license_sku_eval/license_sku_quantity_eval %s" % err)

    def modify_license(
            self,
            licensetype=None,
            license_sku_perm="",
            license_sku_quantity_perm="",
            license_sku_eval="",
            license_sku_quantity_eval="",
            sku_expiration="",
            license_expiration_days="",
            license_evaluation_days=""):
        """
        function to modify generated License
        args:
            licensetype(str): provide license type
            filepath (str): provide the license file path
            validate_popup (boolean) : True if you want to close the popup in adminconsole
            license_sku_perm (str)  : provide skus for permanent
            license_sku_eval (str)  : provide skus for evaluation
            license_sku_quantity_perm (str)  : provide quantity for permanent
            license_sku_quantity_eval (str)  : provide qunatity for evaluation
            license_expiration_days(str)    : provide license expiration days
            license_evaluation_days (str)   : provide license evaluation days
            sku_expiration (str)            : provide sku_expiration
        """
        try:

            self.__validateinput(licensetype, license_sku_perm,
                                 license_sku_quantity_perm, license_sku_eval, license_sku_quantity_eval)

            self.evaluation_days = license_evaluation_days
            self.expiry_date = license_expiration_days
            self.openlicensingsite
            self.license_details()
            self.licgen.goto_modify_license()
            create_lic_obj = licensegenerator.ModifyLicense(
                self.webconsole, self.adminconsole, self.lic_response, self.license_types)
            create_lic_obj.modify_license(
                licensetype,
                license_sku_perm,
                license_sku_quantity_perm,
                license_sku_eval,
                license_sku_quantity_eval,
                sku_expiration,
                license_expiration_days,
                license_evaluation_days)
            time.sleep(20)
            filelist = glob.glob(os.path.join(automation_constants.TEMP_DIR, "*.xml*"))
            license_file = ""
            for file in filelist:
                license_file = file
            if not license_file:
                raise Exception("License file not generated from licensing site")
            self.log.info("New license file %s" % license_file)
            return license_file
        except Exception as err:
            self.log.error("Exception raised while modifying license %s" % err)
            raise Exception('Exception raised while modifying license %s' % err)

    def create_newlicense(
            self,
            licensetype=None,
            license_sku_perm="",
            license_sku_quantity_perm="",
            license_sku_eval="",
            license_sku_quantity_eval="",
            sku_expiration="",
            license_expiration_days="",
            license_evaluation_days=""):
        """
        function to generate new License
        args:

            licensetype(str): provide license type
            license_sku_perm (str)  : provide skus for permanent
            license_sku_eval (str)  : provide skus for evaluation
            license_sku_quantity_perm (str)  : provide quantity for permanent
            license_sku_quantity_eval (str)  : provide qunatity for evaluation
            license_expiration_days(str)    : provide license expiration days
            license_evaluation_days (str)   : provide license evaluation days
            sku_expiration (str)            : provide sku_expiration
        """
        try:
            self.__validateinput(licensetype, license_sku_perm,
                                 license_sku_quantity_perm, license_sku_eval, license_sku_quantity_eval)
            self.openlicensingsite
            self.license_details()
            self.evaluation_days = license_evaluation_days
            self.expiry_date = license_expiration_days
            self.licgen.goto_create_license()
            create_lic_obj = licensegenerator.CreateLicense(
                self.webconsole, self.adminconsole, self.lic_response, self.license_types)
            create_lic_obj.create_newlicense(
                licensetype,
                license_sku_perm,
                license_sku_quantity_perm,
                license_sku_eval,
                license_sku_quantity_eval,
                sku_expiration,
                license_expiration_days,
                license_evaluation_days)
            time.sleep(20)
            filelist = glob.glob(os.path.join(automation_constants.TEMP_DIR, "*.xml*"))
            license_file = ""
            for file in filelist:
                license_file = file
            if not license_file:
                raise Exception("License file not generated from licensing site")
            self.log.info("New license file %s" % license_file)
            return license_file
        except Exception as err:
            self.log.error("Exception raised while generating license %s" % err)
            raise Exception('Exception raised while creating new license %s' % err)

    @property
    def delete_license(self):
        """
        Function to delete license from licensing website
        """
        try:
            self.openlicensingsite
            self.license_details()
            self.licgen.goto_delete_license()
            delete_lic_obj = licensegenerator.DeleteLicense(self.webconsole)
            delete_lic_obj.delete_license(self.lic_response['registration_code'])
        except Exception as err:
            self.log.error("Exception raised while deleting  license %s" % err)
            raise Exception('Exception raised while deleting  license %s' % err)

    def hyperv_operation(self, snap_name="License_snap", optype='CREATE'):
        """
        create/delete/Revert snap of the machine
        :param
        snap_name: name of the snap
        optype: type of snap operation to be performed
        :return:
            True - if operation succeds
            False - on Failure
        """
        try:

            self.vm_operation_file = "HyperVOperation.ps1"
            self.utils_path = vsutil.UTILS_PATH
            _ps_path = os.path.join(
                self.utils_path, self.vm_operation_file)
            if optype == 'CREATE':
                self.operation_dict["operation"] = "CreateSnap"
            elif optype == 'DELETE':
                self.operation_dict["operation"] = "DeleteSnap"
            elif optype == 'REVERT':
                self.operation_dict["operation"] = "RevertSnap"
            self.operation_dict["extra_args"] = snap_name

            if self.hyperv_host_name is not None:
                output = self.hyperv_host_name._execute_script(_ps_path, self.operation_dict)
                time.sleep(30)
                self.operation_dict["operation"] = "PowerOn"
                output = self.hyperv_host_name._execute_script(_ps_path, self.operation_dict)
                time.sleep(60)
            else:
                self.log.error("Hyperv server is not specified and you cannot do snap operations")
                return False
            _stdout = output.output
            if '0' in _stdout:
                self.log.info("Snapshot {} was successfull and wait for 20 seconds".format(optype))
                time.sleep(20)
                return True
            else:
                return False

        except Exception as err:
            self.log.exception("Exception in performing snap operation %s" % err)
            raise err

    def enter_quantity(self, map_lic):
        """
        Function to enter license quantity

        map_lic (dict): Provide license mapping

        """
        skus = set()
        if self._license_sku_perm is not None:
            for sku in self._license_sku_perm:
                if sku not in map_lic.keys():
                    raise Exception("Invalid sku")
                skus.add(sku)
                map_lic[sku]['quantity'] += map_lic[sku]['base'] * self._license_sku_quantity_perm
        if self._license_sku_eval is not None:
            for sku in self._license_sku_eval:
                if sku not in map_lic.keys():
                    raise Exception("Invalid sku")
                skus.add(sku)
                map_lic[sku]['quantity'] += map_lic[sku]['base'] * self._license_sku_quantity_eval
        return list(skus)

    @property
    def validate_license_details(self):
        """ Validates the details on the License page """
        license_mode_mapper = {"EVALUATION": 1000, "PRODUCTION": 1002, "DR_PRODUCTION": 1004}
        lic_response = LicenseDetails(self.commcell)
        details = self.lic_object.get_license_details()

        list_response = []

        list_response.append(lic_response.commcell_id)
        list_response.append(lic_response.cs_hostname)
        list_response.append(lic_response.license_ipaddress)
        list_response.append(lic_response.oem_name)
        list_response.append(lic_response.license_mode)
        list_response.append(lic_response.serial_number)
        list_response.append(lic_response.registration_code)

        if int(lic_response.expiry_date) != 0:
            list_response.append(datetime.fromtimestamp
                                 (int(lic_response.expiry_date)).strftime("%b %d, %Y").replace(" 0", " "))
        if 'License has expired.' in details.keys():
            list_details = [value for key, value in details.items()][:-1]
        else:
            list_details = [value for key, value in details.items()]

        key = [key for key, value in license_mode_mapper.items() if value == lic_response.license_mode][0]
        if key == list_details[4].split()[0].upper():
            self.log.info("Commserver is with correct license type")
        else:
            raise Exception(
                "Invalid license typer detected on commserver. DB license value {%s}, AC license value{%s}" %
                (key, list_details[4]))

        list_details[4] = license_mode_mapper[list_details[4].split()[0]]
        list_details[0] = int(list_details[0], 16)
        ordstring = 'To order an additional license, send email to prodreg@commvault.com'
        if ordstring in list_details:
            list_details.remove(ordstring)
        '''if the license type is EVALUATION'''
        if list_details[4] == license_mode_mapper["EVALUATION"]:
            '''Ignnore the last warning text'''
            if len(list_details) > len(list_response):
                list_details = list_details[:-1]
            if list_details == list_response:
                self.log.info("Details validated successfully")
            else:
                raise Exception(
                    "comparision failed for license details, Db values {%s}, AC values {%s}" %
                    (list_response, list_details))

        elif list_details[4] == license_mode_mapper["PRODUCTION"]:
            '''Ignnore the last warning text'''
            if len(list_details) > len(list_response):
                list_details = list_details[:-1]
            if list_details == list_response:
                self.log.info("Details validated successfully")
            else:
                raise Exception(
                    "comparision failed for license details, Db values {%s}, AC values {%s}" %
                    (list_response, list_details))

        map_lic = {
            "CV-BR-FT": {"table": "capacity_licenses", "row": "Commvault Backup and Recovery", "quantity":
                         0, "base": 1},
            "SB-C-DPE-1T": {"table": "capacity_licenses",
                            "row": "Backup",
                            "quantity": 0, "base": 1},
            "CV-BR-OI": {"table": "complete_oi_licenses", "row": "Operating Instances", "quantity":
                         0, "base": 1},
            "BC-BR-VOI": {"table": "complete_oi_licenses", "row": "Virtual Operating Instances", "quantity":
                          0, "base": 1},
            "CV-BR-VM10-VOI": {"table": "complete_oi_licenses", "row": "Virtual Operating Instances", "quantity":
                               0, "base": 10},

            "CV-BKRC-VM10-VOI": {"table": "complete_oi_licenses", "row": "Virtual Operating Instances", "quantity":
                                 0, "base": 10},
            "MTL-MCSS-A1-TB": {"table": "metallic_licenses", "row": "Metallic Storage Service", "quantity":
                               0, "base": 1},
            "CV-ACT-ED-FT": {"table": "activate_licenses", "row": "Activate E-Discovery For Files",
                             "quantity": 0, "base": 1},
            "CV-ACT-ED-MB": {"table": "activate_licenses",
                             "row": "Activate E-Discovery For Email/Cloud Apps",
                             "quantity": 0, "base": 1},
            "CV-ACT-SD-FT": {"table": "activate_licenses", "row": "Activate Sensitive Data For Files",
                             "quantity": 0, "base": 1},
            "CV-ACT-SD-MB": {"table": "activate_licenses",
                             "row": "Activate Sensitive Data For Email/Cloud Apps",
                             "quantity": 0, "base": 1}

        }

        if self._license_sku_eval is not None or self._license_sku_perm is not None:
            self.get_license_individual_details()
            skus = self.enter_quantity(map_lic)
            for sku in skus:
                table_name, row_name, quantity = map_lic[sku]['table'], map_lic[sku]['row'], map_lic[sku]['quantity']
                try:
                    if table_name == "capacity_licenses":
                        self.__validate_capacity_license(
                            self.lic_individual_details[table_name], sku, row_name, quantity)
                    elif table_name == "complete_oi_licenses":
                        self.__validate_complete_oi_license(
                            self.lic_individual_details[table_name], sku, row_name, quantity)
                    elif table_name == "metallic_licenses":
                        self.__validate_metallic_license(
                            self.lic_individual_details[table_name], sku, row_name, quantity)
                    elif table_name == "activate_licenses":
                        self.__validate_activate_license(
                            self.lic_individual_details[table_name], sku, row_name, quantity)
                    else:
                        raise Exception("invalid table data to validate")
                except Exception as err:
                    raise err

    def __validate_capacity_license(self, capacity_license_detail, sku, row_name, quantity):
        '''
        Check the quantity of capacity license details is correct

        Args:
                capacity_license_detail     (List)  --  List of row in capacity table

                sku   (str)  -- Sku number need to verify

                quantity   (int)  --  Number of quantities applied

        Returns:
            None

        '''
        try:
            for row in capacity_license_detail:
                if row_name in row:
                    available_cap = row[3]
                    if available_cap == quantity:
                        self.log.info("%s is with successfully applied with quantity %d" % (sku, quantity))
                        return
                    else:
                        raise Exception(
                            """Invalid available total detected on commserver. license quantity {%d},
                             Available total capacity{%d}""" % (quantity, available_cap))
            raise Exception(f"""Cannot find the corresponding row of sku {sku}
         in capacity license detail {capacity_license_detail}""")
        except Exception as err:
            raise Exception("Exception raised when validate capacity license details %s" % err)

    def __validate_complete_oi_license(self, complete_oi_license_detial, sku, row_name, quantity):
        '''
        Check the quantity of complete oi license details is correct

        Args:
                complete_oi_license_detial     (List)  --  List of row in complete oi table

                sku   (str)  -- Sku number need to verify

                quantity   (int)  --  Number of quantities applied

        Returns:
            None

        '''
        try:
            for row in complete_oi_license_detial:
                if row_name in row:
                    available_cap = row[4]
                    if available_cap == quantity:
                        self.log.info("%s is with successfully applied with quantity %d" % (sku, quantity))
                        return
                    else:
                        raise Exception(
                            """Invalid available total detected on commserver. license quantity {%d},
                             Available total capacity{%d}""" % (quantity, available_cap))
            raise Exception("Cannot find the corresponding row of sku %s in complete oi license detail" % sku)
        except Exception as err:
            raise Exception("Exception raised when validate complete oi license details %s" % err)

    def __validate_activate_license(self, activate_license_detial, sku, row_name, quantity):
        '''
        Check the quantity of activate license details is correct

        Args:
                activate_license_detial     (List)  --  List of row in activate table

                sku   (str)  -- Sku number need to verify

                quantity   (int)  --  Number of quantities applied

        Returns:
            None

        '''
        try:
            for row in activate_license_detial:
                if row_name in row:
                    available_cap = row[4]
                    if available_cap == quantity:
                        self.log.info("%s is with successfully applied with quantity %d" % (sku, quantity))
                        return
                    else:
                        raise Exception(
                            """Invalid available total detected on commserver. license quantity {%d},
                             Available total capacity{%d}""" % (quantity, available_cap))
            raise Exception("Cannot find the corresponding row of sku %s in activate license detail" % sku)
        except Exception as err:
            raise Exception("Exception raised when validate activate license details %s" % err)

    def __validate_metallic_license(self, metallic_license_detial, sku, row_name, quantity):
        '''
        Check the quantity of metallic license details is correct

        Args:
                metallic_license_detial     (List)  --  List of row in metallic table

                sku   (str)  -- Sku number need to verify

                quantity   (int)  --  Number of quantities applied

        Returns:
            None

        '''
        try:
            for row in metallic_license_detial:
                if row_name in row:
                    available_cap = row[4]
                    if available_cap == quantity:
                        self.log.info("%s is with successfully applied with quantity %d" % (sku, quantity))
                        return
                    else:
                        raise Exception(
                            """Invalid available total detected on commserver. license quantity {%d},
                             Available total capacity{%d}""" % (quantity, available_cap))
            raise Exception("Cannot find the corresponding row of sku %s in metallic license detail" % sku)
        except Exception as err:
            raise Exception("Exception raised when validate metallic license details %s" % err)

    def change_time_date(self, csname, username, password, csclient, daystoadd=91):
        """
        Change commserver date and time and restart services
        Args:
                csname     (str)  --  commserver name

                username   (str)  -- Commserver machine user name

                password   (str)  --  Commserver machine password

            Returns:
                None
        """
        try:
            cshost = Machine(csname, None, username=username, password=password)
            cshost.add_days_to_system_time(daystoadd)
            time.sleep(1)
            count = 0
            while count <= 2:
                try:
                    cshost.start_all_cv_services()
                    time.sleep(2)
                    if csclient.is_ready:
                        break
                except Exception as err:
                    count += 1
                    self.log.info("exception raised while restarting services %s" % err)
                    if count >= 2:
                        raise Exception("exception raised while restarting services %s" % err)

            self.commcell.refresh()
        except Exception as err:
            self.log.error("Exception raised in change date and time function %s" % err)
            raise Exception("Exception raised in change date and time function %s" % err)

    def license_calendar_date_picker(self, date):
        """
        Picks date from the date picker calendar

        Args:
            date   (dict):        the time to be set as range during the browse

                Sample dict:    {   'year':     2017,
                                    'month':    October,
                                    'date':     31,
                                }
        """
        try:

            datepicker = self.driver.find_element(By.ID, 'ui-datepicker-div')

            target_month_year_string = str(date['month']) + " " + str(date['year'])
            target_year = str(date['year'])
            target_month = str(date['month'])
            target_date = str(date['date'])

            elem_selected_year = datepicker.find_element(By.CLASS_NAME, "ui-datepicker-year")
            selected_year_string = elem_selected_year.get_attribute("innerHTML")

            elem_selected_month = datepicker.find_element(By.CLASS_NAME, "ui-datepicker-month")
            selected_month_string = elem_selected_month.get_attribute("innerHTML")

            selected_month_year_string = selected_month_string + " " + selected_year_string

            previous_button_xpath = "./div/a[1]"
            next_button_xpath = "./div/a[2]"

            while selected_month_year_string != target_month_year_string:
                selected_month_number = datetime.strptime(selected_month_string, "%B").month
                target_month_number = datetime.strptime(target_month, "%B").month
                if (((int(selected_year_string)) < int(target_year))) or selected_month_number < target_month_number:
                    # Click the next button
                    next_click = datepicker.find_element(By.XPATH, next_button_xpath)
                    next_click.click()
                else:
                    previous_click = datepicker.find_element(By.XPATH, previous_button_xpath)
                    previous_click.click()

                elem_selected_year = datepicker.find_element(By.CLASS_NAME, "ui-datepicker-year")
                selected_year_string = elem_selected_year.get_attribute("innerHTML")

                elem_selected_month = datepicker.find_element(By.CLASS_NAME, "ui-datepicker-month")
                selected_month_string = elem_selected_month.get_attribute("innerHTML")

                selected_month_year_string = selected_month_string + " " + selected_year_string

            elem_date = self.driver.find_element(By.XPATH, 
                "//td[not(contains(@class,'ui-datepicker-other-month'))]/a[text()='" + target_date + "']")
            elem_date.click()

            time.sleep(5)

        except Exception as err:
            raise Exception("Exception raised when selecting date from calendar %s" % err)

    def validate_warning_popup(self):
        '''Validate the expiry date on warning windows is correct'''
        try:
            if self.adminconsole.check_if_entity_exists("id", 'customStartupMessage_button_#3974'):
                if self.license_type == list(self.license_types.keys())[2]:
                    raise Exception(
                        "Application exception, no warning should appear when permanent license type applied")

                text = self.driver.find_element(By.XPATH, "//div[@class='form-group ']/div").get_attribute('innerHTML')
                self.log.info("Warning message %s" % text)
                pattern = "(January|February|March|April|May|June|July|August|September|October|November|December)\\s([123456789]|[12][0-9]|3[01])(th|rd|nd|st)\\s(20[0-9][0-9])"
                expression = re.compile(pattern)
                matches = expression.findall(text)
                month = matches[0][0]
                day = int(matches[0][1])
                year = matches[0][3]
                #self.evaluation_date = datetime.today() + timedelta(int(evaluation_days))
                if self.license_type == list(self.license_types.keys())[3]:
                    expiry_date = datetime.today() + timedelta(int(self.expiry_date))  # self.expiry_date
                    expiry_date = expiry_date.strftime("%B %d %Y").split(" ")
                    expiry_month = expiry_date[0]
                    expiry_day = int(expiry_date[1]) - 1
                    expiry_year = expiry_date[2]
                elif self.license_type == list(self.license_types.keys())[0]:
                    expiry_date = datetime.today() + timedelta(int(self.evaluation_days))  # self.evaluation_date
                    expiry_date = expiry_date.strftime("%B %d %Y").split(" ")
                    expiry_month = expiry_date[0]
                    expiry_day = int(expiry_date[1])
                    expiry_year = expiry_date[2]
                else:
                    raise Exception("The license type %s does not included in this check function" % self.license_type)

                if month == expiry_month and day == expiry_day and year == expiry_year:
                    self.log.info("The expiry date is successfully validated")
                    self.adminconsole.close_popup()
                else:
                    raise Exception("Invalid expiry date")
            elif self.license_type == list(self.license_types.keys())[2]:
                self.log.info("No warning popup detected, successfully validate for ")
            elif self.license_type == list(self.license_types.keys())[3]:
                raise Exception(
                    "No warning window opened for %s license, Please check the expiry date" %
                    self.license_type)
            else:
                raise Exception("The license type %s does not included in this check function" % self.license_type)

        except Exception as err:
            raise Exception("Exception raised when validating expiry date %s" % err)
