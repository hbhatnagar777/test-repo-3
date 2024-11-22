# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root fors
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  Setup function for the test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
import socket
from Application.CloudApps.constants import AZUREBLOB_INSTANCE_TYPE
from Application.CloudApps.constants import AMAZONS3_INSTANCE_TYPE
from Application.CloudStorage.azure_helper import AzureHelper
from Application.CloudStorage.s3_helper import S3Helper
from Application.CloudStorage.cloud_storage_helper import CloudStorageHelper
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Amazon S3 backup and Restore test case"""

    def __init__(self):
        """TestCase constructor"""
        super(TestCase, self).__init__()
        self.name = "cloud storage Test Case-Acceptance test for all s3 cloud storage functions"
        self.controller_object = None
        self.azure_helper = None
        self.s3_helper = None
        self.cloud_storage_helper = None
        self.instance = None
        self.subclient = None
        self.session = None
        self.machine = None
        self.commserver_name = None
        self.fs_restore_path = None
        self.outofplace_instance_type = None
        self.outofplace_session = None
        self.result_string = None
        self.status = None
        self.tcinputs = {
            "access_node": None,
            "access_key_s3": None,
            "secret_key_s3": None,
            "region": None,
            "account_name_azure": None,
            "access_key_azure": None,
            "outofplace_client_name": None,
            "fs_client": None
        }

    def setup(self):
        """Initializes pre-requisites for this test case"""
        self.commserver_name = self.commcell.commserv_name
        self.log.info('CS set to "%s" in test case: "%s"', self.commserver_name,
                      self.id)
        self.machine = Machine(self.tcinputs['fs_client'], self.commcell)
        self.controller_object = Machine(socket.gethostname())
        self.azure_helper = AzureHelper(self)
        self.s3_helper = S3Helper(self)
        self.cloud_storage_helper = CloudStorageHelper(self)

    def run(self):
        """run method of this testcase"""
        try:
            self.log.info('Started executing "%s" Test Case on "%s"',
                          self.id, self.commserver_name)
            self.log.info(" STEP 0: Successfully got cloud apps agent object")
            access_key = self.instance.access_keyid
            secret_access_key = self.instance.secret_accesskey
            region = self.tcinputs['region']
            self.session = self.s3_helper.create_session_s3(
                access_key, secret_access_key, region)
            # run full backup on this content
            self.log.info("Starting Full backup")
            self.cloud_storage_helper.cloud_apps_backup(self.subclient, "Full")
            # downloading the subclient contents to local
            self.s3_helper.download_contents_s3(self.session, self.subclient.content,
                                                'originalcontents', False)
            self.log.info("successfully downloaded the files")
            self.s3_helper.delete_contents_s3(self.session, self.subclient.content)
            self.log.info("successfully deleted contents from cloud")
            self.log.info("Running an in place restore")
            self.cloud_storage_helper.cloud_apps_restore(self.subclient, "in_place")
            # downloading restored files to local machine for file comparison
            self.s3_helper.download_contents_s3(self.session, self.subclient.content,
                                                'inplacecontents', False)
            # in place restore validation
            self.log.info("Validating in place restore")
            self.cloud_storage_helper.restore_validation(
                self.controller_object,
                'originalcontents',
                'inplacecontents',
                'in_place')
            # run out of place restore
            self.log.info("Running out of place restore")
            outofplace_client = self.commcell.clients.get(
                self.tcinputs['outofplace_client_name'])
            agent = outofplace_client.agents.get('cloud apps')
            outofplace_cloud_type = agent.instances.get(next(iter(
                agent.instances._get_instances()))).ca_instance_type
            storage_policy = self.subclient.storage_policy
            if outofplace_cloud_type == 6:
                cloud_options = {
                    'instance_name': 'testazure',
                    'access_node': self.tcinputs['access_node'],
                    'description': None,
                    'storage_policy': storage_policy,
                    'accountname': self.tcinputs['account_name_azure'],
                    'accesskey': self.tcinputs['access_key_azure'],
                    'number_of_streams': 1,
                    'cloudapps_type': 'azure'
                }
            elif outofplace_cloud_type == 5:
                cloud_options = {
                    'instance_name': 'tests3',
                    'access_node': self.tcinputs['access_node'],
                    'description': None,
                    'storage_policy': storage_policy,
                    'accesskey': self.tcinputs['access_key_s3'],
                    'secretkey': self.tcinputs['secret_key_s3'],
                    'number_of_streams': 1,
                    'cloudapps_type': 's3'
                }
            outofplace_instance = agent.instances.add_cloud_storage_instance(cloud_options)
            self.cloud_storage_helper.cloud_apps_restore(
                self.subclient,
                "out_of_place",
                self.tcinputs['outofplace_client_name'],
                f"/{'outofplacecontents'}/",
                outofplace_instance.instance_name)
            self.outofplace_instance_type = outofplace_instance.ca_instance_type
            # downloading restored files to local machine for file comparison
            if self.outofplace_instance_type == AZUREBLOB_INSTANCE_TYPE:
                account_name = outofplace_instance.account_name
                account_key = outofplace_instance.access_key
                self.outofplace_session = self.azure_helper.create_session_azure(
                    account_name, account_key)
                self.azure_helper.download_contents_azure(
                    self.outofplace_session,
                    f"/{'outofplacecontents'}/",
                    'outofplacecontents',
                    True)
            elif self.outofplace_instance_type == AMAZONS3_INSTANCE_TYPE:
                access_key = outofplace_instance.access_keyid
                secret_access_key = outofplace_instance.secret_accesskey
                region = self.tcinputs['region']
                self.outofplace_session = self.s3_helper.create_session_s3(
                    access_key,
                    secret_access_key,
                    region)
                self.s3_helper.download_contents_s3(
                    self.outofplace_session,
                    f"/{'outofplacecontents'}/",
                    'outofplacecontents',
                    True)
            else:
                self.log.info(
                    "out of place cannot be possible for this instance type")
            # out of place restore validation
            self.log.info("Validating out of place restore")
            self.cloud_storage_helper.restore_validation(
                self.controller_object,
                'originalcontents',
                'outofplacecontents',
                'out_of_place')
            if self.machine.os_info == 'WINDOWS':
                self.fs_restore_path = 'C:\\fscontents'
            elif self.machine.os_info == 'UNIX':
                self.fs_restore_path = '/opt/fscontents'
            # run restore to fs
            self.log.info("Running fs restore")
            self.cloud_storage_helper.cloud_apps_restore(
                self.subclient,
                "fs_restore",
                self.tcinputs['fs_client'],
                self.fs_restore_path)
            # fs restore validation
            self.log.info("Validating fs restore")
            self.cloud_storage_helper.restore_validation(
                self.machine,
                'originalcontents',
                self.fs_restore_path,
                "fs_restore")
            # add more objects to this container and run incremental backup
            self.log.info(
                "adding more objects to subclient content to run incremental backups")
            self.s3_helper.create_container_s3(self.session, 'containerautomation')
            self.s3_helper.upload_file_s3(self.session, 'CVAutomation.py',
                                          'containerautomation',
                                          'CVAutomation.py')
            new_content = self.subclient.content
            new_content.append(
                f"/{'containerautomation'}/{'CVAutomation.py'}")
            self.subclient.content = new_content
            # run incremental backup
            self.log.info("Starting an incremental backup")
            self.cloud_storage_helper.cloud_apps_backup(self.subclient, "Incremental")
            # run synthetic full backup
            self.log.info("Starting a synthetic full backup")
            self.cloud_storage_helper.cloud_apps_backup(self.subclient, 'Synthetic_full')
            self.result_string = "Run of test case 50271 has completed successfully"
            self.status = constants.PASSED
        except Exception as exp:
            self.log.error('Failed with error: "%s"', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """tear down method of this testcase"""
        self.cloud_storage_helper.cleanup(
            self.machine,
            'originalcontents',
            'inplacecontents',
            'outofplacecontents',
            self.fs_restore_path)
        client = self.commcell.clients.get(self.tcinputs['outofplace_client_name'])
        agent = client.agents.get('cloud apps')
        self.log.info("Deleting the created container and instance")
        if self.outofplace_instance_type == AMAZONS3_INSTANCE_TYPE:
            self.s3_helper.delete_container_s3(self.outofplace_session,
                                               'outofplacecontents')
            agent.instances.delete('tests3')
        elif self.outofplace_instance_type == AZUREBLOB_INSTANCE_TYPE:
            self.azure_helper.delete_container_azure(self.outofplace_session,
                                                     'outofplacecontents')
            agent.instances.delete('testazure')
        new_content = self.subclient.content
        new_content.remove(
            f"/{'containerautomation'}/{'CVAutomation.py'}")
        self.subclient.content = new_content
        self.s3_helper.delete_container_s3(
            self.session,
            'containerautomation')
        self.log.info("container deleted successfully")
