# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file to implement helper functions for control plane recovery.

ControlPlaneRecoveryhelper: Class for validations on SERVER cache operations

ClientsCacheValidator:

    __init__()                           --   This class implements helper functions for control plane recovery of a cs

    wait_until_vm_is_recovered()         --   This method waits until given request id is successfully completed

    start_recovery_of_latest_backupset() --   This method gets the latest backupset of commcell and starts a recovery


"""
import time
from cvpysdk.cleanroom.cs_recovery import CommServeRecovery
from cvpysdk.commcell import Commcell
from AutomationUtils import logger


class ControlPlaneRecoveryhelper:
    """This class implements helper functions for control plane recovery of a commserver"""

    def __init__(self, cloud_commcell_obj: Commcell, cs_guid: str):
        """Method to initialize ControlPlaneRecoveryhelper object"""
        self.cloud_commcell_obj = cloud_commcell_obj
        self.cs_guid = cs_guid
        self.cs_recovery = CommServeRecovery(self.cloud_commcell_obj, self.cs_guid)
        self.log = logger.get_log()

    def wait_until_vm_is_recovered(self, reqid: int):
        """
        This method waits until given request id is successfully completed
        Args:
            reqid (int): request id of the commserve recovery request
        """
        for _ in range(6):
            self.log.info("waiting for 10 minutes for the cs to be recovered")
            time.sleep(600)
            details = self.cs_recovery.get_vm_details(reqid)
            if details:
                self.log.info(f"CS is recovered. Waiting for 10 minutes buffer time")
                self.log.info(f"VM Access Details : {details}")
                time.sleep(600)
                return details
        self.log.info(f"VM Access Details : {details}")
        raise Exception("CS Recovery time limit exceeded. Recovery did not complete in 50 mins.")

    def start_recovery_of_latest_backupset(self):
        """
        This method gets the latest backupset of commcell and starts a recovery
        Returns:
            Request id (id) of the generated request
        """
        backupsets = self.cs_recovery.backupsets
        latest_backupset_name = max(list(backupsets.keys()), key=lambda name: int(name[4:]))
        self.log.info(f"starting recovery on latest backupset {latest_backupset_name}")
        return self.cs_recovery.start_recovery(latest_backupset_name)
