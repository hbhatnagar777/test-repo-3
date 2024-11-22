# --------------------------------------------------------------------------
# See LICENSE.txt in the project root for
# license information
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this tesc case
"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils, VirtualServerHelper
from AutomationUtils import logger
from VirtualServer.VSAUtils.VirtualServerUtils import decorative_log


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of Vmware Browse performance test"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Vmware Browse performance test"

    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()

        try:
            log.info("Started executing %s testcase", self.id)
            VirtualServerUtils.decorative_log("Initialize helper objects")
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            # checking if any jobs to be backup copied
            auto_commcell.run_backup_copy(auto_subclient.storage_policy)
            # Running snap job
            VirtualServerUtils.decorative_log("Starting Snap Job")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)
            # Running backup copy jobs
            auto_commcell.run_backup_copy(auto_subclient.storage_policy)
            # checking for browse time
            browsetime = [True, False]  # Reg key on is True
            finaltime = []
            for each in browsetime:
                browsetime = auto_subclient.get_browse_time(self.subclient.storage_ma,
                                                             self.subclient.subclient_id,
                                                             self.tcinputs.get(
                                                                 'copyprecedence'),
                                                             auto_subclient.subclient.content[0]['id'],
                                                              each)
                finaltime.append(browsetime)
            decorative_log('Browse times' + str(finaltime))
            if finaltime[0] < finaltime[1] and (
                finaltime[0]) < self.tcinputs.get(
                    'time'):
                decorative_log(
                    'browse looks good' + str(finaltime[1] - finaltime[0]))
            else:
                self.log.error(
                    ' browse time took more time than expected')
                raise Exception
        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
