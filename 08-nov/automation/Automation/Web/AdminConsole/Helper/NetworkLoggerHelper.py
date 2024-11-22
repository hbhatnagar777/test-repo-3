from selenium.webdriver.common.by import By
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the methods for performance test via NwLoggerPage

Classes:

NetworkLogger -- Responsible for Navigating to the different pages and calculating the load time for each page

    --Functions:

    __init__()  --  Class initializer

    access_item_in_table -- Access the first item in the react table or angular table

    wait_for_load   --  Waits for complete page load - tables , individual components

    navigate_to_eachtab -- Navigate to the multiple tabs in a table calculate performance of them

    generate_directory  --  Generates the CSV and graphs folder

    create_graphs   --  Generates the graph based on the failures in UI and API load times

    validate_threshold  --  This function captures the pages and APIs crossing threshold limit

    record_load_time    -- Record load time and API times after page load completes

    navigate_to_screens --  Navigate to all the screens through nav methods in adminconsole navigator

    mail_reports   --  Email the API graphs and csvs to the testcase recepients

LoadTimeValuesHelper  -- Responsible for handling SQLITE DB operations

    -- Functions:

    __init__()  --  Class initializer

    get_latest_runid    -- Get the latest run ID from DB

    get_latest_version -- Get the latest version from the DB

    execute_query -- Execute the select query and return all rows

    create_tables -- Create tables to store performance data

    clear_database -- Delete all rows from the tables

NwLoggerPage    --  Responsible for interacting with the NwLogger Page

    --Function :

    __init__()  -- Initializer

    refresh_nwlogger - Refresh the nwlogger page to get the latest api values in the html table

    get_table_values -- Read the values in the html table

AutoMR    --  Responsible for creating MRs automatically

    --Function :

    __init__()  -- Initializer

    wait_for_load   --  Waits for complete page load - tables , individual components
    
    navigate_to_tab -- Navigates to a tab in a page

    access_item_in_table -- Access the first item in the react table or angular table
    
    report_defect -- Method to create one MR from CC 
    
    create_mrs -- Navigates to the faulty pages and call the method to create MR
    
