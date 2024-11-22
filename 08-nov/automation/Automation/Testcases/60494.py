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
    __init__()                          --  initialize TestCase class

    setup()                             --  setup function of this test case

    run()                               --  run function of this test case

    tear_down()                         --  tear down function of this test case

    validate_create_classifier()        --  validates the classifier creation

    validate_classifier_samples()       --  Validates the sample docs details for trained classifier

    validate_modify_classifier()        --  Validates enable/disable on classifier

    vaidate_training()                  --  Validates training on classifier

    validate_delete_classifier()        --  Validates classifier delete

"""

import time
import zipfile
from cvpysdk.activateapps.entity_manager import EntityManagerTypes
from cvpysdk.activateapps.constants import TrainingStatus

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase


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
        self.name = "Integration Test case for Classifier in Cvpysdk"
        self.tcinputs = {
            "ContentAnalyserCloudName": None,
            "ModelDataZipFile": None,
            "BigModelDataZipFile": None
        }
        self.classifier_name = "IntegrationClassifierTesting"
        self.classifier_name_modified = "IntegrationClassifierTestingModified"
        self.classifier_obj = None
        self.classifiers = None
        self.test_start = int(time.time())

    def validate_delete_classifier(self):
        """Validates classifier delete"""

        self.classifiers.delete(classifier_name=self.classifier_name_modified)
        if self.classifiers.has_classifier(classifier_name=self.classifier_name_modified):
            raise Exception(f"Classifier exists even after deletion : {self.classifier_name_modified}")
        self.log.info("Delete classifier Validation : Passed")

    def vaidate_training(self):
        """Validates training on classifier"""
        self.log.info("Going to upload big zip file on this classifier")
        self.classifier_obj.upload_data(zip_file=self.tcinputs['BigModelDataZipFile'])
        self.log.info("Upload done. Going to start training")
        self.classifier_obj.start_training(wait_for=False)
        self.log.info("Training started. Wait for 30seconds and then cancel it")
        time.sleep(30)
        self.log.info("Going to cancel training")
        self.classifier_obj.cancel_training()
        self.log.info("Check the training status for cancellation")
        if not self.classifier_obj.training_status != TrainingStatus.CANCELLED.value:
            raise Exception(f"Cancel training failed with status : {self.classifier_obj.training_status}")
        self.log.info("Cancel Training Validation : Passed")

    def validate_modify_classifier(self):
        """Validates enable/disable on classifier"""
        self.log.info(f"Going to disable classifier : {self.classifier_name}")
        self.classifier_obj.modify(enabled=False)
        if self.classifier_obj.is_enabled:
            raise Exception("Classifier still shows as enabled")
        self.log.info("Disabled classifier Validation : Passed")
        self.log.info(f"Going to enable classifier : {self.classifier_name}")
        self.classifier_obj.modify(enabled=True)
        if not self.classifier_obj.is_enabled:
            raise Exception("Classifier still shows as disabled")
        self.log.info("Enable classifier Validation : Passed")
        self.log.info(f"Going to modify classifier with new name : {self.classifier_name_modified}")
        self.classifier_obj.modify(classifier_new_name=self.classifier_name_modified)
        if not self.classifiers.has_classifier(classifier_name=self.classifier_name_modified):
            raise Exception(f"Modified name is not shown in classifier : {self.classifier_name_modified}")
        self.log.info("Rename classifier Validation : Passed")

    def validate_classifier_samples(self):
        """validates the sample docs details for trained classifier"""
        if not self.classifier_obj.training_status != TrainingStatus.COMPLETED.value:
            raise Exception(f"Training status is not in completed state : {self.classifier_obj.training_status}")
        self.log.info("Training status validation : Passed")

        if not self.classifier_obj.last_training_time > self.test_start:
            raise Exception(
                f"Last model train timings are not updated properly : {self.classifier_obj.last_training_time}")
        self.log.info("Last Model Training Time validation : Passed")

        if not self.classifier_obj.training_accuracy >= 80:
            raise Exception(f"Classifier accuracy is not as expected as 80%")
        self.log.info("Training Accuracy validation : Passed")

        zip_obj = zipfile.ZipFile(self.tcinputs['ModelDataZipFile'], 'r')
        total_elements = len(zip_obj.namelist())
        zip_obj.close()

        if self.classifier_obj.sample_details['totalSamples'] < (total_elements / 2):
            raise Exception(
                f"Total sample details shows document count less than 2X zip file content of : {total_elements} files")
        self.log.info("Total Samples Validation : Passed")

        if not self.classifier_obj.sample_details['trainingSamplesUsed'] > 0 or \
                not self.classifier_obj.sample_details['validationSamplesUsed'] > 0:
            raise Exception(f"Sampling documents came as Zero")
        self.log.info("Trained Samples Validation : Passed")

    def validate_create_classifier(self):
        """Validates creation of classifier"""

        self.log.info(f"Creating Classifier : {self.classifier_name}")
        self.classifier_obj = self.classifiers.add(classifier_name=self.classifier_name,
                                                   content_analyzer=self.tcinputs['ContentAnalyserCloudName'],
                                                   training_zip_data_file=self.tcinputs['ModelDataZipFile'])
        if not self.classifiers.has_classifier(classifier_name=self.classifier_name):
            raise Exception("Classifier not created properly")
        self.log.info("Classifier got created & Trained")

    def setup(self):
        """Setup function of this test case"""
        self.classifiers = self.commcell.activate.entity_manager(EntityManagerTypes.CLASSIFIERS)
        if self.classifiers.has_classifier(self.classifier_name):
            self.log.info(f"Deleting the classifier from previous run - {self.classifier_name}")
            self.classifiers.delete(classifier_name=self.classifier_name)
        if self.classifiers.has_classifier(self.classifier_name_modified):
            self.log.info(f"Deleting the classifier from previous run - {self.classifier_name_modified}")
            self.classifiers.delete(classifier_name=self.classifier_name_modified)

    def run(self):
        """Run function of this test case"""
        try:
            self.validate_create_classifier()
            self.validate_classifier_samples()
            self.validate_modify_classifier()
            self.vaidate_training()
            self.validate_delete_classifier()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.log.exception(exp)
            self.status = constants.FAILED
