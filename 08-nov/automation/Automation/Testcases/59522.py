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
            "StorageType": "auto_storage",
            "regkeyserver": "https://index.docker.io/v1/",
            "dockerusername": "auto1234",
            "dockerpassword": "auto",
            "dockeremail": "auto@auto.com"
        }
    }
"""

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
           namespace/pod/pvc/statefullset
        7) from command center, initiate full application out of place restore and wait for
           restore job complete
        8) connect to cassandra/mongo db, verify the restored db data are correct
        9) connect to kubernetes master node, add more db data
        10) from command center, run incremental backup job and verify job completes
        11) from command center, initiate full application out of place restore and wait
            for restore job complete
        12) connect to cassandra/mongo db, verify the restored db data are correct
        13) from command center, initiate full application in place restore and wait
            for restore job complete
        14) connect to cassandra/mongo db, verify the restored db data are correct
        23) connect to kubernetes master node, clean up test bed
        24) delete the test kubernetes cluster
        25) log out from command center and close the browser
    """

    def __init__(self):
        super(TestCase, self).__init__()
        self.name = "Kubernetes - multiple applications backup and restore from admin console"
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
            "StorageType": None,
            "regkeyserver": None,
            "dockerusername": None,
            "dockerpassword": None,
            "dockeremail": None
        }

    def setup(self):
        """Initializes object required for this testcase"""
        self.k8s_server_name = "automated_K8s_server_59522"
        self.k8s_application_group_name = "automated_K8s_application_group"
        self.namespace = "automated59522"
        self.restore_namespace = "restoretest59522"
        self.cassandra_namespace = "cassandra59522"
        self.cassandra_restore_namespace = "rescass59522"
        self.cassandra_keyspace = "auto59522"
        self.cassandra_tablename = "automatedtable"
        self.mongo_namespace = "mongo59522"
        self.mongo_restore_namespace = "resmon59522"
        self.tcinputs.update({"Namespace": "automated59522"})
        self.tcinputs.update({"RestoreNamespace": "restoretest59522"})
        self.tcinputs.update({"cassandra_namespace": "cassandra59522"})
        self.tcinputs.update({"cassandra_restore_namespace": "rescass59522"})
        self.tcinputs.update({"mongo_namespace": "mongo59522"})
        self.tcinputs.update({"mongo_restore_namespace": "resmon59522"})
        self.tcinputs.update({"cassandra_keyspace": "auto59522"})
        self.tcinputs.update({"cassandra_tablename": "automatedtable"})

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
            self.k8s = K8sHelper(self.admin_console, self, db=True)
            self.k8s.populate_cassandra_mongo_db()
            self.k8s.create_k8s_cluster(db=True)
            self.k8s.verify_backup(backup_level=Backup.BackupType.FULL)

            # manifest restore and verification
            self.k8s.namespace = self.cassandra_namespace
            self.k8s.verify_manifest_restore_job()
            self.k8s.verify_restored_manifest()
            self.k8s.namespace = self.mongo_namespace
            self.k8s.verify_manifest_restore_job()
            self.k8s.verify_restored_manifest()

            # drop application data from source namespace and run full
            # application inplace restore
            self.k8s.drop_db_data(self.cassandra_namespace)
            self.k8s.verify_fullapp_restore_job(inplace=True)
            self.k8s.verify_db_restore_data(
                self.cassandra_namespace, self.mongo_namespace)

            # full application out of place restore and verification
            self.k8s.verify_fullapp_restore_job(
                inplace=False, app=True, dbs=[
                    "cassandra", "mongo"])
            self.k8s.verify_db_restore_data(
                self.cassandra_restore_namespace,
                self.mongo_restore_namespace)

            # add more data and run inc job
            self.k8s.populate_cassandra_mongo_db(jobtype='INCR')
            self.k8s.verify_backup(backup_level=Backup.BackupType.INCR)

            # drop application data from source namespace and run full
            # application inplace restore
            self.k8s.drop_db_data(self.cassandra_namespace)
            self.k8s.verify_fullapp_restore_job(inplace=True)
            self.k8s.verify_db_restore_data(
                self.cassandra_namespace, self.mongo_namespace)

            # full application out of place restore and verification
            self.k8s.verify_fullapp_restore_job(
                inplace=False, app=True, dbs=[
                    "cassandra", "mongo"])
            self.k8s.verify_db_restore_data(
                self.cassandra_restore_namespace,
                self.mongo_restore_namespace)

            # delete the kubernetes seudo client and clean up the test data
            self.k8s.delete_k8s_cluster()
            self.k8s.cleanup_db_testdata()

        except Exception as error:
            self.utils.handle_testcase_exception(error)
        finally:
            Browser.close_silently(self.browser)