"""
from AutomationUtils.machine import Machine
from Web.Common.page_object import (
    WebAction,
    PageService
)
from AutomationUtils import logger
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, \
    ElementNotVisibleException, ElementNotInteractableException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from Web.AdminConsole.Components.panel import ModalPanel
from inspect import getmembers, isfunction
from Web.Common.page_object import TestStep
from Web.AdminConsole.Components.table import Rtable, Table
from Web.AdminConsole.Components.dialog import RModalDialog
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from AutomationUtils import (constants, config)
import sqlite3
import datetime
import time
import csv
import smtplib
import re
from Server.RestAPI.Locust.graph_analysis import *

TIMESTAMP = str(time.asctime(time.localtime(time.time()))).replace(" ", "_").replace(":", "_")


class NetworkLogger:
    """
        Class for the helper file
    """
    teststep = TestStep()

    def __init__(self, commcell_obj, admin_console, mail_list, browser, tcinputs):

        """
        __init__ function of PerformanceHelper class

        :param commcell_obj: commcell object of remote CS machine
        :param admin_console: logged in admin console object
        :param mail_list: list of email IDs comma separated
        :browser : browser object
        :tcinputs : testcase inputs have to be passed
            Customization inputs:
                includeapidiff - Includes the API added and removed in CSVs
                includecurrentruninfo - Inclues the CSVs which has the current run statistics apart from the average
                                        load time info

        """
        self.commcell_obj = commcell_obj
        self.version = self.commcell_obj.version.split("11.")[-1]
        self.admin_page = admin_console.navigator
        self.admin_console = admin_console
        if not self.admin_console.performance_test:
            raise Exception("PERFORMANCE_TEST config is not enabled")
        self.log = logger.get_log()
        self.ui_only = self.admin_console.nwloggermode
        self.panel = ModalPanel(admin_console)
        self.driver = browser.driver
        self.rtable = Rtable(self.admin_console)
        self.table = Table(self.admin_console)
        self.start_time = datetime.datetime.now()
        self.mail_list = mail_list
        self.mailer = None
        self.nwlogpage = NwLoggerPage(self.driver, browser, admin_console)
        self.fail_data_count = {"API": 0, "UI": 0, "PAGE": 0, "BROWSERPAGE": 0, "BROWSERAPI": 0, 'APICOUNT': 0,
                                "NEWAPI": 0, "NEWBRWSERAPI": 0}
        self.tcinputs = tcinputs
        self.nlogfolder = os.path.join(constants.AUTOMATION_DIRECTORY, 'Server', 'RestAPI', "NetworkLogger")
        url = r'https://' + self.tcinputs.get('webconsoleHostname',
                                              self.commcell_obj.webconsole_hostname) + r'/adminconsole/nwLogger.do'
        self.browser = browser
        if self.admin_console.nwloggermode:
            self.driver.get(url)
            self.browser.open_new_tab()
            self.browser.switch_to_latest_tab()
            self.driver.get(r'https://' + self.tcinputs.get('webconsoleHostname',
                                                            self.commcell_obj.webconsole_hostname) + "/commandcenter")
            self.admin_console.wait_for_completion()
            self.nlogger_handle = self.driver.window_handles[0]
        self.curr_window = self.driver.current_window_handle
        self.nav_list = [api[0] for api in getmembers(self.admin_console.navigator) if
                         api[0].startswith("navigate_to")]
        self.__generate_directory()
        self.db_name = self.tcinputs.get("db_name", "NETWORK_LOGGER.db")
        self.db_helper = LoadTimeValuesHelper(self.db_name)
        self.db_helper.create_tables()
        self.db_connection = self.db_helper.db_connection
        if self.tcinputs.get("capture_only"):
            self.db_helper.clear_database()
        self.db_helper.execute_query(f"""INSERT INTO RUNINFO (RUNDATE,VERSION,HOSTNAME) VALUES ('{self.start_time}'
        ,'{str(self.version)}','{self.commcell_obj.webconsole_hostname}')""")
        self.run_id = self.db_helper.get_latest_runid()[0]  # CURRENT RUN ID
        self.fail_data_count = {"API": 0, "UI": 0, "BROWSERPAGE": 0, "BROWSERAPI": 0, 'APICOUNT': 0, "NEWAPI": 0,
                                "NEWNWLOGAPI": 0, "BROWSERAPIREMOVED": 0}
        self.page_load_time_threshold = self.tcinputs.get("uitimethreshold", 25)
        self.api_responsetime_threshold = self.tcinputs.get("apitimethreshold", 10000)
        self.table_data = None
        self.details_page_visited = True
        self.apirows = []
        self.email_msg = None

    @PageService()
    def close_panel(self):
        """Close if a panel is opened"""
        self.admin_console.unswitch_to_react_frame()
        try:
            if self.driver.find_element(By.XPATH,
                "//div[@class='modal-dialog']//div[@class='modal-content']|//div[contains(@class,'mui-modal-content')]").size['height'] > 100:
                self.driver.find_element(By.XPATH,
                    "//button[contains(text(), 'Close')]|//div[contains(text(),'Cancel')]|//button[contains(@class,"
                    "'btn btn-default') and contains(text(),'Cancel')]|//a[contains(@class,'modal__close-btn')]|//div[contains(text(), 'Close')]"
                ).click()
        except NoSuchElementException:
            self.log.info("No panel to close")

    @PageService(log=True, react_frame=True)
    def access_item_in_table(self, name, record=True):
        """ACCESS FIRST ELEMENT IN TABLE
        Args:
            name : str -- Name of the table which will be used to store in the database,
            record : boolean -- True if the APIs and performance has to be recorded
            """
        self.details_page_visited = False
        try:
            ignore_tables = ["global_exceptions"]
            first_anchor_tag = "//tbody//a"
            xpath_angulartable = self.table._xp + first_anchor_tag
            xpath_reacttable = self.rtable._xpath + first_anchor_tag
            if name not in ignore_tables:
                data = self.driver.find_elements(By.XPATH, xpath_angulartable + '|' + xpath_reacttable)
                if data and data[0].size['height'] > 0 and data[0].size['width'] > 0:
                    data[0].click()
                    self.admin_console.start_time_load = time.time()
                    self.admin_console.wait_for_completion()
                    self.wait_for_load()
                    self.admin_console.end_time_load = time.time()
                    if record:
                        self.record_load_time(name + "_details",
                                              (self.admin_console.end_time_load - self.admin_console.start_time_load))
                        self.details_page_visited = True
                self.close_panel()
        except (ElementNotInteractableException, StaleElementReferenceException):
            self.log.error("Exception while clicking the first element in the table")

    def wait_for_load(self, admin_page=True):
        """Waits for the page to load along with other loaders for table and react components
        Args:
            admin_page : boolean -- True if it is a details page
            """
        # if admin_page:
        #     self.admin_page.wait_for_completion()
        # self.log.info("Waiting for the loaders to disappear")
        try:
            WebDriverWait(self.driver, 800).until(
                ec.invisibility_of_element_located((By.XPATH,
                                                    "//*[contains(@class, 'loader-backdrop')]|//div[contains(@title,'Loading')]|//div[contains(@class,'loading-data')]|//div[contains(@class,'grid-loading')]")))
        except TimeoutException:
            self.log.info("5 mins Timeout Exception occured . Moving on")

    @PageService()
    def __switchto_parenttab(self, page):
        """Navigates to a parent tab"""
        eval(f"self.admin_page.navigate_to_" + page + '()')
        self.admin_console.clear_perfstats()

    @PageService(react_frame=True)
    def navigate_to_eachtab(self, page, record=True):
        """Navigate to multiple tabs in a table
            Args:
                page -- (str) Page name to be stored in DB
                record -- (boolean) True if performance needs to be recorded
        """
        try:
            visited = [""]
            tabs = self.rtable.get_all_tabs()
            tab_length = len(tabs)
            # Find the number of tabs present in the table
            if tab_length < 1 or page.upper() == 'MY_DATA':
                return False
            self.access_item_in_table(page + ":" + tabs[0], record)
            if self.details_page_visited and tab_length > 1:
                self.__switchto_parenttab(page)
            count = 1
            while len(visited) < tab_length and count < tab_length:
                i = tabs[count]
                if i not in visited:
                    tab_text = i
                    self.log.info("Navigating to tab " + tab_text + " in " + page + " page")
                    time1 = self.admin_console.start_time_load = time.time()
                    self.rtable.view_by_title(i)
                    time2 = self.admin_console.end_time_load = time.time()
                    visited.append(tab_text)
                    if record and ((self.ui_only and count > 0) or not self.ui_only):
                        self.log.info("Record the load time for tab")
                        self.record_load_time(page + ":" + tab_text, time2 - time1)
                    self.access_item_in_table(page + ":" + tab_text, record)
                    if count < (len(tabs) - 1):
                        self.__switchto_parenttab(page)
                    count += 1
            return True

        except NoSuchElementException:
            self.log.info("No react table present in the page " + page)
            return False

    def __generate_directory(self):
        #  This method is used to create a directory to store csv and DB generated from run
        dir_path = self.nlogfolder
        csv_dir = os.path.join(dir_path, "CSV_reports")
        self.cmd = TIMESTAMP
        run_folder = os.path.join(csv_dir, TIMESTAMP)
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        if not os.path.exists(csv_dir):
            os.mkdir(csv_dir)
        os.mkdir(run_folder)
        self.runfolder = run_folder

    @staticmethod
    def __process_api_string(api_string):
        """Remove the IDs from the API to make it consistent across the runs and service packs"""
        if "reports" in api_string:
            return re.sub(r'(id=|entity=|Id=|IdList=)([\d]+)', r'\1{id}', api_string, flags=re.MULTILINE | re.I)
        partial_output = re.sub(r'\/[a-z0-9]+[-][a-z0-9-]*',r'/{id}', api_string, flags=re.MULTILINE | re.I)
        return re.sub(r'(id=|entity=|Id=|IdList=|\/)([\d]+)', r'\1{id}', partial_output, flags=re.MULTILINE | re.I)

    def record_load_time(self, page, uitime, stats_input=None):
        """
            stores the APIs which loaded upon navigating to the page;
            stores the load time in associated lists and dictionaries;

            :return: None
        """
        self.log.info("Record the APIs called in this page " + str(page))
        current_url = self.driver.current_url
        ui_endpoint_brwser = '#' + current_url.split("#")[-1]
        if not stats_input:
            browser_cache = self.browser.get_browser_networkstats()
            # Collect the APIs in this page from nwlogger page
            if self.admin_console.nwloggermode:
                self.nwlogpage.get_table_values()
                nwlogger_cache = self.nwlogpage.current_data
                for row in nwlogger_cache:
                    if ui_endpoint_brwser in row['PAGE'] or row["PAGE"] in ui_endpoint_brwser:
                        user_nwlog = row['USER']
                        if user_nwlog == self.tcinputs.get("username") or user_nwlog == self.tcinputs.get(
                                "user_id").__str__():
                            data = [page.upper(), self.__process_api_string(row['UI ENDPOINT']),
                                    self.__process_api_string(row['API']), str(row['TIME TAKEN']), self.run_id]
                            data = ','.join(["'" + str(elem) + "'" for elem in data])
                            nwlog_query = f"INSERT INTO APITIME (PAGE,UIENDPOINT,API,TIMETAKEN,RUNID) VALUES ({data})"
                            self.db_connection.execute(nwlog_query)

        else:
            browser_cache = stats_input
        # Capture browser APIs and insert into the
        for item in browser_cache:
            if (item.get('initiatorType') == 'xmlhttprequest' or item.get('initiatorType') == 'fetch') and \
                    not item['name'].endswith('.jsp') and not item['name'].endswith(".js"):
                api = str(item['name'])
                api = api.split("/webconsole")[-1]
                string_split = api.split("commandcenter")[-1]
                proxy_split = string_split.split("/proxy")[-1]
                api_split = self.__process_api_string(proxy_split.split("/api")[-1])
                data = [page.upper(), api_split, str(int(item['duration'])), + self.run_id]
                data = ','.join(["'" + str(elem) + "'" for elem in data])
                brwser_query = f"INSERT INTO BROWSERAPITIME (PAGE, API, TIMETAKEN, RUNID) VALUES ({data})"
                if [api_split, str(int(item['duration']))] in self.apirows:
                    pass
                else:
                    self.db_connection.execute(brwser_query)
                    self.apirows.append([api_split, str(int(item['duration']))])

        ui_time_query = F"INSERT INTO UITIME (PAGE, TOTALTIME, RUNID) VALUES ('{page.upper()}','{uitime * 1000}','{self.run_id}')"
        self.db_connection.execute(ui_time_query)

        page_url = f"INSERT INTO PAGEURL (PAGE, URL,RUNID) VALUES ('{page.upper()}', '{current_url}', '{self.run_id}')"
        self.db_connection.execute(page_url)

    def mail_reports(self):
        """Send the email to the receipients"""
        email = self.mail_list
        cntrol = Machine()
        fromaddr = "apitesting@commvault.com"
        toaddr = email.split(',')
        body_text = ""
        if self.fail_data_count["UI"] > 0:
            table = "<h2>Command Center UI Load time which exceeded threshold increase</h2>" \
                    "<tr><th>PAGE</th><th>CURRENT EXECUTION TIME(in ms)</th><th>PREVIOUS EXECUTION TIME(in ms)</th><th>COMMANDCENTER LINK</th></tr>"
            for i in self.table_data:
                table += f"<tr><td>{i[0]}</td><td>{i[1]}</td><td>{i[2]}</td><td><a href='{i[3]}'>{i[3]}</a></td></tr>"
                body_text = f"<table>{table}</table><br>"
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        msg['To'] = ", ".join(toaddr)
        msg['Subject'] = "SP" + str(self.version) + " - Command Center Screens Load Time Stats on " + str(
            self.commcell_obj.webconsole_hostname) + f" ({cntrol.machine_name})"
        self.nlogfolder = os.path.join(constants.AUTOMATION_DIRECTORY, 'Server', 'RestAPI', "NetworkLogger")
        csv_dir = os.path.join(self.nlogfolder, "CSV_reports", TIMESTAMP)
        file_list = ["average_ui_time.csv", "average_brwser.csv"]
        if self.run_id == 1:
            file_list = ["uitime.csv", "browserapi.csv"]
        file_description_map = {
            "average_ui_time.csv": "CSV File contains the average load time of 5 runs in Current SP compared to "
                                   "average load time of 5 runs in previous version",
            "average_brwser.csv": "CSV File contains the average response time of the "
                                  "APIs from five runs in page which is "
                                  "compared with the average response time in previous SP",
            "ui_failure.png": "Comparision graph of page load time crossing the 25 percent threshold increase with page"
                              "load times from previous service pack",
            "brwser_api_failure.png": "Comparison Graph of the API response times which are exceeding 10 secs "
                                      "threshold benchmark in current service pack with response times in previous "
                                      "service pack",
            "newbrwser.csv": "CSV file contains the APIs which aren't recorded in previous SP for the respective "
                             "pages ",
            "average_api_time.csv": "CSV File which contains the average response time of the "
                                    "APIs(Nwlogger) from five runs in page which is "
                                    "compared with the average response time in previous SP",
            "newnwlog.csv": "CSV file contains the APIs(nwlogger) which aren't "
                            "recorded in previous SP for the respective pages",
            "browserapi.csv": "CSV file which contains the API response times data in the current run",
            "uitime.csv": "CSV file which contains the UI load times in the current run",
            "apitime.csv": "CSV file which contains the API response times(NWLOGGER) data in current run",
            "browserapiremoved.csv": "CSV file which contains the APIs that are removed in the respective page"
        }

        file_name_map = {
            "average_ui_time.csv": "AVERAGE_PAGETIMES.csv",
            "average_brwser.csv": "AVERAGE_APITIMES.csv",
            "ui_failure.png": "PAGE_LOAD_TIME_FAIL.png",
            "brwser_api_failure.png": "API_LOAD_TIME_FAIL.png",
            "newbrwser.csv": "NEWAPIS_BROWSER.csv",
            "newnwlog.csv": "NEWAPIS_NWLOG.csv",
            "average_api_time.csv": "AVERAGE_APITIMES_NWLOG.csv",
            "browserapi.csv": "CURRENT_APITIME_BROWSER.csv",
            "uitime.csv": "CURRENT_UI_LOADTIMES.csv",
            "apitime.csv": "CURRENT_APITIME_NWLOG.csv",
            "browserapiremoved.csv": "OLD_API_REMOVED.csv"
        }

        if self.fail_data_count["UI"]:
            file_list.insert(0, "ui_failure.png")
        if self.fail_data_count["BROWSERAPI"]:
            file_list.insert(0, "brwser_api_failure.png")
        if self.fail_data_count["NEWAPI"] and self.tcinputs.get("includeapidiff"):
            file_list += ["newbrwser.csv"]
        if self.fail_data_count['BROWSERAPIREMOVED'] and self.tcinputs.get("includeapidiff"):
            file_list += ["browserapiremoved.csv"]
        if self.admin_console.nwloggermode:
            if not self.run_id == 1:
                file_list = file_list + ["average_api_time.csv"]
                if self.fail_data_count["NEWNWLOGAPI"] and self.tcinputs.get("includeapidiff"):
                    file_list += ["newnwlog.csv"]
        if self.tcinputs.get("includecurrentruninfo"):
            file_list += ["uitime.csv", "browserapi.csv"]
            if self.admin_console.nwloggermode:
                file_list += ["apitime.csv"]
        time_stamp = "_" + time.asctime(time.localtime(time.time())).replace(" ", "_").replace(":", "_")
        body_content = body_text + "<h2>Please find the attached reports for Command Center UI and API load time statistics</h2>"
        for i in range(len(file_list)):
            attachment = open(os.path.join(csv_dir, file_list[i]), "rb")
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            new_file_name = file_name_map.get(file_list[i])
            file_name = new_file_name.split(".")[0].upper() + time_stamp + "." + file_list[i].split(".")[-1]
            part.add_header('Content-Disposition', "attachment; filename= %s" % file_name)
            msg.attach(part)
            body_content += "<p><b>" + new_file_name + "</b> : " + file_description_map.get(file_list[i]) + "</p>"
        if self.email_msg:
            body_content += "<h1>" + self.email_msg + "</h1>"
        style = """td, th {
          border: 1px solid #dddddd;
          text-align: left;
          padding: 8px;
        }"""
        body = f"""
            <!DOCTYPE html>
            <html lang="en" lang="en">
                <head>
                    <meta content="text/html; charset=" />
                    <style>
                        {style}
                    <style>
                </head>
                <body>
                    {body_content}
                </body>
            </html>
            """
        msg.attach(MIMEText(body, 'html'))
        server = smtplib.SMTP("smtp.commvault.com")
        text = msg.as_string()
        server.sendmail(fromaddr, toaddr, text)
        server.quit()

    def __valid_page(self, page):
        """Check if the page is valid and needs to be visited"""
        ignore_list = ["navigate_to_storage_pools", "navigate_to_network", "navigate_to_my_data",
                       "navigate_to_company", "navigate_to_governance_apps",
                       "navigate_to_systems"]  # PAGES WHICH SHOULD NOT BE VISITED DUE TO DUPLICATES
        input_ignore_list = self.tcinputs.get("ignore_navs", "").split(",")
        ignore_list += input_ignore_list
        ignore_page_list = [x.split("navigate_to_")[-1] for x in ignore_list]
        input_page_list = self.tcinputs.get("pagelist")
        page = page.split("navigate_to_")[-1]
        if page not in ignore_page_list:
            if input_page_list and page in input_page_list:
                return True
            elif not input_page_list:
                return True
        return False

    @PageService()
    def navigate_to_screens(self, record=True):
        """NAVIGATE TO ALL SCREENS"""
        count = 0
        self.log.info("count of navs " + str(len(self.nav_list)))
        self.admin_console.clear_perfstats()
        for i in self.nav_list:
            try:
                if len(self.driver.window_handles) > 2 or (not self.ui_only and len(self.driver.window_handles) > 1):
                    self.log.error("Error :  A new tab opened in the main browser")
                    for j in self.driver.window_handles:
                        if j != self.curr_window and (self.ui_only or (not self.ui_only and j != self.nlogger_handle)):
                            self.driver.switch_to.window(j)
                            self.driver.close()
                    self.driver.switch_to.window(self.curr_window)
                try:
                    if self.__valid_page(i):
                        if not self.ui_only:
                            self.driver.switch_to.window(self.curr_window)
                        self.log.info("Navigating to {}".format(i))
                        self.admin_console.clear_perfstats()
                        eval("self.admin_page." + i + "()")
                        time1 = self.admin_page.start_time_load
                        # THESE ARE THE XPATHS USED TO WAIT UNTIL THE TABLES ARE LOADED WITH DATA
                        self.wait_for_load(admin_page=False)
                        # WAIT UNTIL THE TABLE LOADS PROPERLY
                        time2 = float(round(time.time(), 2))
                        ui_time = time2 - time1
                        self.log.info("Load time is " + str(ui_time))
                        if record:
                            self.record_load_time(i.split("navigate_to_")[-1], ui_time)
                        tab_navstatus = self.navigate_to_eachtab(i.split("navigate_to_")[-1], record=record)
                        # We can add a function over here which can go through the each report
                        if not tab_navstatus and i != "navigate_to_my_data":
                            self.access_item_in_table(i.split("navigate_to_")[-1], record=record)
                        self.db_connection.commit()
                except KeyError as e:
                    self.log.error(e)
                count += 1
                self.log.info("Count : " + str(count))
            except (NoSuchElementException, ElementClickInterceptedException, ElementNotVisibleException) as e:
                self.log.error("The following page navigation does not exists {}".format(i))
                self.log.info(e)
        return True, ""

    def report_generator(self):
        # First file lets take the UI page load times and dump it in the csv
        ui_time_csv = CsvHelper("uitime.csv")
        mr_details = []  # To store the details of MR to be created
        def format_tuple(data):
            return [list(e) for e in data]

        api_time_csv = CsvHelper("apitime.csv")
        browser_apitime_csv = CsvHelper("browserapi.csv")
        average_uitime_csv = CsvHelper("average_ui_time.csv")
        average_apitime_csv = CsvHelper("average_api_time.csv")
        average_apitimebrwser_csv = CsvHelper("average_brwser.csv")
        new_brwserapicsv = CsvHelper("newbrwser.csv")
        newnwlogapicsv = CsvHelper("newnwlog.csv")
        page_graph_fail = CsvHelper("page_graph_fail.csv")
        brsr_api_graph_fail = CsvHelper("brsr_api_graph_fail.csv")
        apis_removed = CsvHelper("browserapiremoved.csv")

        # Write Columns for the graph related CSVs
        page_graph_fail.csv_writer.writerow(["PAGE", "CURRENT TIME", "PREV TIME"])
        brsr_api_graph_fail.csv_writer.writerow(["PAGE", "API", "CURRENT TIME", "PREVIOUS TIME"])
        apis_removed.csv_writer.writerow(["PAGE", "API", "RESPONSETIME"])
        new_brwserapicsv.csv_writer.writerow(["PAGE", "API", "RESPONSETIME"])
        newnwlogapicsv.csv_writer.writerow(["PAGE", "UIENDPOINT", "API", "TIMETAKEN"])

        version = self.db_helper.get_version(self.run_id)[0]
        ui_data = self.db_helper.execute_query(
            f"SELECT PAGE,TOTALTIME,'{version}' AS VERSION FROM UITIME WHERE RUNID = " + str(self.run_id))

        ui_data = format_tuple(ui_data)

        ui_time_csv.csv_writer.writerow(["PAGE", "TOTALTIME", "VERSION"])

        ui_time_csv.csv_writer.writerows(ui_data)

        brwsr_api_data = self.db_helper.execute_query(
            f"SELECT PAGE,API,TIMETAKEN,'{version}' AS VERSION FROM BROWSERAPITIME WHERE RUNID = " + str(
                self.run_id))

        brwsr_api_data = format_tuple(brwsr_api_data)

        browser_apitime_csv.csv_writer.writerow(["PAGE", "API", "TIMETAKEN", "VERSION"])

        browser_apitime_csv.csv_writer.writerows(brwsr_api_data)

        if self.admin_console.nwloggermode:
            nwlog_api_data = self.db_helper.execute_query(
                f"SELECT PAGE,UIENDPOINT,API,TIMETAKEN,'{version}' AS VERSION FROM APITIME WHERE RUNID = " + str(
                    self.run_id))

            nwlog_api_data = format_tuple(nwlog_api_data)
            api_time_csv.csv_writer.writerow(["PAGE", "UIENDPOINT", "API", "TIMETAKEN", "VERSION"])
            api_time_csv.csv_writer.writerows(nwlog_api_data)

        if not self.run_id == 1:
            # GET ALL THE VERSIONS PRESENT IN THE  DB
            query = "SELECT DISTINCT VERSION FROM RUNINFO"
            versions = self.db_helper.execute_query(query)
            version_map = []
            mversion_map = []
            is_metallic_version = True if len(version) >= 2 else False
            for i in versions:
                if len(i[0]) >= 2:
                    mversion_map.append(float(i[0]))
                else:
                    version_map.append(float(i[0]))
            final_array = version_map

            if is_metallic_version:
                # Take the version from a particular array
                final_array = mversion_map

            if max(final_array) == float(version):
                # IDEAL CONDITION :  Current Run is the max version . Other condition not yet handled
                all_versions = final_array
                all_versions.remove(float(version))

                temp_out = self.db_helper.execute_query(
                    "SELECT ID FROM RUNINFO WHERE VERSION = '" + str(version) + "' ORDER BY ID DESC LIMIT 5")
                runs_of_curr_version = ','.join([str(i[0]) for i in temp_out])
                curr_run_array = temp_out

                current_avg_ui_time = format_tuple(self.db_helper.execute_query(
                    f"SELECT PAGE, CAST(AVG(TOTALTIME) AS INT) FROM UITIME WHERE RUNID IN ({runs_of_curr_version}) GROUP BY PAGE"))

                current_brwser_api_time = format_tuple(self.db_helper.execute_query(f"SELECT PAGE, API, CAST(AVG("
                                                                                    f"TIMETAKEN) AS INT) AS RESPONSETIME"
                                                                                    f" FROM BROWSERAPITIME WHERE "
                                                                                    f"RUNID IN ({runs_of_curr_version}) GROUP "
                                                                                    f"BY API,PAGE ORDER BY PAGE "))
                current_avg_api_times = None
                if self.admin_console.nwloggermode:
                    current_avg_api_times = format_tuple(
                        self.db_helper.execute_query(f"SELECT PAGE, UIENDPOINT, API, CAST(AVG("
                                                     f"TIMETAKEN) AS INT) AS RESPONSETIME "
                                                     f"FROM APITIME WHERE "
                                                     f"RUNID IN ({runs_of_curr_version}) GROUP "
                                                     f"BY API,PAGE,UIENDPOINT ORDER BY PAGE "))

                # If there exists runs from previous version
                if len(all_versions) != 0:
                    prev_version = max(all_versions)

                    temp_out = self.db_helper.execute_query(
                        "SELECT ID FROM RUNINFO WHERE VERSION = '" + str(prev_version) + "' ORDER BY ID DESC LIMIT 5")
                    runs_of_prev_version = ','.join([str(i[0]) for i in temp_out])
                    self.email_msg = "COMPARISION IS BETWEEN " + str(version) + f"({str(len(curr_run_array))}" \
                                                                                f" runs) & " + str(prev_version) + \
                                     f"({str(len(temp_out))} runs) "
                    prev_avg_ui_time = self.db_helper.execute_query(
                        f"SELECT PAGE, CAST(AVG(TOTALTIME) AS INT) FROM UITIME WHERE RUNID IN ({runs_of_prev_version}) GROUP BY PAGE")
                    prev_avg_ui_time = format_tuple(prev_avg_ui_time)
                    self.table_data = []

                    for i in current_avg_ui_time:
                        page = i[0]
                        for j in prev_avg_ui_time:
                            if j[0] == page:
                                i.append(j[1])
                        if len(i) == 2:
                            i.append(-1)
                        pageurl = self.db_helper.execute_query("SELECT URL FROM PAGEURL WHERE PAGE = '" + page.upper() +"' AND RUNID = "+str(self.run_id))

                        # THIS PART WILL CALCULATE THE PAGES CROSSING THRESHOLD VALUES AND PUT INTO THE GRAPH CSV
                        if not int(i[2]) == -1:
                            increase = ((int(i[1]) - int(i[2])) / int(i[2]))
                            if (increase * 100) > self.page_load_time_threshold:
                                self.fail_data_count["UI"] += 1
                                page_graph_fail.csv_writer.writerow(i[:3])
                                # Save the pagedata which can be used to generate email
                                if (self.tcinputs.get("createMR") and i[0] != 'LOGIN' and
                                        int(i[1]/1000) > int(self.tcinputs.get("threshold_time", 30))):
                                    # Finding APIs in the page
                                    api_details = []
                                    for k in current_brwser_api_time:
                                        if k[0] == i[0]:
                                            api_details.append([k[1][:150],k[2]])
                                            #storing api(length limited to 150 chars) and time
                                    # Recording data to create MR for pages having long difference from previous version
                                    data = {
                                        'page': i[0],
                                        'currentTime': int(i[1]),
                                        'previousTime': int(i[2]),
                                        'currentVersion': version,
                                        'previousVersion': prev_version,
                                        'pageUrl': pageurl[0][0],
                                        'api_details': api_details
                                    }
                                    mr_details.append(data)

                        if pageurl:
                            url = pageurl[0][0]
                            i.append(url)
                            self.table_data.append(i)

                    average_uitime_csv.csv_writer.writerow(
                        ["PAGE", "AVGTIME IN CUR VERSION", "AVGTIME IN PREV VERSION"])
                    average_uitime_csv.csv_writer.writerows(current_avg_ui_time)
                    previous_brwser_api_time = format_tuple(self.db_helper.execute_query(f"SELECT PAGE, API, CAST(AVG("
                                                                                         f"TIMETAKEN) AS INT) AS RESPONSETIME"
                                                                                         f" FROM BROWSERAPITIME WHERE "
                                                                                         f"RUNID IN ({runs_of_prev_version}) GROUP "
                                                                                         f"BY API,PAGE ORDER BY PAGE"))
                    for i in current_brwser_api_time:
                        page = i[0]
                        api = i[1]
                        flag = False
                        newpage = True
                        for j in previous_brwser_api_time:
                            if j[0] == page:
                                if len(j) < 4:
                                    j.append(0)
                                newpage = False
                                if j[1].lower() == api.lower():
                                    i.append(j[2])
                                    flag = True
                                    j[-1] = 1
                                    break
                        if not newpage and not flag:
                            self.log.info("This API isn't present in prev version -> " + i.__str__())
                            new_brwserapicsv.csv_writer.writerow(i[:3])
                            self.fail_data_count["NEWAPI"] += 1
                        if not flag:
                            i.append(-1)
                        if int(i[2]) > 10000:
                            self.fail_data_count["BROWSERAPI"] += 1
                            row_m = i
                            row_m[1] = i[1][:50].replace(",", "")
                            brsr_api_graph_fail.csv_writer.writerow(i)

                    for i in previous_brwser_api_time:
                        if len(i) == 4 and i[3] == 0:
                            self.log.info("This old api isn't present in current version -> " + i.__str__())
                            apis_removed.csv_writer.writerow(i[:3])
                            self.fail_data_count["BROWSERAPIREMOVED"] += 1

                    average_apitimebrwser_csv.csv_writer.writerow(
                        ["PAGE", "API", "CUR AVG TIME", "PREV VERSION AVG TIME"])
                    average_apitimebrwser_csv.csv_writer.writerows(current_brwser_api_time)

                    if self.admin_console.nwloggermode:
                        previous_avg_api_times = self.db_helper.execute_query(f"SELECT PAGE, UIENDPOINT, API, CAST(AVG("
                                                                              f"TIMETAKEN) AS INT) AS RESPONSETIME "
                                                                              f"FROM APITIME WHERE "
                                                                              f"RUNID IN ({runs_of_prev_version}) GROUP "
                                                                              f"BY API,PAGE,UIENDPOINT ORDER BY PAGE ")
                        previous_avg_api_times = format_tuple(previous_avg_api_times)

                        for i in current_avg_api_times:
                            page = i[0]
                            uiend = i[1]
                            api = i[2]
                            flag = False
                            newpage = True
                            for j in previous_avg_api_times:
                                if j[0] == page:
                                    newpage = False
                                    if j[1] == uiend and j[2] == api:
                                        i.append(j[3])
                                        flag = True
                                        break
                            if not newpage and not flag:
                                self.log.info("this api isn't present in the prev version")
                                self.log.info(i)
                                self.fail_data_count["NEWNWLOGAPI"] += 1
                                newnwlogapicsv.csv_writer.writerow(i)
                                i.append(-1)

                        average_apitime_csv.csv_writer.writerow(
                            ["PAGE", "UIENDPOINT", "API", "CURR AVG TIME", "PREV AVG TIME"])
                        average_apitime_csv.csv_writer.writerows(current_avg_api_times)

                else:
                    # There are no runs from the previous version just put all the CSVs with current data
                    if self.admin_console.nwloggermode:
                        average_apitime_csv.csv_writer.writerow(
                            ["PAGE", "UIENDPOINT", "API", "CURR AVG TIME"])
                        average_apitime_csv.csv_writer.writerows(current_avg_api_times)

                    average_apitimebrwser_csv.csv_writer.writerow(
                        ["PAGE", "API", "CUR AVG TIME"])
                    average_apitimebrwser_csv.csv_writer.writerows(current_brwser_api_time)

                    average_uitime_csv.csv_writer.writerow(
                        ["PAGE", "AVGTIME IN CUR VERSION"])
                    average_uitime_csv.csv_writer.writerows(current_avg_ui_time)

        del average_uitime_csv
        del average_apitime_csv
        del api_time_csv
        del browser_apitime_csv
        del ui_time_csv
        del average_apitimebrwser_csv
        del newnwlogapicsv
        del new_brwserapicsv
        del brsr_api_graph_fail
        del page_graph_fail
        del apis_removed
        return mr_details
    def create_graphs(self):
        """Generate the graphs from CSV for the failures"""
        file_path = os.path.join(self.nlogfolder, "CSV_reports", TIMESTAMP)
        ui_graph_file_name = os.path.join(file_path, "ui_failure.png")
        api_graph_file_name = os.path.join(file_path, "brwser_api_failure.png")
        self.log.info("Inside the create graphs")
        if self.fail_data_count["UI"]:
            generate_ui_failure(os.path.join(file_path, "page_graph_fail.csv"),
                                ui_graph_file_name, "PAGE LOAD TIME EXCEEDING THRESHOLD", "LOAD TIME IN ms")

        if self.fail_data_count["BROWSERAPI"]:
            generate_ui_failure(os.path.join(file_path, "brsr_api_graph_fail.csv"), api_graph_file_name,
                                "API LOAD TIME EXCEEDING THRESHOLD", "LOAD TIME IN ms", column_start=1)


class CsvHelper:

    def __init__(self, file_name):
        """Class constructor :
            Args:
                file_name : CSV file name
                """
        self._name = file_name
        self.nlogfolder = os.path.join(constants.AUTOMATION_DIRECTORY, 'Server', 'RestAPI', "NetworkLogger")
        csv_dir = os.path.join(self.nlogfolder, "CSV_reports", TIMESTAMP)
        self.file_handle = open(os.path.join(csv_dir, file_name), "w")
        self.csv_writer = csv.writer(self.file_handle)

    def __del__(self):
        self.file_handle.close()


class LoadTimeValuesHelper:
    """
    This class contains the additional methods which will help in interacting with NWLOGGER DB files
    """

    def __init__(self, db_name="NETWORK_LOGGER.db"):
        """Class initializer
        Args:
            db_name (str) : Name of the .db file for load time values
        """
        self.db_name = db_name
        self.nlogfolder = os.path.join(constants.AUTOMATION_DIRECTORY, 'Server', 'RestAPI', "NetworkLogger")
        try:
            self.db_connection = sqlite3.connect(os.path.join(self.nlogfolder, self.db_name))
        except Exception:
            raise Exception("Exception while accessing the db file")

    def get_latest_runid(self):
        query = """SELECT ID from RUNINFO ORDER BY ID DESC"""
        return self.execute_query(query, fetchall=False)

    def get_version(self, run_id):
        query = """SELECT VERSION FROM RUNINFO WHERE ID = {}""".format(run_id)
        return self.execute_query(query, fetchall=False)

    def execute_query(self, sql, fetchall=True):
        cursor = self.db_connection.execute(sql)
        self.db_connection.commit()
        if fetchall:
            return cursor.fetchall()
        else:
            return cursor.fetchone()

    def create_tables(self):
        """CREATE THE TABLES NECESSARY FOR THE DATA STORAGE """
        self.db_connection.execute('''CREATE TABLE IF NOT EXISTS RUNINFO
                (ID INTEGER PRIMARY KEY     NOT NULL,
                RUNDATE     TIMESTAMP   NOT NULL,
                VERSION     TEXT    NOT NULL,
                HOSTNAME    TEXT
                );''')
        self.db_connection.execute('''CREATE TABLE IF NOT EXISTS APITIME
                 (ID INTEGER PRIMARY KEY     NOT NULL,
                 PAGE           TEXT    NOT NULL,
                 UIENDPOINT            TEXT     NOT NULL,
                 API        TEXT     NOT NULL,
                 TIMETAKEN         TEXT     NOT NULL,
                 RUNID           INTEGER    NOT NULL,
                 FOREIGN KEY(RUNID) REFERENCES RUNINFO(ID)
                 );
                 ''')
        self.db_connection.execute('''
                CREATE TABLE IF NOT EXISTS PAGEURL
                 (ID INTEGER PRIMARY KEY     NOT NULL,
                 PAGE           TEXT    NOT NULL,
                 URL         TEXT     NOT NULL,
                 RUNID           INTEGER    NOT NULL,
                FOREIGN KEY(RUNID) REFERENCES RUNINFO(ID)
                );
                ''')
        self.db_connection.execute('''
                CREATE TABLE IF NOT EXISTS UITIME
                 (ID INTEGER PRIMARY KEY     NOT NULL,
                 PAGE           TEXT    NOT NULL,
                 TOTALTIME         TEXT     NOT NULL,
                 RUNID           INTEGER    NOT NULL,
                FOREIGN KEY(RUNID) REFERENCES RUNINFO(ID)
                );
                ''')
        self.db_connection.execute('''CREATE TABLE IF NOT EXISTS BROWSERAPITIME
                 (ID INTEGER PRIMARY KEY     NOT NULL,
                 PAGE           TEXT    NOT NULL,
                 API        TEXT     NOT NULL,
                 TIMETAKEN         TEXT     NOT NULL,
                 RUNID           INTEGER    NOT NULL,
                 FOREIGN KEY(RUNID) REFERENCES RUNINFO(ID)
                 );
                 ''')

    def clear_database(self):
        """DELETE ALL THE VALUES FROM THE TABLES"""
        self.execute_query("DELETE FROM BROWSERAPITIME")
        self.execute_query("DELETE FROM PAGEURL")
        self.execute_query("DELETE FROM UITIME")
        self.execute_query("DELETE FROM RUNINFO")
        self.execute_query("DELETE FROM APITIME")


class NwLoggerPage:
    """This class contains all the methods which is used to interact with nwlogger page"""

    def __init__(self, driver, browser, adminconsole):
        """Class constructor"""
        self.nwlog = None
        self.driver = driver
        self.browser = browser
        self.adminconsole = adminconsole
        self.current_data = []

    def refresh_nwlogger(self):
        """Refresh the nwlogger page to reload the API table contents"""
        time.sleep(2)
        self.driver.refresh()
        sleep_time = 1
        load_time = 0
        while load_time <= 100:
            if self.driver.execute_script("return document.readyState") == "complete":
                break
            time.sleep(sleep_time)
            load_time = load_time + sleep_time

    def get_table_values(self):
        """Read the table and get the data for API load time """
        self.current_data = []
        self.browser.switch_to_first_tab()
        self.refresh_nwlogger()
        rows = self.driver.find_elements(By.XPATH, '//table[@class="table"]/tbody/tr')
        cols_ = self.driver.find_elements(By.XPATH, '//table[@class="table"]/thead/tr//th')
        index_map = {}
        for cnt, elem in enumerate(cols_):
            index_map[elem.text.upper()] = cnt + 1
        for row in rows:
            row_data = {"PAGE": row.find_element(By.XPATH, f"./td[{index_map['PAGE']}]").text,
                        "UI ENDPOINT": row.find_element(By.XPATH, f"./td[{index_map['UI ENDPOINT']}]").text.split(
                            ".svc")[-1]}
            if index_map.get("USER"):
                row_data["USER"] = row.find_element(By.XPATH, f"./td[{index_map['USER']}]").text
            row_data["TIME TAKEN"] = round(
                float(row.find_element(By.XPATH, f"./td[{index_map['TIME TAKEN']}]").text.split('ms')[0]),
                2)
            api_method = row.find_element(By.XPATH, f'./td[{index_map["METHOD"]}]').text + ' '
            url = re.split(r":[0-9]{2}|.svc", row.find_element(By.XPATH, f"./td[{index_map['API']}]").text)
            if len(url) > 1:
                if "SearchSvc/CVWebService" in url[1]:
                    path = url[2]
                else:
                    path = url[1]
            else:
                path = url[0]
            row_data["API"] = api_method + path
            self.current_data.append(row_data)
        self.browser.switch_to_latest_tab()


class AutoMR:
    def __init__(self, commcell_obj, admin_console, browser, tcinputs):
        """
        :param commcell_obj: commcell object of remote CS machine
        :param admin_console: logged in admin console object
        :browser : browser object
        :tcinputs : testcase inputs have to be passed
            Customization inputs:
                createMR - Set this key true to generate MRs to report pages taking long time
                threshold_time - The threshold value of time in seconds above which the pages are considered faulty.
                                Default value is 30s
                reported_by - Email id of the reporter of the defect. (optional)
                reported_to - Email id of the assignee of the defect. (optional)
                setup_credentials - Can provide the URl of the setup details from Dead-Drop . (optional)

        """
        self.commcell_obj = commcell_obj
        self.version = self.commcell_obj.version.split("11.")[-1]
        self.admin_page = admin_console.navigator
        self.admin_console = admin_console
        self.log = logger.get_log()
        self.ui_only = self.admin_console.nwloggermode
        self.panel = ModalPanel(admin_console)
        self.driver = browser.driver
        self.rtable = Rtable(self.admin_console)
        self.table = Table(self.admin_console)
        self.tcinputs = tcinputs
        self.browser = browser
        self.dialog = RModalDialog(self.admin_console)
    def wait_for_load(self, admin_page=True):
        try:
            WebDriverWait(self.driver, 800).until(
                ec.invisibility_of_element_located((By.XPATH,
                                                    "//*[contains(@class, 'loader-backdrop')]|//div[contains(@title,'Loading')]|//div[contains(@class,'loading-data')]|//div[contains(@class,'grid-loading')]")))
        except TimeoutException:
            self.log.info("5 mins Timeout Exception occured . Moving on")

    @PageService(react_frame=True)
    def navigate_to_tab(self, page, tab):
        """Navigate to a tab in a table
            Args:
                page -- (str) Page name
                tab -- (str) Tab name
        """
        try:
            tabs = self.rtable.get_all_tabs()
            for i in tabs:
                if i.lower() == tab:
                    tab = i
                    break
            self.log.info("Navigating to tab " + tab + " in " + page + " page")
            self.rtable.view_by_title(tab)
        except NoSuchElementException:
            self.log.info("No react table present in the page ")
    @PageService(log=True, react_frame=True)
    def access_item_in_table(self, name):
        """ACCESS FIRST ELEMENT IN TABLE
        Args:
            name : str -- Name of the table which will be used to store in the database
        """
        try:
            first_anchor_tag = "//tbody//a"
            xpath_angulartable = self.table._xp + first_anchor_tag
            xpath_reacttable = self.rtable._xpath + first_anchor_tag
            data = self.driver.find_elements(By.XPATH, xpath_angulartable + '|' + xpath_reacttable)
            if data and data[0].size['height'] > 0 and data[0].size['width'] > 0:
                data[0].click()
                self.admin_console.wait_for_completion()
                self.wait_for_load()
        except (ElementNotInteractableException, StaleElementReferenceException):
            self.log.error("Exception while clicking the first element in the table")

    def report_defect(self, details):
        try:
            self.driver.find_element(By.XPATH, "//div[@aria-label='Reported defects']").click()
            self.wait_for_load()
            self.dialog.click_button_on_dialog(text="Report a defect")
            self.wait_for_load()
            # Filling defect summary
            self.admin_console.fill_form_by_xpath("//input[@id='subject']",f"SP{details.get("currentVersion")}: "
                                                        f"{details.get("page")} page taking long time to load")
            if self.tcinputs.get("reported_by"):
                # Filling defect reporter email
                self.admin_console.fill_form_by_xpath("//input[@id='email']", self.tcinputs.get("reported_by"))
            if self.tcinputs.get("reported_to"):
                # Filling defect assignee email
                self.admin_console.fill_form_by_xpath("//input[@id='assignedEmail']", self.tcinputs.get("reported_to"))
            issue_detail = (
                        f"In SP{details.get("previousVersion")} time for the page {(details.get("page")).lower()} "
                        f"to get load is around {int(details.get("previousTime")/1000)}s. "
                        f"But in SP{details.get("currentVersion")} it takes around "
                        f"{int(details.get("currentTime")/1000)}s. \n APIs and time taken for it in the page are:")

            for api in details.get("api_details"):
                issue_detail += f"\n {api[0]} Time: {api[1]}ms"
            if self.tcinputs.get("setup_credentials"):
                issue_detail += "\nCredentials: " + self.tcinputs.get("setup_credentials")
            iframe = self.driver.find_element(By.XPATH, "//iframe[@class='k-iframe']")
            # To switch to iframe which contain the description
            self.driver.switch_to.frame(iframe)
            issue_input = self.driver.find_element(By.XPATH, "//p")
            issue_input.click()
            issue_input.send_keys(Keys.CONTROL, Keys.END)
            issue_input.send_keys(Keys.RETURN)
            issue_input.send_keys(issue_detail)
            # Switch back to main content
            self.driver.switch_to.default_content()
            self.dialog.click_button_on_dialog(id="Save")#submiting the MR
            self.wait_for_load()
            # self.dialog.click_button_on_dialog(id="Cancel")
            # self.wait_for_load()
            self.dialog.click_button_on_dialog(aria_label="Close")
            self.wait_for_load()
            return
        except Exception as e:
            raise Exception(e)
    def create_mrs(self,mr_details):
        try:
            self.log.info("Inside MR Creation")
            self.log.info("No.of Defects to report: {}".format(len(mr_details)))
            reported_page_urls = []
            for i in mr_details:
                if i.get("pageUrl") in reported_page_urls:
                    continue
                reported_page_urls.append(i.get("pageUrl"))
                page = (i.get("page")).lower()
                basepage = page.split(":")[0]
                eval("self.admin_page.navigate_to_" + basepage + "()")
                if ":" in page:
                    tail = page.split(":")[-1]
                    tab = tail.split("_details")[0]
                    self.navigate_to_tab(page, tab)
                    if "_details" in tail:
                        self.access_item_in_table(page)
                self.log.info("Creating MR for {}".format(page))
                self.report_defect(i)

        except (ElementNotInteractableException, StaleElementReferenceException) as e:
            self.log.error(f"Exception occurred: {e}")
