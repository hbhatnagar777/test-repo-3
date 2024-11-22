# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
	__init__()      --  initialize TestCase class

	run()           --  run function of this test case
"""

import random
import string

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from NAS.NASUtils.nashelper import NASHelper
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.database_helper import get_csdb


class TestCase(CVTestCase):
	"""Class for running and validating Aux copy from NAS-NAS and NAS-MA """

	def __init__(self):
		""""Initializes TestCase object"""
		super(TestCase, self).__init__()
		self.name = "NetApp - V2 - Windows MA-Aux copy from NAS-NAS and NAS-MA and Restores"
		self.product = self.products_list.NDMP
		self.feature = self.features_list.DATAPROTECTION
		self.show_to_user = True
		self.tcinputs = {
			"CIFSShareUser": None,
			"CIFSSharePassword": None,
			"FilerRestoreLocation": None,
			"Auxcopyname_NAS": None,
			"AuxCopyLibrary": None,
			"AuxCopyMediaAgent": None
		}

	def _run_backup(self, backup_type):
		"""Starts backup job"""
		self.log.info("*" * 10 + " Starting Subclient {0} Backup ".format(backup_type) + "*" * 10)
		job = self._subclient.backup(backup_type)
		self.log.info(f"Started {backup_type} backup with Job ID: {job.job_id}")
		if not job.wait_for_completion():
			raise Exception(
				f"Failed to run {backup_type} backup job with error: {job.delay_reason}")
		return job

	def _get_copy_precedence(self, storage_policy, storage_policy_copy):
		"""Returns the copy precedence value"""
		self.csdb.execute(
			"select copy from archGroupCopy where archGroupId in (select id from archGroup where \
			name = '{0}') and name = '{1}'".format(storage_policy, storage_policy_copy))
		cur = self.csdb.fetch_one_row()
		return cur[0]

	def run(self):
		"""Main function for test case execution"""

		try:
			self.log.info(
				f"Will run below test case on: {self.tcinputs['SubclientName']} subclient")
			self.log.info(f"Number of data readers: {self.subclient.data_readers} ")
			if self.subclient.data_readers != 3:
				self.log.info("Setting the data readers count to 3")
				self.subclient.data_readers = 3
			self.nas_helper = NASHelper()
			self.log.info("Get NAS Client object")
			nas_client = self.nas_helper.get_nas_client(self._client, self._agent)

			self.log.info("Make a CIFS Share connection")
			nas_client.connect_to_cifs_share(
				str(self.tcinputs['CIFSShareUser']), str(self.tcinputs['CIFSSharePassword'])
			)

			self._run_backup("FULL")
			for content in self._subclient.content:
				volume_path, _ = nas_client.get_path_from_content(content)
				self.nas_helper.copy_test_data(nas_client, volume_path)

			self._run_backup("INCREMENTAL")
			for content in self._subclient.content:
				volume_path, _ = nas_client.get_path_from_content(content)
				self.nas_helper.copy_test_data(nas_client, volume_path)

			job = self._run_backup("DIFFERENTIAL")

			storage_policy = self.commcell.storage_policies.get(self._subclient.storage_policy)
			storage_policy_copy = storage_policy.get_copy(self.tcinputs["Auxcopyname_NAS"])
			self.log.info("*" * 10 + " Run Aux Copy to NAS attached tape " + "*" * 10)
			job = storage_policy.run_aux_copy(storage_policy_copy.copy_name)
			self.log.info(f"Started Aux Copy job with Job ID: {job.job_id}")

			if not job.wait_for_completion():
				raise Exception(f"Failed to run aux copy job with error: {job.delay_reason}")

			self.log.info("Successfully finished Aux Copy Job")

			options_selector = OptionsSelector(self._commcell)

			size = nas_client.get_content_size(self._subclient.content)
			copy_precedence = self._get_copy_precedence(
				self._subclient.storage_policy, storage_policy_copy.copy_name
			)
			windows_restore_client, windows_restore_location = \
				options_selector.get_windows_restore_client(size=size)

			self.log.info("*" * 10 + " Run out of place restore to Windows Client from Aux copy" + "*" * 10)

			job = self._subclient.restore_out_of_place(
				windows_restore_client.machine_name, windows_restore_location, self._subclient.content,
				copy_precedence=int(copy_precedence)
			)
			self.log.info(
				f"Started Restore out of place to Windows client job with Job ID: {job.job_id}")

			if not job.wait_for_completion():
				raise Exception(
					f"Failed to run restore out of place job with error: {job.delay_reason}")

			self.log.info("Successfully finished Restore out of place to windows client from Aux copy")

			self.nas_helper.validate_windows_restored_content(
				nas_client, windows_restore_client, windows_restore_location, self._subclient.content
			)

			self.log.info("*" * 10 + " Run out of place restore to Linux Client from Aux copy" + "*" * 10)

			linux_restore_client, linux_restore_location = \
				options_selector.get_linux_restore_client(size=size)

			job = self._subclient.restore_out_of_place(
				linux_restore_client.machine_name, linux_restore_location, self._subclient.content,
				copy_precedence=int(copy_precedence)
			)
			self.log.info(
				f"Started restore out of place to linux client job with Job ID: {job.job_id}")

			if not job.wait_for_completion():
				raise Exception(
					f"Failed to run restore out of place job with error:{job.delay_reason} ")

			self.log.info("Successfully finished Restore out of place to linux client")

			out = []
			out = windows_restore_client.compare_folders(
				linux_restore_client, windows_restore_location,
				linux_restore_location, ignore_files=self.nas_helper.ignore_files_list)
			if out:
				self.log.error(
					"Restore validation failed. List of different files \n%s", str(out)
				)
				raise Exception(
					"Restore validation failed. Please check logs for more details."
				)

			self.log.info("Successfully validated restored content")
			self.log.info("*" * 10 + " Run out of place restore to Filer from Aux copy " + "*" * 10)
			filer_restore_location = str(self.tcinputs['FilerRestoreLocation'])

			job = self._subclient.restore_out_of_place(
				self._client.client_name,
				filer_restore_location,
				self._subclient.content,
				copy_precedence=int(copy_precedence))

			self.log.info(
				f"Started Restore out of place to filer job with Job ID: {job.job_id}")

			if not job.wait_for_completion():
				raise Exception(
					f"Failed to run restore out of place job with error: {job.delay_reason}")

			self.log.info("Successfully finished Restore out of place to Filer")

			self.nas_helper.validate_filer_restored_content(
				nas_client, windows_restore_client, windows_restore_location,
				self.subclient.content, filer_restore_location
			)
			# create a random string
			random_string = "".join([random.choice(string.ascii_letters) for _ in range(4)])

			storage_policy = self.commcell.storage_policies.get(self.subclient.storage_policy)
			storage_policy_copy = "SPCopy_" + random_string

			self.log.info(
				f"Creating Storage Policy Copy {storage_policy_copy}")
			storage_policy.create_secondary_copy(
				storage_policy_copy, str(self.tcinputs['AuxCopyLibrary']),
				str(self.tcinputs['AuxCopyMediaAgent'])
			)
			self.log.info("Successfully created secondary copy")

			self.log.info("*" * 10 + " Run Aux Copy job to MA library " + "*" * 10)
			job = storage_policy.run_aux_copy(
				storage_policy_copy, str(self.tcinputs['AuxCopyMediaAgent'])
			)
			self.log.info(f"Started Aux Copy job with Job ID:{job.job_id}")

			if not job.wait_for_completion():
				raise Exception(f"Failed to run aux copy job with error:{job.delay_reason}")

			self.log.info("Successfully finished Aux Copy Job")
			copy_precedence = self._get_copy_precedence(
				self._subclient.storage_policy, storage_policy_copy
			)
			windows_restore_client, windows_restore_location = \
				options_selector.get_windows_restore_client(size=size)

			self.log.info("*" * 10 + " Run out of place restore to Windows Client from Aux copy" + "*" * 10)

			job = self._subclient.restore_out_of_place(
				windows_restore_client.machine_name, windows_restore_location, self._subclient.content,
				copy_precedence=int(copy_precedence)
			)
			self.log.info(
				f"Started Restore out of place to Windows client job with Job ID:{job.job_id}")

			if not job.wait_for_completion():
				raise Exception(
					f"Failed to run restore out of place job with error:{job.delay_reason}")

			self.log.info("Successfully finished Restore out of place to windows client from Aux copy")

			self.nas_helper.validate_windows_restored_content(
				nas_client, windows_restore_client, windows_restore_location, self._subclient.content
			)

			self.log.info("*" * 10 + " Run out of place restore to Linux Client from Aux copy" + "*" * 10)

			linux_restore_client, linux_restore_location = \
				options_selector.get_linux_restore_client(size=size)

			job = self._subclient.restore_out_of_place(
				linux_restore_client.machine_name, linux_restore_location, self._subclient.content,
				copy_precedence=int(copy_precedence)
			)
			self.log.info(
				"Started restore out of place to linux client job with Job ID: " + str(job.job_id)
			)

			if not job.wait_for_completion():
				raise Exception(
					f"Failed to run restore out of place job with error:{job.delay_reason} ")

			self.log.info("Successfully finished Restore out of place to linux client")

			out = []
			out = windows_restore_client.compare_folders(
				linux_restore_client, windows_restore_location,
				linux_restore_location, ignore_files=self.nas_helper.ignore_files_list)
			if out:
				self.log.error(
					"Restore validation failed. List of different files \n%s", str(out)
				)
				raise Exception(
					"Restore validation failed. Please check logs for more details."
				)

			self.log.info("Successfully validated restored content")
			self.log.info("*" * 10 + " Run out of place restore to Filer from Aux copy " + "*" * 10)
			filer_restore_location = str(self.tcinputs['FilerRestoreLocation'])

			job = self._subclient.restore_out_of_place(
				self._client.client_name,
				filer_restore_location,
				self._subclient.content,
				copy_precedence=int(copy_precedence))

			self.log.info(
				f"Started Restore out of place to filer job with Job ID: {job.job_id}")

			if not job.wait_for_completion():
				raise Exception(
					f"Failed to run restore out of place job with error: {job.delay_reason}")

			self.log.info("Successfully finished Restore out of place to Filer")

			self.nas_helper.validate_filer_restored_content(
				nas_client, windows_restore_client, windows_restore_location,
				self.subclient.content, filer_restore_location
			)

		except Exception as exp:
			self.log.error(f'Failed with error:{exp}')
			self.result_string = str(exp)
			self.status = constants.FAILED
