# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright 2020 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Base class for all tests about the failover group.This is inherited from class
CVTestDROrchestration.

CVTestCaseFailoverGroup is the only class defined in this file.

CVTestCaseFailoverGroup: Class for executing this test case

CVTestCaseFailoverGroup:
    __init__()                      --  Initialize only variables related to `FailoverGroup`

    setup()                         --  Set up `self._replication_monitor` object,
                                        `self._src_vm_name`, and `self._dst_vm_name`

    run()                           --  Run function for the test case. This should be overridden.

    ##### internal methods #####
    _init_failover_group()          --  Initialize the `FailoverGroup` object

    _get_dst_vm_names()             --  Collectes all corresponding destination VM names

    ##### property methods #####
    _operation_validate_dr_orchestration_job    --  operation to validate DR orchestration jobs
                                                    from failover group

    _operation_testboot                         --  operation to run testboot from failover group

    _operation_planned_failover                 --  operation to run planned failover from
                                                    failover group

    _operation_unplanned_failover               --  operation to run unplanned failover from
                                                    failover group

    _operation_point_in_time_failover           --  operation to run point-in-time failover from
                                                    failover group

    _operation_failback                         --  operation to run failback from failover group

    _operation_undo_failover                    --  operation to run undo failover from failover
                                                    group

    _operation_schedule_reverse_replication     --  operation to schedule reverse replication from
                                                    failover group

    _operation_force_one_reverse_replication    --  operation to force one reverse replication from
                                                    failover group

"""

from cvpysdk.drorchestration.failovergroups import FailoverGroup, FailoverGroups

from VirtualServer.DROrchestration.cvtestcase_drorchestration import CVTestDROrchestration
from VirtualServer.VSAUtils import VirtualServerHelper, VirtualServerConstants
from VirtualServer.VSAUtils.HypervisorHelper import Hypervisor


class CVTestCaseFailoverGroup(CVTestDROrchestration):
    """Class for test cases about the failover group."""

    def __init__(self):
        super(CVTestCaseFailoverGroup, self).__init__()

        # collection of source vm names to be tested
        self._src_vm_names = []
        # collection of destination vm names to be tested
        self._dst_vm_names = []

        # will be initialized in the `setup()`
        self._failover_group = None

        self._dest_auto_client = None

        self.tcinputs.update({
            "failoverGroupName": ""
        })

    def setup(self):
        """Initializes all member variables for later use."""
        super(CVTestCaseFailoverGroup, self).setup()

        try:
            self._failover_group = self._init_failover_group()

            self._src_vm_names = list(map(
                lambda x: x["clientName"],
                self._failover_group.failover_group_properties["clientList"]))
            self._dst_vm_names = self._get_dst_vm_names()
            self.log.info(
                "Found src VM \"%s\" and dst VM \"%s\"",
                str(self._src_vm_names),
                str(self._dst_vm_names))
            self._dest_hypervisor = self._init_dest_hypervisor()
        except Exception as exp:
            self.log.error(str(exp))
            raise Exception("Failed during `setup()`.")

    def run(self):
        """This should be overridden by child classes."""
        raise NotImplementedError(
            "`run` is not implemented by its child class.")

    @property
    def _operation_validate_dr_orchestration_job(self):
        """Returns the operation to validate DR orchestration jobs"""
        return self._failover_group.validate_dr_orchestration_job

    @property
    def _operation_testboot(self):
        """Returns the operation to run testboot"""
        return self._failover_group.testboot

    @property
    def _operation_planned_failover(self):
        """Returns the operation to run planned failover"""
        return self._failover_group.planned_failover

    @property
    def _operation_unplanned_failover(self):
        """Returns the operation to run unplanned failover"""
        return self._failover_group.unplanned_failover

    @property
    def _operation_point_in_time_failover(self):
        """Returns the operation to run point-in-time failover"""
        return self._failover_group.point_in_time_failover

    @property
    def _operation_failback(self):
        """Returns the operation to run failback"""
        return self._failover_group.failback

    @property
    def _operation_undo_failover(self):
        """Returns the operation to run undo failover"""
        return self._failover_group.undo_failover

    @property
    def _operation_schedule_reverse_replication(self):
        """Returns the operation to schedule reverse replication"""
        return self._failover_group.schedule_reverse_replication

    @property
    def _operation_force_one_reverse_replication(self):
        """Returns the operation to force one reverse replication"""
        return self._failover_group.force_reverse_replication

    @property
    def _replication_ids(self) -> [int]:
        """Returns the list of replications IDs"""
        return self._failover_group._replication_Ids

    def _init_failover_group(self) -> FailoverGroup:
        """Initializes the `FailoverGroup` object.

        This should only be used in `setup()`. Making this a function helps
        shorten the length of `setup()`.
        """
        self.log.info("Started to initialize a `FailoverGroup` object.")
        try:
            failover_group = FailoverGroups(
                self._commcell, self.instance).get(
                    self.tcinputs)
        except Exception as exp:
            raise Exception(
                "Failed to initialize a `FailoverGroup` object: {}".format(exp))
        self.log.info("Initialization of `FailoverGroup` object finished.")
        return failover_group

    def _get_dst_vm_names(self):
        """Collectes all corresponding destination VM names"""
        dst_vm_names = []
        for client in self._failover_group.failover_group_properties["clientList"]:
            entity_id = client["clientId"]
            client_list_req = (self.commcell._services['FAILOVER_GROUP_MACHINES']
                               if self._commcell.commserv_version > 30
                               else self.commcell._services['DR_GROUP_MACHINES']) % entity_id

            (flag, response) = self.commcell._cvpysdk_object.make_request(
                method='GET', url=client_list_req)
            if flag:
                res_json = response.json()
                if res_json and 'client' in res_json and len(
                        res_json['client']) > 0 and 'destClient' in res_json['client'][
                            0] and 'GUID' in res_json['client'][0]['destClient']:
                    dst_vm_names.append(
                        res_json['client'][0]['destClient']['clientName'])
                    if not self._dest_auto_client:
                        self._dest_auto_client = res_json['client'][0]['destinationClient']['clientName']
                else:
                    raise Exception(
                        "Failed to fetch client list through {}.".format(client_list_req))
            else:
                response_string = self.commcell._update_response_(
                    response.text)
                raise Exception(
                    "Failed to fetch client list through {}: {}.".format(
                        client_list_req, response_string))

        return dst_vm_names

    def _init_dest_hypervisor(self) -> Hypervisor:
        """Initializes the `Hypervisor` object.

        This should only be used in `setup()`. Making this a function helps
        shorten the length of `setup()`.
        """
        self.log.info("Started to initialize the destination `Hypervisor` object.")
        try:
            client = self.commcell.clients.get(self._dest_auto_client)
            agent = client.agents.get(self.tcinputs['AgentName'])
            instance = agent.instances.get(self.tcinputs['InstanceName'])
            auto_commcell = VirtualServerHelper.AutoVSACommcell(
                self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(
                auto_commcell, client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(
                auto_client, agent, instance)
            hypervisor = auto_instance.hvobj
        except Exception as exp:
            raise Exception(
                "Failed to initialize the `Hypervisor` object: "
                "{}.".format(exp))
        self.log.info("Initialization of `Hypervisor` object finished.")
        return hypervisor
