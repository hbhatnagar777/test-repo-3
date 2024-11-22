# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Base Class for all CV Testsets

CVTestset is the only class defined in this class

CVTestset: Base Class for executing Testsets.

CVTestset:
    __init__()                  --  initialize basic objects of a Testset

    populate_testcase_queue()   --  add all testcase(s) into the queue for a specific testset

    _testcase_processor()       --  thread worker which operates on the testcase queue

    start_testcase_threads()    --  starts worker threads which will populate the queue

    _update_qa()                --  updates the test case run status to the QA Center

    convert_json()              --  converts workflow JSON to testset based JSON

"""

from queue import Queue
from threading import current_thread

import socket
import os

from AutomationUtils.engweb_operations import EngWeb
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import commonutils
from AutomationUtils import defines as AUTOMATION_DEFINES

from . import logger
from . import constants
from . import defines as A_DEF


class CVTestset:
    """Base class for all the Testset(s)"""
    STATUS = {
        constants.PASSED: 0,
        constants.FAILED: 1,
        constants.SKIPPED: 2
    }

    def __init__(self, testsetNode, name, CVAutomation):
        """Initialize the Testset class object"""
        self._log = CVAutomation._log
        self.nodeInfo = testsetNode
        self.name = name
        self._product = None
        self._applicable_os = None
        self._appVer = None
        self._addProp = None
        self._autocenter_tsid = None
        self._controller_id = None
        self._tsid_status = None
        self.tcThreadCount = self.nodeInfo[A_DEF.JSON_TESTCASE_CONFIG_KEY].get(
            A_DEF.JSON_THREAD_COUNT_KEY, A_DEF.DEFAULT_TC_THREADS)
        self.tcUpdateQA = bool(self.nodeInfo[A_DEF.JSON_TESTCASE_CONFIG_KEY].get(
            A_DEF.JSON_TESTCASE_UPDATEQA_KEY, A_DEF.TC_UPDATE_QA))
        self._testcaseQ = None
        self.testcaseNode = self.nodeInfo[A_DEF.JSON_TESTCASE_INPUT_KEY]
        
        # test_case_collection = [(id,info),(id,info),...,(id,info)]
        if isinstance(self.testcaseNode, list):
            self.test_case_collection = [item for case in self.testcaseNode for item in case.items()]
        else:
            self.test_case_collection = self.testcaseNode.items()
        
        self.CVAutomation = CVAutomation 

        # Set the parameters from the JSON
        self.product = self.nodeInfo[A_DEF.TS_PRODUCT_NAME]
        self.applicable_os = self.nodeInfo[A_DEF.TS_OS_TYPE]
        self.appVer = testsetNode.get(A_DEF.TS_APP_VER, None)
        self.addProp = testsetNode.get(A_DEF.TS_ADD_PROP, None)
        self.autocenter_tsid = testsetNode.get(A_DEF.TS_ID, None)
        self.controller_id = testsetNode.get(A_DEF.TS_CONTROLLER_ID, None)
        if self.CVAutomation.autocenter is not None and self.CVAutomation.autocenter.request_id is not None:
            self.request_id = self.CVAutomation.autocenter.request_id
        else:
            self.request_id = None
        self._test_case_results = list()

    def populate_testcase_queue(self):
        """Reads all testcase(s) in the input JSON and
            places it into the testcase queue for this testset.

        """
        # Check if this testcase needs to be filtered.
        tcFilter = [x.lower() for x in getattr(self.CVAutomation, A_DEF.TESTCASE_LIST, [])]
        
        for testcase, testcaseInfo in self.test_case_collection:
            if len(tcFilter) > 0:
                if testcase.lower() not in tcFilter:
                    self._log.warning(
                        f"Testcase [{testcase}] was not selected for execution, skipping it!"
                    )
                    continue

            self._log.info(f"Queuing testcase [{testcase}] for testset [{self.name}].")
            self.testcaseQ.put((testcase, testcaseInfo), block=True)

    def _testcase_processor(self, threadID, q):
        """This is a worker thread which runs the actual testcase(s) in the testset.
            It waits until something has been added into the queue.

            Args:
                threadID    (str)       --  The unique ID of this thread.

                    Example: 87b858b4-fa2c-11e7-8579-005056840332

                q           (Queue)     --  The queue which all threads are operating on.

        """
        while True:
            """
                tcID (str) - id of the testcase being run

                tcinputs (OrderedDict) - the testcase inputs from the input JSON file.
            """
            tcID, tcinputs = q.get()
            self._log.info("Executing testcase [{0}] in testset [{1}].".format(tcID, self.name))

            # Set the current thread to the current testcase ID.
            current_thread().name = str(tcID)

            try:
                # Load up the requested testcase object.

                # We must take control of the global lock
                # to avoid any race condition while searching for the module.

                # This becomes an issue when running the same testcase
                # at the same time in multiple testset threads.

                # When the testcase class is found, it's added to sys.modules.
                # You must use the sys.modules if it

                # Acquiring the lock prevents that race condition and allows finding to work.

                with self.CVAutomation.lock:
                    # test_case is an instance of the TestCase class by tcID.
                    test_case = CVTestCase.loadTestcaseObject(tcID)

                # Set some properties on the testcase.
                test_case.id = tcID
                test_case.commcell = self.CVAutomation._commcell
                test_case.log_dir = self.CVAutomation._log_dir
                test_case.csdb = self.CVAutomation._csdb
                test_case.tsName = self.name
                test_case.inputJSONnode[A_DEF.JSON_COMMCELL_INPUT_KEY] = getattr(
                    self, A_DEF.COMMCELL_NODE)
                test_case.inputJSONnode[A_DEF.JSON_EMAIL_INPUT_KEY] = \
                    self.CVAutomation._inputs[A_DEF.JSON_EMAIL_INPUT_KEY]
                test_case.addProp = self.addProp
                test_case.jobID = self.CVAutomation.jobID
                test_case.update_qa = self.tcUpdateQA

                # Validate if all the required testcase inputs are specified
                for tc_input in test_case.tcinputs:
                    if tc_input not in tcinputs:
                        raise Exception(
                            '{0} is a required input for {1} test case. Please add it.'.format(
                                tc_input, tcID)
                        )

                test_case.tcinputs = tcinputs
                if self.CVAutomation.autocenter is not None:
                    if "skipifTSfailed" in self.nodeInfo:
                        skip_testset_name = self.nodeInfo.get("skipifTSfailed", "")
                        if skip_testset_name and len(self.CVAutomation._test_set_results) > 0:
                            for skiptestset in skip_testset_name.split(','):
                                findfailed = self.CVAutomation._test_set_results.get(skiptestset, None)
                                if findfailed is not None and test_case.status != constants.SKIPPED:
                                    for value in findfailed:
                                        if 'Status' in value:
                                            tcstatus = value.get('Status', "")
                                            if tcstatus == constants.FAILED:
                                                test_case.status = constants.SKIPPED
                                                test_case.result_string = ""
                                                break

                if 'skipIfTCIDfailed' in self.nodeInfo:
                    skipIfTCIDfailed = self.nodeInfo['skipIfTCIDfailed']
                    if skipIfTCIDfailed and len(self._test_case_results) > 0:
                        for skipIDIterItem in skipIfTCIDfailed.split(','):
                            for iterItem in self._test_case_results:
                                if ('status' in str(iterItem)) and (
                                        str(skipIDIterItem) == str(iterItem['testcaseId'])
                                        and iterItem['status'] == CVTestset.STATUS[constants.FAILED]):
                                    self._log.info(
                                        "\n[TestSet : " +
                                        self.name +
                                        " ; TestCase : " +
                                        tcID +
                                        " ] = SKIPPED because test case " +
                                        str(skipIDIterItem) +
                                        " failed and ANSWERS_JSON_FILE_require skipIfTCIDfailed to be set\n")
                                    test_case.status = constants.SKIPPED
                if test_case.status != constants.SKIPPED:
                    if self.CVAutomation.autocenter is not None:
                        from Autocenter import defines as ac_define
                        self.CVAutomation.autocenter.updatetc_status(self.autocenter_tsid, str(
                            test_case.id), self.controller_id, ac_define.AC_RUNNING)  # Status 3=Running\Active
                        monitor = self.CVAutomation.autocenter.monitortc_runtime(
                            int(self.autocenter_tsid), str(test_case.id), self.controller_id)
                        test_case.autocenter = self.CVAutomation.autocenter
                        with monitor:
                            test_case.execute()
                        # Launch the testcase
                    else:
                        test_case.execute()

                self.CVAutomation._update_test_results(
                    tcID,
                    test_case.name,
                    test_case.status,
                    test_case.result_string,
                    test_case.tcinputs.get('ClientName', None),
                    test_case.tsName,
                    test_case.start_time,
                    test_case.end_time,
                    self.request_id,
                    self.autocenter_tsid,
                    test_case.attachments
                )

                self._test_case_results.append({
                    "testcaseId": int(tcID),
                    "summary": test_case.result_string.replace("'", "''"),
                    "status": CVTestset.STATUS[test_case.status],
                    "attachments": test_case.attachments
                })

                if self.CVAutomation.autocenter is not None:
                    if test_case.status == constants.FAILED or test_case.status == constants.SKIPPED:
                        self.tsid_status = ac_define.AC_FAIL
                    elif self.tsid_status != ac_define.AC_FAIL and test_case.status == constants.PASSED:
                        self.tsid_status = ac_define.AC_PASS
                    else:
                        self.tsid_status = ac_define.AC_FAIL

                self._log.info(
                    "Testcase [{0}] in testset [{1}] [{2}].".format(
                        tcID, self.name, test_case.status))
            except Exception as excp:
                # This is not a testcase exception, this is exception launching.
                error_message = "Failed to run testcase with error: {0}".format(excp)
                self._log.exception(error_message)
                test_case.status = constants.FAILED
                self.CVAutomation._update_test_results(
                    tcID,
                    constants.NO_REASON,
                    constants.FAILED,
                    error_message,
                    test_case.tcinputs.get('ClientName', None),
                    test_case.tsName,
                    test_case.start_time,
                    test_case.end_time,
                    self.request_id,
                    self.autocenter_tsid,
                    test_case.attachments
                )
                self._test_case_results.append({
                    "testcaseId": int(tcID),
                    "summary": error_message,
                    "status": CVTestset.STATUS[constants.FAILED],
                    "attachments": test_case.attachments
                })

            finally:
                self._update_qa(
                    test_case,
                    self.autocenter_tsid,
                    test_case.log_dir,
                    self.controller_id)

            # We have finished processing 1 testcase in this testset.
            # Erase the testcase name from the thread to avoid confusion.
            current_thread().name = None
            q.task_done()

    def start_testcase_threads(self):
        """Starts n number of worker threads to process testcase(s).
            Creates 1 queue for all testcases in the testset.

            The threads will all operate on the same queue to execute a testcase.

            _testcase_processor method handles the testcase execution.
        """

        self._log.info("[{0}] testcase execution thread(s) starting for testset[{1}]. ".format(
            self.tcThreadCount, self.name))

        # Create 1 testcase queue for each and every testset.
        tcQueue = Queue()
        commonutils.threadLauncher(self.tcThreadCount, tcQueue, self._testcase_processor)

        self.testcaseQ = tcQueue

    def _update_qa(self, test_case, ts_id=None,
                   log_dir=None, controller_id=None):
        """Updates the status of the Test Case run to the Quality Assurance Center (QA).

            Gets the verison and service pack installed on the CommServ.

            CVTestset Attributes:

                product                 --  product / agent the test case belongs to

                applicable_os           --  OS type, the test case is written for

                application_version     --  version of the application the test case is written for

                additional_properties   --  additional properties for the test case, if any

            Product is a required attribute. Other attributes are optional.

            Args:
                test_case   (object)    --  instance of the TestCase class

            Returns:
                None

            Raises:
                Exception:
                    if the test case is marked as SKIPPED

                    if failed to update QA with the test case run status

        """
        try:

            if self.CVAutomation.autocenter is not None:
                from Autocenter import defines as ac_define
                if test_case.status == constants.FAILED or test_case.status == constants.SKIPPED:
                    self.CVAutomation.autocenter.updatetc_status(
                        ts_id, str(
                            test_case.id), controller_id, ac_define.AC_FAIL)  # Status 2=Failed
                    try:
                        self.CVAutomation.autocenter.upload_runlog(
                            ts_id, test_case.id, log_dir)
                    except Exception as exp:
                        self._log.error("Unable to copy logs to Autocenter")
                else:
                    self.CVAutomation.autocenter.updatetc_status(
                        ts_id, str(
                            test_case.id), controller_id, ac_define.AC_PASS)  # Status 1=Passed
            if self.tcUpdateQA:
                self._log.info("Updating QA")
            else:
                self._log.info("Not Updating QA")
                return
            
            try:
                engweb = EngWeb()
            except AttributeError as exp:
                self._log.warning('Entry missing in configuration file for updating QA\nError: %s', exp)
                return
            except ValueError:
                self._log.warning('Update QA values not populated in configuration file')
                return
            except Exception as exp:
                self._log.error(exp)
                return

            status = None
            # test = vars(test_case)

            if test_case.status == 'PASSED':
                status = 1
            elif test_case.status == 'FAILED':
                status = 0
            else:
                raise Exception('Test Case marked as SKIPPED. Not updating the QA DB.')

            # getting the IP address for the controller machine using the FQDN raises error
            # while getting the addr info for machines that are not part of a domain, but are
            # present only in the WORKGROUP
            # we should use the hostname for such machines to get the IP Address
            controller = None

            try:
                controller = socket.gethostbyname(socket.getfqdn())
            except socket.gaierror:
                controller = socket.gethostbyname(socket.gethostname())

            sp_version = test_case.tcinputs.get('ServicePack', None)
            cs_version = str(self.CVAutomation.commserv_version) if self.CVAutomation.commserv_version \
                else AUTOMATION_DEFINES.DEFAULT_CS_VERSION.replace('SP21', sp_version)

            test_case_run_comments = """
            Automation Controller: {0}
            CommServ Name: {1}
            Web Console: {2}
            CommServ Version: {3}
            """.format(
                controller,
                getattr(self.CVAutomation._commcell, 'commserv_name', 'None'),
                self.CVAutomation._inputs['commcell'][
                    'webconsoleHostname'] if 'commcell' in self.CVAutomation._inputs.keys() else 'Dummy_CS',
                cs_version
            )
            try:
                if self.CVAutomation._inputs.get('testsets', {}).get(self.name, {}).get('TESTSET_ID') is None:
                    self.CVAutomation._inputs['testsets'][self.name]['TESTSET_ID'] = engweb.get_testset_id(
                        cs_version + "_" + self.name)
            except Exception as excp:
                self._log.error('Failed to get testset id')
            self._log.info('Test Set Name: %s', self.name)
            self._log.info('Test Case ID: %s', test_case.id)
            self._log.info('Test Case Status: %s', status)
            self._log.info('Comments: %s', test_case_run_comments)

            engweb.update_qa(cs_version + "_" + self.name, test_case.id, status, test_case_run_comments)

        except Exception as excp:
            self._log.error('Failed to Update QA with test case status')
            self._log.exception('Error: %s', excp)

    @staticmethod
    def convert_json(jsonInput, tcFilter=[], tsFilter=[]):
        """This takes the GUI / Workflow formated input JSON, reads, analyzes,
            and converts to a 'dummy' testset format, making necessary modifications.

            If either tcFilter or tsFilter are specified, first we remove the testcase(s),
            then if tsFilter is specified, we ignore any testset(s).

            If tsFilter is specified without tcFilter,
            then those testset(s) are run in their entirety.

            Args:
                jsonInput   (OrderedDict)   --  json input string received from the workflow
                that launches automation.

                tcFilter    (list)          --  list of specific testcase(s) to run,
                ignoring anything else in the input.

                tsFilter    (list)          --  list of specific testset(s) to run,
                ignoring anything else in the input.

            Returns:
                OrderedDict     -   the newly formated json output OrderedDict.

        """
        try:
            log = logger.getLog()
            tcInfo = jsonInput.pop(A_DEF.JSON_TESTCASE_INFO_KEY)
            jsonOutput = jsonInput

            # Check if we are working on specific testcase(s)
            if len(tcFilter) > 0:
                log.info(
                    "A testcase filter was selected, only running following testcase(s):" +
                    os.linesep +
                    ','.join(tcFilter))
                checkTC = True
            else:
                checkTC = False

            # Check if we are working on specific testset(s)
            if len(tsFilter) > 0:
                log.info(
                    "A testset filter was selected, only running following testset(s):" +
                    os.linesep +
                    ','.join(tsFilter))
                checkTS = True
            else:
                checkTS = False

            # Add the testset config key, for now just the number of threads
            jsonOutput[A_DEF.JSON_TESTSET_CONFIG_KEY] = {
                A_DEF.JSON_THREAD_COUNT_KEY: A_DEF.DEFAULT_TS_THREADS
            }

            dummyTestsets = {}
            for tc, inputs in tcInfo[A_DEF.JSON_TESTCASE_INPUT_KEY].items():
                if checkTC:
                    if tc not in tcFilter:
                        log.warning(
                            f"Testcase [{tc}] was not selected for execution, skipping it!"
                        )
                        continue

                # Load the testcase object
                test_case = CVTestCase.loadTestcaseObject(tc)

                """Setup the testset dummy node, using the properties set inside of the CVTestCase.
                    This name is used to update QA
                    This name is important, it's format is PRODUCT_OS_APPLICATION_PROPERTY.
                """
                tsName = "{0}_{1}_{2}_{3}".format(
                    test_case.product,
                    test_case.applicable_os,
                    test_case.appVer,
                    test_case.addProp)

                # Product AND OS are always set, remove the optional items from tsName
                tsName = tsName.replace(
                    "_" + A_DEF.TS_ADD_PROP_NOTSET, ""
                ).replace(
                    "_" + A_DEF.TS_APP_VER_NOTSET, ""
                )

                if checkTS:
                    if tsName.lower() not in [x.lower() for x in tsFilter]:
                        log.warning(
                            f"Testset [{tsName}] was not selected for execution, skipping it!"
                        )
                        continue

                dummyTestsets.setdefault(tsName, {A_DEF.TS_PRODUCT_NAME: test_case.product})

                dummyTestsets[tsName][A_DEF.TS_OS_TYPE] = test_case.applicable_os
                dummyTestsets[tsName][A_DEF.TS_APP_VER] = test_case.appVer
                dummyTestsets[tsName][A_DEF.TS_ADD_PROP] = test_case.addProp

                # Set the testcase config.
                dummyTestsets[tsName][A_DEF.JSON_TESTCASE_CONFIG_KEY] = {
                    A_DEF.JSON_TESTCASE_UPDATEQA_KEY: tcInfo[A_DEF.JSON_TESTCASE_UPDATEQA_KEY],
                    A_DEF.JSON_THREAD_COUNT_KEY: A_DEF.DEFAULT_TC_THREADS
                }

                # Get the testcases dictionary from the testset OR create if it does not exist
                tcDict = dummyTestsets[tsName].get(A_DEF.JSON_TESTCASE_INPUT_KEY, {})
                tcDict[tc] = inputs

                # If parallel execution is set to True, set testcase threads to number of
                # cases per this testset.
                if tcInfo.get(A_DEF.JSON_TESTCASE_PARALLEL, False):
                    dummyTestsets[tsName][A_DEF.JSON_TESTCASE_CONFIG_KEY][
                        A_DEF.JSON_THREAD_COUNT_KEY] = len(tcDict)

                dummyTestsets[tsName][A_DEF.JSON_TESTCASE_INPUT_KEY] = tcDict

            jsonOutput[A_DEF.JSON_TESTSET_INPUT_KEY] = dummyTestsets

            return jsonOutput

        except Exception as err:
            raise err

    @property
    def testcaseQ(self):
        """Returns the testcase queue for this testset"""
        return self._testcaseQ

    @testcaseQ.setter
    def testcaseQ(self, value):
        """Sets the testcase queue for this testset"""
        self._testcaseQ = value

    @property
    def name(self):
        """Returns the name of this test case."""
        return self._name

    @name.setter
    def name(self, value):
        """Sets the name of this test case."""
        self._name = value

    @property
    def product(self):
        """Returns the quality center product name."""
        return self._product

    @product.setter
    def product(self, product_name):
        """Sets the quality center product name."""
        self._product = product_name

    @property
    def applicable_os(self):
        """Returns the applicable operating system for this testset."""
        return self._applicable_os

    @applicable_os.setter
    def applicable_os(self, os_name):
        """Sets the applicable operating systems for this testset.
            Default value: self.os_list.WINDOWS
        """
        self._applicable_os = os_name

    @property
    def appVer(self):
        """Returns the quality center application version name."""
        return self._appVer

    @appVer.setter
    def appVer(self, appVer):
        """Sets the quality center application version name."""
        self._appVer = appVer

    @property
    def addProp(self):
        """Returns the quality center additional property name."""
        return self._addProp

    @addProp.setter
    def addProp(self, propName):
        """Sets the quality center additional property name."""
        self._addProp = propName

    @property
    def autocenter_tsid(self):
        """Returns the quality center additional property name."""
        return self._autocenter_tsid

    @autocenter_tsid.setter
    def autocenter_tsid(self, tsid):
        """Sets the quality center additional property name."""
        self._autocenter_tsid = tsid

    @property
    def controller_id(self):
        """Returns the autocenter controller id"""
        return self._controller_id

    @controller_id.setter
    def controller_id(self, controllerid):
        """Sets the the autocenter controller id."""
        self._controller_id = controllerid

    @property
    def tsid_status(self):
        """Returns the quality center additional property name."""
        return self._tsid_status

    @tsid_status.setter
    def tsid_status(self, status):
        """Sets the quality center additional property name."""
        self._tsid_status = status

    def get_test_case_details(self):
        """Returns test case results"""
        return self._test_case_results
