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
	 __init__()      --  initialize TestCase class

	 run()           --  run function of this test case

	 filters_validate -- Function to validate the filters
 """

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from FileSystem.FSUtils.fshelper import FSHelper


class TestCase(CVTestCase):
	"""TestCase for Basic acceptance Test of Client Group filters"""

	def __init__(self):
		"""Initializes test case class object"""
		super(TestCase, self).__init__()
		self.name = "Client Group Filters and Commcell test"
		self.global_win_filters = None
		self.global_unix_filters = None
		self.unix_machine = None
		self.win_machine = None
		self.global_filters_enabled = None
		self.commcell = None
		self.cleanup_run = None
		self.content_path = None
		self.helper = None
		self.server_group_name = None
		self.tcinputs = {
			"StoragePolicyName": None,
			"WindowsClient": None,
			"UnixClient": None
		}
		self.client_group_obj = None

	def filters_validate(self, client):
		"""Function to validate whether the filters were set correctly or not

		Args:
			client        (obj)  --  Client object.

		"""

		self.client = client
		self.agent = self.client.agents.get('File System')
		self.instance = self.agent.instances.get('DefaultInstanceName')
		self.machine = Machine(machine_name=self.client)
		self.helper = FSHelper(self)
		self.helper.populate_tc_inputs(self, mandatory=False)
		self.log.info("Creating test data")

		if self.machine.os_info == "WINDOWS":
			filter_extensions = str(self.windows_filters) + ",*.bcd" + "," + ",".join(self.global_win_filters)

		elif self.machine.os_info == "UNIX":
			filter_extensions = str(self.unix_filters) + ",*.tar" + "," + ",".join(self.global_unix_filters)

		if len(self.global_win_filters) == 0 or len(self.global_unix_filters) == 0:
			filter_extensions = filter_extensions[:-1]

		filter_extension = filter_extensions.replace('*', '')
		# print(filter_extension)
		
		install_dir = self.client.install_directory
		self.content_path = self.machine.join_path(install_dir, "Test_53908")
		self.helper.generate_testdata(filter_extension.split(','), self.content_path)
		self.log.info("COntent path: " + self.content_path)
		sub_content = self.content_path.split('*')
		backupset_name = "Test_53908"

		self.helper.create_backupset(backupset_name, delete=True)
		self.helper.create_subclient(name = "Filter", storage_policy = self.tcinputs['StoragePolicyName'], content = sub_content,
									 data_readers=4)
									 
		global_filter_prop = {"fsSubClientProp": {"useGlobalFilters": 1}}
			
		self.subclient.update_properties(global_filter_prop)
		win_filters1 = str(self.windows_filters).split(',')
		unix_filters1 = str(self.unix_filters).split(',')

		# print(self.subclient.subclient_id)
		
		if self.global_filters_enabled:

			win_filters1 = win_filters1 + self.global_win_filters
			unix_filters1 = unix_filters1 + self.global_unix_filters
		
		job = self.helper.run_backup(backup_level = "FULL", wait_to_complete=False)[0]
		while job.phase != "Backup":
			continue
		job.pause()
		
		if self.global_filters_enabled:
			self.helper.validate_filters(win_filters1, unix_filters1)
		else:
			self.helper.validate_filters(win_filters1, unix_filters1, self.global_win_filters, self.global_unix_filters)
		job.resume()

	def run(self):
		"""Creates a group with the specified clients and sets the filters"""
		global_win_filters = None
		global_unix_filters = None
		self.global_filters_enabled = True
		self.server_group_name = "Test_53908"

		#used for deleteing [''] for delete_all() in GlobalFilter
		empty_str_list = ['']
		try:

			if self.commcell.client_groups.has_clientgroup(self.server_group_name):
				self.log.info("Client group already exists, deleting it.")
				self.commcell.client_groups.delete(self.server_group_name)

			clients = self.tcinputs['WindowsClient'] + ',' + self.tcinputs['UnixClient']

			self.client_group_obj = self.commcell.client_groups.add(self.server_group_name, clients)
			self.log.info("Created client group : %s", self.server_group_name)
			self.unix_client = self.commcell.clients.get(self.tcinputs['UnixClient'])
			self.windows_client = self.commcell.clients.get(self.tcinputs['WindowsClient'])
			self.unix_machine = Machine(self.unix_client)
			self.win_machine = Machine(self.windows_client)

			if not self.unix_client.is_ready:
				self.log.error("Check readiness for the unix client failed")

			if not self.windows_client.is_ready:
				self.log.error("Check readiness for the windows client failed")

			self.windows_filters = "*.doc,*.txt"
			self.unix_filters = "*.dmg,*.pkg"

			cg_filters = {"windows_filters": str(self.windows_filters).split(','),
						  "unix_filters": str(self.unix_filters).split(',')
						  }
			self.client_group_obj.client_group_filter = cg_filters
			self.log.info("The  filters have been set")

			"""
			Adding code for global filters
			"""

			self.log.info("Adding global filters to commcell")

			#instance of Global Filters class
			global_filters = self.commcell.global_filters
			
			#instance of Global Filter class for Windows
			global_win_filters = global_filters.get("Windows")
		
			#instance of Global Filter class for Unix
			global_unix_filters = global_filters.get("Unix")
		
			#delete filters
			global_win_filters.delete_all()
			global_unix_filters.delete_all()
			
			# Using empty list to delete the filter set by delete_all() --> ['']
			global_win_filters._update("DELETE", empty_str_list)
			global_unix_filters._update("DELETE", empty_str_list)

			#refresh filters
			global_win_filters.refresh()
			global_unix_filters.refresh()

			#take inputs
			self.global_win_filters = self.tcinputs["GlobalWindowsFilters"].split(",")
			self.global_unix_filters = self.tcinputs["GlobalUnixFilters"].split(",")

			# print(self.global_win_filters)
			# print(self.global_unix_filters)

			#add filters
			global_win_filters.add(self.global_win_filters)
			global_unix_filters.add(self.global_unix_filters)

			#refresh
			global_win_filters.refresh()
			global_unix_filters.refresh()

			self.filters_validate(self.windows_client)
			self.filters_validate(self.unix_client)

			self.log.info("Removing the global filters and checking again")

			# delete filters
			global_win_filters.delete_all()
			global_unix_filters.delete_all()

			# Using empty list to delete the filter set by delete_all() --> ['']
			global_win_filters._update("DELETE", empty_str_list)
			global_unix_filters._update("DELETE", empty_str_list)

			# refresh filters
			global_win_filters.refresh()
			global_unix_filters.refresh()
			self.global_filters_enabled = False

			self.filters_validate(self.windows_client)
			self.filters_validate(self.unix_client)

		except Exception as excp:
			self.log.info(str(excp))
			self.log.error("TEST CASE FAILED")
			self.status = constants.FAILED
			self.result_string = str(excp)

		finally:
			if self.cleanup_run:
				
				self.commcell.client_groups.delete(self.server_group_name)

				global_win_filters.delete_all()
				global_unix_filters.delete_all()

				# Using empty list to delete the filter set by delete_all() --> ['']
				global_win_filters._update("DELETE", empty_str_list)
				global_unix_filters._update("DELETE", empty_str_list)
				global_win_filters.refresh()
				
				self.win_machine.remove_directory(self.content_path)
				self.unix_machine.remove_directory(self.content_path)
				global_unix_filters.refresh()