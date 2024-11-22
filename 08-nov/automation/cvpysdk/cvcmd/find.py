"""

Main File for performing Find operation at subclient Level

"""
import os
import logger
from collections import OrderedDict


class Find(object):
	"""Class for Find operation
	Methods :
	find = Performs search based on filename provided
	"""

	def __init__(self, loggingPath, commcell_object, client_name, agent_name, backupset_name):
		"""Initialize the browse  for the given path.

			Args:
				commcell_object - instance of commcell class
				client_name - Client Name
				agent_name - default is "File System" Agent
				backupset_name
			Returns:
				Instance of Find class


		"""
		self._commcell_object = commcell_object
		self._client_name = client_name
		self._agent_name = agent_name
		self._backupset_name = backupset_name
		self._LOG = logger.CVCLogger()
		self._LOG.initializelogger('cvc.log', loggingPath)
		self._LOG = self._LOG.log
		try:
			self._clientobj = self._commcell_object.clients.get(
				str(self._client_name))
			self._LOG.info("client object created successfully")
			self._agentobj = self._clientobj.agents.get(str(self._agent_name))
			self._LOG.info("agent object created successfully")
			if self._backupset_name is None:
				self._backupset_name = self._agentobj.backupsets.default_backup_set
			self._backupsetobj = self._agentobj.backupsets.get(self._backupset_name)
			self._LOG.info("backupset object created successfully")
		except Exception as backupset_obj_exception:
			self._LOG.error("Exception while creating backupset object: %s" % str(backupset_obj_exception))
			print("Exception while creating backupset object: %s" % str(backupset_obj_exception))

	def _subclient_object_creation(self, subclientname):
		"""
		Method to create subclient object
		Args :
		Find Class object
		Returns :
		Object of subclient
		"""
		try:
			flag = 1
			self._LOG.info("Client Name : %s"% (self._client_name))
			self._LOG.info("Agent Name  :%s "% (self._agent_name))
			self._LOG.info("BackupSet Name : %s"% (self._backupset_name))
			subclientobj = self._backupsetobj.subclients.get(
				str(subclientname))
			self._LOG.info("subclient object created successfully")
			flag = 0
		except Exception as subclient_exception:
			subclient_exception = str(subclient_exception)
			self._LOG.error(
				"Exception Raised in Subclient Object creation : %s"% (subclient_exception))
			flag = 1
		finally:
			return (flag, subclientobj)

	def _find_list_display(self, browse_list, browse_dict):
		"""
		Method to print the Find List of items
		"""
		try:
			self._LOG.info(browse_list)
			complete_browse_dict = {}
			for key1, value1 in browse_dict.items():
				parent_dir = os.path.abspath(os.path.join(key1, os.pardir))
				if parent_dir not in complete_browse_dict:
					complete_browse_dict[parent_dir] = {}
				complete_browse_dict[parent_dir].update({key1:value1})
			for key2, value2 in complete_browse_dict.items():
				print("\n" + key2 + ": \n")
				self._find_display(value2)
			print()

		except Exception as e:
			find_display_exception = str(e)
			self._LOG.error("Exception Raised in Find Display : %s"%
					  (find_display_exception))

	def _find_display(self, browse_dict):
		"""
		Method to print the details of files in the path
		"""
		dflag = 0
		self._LOG.info("Printing details of files")
		try:
			print ("{:<30} {:<8} {:<20} {:<8}".format('Name','Size','MTime','Type'))
			for key1, value1 in browse_dict.items():
				print ("{:<30} {:<8} {:<20} {:<8}".format(browse_dict[key1]['name'], browse_dict[key1]['size'], browse_dict[key1]['modified_time'], browse_dict[key1]['type']))
		except Exception as e:
			find_display_exception = str(e)
			self._LOG.error("Exception Raised in Find Display : %s"%
					  (find_display_exception))
			dflag = 1
		finally:
			return dflag


	def find(self, filename, subclientname=None, fromtime=0, totime=0):
		"""This method is responsible for initiating find operation based on filename
		Args :
			Find  Class Instance
			filename
			subclientname
			fromtime
			totime
		Returns :
			Prints Find Results
			Flag : Boolean that represents the completion of Find
		"""
		try:
			bflag = 1
			self._LOG.info("Find")
			self._LOG.info("filename :%s" % filename)
			self._LOG.info("Fromtime and Totime")
			self._LOG.info(fromtime)
			self._LOG.info(totime)
			if subclientname is None:
				bs = self._backupsetobj.backupset_name
				bs = str(bs)
				self._LOG.info("Proceeding with Find at backupsetlevel : %s" % bs)
				(find_list, find_dict) = self._backupsetobj.find(
					file_name=filename, from_time=fromtime, to_time=totime)
				self._find_list_display(find_list, find_dict)
				bflag = 0
			else:
				self._LOG.info("Verify if this subclient exists in given backupset")
				status = self._backupsetobj.subclients.has_subclient(
					subclientname)
				if status is True:
					subclientobj = self._backupsetobj.subclients.get(
						str(subclientname))
					self._LOG.info("subclient object created successfully")
					self._LOG.info("Path mentioned in command : %s"% (filename))
					(find_list, find_dict) = subclientobj.find(
						file_name=filename, from_time=fromtime, to_time=totime)
					self._find_list_display(find_list, find_dict)
					bflag = 0
				else:
					print("Given subclient does not exists in backupset :%s" %
						  self._backupsetobj.backupset_name)
					self._LOG.error(
						"Given subclient does not exists in backupset.So Enter proper subclient")
		except Exception as find_exception:
			self._LOG.error("Exception occurred in Find : %s"% (find_exception))
			bflag = 1
		finally:
			if bflag == 0:
				self._LOG.info("Find Completed successfully")
			else:
				self._LOG.error(" Find Encountered Error")
			return bflag
