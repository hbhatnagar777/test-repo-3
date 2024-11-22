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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

TestCase Inputs [Optional inputs have defaults]:
    local_cs_is_source  (bool)  --  True if testcase is run from source cs, False if destination cs
                                    default: False

    [Second CS Info]
    cs_hostname (str)           --  hostname of the other commcell
    cs_username (str)           --  username to access other commcell
    cs_password (str)           --  password to access other commcell

    [Vcenter Info]
    vcenter_hostname    (str)   --  hostname of vcenter
    vcenter_username    (str)   --  username to access vcenter to create vsa clients
    vcenter_password    (str)   --  password to access vcenter to create vsa clients
    above 3 defaults taken from config["Laptop"]["Install"]["HyperV..."],

    [Network Info]
    share_name          (str)   --  name of network share for export or import folder
                                    default: determined from network share path
    share_username      (str)   --  username to access network share
    share_password      (str)   --  password to access network share
    above 2 defaults taken from config["Laptop"]["Install"]["Network..."],

    [CCM Folder Info]
    import_location     (str)   --  network share or local folder path to parent directory for import
                                    default: E:\\autoimports (will be created if it doesn't exist)
    export_location     (str)   --  network share or local folder path to parent directory for export
                                    default: will be determined from import location after network share
    [VM Info]
    discovered_vm   (str)       --  name of VM to test merge on
                                    default: clone_test linux VM

    source_options or dest_options  (dict)  --  options nested inside tcinputs, under source_options or dest_options
        [Storage]
            "media_agent"   (str): media agent for storage if library not given [default: CS client]
            "mount_path"    (str): mount path for library if library not given [default: E:\\source_lib or dest_lib]
            "library":      (str): library name if policy not given [default: source_lib or dest_lib]
            "policy":       (str): policy name if subclient not given [default: source_policy or dest_policy]
        [VM Entities]
            "pseudo_client" (str): parent vcenter client name [default: source_vcenter or dest_vcenter]
            "vcenter_proxy" (str): vsa proxy for vcenter client [default: CS client]
            "backupset"     (str): vm subclient's backupset [default: source_backupset or dest_backupset]
            "subclient"     (str): vm subclient name [default: source_subclient or dest_subclient]
        [FS Entities]
            "fs_client"     (str): fs client name [default: source_fsclient or dest_fsclient]
            "fs_backupset"  (str): fs backup set [default: source_fsbackupset or dest_fsbackupset]
            "fs_subclient"  (str): fs subclient [default: source_fssubclient or dest_fssubclient]
            "fs_content"    (str): fs content [default: C:\\Users\\Administrator\\Documents]
        [FS Installation]
            "fsmachine_hostname"    (str): hostname of machine to remote install on
            "fsmachine_username"    (str): username to access the machine
            "fsmachine_password"    (str): password to access the machine
            defaults are taken from config["Laptop"]["Install"]["windows"],

        Note: Entities will be reused if already exist, creation will only take place as a last resort
"""
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from Server.CommcellMigration.ccmhelper import CCMVSAHelper
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """Class for executing this Test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.dest_helper = None
        self.src_helper = None

        self.name = "CCM Merging VSA Clients v2 to v1"
        self.tcinputs = {
            "cs_hostname": None,
            "cs_username": None,
            "cs_password": None,
        }

    def setup(self):
        """Setup function of this test case"""
        local_src = bool(self.tcinputs.get('local_cs_is_source'))
        other_commcell = Commcell(
            self.tcinputs["cs_hostname"], self.tcinputs["cs_username"], self.tcinputs["cs_password"]
        )
        source_cs = self.commcell if local_src else other_commcell
        dest_cs = other_commcell if local_src else self.commcell

        self.src_helper = CCMVSAHelper(source_cs, True, 2, self.tcinputs)
        self.dest_helper = CCMVSAHelper(dest_cs, False, 1, self.tcinputs)

        self.src_helper.setup_entities()
        self.dest_helper.setup_entities()

        self.src_helper.setup_job()
        self.dest_helper.setup_job()

        self.src_helper.setup_ccm_folder()
        self.dest_helper.setup_ccm_folder()

    def run(self):
        """Main function for test case execution"""
        self.src_helper.perform_ccm_operation()
        self.dest_helper.perform_ccm_operation()
        self.log.info("-----------CCM VALIDATION-----------")
        errors = self.dest_helper.verify_jobs_merge()
        if errors:
            for err in errors:
                self.log.error(err)
            raise CVTestStepFailure("Jobs failed to migrate!")
        else:
            self.log.info("------------CCM VALIDATION PASSED!------------")
