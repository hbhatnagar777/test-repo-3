# -*-  coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ---------------------------------------------------------------------------

r"""Main controller file for Running Commvault Automation.

This file handles the initialization of Automation, including:

    a.  initalizing logger objects

    b.  establishing connection to the commcell, via REST API, using Developer SDK - Python

    c.  reading, and loading the input JSON

    d.  get the version and service pack installed on the CommServ
    
    e.  parsing through the list of all test cases to be ran

    f.  executing the test case via organization into test sets by product\os\application\etc.

    g.  processing the test case output

    h.  updating test case status to DB

    i.  updating test case status to QA

    j.  generating email content with test case status

    k.  disconnecting from the commcell

    l.  ...etc...



CVAutomation is the only class defined in this file, which handles the Automation Run for the
given input JSON.  It operates as a producer\consumer Queue where threads are started and waiting
for items to enter the queue.


CVAutomation:

    __init__()                      --  initialize instance of the CVAutoamtion class,
    and the class attributes

    _read_args()                    --  reads the Command Line Args

    _read_input_file()              --  reads the input json file and returns dict

    _initialize_logger()            --  initializes CVAutomation logger object

    _login_to_webconsole()          --  establishes a connection to the webconsole, and performs login
    operation using the credentials provided

    _get_commserv_version()         --  gets the version and service pack installed on the CommServ

    _testset_thread_processor()     --  the thread function that processes a testset

    setup()                         --  sets up objects needed for the entire run of automation,
    like commcell and csdb.

    _start_testset_threads()        --  will start all of the threads to process a testset based on the
    config in json input or default in defines.  These threads pull CVTestset objects
    off CVAutomation.queue.

    _populate_testset_queue()       --  for every testset in json input, create CVTestset object and
    push into the queue which holds all testset objects, a testset thread will pull
    items off the queue and process them.

    _run_testsets_threaded()        --   starts the testset threads, populates the queue, and waits for
    queue to empty

    _update_test_results()          --  updates the test set results to local variable

    _get_html_report()              --  returns the HTML Report

    _send_mail()                    --  sends an email to specified receivers

    _update_results_to_db()         --  Updates the test case results to the DB
    
    _console_output()               --  function to print test case execution output on console

    _exit_run()                     --  Exits the run with the exit code

    execute()                       --  executes the cvautomation

    _get_client_names_for_subject() -- returns the client names that are to be returned with subject line

    _get_attachments_list()         -- returns the list of attachment file paths from all testcases
"""

import os
import sys
import json
import argparse
import threading
import time
import itertools
import traceback
from datetime import datetime

from collections import (
    OrderedDict,
    defaultdict
)
from queue import Queue

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from cvpysdk.commcell import Commcell

from AutomationUtils import logger
from AutomationUtils import constants
from AutomationUtils import database_helper
from AutomationUtils import cvtestset
from AutomationUtils import defines as AUTOMATION_DEFINES
from AutomationUtils import commonutils
from AutomationUtils.machine import Machine
from AutomationUtils.mailer import Mailer
from AutomationUtils.htmlgenerator import HTMLReportGenerator
from AutomationUtils.database_helper import CommServDatabase

from AutomationUtils.config import get_config

AUTOMATION_CONFIG = get_config()

