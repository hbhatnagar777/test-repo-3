# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
TestCase is the only class defined in this file.

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case

    Input Example:

    "testCases": {

        "59378": {
            "api_server_endpoint": "https://10.0.0.0:6443",
            "authentication": "Service account",
            "secretName": "test-sa",
            "secretKey": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "access_node": "autonode",
            "MasterNode": "10.0.0.0",
            "Username": "root",
            "Password": "12345",
            "ScriptsFile": "/auto",
            "plan": "auto_plan",
            "StorageType": "auto_storage"
        }
    }
"""
import time
from Reports.utils import TestCaseUtils

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import config

from Web.Common.cvbrowser import BrowserFactory
from Web.Common.cvbrowser import Browser
from Web.Common.exceptions import CVTestCaseInitFailure

from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Helper.k8s_helper import K8sHelper


CONSTANTS = config.get_config()


class TestCase(CVTestCase):
    """TestCase to create kubernetes cluster, backup and restore from admincnonsole
        This test case does the following
        1) Connect to kubernetes master node, setup testbed
           (create namespace, deploy test pods, list pod and upload test data to pod)
        2) log into command center, create Kubernetes cluster and add application groups if
           cluster with same name exist, delete it and recreate)
        3) from command center, run full backup job for newly created application group
           and verify job complete
        4) from command center, initiate manifest restore and wait for restore job complete
        5) connect to k8s master node, verify the restored manifest match with current running
           namespace/pod/pvc
        7) from command center, initiate full application out of place restore and wait for
           restore job complete
        8) connect to k8s master node, verify the restored data match with source pod data
            a. download source pod data to master node local path
            b. download the restored pod data to master node local path
            c. verify the restored pod data match with source pod data
        9) connect to kubernetes master node, add more data and upload to pod
        10) from command center, run incremental backup job and verify job completes
        11) from command center, initiate manifest restore and wait for restore job complete
        12) connect to k8s master node, verify the restored manifest match with current running
            namespace/pod/pvc
        13) from command center, initiate full application out of place restore and wait
            for restore job complete
        14) connect to k8s master node, verify the restored data match with source pod data
            a. download source pod data to master node local path
            b. download the restored pod data to master node local path
            c. verify the restored pod data match with source pod data
        15) download source pod data to master node local path
        16) cleanup source namespace
        17) from command center, initiate full application in place restore and wait
            for restore job complete
        18) connect to k8s master node, verify the restored data match with source pod data
            a.download the restored pod data to master node local path
            b. verify the restored pod data match with source pod data
        19) from command center, initiate volume and data out of place restore and wait
            for restore job complete
        20) connect to k8s master node, verify data are restored correctly
        21) from command center, initiate volume and data in place restore with
            unconditional overwrite option
        22) connect to k8s master node, verify data are restore correctly
        23) connect to kubernetes master node, clean up test bed
        24) delete the test kubernetes cluster
        25) log out from command center and close the browser
    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Kubernetes - create cluster, backup and restore from admin console"
        self.utils = TestCaseUtils(self)
        self.browser = None
        self.admin_console = None
        self.k8s_server_name = None
        self.k8s = None
        self.tcinputs = {
            "api_server_endpoint": None,
            "authentication": None,
            "secretName": None,
            "secretKey": None,
            "access_node": None,
            "MasterNode": None,
            "Username": None,
            "Password": None,
            "plan": None,
            "StorageType": None
        }

    def setup(self):
        """Initializes object required for this testcase"""
        self.k8s_server_name = "automated_K8s_server_59378"
        self.k8s_application_group_name = "automated_K8s_application_group"
        self.namespace = "automated59378"
        self.restore_namespace = "restoretest59378"
        self.tcinputs.update({"Namespace": "automated59378"})
        self.tcinputs.update({"RestoreNamespace": "restoretest59378"})

    def init_tc(self):
        """Initialize browser and redirect to required report page"""
        try:
            self.browser = BrowserFactory().create_browser_object()
            self.browser.open()
            self.admin_console = AdminConsole(
                self.browser, self.commcell.webconsole_hostname)
            self.admin_console.login()
        except Exception as _exception:
            raise CVTestCaseInitFailure(_exception) from _exception

    def run(self):
        try:
            self.init_tc()
            self.k8s = K8sHelper(self.admin_console, self)

            self.k8s.populate_test_data()
            self.k8s.create_k8s_cluster()
            self.k8s.verify_backup(backup_level=Backup.BackupType.FULL)

            # after full backup, manifest restore and verification
            self.k8s.verify_manifest_restore_job()
            self.k8s.verify_restored_manifest()

            # after full backup, full application out of place restore
            # and verification
            self.k8s.verify_fullapp_restore_job(inplace=False)
            self.k8s.download_src_pod_data()
            self.k8s.download_rst_pod_data()
            time.sleep(60)
            self.k8s.verify_restore_data()

            # after full backup, volume and data out of place restore
            # self.k8s.verify_volumedata_restore_job(inplace=False)

            # self.k8s.kubehelper.populate_tc_inputs(self)
            self.k8s.populate_test_data(jobtype='INCR')
            self.k8s.verify_backup(backup_level=Backup.BackupType.INCR)

            # after incremental backup, manifest restore and verification
            self.k8s.verify_manifest_restore_job()
            self.k8s.verify_restored_manifest()

            # after incremental job, full application out of place restore
            # and verification
            self.k8s.delete_and_recreate_namespace(self.restore_namespace)
            self.k8s.verify_fullapp_restore_job(inplace=False)
            self.k8s.download_src_pod_data()
            self.k8s.download_rst_pod_data()
            time.sleep(60)
            self.k8s.verify_restore_data()

            # after incremental backup, full application in place restore
            # and verification
            self.k8s.download_src_pod_data()
            self.k8s.verify_fullapp_restore_job(inplace=True)
            self.k8s.restore_namespace = self.k8s.namespace
            self.k8s.download_rst_pod_data()
            time.sleep(60)
            self.k8s.verify_restore_data()

            # delete the kubernetes seudo client and clean up the test data
            self.k8s.delete_k8s_cluster()
            self.k8s.cleanup_testdata()

        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            Browser.close_silently(self.browser)
