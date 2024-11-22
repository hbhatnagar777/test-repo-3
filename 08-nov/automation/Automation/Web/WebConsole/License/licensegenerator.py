from selenium.webdriver.common.by import By
# -**- coding: utf-8 -**-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Module has all the features which are present in License Generator page.

LicenseGenerator:

    access_category              --  Access category link present on download center

    access_manage_information    --  Access manage insformation

    access_sub_Category          --  Access sub category

    download_package             --  Download specified packages

    get_package_list             --  Get packages list

    is_subcategory_exists        --  check if specified subcategory exists

    search_package_keyword       --  Search for package keyword in search bar

"""
from datetime import datetime, timedelta
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from selenium.webdriver.support import expected_conditions as EC
from Web.API import webconsole
from Web.Common.page_object import (
    WebAction,
    PageService
)



class LicenseGenerator:
    """Class for generating License"""

    def __init__(self, webconsole):
        """
        License generator class for license create / update and apply on commserver

        Args:
            webconsole (WebConsole): The webconsole object to use
        """
        
        
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver
        #delete license
        self.deletelictag = '//a[contains(@href,"deletelicense.jsp")]'
        #create license
        self.createlictag = '//a[contains(@href,"newbundles.jsp")]'
        #modify license
        self.modifylictag = '//a[contains(@href,"modifybundles.jsp")]'
    
    
        
    @WebAction()
    def __click_delete(self):
        """Open delete license from License generator page"""
        link = self._driver.find_element(By.XPATH, self.deletelictag)
        link.click()
    
    @PageService()
    def goto_delete_license(self):
        """Open delete license from License generator page"""
        self.__click_delete()
        self._webconsole.wait_till_load_complete()
    
    @WebAction()
    def __click_create(self):
        """Open create license from License generator page"""
        link = self._driver.find_element(By.XPATH, self.createlictag)
        link.click()
    
    @PageService()
    def goto_create_license(self):
        """Open create license from License generator page"""
        self.__click_create()
        self._webconsole.wait_till_load_complete()
    
    @WebAction()
    def __click_modify(self):
        """Open modify license from License generator page"""
        link = self._driver.find_element(By.XPATH, self.modifylictag)
        link.click()
    
    @PageService()
    def goto_modify_license(self):
        """Open modify license from License generator page"""
        self.__click_modify()
        self._webconsole.wait_till_load_complete()

    

class DeleteLicense(object):
    """
    class to delete the license
    
    """
    def __init__(self, webconsole):
        """
        Delete license class for deleting license

        Args:
            webconsole (WebConsole): The webconsole object to use
        """
        self._webconsole = webconsole
        self._driver = webconsole.browser.driver
        self._commcell_id_tag = "txtRegCode"
        self._delete_button = "deleteRegCode"
        self._yes_no_btn = "yesBtn"
        
    @PageService()
    def delete_license(self, regcode):
        """
        function to delete license
        """                  
        self.__perform_delete(regcode)
        self._webconsole.wait_till_load_complete()
        
    @WebAction()
    def __perform_delete(self,regcode):
        """function to perform delete operation"""
        commcell_id_box = self._driver.find_element(By.ID, self._commcell_id_tag)
        commcell_id_box.send_keys(str(regcode).strip())
        delete_btn = self._driver.find_element(By.ID, self._delete_button)
        delete_btn.click()
        self._webconsole.wait_till_load_complete()
        yes_no__btn = self._driver.find_element(By.ID, self._yes_no_btn)
        yes_no__btn.click()

class CreateLicense(object):
    """
    Class to create license from license generator website
    """
    
    def __init__(self, webconsole, adminconsole, lic_response, license_types):
        """
        init function for creating license
        
        """
        self._webconsole = webconsole
        self._adminconsole = adminconsole
        self._driver = webconsole.browser.driver
        self._lic_response = lic_response
        self._license_types = license_types
        self._license_sku_perm = None
        self._license_sku_eval = None
        self._license_sku_quantity_perm = None
        self._license_sku_quantity_eval = None
        
        self._serial_tag = "//input[@id='SerialNoCust']"
        self._regcode_tag = "//input[@id='RegCodeCust']"
        self._license_type_tag = "ddlLicenseType"
        self._checkout_tag = "showCartBtnCustUp"
        self._generatebtn_tag = "cartLicGenerateBtnCust"
        self._revert_tag = "revertUp"
        
    @PageService()
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
        
        if license_sku_perm:
            self._license_sku_perm = license_sku_perm.split(',')
            self._license_sku_quantity_perm = int(license_sku_quantity_perm) 
        if license_sku_eval:  
            self._license_sku_eval = license_sku_eval.split(',')
            self._license_sku_quantity_eval = int(license_sku_quantity_eval)
            
        serialtag = self._driver.find_element(By.XPATH, self._serial_tag)
        serialtag.send_keys(str(self._lic_response['serial_number']).strip())
        regcode = self._driver.find_element(By.XPATH, self._regcode_tag)
        regcode.send_keys(self._lic_response['registration_code'])
        self._adminconsole.select_value_from_dropdown(self._license_type_tag, licensetype)
        self._webconsole.wait_till_load_complete()
        
        component = Components(self._webconsole, self._adminconsole)
        ''' enter the perm skus and eval skus'''
        if self._license_sku_perm is not None:
            if licensetype == list(self._license_types.keys())[0]:
                component._enter_sku(self._license_sku_perm, False, self._license_sku_quantity_perm, self._license_sku_quantity_eval)
            else:
                component._enter_sku(self._license_sku_perm, True, self._license_sku_quantity_perm, self._license_sku_quantity_eval)
        if self._license_sku_eval is not None:
            component._enter_sku(self._license_sku_eval, False, self._license_sku_quantity_perm, self._license_sku_quantity_eval)
        if self._license_sku_perm is None and self._license_sku_eval is None:
            '''if no sku provided,  select default bundle'''
            txt_box = self._driver.find_element(By.ID, self._revert_tag)
            txt_box.click()
            self._webconsole.wait_till_load_complete()
            if licensetype == list(
                    self._license_types.keys())[0] or licensetype == list(
                    self._license_types.keys())[1]:
                component._enter_termend_date(sku_expiration=sku_expiration)

        if licensetype == list(
                self._license_types.keys())[0] or licensetype == list(
                self._license_types.keys())[1] or licensetype == list(
                self._license_types.keys())[4]:
            component._enter_evaluation_days(license_evaluation_days)
        elif licensetype == list(self._license_types.keys())[3]:
            component._enter_expiration_date(license_expiration_days)

        time.sleep(5)
        if self._license_sku_eval is not None:
            for sku_number in self._license_sku_eval:
                component._enter_termend_date(sku_number, sku_expiration)

        checkout_button = self._driver.find_element(By.ID, self._checkout_tag)
        checkout_button.click()
        self._webconsole.wait_till_load_complete()
        generate_btn = self._driver.find_element(By.ID, self._generatebtn_tag)
        generate_btn.click()
        self._webconsole.wait_till_load_complete()
        
class ModifyLicense(object):
    """
    Class to create license from license generator website
    """
    
    def __init__(self, webconsole, adminconsole, lic_response, license_types):
        """
        init function for creating license
        
        """
        self._webconsole = webconsole
        self._adminconsole = adminconsole
        self._driver = webconsole.browser.driver
        self._lic_response = lic_response
        self._license_types = license_types
        self._license_sku_perm = None
        self._license_sku_eval = None
        self._license_sku_quantity_perm = None
        self._license_sku_quantity_eval = None
        
        self._commcell_regcode = "//*[@id='txtCsId']"
        self._go_btn = "goBtn"
        self._license_type_tag = "ddlLicenseType"
        self._custom_license_tag = 'customLicenseTableSku'
        self._custom_body_tag = 'custtblbodySku'
        self._sku_remove_tag = 'skuRemove'
        self._pno_title = 'pNosTitle'
        self._cust_tbltag = 'custtblbody'
        self._pno_rem_tag = 'pnoRemove'
        self._revert_tag = "revertUp"
        self._checkout_tag = "showCartBtnCustUp"
        self._generatebtn_tag = "cartLicGenerateBtnCust"
        
    @PageService()
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
        
        
        if license_sku_perm:
            self._license_sku_perm = license_sku_perm.split(',')
            self._license_sku_quantity_perm = int(license_sku_quantity_perm) 
        if license_sku_eval:  
            self._license_sku_eval = license_sku_eval.split(',')
            self._license_sku_quantity_eval = int(license_sku_quantity_eval)
        
        commcell_id_box = self._driver.find_element(By.XPATH, self._commcell_regcode)
        count = 0 
        while 'disable' in self._driver.find_element(By.ID, "custLicDiv").get_attribute('class') and count <=3:
            self._driver.find_element(By.ID, self._go_btn).click()
            commcell_id_box.send_keys(str(self._lic_response['registration_code']).strip())
            self._webconsole.wait_till_load_complete()
            self._driver.find_element(By.ID, self._go_btn).click()
            count +=1
        self._webconsole.wait_till_load_complete()
        self._adminconsole.select_value_from_dropdown(self._license_type_tag, licensetype)
        self._webconsole.wait_till_load_complete()
        '''delete all existing sku and part numbers'''
        if self._adminconsole.check_if_entity_exists('id', self._custom_license_tag):
            rowcount = len(self._driver.find_elements(By.ID, self._custom_body_tag))
            for _ in range(0, rowcount):
                self._driver.find_element(By.ID, self._sku_remove_tag).click()
                self._webconsole.wait_till_load_complete()
        if self._adminconsole.check_if_entity_exists('id', self._pno_title):
            rowcount = len(self._driver.find_elements(By.ID, self._cust_tbltag))
            for _ in range(0, rowcount):
                self._driver.find_element(By.ID, self._pno_rem_tag).click()
                self._webconsole.wait_till_load_complete()
                
        component = Components(self._webconsole, self._adminconsole)
        ''' enter the perm skus and eval skus'''
        if self._license_sku_perm is not None:
            component._enter_sku(self._license_sku_perm, True, self._license_sku_quantity_perm, self._license_sku_quantity_eval)
        if self._license_sku_eval is not None:
            component._enter_sku(self._license_sku_eval, False, self._license_sku_quantity_perm, self._license_sku_quantity_eval)
        if self._license_sku_perm is None and self._license_sku_eval is None:
            '''if no sku provided,  select default bundle'''
            txt_box = self._driver.find_element(By.ID, self._revert_tag)
            txt_box.click()
            self._webconsole.wait_till_load_complete()
            if licensetype == list(
                    self._license_types.keys())[0] or licensetype == list(
                    self._license_types.keys())[1]:
                component._enter_termend_date(sku_expiration=sku_expiration)

        if licensetype == list(
                self._license_types.keys())[0] or licensetype == list(
                self._license_types.keys())[1] or licensetype == list(
                self._license_types.keys())[4]:
            component._enter_evaluation_days(license_evaluation_days)
        elif licensetype == list(self._license_types.keys())[3]:
            component._enter_expiration_date(license_expiration_days)

        time.sleep(5)
        if self._license_sku_eval is not None:
            for sku_number in self._license_sku_eval:
                component._enter_termend_date(sku_number, sku_expiration)

        chk_box = self._driver.find_element(By.ID, self._checkout_tag)
        WebDriverWait(self._driver, 20).until(EC.element_to_be_clickable((By.ID, self._checkout_tag)))
        time.sleep(5)
        chk_box.click()
        self._webconsole.wait_till_load_complete()
        chk_box = self._driver.find_element(By.ID, self._generatebtn_tag)
        chk_box.click()
        self._webconsole.wait_till_load_complete()
        time.sleep(10)

class Components(object):
    """
    components class to perform operations on web elements for License page
    """
    
    def __init__(self, webconsole, adminconsole):
        """
        
        """
        self._webconsole = webconsole
        self._adminconsole = adminconsole
        self._driver = webconsole.browser.driver
        self._sku_search_field_tag = "//*[@id='searchBox']"
        self._sku_search_btn_tag = "searchBtn"
        self._sku__close_search_tag = "//*[@id='closeSearch']"
        self.evaluation_date = None
        self.expiry_date = None
    
    @WebAction()    
    def _enter_sku(self, sku_numbers, permanent=True, license_sku_quantity_perm=10, license_sku_quantity_eval=10):
        '''
        Enter all sku numbers applied for license
        args:
            sku_numbers (str): provide number of skus
            permanent (boolen) : True if permanent license
         
        '''
        
        search_box = self._driver.find_element(By.XPATH, self._sku_search_field_tag)
        for sku_number in sku_numbers:
            # if the search box is not empty
            if search_box.get_attribute("value") != "":
                search_box.clear()
                self._webconsole.wait_till_load_complete()
            search_box.send_keys(str(sku_number).strip())
            search_btn = self._driver.find_element(By.ID, self._sku_search_btn_tag)
            search_btn.click()
            self._webconsole.wait_till_load_complete()
            sku_textbox, add_btn = self._find_sku_row(sku_number, permanent)
            if sku_textbox is not None and add_btn is not None:
                if permanent:
                    self._driver.execute_script("arguments[0].setAttribute(arguments[1], arguments[2]);",
                                               sku_textbox,
                                               "value",
                                               "{}".format(license_sku_quantity_perm))
                else:
                    self._driver.execute_script("arguments[0].setAttribute(arguments[1], arguments[2]);",
                                               sku_textbox,
                                               "value",
                                               "{}".format(license_sku_quantity_eval))
                self._webconsole.wait_till_load_complete()
                add_btn.click()
                self._webconsole.wait_till_load_complete()
                '''close the search box each time otherwise will be interrupted'''
                self._driver.find_element(By.XPATH, self._sku__close_search_tag).click()
                self._webconsole.wait_till_load_complete()
    
    @WebAction()
    def _find_sku_row(self, sku_number=None, permanent=True):
        """
        input: this function will take single sku number as input
        description:
        This function is to find the text input box with corresponding sku number and return it
        with the add button. Otherwise, the function will return None
        args:
            sku_numbers (str): provide number of skus
            permanent (boolen) : True if permanent license
        """
        
        if self.__result_found:
            try:
                search_table = self._driver.find_element(By.ID, "searchcusttblbodySku")
                hover_elements = search_table.find_elements(By.CLASS_NAME, "hoverSearch")
                for ele in hover_elements:
                    if ele.find_element(By.XPATH, ".//*[@id='tdSku']/a").get_attribute("innerHTML") == sku_number:
                        if permanent:
                            return ele.find_element(By.ID, "PermSkuSrch"), ele.find_element(By.CLASS_NAME, "addSku")
                        else:
                            return ele.find_element(By.ID, "EvalSkuSrch"), ele.find_element(By.CLASS_NAME, "addSku")
            except Exception as err:
                search_table = self._driver.find_element(By.ID, "searchcusttblbody")
                hover_elements = search_table.find_elements(By.CLASS_NAME, "hoverSearch")
                for ele in hover_elements:
                    if ele.find_element(By.XPATH, 
                            ".//*[@id='tdPartNo']/a").get_attribute("innerHTML") == sku_number:
                        if permanent:
                            return ele.find_element(By.ID, 
                                "PermPNosSrch"), ele.find_element(By.CLASS_NAME, "addPartNo")
                        else:
                            return ele.find_element(By.ID, 
                                "EvalPNosSrch"), ele.find_element(By.CLASS_NAME, "addPartNo")
    
        else:
            raise Exception("No sku number %s matched" % sku_number)
        
    @WebAction()
    def _enter_evaluation_days(self, evaluation_days=None):
        '''Pick the evaluation date for New License Type
        args:
            evaluation_days (str) : provide evaluation days
        
        '''
        if evaluation_days is not None and evaluation_days != "":
            self.evaluation_date = datetime.today() + timedelta(int(evaluation_days))
            self._driver.find_element(By.ID, 'divLicInfo').click()
            self._webconsole.wait_till_load_complete()
            self._adminconsole.select_value_from_dropdown("ddlEvalDays", str(evaluation_days))
            self._webconsole.wait_till_load_complete()
        else:
            raise Exception("evaluation days cannot be None or Empty")
    
    @WebAction()
    def __result_found(self):
        '''
        if there is no sku records found return false,otherwise return true
        '''
        # if there is no result found
        self._driver.find_element(By.ID, "divNoResult")
        return False
    
    @WebAction()
    def _enter_expiration_date(self, expiration_day=None):
        '''Select the expiration date of Pure Subscription/Permanent with Expiry type
        args:
            expiration_day (str): provide expiration days
        '''
       
        if expiration_day is not None and expiration_day != "":
            self.expiry_date = datetime.today() + timedelta(int(expiration_day))
            self._driver.find_element(By.ID, 'divLicInfo').click()
            self._webconsole.wait_till_load_complete()
            self._driver.find_element(By.ID, 'txtExpDate').click()
            self._webconsole.wait_till_load_complete()
            expiration_date = datetime.now() + timedelta(days=int(expiration_day))
            time_value = {
                'year': expiration_date.year,
                'month': expiration_date.strftime("%B"),
                'date': expiration_date.day}
            self._license_calendar_date_picker(time_value)
            self._webconsole.wait_till_load_complete()
        else:
            raise Exception("The expiration day cannot be None or Empty")
        
    
        
    @WebAction()
    def _license_calendar_date_picker(self, date):
        """
        Picks date from the date picker calendar

        Args:
            date   (dict):        the time to be set as range during the browse

                Sample dict:    {   'year':     2017,
                                    'month':    October,
                                    'date':     31,
                                }
        """
        datepicker = self._driver.find_element(By.ID, 'ui-datepicker-div')

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

        elem_date = self._driver.find_element(By.XPATH, 
            "//td[not(contains(@class,'ui-datepicker-other-month'))]/a[text()='" + target_date + "']")
        elem_date.click()

        time.sleep(5)
        
    def _enter_termend_date(self, sku="P_CV_11.0.0", sku_expiration=None):
        '''Select the term end date for sku number using date picker'''
       
        if sku_expiration is not None and sku_expiration != "":
            if self._adminconsole.check_if_entity_exists('id', 'skuTitle'):
                if self._adminconsole.check_if_entity_exists(
                        'xpath', "//table[@id='customLicenseTableSku']/tbody/tr/td[1]/a[text()='{}']".format(sku)):
                    calender_ele = self._driver.find_element(By.XPATH, 
                        "//table[@id='customLicenseTableSku']/tbody/tr/td[1]/a[text()='{}']".format(sku))
                    calender_ele.find_element(By.XPATH, "./../../td[4]/input").click()
                    self._webconsole.wait_till_load_complete()
                    expiration_date = datetime.now() + timedelta(days=int(sku_expiration))
                    time_value = {
                        'year': expiration_date.year,
                        'month': expiration_date.strftime("%B"),
                        'date': expiration_date.day}
                    self._license_calendar_date_picker(time_value)

            elif self._adminconsole.check_if_entity_exists('id', 'pNosTitle'):
                if self._adminconsole.check_if_entity_exists(
                        'xpath', "//*[@id='pNoCust']/a[text()='{}']".format(sku)):
                    calender_ele = self._driver.find_element(By.XPATH, 
                        "//*[@id='pNoCust']/a[text()='{}']".format(sku))
                    calender_ele.find_element(By.XPATH, "./../../td[4]/input").click()
                    self._webconsole.wait_till_load_complete()
                    expiration_date = datetime.now() + timedelta(days=int(sku_expiration))
                    time_value = {
                        'year': expiration_date.year,
                        'month': expiration_date.strftime("%B"),
                        'date': expiration_date.day}
                    self._license_calendar_date_picker(time_value)
            else:
                raise Exception("Cannot find the sku %s row in Bundles" % sku)

        else:
            raise Exception("sk_expiration input type %s is not valid" % type(sku_expiration))
    