class CVAutomation:
    """Main controller class for running Commvault Automation."""

    def __init__(self):
        """Initialize instance of the CVAutomation class."""
        self._inputs = {}
        self._test_set_results = defaultdict(list)
        self._automation_results = list()
        self._commcell = None
        self._log = None
        self._log_dir = None
        self._csdb = None
        self._lock = threading.Lock()
        self._test_cases_dir = None
        self.test_headers = None
        self._commserv_version = None
        self._ts_queue = None
        self._input_file = None
        self._job_id = None
        self._start_time = None
        self._end_time = None
        self._controller = None
        self.autocenter = None

    def _read_args(self, input_json=None):
        """Reads the Command Line arguments if the input json is not given,
            or set to default value None.

            If the input json is given in the method args, then loads that JSON into the
            _inputs dict.

            Otherwise, reads the command line args for the input JSON, and loads that.

            Ability to give a specific testcase OR testcases to run from command line.
            If inputJSON is also specified, only the specified testcase(s)
            from that input json are executed.

            Args:
                input_json  (str)   --  path of the JSON input file to load

            Returns:
                None

            Raises:
                None

            TODO:
                If --tc is supplied with no input json,
                we will attempt to ask for the inputs on command line.

        """

        if input_json is None:
            parser = argparse.ArgumentParser(
                description="Commvault Test Automation",
                formatter_class=argparse.RawTextHelpFormatter
            )

            parser.add_argument(
                '--inputJSON',
                '-json',
                dest='input_file',
                help='Input JSON file path',
                required=True,
                default=None
            )

            parser.add_argument(
                '-tc',
                '--testcase',
                action='append',
                dest='tcList',
                help=(
                    'Specific testcase to execute.{0}'
                    'Add this argument for EACH testcase you wish to run.{0}'
                    'EXAMPLE: -tc 1234 -tc 5678 -tc 9012'
                ).format(os.linesep),
                required=False,
                metavar="TESTCASE_ID",
                default=[]
            )

            parser.add_argument(
                '-ts',
                '--testset',
                action='append',
                dest='tsList',
                help=(
                    'Specific testset to execute.{0}'
                    'Add this argument for EACH testset you wish to run.{0}'
                    'EXAMPLE: -ts FileSystem_WINDOWS -ts FileSystem_WINDOWS_ONEPASS'
                ).format(os.linesep),
                required=False,
                metavar="TESTSET_NAME",
                default=[]
            )

            parser.add_argument(
                '-c',
                '--convert',
                action='store_true',
                dest='convertJson',
                help='Convert the input json into testset format',
                required=False,
                default=False
            )

            parser.add_argument(
                '-o',
                '--outputFile',
                dest='outputJsonFile',
                help='Full path to the output file where converted JSON will be saved.',
                metavar="FULL_PATH_TO_FILE",
                default=None
            )
            
            parser.add_argument(
                '-oc',
                '--outputConsole',
                dest='outputonconsole',
                help='testcase execution output will be displayed on console',
                default=False,
                required=False,
            )

            parser.add_argument(
                '-of',
                '--outputTofile',
                dest='outputonfile',
                help='testcase execution output will be saved to a file',
                default=None,
                required=False,
            )

            parser.add_argument(
                '-otc',
                '--outputTableToConsole',
                dest='outputTableToConsole',
                help='testcase execution output will be displayed in table format on console',
                action='store_true',
                required=False,
            )

            args = parser.parse_args()

            # Store the arguments
            # so if they increase, no need to create properties for every new argument
            self._input_file = args.input_file
            setattr(self, AUTOMATION_DEFINES.TESTCASE_LIST, args.tcList)
            setattr(self, AUTOMATION_DEFINES.TESTSET_LIST, args.tsList)
            setattr(self, AUTOMATION_DEFINES.CONVERT_INPUT, args.convertJson)
            setattr(self, AUTOMATION_DEFINES.JSON_OUT_PATH, args.outputJsonFile)
            setattr(self, AUTOMATION_DEFINES.JSON_OUT_CONSOLE, args.outputonconsole)
            setattr(self, AUTOMATION_DEFINES.JSON_OUT_FILE, args.outputonfile)
            setattr(self, AUTOMATION_DEFINES.JSON_OUT_TABLE_CONSOLE, args.outputTableToConsole)

        else:
            self._input_file = input_json
            setattr(self, AUTOMATION_DEFINES.TESTCASE_LIST, [])
            setattr(self, AUTOMATION_DEFINES.TESTSET_LIST, [])
            setattr(self, AUTOMATION_DEFINES.CONVERT_INPUT, False)
            setattr(self, AUTOMATION_DEFINES.JSON_OUT_PATH, None)
            setattr(self, AUTOMATION_DEFINES.JSON_OUT_CONSOLE, False)
            setattr(self, AUTOMATION_DEFINES.JSON_OUT_FILE, None)

        self._inputs = self._read_input_file()

    def _read_input_file(self):
        """Reads the input json file, and returns the dictionary.

            Checks if the file exists or not.

            If the file exits, loads into a python dict, and returns the dict.
            Otherwise, raises Exception.

            Returns:
                dict    -   JSON loaded into a dictionary

            Raises:
                Exception:
                    if JSON file not found, i.e., file does not exist at the given location

        """
        # Check if input file exists
        if not os.path.exists(self._input_file):
            raise Exception("JSON File Not Found at: " + self._input_file)

        # Load inputs from input file
        with open(self._input_file, 'r', encoding='utf-8') as json_input:
            return json.load(json_input, object_pairs_hook=OrderedDict)

    def _initialize_logger(self):
        """Initialize the logger for the Automation run."""
        try:
            # Get the job ID from the JSON
            self.jobID = self._inputs.get('jobID', '###')
            self._log_dir = constants.LOG_DIR
            __ = logger.Logger(
                self._log_dir, constants.AUTOMATION_LOG_FILE_NAME, self.jobID
            )

            self._log = logger.getLog()

            self._log.info("*" * 80)
            self._log.info(
                "%(boundary)s %(message)s %(boundary)s",
                {
                    'boundary': "*" * 25,
                    'message': "Automation Execution Started"
                }
            )
            self._log.info("*" * 80)
        except Exception as excp:
            raise Exception("Failed to initialize logger with error: {0}".format(excp))

    def _login_to_webconsole(self):
        """Establishes connection to the Commcell via Web Console, if commcell details are
            given in the input JSON.

            If commcell details are not present in the input dict, then exit out.

        """
        try:
            if 'commcell' not in self._inputs:
                return
            
            try:
                verify_ssl = AUTOMATION_CONFIG.API.VERIFY_SSL_CERTIFICATE
            except AttributeError:
                verify_ssl = False

            commcell_dict = self._inputs['commcell']

            if isinstance(commcell_dict, list):
                valid_webconsole_found = False
                for commcell in commcell_dict:
                    webconsole_hostname = commcell.get('webconsoleHostname')
                    commcell_username = commcell.get('commcellUsername')
                    commcell_password = commcell.get('commcellPassword')

                    if commcell_password is None:
                        raise Exception(
                            f"Commcell password is not set in input request for WebConsole: {webconsole_hostname}")
                    self._log.info(
                        f'Trying with WebConsole Hostname: {webconsole_hostname}, Commcell Username: {commcell_username}')

                    try:
                        self._commcell = Commcell(webconsole_hostname, commcell_username, commcell_password, verify_ssl=verify_ssl)
                        self._log.info(f'Logged in to the Commcell {webconsole_hostname} successfully.')
                        valid_webconsole_found = True
                        self._inputs["commcell"] = commcell
                        break

                    except Exception as excp:
                        self._log.exception(f'Failed to login to {webconsole_hostname} \nError: "{excp}"')

                if not valid_webconsole_found:
                    self._log.exception("None of the webconsoles passed could be connected to")
                    self._exit_run()

            else:
                webconsole_hostname = commcell_dict['webconsoleHostname']
                commcell_username = commcell_dict['commcellUsername']

                self._log.info('WebConsole Hostname: %s', webconsole_hostname)
                self._log.info('Commcell Username: %s', commcell_username)

                if ('commcellPassword' in commcell_dict and
                        commcell_dict['commcellPassword'] is not None):
                    self._log.info('Reading the Password from the Input JSON')
                    commcell_password = commcell_dict['commcellPassword']
                else:
                    raise Exception("Commcell password is not set in input request.")

                self._commcell = Commcell(webconsole_hostname, commcell_username, commcell_password, verify_ssl=verify_ssl)

                self._log.info('Logged in to the Commcell successfully.')
        except Exception as excp:
            self._log.exception('Failed to login\nError: "%s"', (excp))
            temp = {
                "Operation": "Login",
                "Status": constants.FAILED,
                "Reason": "{0}".format(excp)
            }
            self._test_set_results["FAILED"].append(temp)

    def _get_commserv_version(self):
        """Gets the Version, and the Service Pack installed on the CommServ.

            Connects to the CommServ, and returns the version string in the format:

                vXX B80 SPXX

                e.g.:   v11 B80 SP9

            Returns:
                str     -   version info string for the CommServ

        """
        if self._commcell and self._commcell.version:
            # Getting the version number from the commcell object
            version = self._commcell.version.split('.')
            return 'v{0} B80 SP{1}'.format(version[0], version[1])

        # Return the default in the defines
        return AUTOMATION_DEFINES.DEFAULT_CS_VERSION

    def _testset_thread_processor(self, thread_id, testset_queue):
        """This is the worker thread which runs the actual testcases in the testset.

            Args:
                thread_id       (str)       --  the internal unique id of this thread

                        **(Currently unused)**

                testset_queue   (Queue)     --  the queue which this thread should operate on

                    The queue holds CVTestset objects for every testset in the input json file

        """
        while True:
            # Get the testset from the queue.  This is a CVTestset object.
            testset = testset_queue.get()
            self._log.info("Executing testset [%s]", testset.name)

            if self.autocenter is not None:
                from Autocenter import defines as ac_defines
                self.autocenter.update_ts_status(
                    testset.autocenter_tsid,
                    ac_defines.AC_RUNNING,
                    testset.controller_id)
                self.autocenter.update_run_logloc(
                    testset.autocenter_tsid, str(
                        self.autocenter.log))
                self.autocenter.updatecontroller_splevel(testset.autocenter_tsid)

            # Based on the threadcount, start n# threads to run testcases
            testset.start_testcase_threads()

            # Every testset object contains 1 testcase queue,
            # which will control all testcase executions
            testset.populate_testcase_queue()

            # Wait for the testcases to finish for this testset.
            if self.autocenter is not None:
                with self.autocenter.healthcheck_thread((testset.autocenter_tsid)):
                    testset.testcaseQ.join()
                self.autocenter.update_ts_status(
                    testset.autocenter_tsid,
                    testset.tsid_status,
                    testset.controller_id)
            else:
                testset.testcaseQ.join()
            self._log.info("Finished executing testset [%s].", testset.name)
            testset_queue.task_done()

            self._automation_results.append({
                "featureName": testset.product,
                "osName": testset.applicable_os,
                "appVersionName": (
                    testset.appVer if testset.appVer and
                    testset.appVer.lower() not in constants.IGNORE_VALUES else ""
                ),
                "addPropName": (
                    testset.addProp if testset.addProp and
                    testset.addProp.lower() not in constants.IGNORE_VALUES else ""
                ),
                "testcase": testset.get_test_case_details()
            })

    def setup(self):
        """Performs the required tasks for executing automation."""
        self._log.info("Input file path: %s", os.path.realpath(self._input_file))

        # Check if commcell object was initialized; do Commcell specific operations here.
        if self._commcell:
            # Create CS DB object
            self._csdb = CommServDatabase(self._commcell)

            # get the commserv version
            self.commserv_version = self._get_commserv_version()

            # Set global csdb object
            database_helper.set_csdb(self._csdb)

    def _start_testset_threads(self):
        """Start n number of testset threads.
            Either the THREADS flag in testsetConfig JSON input defines how many will run OR the
                defines file.

            All threads operate on a single queue per this CVAutomation object.

            _testset_thread_processor handles the testset execution as the threaded function.
        """
        if AUTOMATION_DEFINES.JSON_TESTSET_CONFIG_KEY in self._inputs:
            thread_count = int(
                self._inputs[AUTOMATION_DEFINES.JSON_TESTSET_CONFIG_KEY].get(
                    AUTOMATION_DEFINES.JSON_THREAD_COUNT_KEY,
                    AUTOMATION_DEFINES.DEFAULT_TS_THREADS
                )
            )  # Default to single thread.
        else:
            thread_count = AUTOMATION_DEFINES.DEFAULT_TS_THREADS

        self._log.info("[%s] testset execution thread(s) starting. ", thread_count)

        testset_queue = Queue()
        commonutils.threadLauncher(thread_count, testset_queue, self._testset_thread_processor)

        self._ts_queue = testset_queue

    def _populate_testset_queue(self):
        """Parses through the list of testsets in the JSON input file and creates
            cvtestset.CVTestset objects.
            Those objects are then added to the queue.
        """

        # Check if any testset needs to be filtered,
        # covert to lower to handle different user inputs
        testset_filter = [x.lower() for x in getattr(self, AUTOMATION_DEFINES.TESTSET_LIST, [])]

        for testset in self._inputs[AUTOMATION_DEFINES.JSON_TESTSET_INPUT_KEY]:
            if testset_filter and testset.lower() not in testset_filter:
                self._log.warning(
                    "Testset [%s] was not selected for execution, skipping it!",
                    testset
                )
                continue

            # Get the JSON node for this testset.
            testset_node = self._inputs[AUTOMATION_DEFINES.JSON_TESTSET_INPUT_KEY][testset]
            testset = cvtestset.CVTestset(testset_node, testset, self)

            # Add required inputs to the testset which we may need access to later
            setattr(
                testset,
                AUTOMATION_DEFINES.COMMCELL_NODE,
                self._inputs.get(AUTOMATION_DEFINES.JSON_COMMCELL_INPUT_KEY)
            )

            self._log.info("Queuing automation for testset [%s].", testset.name)
            self._ts_queue.put((testset), block=True)

    def _run_testsets_threaded(self):
        """Parses through the list of testsets to be executed in the input JSON file.
            Launches n number of threads as defined in the input file OR defines.

            These threads operate on a single queue which is part of self.

            After all threads are launched,
            create cvtestset.CVTestset object and push into the queue.

            Wait for the queue to complete.
        """
        # Fire the threads which will run testsets. It will operate on a global Queue.
        # The number of threads is determined in the defines OR input file.
        self._start_testset_threads()

        # Push the threads into the global testset queue.
        self._populate_testset_queue()

        # Wait for the global testset queue to empty
        self._ts_queue.join()

        self._log.info("Finished processing ALL testset(s).")

    def _update_test_results(self, tc_id, name, status, summary, client_name, 
                             test_set_name, start_time=None, end_time=None, 
                             request_id=None, autocenter_tsid=None, attachments=None):
        """Updates the Test Case Results to instance variable.

            Args:
                tc_id           (str)   --  test case id

                name            (str)   --  test case name

                status          (str)   --  test case status

                summary         (str)   --  test case summary

                client_name     (str)   --  name of the client on which the test case was run

                test_set_name   (str)   --  name of the testset

            Raises:
                Exception:
                    If thread lock cannot be obtained

        """
        try:
            with self.lock:
                if client_name is None:
                    if self._commcell:
                        client_name = self._commcell.commserv_name
                    else:
                        client_name = constants.NO_REASON

                test_case_url = constants.ENGWEB_TESTCASE_URL.format(tc_id)
                
                autocenter_url = None
                if request_id is not None and status == constants.FAILED:
                    from Autocenter.defines import AUTOCENTER, FAILUREURL
                    if FAILUREURL in self._inputs[AUTOCENTER]:
                        autocenter_url = self._inputs[AUTOCENTER][FAILUREURL].format(
                            tc_id, autocenter_tsid, request_id)

                test_case_results = {
                    "Test Case ID": tc_id,
                    "Test Case Name": name,
                    "Client Name": client_name,
                    "Test Case URL": test_case_url,
                    "Status": status,
                    "Summary": summary,
                    "Start Time": start_time,
                    "End Time": end_time,
                    "Autocenter URL": autocenter_url,
                    "Attachments": attachments
                }
                self._test_set_results[test_set_name].append(test_case_results)

        except Exception as err:
            self._log.exception(str(err))

    def _get_html_report(self, no_results=False):
        """Generates the html report

            Args:
                no_results   (bool)  -- if set returns no results html report

            Returns:
                (str)   --  html report

            Raises Exception:
                if failed to generate html report
        """
        try:
            # Create test result table headers list (S.No will be included by default)
            self.test_headers = [
                'Test Case ID',
                'Test Case Name',
                'Client Name',
                'Status',
                'Start Time',
                'End Time',
                'Summary']

            if self._commcell is None and self._inputs.get('commcell') is not None:
                if (self._inputs.get('commcell').get('commcellUsername') is not None
                        and self._inputs.get('commcell').get('commcellPassword') is not None):
                    self.test_headers = ['Operation', 'Status', 'Reason']

            # Create HTML Table
            html = HTMLReportGenerator()

            if no_results:
                return html.get_no_results_html()

            summary_details = dict()

            summary_details['StartTime'] = time.strftime(
                '%Y-%m-%d %H:%M:%S', time.localtime(self._start_time))
            summary_details['EndTime'] = time.strftime(
                '%Y-%m-%d %H:%M:%S', time.localtime(self._end_time))
            summary_details['LogsLocation'] = self._log_dir

            log_file_path = "#"
            if self.controller.os_info == "WINDOWS":
                log_file_path = self.controller.get_unc_path(self._log_dir)

            summary_details['Logs'] = log_file_path

            if self._commcell:
                version = self._commcell.version.split('.')
                summary_details['Commcell'] = self._commcell.commserv_name
                summary_details['Service Pack'] = f'SP{version[1]}.{version[2]}'
            else:
                summary_details['Commcell'] = constants.NO_REASON
                summary_details['Service Pack'] = constants.NO_REASON

            summary_details['Controller'] = self.controller.machine_name

            html.add_summary(summary_details)

            html.create_table(self.test_headers, self._test_set_results, self._inputs)

            self._log.info("Successfully generated Test case results")

            # Return HTML as string
            email_content = html.get_html()
            return email_content

        except Exception as excp:
            error_message = "Failed to generate HTML report with error: {0}".format(excp)
            self._log.exception(error_message)
            return error_message

    def __get_result_in_table_format(self) -> str:
        """
        Returns the test case results in table format

        The table includes the following columns:
        - Test Case ID
        - Test Case Name
        - Status
        - Start Time
        - End Time
        - Total Time Taken

        Each testset will have its own table with the testset name as the table header.

        """
        from tabulate import tabulate  # external module, so importing here to avoid failure in other cases
        result_table_str = []  # list to store the formatted data for each testset

        try:
            # Iterate through each testset
            for testset_name, testset_results in self._test_set_results.items():
                headers = ["Test Case ID", "Test Case Name", "Status", "Start Time", "End Time", "Total Time Taken"]
                formatted_data = []
                for testcase in testset_results:
                    # Format the test case name for multiline support
                    name_lines = [testcase['Test Case Name'][i:i + 30] for i in range(0, len(testcase['Test Case Name']), 30)]
                    formatted_name = '\n'.join(name_lines)

                    # Calculate total time taken
                    start_time = datetime.strptime(testcase['Start Time'], '%Y-%m-%d %H:%M:%S')
                    end_time = datetime.strptime(testcase['End Time'], '%Y-%m-%d %H:%M:%S')
                    total_time_taken = str(end_time - start_time)

                    # Append formatted data to the list
                    formatted_data.append([
                        testcase['Test Case ID'],
                        formatted_name,
                        "PASSED ✅" if testcase['Status'] == 'PASSED' else "FAILED ❌",
                        testcase['Start Time'],
                        testcase['End Time'],
                        total_time_taken
                    ])

                formatted_str = "\n" + f"Testset: {testset_name}" + "\n" + tabulate(formatted_data, headers=headers,
                                                                                       tablefmt="fancy_grid") + "\n"
                result_table_str.append(formatted_str)
            return '\n'.join(result_table_str)
        except Exception as excp:
            error_message = "Failed to print test case results to console with error: {0}".format(excp)
            self._log.exception(error_message)

    def __update_receivers(self):
        """Updates the final set of recievers after parsing the testcase status"""
        try:
            extra_receivers = AUTOMATION_CONFIG.email.extra_receivers
        except AttributeError:
            extra_receivers = ''
        if extra_receivers:
            self._inputs["email"]['receiver'] = f"{self._inputs['email']['receiver']};{extra_receivers}"
        try:
            fail_only_receivers = self._inputs["email"]["notifyFailOnly"]
            assert isinstance(fail_only_receivers, list)
        except KeyError:
            self._log.debug("'notifyFailOnly' key is not found skipping...")
            return
        except AssertionError:
            self._log.error("'notifyFailOnly' key in input JSON should be an Array")
            return
        for testcase in itertools.chain(*self._test_set_results.values()):
            if testcase["Status"] == constants.FAILED:
                self._inputs["email"]['receiver'] = f"{self._inputs['email']['receiver']};{';'.join(fail_only_receivers)}"
                return

    def _get_client_names_for_subject(self):
        """Returns the target client names list for which the automation testcases were launched"""
        try:
            include_clients = (
                AUTOMATION_CONFIG.email.includeClientsInSubject and not self._inputs.get('email', {}).get('subject')
            )
        except AttributeError:
            # default to true
            include_clients = True

        # Get unique client names list and add it to the email subject
        client_names = set()
        if include_clients:
            for tc in itertools.chain(*self._test_set_results.values()):
                if 'Client Name' in tc:
                    client_names.add(tc['Client Name'])

        client_name = ''
        if len(client_names) > 0:
            client_name = ' [{0}]'.format(', '.join(client_names))
        
        return client_name

    def _get_attachments_list(self):
        """Returns the attachments for all automation testcases"""
        # Get unique file path attachments add it to mail
        file_paths = set()
        for tc in itertools.chain(*self._test_set_results.values()):
            if 'Attachments' in tc:
                file_paths |= set(tc['Attachments'])
        self._log.info(f"total attachments list: {file_paths}")
        return file_paths

    def _send_mail(self):
        """Sends an email to specified users."""
        if self._test_set_results:
            email_content = self._get_html_report()
        else:
            self._log.warning("No Test results were found.")
            email_content = self._get_html_report(no_results=True)

        self.__update_receivers()

        if not self._inputs['email']['receiver']:
            self._log.info("No email receivers found. Skipping email.")
            return
        
        if 'email' in self._inputs:
            if 'subject' in self._inputs['email']:
                subject = self._inputs['email']['subject']
            else:
                product_list = []
                for set_ in self._inputs["testsets"].keys():
                    testset_name = []
                    testset_name.append(self._inputs["testsets"][set_].get("TESTSET_PRODUCT_NAME", ""))
                    testset_name.append(self._inputs["testsets"][set_].get("TESTSET_OS_TYPE", ""))
                    testset_name.append(self._inputs["testsets"][set_].get("TESTSET_ADDITIONAL_PROP", ""))
                    testset_name.append(self._inputs["testsets"][set_].get("TESTSET_APPLICATION_VERSION", ""))
                    testsetname = ""
                    for index, name in enumerate(testset_name):
                        if index == 0:
                            testsetname = name
                        elif name != "" and name is not None:
                            testsetname = testsetname + "_" + name
                            
                    product_list.append(testsetname)

                subject = constants.EMAIL_SUBJECT + str(product_list)

            suite_status = '[SUCCESS] '
            for testcase in itertools.chain(*self._test_set_results.values()):
                if testcase["Status"] == constants.FAILED:
                    suite_status = '[FAILED] '
                    break

            # get the client names for the subject line
            client_name = self._get_client_names_for_subject()
            all_tc_attachments = self._get_attachments_list()

            subject = suite_status + subject + client_name
            mailer = Mailer(self._inputs['email'], self._commcell)
            mailer.mail(subject, email_content, attachments=all_tc_attachments)

        else:
            self._log.info("Email is not specified. Printing output to console")
            print(email_content)

    def _init_autocenter(self):
        """Intentionally left blank
        """
        try:
            acobject = None
            if AUTOMATION_DEFINES.AUTOCENTER_INPUT_TAG in self._inputs.keys():
                self._log.info("Initializing Autocenter based on input file.")
                from Autocenter import Autocenter as AC
                acobject = AC.Autocenter(
                    commcell=self._commcell,
                    user_input=self._inputs)
                self._log.info("Successfully initialized Autocenter.")

            setattr(self, AUTOMATION_DEFINES.AUTOCENTER_INPUT_TAG, acobject)

            return True
        except Exception as err:
            self._log.exception(str(err))
            setattr(self, AUTOMATION_DEFINES.AUTOCENTER_INPUT_TAG, None)
            return False

    def execute(self, input_json_file_path=None):
        """Starts the CVAutomation execution."""
        # Initialization steps - We must parse inputs BEFORE anything else.  DO not change this.
        self._start_time = int(time.time())
        self._read_args(input_json_file_path)

        self._initialize_logger()

        # add email receivers value to Mailer.RECEIVERS
        if 'email' in self._inputs:
            Mailer.RECEIVERS = self._inputs.get('email').get('receiver')

        # Check if we are running in testcase OR testset mode & what filters should be applied
        tc_filter = getattr(self, AUTOMATION_DEFINES.TESTCASE_LIST)
        ts_filter = getattr(self, AUTOMATION_DEFINES.TESTSET_LIST)
        if (AUTOMATION_DEFINES.JSON_TESTSET_CONFIG_KEY not in self._inputs or
                AUTOMATION_DEFINES.JSON_TESTSET_INPUT_KEY not in self._inputs):

            # Build dummy testsets for the requested testcase(s) and reform the JSON.
            # We must filter them here because conversion loads testcases and
            # perhaps we're filtering a testcase which fails to load.
            self._inputs = cvtestset.CVTestset.convert_json(self._inputs, tc_filter, ts_filter)

            # Check if the user wants to convert the JSON and save it.
            if getattr(self, AUTOMATION_DEFINES.CONVERT_INPUT, False):
                if getattr(self, AUTOMATION_DEFINES.JSON_OUT_PATH) is not None:
                    with open(getattr(self, AUTOMATION_DEFINES.JSON_OUT_PATH), 'w') as file:
                        json.dump(self._inputs, file)
                else:
                    # Print the conversion to command line
                    print(json.dumps(self._inputs))

        # Main execution Steps
        self._login_to_webconsole()
        if self._commcell is None and self._inputs.get('commcell') is not None:
            if (self._inputs.get('commcell').get('commcellUsername') is not None
                    and self._inputs.get('commcell').get('commcellPassword') is not None):
                try:
                    self._send_mail()
                except Exception as e:
                    self._log.error("An exception occurred while sending email: %s", str(e))
                    self._log.error(traceback.format_exc())
                self._exit_run()

        # Autocenter will be initialized based on input JSON requesting it.
        self._init_autocenter()

        # Setup the run with common required parameters
        self.setup()

        # Launch automation if this is NOT a convert operation.  Keep them separate.
        if not getattr(self, AUTOMATION_DEFINES.CONVERT_INPUT, False):
            self._run_testsets_threaded()

            self._end_time = int(time.time())
            # Final Step to send report
            try:
                self._send_mail()
            except Exception as e:
                self._log.error("An exception occurred while sending email: %s", str(e))
                self._log.error(traceback.format_exc())
            # Updates tst results to db
            self._update_results_to_db()
            # print execution status on console
            self._console_output()

        self._log.info("*" * 80)
        self._log.info(
            "%(boundary)s %(message)s %(boundary)s",
            {
                'boundary': "*" * 24,
                'message': "Automation Execution Finished "
            }
        )
        self._log.info("Logging out from CommServer")
        self._log.info("*" * 80)
        self._commcell.logout()

        self._exit_run()

    @property
    def lock(self):
        """Returns the global lock"""
        return self._lock

    @property
    def commserv_version(self):
        """Returns the cs version."""
        return self._commserv_version

    @commserv_version.setter
    def commserv_version(self, value):
        """Sets the cs version."""
        self._commserv_version = value

    @property
    def jobID(self):
        """Returns the workflow main job id."""
        return self._job_id

    @jobID.setter
    def jobID(self, value):
        """Sets the workflow main job id."""
        self._job_id = value

    @property
    def controller(self):
        """Returns the controller machine object"""
        if self._controller is None:
            self._controller = Machine()

        return self._controller

    def _update_results_to_db(self):
        """Updates the test case results to the DB """
        if not isinstance(self.jobID, int) or self.jobID <= 0:
            self._log.info("Job id is not set in the request. Skip updating results to db.")
            return

        results_dict = {
            "jobId": self.jobID,
            "startTime": self._start_time,
            "endTime": self._end_time,
            "servicePack": self._commcell.commserv_version,
            "testset": self._automation_results
        }
        response = self._commcell.request("POST", "Automation/UpdateResults", results_dict)
        if response and response.json():
            if response.json()['errorCode'] == 0:
                self._log.info("Successfully Updated results into DB.")
            else:
                error_message = response.json()['errorMessage']
                self._log.info(f"Failed to update results into DB.\n {error_message}")
                raise Exception(f"Failed to update results into DB.\n {error_message}")
        else:
            self._log.info(f"Updating results to DB failed!.\n {response.text}")
            raise Exception(f"Updating results to DB failed! \n Response: {response.text}")
    
    def _console_output(self):
        """function to print test case execution output on console"""
        if self._automation_results is not None:
            if getattr(self, AUTOMATION_DEFINES.JSON_OUT_CONSOLE, "False") == "True":
                print(self._automation_results)
            if getattr(self, AUTOMATION_DEFINES.JSON_OUT_FILE, None) is not None:
                with open(getattr(self, AUTOMATION_DEFINES.JSON_OUT_FILE), 'w') as fileobj:
                    fileobj.write(str(self._automation_results))

            if getattr(self, AUTOMATION_DEFINES.JSON_OUT_TABLE_CONSOLE, False):
                str_data = self.__get_result_in_table_format()
                print(str_data)
                self._log.info(str_data)

    def _exit_run(self):
        """Exits the run with the exit code"""
        exit_code = 0  # Passed
        for testcase in itertools.chain(*self._test_set_results.values()):
            if testcase["Status"] == constants.FAILED:
                exit_code = 1  # Failed
                break
        exit(exit_code)


if __name__ == "__main__":
    # If no arguments are passed print help message
    if len(sys.argv) <= 1:
        sys.argv.append('-h')

    # Create CVAuto object
    CVAUTOMATION = CVAutomation()

    CVAUTOMATION.execute()
