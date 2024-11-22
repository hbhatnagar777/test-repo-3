# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: executes nfs lock test and validates test results.

"""
import sys
import re

from AutomationUtils.cvtestcase import CVTestCase
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper
from Server.NFSObjectStore.NFSObjectStoreHelper import ObjectstoreClientUtils as NFSutils
from Server.serverhelper import ServerTestCases

NFSTEST_LOCK_Path = "/usr/bin/nfstest_lock"


class TestCase(CVTestCase):
    """Class for executing nfs file lock tests for Linux HFS server"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = " nfs file lock tests for Linux HFS server"
        self.product = self.products_list.OBJECTSTORE
        self.feature = self.features_list.OBJECTSTORENFS
        self.applicable_os = self.os_list.LINUX
        self.show_to_user = True
        self.tcinputs = {
            'NFSServerHostName': None,
            'clientHostname': None,
            'clientUsername': None,
            'clientPassword': None,
            'indexServerMA': None,
            'storagePolicy':None
        }
        self.nfsutil_obj = None
        self.NFS_server_obj = None
        self.server = None

    def check_pre_requsists(self):
        # check if client is Linux client
        if not self.nfsutil_obj.machine_obj.os_info.lower() == "unix":
            raise Exception("{0} client should be Linux client".format(self.tcinputs[clientHostname]))

        # check if nfstest_lock is installed on the client
        if not self.nfsutil_obj.machine_obj.check_file_exists(NFSTEST_LOCK_Path):
            raise Exception("nfstest_lock is not found at {0} on "
                            "client {1}".format(NFSTEST_LOCK_Path,
                                                self.tcinputs['clientHostname']))

    def execute_nfs_test_lock(self):
        # example command to run nfs_test_lock test suite
        # nfstest_lock --server 172.24.42.135 --export /nfslocktest --mtpoint /tmp/nfslock
        _cmd = "{0} --server {1} --export /{2} -mtpoint {3}".format(NFSTEST_LOCK_Path,
                                                                    self.tcinputs['NFSServerHostName'],
                                                                    self.nfsutil_obj.Obj_store_name,
                                                                    self.nfsutil_obj.mount_dir)
        self.log.info("executing nfs_lock tests, command used {0}".format(_cmd))
        output = self.nfsutil_obj.machine_obj.execute_command(_cmd)
        self.log.info("nfs lock tests completed")

        # it is expected to see the summary at last but 4th line. example output is below
        # 282 tests (281 passed, 1 failed)
        summary = output.output.split('\n')[-4]
        if "passed" not in summary or "failed" not in summary:
            raise Exception("couldn't find the expected summary line in test output"
                            "nfs lock test output:{0}".format(output.output))

        self.log.info("nfs lock test summary {0}".format(summary))
        _match = re.search("(.*) tests \((.*) passed, (.*) failed\)", summary)

        if _match is None or len(_match.groups()) != 3:
            raise Exception("expected summary not found in the nfs_test_lock test output.\n"
                            "output: %s" % output.output)

        total_tests, tests_passed, tests_failed = [_match.group(1), _match.group(2), _match.group(3)]
        if int(tests_failed):
            raise Exception("nfs_test_lock() has failures. All tests are expected to pass."
                            "test output:\n %s" % output.output)
        self.log.info("all tests in nfs_test_lock() are passed. Summary: {0}".format(summary))

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")
        self.server = ServerTestCases(self)

        try:
            self.nfsutil_obj = NFSutils(self.tcinputs['clientHostname'],
                                        self.tcinputs['clientUsername'],
                                        self.tcinputs['clientPassword'],
                                        self.id,
                                        self.commcell)
            self.check_pre_requsists()

            self.NFS_server_obj = NFSHelper(self.tcinputs['NFSServerHostName'],
                                            self.commcell,
                                            self.inputJSONnode['commcell']['commcellUsername'],
                                            self.inputJSONnode['commcell']['commcellPassword'],
                                            self.tcinputs['storagePolicy'])

            self.log.info("Creating Object Store : {0}".format(self.nfsutil_obj.Obj_store_name))
            self.NFS_server_obj.create_nfs_objectstore(
                                                        self.nfsutil_obj.Obj_store_name,
                                                        self.NFS_server_obj.storage_policy,
                                                        self.tcinputs['indexServerMA'],
                                                        self.tcinputs['NFSServerHostName'],
                                                        self.tcinputs['clientHostname'],
                                                        squashing_type="NO_ROOT_SQUASH",
                                                        delete_if_exists=True)
        except Exception as excp:
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.server.fail(excp, "test case failed in setup function")

    def run(self):
        """Main function for test case execution"""
        try:
            self.execute_nfs_test_lock()
        except Exception as excp:
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.server.fail(excp, "test case failed in run function")

    def tear_down(self):
        """Tear down function"""
        self.NFS_server_obj.delete_nfs_objectstore(self.nfsutil_obj.Obj_store_name,
                                                   delete_user=True)
