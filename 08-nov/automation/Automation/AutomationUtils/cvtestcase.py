# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2017 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Base Class for all CV TestCase's

CVTestCase is the only class defined in this class

CVTestCase: Base Class for executing Test Cases.

CVTestCase:
    __init__()              --  initialize basic objects of a Test Case

    _initialize_logger()    --  initializes logger for a Test Case

    products_list()         --  list of commvault quality center products

    features_list()         --  list of commvault quality center features

    os_list()               --  list of commvault quality center operating systems

    show_to_user()          --  flag to determine if the givn test case should be shown or hidden

    id()                    --  returns test case id

    name()                  --  returns test case name

    commcell()              --  returns CVPySDK Commcell object

    client()                --  returns the CVPySDK client object

    agent()                 --  returns the CVPySDK agent object

    instance()              --  returns the CVPySDK instance object

    backupset()             --  returns the CVPySDK backupset object

    subclient()             --  returns the CVPySDK subclient object

    product()               --  returns product name for which this test case will be
                                    executed

    applicable_os()         --  returns os name for which this test case will be
                                    executed

    tcinputs()              --  returns test case inputs

    log_dir()               --  returns log directory path

    feature()               --  returns the feature name for which this test case
                                    will be executed

    csdb()                  --  returns the commserv db object

    result_string()         --  returns the test case final result,
                                    user has to set this value at the end of test case

    status()                --  returns the final status of test case.

    setup()                 --  Setup function for the test case

    run()                   --  Run function for the test case

    tear_down()             --  Tear down function for the test case

    execute()               --  executes this Test Case

