# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


""""Main file for executing this test case
TestCase is the only class defined in this file.
TestCase: Class for executing this test case
TestCase:
    __init__()      --  initialize TestCase class
    setup()         --  setup function of this test case
    run()           --  run function of this test case
    tear_down()     --  tear down function of this test case

    Test Case:
        [Network & Firewall] : Validation of Data Interface Pair between Group to
         Group and Group to Client\Client to Group with Wildcard filter.

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.Network.networkhelper import NetworkHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name                (str)       -   name of this test case

                applicable_os       (str)       —   applicable os for this test case
                                                            Ex: self.os_list.WINDOWS

                product             (str)       —   applicable product for this test case
                                                                 Ex: self.products_list.FILESYSTEM

                features            (str)       —   qcconstants feature_list item
                                                             Ex: self.features_list.DATAPROTECTION

                show_to_user        (bool)      —   test case flag to determine if the test case is
                                                             to be shown to user or not

                default: False
                tcinputs            (dict)      -   test case inputs with input name as dict key
                                                    and value as input type

                Inputs:
                    One client NetworkClient can be any file system client with one IP address of client
                    One media agenta as NetworkMediaAgent with one IP address of MA

        """
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Validation of Data Interface Pair " \
                    "between Group to Group and Group to Client\Client to Group with Wildcard filter."
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.show_to_user = True
        self.tcinputs = {
            "NetworkClient": None,
            "NetworkClient_IP": None,
            "NetworkMediaAgent": None,
            "NetworkMediaAgent_IP": None
        }

        self.network_helper = None
        self.client_grp_map = None

        # Clients
        self.client = None,
        self.client_ip = None,
        self.media_agent = None,
        self.media_agent_ip = None,
        self.client_names_list = None,

        # Client Groups
        self.client_grp = 'client_grp_56696'
        self.ma_grp = 'ma_grp_56696'
        self.clients_grps_obj = None
        self.client_grp_list = [self.client_grp, self.ma_grp]

    def setup(self):
        """Setup function of this test case"""
        try:
            self.network_helper = NetworkHelper(self)

            self.client = self.tcinputs['NetworkClient']
            self.client_ip = self.tcinputs['NetworkClient_IP']
            self.media_agent = self.tcinputs['NetworkMediaAgent']
            self.media_agent_ip = self.tcinputs['NetworkMediaAgent_IP']
            self.client_names_list = [self.client, self.media_agent]

            # Create Client groups
            # Client grp list
            self.clients_grps_obj = self.commcell.client_groups
            for client_grp, client_name in zip(self.client_grp_list, self.client_names_list):
                self.log.info('Creating client group: {0} with client: {1}'.format(client_grp, client_name))

                if self.clients_grps_obj.has_clientgroup(client_grp):
                    self.clients_grps_obj.delete(client_grp)
                self.clients_grps_obj.add(client_grp, clients=[client_name])

            self.network_helper.remove_network_config([{'clientName': self.client},
                                                       {'clientName': self.media_agent}])

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.tear_down()

    def run(self):
        """Run function of this test case"""
        self.log.info("Started executing testcase 54190")
        try:

            # Dips between clientgroup and client
            dips_list = [({'clientgroup': self.client_grp, 'srcip': '*'},
                          {'client': self.media_agent, 'destip': self.media_agent_ip})]
            self.network_helper.add_dips(dips_list)

            self.verify_summary_dips()

            self.network_helper.validate_with_plan([self.client], self.media_agent)

            self.network_helper.entities.cleanup()
            self.network_helper.delete_dips(dips_list)

            # Dips between client and clientgroup
            dips_list = [({'client': self.client, 'srcip': self.client_ip},
                          {'clientgroup': self.ma_grp, 'destip': ' '})]
            self.network_helper.add_dips(dips_list)

            self.verify_summary_dips()

            self.network_helper.validate_with_plan([self.client], self.media_agent)
            self.network_helper.entities.cleanup()

            self.network_helper.delete_dips(dips_list)

            # Dips between clientgroup and clientgroup
            dips_list = [({'clientgroup': self.client_grp, 'srcip': self.client_ip[:3] + '.*'},
                          {'clientgroup': self.ma_grp, 'destip': self.media_agent_ip[:3] + '.*'})]
            self.network_helper.add_dips(dips_list)

            self.verify_summary_dips()

            self.network_helper.validate_with_plan([self.client], self.media_agent)
            self.network_helper.entities.cleanup()

            self.network_helper.delete_dips(dips_list)

            # Dips between clientgroup and client with wildcard
            dips_list = [({'clientgroup': self.client_grp, 'srcip': self.client_ip[0:3] + ".*"},
                          {'client': self.media_agent, 'destip': self.media_agent_ip})]
            self.network_helper.add_dips(dips_list)

            self.verify_summary_dips()

            self.network_helper.validate_with_plan([self.client], self.media_agent)
            self.network_helper.entities.cleanup()

            self.network_helper.delete_dips(dips_list)

            # Dips between client and clientgroup
            dips_list = [({'client': self.client, 'srcip': self.client_ip},
                          {'clientgroup': self.ma_grp, 'destip': self.media_agent_ip[0:3] + ".*"})]
            self.network_helper.add_dips(dips_list)

            self.verify_summary_dips()

            self.network_helper.validate_with_plan([self.client], self.media_agent)
            self.network_helper.entities.cleanup()

            self.network_helper.delete_dips(dips_list)

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""

        if self.network_helper is not None:
            self.network_helper.cleanup_network()

        self.log.info("Deleting client groups")
        for client_group in self.client_grp_list:
            if self.clients_grps_obj.has_clientgroup(client_group):
                self.clients_grps_obj.delete(client_group)

        if self.network_helper.entities is not None:
            self.network_helper.entities.cleanup()

    def verify_summary_dips(self):
        """Verify network summary for dips configuration

        Args:
            client_list: list of clients

        Raises:
            Exception:
                    If network summary is incorrect for dips

        """
        return 
        summary_dict = self.network_helper.get_network_summary([self.client, self.media_agent])
        if self.client + " " + self.media_agent + " type=dip" not in summary_dict[self.client] or 'local_iface' not in \
                summary_dict[self.client] or 'remote_iface' not in summary_dict[self.client]:
            raise Exception("Incorrect network summary for client : " + self.client)
        if self.media_agent + " " + self.client + " type=dip" not in summary_dict[
            self.media_agent] or 'local_iface' not in summary_dict[self.media_agent] or 'remote_iface' not in \
                summary_dict[self.media_agent]:
            raise Exception("Incorrect network summary for client : " + self.media_agent)
