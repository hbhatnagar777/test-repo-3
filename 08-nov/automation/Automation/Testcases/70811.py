# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to validate download and install service pack on the CS.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:

    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

"""

from AutomationUtils import config
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Install import installer_utils
from Install.softwarecache_helper import SoftwareCache
from Install.updatecenterhelper import Buildhelper
from Install.install_validator import InstallValidator
from Install.precerthelper import RegistryManager
from Install.installer_constants import (
    REG_INTEGRATION_BATCH_MEDIA, BATCHBUILD_CURRENTBATCHSTAGE, BATCHBUILD_PRECERT_MEDIA_SUCCESS,
    REG_INTEGRATION_VALUE_BATCH, BATCHBUILD_PRECERT_COMPLETE
)
from cvpysdk.deployment.deploymentconstants import (
    UnixDownloadFeatures, WindowsDownloadFeatures
)

class TestCase(CVTestCase):
    """Class for executing Push Service Pack upgrades of CS"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Precert Updatecenter specific operations"
        self.install_helper = None
        self.download_helper = None
        self.config_json = None
        self.cs_machine = None
        self.commcell = None
        self.result_string = ''
        self.status = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.spname = self.tcinputs.get("servicepack")
        self.primaryvalue = self.tcinputs.get("primary")
        self.skip_freshinstall = self.tcinputs.get("skipfreshinstall",0)
        self.cs_machine = Machine(
            machine_name=self.config_json.Install.commserve_client.machine_host,
            username=self.config_json.Install.commserve_client.machine_username,
            password=self.config_json.Install.commserve_client.machine_password
        )
        self.local_machine = self.autocenter.controller
        self.build_helper = Buildhelper()
        self.download_helper = SoftwareCache(self.commcell)
        installed_spinfo = self.download_helper.current_cs_media.split("_")
        self.installed_spnum = str(installed_spinfo[0])
        self.installed_transnum = str(installed_spinfo[1])
        self.installed_revnum = str(installed_spinfo[2].replace("R", ""))
        self.build_helper.get_build_id(
            self.installed_revnum, self.installed_transnum, self.installed_spnum
        )
        precert_data = self.build_helper.get_precert_mode()
        self.media,self.cupack,self.bupdate,self.statuscode, self.statusmsg = precert_data
        self.log.info(f"Media: {self.media}, CU Pack: {self.cupack}, Bupdate: {self.bupdate}, Status code: {self.statuscode}, Status message: {self.statusmsg}")
        self.log.info("Creating Precert speficic registry entries")
        self.regmgr = RegistryManager(
            self.local_machine, self.build_helper, self.primaryvalue, self.log)
        self.primary = int(self.regmgr.primary)
        self.integrationtype = self.regmgr.integration_type
        self.integrattionmode = self.regmgr.integration_mode
        self.log.info(f"Primary node value: {self.primary}")
        self.log.info(f"Integration type: {self.integrationtype}")
        self.log.info(f"Integration mode: {self.integrattionmode}")

    def run(self):
        """Main function for test case execution"""
        try:
            _sp_transaction = installer_utils.get_latest_recut_from_xml(self.spname)
            latest_cu_filer = installer_utils.get_latest_cu_from_xml(_sp_transaction)
            build_recutnum = self.build_helper.get_media_recut_info(self.installed_spnum, 1)
            if not build_recutnum:
                raise Exception("Failed to run the query for reading build team database.")

            self.log.info("Checking Readiness of the CS machine")
            _commserv_client = self.commcell.commserv_client
            if _commserv_client.is_ready:
                self.log.info("Check Readiness of CS successful")
            else:
                self.log.error("Check Readiness Failed")
                raise Exception("Check Readiness Failed")

            self.log.info("Getting the installed SP number, transaction number and revision number from cache")

            self.download_helper = SoftwareCache(self.commcell)
            installed_spinfo = self.download_helper.current_cs_media.split("_")
            self.installed_spnum = str(installed_spinfo[0])
            self.installed_transnum = str(installed_spinfo[1])
            self.installed_revnum = str(installed_spinfo[2].replace("R", ""))

            installed_spinfo_onfiler = _sp_transaction.split("_")
            filer_installed_spnum = str(installed_spinfo[0])
            filer_installed_transnum = str(installed_spinfo[1])
            filer_installed_revnum = str(
                installed_spinfo_onfiler[2].replace("R", ""))

            self.build_helper.get_build_id(
                self.installed_revnum, self.installed_transnum, self.installed_spnum
            )
            self.log.info(f"Installed SPnum {self.installed_spnum}, installed transaction number: {self.installed_transnum} Recut number: {self.installed_revnum}")

            package_list = [UnixDownloadFeatures.COMMSERVE.value] if self.commcell.is_linux_commserv \
                else [WindowsDownloadFeatures.COMMSERVE.value]
            install_validation = InstallValidator(
                _commserv_client.client_hostname, self,
                machine_object=self.cs_machine, package_list=package_list,
                feature_release=_sp_transaction, is_push_job=True
            )

            media  = 1 if self.integrationtype == REG_INTEGRATION_BATCH_MEDIA else 0

            if media:
                build_recutinfo = self.build_helper.get_media_recut_info(
                    self.installed_spnum, 0)                
            else:
                build_recutinfo = self.build_helper.get_media_recut_info(
                self.installed_spnum, 1)
            build_recutnum = str(build_recutinfo[3])
            build_recut_transnumber = str(build_recutinfo[2])

            if build_recutnum != self.installed_revnum and build_recutnum != filer_installed_revnum:
                self.log.error(
                    f"Recut number mismatch: cache: {self.installed_revnum} and filer :{filer_installed_revnum} : BuildDB :{build_recutnum}")
                raise Exception(
                    f"Recut number mismatch: cache: {self.installed_revnum} and filer :{filer_installed_revnum} : BuildDB :{build_recutnum}")
            if filer_installed_transnum != self.installed_transnum and build_recut_transnumber != self.installed_transnum:
                self.log.error(
                    f"transaction number mismatch: cache: {self.installed_transnum} ,  filer :{filer_installed_transnum}, build {build_recut_transnumber}")
                raise Exception(
                    f"transaction number mismatch: cache: {self.installed_transnum} and filer :{filer_installed_transnum}")           

            self.log.info(
                f"Installed SPnum {self.installed_spnum}, installed transaction number: {self.installed_transnum} Recut number: {self.installed_revnum}")

            if self.primary:
                self.log.info(
                    f"Starting Install Validation on Primary node for Unix machine")                
                visibility = 1
                if media:
                    visibility = 0
                self.log.info("Check fresh install test case staus") 
                fresinstall_requestid = self.regmgr.fresh_install_requestid  
                if self.skip_freshinstall:
                    self.log.info("User opted to skip fresh install test case validation")  
                elif fresinstall_requestid is not None:
                    self.log.info(f"Check automation.log for the request status: {fresinstall_requestid}")
                    request_status = self.autocenter.check_precert_status(fresinstall_requestid,max_attempts=60,log=self.log)
                    self.log.info(f"Request  {fresinstall_requestid} status: {request_status}")
                    if request_status != 0:
                        raise Exception(f"Fresh install request {fresinstall_requestid} not Passed. It might be  failed")
                    self.log.info("Fresh install request is passed, setting visibility to 1")
                    visibility = 1
                    self.log.info("Deleting the fresh install request id {fresinstall_requestid} ")
                    self.regmgr.delete_fresh_install_requestid()
                
                #Check windows precert status
                self.log.info(f"Check log for the request status: {self.autocenter.request_id}")
                win_request_status = self.autocenter.check_precert_status(self.autocenter.request_id,max_attempts=60,log=self.log)
                self.log.info(f"Request  {self.autocenter.request_id} status: {win_request_status}")
                if win_request_status != 0:
                    raise Exception(f"Windows request {self.autocenter.request_id} not Passed. It might be failed or still running")                    

                self.releasedupdates = self.build_helper.get_released_updates()
                cacheupdate_numbers, latest_cu_folder = install_validation.get_looseupdates_fromcache()
                non_precertified_update_numbers = []
                non_precertified_update_numbers = list(
                    set(cacheupdate_numbers) - set(self.releasedupdates))
                self.log.info(
                    f"Cacheupdae numbers after doing set with released updates:  {non_precertified_update_numbers}")
                
                status = "Certified" 
                if len(non_precertified_update_numbers) > 0:
                    self.build_helper.certify_and_setvisibility(non_precertified_update_numbers, self.installed_spnum, self.installed_revnum,
                             visibility = 1, status=status)
                else:
                    self.log.error("No loose updates found in Cache")
                if latest_cu_folder and self.cupack != "Certified" :
                    cunumber = int(latest_cu_folder.replace("CU", ""))
                    if cunumber != int(latest_cu_filer):
                        self.log.error(
                            f"Latest CU folder{cunumber}is not matching with the latest CU {latest_cu_filer} from the XML")
                        raise Exception(
                            f"Latest CU folder{cunumber}is not matching with the latest CU {latest_cu_filer} from the XML")
                    self.build_helper.certify_and_setvisibility(non_precertified_update_numbers, self.installed_spnum, self.installed_revnum, 
                                                                visibility = visibility, status=status,bupdate = 0, cupack=cunumber, media = media)

                media  = 1 if self.integrationtype == REG_INTEGRATION_BATCH_MEDIA else 0
                batch_mode = 1 if self.integrationtype == REG_INTEGRATION_VALUE_BATCH else 0
                if media:
                    self.log.info("Marking Media mode as success")
                    self.build_helper.modify_build_property(BATCHBUILD_CURRENTBATCHSTAGE, BATCHBUILD_PRECERT_MEDIA_SUCCESS)
                elif batch_mode:
                    self.log.info("Marking Batch mode as success")
                    self.build_helper.modify_build_property(BATCHBUILD_CURRENTBATCHSTAGE, BATCHBUILD_PRECERT_COMPLETE)

            self.result_string = "Passed"
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
