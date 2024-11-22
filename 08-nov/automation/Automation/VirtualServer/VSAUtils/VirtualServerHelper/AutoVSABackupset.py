# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Backupset Helper

classes defined:
    AutoVSABackupset  - wrapper for VSA Backupset Operations
"""


class AutoVSABackupset(object):
    """
    class for performing backupset operations. it acts as wrapper for Testcase and SDK
    """

    def __init__(self, instance_obj, backupset):
        """
        Initialize SDK objects

        Args:
            backupset   (obj)   - object for backupset class in SDK
        """
        self.auto_vsainstance = instance_obj
        self.auto_commcell = self.auto_vsainstance.auto_vsaclient.auto_commcell
        self.log = self.auto_vsainstance.log
        self.vsa_agent = self.auto_vsainstance.vsa_agent
        self.backupset = backupset
        self.backupset_name = self.backupset.backupset_name
        self.backupset_id = self.backupset.backupset_id
