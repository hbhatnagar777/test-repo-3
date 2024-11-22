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

    run()           --  run function of this test case

This testcase validates the DIP settings through the command center

Inputs required are :

SourceClient : A client computer

MediaAgent : A Media agent computer

SourceIP : IP address of the source client computer

MediaAgentIP : IP address of the destination/media agent

Optional Inputs for IPV6 :-

SourceIPV6 : IPV6 address of the client computer

MediaAgentIPV6 : IPv6 address of the media agent

Restore : (Boolean) to run restore also

"""
import time
import socket
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector, CVEntities
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Server.Network.networkhelper import NetworkHelper
from Web.Common.exceptions import CVTestCaseInitFailure, CVTestStepFailure
from Web.Common.page_object import TestStep
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.machine import Machine
from Web.AdminConsole.AdminConsolePages.NetworkPage import BackupNetworks, NetworkPage


class TestCase(CVTestCase):
    """Command Center- Setting up DIPS(Backup networks) between computers - Command Center"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Setting up DIPS(Backup networks) between computers - Command Center"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self._client_group_name1 = "CG_60371_1"
        self._client_group_name2 = "CG_60371_2"
        self.driver = None
        self.smart_groups = ["My CommServe Computer", "My CommServe Computer and MediaAgents", "My MediaAgents"]
        self.client_group_obj1 = None
        self.client_group_obj2 = None
        self._network = None
        self.client_list = []
        self.client_groups = None
        self.commserve = None
        self.source_client_obj = None
        self.destination_client_obj = None
        self.summary = None
        self.tcinputs = {
            "SourceClient": None,
            'MediaAgent': None
        }
        self.interface_list1 = None
        self.interface_list2 = None
        self.hostname1 = None
        self.hostname2 = None
        self.option = None
        self.serverbase = None
        self.networkpage = None
        self.restore = False

    @test_step
    def init_tc(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.entities = CVEntities(self)
            self.client_list.extend([self.tcinputs["SourceClient"],
                                     self.tcinputs['MediaAgent']])
            self.commserve = self.commcell.commserv_name
            self._network = NetworkHelper(self)
            self.option = OptionsSelector(self.commcell)
            self.client_groups = self._network.entities.create_client_groups([self._client_group_name1,
                                                                              self._client_group_name2])
            self.client_group_obj1 = self.client_groups[self._client_group_name1]['object']
            self.client_group_obj2 = self.client_groups[self._client_group_name2]['object']
            self.client_group_obj1.add_clients([self.tcinputs["SourceClient"]])
            self.client_group_obj2.add_clients([self.tcinputs['MediaAgent']])
            self.source_client_obj = self.commcell.clients.get(self.tcinputs["SourceClient"])
            self.hostname1 = self.source_client_obj.client_hostname
            self.destination_client_obj = self.commcell.clients.get(self.tcinputs['MediaAgent'])
            self.hostname2 = self.destination_client_obj.client_hostname
            self.serverbase = CommonUtils(self.commcell)
            self.create_entities(self.tcinputs["SourceClient"], self.tcinputs["MediaAgent"])
            self.precheck()
            self.tcinputs["SourceIP"] = self.convert_hostname_to_ip(self.hostname1)
            self.tcinputs["MediaAgentIP"] = self.convert_hostname_to_ip(self.hostname2)
            if self.tcinputs.get('Restore'):
                self.restore = True

        except Exception as e:
            raise CVTestCaseInitFailure(e)

    def convert_hostname_to_ip(self, hostname):
        """Converts a hostname to its corresponding IP address.

        Args:
            hostname (str): The hostname to convert to an IP address.

        Returns:
            str: The IP address corresponding to the given hostname.
        """
        try:
            ip_address = socket.gethostbyname(hostname)
            return ip_address
        except socket.error as e:
            raise Exception(f"Unable to resolve hostname {hostname}: {e}")

    def precheck(self):
        """Check if the selected computers already have the DIP config"""
        # Set the registry key nCLNT_DEBUG to 1
        self.source_client_obj.add_additional_setting("Firewall", "nCLNT_DEBUG", "STRING", "1")
        self.destination_client_obj.add_additional_setting("Firewall", "nCLNT_DEBUG", "STRING", "1")

        source_id = int(self.source_client_obj.client_id)
        source = self.tcinputs["SourceClient"]
        dest_id = int(self.destination_client_obj.client_id)
        mediaagent = self.tcinputs["MediaAgent"]
        interfaces = self._network.get_dips_client(self.tcinputs["SourceClient"])
        client_groups = self.commcell.client_groups.all_clientgroups

        for i in interfaces:
            if i["destGroupId"] == 0:
                if i["srcGroupId"] == 0:
                    if (i["client1"].get('id') == source_id and i["client2"].get("id") == dest_id) or (
                            i["client2"].get('id') == source_id and i["client1"].get("id") == dest_id):
                        if source_id == i.get("client2").get("id"):
                            name1 = source
                            name2 = mediaagent
                        else:
                            name2 = source
                            name1 = mediaagent
                        data = [(
                            {'client': name1, 'srcip': i.get("client2")["name"]},
                            {'client': name2, 'destip': i.get("client1")["name"]}
                        )]
                        self._network.delete_dips(data)
                else:
                    name = source if source_id == i.get("client2").get("id") else mediaagent
                    for k, v in client_groups.items():
                        if v == str(i.get("srcGroupId")):
                            cg_name = k
                            associated_clients = self.commcell.client_groups.get(
                                cg_name).associated_clients
                            if source in associated_clients or mediaagent in associated_clients:
                                data = [(
                                    {'clientgroup': cg_name, 'srcip': i.get("client1")["name"]},
                                    {'client': name, 'destip': i.get("client2")["name"]}
                                )]
                                self._network.delete_dips(data)
            else:
                if i["srcGroupId"] == 0:
                    name = source if source_id == i.get("client2").get("id") else mediaagent
                    for k, v in client_groups.items():
                        if v == str(i.get("destGroupId")):
                            cg_name = k
                            associated_clients = self.commcell.client_groups.get(
                                cg_name).associated_clients
                            if source in associated_clients or mediaagent in associated_clients:
                                data = [(
                                    {'client': name, 'srcip': i.get("client1")["name"]},
                                    {'clientgroup': cg_name, 'destip': i.get("client2")["name"]}
                                )]
                                self._network.delete_dips(data)
                else:
                    cg1 = None
                    cg2 = None
                    for k, v in client_groups.items():
                        if v == str(i.get("destGroupId")):
                            cg1 = k
                        if v == str(i.get("srcGroupId")):
                            cg2 = k
                    if cg1 and cg2:
                        data = [(
                            {'clientgroup': cg1, 'srcip': i.get("client1")["name"]},
                            {'clientgroup': cg2, 'destip': i.get("client2")["name"]}
                        )]
                        self._network.delete_dips(data)
        summary = self.source_client_obj.get_network_summary()
        summary = summary.split("\n")
        for i in summary:
            if self.tcinputs["SourceClient"] + " " + self.tcinputs['MediaAgent'] + " " in i:
                if "local_iface" in i or "remote_iface" in i:
                    raise CVTestStepFailure("There is still DIP configuration already")
                if "type=proxy" in i:
                    raise CVTestStepFailure("There is no direct route between client and media agent")
        self.log.info("There is no DIPs before the testcase")

    @test_step
    def navigate_to_dip(self):
        """Navigate to DIPs"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login(username=self.inputJSONnode['commcell']['commcellUsername'],
                                     password=self.inputJSONnode['commcell']['commcellPassword'])
            self.navigator = self.admin_console.navigator
            self.navigator.navigate_to_network()
            self.networkpage = NetworkPage(self.admin_console)
            self.networkpage.click_dips()

            self.backupnetworks = BackupNetworks(self.admin_console)

        except Exception as e:
            raise CVTestCaseInitFailure(e)

    def validate_dip(self, summary, source, destination, interface1=None, interface2=None):
        self.log.info(summary)
        try:
            self.summary = summary.split("\n")
            flag1 = False
            flag2 = False
            for i in self.summary:
                j = i.lower()
                if source + " " + destination + " " in i:
                    # Passive route
                    if "type=passive" in i:
                        return "passive"

                    self.log.info(i)
                    if 'local_iface' in j and interface1.lower() in j:
                        flag1 = True
                        self.log.info("Validated interface route in source client")

                    if ('remote_iface' in j or 'cvfwd' in j) and interface2.lower() in j:
                        flag2 = True
                        self.log.info("Validated interface route in source client")

            if flag1 and flag2:
                return True
            return False
        except Exception as e:
            raise CVTestStepFailure(e)

    def validate_tokens(self):
        """Verifies the network push worktoken submitted to the client and media agent"""
        # Verify the network worktokens being submitted to the clients automatically
        self._network.push_config_client([self.tcinputs["SourceClient"], self.tcinputs['MediaAgent']])
        time.sleep(5)
        col1, res = self.option.exec_commserv_query("""SELECT clientId, workToken from APP_WorkQueueRequest""")
        client = False
        mediaagent = False
        for row in res:
            if row[0] == self.source_client_obj.client_id and row[1] == "5":
                self.log.info("Verified the worktoken for the client")
                client = True
            if row[0] == self.destination_client_obj.client_id and row[1] == "5":
                self.log.info("Verified the worktoken for the media agent")
                mediaagent = True
        if not mediaagent:
            raise CVTestStepFailure("Validation of the worktokens failed")
            pass

    def verify_summary(self, ip1, ip2, creation):
        """Verifies the summary of both client and MA"""
        time.sleep(30)
        source_summary = self.source_client_obj.get_network_summary()
        destination_summary = self.destination_client_obj.get_network_summary()
        check1 = self.validate_dip(source_summary, self.tcinputs["SourceClient"], self.tcinputs['MediaAgent'],
                                   interface1=ip1, interface2=ip2)
        check2 = self.validate_dip(destination_summary, self.tcinputs['MediaAgent'], self.tcinputs["SourceClient"],
                                   interface1=ip2, interface2=ip1)
        if creation:
            if check1 and check2:
                return True
            else:
                return False
        else:
            if check1 == "passive" and not check2:
                return True
            elif check2 == "passive" and not check1:
                return True
            elif not check1 and not check2:
                return True
            return False

    @test_step
    def verify_dip_cg_client(self):
        """Configure DIP between CG and Client"""
        try:
            media_agent_interface = self.tcinputs["MediaAgentIP"]
            self.backupnetworks.add_backupnetworks(entity1=self._client_group_name1,
                                                   entity2=self.destination_client_obj.display_name,
                                                   interface2=media_agent_interface)
            self.validate_tokens()

            if not self.verify_summary(self.hostname1, media_agent_interface, True):
                raise CVTestStepFailure("DIP Settings have failed")

            self.backup_and_restore(None, self.tcinputs['MediaAgentIP'], Restore=self.restore)

            # Delete the dip and now validate
            self.backupnetworks.delete_backupnetworks(entity1=self._client_group_name1,
                                                      entity2=self.destination_client_obj.display_name)
            if not self.verify_summary(self.hostname1, media_agent_interface, False):
                raise CVTestStepFailure("DIP Settings have failed")

        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def verify_dip_client_cg(self):
        """Configure DIP between Client and Client group"""
        try:
            source_interface = self.tcinputs["SourceIP"]
            self.backupnetworks.add_backupnetworks(entity1=self.source_client_obj.display_name,
                                                   entity2=self._client_group_name2,
                                                   interface1=source_interface)
            self.validate_tokens()

            if not self.verify_summary(self.tcinputs["SourceIP"], self.hostname2, True):
                raise CVTestStepFailure("DIP settings failed")

            self.backup_and_restore(self.tcinputs['SourceIP'], None, Restore=self.restore)
            # Delete the DIP

            self.backupnetworks.delete_backupnetworks(entity1=self.source_client_obj.display_name,
                                                      entity2=self._client_group_name2)

            if not self.verify_summary(self.tcinputs["SourceIP"], self.hostname2, False):
                raise CVTestStepFailure("DIP settings failed")

        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def verify_dip_client_client(self):
        """Configure DIP between two clients and validate"""
        try:
            self.backupnetworks.add_backupnetworks(entity1=self.source_client_obj.display_name,
                                                   entity2=self.destination_client_obj.display_name,
                                                   interface1=self.tcinputs["SourceIP"],
                                                   interface2=self.tcinputs['MediaAgentIP'])
            self.validate_tokens()

            if not self.verify_summary(self.tcinputs["SourceIP"], self.tcinputs["MediaAgentIP"], True):
                raise CVTestStepFailure("DIP settings failed")

            self.backup_and_restore(self.tcinputs["SourceIP"], self.tcinputs["MediaAgentIP"], Restore=self.restore)

            # Delete the DIP configured and validate
            self.backupnetworks.delete_backupnetworks(entity1=self.source_client_obj.display_name,
                                                      entity2=self.destination_client_obj.display_name)
            if not self.verify_summary(self.tcinputs["SourceIP"], self.tcinputs["MediaAgentIP"], False):
                raise CVTestStepFailure("DIP settings failed")

        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def verify_dip_wildcard_cg_cg(self, hostname1, hostname2, wildcard1, wildcard2):
        """Verify the wildcard interface between group to group"""
        try:
            self.backupnetworks.add_backupnetworks(entity1=self._client_group_name1,
                                                   entity2=self._client_group_name2,
                                                   interface1=wildcard1,
                                                   interface2=wildcard2)
            self.validate_tokens()

            if not self.verify_summary(hostname1, hostname2, True):
                raise CVTestStepFailure("DIP settings failed")

            self.backup_and_restore(hostname1, hostname2, Restore=self.restore)

            # Delete the DIP configured and validate
            self.backupnetworks.delete_backupnetworks(entity1=self._client_group_name1,
                                                      entity2=self._client_group_name2)
            if not self.verify_summary(hostname1, hostname2, False):
                raise CVTestStepFailure("DIP settings failed")

        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def validate_dip_wildcard_cg_client(self, hostname1, hostname2, wildcard1):
        """Verify the wildcard interface between group to a client"""
        try:
            self.backupnetworks.add_backupnetworks(entity1=self._client_group_name1,
                                                   entity2=self.destination_client_obj.display_name,
                                                   interface2=hostname2,
                                                   interface1=wildcard1)
            self.validate_tokens()

            if not self.verify_summary(hostname1, hostname2, True):
                raise CVTestStepFailure("DIP settings failed")


            # Delete the DIP configured and validate
            self.backupnetworks.delete_backupnetworks(entity1=self._client_group_name1,
                                                      entity2=self.destination_client_obj.display_name)
            if not self.verify_summary(hostname1, hostname2, False):
                raise CVTestStepFailure("DIP settings failed")

        except Exception as e:
            raise CVTestStepFailure(e)

    @test_step
    def validate_dip_wildcard_client_cg(self, hostname1, hostname2, wildcard2):
        """Validate the DIP set between the client and client group with wildcard filter on client group"""
        try:
            self.backupnetworks.add_backupnetworks(entity1=self.source_client_obj.display_name,
                                                   entity2=self._client_group_name2,
                                                   interface1=hostname1,
                                                   interface2=wildcard2)
            self.validate_tokens()

            if not self.verify_summary(hostname1, hostname2, True):
                raise CVTestStepFailure("DIP settings failed")

            self.backup_and_restore(hostname1, hostname2, Restore=self.restore)

            # Delete the DIP configured and validate
            self.backupnetworks.delete_backupnetworks(entity1=self.source_client_obj.display_name,
                                                      entity2=self._client_group_name2)
            if not self.verify_summary(hostname1, hostname2, False):
                raise CVTestStepFailure("DIP settings failed")

        except Exception as e:
            raise CVTestStepFailure(e)

    def run(self):
        try:
            self.init_tc()
            self.navigate_to_dip()
            self.verify_dip_cg_client()
            self.verify_dip_client_cg()
            self.verify_dip_client_client()
            self.verify_dip_wildcard_cg_cg(self.hostname1, self.hostname2,
                                           self.hostname1.replace(self.hostname1.split('.')[0], "*"),
                                           self.hostname2.replace(self.hostname2.split('.')[0], "*"))
            self.validate_dip_wildcard_cg_client(self.hostname1, self.tcinputs["MediaAgentIP"],
                                                 self.hostname1.replace(self.hostname1.split('.')[0], "*"))

            self.validate_dip_wildcard_client_cg(self.tcinputs["SourceIP"], self.hostname2,
                                                 self.hostname2.replace(self.hostname2.split('.')[0], "*"))

            if self.tcinputs.get("SourceIPV6") and self.tcinputs.get("MediaAgentIPV6"):
                source_filter = self.tcinputs["SourceIPV6"].replace(self.tcinputs["SourceIPV6"].split(":")[0], "*")
                ma_filter = self.tcinputs["MediaAgentIPV6"].replace(self.tcinputs["MediaAgentIPV6"].split(":")[0], "*")
                self.verify_dip_wildcard_cg_cg(self.tcinputs["SourceIPV6"], self.tcinputs["MediaAgentIPV6"],
                                               source_filter, ma_filter)
                self.validate_dip_wildcard_cg_client(self.tcinputs["SourceIPV6"], self.tcinputs["MediaAgentIPV6"],
                                                     source_filter)
                self.validate_dip_wildcard_client_cg(self.tcinputs["SourceIPV6"], self.tcinputs["MediaAgentIPV6"],
                                                     ma_filter)

        except Exception as e:
            raise CVTestStepFailure(e)
        finally:
            self._network.entities.cleanup()
            self._network.cleanup_network()
            self.admin_console.logout_silently(self.admin_console)
            self.browser.close_silently(self.browser)

    def create_entities(self, client_name,
                        media_agent, test_data_path=None, test_data_level=1,
                        test_data_size=1):
        """Function to create entities for backup and restore jobs on a  client

                Args:
                        client_name(str)      -- client name

                        media_agent(str)        --  media agent to be used

                        test_data_path(str)     -- path to generate test data

                        test_data_level(int)    -- depth of folders under test data

                        test_data_size(int)     -- size of each test file to be generated in KB


        """
        # create disk library
        disklibrary_inputs = {
            'disklibrary': {
                'name': "disklibrary_" + media_agent,
                'mediaagent': media_agent,
                'mount_path': self._network.entities.get_mount_path(media_agent),
                'username': '',
                'password': '',
                'cleanup_mount_path': True,
                'force': False,
            }
        }
        self.log.info("Creating disk library using media agent {0}".format(media_agent))
        self._network.entities.create(disklibrary_inputs)
        # create storage policy
        storagepolicy_inputs = {
            'target':
                {
                    'library': "disklibrary_" + media_agent,
                    'mediaagent': media_agent,
                    'force': False
                },
            'storagepolicy':
                {
                    'name': "storagepolicy_" + media_agent,
                    'dedup_path': None,
                    'incremental_sp': None,
                    'retention_period': 3,
                },
        }
        self.log.info("Creating storage policy using library {0}".
                      format("disklibrary_" + media_agent))
        self._network.entities.create(storagepolicy_inputs)

        self.log.info("Creating subclient for client {0}".format(client_name))
        self.subclient_name = "subclient_" + client_name + self.option.get_custom_str()
        self.backupset_name = "backupset_" + client_name + self.option.get_custom_str()
        # create subclient
        subclient_inputs = {
            'target':
                {
                    'client': client_name,
                    'agent': "File system",
                    'instance': "defaultinstancename",
                    'storagepolicy': "storagepolicy_" + media_agent,
                    'force': True
                },
            'backupset':
                {
                    'name': self.backupset_name,
                    'on_demand_backupset': False,
                    'force': True,
                },

            'subclient':
                {
                    'name': self.subclient_name,
                    'client_name': client_name,
                    'backupset': self.backupset_name,
                    'data_path': test_data_path,
                    'level': test_data_level,
                    'size': test_data_size,
                    'description': "Automation - Target properties",
                    'subclient_type': None,
                }
        }
        self._network.entities.create(subclient_inputs)

        agent_obj = self.source_client_obj.agents.get('File System')
        backupset_obj = agent_obj.backupsets.get(self.backupset_name)
        self.subclient_obj = backupset_obj.subclients.get(self.subclient_name)

    def verify_logs(self, job, interface1, interface2, s_time, job_type):
        """Logs are validated with the interfaces"""
        client_machine = Machine(self.source_client_obj)
        media_agent = Machine(self.destination_client_obj)

        client_logs = client_machine.get_logs_for_job_from_file(job.job_id, f"cl{job_type}.log")
        self.log.info("restore logs : ")
        self.log.info(client_logs)
        client_cvfwd = client_machine.get_logs_after_time_t("cvfwd.log", s_time)

        media_cvfwd = media_agent.get_logs_after_time_t("cvfwd.log", s_time)
        interface_usage = 0

        for i in client_logs:
            if interface1 and (interface1 in i):
                if interface2 and (interface2 in i):
                    self.log.info("The backup/restore job using the interfaces configured ")
                    self.log.info(i)
                    interface_usage += 1
                    break
                else:
                    self.log.info("The backup/restore job using the interfaces configured ")
                    self.log.info(i)
                    interface_usage += 1
                    break

            elif interface2 and (interface2 in i):
                self.log.info("The backup/restore job using the interfaces configured ")
                self.log.info(i)
                interface_usage += 1
                break

        for i in client_cvfwd:
            if "Initialized" in i:
                if interface1 and (interface1 in i) \
                        and self.tcinputs["MediaAgent"] in i:
                    if interface2 and (interface2 in i):
                        self.log.info("The backup/restore job using the interfaces configured ")
                        self.log.info(i)
                        interface_usage += 1
                        break
                    else:
                        self.log.info("The backup/restore job using the interfaces configured ")
                        self.log.info(i)
                        interface_usage += 1
                        break

                elif interface2 and (interface2 in i) \
                        and self.tcinputs["MediaAgent"] in i:
                    self.log.info("The backup/restore job using the interfaces configured ")
                    self.log.info(i)
                    interface_usage += 1
                    break

        for i in media_cvfwd:
            if "Initialized" in i:
                if interface1 and (interface1 in i) and self.tcinputs["SourceClient"] in i:
                    if interface2 and (interface2 in i):
                        self.log.info("The backup/restore job using the interfaces configured ")
                        self.log.info(i)
                        interface_usage += 1
                        break
                    else:
                        self.log.info("The backup/restore job using the interfaces configured ")
                        self.log.info(i)
                        interface_usage += 1
                        break
                elif interface2 and (interface2 in i) and self.tcinputs["SourceClient"] in i:
                    self.log.info("The backup/restore job using the interfaces configured ")
                    self.log.info(i)
                    interface_usage += 1
                    break
        self.log.info(interface_usage)

        if not interface_usage:
            self.log.info("Couldn't find the DIPS configured used in logs for job")
            raise CVTestStepFailure("The DIP configuration is not used in Jobs ")

    def backup_and_restore(self, interface1, interface2, **kwargs):

        restore = kwargs.get("Restore")
        self.log.info(
            "Going to trigger backup job on Subclient: {0}".format(self.subclient_name))
        import datetime
        s_time = datetime.datetime.now()
        self.source_client_obj.restart_services(wait_for_service_restart=False)
        self.log.info("Restarting the services on client")
        self.option.sleep_time(15)

        job = self.serverbase.subclient_backup(self.subclient_obj, "full")

        job.wait_for_completion()

        self.verify_logs(job, interface1, interface2, s_time, "Backup")

        if restore:
            self.log.info("Successfully finished subclient full backup and validation")
            self.log.info("*" * 10 + " Run Restore out of place " + "*" * 10)
            # run restore in place job
            s_time = datetime.datetime.now()

            self.source_client_obj.restart_services(wait_for_service_restart=False)
            self.option.sleep_time(15)

            job = self.serverbase.subclient_restore_out_of_place(self.subclient_obj.content[0]
                                                                 + "\\RESTOREDATA",
                                                                 self.subclient_obj.content,
                                                                 self.tcinputs["SourceClient"],
                                                                 self.subclient_obj)

            self.verify_logs(job, interface1, interface2, s_time, "Restore")
