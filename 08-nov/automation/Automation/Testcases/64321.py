from AutomationUtils.cvtestcase import CVTestCase
from Application.Teams.teams_helper import TeamsHelper
from Application.Teams.teams_constants import TeamsConstants
from AutomationUtils import constants
const = TeamsConstants()


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Microsoft O365 verify Teams Users Discover Based on Chat Backup Enable Option Verification"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.tcinputs = {
            "ClientName": None
        }

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client)

    def run(self):
        """Main function for test case execution."""
        self.log.info("1. Disable user chat backup option")
        self.helper.disable_chat_backup()
        self.log.info("2. verify users or groups discovery wont run")
        if self.helper.discover(discovery_type=const.CloudAppEdiscoveryType.Users) is None:
            self.log.info("Users Discovery not running")
        else:
            self.log.info("Users Discovery running")
            self.status = constants.FAILED

        self.log.info("3. Enable user chat backup option")
        self.helper.enable_chat_backup()
        self.log.info("4. verify Users discovery should run")
        users_from_tenant = []
        for username in sorted(list(self.helper.get_all_users_in_tenant())):
            if not (username.startswith('CVEXBackup') or "EXT" in username):
                users_from_tenant.append(username)

        users_from_dat_file = sorted(
            list(self.helper.discover(discovery_type=const.CloudAppEdiscoveryType.Users, refresh_cache=True).keys()))
        if users_from_dat_file == users_from_tenant:
            self.log.info("Users Discovering successfully")
        else:
            self.log.info("Users Not Discovering")
            self.status = constants.FAILED


