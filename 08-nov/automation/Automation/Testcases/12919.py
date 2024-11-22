
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright ©2018 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case
TestCase: Class for executing this test case

TestCase:
        __init__(): Initializes test case class object.
        full_backup(new_ad_objs): Runs full backup and restore.
        incremental_backup(new_ad_objs): Runs incremental backup and restore.
        sync_full_backup(new_ad_objs): Runs sync full backup and restore.
        cleanup(objs): Cleans up all objects in the list.
        setup(): Setup function of this test case.
        run(): Run function of this test case.
        teardown(): Teardown function of this test case.
"""

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Application.AD.ms_ad import ADOps, CVAD
from Application.AD.exceptions import ADException
from Web.Common.page_object import TestStep

class TestCase(CVTestCase):
    """Class for executing Basic functionality of Lotus Notes Database agent test case

    Attributes:
        test_step (TestStep): Instance of the TestStep class.

    Properties:
        name (str): Name of this test case.
        applicable_os (str): Applicable OS for this test case.
        product (str): Applicable product for AD.
        feature (str): Features of the test case.
        show_to_user (bool): True if the customer should see this test case.
        tcinputs (dict): Dictionary of test case inputs.
        subclientname (str): Subclient name.
        ad_ins (object): Application AD object.
        ad_basedn (str): AD object base DN.
    """

    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name                    (str)           --  name of this test case
                applicable_os           (str)           --  applicable os for this test case
                product                 (str)           --  applicable product for AD
                features                (str)           --  Backup and Restore
                show_to_user            (bool)          --  True, Customer should see this test case
                tcinputs                (dict)          --  dict of test case inputs
                    ClientName    (str)    -- required
                                                ClientName (Required)
                    AgentName     (str)    -- required
                                                "ACTIVE DIRECOTRY"
                    BackupsetName (str)    -- optional
                        Backupset Name,will use "defaultbaupset" if not specified
                    InstanceName  (str)    -- optional
                        Instance Name, will use "defaultinstancename" if not specified
                    SubclientName (str)    -- optional
                        Subclient Name, will use "TC_casenumber" if not specified
                    StoragePolicy (str)    -- optional
                        Storage Policy used for subclient
                    AD_server     (str)    -- optional
                        AD server to connect. wil connect to agent machine
                    AD_user       (str)    -- required
                        User to access AD
                        Currenlty, we need input, should get from cs
                    AD_password   (str)    -- required
                        password for AD_user
                subclientname      (str)        -- subclientclient name
                ad_ins             (object)     -- Application AD object
                ad_basedn          (str)        -- AD object base DN
        """
        super().__init__()
        self.name = "Active Directory - Basic Backup & Restore"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.ACTIVEDIRECTORY
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.ad_ins = None
        self.ad_basedn = ""
        self.domainname = ""
        self.subclientname = ""
        self.tcinputs = {
            "ClientName" : None,
            "AgentName" : "ACTIVE DIRECTORY",
            "StoragePolicy" : None,
            "AD_user" : None,
            "AD_password" : None,
        }
        self.ad_content = None
        self.restore_path = None
        self.cvad = None

        if "cleanup" in self.tcinputs:
            self.cleanup_objs = self.tcinputs['cleanup']
        else:
            self.cleanup_objs = True

    @test_step
    def full_backup(self, new_ad_objs):
        """
        Run full backup and restore

        Args:
            new_ad_objs (list): List of new AD objects to be backed up

        Returns:
            object: The result of the full backup operation
        """
        return self.cvad.simple_backup(backuptype="Full", objs=new_ad_objs)

    @test_step
    def incremental_backup(self, new_ad_objs):
        """
        Run incremental backup and restore

        Args:
            new_ad_objs (list): List of new Active Directory objects to be backed up

        Returns:
            object: The result of the simple backup operation

        """
        return self.cvad.simple_backup(backuptype="Incremental", objs=new_ad_objs)

    @test_step
    def sync_full_backup(self, new_ad_objs):
        """
        Run sync full backup and restore

        This method performs a sync full backup and restore operation. It takes a list of new Active Directory objects
        as input and returns the result of the backup operation.

        :param new_ad_objs: A list of new Active Directory objects to be backed up
        :type new_ad_objs: list
        :return: The result of the backup operation
        :rtype: str
        """
        return self.cvad.simple_backup(backuptype="synthetic_full", objs=new_ad_objs, incremental_backup=True)

    def cleanup(self, objs):
        """
        Clean up all objects in the list.

        Args:
            objs (list): A list of objects to be cleaned up.

        Returns:
            None

        """
        self.log.debug(f"start to clean up objects {objs}")
        self.ad_ins.cv_ugo_delete(objs, self.ad_content)
        self.log.debug("all objects are cleaned")

    def setup(self):
        """
        Setup function of this test case
        """
        self.log.debug(f"start to process testcase setup {self.name}")
        try:
            if "AD_server" not in self.tcinputs:
                self.log.debug("No AD server defined, will use agent hostname")
                ad_server = self.client.client_hostname
            else:
                ad_server = self.tcinputs['AD_server']
            ad_user = self.tcinputs['AD_user']
            ad_password = self.tcinputs['AD_password']
            self.log.debug(f"Will create AD objects with the following information:\n server: {ad_server}\n user: {ad_user}\n password: {ad_password}")
            self.ad_ins = ADOps(server=ad_server,
                                user=ad_user,
                                password=ad_password,
                                log=self.log)
            self.ad_basedn = self.ad_ins.ldap_info['basedn']
            self.log.debug(f"The AD object base dn is {self.ad_basedn}")
            if "BackupsetName" not in self.tcinputs:
                self.log.debug("No backupset is found in answer file, use defaultbackupset")
                self._backupset = self._agent.backupsets.get("defaultbackupset")
                self.log.debug(f"backupset object is created. The object is:{self._backupset}")

            if "SubclientName" not in self.tcinputs or self.tcinputs.get("SubclientName") is None:
                self.log.debug("No subclient is found in asnwer file, use default Name")
                self.subclientname = f"TC_{str(self.id)}"
                self.log.debug(f"No subclient name is assigned,will use default subclinet name: {self.subclientname}")
            else:
                self.subclientname = self.tcinputs.get("SubclientName")
            sc_content = [f"OU={self.ad_basedn},OU=Automation,OU={str(self.id)}"]
            self.subclient = self.backupset.check_subclient(\
                                self.backupset,\
                                self.subclientname,\
                                storagepolicy=self.tcinputs.get("StoragePolicy"),\
                                subclientcontent=sc_content)
            self.log.debug(f"subclient object is created. the object is:{self.subclient}")
            self.log.debug(f"Get all Content from subclient {self.subclientname}")
            if self.subclientname == "default":
                self.log.debug("using default subclient and hard code the path 'OU=12919,OU=Automation' ")
                default_container = 'OU=12919,OU=Automation'
                self.ad_content = [(default_container+","+self.ad_ins.basedn, default_container)]
                self.restore_path = "\\\\".join((default_container+","+self.ad_ins.basedn).split(",")[::-1])
                self.log.debug(f"hard code the restore path to {self.restore_path}")
            else:
                sc_contents = self.subclient.content
                sc_contentsdisplay = '\n'.join(sc_contents)
                self.log.debug(f"current subclient {self.subclientname} has the following content: {sc_contentsdisplay}")
                self.log.debug("Convert subclient content to AD format")
                self.ad_content = self.subclient.cv_contents(sc_contents, entrypoint=self.ad_ins.basedn)
            self.log.debug(f"subclient content in AD format:{self.ad_content}")
            self.cvad = CVAD(self.ad_ins, self.subclient, self.restore_path, self.ad_content)
            self.log.debug("setup phase is completed")
        except ADException as exp:
            self.status = constants.FAILED
            self.log.exception(f"there is exception happened, here is the detail {exp.report}")
        except Exception as exp:
            self.status = constants.FAILED
            self.log.exception(f"there is not AD exception happened, here is the detail {exp}")

    def run(self):
        """Run function of this test case"""
        try:
            self.log.debug(f"Get all Content from subclient {self.subclientname}")
            if self.subclientname == "default":
                self.log.debug("using default subclient and hard code the path 'OU=12919,OU=Automation' ")
                default_container = 'OU=12919,OU=Automation'
                self.ad_content = [(default_container+","+self.ad_ins.basedn, default_container)]
                self.restore_path = "\\\\".join((default_container+","+self.ad_ins.basedn).split(",")[::-1])
                self.log.debug(f"hard code the restore path to {self.restore_path}")
            else:
                sc_contents = self.subclient.content
                sc_contentsdisplay = '\n'.join(sc_contents)
                self.log.debug(f"current subclient {self.subclientname} has the following content: {sc_contentsdisplay}")
                self.log.debug("Convert subclient content to AD format")
                self.ad_content = self.subclient.cv_contents(sc_contents, entrypoint=self.ad_ins.basedn)
            self.log.debug(f"subclient content in AD format:{self.ad_content}")

            if self.cleanup_objs:
                ad_objlists_base = self.ad_ins.cv_ad_objectlist(self.ad_content)
                self.cleanup(ad_objlists_base)
            new_ad_objs = []

            new_ad_objs = self.full_backup(new_ad_objs)
            new_ad_objs = self.incremental_backup(new_ad_objs)
            new_ad_objs = self.sync_full_backup(new_ad_objs)
            self.cleanup_objs = new_ad_objs
            self.log.debug("run phase completed")
            self.status = constants.PASSED
            self.teardown()
        except ADException as exp:
            self.status = constants.FAILED
            self.log.exception(f"there is exception happened, here is the detail {exp.report}")
        except Exception as exp:
            self.status = constants.FAILED
            self.log.exception(f"there is not AD exception happened, here is the detail {exp}")

    def teardown(self):
        """Teardown function of this test case"""
        if self.cleanup_objs:
            self.cleanup(self.cleanup_objs)
        self.log.debug("tear down phase completed")
