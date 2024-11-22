# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
TestCase is the only class in this file
"""
import collections
import time
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.exchangepowershell_helper import ExchangePowerShell
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """Class to perform check for O365 license consumption for active users only"""
    test_step = TestStep()

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = 'Check O365 license consumption for MSFT Licensed users'
        self.client = None
        self._subclient = None
        self.agent = None
        self.instance = None
        self.backupset = None

        self._utility = None

        self.license_sp_query = """
            DECLARE @isMasterSPRunning INT=0
            SELECT @isMasterSPRunning = CONVERT(INT, value) FROM GXGlobalParam WITH (NOLOCK) WHERE name = 'LicCalcUsageMasterSPRunning'
            IF @isMasterSPRunning = 1
            BEGIN
                WHILE @isMasterSPRunning = 1
                BEGIN     
                    WAITFOR DELAY '00:00:05'
                    SET @isMasterSPRunning = 0
                    SELECT @isMasterSPRunning = CONVERT(INT, value) FROM GXGlobalParam WITH (NOLOCK) WHERE name = 'LicCalcUsageMasterSPRunning'
                END
            END
            ELSE
            BEGIN
                EXEC LicCalcUsageMaster @nCallerType = 2
            END
        """
        self.query = "select distinct ObjectName from Lic_CurrentUsage where UsageType =18" \
                     " and AppTypeId =137 and lictype = 200011"

        self._created_user: str = str()
        self._created_user_alias: str = str()
        self.tcinputs = {
            "ExchangePlan": None
        }
        self.exmbclient_object: ExchangeMailbox
        self.powershell: ExchangePowerShell

    @test_step
    def set_all_user_associations(self):
        """Enable All Mailboxes' association on the Client"""
        self.subclient.enable_auto_discover_association(association_name="All Users",
                                                        plan_name=self.tcinputs["ExchangePlan"])
        self.exmbclient_object.cvoperations.wait_for_ad_mailbox_monitor()

    @test_step
    def set_content_association(self, mailbox_alias: str):
        """Enable association on the Client for passed content"""
        _assoc_content = {
            'mailboxNames': [mailbox_alias],
            'plan_name': self.tcinputs["ExchangePlan"]
        }

        self.subclient.set_user_assocaition(_assoc_content, use_policies=False)
        self.exmbclient_object.cvoperations.wait_for_ad_mailbox_monitor()

    @test_step
    def check_licensed_users_tally(self):
        """Check that licensed users match up with users on Azure."""
        _db_users = self.exmbclient_object.csdb_helper.get_licensed_users_for_client()  # only user mailboxes
        _api_users = self.exmbclient_object.access_node_powershell.get_licensed_users()  # all user and shared mailboxes with license
        self.log.info("Licensed Users from the DB: {}".format(_db_users))
        self.log.info("Licensed Users from Powershell: {}".format(_api_users))
        _licensed_users = [user for user, user_license in _db_users if int(user_license) == 1]
        return collections.Counter(_licensed_users) != collections.Counter(
            _api_users)

    @test_step
    def create_and_assign_user_license(self):
        """Create a mailbox and assign license to the user."""
        _testdata = TestData(self.exmbclient_object)
        _mailboxe = _testdata.create_online_mailbox(use_json=False, count=1)[0]
        smtp = _mailboxe + "@" + self.tcinputs['DomainName']
        self.log.info("Created Online User: {}".format(smtp))

        time.sleep(45)
        self.exmbclient_object.graph_helper.modify_user_license(user_upn=smtp, operation="assign")
        self.log.info("License Assigned to the User: {}".format(_mailboxe))
        time.sleep(45)  # AD Sync time
        self.exmbclient_object.cvoperations.run_admailbox_monitor()
        self.subclient.refresh()

        return smtp, _mailboxe

    @test_step
    def check_user_applied_license(self, user_upn):
        """Check whether user was correctly applied a license by discovery."""
        _db_users = self.exmbclient_object.csdb_helper.get_licensed_users_for_client()
        self.log.info("Licensed Users from the DB: {}".format(_db_users))
        for user, user_license in _db_users:
            if user.lower() == user_upn.lower():
                return int(user_license) == 1
        return False

    @test_step
    def remove_user_license(self, smtp):
        """Remove the license for a user."""
        self.exmbclient_object.graph_helper.modify_user_license(user_upn=smtp, operation="remove")
        time.sleep(45)  # AD Sync time
        self.exmbclient_object.cvoperations.run_admailbox_monitor()

    @test_step
    def check_user_license_removed(self, user_upn):
        """Check whether the license was removed for the user"""
        _db_users = self.exmbclient_object.csdb_helper.get_licensed_users_for_client()
        self.log.info("Licensed Users from the DB: {}".format(_db_users))
        for user, user_license in _db_users:
            if user.lower() == user_upn.lower():
                return False
        return True

    def setup(self):
        """Setup function for the test case"""
        self.log.info('Creating Exchange Mailbox client object.')
        self.exmbclient_object = ExchangeMailbox(self)

        # self.powershell = ExchangePowerShell(ex_object=self.exmbclient_object, cas_server_name=None,
        #                                      exchange_server=None,
        #                                      exchange_adminname=self.exmbclient_object.exchange_online_user,
        #                                      exchange_adminpwd=self.exmbclient_object.exchange_online_password,
        #                                      server_name=self.exmbclient_object.server_name)

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self.log.info("Exchange Client has been created")

        self._subclient = self.exmbclient_object.cvoperations.subclient
        self.log.info("Exchange Sub-client is created")

        self._utility = OptionsSelector(self.commcell)

    def run(self):
        """Run Function for the Test Case"""
        try:
            # self.set_all_user_associations()
            # status = self.check_licensed_users_tally()
            #
            # if not status:
            #     self.log.exception("Error in checking the licensed user tally.")
            #     raise Exception("Licensed User tally did not match...")

            self._created_user, self._created_user_alias = self.create_and_assign_user_license()

            self.set_content_association(self._created_user_alias)

            self.subclient.backup()

            status = self.check_user_applied_license(user_upn=self._created_user)
            if not status:
                self.log.exception("Error in assigning license to the user.")
                raise Exception("Error in discovery to assign license to the user...")

            self.remove_user_license(self._created_user)

            self.subclient.backup()

            status = self.check_user_license_removed(user_upn=self._created_user)
            if not status:
                self.log.exception("Error in verifying condition of license removal.")
                raise Exception("Discovery was not able to remove license for the user...")

        except Exception as ex:
            handle_testcase_exception(self, ex)

    def tear_down(self):
        """Tear down function for the test case"""
        self.exmbclient_object.graph_helper.delete_azure_ad_user(user_upn=self._created_user)