"""

from threading import current_thread

import os
import sys

from time import strftime, localtime
from AutomationUtils import commonutils

from . import logger
from . import constants
from . import qcconstants
from . import defines as A_DEF

from cvpysdk.commcell import Commcell

_TESTCASE_INFO = {}


class CVTestCase:
    """Base class for all the TestCase's"""

    def __init__(self):
        """Initialize the TestCase class object"""
        self._product = None
        self._products_list = qcconstants.Products
        self._features_list = qcconstants.Features
        self._os_list = qcconstants.OS
        self._show_to_user = False
        self._id = None
        self._name = None
        self._status = constants.PASSED
        self._result_string = constants.NO_REASON
        self._attachments = []
        self._tcinputs = {}
        self._commcell = None
        self._log_dir = None
        self._feature = None
        self._applicable_os = self.os_list.WINDOWS.value
        self._csdb = None
        self._client = None
        self._agent = None
        self._instance = None
        self._backupset = None
        self._subclient = None
        self._log = None
        self._tsName = None
        # Get the testcase thread ID it is running in to use it for later logging.
        self._tcTID = current_thread().ident  # current_thread().getName()
        self._app_ver = None
        self._add_prop = None
        self._inputJSONnode = {}
        self._jobID = None
        self.update_qa = False
        self._start_time = self._gethour_min_sec_string()
        self._end_time = self._gethour_min_sec_string()

    def _initialize_logger(self):
        """Initialize Logger for this Test Case"""
        if self.log_dir is None:
            self.log_dir = logger.get_log_dir()

        self.log = logger.Logger(self.log_dir, self.id, self.jobID).log

    def reinitialize_testcase_info(self):
        """Executes the test case"""
        try:
            self._initialize_logger()

            self.log.info("*" * 80)

            self.log.info("Started executing %s test case.", self.id)

            self.log.debug("Inputs to the test case are: %s", self.tcinputs)

            # Initialize the TestcaseInfo and save some of the info for later use.
            tcInfo = TestcaseInfo(self.tcTID)
            tcInfo.setInfo(A_DEF.TC_TCINFO_TESTCASE_NAME, self.name)
            tcInfo.setInfo(A_DEF.TC_TCINFO_TESTCASE_ID, self.id)

            # Clear existing objects from previous test case
            self.commcell.refresh()

            self.log.info("Create basic sdk objects if inputs are specified")

            # Initialize instance of the Client class, if the client name is provided in the JSON
            if 'ClientName' in self.tcinputs:
                self.log.info("Create client object for: %s", self.tcinputs['ClientName'])
                self._client = self.commcell.clients.get(self.tcinputs['ClientName'])

            # Initialize instance of the Agent class, if the client object is initialized
            # successfully, and agent name is given in the input JSON
            # If agent name is not given, assume the test case is not related to an Agent, but
            # has some operations specific to client
            if self._client is not None and 'AgentName' in self.tcinputs:
                self.log.info("Create agent object for: %s", self.tcinputs['AgentName'])
                self._agent = self._client.agents.get(self.tcinputs['AgentName'])

            # Continue to instance, backupset, and subclient object initialization, only if agent
            # object was created successfully
            # If agent object was created successfully, means the test case is for testing
            # functionality of the agent, and all objects till subclient should be initialized
            if self._agent is not None:
                # Create object of Instance, if instance name is provided in the JSON
                if 'InstanceName' in self.tcinputs:
                    self.log.info("Create instance object for: %s", self.tcinputs['InstanceName'])
                    self._instance = self._agent.instances.get(self.tcinputs['InstanceName'])

                # Create object of the Backupset class
                if 'BackupsetName' in self.tcinputs:
                    self.log.info("Creating backupset object for: %s",
                                  self.tcinputs['BackupsetName'])

                    # If instance object is not initialized, then instantiate backupset object
                    # from agent
                    # Otherwise, instantiate the backupset object from instance
                    if self._instance is None:
                        self._backupset = self._agent.backupsets.get(
                            self.tcinputs['BackupsetName']
                        )
                    else:
                        self._backupset = self._instance.backupsets.get(
                            self.tcinputs['BackupsetName']
                        )

                # Create object of the Subclient class
                if 'SubclientName' in self.tcinputs:
                    self.log.info("Creating subclient object for: %s",
                                  self.tcinputs['SubclientName'])

                    # If backupset object is not initialized, then try to instantiate subclient
                    # object from instance
                    # Otherwise, instantiate the subclient object from backupset
                    if self._backupset is None:
                        if self._instance is None:
                            pass
                        else:
                            self._subclient = self._instance.subclients.get(
                                self.tcinputs['SubclientName']
                            )
                    else:
                        self._subclient = self._backupset.subclients.get(
                            self.tcinputs['SubclientName']
                        )
        except Exception as exp:
            self.log.info("failed to reintialize testcase info")
            self.log.exception(exp)

    def execute(self):
        """Executes the test case"""
        try:
            self._initialize_logger()

            self.log.info("*" * 80)

            self.log.info("Started executing %s test case.", self.id)

            self.log.debug("Inputs to the test case are: %s", self.tcinputs)

            # Initialize the TestcaseInfo and save some of the info for later use.
            tcInfo = TestcaseInfo(self.tcTID)
            tcInfo.setInfo(A_DEF.TC_TCINFO_TESTCASE_NAME, self.name)
            tcInfo.setInfo(A_DEF.TC_TCINFO_TESTCASE_ID, self.id)

            # Clear existing objects from previous test case
            if self.commcell is not None:
                self.commcell.refresh()

            self.log.info("Create basic sdk objects if inputs are specified")

            # Initialize instance of the Client class, if the client name is provided in the JSON
            if 'ClientName' in self.tcinputs:
                self.log.info("Create client object for: %s", self.tcinputs['ClientName'])
                self._client = self.commcell.clients.get(self.tcinputs['ClientName'])

            # Initialize instance of the Agent class, if the client object is initialized
            # successfully, and agent name is given in the input JSON
            # If agent name is not given, assume the test case is not related to an Agent, but
            # has some operations specific to client
            if self._client is not None and 'AgentName' in self.tcinputs:
                self.log.info("Create agent object for: %s", self.tcinputs['AgentName'])
                self._agent = self._client.agents.get(self.tcinputs['AgentName'])

            # Continue to instance, backupset, and subclient object initialization, only if agent
            # object was created successfully
            # If agent object was created successfully, means the test case is for testing
            # functionality of the agent, and all objects till subclient should be initialized
            if self._agent is not None:
                # Create object of Instance, if instance name is provided in the JSON
                if 'InstanceName' in self.tcinputs:
                    self.log.info("Create instance object for: %s", self.tcinputs['InstanceName'])
                    self._instance = self._agent.instances.get(self.tcinputs['InstanceName'])

                # Create object of the Backupset class
                if 'BackupsetName' in self.tcinputs:
                    self.log.info("Creating backupset object for: %s",
                                  self.tcinputs['BackupsetName'])

                    # If instance object is not initialized, then instantiate backupset object
                    # from agent
                    # Otherwise, instantiate the backupset object from instance
                    if self._instance is None:
                        self._backupset = self._agent.backupsets.get(
                            self.tcinputs['BackupsetName']
                        )
                    else:
                        self._backupset = self._instance.backupsets.get(
                            self.tcinputs['BackupsetName']
                        )

                # Create object of the Subclient class
                if 'SubclientName' in self.tcinputs:
                    self.log.info("Creating subclient object for: %s",
                                  self.tcinputs['SubclientName'])

                    # If backupset object is not initialized, then try to instantiate subclient
                    # object from instance
                    # Otherwise, instantiate the subclient object from backupset
                    if self._backupset is None:
                        if self._instance is None:
                            pass
                        else:
                            self._subclient = self._instance.subclients.get(
                                self.tcinputs['SubclientName']
                            )
                    else:
                        self._subclient = self._backupset.subclients.get(
                            self.tcinputs['SubclientName']
                        )
            self.start_time = self._gethour_min_sec_string()
            self.log.info("Started executing %s Setup function", self.id)
            self.setup()

            self.log.info("Started executing %s Run function", self.id)
            self.run()

            self.log.info("Started executing %s Tear Down function", self.id)
            self.tear_down()            

        except Exception as exp:
            if self.log is not None:
                self.log.error("Test Case execution failed.")
                self.log.exception('Failed with error: %s', exp)

            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            self.end_time = self._gethour_min_sec_string()
            if self.log is not None:
                self.log.info("%s Test Case execution finished", self.id)
                # Remove the handler from the logger so we stop writing to the old file.
                self.log.handlers = []

    @staticmethod
    def locateTestcase(testcase):
        """Find the testcase.  It can only be a System OR User created / custom testcase.
            Args:
                testcase(str): the testcase id from the input json

            Returns:
                tuple: The path of the testcase and type, if its a system created or user created.
        """
        testcaseType = None
        path_ = None
        if os.path.exists(os.path.join(constants.TESTCASE_SYSTEM_DIR, testcase + '.py')):
            path_ = os.path.join(constants.TESTCASE_SYSTEM_DIR, testcase + '.py')
            testcaseType = constants.TESTCASE_SYSTEM_TYPE
        elif os.path.exists(os.path.join(constants.TESTCASE_CUSTOM_DIR, testcase + '.py')):
            path_ = os.path.join(constants.TESTCASE_CUSTOM_DIR, testcase + '.py')
            testcaseType = constants.TESTCASE_USER_TYPE
        elif os.path.exists(os.path.join(constants.TESTCASE_VIRTUAL_SERVER_DIR, testcase + '.py')):
            path_ = os.path.join(constants.TESTCASE_VIRTUAL_SERVER_DIR, testcase + '.py')
            testcaseType = constants.TESTCASE_USER_TYPE
        else:
            # No testcase found, decide what to do later.
            pass
        return (path_, testcaseType)

    @staticmethod
    def loadTestcaseObject(testcase):
        """Load a CVTestCase object based on the testcase id
            Args:
                testcase(str): the testcase id from input json

            Returns:
                CVTestCase: initialzied and loaded testcase module.

        """
        (path_, testcaseType) = CVTestCase.locateTestcase(testcase)

        # TODO: decide what to do if testcase is missing...exception for now.

        # Load TestCase class from the testcase.py file
        # NEVER REMOVE THIS, IT IS CRITICAL TO MULTIPROCESSING\THREADING
        sys.path.append(os.path.dirname(os.path.realpath(path_)))
        module = commonutils.import_module(os.path.dirname(os.path.realpath(path_)), testcase)

        # Init the testcase and set some properties
        test_case_class = getattr(module, constants.TEST_CASE_CLASS_NAME)
        test_case = test_case_class()

        return test_case

    @property
    def products_list(self):
        """List of supported products in commvault quality center database"""
        return self._products_list

    @property
    def features_list(self):
        """List of supported features in commvault quality center database"""
        return self._features_list

    @property
    def os_list(self):
        """List of supported operating systems in commvault quality center database"""
        return self._os_list

    @property
    def show_to_user(self):
        """Test case flag to determine if the specified test case is to be shown to user or not"""
        return self._show_to_user

    @show_to_user.setter
    def show_to_user(self, flag):
        """Sets the show to user flag for this test case.
            show_to_user flag determines if the test case is to be shown to user or not

            Allowed values: True/ False
            Default: False
        """
        if not isinstance(flag, bool):
            raise Exception("show_to_user accepts only boolean values")

        self._show_to_user = flag

    @property
    def id(self):
        """Returns the id of this test case."""
        return self._id

    @id.setter
    def id(self, value):
        """Sets the id of this test case."""
        self._id = value

    @property
    def tcTID(self):
        """Returns the unique thread ID of this test case."""
        return self._tcTID

    @tcTID.setter
    def tcTID(self, value):
        """Sets the unique thread ID test case."""
        self._tcTID = value

    @property
    def name(self):
        """Returns the name of this test case."""
        return self._name

    @name.setter
    def name(self, value):
        """Sets the name of this test case."""
        self._name = value

    @property
    def commcell(self) -> Commcell:
        """Returns the CVPySDK commcell object."""
        return self._commcell

    @commcell.setter
    def commcell(self, value):
        """Sets the CVPySDK commcell object."""
        self._commcell = value

    @property
    def client(self):
        """Returns the CVPySDK client object."""
        if self._client is None:
            raise Exception('Client object not initialized')

        return self._client

    @client.setter
    def client(self, value):
        """Sets the CVPySDK client object."""
        self._client = value

    @property
    def agent(self):
        """Returns the CVPySDK agent object."""
        if self._agent is None:
            raise Exception('Agent object not initialized')

        return self._agent

    @agent.setter
    def agent(self, value):
        """Sets the CVPySDK agent object."""
        self._agent = value

    @property
    def instance(self):
        """Returns the CVPySDK instance object."""
        if self._instance is None:
            raise Exception('Instance object not initialized')

        return self._instance

    @instance.setter
    def instance(self, value):
        """Sets the CVPySDK instance object."""
        self._instance = value

    @property
    def backupset(self):
        """Returns the CVPySDK backupset object."""
        if self._backupset is None:
            raise Exception('Backupset object not initialized')

        return self._backupset

    @backupset.setter
    def backupset(self, value):
        """Sets the CVPySDK backupset object."""
        self._backupset = value

    @property
    def subclient(self):
        """Returns the CVPySDK subclient object."""
        if self._subclient is None:
            raise Exception('Subclient object not initialized')

        return self._subclient

    @subclient.setter
    def subclient(self, value):
        """Sets the CVPySDK subclient object."""
        self._subclient = value

    @property
    def product(self):
        """Returns the quality center product name."""
        return self._product

    @product.setter
    def product(self, product_name):
        """Sets the quality center product name."""
        if not isinstance(product_name, self.products_list):
            raise Exception("variable agent accepts only enum - CVTestCase.products_list")

        self._product = product_name.value

    @property
    def applicable_os(self):
        """Returns the applicable operating system for this test case."""
        return self._applicable_os

    @applicable_os.setter
    def applicable_os(self, os_name):
        """Sets the applicable operating systems for this test case.
            Default value: self.os_list.WINDOWS
        """
        if not isinstance(os_name, self.os_list):
            raise Exception("variable os accepts only enum - CVTestCase.os_list")
        self._applicable_os = os_name.value

    @property
    def tcinputs(self):
        """Returns the dict of inputs generated for this test case."""
        return self._tcinputs

    @tcinputs.setter
    def tcinputs(self, value):
        """Sets the test case inputs dict for this test case.

            By default below dict will be appended
            default_dict = {
                "ClientName": "dummyclient",
                "AgentName": "dummyAgent",
                "InstanceName": "dummyInstance",
                "BackupsetName": "dummyBackupset",
                "SubclientName": "dummySubclient"
            }
        """
        self._tcinputs = value

    @property
    def log_dir(self):
        """Returns the log directory path for this test case."""
        return self._log_dir

    @log_dir.setter
    def log_dir(self, value):
        """Sets the log directory path for this test case."""
        self._log_dir = value

    @property
    def log(self):
        """Returns the log for this test case."""
        return self._log

    @log.setter
    def log(self, value):
        """Sets the log for this test case."""
        self._log = value

    @property
    def csdb(self):
        """Returns the CommServ Database object."""
        return self._csdb

    @csdb.setter
    def csdb(self, value):
        """Sets the CommServ Database object as a property."""
        self._csdb = value

    @property
    def tsName(self):
        """Returns the testset name if launched by a testset."""
        return self._tsName

    @tsName.setter
    def tsName(self, value):
        """Sets the testset name as a property."""
        self._tsName = value

    @property
    def feature(self):
        """Returns the quality center feature name."""
        return self._feature

    @feature.setter
    def feature(self, feature_name):
        """Sets the quality center feature name."""
        if not isinstance(feature_name, self.features_list):
            raise Exception("variable feature accepts only enum - CVTestCase.feature_list")
        self._feature = feature_name.value

    @property
    def start_time(self):
        """Returns the test case execution start time"""
        return self._start_time

    @start_time.setter
    def start_time(self, value):
        """Sets the test case execution start time"""
        self._start_time = value

    @property
    def end_time(self):
        """Returns the test case execution end time"""
        return self._end_time

    @end_time.setter
    def end_time(self, value):
        """Sets the test case execution end time"""
        self._end_time = value

    @property
    def result_string(self):
        """Returns the final result string of this test case"""
        return self._result_string

    @result_string.setter
    def result_string(self, value):
        """Sets the final result string of this test case"""
        self._result_string = value

    @property
    def attachments(self):
        """Returns the attachments to be sent by this test case"""
        return self._attachments

    @attachments.setter
    def attachments(self, value):
        """Sets the attachments to be sent this test case"""
        self._attachments = value

    @property
    def status(self):
        """Returns the final status of this test case."""
        return self._status

    @status.setter
    def status(self, value):
        """Sets the final status of this test case.

            Args:
                value   (str)   --  Test Case status

                    Valid values:
                        constants.PASSED

                        constants.FAILED

                        constants.SKIPPED

        """
        self._status = value

    @property
    def addProp(self):
        """Returns the additional property of this test case."""
        if self._add_prop is None:
            return A_DEF.TS_ADD_PROP_NOTSET
        else:
            return self._add_prop

    @addProp.setter
    def addProp(self, value):
        """Sets the additional property of this test case."""
        self._add_prop = value

    @property
    def appVer(self):
        """Returns the application version of this testcase."""
        if self._app_ver is None:
            return A_DEF.TS_APP_VER_NOTSET
        else:
            return self._app_ver

    @appVer.setter
    def appVer(self, value):
        """Sets the application version."""
        self._app_ver = value

    @property
    def inputJSONnode(self):
        """Returns dictionary of input node(s)"""
        return self._inputJSONnode

    @inputJSONnode.setter
    def inputJSONnode(self, value):
        """Sets the inputJSONnode version."""
        self._inputJSONnode = value

    @property
    def jobID(self):
        """Returns the workflow main jobID."""
        return self._jobID

    @jobID.setter
    def jobID(self, value):
        """Sets the workflow main jobID."""
        self._jobID = value

    def setup(self):
        """Setup function of test case"""
        pass

    def run(self):
        """Run Function of the test case"""
        pass

    def tear_down(self):
        """Tear down function of test case"""
        pass

    def _gethour_min_sec_string(self):
        """
        returns a String with current date in <yyyy>-<mm>-<dd> format
        """
        return strftime("%Y-%m-%d %H:%M:%S", localtime())


class TestcaseInfo:
    """ TestcaseInfo class holds information about a running instance of a testcase.
    This information is UNIQUE based on the thread ID of the running testcase.

    There is a global _TESTCASE_INFO dictionary which uses GUID as the key.

    The GUID's are created when a testcase thread is launched, and CVTestCase object is initialized for that thread.

    Therefore it is safe to assume every GUID is unique PER instance of a running testcase, even if the same testcase is running
     for multiple testsets.
    """

    def __init__(self, testcaseGUID):
        global _TESTCASE_INFO
        self.testcaseGUID = testcaseGUID

        _TESTCASE_INFO[self.testcaseGUID] = {}

    def setInfo(self, key, value):
        global _TESTCASE_INFO

        # Get the info dict for this GUID, if not, get an empty one (this should
        # never happen, unless someone initialized incorrectly).
        info = _TESTCASE_INFO.get(self.testcaseGUID, {})
        info[key] = value

        _TESTCASE_INFO[self.testcaseGUID] = info

    @staticmethod
    def getTestcaseID(guid):
        global _TESTCASE_INFO
        tcInfo = _TESTCASE_INFO.get(guid, {})

        return tcInfo.get(A_DEF.TC_TCINFO_TESTCASE_ID, None)
