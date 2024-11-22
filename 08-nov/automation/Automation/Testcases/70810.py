# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for license information.
# ---------------------------------------------------------------------

"""Main file for executing this test case.

Test cases to validate download and install service pack on the CS.

TestCase is the only class defined in this file.

TestCase:
    Class for executing this test case.

TestCase:
    __init__()                  --  initialize TestCase class.
    setup()                     --  setup function of this test case.
    run()                       --  run function of this test case.
"""
import os
from AutomationUtils import config
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase
from Install import installer_utils
from Install.update_helper import UpdateHelper
from Install.softwarecache_helper import SoftwareCache
from Install.updatecenterhelper import Buildhelper
from Install.install_validator import InstallValidator
from Install.precerthelper import RegistryManager
from Install.installer_constants import (
    REG_FRESH_INSTALL_REQUESTID, BATCHBUILD_CURRENTBATCHSTAGE, BATCHBUILD_PRECERT_MEDIA_SUCCESS, REG_INTEGRATION_BATCH_MEDIA
)
from cvpysdk.deployment.deploymentconstants import (
    DownloadPackages, DownloadOptions, UnixDownloadFeatures, WindowsDownloadFeatures
)


class TestCase(CVTestCase):
    """Class for executing Push Service Pack upgrades of CS"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = "Precert Commserver Download and install validations"
        self.install_helper = None
        self.update_helper = None
        self.tcinputs = {
            'servicepack': None,
            'primary': None,
            'testsetid': None
        }
        self.download_helper = None
        self.config_json = None
        self.cs_machine = None
        self.commcell = None
        self.result_string = ''
        self.status = None
        self.csobj = None
        self.primary = None

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.config_json = config.get_config()
        self.spname = self.tcinputs.get("servicepack")
        self.testsetid = self.tcinputs.get("testsetid")
        self.primaryvalue = self.tcinputs.get("primary")        
        self.cs_machine = Machine(
            machine_name=self.config_json.Install.commserve_client.machine_host,
            username=self.config_json.Install.commserve_client.machine_username,
            password=self.config_json.Install.commserve_client.machine_password
        )
        self.update_helper = UpdateHelper(self.commcell, self.cs_machine)
        self.local_machine = Machine()
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

        #self.cupack = "Pending"           
        
        self.log.info("Creating Precert speficic registry entries")
        self.regmgr = RegistryManager(
            self.local_machine, self.build_helper, self.primaryvalue, self.log)
        self.regmgr.create_registry()
        
        self.primary = int(self.regmgr.primary)
        self.integrationtype = self.regmgr.integration_type
        self.integrattionmode = self.regmgr.integration_mode
        self.log.info(f"Primary node value: {self.primary}")
        self.log.info(f"Integration type: {self.integrationtype}")
        self.log.info(f"Integration mode: {self.integrattionmode}")
        self.log.info(self.config_json.Install.download_server)        

    def run(self):
        """Main function for test case execution"""
        try:
            _sp_transaction = installer_utils.get_latest_recut_from_xml(
                self.spname)
            latest_cu_filer = installer_utils.get_latest_cu_from_xml(_sp_transaction)
            build_recutnum = self.build_helper.get_media_recut_info(
                self.installed_spnum, 1)
            if not build_recutnum:
                raise Exception(
                    "Failed to run the query for reading build team database.")
            fresinstall_requestid = self.regmgr.fresh_install_requestid            
            
            if self.primary and (self.media != "Certified" or self.cupack != "Certified" ) and fresinstall_requestid is None:
                self.log.info(f"Precert Running Fresh install testset because of  new media {self.media} or CU already certified {self.cupack}")
                request_id= self.autocenter.run_testset(self.testsetid)
                self.log.info(f"Submitted Request [{request_id}] for Fresh install testset: {self.testsetid}")
                self.regmgr._create_or_update_registry(self.regmgr.regkey, REG_FRESH_INSTALL_REQUESTID, request_id)

            job_obj = self.commcell.download_software(
                options=DownloadOptions.SERVICEPACK_AND_HOTFIXES.value,
                os_list=[package.value for package in DownloadPackages],
                service_pack=self.spname,
                cu_number=latest_cu_filer
            )
            self.log.info("Job %s started", job_obj.job_id)
            if job_obj.wait_for_completion():
                self.log.info("Download Software Job Successful")
            else:
                raise Exception("Download job failed")

            self.log.info(f"Starting Service pack upgrade of CS from "
                          f"SP{str(self.commcell.commserv_version)} to {self.spname}")
            self.update_helper.push_sp_upgrade(
                client_computers=[self.commcell.commserv_client.client_name], download_software=True,all_updates=True)
            self.log.info("SP upgrade of CS successful")

            _commserv_client = self.commcell.commserv_client
            if _commserv_client.is_ready:
                self.log.info("Check Readiness of CS successful")
            else:
                self.log.error("Check Readiness Failed")
                raise Exception("Check Readiness Failed")
            self.log.info("Run Fresh install based on New Media or CU pack")
            
            
            self.log.info("Starting Install Validation")
            self.log.info(
                "Getting the installed SP number, transaction number and revision number from cache")
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

            # Get the Latest Media Recut information from updatecenter DB, if media use 0 means no-precertified media.
            #1 for certified media
            
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

            if filer_installed_spnum != self.installed_spnum:
                self.log.eror(
                    f"SP number mismatch: cache: {self.installed_spnum } and filer :{filer_installed_spnum} ")
                raise Exception(
                    f"SP number mismatch: cache: {self.installed_spnum } and filer :{filer_installed_spnum} ")

            if filer_installed_transnum != self.installed_transnum and build_recut_transnumber != self.installed_transnum:
                self.log.error(
                    f"transaction number mismatch: cache: {self.installed_transnum} ,  filer :{filer_installed_transnum}, build {build_recut_transnumber}")
                raise Exception(
                    f"transaction number mismatch: cache: {self.installed_transnum} and filer :{filer_installed_transnum}")           

            self.log.info(
                f"Installed SPnum {self.installed_spnum}, installed transaction number: {self.installed_transnum} Recut number: {self.installed_revnum}")

            package_list = [UnixDownloadFeatures.COMMSERVE.value] if self.commcell.is_linux_commserv else [
                WindowsDownloadFeatures.COMMSERVE.value]
            self.log.info("Creating Install validator object")
            install_validation = InstallValidator(
                _commserv_client.client_hostname, self,
                machine_object=self.cs_machine, package_list=package_list,
                feature_release=_sp_transaction, is_push_job=True
            )
            self.log.info("Doing Install validation")
            install_validation.validate_install(validate_mongodb=False)

            self.log.info("""Performing Databaseupgrade, please check the Databaseupgrade.log on commserver
                          It can take time up to 30-60 minutes""")
            self.update_helper.commserv_dbupgrade(self.cs_machine, install_validation.installation_path, _commserv_client.log_directory)

            self.log.info("Doing Install validation")
            install_validation.validate_install(validate_mongodb=False)
            

            if self.primary:
                self.log.info(
                    f"Starting Install Validation on Primary node for Unix machine")
                self.releasedupdates = self.build_helper.get_released_updates()
                cacheupdate_numbers, latest_cu_folder = install_validation.get_looseupdates_fromcache()

                non_precertified_update_numbers = []
                non_precertified_update_numbers = list(
                    set(cacheupdate_numbers) - set(self.releasedupdates))
                self.log.info(
                    f"Cacheupdae numbers after doing set with released updates:  {non_precertified_update_numbers}")

                status = "InProgress"
                if len(non_precertified_update_numbers) > 0:
                    self.build_helper.certify_and_setvisibility(non_precertified_update_numbers, self.installed_spnum, self.installed_revnum,
                            visibility = 0, status=status)
                else:
                    self.log.error("No loose updates found in Cache")

                if latest_cu_folder and self.cupack != "Certified":
                    cunumber = int(latest_cu_folder.replace("CU", ""))
                    if cunumber != int(latest_cu_filer):
                        self.log.error(
                            f"Latest CU folder{cunumber}is not matching with the latest CU {latest_cu_filer} from the XML")
                        raise Exception(
                            f"Latest CU folder{cunumber}is not matching with the latest CU {latest_cu_filer} from the XML")
                    values = self.build_helper.certify_and_setvisibility(non_precertified_update_numbers, self.installed_spnum, self.installed_revnum, 
                                                                visibility = 0, status=status,bupdate = 0, cupack=cunumber, media = media)
                    
            self.result_string = "Passed"
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED
