# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case
"""

import random
import time
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Server.Security.user_login_validator import LoginValidator
from Server.Security.userconstants import WebConstants


class TestCase(CVTestCase):
    """Class for executing DR backup test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = """Limit user logon feature for User's [commcell user, AD user, LDAP user, company user]"""
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.validator = None
        self.tcinputs = {
            "Commcell": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()

    def run(self):
        """Execution method for this test case"""
        try:
            tc = ServerTestCases(self)
            self.validator = LoginValidator(self)
            self.validator.prerequisites()
            self.validate_limit_user_logon_attempts()
        except Exception as excep:
            tc.fail(excep)
        finally:
            self.validator.cleanup()
            self._commcell.disable_limit_user_logon_attempts()
            if "unix" in self.commcell.commserv_client.os_info.lower():
                self.log.info("Performing commvault restart")
                self.commcell.commserv_client.restart_services()
            else:
                self.log.info("Performing IISRESET")
                self.commcell.commserv_client.execute_command('iisreset')
            self.log.info("waiting 180 seconds = 3 mins")
            time.sleep(180)

    def attempt_n_number_of_invalid_login_attempts(self, username, attempts, force=False):
        """
        """
        self.log.info("Attempting '{0}' invalid login attempts for user = {1}".format(attempts, username))
        for attempt in range(attempts):
            interface = random.sample(["gui", "web"], 1)
            self.log.info("Attempt = {2} user = {0} login with invalid "
                          "creds from = {1}".format(username, interface, attempt + 1))
            try:
                if interface[0] == "web":
                    self.validator.userhelper.web_login(username, "*******",
                                                        web=WebConstants(self._commcell.commserv_hostname))
                elif interface[0] == "gui":
                    self.validator.userhelper.gui_login(self._commcell.webconsole_hostname, username, "*******")
            except Exception as exp:
                if attempt + 1 == attempts:
                    if force:
                        raise exp
                    else:
                        return str(exp)

    def validate_limit_user_logon_attempts(self, user_attempt_limit=3, account_lock_duration=900,
                                           failed_login_attempts_within=1200, lock_duration_increment=600):
        """
        Validates featues FailedLoginAttemptLimit and AccountLockDuration for various user's
        Args:
            user_attempt_limit      (int)       --      number of failed attempts before user account gets locked
            account_lock_duration   (int)       --      user account lock duration in *secs*
        Returns:
            None
        Raises:
            Exception:
                if feature validation fails
        """
        attempt_limit = user_attempt_limit
        lock_duration = account_lock_duration
        failed_counter = 0
        self.log.info("Validating Limit user logon feature with values Attempt Limit = {0},"
                      "Account Lock Duration = {1}, Failed login attempts within = {2} and "
                      "Lock Duration increment = {3}".format(user_attempt_limit, account_lock_duration,
                                                             failed_login_attempts_within, lock_duration_increment))
        # self.validator.create_local_user_entity(entity_inputs={"user": {}})
        # Attempt one successful login for all users.

        for user in self.validator.users_login_details:
            username = "{0}\{1}".format(user.get('domain'), user.get('username')) \
                if user.get('domain') else user.get('username')
            self.log.info("Attempting valid login for user = {0}".format(username))
            self.validator.userhelper.gui_login(self._commcell.webconsole_hostname, username, user.get('password'))
        self._commcell.enable_limit_user_logon_attempts(failed_login_attempt_limit=user_attempt_limit,
                                                        failed_login_attempts_within=failed_login_attempts_within,
                                                        account_lock_duration=account_lock_duration,
                                                        lock_duration_increment_by=lock_duration_increment)

        if "unix" in self.commcell.commserv_client.os_info.lower():
            self.log.info("Performing commvault restart")
            self.commcell.commserv_client.restart_services()
        else:
            self.log.info("Performing IISRESET")
            self.commcell.commserv_client.execute_command('iisreset')
        self.log.info("waiting 300 seconds = 5 mins")
        time.sleep(300)
        # Attempt attempt_limit -1 invalid login attempts for all users.
        for user in self.validator.users_login_details:
            username = "{0}\{1}".format(user.get('domain'), user.get('username')) \
                if user.get('domain') else user.get('username')
            self.log.info("Validating failed login attempts within feature for user {0}".format(username))
            self.attempt_n_number_of_invalid_login_attempts(username, user_attempt_limit - 1)
        self.log.info("waiting for {0} secs. so that failed attempts within feature resets"
                      " failed attempts counter".format(failed_login_attempts_within))
        time.sleep(failed_login_attempts_within)
        # Attempt one more invalid login attempt to verify failed attempts within feature
        self.log.info("Attempting one more invalid login attempt to verify failed attempts within feature")
        for user in self.validator.users_login_details:
            username = "{0}\{1}".format(user.get('domain'), user.get('username')) \
                if user.get('domain') else user.get('username')
            try:
                self.attempt_n_number_of_invalid_login_attempts(username, 1, True)
            except Exception as excp:
                if 'locked' in str(excp):
                    raise Exception("Failed attempts within feature validation failed for user {0}".format(
                        username
                    ))
            self.log.info("Failed attempts within feature is successfully validated for user = {0}".format(username))
        # Attempt attempt_limit -1 invalid login attempts for all users.
        for user in self.validator.users_login_details:
            username = "{0}\{1}".format(user.get('domain'), user.get('username')) \
                if user.get('domain') else user.get('username')
            try:
                self.attempt_n_number_of_invalid_login_attempts(username, user_attempt_limit - 1, True)
            except Exception as excp:
                if "locked" not in str(excp) and "incorrect" not in str(excp):
                    raise Exception("'locked' keyword is not present on error masg,"
                                    " error = {0}".format(excp))
                self.log.info("Error message validated = {0}".format(str(excp)))
                self.log.info("Validating isAccountLocked flag for user = {0}".format(username))
                account_lock_info = self._commcell.users.get(user_name=username).get_account_lock_info
                if not account_lock_info['isAccountLocked']:
                    raise Exception("user {0} account is not locked".format(username))
            self.log.info("Failed login limit is successfully validated for user = {0}".format(username))
        # verify that account got locked (i.e) try login with valid creds from interfaces
        # (GUI, WEBCONSOLE, ADMINCONSOLE)
        for user in self.validator.users_login_details:
            username = "{0}\{1}".format(user.get('domain'), user.get('username')) \
                if user.get('domain') else user.get('username')
            self.log.info("Attempting valid login for user = {0}. "
                          "To verify if account is really locked out".format(username))
            for interface in range(2):
                logged_in = 1
                try:
                    if interface == 1:
                        self.validator.userhelper.gui_login(self._commcell.webconsole_hostname,
                                                            username, user.get('password'))
                    elif interface == 0:
                        self.validator.userhelper.gui_login(self._commcell.webconsole_hostname,
                                                            username, user.get('password'))
                        self.validator.userhelper.web_login(username, user.get("password"),
                                                            web=WebConstants(self._commcell.commserv_hostname))
                except Exception as excp:
                    if 'locked' not in str(excp) and "incorrect" not in str(excp):
                        raise Exception("user account must be locked , excp = {0}".format(excp))
                    logged_in = 0
                    self.log.info(excp)
                if logged_in:
                    raise Exception('login must fail with remaining duration to get account unlock')
        self.log.info("Waiting for some time so that account get's "
                      "unlocked secs = {0}".format(lock_duration))
        time.sleep(lock_duration + 180)
        # Verify isAccountLocked status for all users account
        for user in self.validator.users_login_details:
            username = "{0}\{1}".format(user.get('domain'), user.get('username')) \
                if user.get('domain') else user.get('username')
            account_lock_info = self._commcell.users.get(user_name=username).get_account_lock_info
            if account_lock_info['isAccountLocked']:
                raise Exception("user {0} account is still locked after lock duration."
                                "remaining duration = {1}".format(
                    username, account_lock_info['lockEndTime'] - account_lock_info['lockStartTime']))
            self.log.info("{0} account is auto-unlocked successfully".format(username))
            # lock the account one more time to verify lock duration increment feature
            self.attempt_n_number_of_invalid_login_attempts(username, attempt_limit)
        # Verify lock duration increment for all users
        for user in self.validator.users_login_details:
            username = "{0}\{1}".format(user.get('domain'), user.get('username')) \
                if user.get('domain') else user.get('username')
            user_details = self._commcell.users.get(user_name=username)
            account_lock_info = user_details.get_account_lock_info
            if (account_lock_info['lockEndTime'] - account_lock_info['lockStartTime'] !=
                    account_lock_duration + lock_duration_increment):
                raise Exception("{0} user account lock duration {1} secs doesn't match "
                                "with actual settings {2} secs".format(
                    username, account_lock_info['lockEndTime'] - account_lock_info['lockStartTime'],
                              account_lock_duration + lock_duration_increment))
            self.log.info("Lock duration increment verified for user {0}".format(username))
            self.log.info("Attempting user account unlock for user = {0}".format(username))
            status = user_details.unlock()
            if 'Unlock successful' not in status[0]:
                raise Exception("Manual unlock failed for user = {0}, error msg = {1}".format(
                    username, status))
            self.log.info("Unlock successful for user = {0}".format(username))
        # unlock user accounts manually using unlock feature
        for user in self.validator.users_login_details:
            username = "{0}\{1}".format(user.get('domain'), user.get('username')) \
                if user.get('domain') else user.get('username')
            # attempting login with valid creds after account lock duration
            self.validator.retry_webconsole_user_login(username=username, password=user.get('password'))
            self.validator.userhelper.gui_login(self._commcell.webconsole_hostname, username, user.get('password'))
        self.log.info("Limit user logon feature validated successfully")
