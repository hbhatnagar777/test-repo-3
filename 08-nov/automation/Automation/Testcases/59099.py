# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright  Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case
"""

import time
from cvpysdk.security.user import User
from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Server.Security.user_login_validator import LoginValidator


class TestCase(CVTestCase):
    """Class for executing DR backup test case"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = """Validates user guid generation with bAllowMissingDomainADLogin"""
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.NOTAPPLICABLE
        self.show_to_user = True
        self.tcinputs = {
            "Commcell": None
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        self._log = logger.get_log()

    def run(self):
        """Execution method for this test case"""
        key_got_added = False
        tc = ServerTestCases(self)
        validator = LoginValidator(self)
        try:
            validator.prerequisites()
            for user in validator.users_login_details:
                validator.userhelper.gui_login(self.commcell.commserv_hostname,
                                               (user.get('domain') + "\\" + user.get('username')),user.get('password'))
            #ad_server_details = self.tcinputs.get('Commcell').get('LDAPs').get('Active Directory')
            ad_server_details = validator.config_json.Security.LDAPs._asdict().get('Active_Directory')._asdict()
            try:
                self.log.info("Trying to remove host file entry {0}".format(ad_server_details.get('DomainName')))
                validator.client_machine.remove_host_file_entry(hostname=ad_server_details.get('DomainName'))
            except Exception as exp:
                self.log.info(exp)
            self.log.info("Performing iisreset")
            validator.client_machine.execute_command('iisreset')
            time.sleep(120)
            try:
                self.log.info("Trying AD user login when AD is unreachable..")
                for user in validator.users_login_details:
                    validator.userhelper.gui_login(self.commcell.commserv_hostname,
                                                   (user.get('domain') + "\\" + user.get('username')),
                                                   user.get('password'))
                    raise Exception("User {0} looged in when"
                                    " AD is down".format((user.get('domain') + "\\" + user.get('username'))))
            except Exception as exp:
                if "Username / Password are incorrect" not in str(exp):
                    raise Exception("user login should fail exp = {0}".format(exp))
                self.log.info(exp)
                self.log.info("Adding additional setting bAllowMissingDomainADLogin")
            self.commcell.add_additional_setting(category="CommServDB.GxGlobalParam",
                                                 key_name="bAllowMissingDomainADLogin",
                                                 data_type="BOOLEAN",
                                                 value='true')
            self.log.info("Key got added successfully")
            key_got_added = True
            for user in validator.users_login_details:
                self.log.info("Attempting user {0} login when AD is unreachable"
                              " and Key is inplace bAllowMissingDomainADLogin".format(user.get('username')))
                user_obj = User(self.commcell, user_name=(user.get('domain') + "\\" + user.get('username')))
                user['id'] = user_obj.user_id
                user['guid'] = user_obj.user_guid
                validator.userhelper.gui_login(self.commcell.commserv_hostname,
                                               (user.get('domain') + "\\" + user.get('username')),
                                               user.get('password'))

            self.log.info("removing user guid from db")
            for user in validator.users_login_details:
                validator.utility.update_commserve_db("update umusers set userGuid=''"
                                                      " where id={0}".format(user.get('id')))

            for user in validator.users_login_details:
                validator.userhelper.gui_login(self.commcell.commserv_hostname,
                                               (user.get('domain') + "\\" + user.get('username')),
                                               user.get('password'))
                user_obj = User(self.commcell, user_name=(user.get('domain') + "\\" + user.get('username')))
                if not user_obj.user_guid or user.get('guid').lower() == user_obj.user_guid.lower():
                    raise Exception('user {0} guid is not generated successfully'.format(user.get('username')))
                self.log.info('new guid is generated for user {0}: new guid {1} old guid {2}'.format(
                    user.get('username'), user_obj.user_guid,user.get('guid')))

            self.log.info("Trying to add host file entry for domain {0}".format(ad_server_details.get('DomainName')))
            try:
                validator.client_machine.add_host_file_entry(hostname=ad_server_details.get('DomainName'),
                                                             ip_addr=ad_server_details.get('IPAddress'))
            except Exception as exp:
                self.log.info(exp)

            self.log.info("Performing iisreset")
            validator.client_machine.execute_command('iisreset')
            time.sleep(120)

            for user in validator.users_login_details:
                validator.userhelper.gui_login(self.commcell.commserv_hostname,
                                               (user.get('domain') + "\\" + user.get('username')),
                                               user.get('password'))
                user_obj = User(self.commcell, user_name=(user.get('domain') + "\\" + user.get('username')))
                if not user_obj.user_guid or user.get('guid').lower() != user_obj.user_guid.lower():
                    raise Exception('user {0} guid is not updated successfully: new guid {1} old guid {2}'.format(
                        user.get('username'), user_obj.user_guid, user.get('guid')))
                self.log.info('guid is updated for user {0}'.format(user.get('username')))
            self.log.info("user guid generation with bAllowMissingDomainADLogin is validated successfully")
        except Exception as exp:
            tc.fail(exp)
        finally:
            if key_got_added:
                self.commcell.delete_additional_setting(category="CommServDB.GxGlobalParam",
                                                        key_name="bAllowMissingDomainADLogin")
            if validator.users_login_details:
                validator.cleanup()
