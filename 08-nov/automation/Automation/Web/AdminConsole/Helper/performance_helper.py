from selenium.webdriver.common.by import By
"""
This file provides functions used for performance test case of admin console

Class:
    PerformanceHelper

Functions:
    __init__()  -------------------------------------------- initalises the class object
    set_registry_keys() ------------------------------------ verifies if the registry keys "debugModeUsers" and
                                                             "cacheDbLocation" exist and set to the
                                                             corresponding values.
    copy_navigation_folder()    ---------------------------- copies the "navigation" folder from the client machine to
                                                             local machine where the test case will be run.
                                                             also creates a folder in controller machine for output.
    get_page_load_time()    -------------------------------- get page load time of the page based on {state, label}
                                                             or url                                                         
    set_dict_list() ---------------------------------------- set the list containing ditcionaries having values of
                                                              state, label and url, used for navigating to the
                                                              respective page.
    get_dict_list() ---------------------------------------- returns the above list   
    nav_folder_url_list()   -------------------------------- creates the list having dictionaries containing state,
                                                             label and url values from each json file of the
                                                             navigation folder.
    get_dict()  -------------------------------------------- when a dictionary from the json files of the navigation
                                                             folder is passed, it extracts state label and url into a
                                                             dictionary and updates the dict_list
    get_load_time_by_label()    ---------------------------- get page load time of the page based on {state, label}
    get_load_time_by_page_name()    ------------------------ get page load time of the page given its name
    get_load_time_by_url()    ------------------------------ get page load time of the page given its url
    record_load_time()    ---------------------------------- records the APIs found in nwLogger page and stores load
                                                             time in associated lists and dictionaries
    calc_load_time()  -------------------------------------- calculate the load time when the input values are
                                                             state and label, which has to be found in dict_list    
    send_result_as_mail()   -------------------------------- mail the result of load time of the pages in a table format

"""

import json
import os
import time
from datetime import datetime
import pandas as pd


from AutomationUtils.anomalies.webserver_anomaly import WebserverAnomaly
from AutomationUtils.mailer import Mailer
from AutomationUtils import constants
from AutomationUtils import logger
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from AutomationUtils.machine import Machine


