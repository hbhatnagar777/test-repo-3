# -*- coding: utf-8 -*-
# ————————————————————————–
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ————————————————————————–

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Verifies PIT view has the expected content with proper meta data from NFS share.

"""
import sys
import os
import tempfile

from AutomationUtils.cvtestcase import CVTestCase
from Server.NFSObjectStore.NFSObjectStoreHelper import NFSServerHelper as NFSHelper
from Server.NFSObjectStore.NFSObjectStoreHelper import ObjectstoreClientUtils as NFSutils
from AutomationUtils.commonutils import download_url
from Server.serverhelper import ServerTestCases

class TestCase(CVTestCase):
    """Class for executing Basic functionality verification for NFS objectstore PIT views"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "NFS ObjectStore: Basic tests on PIT view for NFS client"
        self.product = self.products_list.OBJECTSTORE
        self.feature = self.features_list.OBJECTSTORENFS
        self.applicable_os = self.os_list.LINUX
        self.show_to_user = True
        self.retval = 0
        self.tcinputs = {
            'NFSServerHostName': None,
            'ClientHostName': None,
            'ClientUserName': None,
            'ClientPassword': None,
            'IndexServerMA': None,
            'PynfsInstallPath': None
        }
        self.nfsutil_obj = None
        self.NFS_server_obj = None
        self.expected_dir_details = None
        self.objstore_test_path = None
        self.snap_test_path = None
        self.pynfs_install_path = None
        self._default_testnfs_install_path = "/CVAutomation/testpynfs"
        self.test_server_path = None
        self.master_zip_file_path = None
        self.server = None

    def download_pynfs_from_git(self, download_dir):
        """download pynfs test suite from git website.

            Args:
                download_dir   (str)     -- directory on controller machine where package will be downloaded

            Returns:
                full path of downloaded zip file
        """
        _master_zip_url = "https://github.com/kofemann/pynfs/archive/master.zip"
        _download_file_path = os.path.join(download_dir, _master_zip_url.split('/')[-1])
        download_url(_master_zip_url, _download_file_path)
        return _download_file_path

    def install_dependencies(self, machine_obj, packages):
        """Installs dependent packages to run pynfs server tests

            Args:
                machine_obj   (object)     -- client machine object where packages need to be installed

                packages      (str)     -- list of valid RPM pcakges separated by space

            Returns:
                None
        """
        # to keep it simple lets just check yum is present
        if not machine_obj.check_file_exists("/usr/bin/yum"):
            raise Exception("yum is not present in client machine %s" % machine_obj.machine_name)

        _cmd = "/usr/bin/yum install --assumeyes %s " % packages
        output = machine_obj.execute_command(_cmd)

        if output.exit_code:
            raise Exception("yum install failed with error %s" % output.exception_message)
        
        # Pynfs has now shifted to Python 3 so we have to install python 3 
        # to check if Python3 is already Present in the given machine
        if not machine_obj.check_file_exists("/usr/bin/python3"):
            self.log.error("Python 3 not present in the system")
            self.log.info("Installing python 3.6")
            cmd = "sudo yum install python36 -y"
            output = machine_obj.execute_command(cmd)
            if output.exit_code:
                raise Exception("Python 3 installation failed due to %s "% output.exception_message)

    def install_pynfs(self, machine_obj, master_zip_path):
        """ It install pynfs test suite on the test client machine. Performs the below steps
                1. copies master zip file from controller machine to test client machine.
                2. unzip zip package
                3. build test suite

            Args:
                machine_obj          (object)     -- client machine object where packages need to be installed

                master_zip_path      (str)     -- downloaded pynfs package on controller machine

            Returns:
                None
        """
        _packages = "krb5-devel python-devel swig python-gssapi python-ply"

        self.install_dependencies(machine_obj, _packages)
        if not machine_obj.check_directory_exists(self._default_testnfs_install_path):
            machine_obj.create_directory(self._default_testnfs_install_path)

        machine_obj._copy_file_from_local(master_zip_path, self._default_testnfs_install_path)
        zip_file_name = os.path.basename(master_zip_path)

        zip_file_path = machine_obj.join_path(self._default_testnfs_install_path, zip_file_name)
        machine_obj.unzip_zip_file(zip_file_path, where_to_unzip=self._default_testnfs_install_path)
        unzip_path = self._default_testnfs_install_path
        build_path = machine_obj.join_path(unzip_path, "pynfs-master")
        # install ply modules for successful build of pynfs
        self.log.info("Installing ply module")
        cmd = "pip3 install ply"
        output = machine_obj.execute_command(cmd)
        if output.exit_code:
            raise Exception("Error in installing ply module due to %s" % output.output)
        build_cmd = "cd %s;./setup.py build" % build_path
        output = machine_obj.execute_command(build_cmd)
        if 'changing mode of build' not in output.output:
            raise Exception("pynfs build failed %s" % output.output)

    def parse_test_server_output_content(self, output):
        """ Parses test server output to look for any new failures. Currently there are some known failures.
            Note: Once known issues are fixed. known_failures list need to be updated.

            Args:
                output             (str)     -- output of testserver.py test run

            Returns:
                object - instance of the RpoHelper class
        """
        known_failures = ["RNM1d", "RNM20", "RNM17", "RNM14", "RNM12", "RNM13", "SEQ6", "EID50"]
        new_failures = []
        for line in output.split('\n'):
            if 'FAILURE' in line:
                if 'st_' not in line:
                    self.log.error("unexpected line '%s' in test output" % line)
                    continue
                else:
                    if line.split()[0] not in known_failures:
                        new_failures.append(line.split()[0])

        if bool(new_failures):
            self.log.error("there are new test failures. testserver output\n: %s" % output)
            raise Exception("there are new test failures. Failures list %s" % known_failures)
        else:
            self.log.info("pynfs test for server is successful")

    def run_pynfs_server_tests(self, nfs_server, share_name, machine_obj, pynfs_install_path):
        """ execute testserver pynfs tests on client machine

            Args:
                nfs_server      (str)     -- hostname of nfs server to be used

                share_name      (str)     -- objectstore name to be used for testing

                machine_obj          (object)     -- media agent name

                pynfs_install_path      (object)  --  name of the storage policy to be used

            Returns:
                object - instance of the RpoHelper class
        """
        test_exclusions = "noblock nochar nofifo nosocket nospecial"
        test_server_path = machine_obj.join_path(pynfs_install_path, "pynfs-master", "nfs4.1")
        _cmd = "cd {0}; ./{1} --maketree {2}:/{3} all {4}".format(test_server_path,
                                                                  "testserver.py",
                                                                  nfs_server,
                                                                  share_name,
                                                                  test_exclusions)
        self.log.info("executing command %s" % _cmd)
        output = machine_obj.execute_command(_cmd)
        if output.exit_code:
            raise Exception("failed to run testserver pynfs tests %s" % output.exception)
        self.log.debug("output of testserver %s" % output.output)
        self.parse_test_server_output_content(output.output)

    def setup(self):
        """ Setup function of this test case """
        self.log.info("executing testcase")
        self.server = ServerTestCases(self) # added by h
        self.nfsutil_obj = NFSutils(self.tcinputs['ClientHostName'],
                                    self.tcinputs['ClientUserName'],
                                    self.tcinputs['ClientPassword'],
                                    self.id,
                                    self.commcell)

        _default_test_server_path = self.nfsutil_obj.machine_obj.join_path(self._default_testnfs_install_path,
                                                   "pynfs-master/nfs4.1/testserver.py")
        if not self.tcinputs['PynfsInstallPath']:
            self.log.info("PynfsInstallPath is not passed to the test. Will try to use from default path")
            if not self.nfsutil_obj.machine_obj.check_file_exists(_default_test_server_path):
                self.log.info("pynfs testserver is not found at default path %s" % _default_test_server_path)
            else:
                self.test_server_path = self._default_testnfs_install_path
        else:
            self.test_server_path = self.tcinputs['PynfsInstallPath']

        if self.test_server_path is None:
            self.log.info("will try to auto install pynfs tests at default path %s" %
                          self._default_testnfs_install_path)
            self.master_zip_file_path = self.download_pynfs_from_git(tempfile.gettempdir())
            self.install_pynfs(self.nfsutil_obj.machine_obj, self.master_zip_file_path)
            self.test_server_path = self._default_testnfs_install_path
        else:
            self.log.info("using test server installation path %s" % self.test_server_path)

        self.NFS_server_obj = NFSHelper(self.tcinputs['NFSServerHostName'],
                                        self.commcell,
                                        self.inputJSONnode['commcell']['commcellUsername'],
                                        self.inputJSONnode['commcell']['commcellPassword'],
                                        self.tcinputs.get('storagePolicy'))

        self.log.info("Creating Object Store : {0}".format(self.nfsutil_obj.Obj_store_name))
        share_path = self.NFS_server_obj.create_nfs_objectstore(
                                                    self.nfsutil_obj.Obj_store_name,
                                                    self.NFS_server_obj.storage_policy,
                                                    self.tcinputs['IndexServerMA'],
                                                    self.tcinputs['NFSServerHostName'],
                                                    self.tcinputs['ClientHostName'],
                                                    squashing_type="NO_ROOT_SQUASH",
                                                    delete_if_exists=True)

    def run(self):
        """Main function for test case execution"""
        try:
            self.run_pynfs_server_tests(self.tcinputs['NFSServerHostName'],
                                        self.nfsutil_obj.Obj_store_name,
                                        self.nfsutil_obj.machine_obj,
                                        self.test_server_path)

        except Exception as excp:
            log_error = "Detailed Exception : {0}".format(sys.exc_info())
            self.log.error(log_error)
            self.server.fail(excp, "test case failed in run function")

    def tear_down(self):
        """Tear down function"""
        # delete zip file if not none
        self.NFS_server_obj.delete_nfs_objectstore(self.nfsutil_obj.Obj_store_name,
                                                   delete_user=True)
