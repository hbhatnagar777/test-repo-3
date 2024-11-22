from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from MediaAgents.MAUtils.hyperscale_helper import HyperScaleHelper
from MediaAgents.MAUtils.hyperscale_setup import HyperscaleSetup

class TestCase(CVTestCase):
    """HS Automation: 2x: Offline platform upgrade using metadata.tar from cloud.commvault.com"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "HS Automation: 2x: Offline platform upgrade using metadata.tar from cloud.commvault.com"
        self.result_string = ""
        self.tcinputs = {
            "InstallerPath": None,
            "LogFilePath": None,
            # "CacheNodeUsername": None, this has to be root itself
            "CacheNodePassword": None,
            "CacheNodeHostname": None
        }
        self.successful = False

    def setup(self):
        """Initializes test case variables"""
        
        # MA setup
        self.cache_node_username = 'root' # self.tcinputs["CacheNodeUsername"] # This has to be root
        # TODO: add support for cvbackupadmin user as well

        self.cache_node_password = self.tcinputs["CacheNodePassword"]
        self.cache_node_hostname = self.tcinputs["CacheNodeHostname"]
        self.installer_path = self.tcinputs["InstallerPath"]
        self.log_file_path = self.tcinputs["LogFilePath"]

        self.hyperscale_helper = HyperScaleHelper(self.commcell, self.csdb, self.log)
        
        result = self.hyperscale_helper.determine_remote_caches([self.cache_node_hostname])
        if len(result) != 1:
            raise Exception(f"Please make sure that the {self.cache_node_hostname} is actually the remote cache")
        
        result, reason = HyperscaleSetup.ensure_root_access(commcell=self.commcell, node_hostnames=[self.cache_node_hostname], node_root_password=self.cache_node_password)
        if not result:
            raise Exception(f"Failed to enable root: {reason}")

    def tear_down(self):
        """Tear down function for this test case"""
        if self.successful:
            self.log.info(f"Test case successful.")
        else:
            self.log.warning("Test case failed")
            self.status = constants.FAILED

    def fail_test_case(self, reason):
        """Prints failure reason, sets the result string

            Args:

                reason         (str)   --  Failure reason

        """
        self.log.error(reason)
        self.result_string = reason

    def run(self):
        """ run function of this test case"""
        try: 
            
            result = HyperscaleSetup.cvoffline_main(
                self.installer_path, self.log_file_path, self.cache_node_hostname, self.cache_node_username, self.cache_node_password)
            if not result: 
                reason = "Offline upgrade has failed"
                return self.fail_test_case(reason)

            self.successful = True
            self.log.info(f"Offline upgrade successfully executed")


        except Exception as exp:
            self.result_string = str(exp)
            self.log.exception("Exception message while executing test case: %s",
                               self.result_string)