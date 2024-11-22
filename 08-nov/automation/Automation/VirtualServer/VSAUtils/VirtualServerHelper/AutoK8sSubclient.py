# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Class for Subclient
classes defined:
    AutoK8sSubclient  - wrapper for Kubernetes VSA Subclient operations

"""
from VirtualServer.VSAUtils.VirtualServerHelper import AutoVSASubclient


class AutoK8sSubclient(AutoVSASubclient):
    """
    class for performing subclient operations. It act as wrapper for Testcase and SDK
    """

    def __init__(self, backupset_obj, subclient):
        """
        Initialize subclient SDK objects

        Args:
            subclient (obj) - object of subclient class of SDK
        """

        self.auto_vsa_backupset = backupset_obj
        self.log = self.auto_vsa_backupset.log
        self.auto_vsainstance = self.auto_vsa_backupset.auto_vsainstance
        self.auto_vsaclient = self.auto_vsainstance.auto_vsaclient
        self.auto_commcell = self.auto_vsainstance.auto_commcell
        self.csdb = self.auto_commcell.csdb
        self.subclient = subclient
        self.subclient_name = self.subclient.subclient_name
        self.subclient_id = self.subclient.subclient_id
        self._browse_ma_id = self.subclient.storage_ma_id
        self._browse_ma = self.subclient.storage_ma
        self.ma_machine = None
        self._controller_machine = None
        self.restore_obj = None
        self.backup_option = None
        self.current_job = None
        self.testcase_id = ''

    # Other functions to be added later
