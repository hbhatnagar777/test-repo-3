# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    run()                       --  run function of this test case


Input Example:

    "testCases":
            {
                "58930": {
                    "Clients":  List of clients' instances to check for     (list)
                                OR
                                Name of client group    (str)
                }
            }

"""

from cvpysdk.schedules import Schedules
from cvpysdk.clientgroup import ClientGroup
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Web.Common.page_object import TestStep, handle_testcase_exception


class TestCase(CVTestCase):
    """ Class for validation of Database Agents schedules association with Default plan"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Database Agents schedules association with Default plan"
        self.db_agents = ['mysql', 'oracle', 'oracle rac', 'postgresql',
                          'db2', 'db2 multinode', 'informix', 'sap for oracle',
                          'sap hana', 'sql server', 'sybase', 'cloud apps']
        self.tcinputs = {
            "Clients": None
        }

    def run(self):
        """ Main function for test case execution """
        try:
            all_clients = True
            dict_db_agents = {db_agent: [] for db_agent in self.db_agents}
            failed_instances = ["", "="*100, "Instances not associated with plan schedule:"]
            if isinstance(self.tcinputs["Clients"], list):
                client_list = self.tcinputs["Clients"]
            else:
                client_list = ClientGroup(self.commcell,
                                          self.tcinputs["Clients"]).associated_clients
            for client in client_list:
                self.client = self.commcell.clients.get(client)
                agents = self.client.agents.all_agents
                for agent in agents:
                    if agent in self.db_agents:
                        agent_obj = self.client.agents.get(agent)
                        instances = agent_obj.instances.all_instances
                        for instance in instances:
                            instance_obj = agent_obj.instances.get(instance)
                            if 'planEntity' in instance_obj.properties:
                                dict_db_agents[agent].append(instance_obj)
            if 0 in [len(num_db_agents) for num_db_agents in list(dict_db_agents.values())]:
                raise Exception("Ensure all clients have at least one DB agent installed and"
                                " every agent has at least one instance associated with a plan")

            self.log.info("Instances list for checking : %s", dict_db_agents)
            self.log.info("Instances associated with plan schedule:")
            for agent in dict_db_agents:
                for instance in dict_db_agents[agent]:
                    incremental = synth_full = log_rpo = False
                    schedules_dict = Schedules(instance).schedules
                    schedule_names = []
                    for schedule in schedules_dict.values():
                        schedule_names.append(schedule['schedule_name'])
                    incremental = 'incremental backup schedule' in schedule_names
                    synth_full = 'synthetic fulls' in schedule_names
                    if agent in ['informix', 'db2', 'db2 multinode', 'cloud apps']:
                        log_rpo = True
                    else:
                        log_rpo = 'incremental automatic schedule for logs' in schedule_names
                    if not (incremental and synth_full and log_rpo):
                        all_clients = False
                        log_line = f"'{instance.instance_name}' instance of" \
                            f" {instance.properties['instance']['appName']} agent of" \
                            f" client '{instance.properties['instance']['clientName']}'" \
                            f" is NOT associated with plan schedule"
                        failed_instances.append(log_line)
                    else:
                        self.log.info("'%s' instance of %s agent of client '%s' is associated"
                                      " with plan schedule", instance.instance_name,
                                      instance.properties['instance']['appName'],
                                      instance.properties['instance']['clientName'])

            if not all_clients:
                failed_instances.append("="*100)
                self.log.info("\n".join(failed_instances))
                self.status = constants.FAILED

        except Exception as exp:
            handle_testcase_exception(self, exp)
