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

"""

from VirtualServer.VSAUtils import VirtualServerUtils, OptionsHelper
from AutomationUtils.cvtestcase import CVTestCase

from Web.AdminConsole.VSAPages.manage_content import ManageContent
from Web.AdminConsole.VSAPages.vm_groups import VMGroups
from Web.AdminConsole.VSAPages.vsa_subclient_details import VsaSubclientDetails
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory
from Web.Common.page_object import handle_testcase_exception


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Azure VM Filters Validation"
        self.product = self.products_list.VIRTUALIZATIONAZURE
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.show_to_user = True
        self.tcinputs = {}

    def setup(self):
        """Setup function of this test case"""
        self.log.info("Initializing browser objects")
        factory = BrowserFactory()
        self.browser = factory.create_browser_object()
        self.browser.open()

        self.log.info("Creating a login object")
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'],
                                 stay_logged_in=True)
        self.vsa_subclient = VsaSubclientDetails(self.admin_console)
        self.navigator = self.admin_console.navigator
        self.vm_group_obj = VMGroups(self.admin_console)

    def validate_vm_preview(self):
        # Validate if preview vm list has no filtered VMs
        self.vsa_subclient.manage_content()
        preview_vms = self.manage_content_obj.preview().keys()
        self.log.info(f"VMs in preview: {preview_vms}")
        assert set(preview_vms) == set(self.auto_subclient.vm_list)
        self.log.info("Preview VM list has no filtered VMs. Proceeding with Backup.")

    def validate_backedup_vms(self):
        # Validate no filtered VMs were backed up
        backup_job_id = self.auto_subclient.backup_job.job_id
        backedup_vms = self.auto_subclient.get_vms_from_backup_job(backup_job_id)
        self.log.info(f"Backed up VMs: {backedup_vms}")
        self.log.info(f"VM List: {self.auto_subclient.vm_list}")
        assert set(backedup_vms) == set(self.auto_subclient.vm_list)
        self.log.info("Backed up VMs list has no filtered VMs")

    def run(self):
        """Run function of this test case"""
        try:
            self.navigator.navigate_to_vm_groups()
            self.vm_group_obj.select_vm_group(self.tcinputs['SubclientName'])
            self.manage_content_obj = ManageContent(self.admin_console)

            self.vsa_subclient.manage_content()
            self.vm_group_obj.clear_vm_filters()

            self.manage_content_obj.filters(self.tcinputs['vm_filters'])

            # Initializing subclient object with updated content
            self.reinitialize_testcase_info()
            self.auto_subclient = VirtualServerUtils.subclient_initialize(self)

            self.validate_vm_preview()

            # Run backup
            VirtualServerUtils.decorative_log("Backup VMs")
            backup_options = OptionsHelper.BackupOptions(self.auto_subclient)
            backup_options.backup_method = "SNAP"
            self.auto_subclient.backup(backup_options)

            self.validate_backedup_vms()
            self.log.info("Successfully validated VM Filtering")
            self.log.info("Testcase completed successfully")

        except Exception as exp:
            handle_testcase_exception(self, exp)

        finally:
            # remove vm filters
            self.vsa_subclient.manage_content()
            self.vm_group_obj.clear_vm_filters()

    def tear_down(self):
        """Tear down function of this test case"""
        self.browser.close()