class PerformanceHelper:
    """
        Class for the helper file
    """

    def __init__(self, commcell_obj, admin_console, driver):

        """
        __init__ function of PerformanceHelper class

        :param commcell_obj: commcell object of remote CS machine
        :param admin_console: logged in admin console object
        :param driver: driver object
        """

        self.remote_mac_obj = Machine(commcell_object=commcell_obj)
        self.commcell_obj = commcell_obj
        self.log = logger.get_log()
        self.dict_list = None
        self.base_path = None
        self.webserv_obj = None
        self.controller_mac_obj = Machine()
        self.des_path = None
        self.driver = driver
        self.time_taken_dict = None
        self.saved_network_logs = None
        self.adminconsole_page = None
        self.admin_console = admin_console
        self.nlogger_page = None
        self.file_path = None
        self.path1 = None
        self.mailer = None
        self.path = None

    def set_registry_keys(self):
        """
        function to set registry keys in the remote CS machine

        :return: None
        """

        count = 0
        self.base_path = self.remote_mac_obj.get_registry_value("Base", "dGALAXYHOME")
        cache_path = os.path.join(self.base_path, 'cachelocation', 'cache')
        self.webserv_obj = WebserverAnomaly(commcell_obj=self.commcell_obj,
                                            client_name=self.commcell_obj.webconsole_hostname)
        if not self.remote_mac_obj.check_registry_exists(
                "cacheDbLocation", cache_path):
            self.remote_mac_obj.create_registry(
                key="cacheDbLocation", value=cache_path)
            count += 1
        if not self.remote_mac_obj.check_registry_exists(
                "debugModeUsers", "Admin"):
            self.remote_mac_obj.create_registry(
                key="debugModeUsers", value="Admin")
            count += 1
        if count > 0:
            try:
                self.webserv_obj.stop_tomcat()
                self.webserv_obj.start_tomcat()
            except Exception as exp:
                self.log.info(exp)

    def copy_navigation_folder(self, rm_uname, rm_pwd):
        """
        copies navigation folder from remote CS machine to controller machine

        :param rm_uname: remote CS machine username
        :param rm_pwd: remote CS machine password
        :return: None
        """

        install_path = constants.INSTALL_DIRECTORY
        now = datetime.now()
        time_stamp = now.strftime("%Y%m%d%H%M%S")
        folder_name = "performanceTestOutput_" + time_stamp
        path = os.path.join(install_path, folder_name)
        os.mkdir(path)
        self.des_path = path

        try:
            full_network_path = self.controller_mac_obj.get_unc_path(self.des_path)
            self.controller_mac_obj.share_directory(share_name="share_output", directory=full_network_path)
        except Exception as exp:
            self.log.info(exp)

        total_path = self.remote_mac_obj.join_path(self.base_path, 'AdminConsole', 'res', 'navigation')
        network_path = self.remote_mac_obj.get_unc_path(total_path)
        self.controller_mac_obj.copy_from_network_share(network_path=network_path, destination_path=self.des_path,
                                                        username=rm_uname, password=rm_pwd)

    def get_ac_performance(self, rm_uname, rm_pwd, email_receiver):
        """
        copies navigation folder from remote CS machine to controller machine

        :param rm_uname: remote CS machine username
        :param rm_pwd: remote CS machine password
        :param email_receiver: email receiver to send the ouput mail
        :return: None
        """

        self.set_registry_keys()

        self.copy_navigation_folder(rm_uname, rm_pwd)

        self.time_taken_dict = {}
        self.saved_network_logs = {}
        self.adminconsole_page = self.driver.window_handles[0]
        url = r'https://' + self.commcell_obj.webconsole_hostname + r'/adminconsole/nwLogger.do'
        self.admin_console.browser.open_url_in_new_tab(url)
        self.nlogger_page = self.driver.window_handles[1]
        self.driver.switch_to.window(self.nlogger_page)
        self.driver.find_element(By.XPATH, '//*[@id="del"]').click()
        test_pop = self.driver.switch_to.alert
        test_pop.accept()
        self.path = self.des_path + r'\AutomationScriptOutput'
        os.mkdir(self.path)

        url_dict_list = self.nav_folder_url_list()

        try:
            for each_dict in url_dict_list:
                label = each_dict['label']
                state = "navigationItem_" + each_dict['state']
                self.get_load_time_by_label(label=label, state=state)

                if 'parent_state' in each_dict.keys():
                    label = each_dict['label']
                    state = "navigationItem_" + each_dict['parent_state']
                    self.get_load_time_by_label(label=label, state=state)

        except NoSuchElementException as exp:
            self.log.info(exp)

        self.send_result_as_mail(email_receiver)

    def set_dict_list(self, input_list):
        """
        sets the values of the dict_list

        :param input_list: the list to be updated as dict_list
        :return: None
        """
        self.dict_list = input_list

    def get_dict_list(self):
        """
        returns list containing dictionaries having key value pairs of label, state and url(and parent_state, if exists)

        :return: dict_list
        """
        return self.dict_list

    def nav_folder_url_list(self):
        """
            iterated through every json file of the navigation folder

            :return: dict_list
        """
        dir_path = self.des_path + r"\navigation"
        file_list = os.listdir(dir_path)

        for file_name in file_list:
            file = os.path.join(dir_path, file_name)

            with open(file) as json_file:
                json_file_dict = json.load(json_file)
                routes_arr = json_file_dict['routes']
                for each_dict in routes_arr:
                    self.get_dict(each_dict)
        dict_list = self.get_dict_list()
        final_list = {'list': dict_list}
        output_path = os.path.join(self.des_path, "url_json_list.json")
        with open(output_path, 'w') as outfile:
            json.dump(final_list, outfile)

        return dict_list

    def get_dict(self, each_dict, parent_state=None):
        """
            get dictionary of url, label, and json form the navigation folder

            :param each_dict: dictionary present in the json file to fetch label, state and url
            :param parent_state: parent_state of the dictionary, if exists
            :return: None
        """
        temp_dict = {}
        res_list = []
        if parent_state is not None:
            temp_dict['parent_state'] = parent_state
        temp_dict['state'] = each_dict['state']
        try:
            temp_dict['label'] = each_dict['cvTitle']
        except KeyError:
            try:
                temp_dict['label'] = each_dict['pageTitle']
            except KeyError:
                temp_dict['label'] = ""
        try:
            temp_dict['url'] = each_dict['url']
            res_list.append(temp_dict)
            existing_list = self.get_dict_list()
            if existing_list is not None:
                res_list = existing_list + res_list
            self.set_dict_list(res_list)
        except KeyError:
            temp_dict['parent'] = True
            res_list.append(temp_dict)
            existing_list = self.get_dict_list()
            if existing_list is not None:
                res_list = existing_list + res_list
            self.set_dict_list(res_list)
            child_list = each_dict['children']
            for each_child_dict in child_list:
                self.get_dict(each_child_dict, temp_dict['state'])

    def get_load_time_by_label(self, label, state):
        """
            gets page load time, given label and state

            :param label: label of the page
            :param state: state of the page 
            :return: None
        """

        self.driver.switch_to.window(self.adminconsole_page)

        try:
            if self.admin_console.check_if_element_exists(self.admin_console.props[label]) and \
                    self.admin_console.check_if_id_exists(nav_id=state):
                self.calc_load_time(label, state)
                self.record_load_time()
        except KeyError as exp:
            self.log.info(exp)

    def get_load_time_by_page_name(self, page_name):
        """
            gets page load time, given its pagename

            :param page_name: name of the page
            :return: None
        """

        label = "label.nav." + page_name
        search_dict = self.nav_folder_url_list()
        for each_dict in search_dict:
            if label in each_dict.values():
                state = "navigationItem_" + each_dict['state']
                self.calc_load_time(label, state)
                self.record_load_time()

    def get_load_time_by_url(self, url):
        """
            gets page load time, given its url

            :param url: url of the page
            :return: None
        """

        try:
            time1 = int(round(time.time()))
            self.driver.get(url)
            time2 = int(round(time.time()))
            time_taken = time2 - time1
            self.time_taken_dict[url] = time_taken
            self.file_path = '{0}.xlsx'.format(url)
            self.path1 = self.remote_mac_obj.join_path(self.path, self.file_path)
            self.saved_network_logs[url] = self.path1
            self.record_load_time()
        except TimeoutException as exp:
            self.log.info(exp)

    def record_load_time(self):
        """
            stores the APIs which loaded upon navigating to the page;
            stores the load time in associated lists and dictionaries;

            :return: None
        """

        self.driver.switch_to.window(self.nlogger_page)
        self.driver.refresh()
        self.admin_console.wait_for_completion()
        rows = self.driver.find_elements(By.XPATH, 
            '//table[@class="table"]/tbody/tr')
        page_list = []
        ui_end_point_list = []
        api_dict_list = []
        time_taken_list = []
        page_dict = {}
        ui_end_point = {}
        api_dict = {}
        time_taken_dict1 = {}
        for row in rows:
            page_list.append(row.find_element(By.XPATH, "./td[1]").text)
            ui_end_point_list.append(row.find_element(By.XPATH, "./td[2]").text)
            api_dict_list.append(row.find_element(By.XPATH, "./td[3]").text)
            time_taken_list.append(row.find_element(By.XPATH, "./td[5]").text)
        page_dict['page'] = page_list
        ui_end_point['uiendpoint'] = ui_end_point_list
        api_dict['api'] = api_dict_list
        time_taken_dict1['time_taken'] = time_taken_list
        page_dict_list = list(page_dict.items())
        ui_end_point1_list = list(ui_end_point.items())
        api_dict_list = list(api_dict.items())
        time_taken_dict1_list = list(time_taken_dict1.items())
        convert_list1 = page_dict_list + ui_end_point1_list + \
            api_dict_list + time_taken_dict1_list
        pd.DataFrame.from_records(convert_list1)
        self.driver.find_element(By.XPATH, '//*[@id="del"]').click()
        test_pop = self.driver.switch_to.alert
        test_pop.accept()

    def calc_load_time(self, label, state):
        """
            calculate the load time when the input values are
            state and label, which has to be found in dict_list 

            :return: None
        """
        try:
            time1 = int(round(time.time()))
            self.admin_console.search_nav_by_id(self.admin_console.props[label], state)
            self.admin_console.wait_for_completion()
            time2 = int(round(time.time()))
            time_taken = time2 - time1
            self.time_taken_dict[state] = time_taken
            self.file_path = '{0}.xlsx'.format(state)
            self.path1 = self.remote_mac_obj.join_path(self.path, self.file_path)
            self.saved_network_logs[state] = self.path1
        except TimeoutException as exp:
            self.log.info(exp)

    def send_result_as_mail(self, email_receiver):
        """
            send the navigation load time details as mail

            :param email_receiver: email receiver to send the ouput mail
            :return: None
        """
        self.mailer = Mailer({'receiver': email_receiver}, self.commcell_obj)
        commcell_obj = self.commcell_obj.webconsole_hostname
        convert_list = list(self.time_taken_dict.items())
        info_message = '''
                        <p>Below is the page load time of all pages in adminconsole</p>
                        <table border="1"><tr><th>PageName</th><th>LoadTime(sec)</th><th>NetworkLogs</th></tr>
                        '''
        for load_time in convert_list:
            info_message += '<tr><td>'
            print(info_message)
            info_message += load_time[0]
            print(info_message)
            info_message += '</td>'
            info_message += '<td>'
            info_message += str(load_time[1])
            info_message += '</td>'
            info_message += '<td>'
            nw_path = self.controller_mac_obj.get_unc_path(self.path)
            info_message += str(r'Share path- ' + nw_path +
                                r'\{0}.xlsx'.format(load_time[0]))
            info_message += '</td>'
            print(info_message)
            info_message += '</tr>'

        info_message += '</table>'

        self.mailer.mail("Pageloadtime details " + commcell_obj, info_message)
