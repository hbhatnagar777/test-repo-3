import time

from AutomationUtils.cvtestcase import CVTestCase
from Application.Teams.teams_helper import TeamsHelper
from Application.Teams.teams_constants import TeamsConstants
from Application.Teams.customcategory import CustomCategory
from AutomationUtils import constants
from Application.Teams.teams_client_helper import TeamsClientHelper

const = TeamsConstants()


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Microsoft O365 verify Teams Custom Category Feature"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.tcinputs = {
            "clientname":None,
            "Office365Plan": None,
            "members": None,
            "ServerPlan": None,
            "index_server": None,
            "access_node":None
        }
        self.created_teams = []
        self.no_of_created_teams = 3
        self.teams_in_teams_tab = []
        self.teams_client_helper = None

    def setup(self):
        """Setup function of this test case."""
        self.teams_client_helper = TeamsClientHelper(self.commcell)
        self.client = self.teams_client_helper.create_client(client_name=self.tcinputs['clientname'],
                                          server_plan=self.tcinputs['ServerPlan'],
                                          index_server=self.tcinputs['index_server'],
                                          access_nodes_list=[self.tcinputs['access_node']])
        self.helper = TeamsHelper(self.client)
        self.plan = self.tcinputs['Office365Plan']
        self.log.info("1 Create 3 teams with display name starts with CUSTOM_CATEGORY")
        for i in range(self.no_of_created_teams):
            team = self.helper.create_public_team("CATEGORY_VERIFICATION"+str(i+1),
                                                  members=self.tcinputs['members'])
            self.created_teams.append(team)

    def run(self):
        """Main function for test case execution."""
        self.helper.discover(refresh_cache=True)
        self.log.info("2 Create Custom Category with name CONTAINS_CUSTOM_CATEGORY")
        custom_category = CustomCategory("CONTAINS_CUSTOM_CATEGORY_NAME")
        self.log.info("3 Add rule with Teams Display name contains CUSTOM_CATEGORY")
        custom_category.add_rule(const.CloudAppField.Team_Display_Name, const.CloudAppFieldOperator.Contains,
                                 "CATEGORY_VERIFICATION")

        self.log.info("5 Add Custom Category to the Content")
        self.helper.set_content(custom_category.custom_json, self.plan, const.CloudAppDiscoveryType.CustomCategory)
        self.log.info("6 Get all team form Teams tab")
        time.sleep(10)
        for team in self.helper.get_associated_teams():
            self.teams_in_teams_tab.append(team["userAccountInfo"]['displayName'].lower())
        self.log.info("7 Compare created teams to the teams got from teams tab.")
        if len(self.teams_in_teams_tab) == self.no_of_created_teams:
            for team in self.created_teams:
                if team.name.lower() not in self.teams_in_teams_tab:
                    raise Exception("Custom category was not working fine")
        else:
            self.status = constants.FAILED
            raise Exception("Custom category was not working fine")
        self.log.info("Custom category was working fine")

    def tear_down(self):
        """Tear down function for test case"""
        self.log.info("8 Delete all created teams")
        for team in self.created_teams:
            self.helper.delete_team(team)
        self.teams_client_helper.delete_client(self.tcinputs['clientname'])




       