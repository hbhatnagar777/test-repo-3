# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc .
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

r"""Main controller file for Running Commvault Automation with autocenter.

This file handles the initialization of Automation, including:

    1. initializing autocenter object

    2. Updates the test set / test cases status

"""

import os
import time
import datetime as dt
import threading

from AutomationUtils import logger
from AutomationUtils.database_helper import MSSQL
from AutomationUtils.mailer import Mailer
from AutomationUtils.machine import Machine

from . import AutocenterUtils
from . import defines as AC_Defines


class Autocenter(object):
    """Autocenter class for running automation using Autocenter"""

    def __init__(self, commcell=None, hushmode=False, maintmode=False, user_input=None):
        """initializes autocenter object
            @args

            commcell (object)     -- commcell object

            husmode (boolean)     --  hushmode as true or false

            maintmode (boolean)   -- autocenter running under maintenance mode (True) otherwise False

            user_input (json)          -- user input information

        """

        self.commcell = commcell
        self.log = logger.getLog()
        self._input = user_input
        self._input_json_node = None
        self._logloc = ""
        self._testsetlist = []
        self._lockfile = AC_Defines.LOCKFILE_NAME
        self.logname = None
        self._request_id = None
        self._settings = {}
        self._config = None
        self._controllers = []
        self._emaillist = [AC_Defines.DEV_AUTOCENTER]  # This is the default list.
        self._status = -1
        self._resumed = None
        self.hushmode = hushmode
        self.pid = str(os.getpid())
        self._latestlog = None
        self.maintenance = maintmode
        self._controller_id = None
        self.autocenter_password = None
        self._updateinput()

        try:
            if not hushmode:
                self.log.info("Loading Autocenter configuration.")
            self._get_config()
            # Get & set the settings.
            if not hushmode:
                self.log.info("Setting custom automation settings.")
            self.setautomationsettings()
            # Get & set the controller machines.
            if not hushmode:
                self.log.info("[AUTOMATION_CENTER: INIT]\tSet controller machines.")

            # Load up the defines and modify any automation constants for this run
            if not hushmode:
                self.log.info(
                    "[AUTOMATION_CENTER: INIT]\tModify constants for automation customs.")

        except Exception as err:
            self.log.error(str(err))
            raise

    @property
    def inputjsonnode(self):
        """Returns dictionary of input node(s)"""
        return self._inputjsonnode

    @inputjsonnode.setter
    def inputjsonnode(self, value):
        """Sets the inputjsonnode version."""
        self._inputjsonnode = value

    @property
    def settings(self):
        """Returns controller settings"""
        return self._settings

    @settings.setter
    def settings(self, key, value):
        """Sets the controller settings"""
        self._settings[key] = value

    @property
    def emaillist(self):
        """Returns emaillist """
        return self._emaillist

    @emaillist.setter
    def emailist(self, value):
        """Sets the controller settings"""
        self._emaillist = value

    @property
    def controller(self):
        """Returns controller settings"""
        return self._controller

    @controller.setter
    def controller(self, value):
        """Sets the controller settings"""
        self._controller = value

    @property
    def request_id(self):
        """Returns controller settings"""
        return self._request_id

    @request_id.setter
    def request_id(self, value):
        """Sets the controller settings"""
        self._request_id = value

    @property
    def logloc(self):
        """Returns controller settings"""
        return self._latestlog

    @logloc.setter
    def logloc(self, value):
        """Sets the controller settings"""
        self._latestlog = value

    @property
    def status(self):
        """Returns controller settings"""
        return self._status

    @status.setter
    def status(self, value):
        """Sets the controller settings"""
        self._status = value

    @property
    def ts_id(self):
        """Returns controller settings"""
        return self._ts_id

    @ts_id.setter
    def ts_id(self, value):
        """Sets the controller settings"""
        self._ts_id = value

    @property
    def controllers(self):
        """Returns controller settings"""
        return self._controllers

    @controllers.setter
    def controllers(self, value):
        """Sets the controller settings"""
        self._controllers = value

    @property
    def controller_id(self):
        """Returns controller settings"""
        return self._controller_id

    @controller_id.setter
    def controller_id(self, value):
        """Sets the controller settings"""
        self._controller_id = value

    def setautomationsettings(self):
        """Returns controller settings"""
        try:
            # "{CALL getTSinfoForQA (?)}", (259))
            results = self.execute_automation_db_proc("EXEC dbo.getACsettings")

            if len(results.rows) > 0:
                for setting in results._rows:
                    settingname = setting[0]
                    settingval = setting[1]
                    self.settings[settingname] = settingval
            else:
                raise Exception(AC_Defines.FAILED_READ_SETTINGS_DB)
        except Exception as err:
            self.log.exception(str(err))
            raise

    def _updateinput(self):
        '''
        updates input to autocenter object
        '''
        try:
            autocenter_dict = self._input[AC_Defines.AUTOCENTER]

            if (AC_Defines.AC_HOST_MACHINE in autocenter_dict and AC_Defines.AC_USER_NAME
                    in autocenter_dict and AC_Defines.AC_PASSWORD in autocenter_dict and
                    AC_Defines.AC_REQUEST_ID in autocenter_dict and AC_Defines.AUTOCENTER_PASSWORD in autocenter_dict):
                self.log.info('Reading Controller information from the Input JSON')
                controller = autocenter_dict[AC_Defines.AC_HOST_MACHINE]
                user = autocenter_dict[AC_Defines.AC_USER_NAME]
                password = autocenter_dict[AC_Defines.AC_PASSWORD]
                self.request_id = autocenter_dict[AC_Defines.AC_REQUEST_ID]
                self.controller = Machine(controller, username=user, password=password)
                self.autocenter_password = autocenter_dict[AC_Defines.AUTOCENTER_PASSWORD]
                self.controller.name = autocenter_dict.get(AC_Defines.AC_MACHINE_NAME, controller)
            else:
                raise Exception(
                    "required input is not available or failed to create machine object")
        except Exception as err:
            self.log.exception(str(err))
            raise

    def _get_config(self):
        try:
            config_file_name = os.path.join(os.path.dirname(
                __file__), AC_Defines.CONFIG_FILE_NAME)
            configfile = AutocenterUtils.AC_ConfigParser()

            if not os.path.exists(config_file_name):
                raise Exception(AC_Defines.CONFIG_FILE_NOT_FOUND.format(config_file_name))
            configfile.read(config_file_name)

            setattr(self, 'DEFINES', configfile.as_dict())
            return
        except Exception as err:
            self.log.exception(str(err))
            raise

    def update_ts_status(self, ts_id, status, controller_id):
        """updates test set status"""
        try:
            if self.maintenance:
                # In maintenance mode, do nothing, there's no testsets
                return True
            if isinstance(status, type(None)):
                status = AC_Defines.AC_FAIL

            if not isinstance(ts_id, str) or not isinstance(status, int):
                if not isinstance(ts_id, type(None)):
                    self.log.error(
                        "[AUTOMATION_CENTER][updateTSstatus] TestsetID and"
                        " status must be integer type. Not setting DB info.")
                    # return False

            if ts_id is None:
                _query = ('EXEC dbo.updateTSrunStatus @requestID=' +
                          str(self.request_id) +
                          ',@testsetID=null,@status=N\'' +
                          str(status) +
                          '\'' +
                          ',@controllerID=' +
                          str(controller_id))
            else:
                _query = ('EXEC dbo.updateTSrunStatus @requestID=' +
                          str(self.request_id) + ',@testsetID=' + str(ts_id) +
                          ',@status=N\'' + str(status) + '\'' +
                          ',@controllerID=' + str(controller_id))

            if self.execute_db_query(_query):
                self.log.info(
                    "[AUTOMATION_CENTER][updateTSstatus] Successfully set "
                    "testset {} to status {} in DB".format(
                        str(ts_id), str(status)))
                # If the testset is PASSED, then mark the testset as VALID
                if status == AC_Defines.AC_PASS and not isinstance(ts_id, type(None)):
                    _query = 'EXEC dbo.markTSvalid @testsetID=' + str(ts_id)
                    if self.execute_db_query(_query):
                        self.log.info(
                            "[AUTOMATION_CENTER][updateTSstatus] Successfully marked"
                            " testset {} valid in DB.".format(str(ts_id)))
                    else:
                        self.log.error(
                            "[AUTOMATION_CENTER][updateTSstatus] Failed to mark "
                            "testset {} valid in DB.".format(str(ts_id)))

                return True
            self.log.error(
                "[AUTOMATION_CENTER][updateTSstatus] Failed setting testset {}"
                " to status {} in DB.".format(str(ts_id), str(status)))
            return False
        except Exception as err:
            self.log.exception(str(err))
            raise

    def execute_automation_db_proc(self, procname, *params, autocommit=True):
        """ executes autocenter db stored procedures"""
        try:
            dbinfo = self.DEFINES["DB_INFO"]
            if self.autocenter_password is None:
                password = dbinfo["password"]
            else:
                password = self.autocenter_password

            dbobject = MSSQL(**{"server": dbinfo["server"],
                                "user": dbinfo["username"],
                                "password": password,
                                "database": dbinfo["dbname"],
                                "autocommit": False,
                                "use_pyodbc": True})
            response = dbobject.execute_storedprocedure(procname, params, autocommit)

            if response._rows is None:
                return bool(response.rowcount == -1)
            else:
                return response

        except Exception as err:
            self.log.exception(str(err))
            raise

    def execute_db_query(self, query, data=None, autocommit=True):
        """executes autocenter db queries"""
        try:
            dbinfo = self.DEFINES["DB_INFO"]

            if self.autocenter_password is None:
                password = dbinfo["password"]
            else:
                password = self.autocenter_password

            dbobject = MSSQL(**{"server": dbinfo["server"],
                                "user": dbinfo["username"],
                                "password": password,
                                "database": dbinfo["dbname"],
                                "autocommit": False,
                                "use_pyodbc": True})
            response = dbobject.execute(query, data, autocommit)

            if response._rows is None:
                return bool(response.rowcount == -1)
            else:
                return response

        except Exception as err:
            self.log.exception(str(err))
            raise

    def update_run_logloc(self, ts_id, log_loc):
        """updates automation run log location to autocenter db"""
        try:
            if not isinstance(ts_id, str) or not isinstance(log_loc, str):
                self.log.error(
                    "[AUTOMATION_CENTER][updateRunLogLoc] TestsetID must be "
                    "integer type, logloc must be string. Not setting DB info.")
                return False

            # This is the location of logs from the CONTROLLER MACHINE

            _query = "UPDATE requestSelection SET sRunLogs='" + \
                     str(log_loc) + "' WHERE requestID=" + \
                     str(self.request_id) + " AND testsetID=" + str(ts_id)
            if not self.execute_db_query(_query):
                self.log.info(
                    "[AUTOMATION_CENTER][updateRunLogLoc] Successfully set "
                    "requestID {} testset {} logloc to {} in DB.".format(
                        str(self.request_id), str(ts_id), str(log_loc)))
                return True
            self.log.info(
                "[AUTOMATION_CENTER][updateRunLogLoc] Failed to set requestID"
                " {} testset {} logloc to {} in DB.".format(
                    str(self.request_id), str(ts_id), str(log_loc)))
            return False
        except Exception as err:
            self.log.exception(str(err))
            raise
    
    def run_schedule(self, schedule_id):
        """
        Runs a schedule.

        Args:
            schedule_id (int): The ID of the schedule.

        Returns:
            bool: True if the schedule was successfully executed, False otherwise.
        """
        try:
            query = f"EXEC dbo.runNowSchedule @user='precert', @nSchedID='{schedule_id}', @subAddr='precert@commvault.com'"
            response = self.execute_automation_db_proc(query)
            if len(response.rows) == 0:
                raise Exception(f"Unable to submit the request: {query}")
            else:
                return response.rows[0][0]
        except Exception as err:
            self.log.exception(str(err))
            raise
    
    def run_testset(self, testsetid):
        """
        Runs a test set.

        Args:
            testsetid (int): The ID of the testset.

        Returns:
            int: Returns autocenter request id.
        """
        try:
            query = f"""SET NOCOUNT ON
                DECLARE @input AS buildTeamRequestProp  --TYPE
                INSERT INTO  @input (name, value) VALUES ('batchID',15)
                INSERT INTO  @input (name, value) VALUES ('type','batch')
                INSERT INTO  @input (name, value) VALUES ('requester','sbandari')
                INSERT INTO  @input (name, value) VALUES ('alsoNotify','pkoti,sbandari')
 
                EXEC     [dbo].[SubmitRequest] @prop = @input, @user='precertuser', @tsList='{testsetid}', @subAddr='', @loop=0"""
            self.log.info(f"Executing the test set: {query}")
            response = self.execute_automation_db_proc(query)
            if len(response.rows) == 0:
                raise Exception(f"Unable to submit the request: {query}")
            else:
                return response.rows[0][0]
        except Exception as err:
            self.log.exception(str(err))
            raise

    def check_precert_status(self, request_id, max_attempts=20, wait_time=2, log=None):
        """
        Check the pre-certification run status of a given request.

        Args:
            request_id (int): The ID of the request to check.
            max_attempts (int): Maximum number of attempts to check the status. Default is 20.
            wait_time (int): Time to wait (in minutes) between each attempt if the status is still running. Default is 2 minutes.

        Returns:
            int: The final status code of the request.
        """
        if log is None:
            log = self.log
        attempts = 0
        request_status = -100
        while attempts <= max_attempts:
            try:
                request_status = self.precert_run_status(request_id)
                if request_status == 100:
                    log.info(f"Few test cases are still running for request id {request_id}, waiting for {wait_time} minutes")                
                    time.sleep(wait_time * 60)
                    attempts += 1
                elif request_status == -100:
                    log.info(f"Few test cases are failed in request : {request_id}")                
                    return request_status
                else:
                    log.info("Current return code for test set: %s", str(request_status))
                    return request_status
            except Exception as err:
                log.exception(str(err))
                return request_status
        log.info(f"Max attempts reached, returning the current status code {request_status} ")
        return request_status
            
    def precert_run_status(self, request_id):
        """
        Returns the precertification run status for a given request ID.

        Args:
            request_id (int): The ID of the request.

        Returns:
            bool: True if there are failed test cases, False otherwise.
        """
        try:
            query = "EXECUTE newprecertRunStatus ?"
            response = self.execute_automation_db_proc(query, request_id)
            if len(response.rows) == 0:
                return Exception(f"Unable to get the request status: {query}")
            else:
                return response.rows[0][0]
        except Exception as err:
            self.log.exception(str(err))
            raise 
    
    def upload_runlog(self, ts_id, testcase, log):
        '''
        uploades failed logs to autocenter

        @args:
            testcase (str) : failed test case number
            log      (str) : Log location of the failed test case.
        '''

        try:
            url = AC_Defines.WEB_UPLOAD_LOG_URL
            client_log_dir = log  # This is log location on client machine
            clienttestcaselog = os.path.join(client_log_dir, testcase + ".log")
            self.log.info(f"Client log location {clienttestcaselog}")
            request_id = self.request_id
            controllername = self.controller.name
            self.log.info(
                "[AUTOMATION_CENTER][uploadRunLog] Uploading [{}.log] to automationcenter,"
                " from controller {}, for testset {} and request {}.".format(
                    str(testcase), str(controllername), str(ts_id), str(request_id)))

            # Location to upload the log to.
            servertestcaselog = f"""{self.settings['WEBLOGS']}\\{controllername}\\{str(ts_id)}"""
            self.log.info(
                "[AUTOMATION_CENTER][uploadRunLog] Server log location {}.".format(
                    str(servertestcaselog)))

            # info to send back to the webserver
            data = {'location': servertestcaselog, 'requestID': str(request_id)}
            files = {'file': open(clienttestcaselog, 'rb')}
            flag, response = self.commcell._cvpysdk_object.make_request(
                'POST', url, files=files, payload=data)
            return flag
        except Exception as err:
            self.log.exception(str(err))
            raise

    def updatecontroller_splevel(self, ts_id):
        """Updates controller service pack to autocenter"""
        try:
            if not isinstance(ts_id, str):
                if not isinstance(ts_id, type(None)):
                    self.log.error(
                        "[AUTOMATION_CENTER][updateControllerSPlevel] TestsetID "
                        "must be integer type. Not setting DB info.")
                    return False

            try:
                updatelevel = 'SP' + self.commcell.version.split('.')[1]
            except:
                updatelevel = 'N/A'

            date = '0000000000'
            _query = 'EXEC dbo.updateControlllerSPlevel @testsetID=' + str(ts_id) \
                     + ',@requestID=' + str(self.request_id) + ',@updateLevel=N\'' + str(updatelevel) \
                     + '\',@updateDate=' + str(date)
            if not self.execute_db_query(_query):
                self.log.error(
                    "[AUTOMATION_CENTER][updateControllerSPlevel] Failed saving testset {}"
                    " sp information in DB.".format(str(ts_id)))
                return False
            return True
        except Exception as err:
            self.log.exception(str(err))
            raise

    def markts_alive(self, ts_id=None):
        """mark test set as alive in autocenter"""

        log = self.log
        try:
            delay = int(self.DEFINES["DB_INFO"]["connection_retry_second"])
            retryrrrors = self.DEFINES["DB_INFO"]["connection_error_ignore"].split(",")
            if isinstance(ts_id, type(None)):
                _query = 'EXEC dbo.markTSalive @requestID=' + \
                         str(self.request_id) + ',@testsetID=null'
            else:
                _query = 'EXEC dbo.markTSalive @requestID=' + \
                         str(self.request_id) + ',@testsetID=' + str(ts_id)

            while True:
                try:
                    if self.execute_db_query(_query):
                        log.info(
                            "[AUTOMATION_CENTER][markTSalive] Successfully "
                            "set testset {} alive in DB.".format(
                                str(ts_id)))
                except Exception as err:
                    log.error(
                        "[AUTOMATION_CENTER][markTSalive] Failed marking TS {}"
                        " alive, will re-try in {} seconds.".format(
                            str(ts_id), str(delay)))
                    time.sleep(delay)
                return True

        except Exception as err:
            log.exception(str(err))
            raise

    def healthcheck_thread(self, testset):
        """creates healthcheck thread for tetset"""

        try:
            class ThreadClass(threading.Thread):
                """ class for creating additional threads for monitoring"""
                exitflag = False

                def __init__(self, autocenter, ts_id):
                    super(ThreadClass, self).__init__()
                    self.autocenter = autocenter
                    self.log = autocenter.log
                    self.ts_id = ts_id
                    self.daemon = True

                def stop(self):
                    self.exitflag = True
                    try:
                        if self.isAlive():
                            self.log.info(
                                "[AUTOMATION_CENTER][Health_Thread] STOPPING.")
                    except Exception:
                        pass

                def __enter__(self):
                    self.start()
                    return self

                def __exit__(self, *args, **kwargs):
                    self.stop()
                    # print('Force set Thread Sleeper stop_event')

                def run(self):
                    try:
                        # Make sure the exitflag is not set.
                        if not self.exitflag:
                            self.log.info("[AUTOMATION_CENTER][Health_Thread] STARTING.")

                        while not self.exitflag:
                            self.autocenter.markts_alive(self.ts_id)

                            # Keep updating every 60 seconds.
                            time.sleep(60)

                    except Exception as err:
                        self.log.exception(str(err))
                        raise

            # Initialze the monitor thread
            monthread = ThreadClass(self, testset)  # send autocenter() & testsetID

            # Send the thread back to the caller once its running.
            return monthread
        except Exception as err:
            self.log.exception(str(err))
            raise

    def updatetc_status(self, ts_id, tc_id, controller_id, status):
        """ updates test case status to autocenter"""
        try:
            if self.maintenance:
                # Running in the maintenance mode
                ts_id = 'Maintenance ID:{0}'.format(self.request_id)
                _query = ('EXEC dbo.updateMaintTCstatus @nMaintID=' + str(self.request_id)
                          + ',@testcase=N\'' + str(tc_id) + '\',@status=' + str(status))
            else:
                if not isinstance(ts_id, str) or not isinstance(status, int) or \
                        not isinstance(tc_id, str):
                    self.log.error(
                        "[AUTOMATION_CENTER][updateTCstatus] TestsetID and status must"
                        " be integer type,testcaseID must be string. Not setting DB info.")
                    return False
                _query = ('EXEC dbo.updateTCstatus @requestID=' +
                          str(self.request_id) + ',@testsetID=' +
                          str(ts_id) + ',@testcase=N\'' + str(tc_id) +
                          '\',@status=N\'' + str(status) +
                          '\'' + ' ,@controllerid=' + str(controller_id))

            if self.execute_db_query(_query):
                self.log.info(
                    "[AUTOMATION_CENTER][updateTCstatus] Successfully set testset"
                    " {} testcase {} to status {} in DB.".format(
                        str(ts_id), str(tc_id), str(status)))
                return True
            self.log.error(
                "[AUTOMATION_CENTER][updateTCstatus] Failed setting testset {}"
                " testcase {} to status {} in DB.".format(
                    str(ts_id), str(tc_id), str(status)))
            return False
        except Exception as err:
            self.log.exception(str(err))
            raise

    def monitortc_runtime(self, ts_id, tc_id, controller_id):
        """monitors test case execution time"""

        try:

            class MonitorThread(threading.Thread):
                """class to create monitor thread"""
                exitflag = False

                def __init__(self, ts_id, tc_id, acobj, starttime, controller_id):
                    """initializes monitor therad"""
                    super(MonitorThread, self).__init__()
                    self.ts_id = ts_id
                    self.tc_id = tc_id
                    self.acobj = acobj
                    self.stime = starttime
                    self.log = acobj.log
                    self.daemon = True
                    self.controller_id = controller_id

                def __enter__(self):
                    """method to start the context manager thread"""
                    self.start()
                    return self

                def __exit__(self, *args, **kwargs):
                    """method to stop the context manager thread"""
                    self.stop()
                    # print('Force set Thread Sleeper stop_event')

                def stop(self):
                    """method to stop the thread"""
                    self.exitflag = True
                    try:
                        if self.isAlive():
                            self.log.info(
                                f"""[AUTOMATION_CENTER][TC_Monitor_Thread] Stop
                                 monitoring testcase {str(self.tc_id)}."""
                            )
                    except Exception:
                        pass

                def getalertscale(self, prevrunseconds):
                    """method to get alert scale"""
                    try:
                        alertscale = 1.00
                        if prevrunseconds >= 18000:  # greater than 5 hours
                            alertscale = 1.20
                        elif 14400 < prevrunseconds < 18000:  # 4 - 5 hours
                            alertscale = 1.25
                        elif 10800 < prevrunseconds < 14400:  # 3 - 4 hours
                            alertscale = 1.30
                        elif 7200 < prevrunseconds < 10800:  # 2 - 3 hours
                            alertscale = 1.35
                        elif 3600 < prevrunseconds < 7200:  # 1 - 2 hours
                            alertscale = 1.40
                        elif 1800 < prevrunseconds < 3600:  # 30m - 1hour
                            alertscale = 1.75
                        elif 60 < prevrunseconds < 1800:  # 30m - 1m
                            alertscale = 2.00
                        elif prevrunseconds <= 60:  # less than 1m
                            alertscale = 10.00

                        self.log.info(
                            "[AUTOMATION_CENTER][TC_Monitor_Thread] Using alert"
                            " threshold of {}percent based on previous runtime"
                            " of {}seconds.".format(str(alertscale), str(prevrunseconds)))

                        return alertscale
                    except Exception as err:
                        self.log.exception(str(err))
                        raise

                def gettcruninfo(self):
                    """gets test case run information"""
                    try:
                        _query = 'EXEC dbo.prevSuccessTCrunTime \'%s\', %s' % (
                            str(self.tc_id), str(self.ts_id))
                        runinfo = self.acobj.execute_automation_db_proc(_query)
                        if len(runinfo.rows) > 1:
                            self.log.warning(
                                "[AUTOMATION_CENTER][TC_Monitor_Thread] Too many"
                                " records returned by {}. EXITING!".format(str(_query)))
                            return {}  # return empty dictionary

                        if not len(runinfo.rows) == 1:
                            self.log.warning(
                                "[AUTOMATION_CENTER][TC_Monitor_Thread] Testcase"
                                " {} has never passed for testset {}. EXITING!".format(
                                    str(self.tc_id), str(self.ts_id)))
                            return {}  # return empty dictionary

                        # columns = [column[0] for column in runinfo.rows[0].cursor_description]

                        return dict(zip(runinfo.columns, runinfo.rows[0]))
                    except Exception as err:
                        self.log.exception(str(err))
                        raise

                def sendalert(self, ts_id, tc_id, currun_seconds, prevrun_time, alertnum):
                    """sends alert based on test case execution duration"""
                    try:
                        toaddress = self.acobj.get_failure_email_string(ts_id)
                        testsetname = self.acobj.execute_db_query(
                            "SELECT webname FROM alltestsets where"
                            " testsetID=" + str(ts_id), autocommit=False)
                        testsetname = testsetname.rows[0][0]
                        maildetails = {AC_Defines.RECEIVER: toaddress}
                        mailobj = Mailer(maildetails, commcell_object=self.acobj.commcell)
                        subject = "Automation Center [%s] ALERT - Testcase [%s]" \
                                  " Runtime threshold exceeded!" % (
                                      str(alertnum), str(tc_id))
                        body = """
                            <h2>WARNING - Runtime threshold exceeded.</h2><br><BR>
                            <TABLE border='1'>
                            <TR><TH>TestcaseID</TH><TH>TestsetID</TH><TH>Previous Runtime</TH><TH>Current Runtime</TH></TR>
                            <TR><TD>%s</TD><TD>%s (%s)</TD><TD>%s</TD><TD>%s</TD></TR>
                            </TABLE>
                            <BR>
                            <a href='http://autocenter.automation.commvault.com/server_side/scripts/testcaseStatus.php?requestID=%s&testsetID=%s'>
                            Run Status</a>
                        """ % (str(tc_id), str(testsetname), str(ts_id), str(prevrun_time),
                               str(currun_seconds), str(self.acobj.request_id), str(ts_id))
                        try:
                            sender = mailobj.mail(subject, body, sender=AC_Defines.AUTOCENTER)
                        except Exception as err:
                            self.log.error("failed to send alert mail {}".format(err))

                        self.log.info(
                            "[AUTOMATION_CENTER][TC_Monitor_Thread] Sending alert to [%s]." %
                            (str(toaddress)))

                    except Exception as err:
                        self.log.error("failed to send alert mail {}".format(err))
                        raise

                def run(self):
                    try:

                        prevtc_runinfo = self.gettcruninfo()
                        firstalert = True
                        if len(prevtc_runinfo) == 0:
                            # There has been an issue finding previous testcase runs, unable to
                            # monitor the status.  Exit
                            self.stop()
                        if not prevtc_runinfo.get("Elapsed"):
                            self.exitflag = True
                            self.log.info(
                                "[AUTOMATION_CENTER][TC_Monitor_Thread] is not launching"
                                " for testcase {}.".format(
                                    str(self.tc_id)))
                        # Make sure the exitflag is not set.
                        if not self.exitflag:
                            # Get the elapsed time of the previous run.
                            prevrunseconds = self.acobj.getsec(str(prevtc_runinfo['Elapsed']))

                            # Get the alert scale for this TC
                            alertscale = self.getalertscale(prevrunseconds)

                            # Second alert is ALWAYS 30min after first alert
                            secondalert = 1800

                            self.log.info(
                                "[AUTOMATION_CENTER][TC_Monitor_Thread] Launching"
                                " monitor thread for testcase {}.".format(
                                    str(self.tc_id)))

                        while not self.exitflag:
                            # Get the current elapsed time.
                            curtime = dt.datetime.now()
                            try:
                                timedelta = (curtime - self.stime)
                                curelap_time = timedelta.total_seconds()
                            except AttributeError:

                                def total_seconds(timedate):
                                    '''returns time value seconds '''
                                    return float(
                                        (timedate.microseconds + (
                                                timedate.seconds + timedate.days * 24 * 3600) * 10 ** 6)
                                    ) / 10 ** 6

                                curelap_time = total_seconds(timedelta)

                            if curelap_time > (prevrunseconds * alertscale) and firstalert:
                                # Threshold is based on a scale in self.getalertscale
                                self.log.warning(
                                    "[AUTOMATION_CENTER][TC_Monitor_Thread] Testcase {} runtime of"
                                    " {} seconds has exceeded previous 'Passed' runtime {}."
                                    " Threshold={} seconds.  SENDING ALERT!".format(
                                        str(self.tc_id), str(curelap_time), str(
                                            prevtc_runinfo['Elapsed']),
                                        str(AC_Defines.TC_MONITOR_THRESHOLD)))
                                self.acobj.updatetc_status(str(self.ts_id), str(
                                    self.tc_id), self.controller_id, AC_Defines.AC_UNRESPONSIVE)
                                # Status 8=Hanging\Unresponsive
                                # Send the alert after monitor thread is stopped.
                                self.sendalert(self.ts_id, self.tc_id, timedelta,
                                               prevtc_runinfo['Elapsed'], 'First')

                                firstalert = False

                            if curelap_time > (prevrunseconds * alertscale) + \
                                    secondalert and not firstalert:
                                # This means an alert was already sent; if it's 30 min after first
                                # alert, send second alert.
                                self.sendalert(self.ts_id, self.tc_id, timedelta,
                                               prevtc_runinfo['Elapsed'], 'Second')
                                self.stop()  # We can stop monitoring after the second alert.

                            # Testcase is within the threshold.  Keep monitoring every 2 seconds
                            time.sleep(2)

                    except Exception as err:
                        self.log.exception(str(err))
                        raise

            # This function is called when a testcase STARTS execution.
            starttime = dt.datetime.now()
            return MonitorThread(ts_id, tc_id, self, starttime, controller_id)
        except Exception as err:
            self.log.exception(str(err))
            raise

    def getsec(self, time):
        '''get the time in seconds'''
        try:
            time = time.split(':')
            return int(time[0]) * 3600 + int(time[1]) * 60 + int(time[2]) + int(time[3] * 1000)
        except Exception as err:
            self.log.exception(str(err))
            raise

    def get_failure_email_string(self, testset):
        '''
        get the email list to send the mail for a specific test set.
        '''
        try:
            query = ("select ed.emailList from testsetNEW ts INNER JOIN"
                     " testsetProp tsp ON ts.testsetID=tsp.testsetID INNER JOIN"
                     " emailDistribution ed ON tsp.emailDistIDFail=ed.emailDistID"
                     " where ts.testsetID=" + str(testset))
            notify_faillist = self.execute_db_query(query, autocommit=False)
            if len(notify_faillist.rows) > 0:
                email_text = ",".join(self.emaillist) + ',' + notify_faillist.rows[0][0]
            else:
                email_text = ",".join(self.emaillist)

            return email_text
        except Exception as err:
            self.log.exception(str(err))
            raise


class AutomationController():
    '''
    Extending the machine class so we can use all of its properties and methods.

    '''

    def add_property(self, name, value):
        '''
        create local fget and fset functions
        '''

        def fget(self): return self._get_property(name)

        def fset(self, value): return self._set_property(name, value)

        # add property to self
        setattr(self.__class__, name, property(fget, fset))
        # add corresponding local variable
        setattr(self, '_' + name, value)

    def _set_property(self, name, value):
        setattr(self, '_' + name, value)

    def _get_property(self, name):
        return getattr(self, '_' + name)

    def __init__(self, **entries):
        for name, value in entries.items():
            self.add_property(name, value)
