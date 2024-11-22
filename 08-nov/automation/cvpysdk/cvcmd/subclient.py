
"""Main file for performing Subclient configuration  Operation """

import os
import logger
from cvpysdk import subclient


class SubClient(object):
	"""Class for for performing changes to subclient configurationn
	Methods :
	subclient_add : Method to create new subclient
	subclient_delete : Method to delete given subclient
	subclient_add_content : Method to add contents to existing subclient
	subclient_delete_content : Method to delete the contents of existing subclient

	"""

	def __init__(self, loggingPath, commcell_object, client_name, agent_name,
				 backupset_name):
		"""Initialize the subclient class variable
			Args:
				commcell_object - instance of commcell class
				client_name - Client Name
				agent_name - default is "File System" Agent
				backupset_name
			Returns:
				object - instance of the subc class
		"""
		self._commcell_object = commcell_object
		self._client_name = client_name
		self._agent_name = agent_name
		self._backupset_name = backupset_name
		self._LOG = logger.CVCLogger()
		self._LOG.initializelogger('cvc.log', loggingPath)
		self._LOG = self._LOG.log

	def _check_backupset(self):
		"""
		Method to check if backupset exists in given client
		Returns status : True or false
		"""
		status = False
		backupsetobj = None
		try:
			#LOG.info("Check backupset existence Module")
			clientobj = self._commcell_object.clients.get(
				str(self._client_name))
			self._LOG.info("client object created successfully")
			agentobj = clientobj.agents.get(str(self._agent_name))
			self._LOG.info("agent object created successfully")
			if self._backupset_name is None:                    
					self._backupset_name = agentobj.backupsets.default_backup_set
			self._LOG.info("BackupSet Name : %s"% (self._backupset_name))
			status = agentobj.backupsets.has_backupset(self._backupset_name)
			if status is True:                
				backupsetobj = agentobj.backupsets.get(str(self._backupset_name))            
		except Exception as e:
			self._LOG.error("Exception in Check backupset:%s" % str(e))
		finally:
			return (status, backupsetobj)

	def subclient_add(self, subclient_name, storage_policy, subclient_content, subclient_filters=None):
		"""
			Method is responsible for creating new subclient with given content
			Args :
			subclient_name (str) - name of the new subclient to add
			storage_policy  (str)   --  name of the storage policy to associate with subclient
			subclient_content (list) --List of paths to be added as subclient content
			Returns :
			Flag : Boolean that represents the completion of subclient_add

		"""
		try:
			bflag = 1
			cflag = 1
			self._LOG.info("Subclient Addition: ")
			self._LOG.info("Client Name : %s"% (self._client_name))
			self._LOG.info("Agent Name  :%s "% (self._agent_name))
			#self._LOG.info("BackupSet Name : %s"% (self._backupset_name))
			self._LOG.info("Subclient Name :%s"% (subclient_name))
			self._LOG.info("Going to add the list of files as new subclient content")
			self._LOG.info(subclient_content)
			self._LOG.info(
				"Lets check if any subclient already exist with the same name :")
			# Check if given backupset exists in that client
			(status, backupsetobj) = self._check_backupset()
			if status is True:
				self._LOG.info("Given backupset exists in Client")
				try:
					check_subclient = backupsetobj.subclients.has_subclient(
						subclient_name)
					if check_subclient is True:
						self._LOG.error("Subclient with same name  exist in this backupset. Try with different subclient name")
						bflag = 2
					else:
						self._LOG.info(
							"Subclient is not existing . So Lets create new subclient:")
						backupset_name = self._backupset_name.lower()
						try:
							create_status = backupsetobj.subclients.add(
								subclient_name, storage_policy)
							cflag = 0
						except Exception as sub_exception:
							sub_exception = str(sub_exception)
							self._LOG.error("Exception occurred during subclient creation :%s"% (sub_exception))
						if cflag == 0:                            
							'''clientobj = self._commcell_object.clients.get(
								str(self._client_name))
							agentobj = clientobj.agents.get(
								str(self._agent_name))
							backupsetobj = agentobj.backupsets.get(
								str(self._backupset_name))'''
							subclientobj = backupsetobj.subclients.get(
								str(subclient_name))
							self._LOG.info("Subclient created successfully")
							try:
								self._LOG.info("Subclient Content Addition")
								subclientobj.content = subclient_content
								if subclient_filters is not None:
									self._LOG.info("Subclient Filter Addition")
									subclientobj.filter_content = subclient_filters
								self._LOG.info(
									"Subclient properties set with given contents")
								bflag = 0
							except Exception as sub_content_exception:
								self._LOG.error("Issue in adding content to new subclient :%s"% (sub_content_exception))
						else:
							self._LOG.error(
								"Issue in creating a new subclient : %s "% (create_status))
				except Exception as sub_property_check:
					sub_property_check = str(sub_property_check)
					self._LOG.error("Exception in subclient property check  : %s"% sub_property_check)
			else:
				self._LOG.error("Given backupset does not exists in given client")
		except Exception as subclient_create_exc:
			subclient_create_exc = str(subclient_create_exc)
			self._LOG.error("Exception in subclient creation : %s"%
					  subclient_create_exc)
		finally:
			if bflag == 0:
				self._LOG.info("Subclient creation succeeded with given contents")
			elif bflag == 2:
				self._LOG.error(
					"Subclient with same already exist . try with different name")
			else:
				self._LOG.error("Subclient Creation Failed")
		return bflag

	def subclient_delete(self, subclient_name):
		"""
		Method is responsible for deleting given subclient
			Args :
			subclient_name (str) - name of the  subclient to be deleted
			Returns :
			Flag : Boolean that represents the completion of subclient_delete
		"""
		try:
			bflag = 1
			self._LOG.info("Subclient Deletion: ")
			self._LOG.info("Client Name : %s"% (self._client_name))
			self._LOG.info("Agent Name  :%s "%(self._agent_name))
			#self._LOG.info("BackupSet Name : %s"% (self._backupset_name))
			self._LOG.info("Subclient Name :%s"% (subclient_name))
			self._LOG.info("Lets check if any subclient exist with given name :")
			(status, backupsetobj) = self._check_backupset()
			if status is True:
				self._LOG.info("Given backupset exists in Client")
				try:
					check_subclient = backupsetobj.subclients.has_subclient(
						subclient_name)
					if check_subclient is True:
						try:
							self._LOG.info("Subclient with same name  exist in this backupset.Lets delete this subclient")
							backupset_name = self._backupset_name.lower()
							flag = backupsetobj.subclients.delete(
								subclient_name)
							if flag is None:
								bflag = 0
						except Exception as subclient_delete_exp:
							subclient_delete_exp = str(subclient_delete_exp)
							self._LOG.error("Exception occurred during subclient deletion :%s"% subclient_delete_exp)
							bflag = 1
					else:
						# print "Subclient is not existing . So Lets create new subclient :"
						self._LOG.error(
							"Subclient is not existing with given name under given backupset")
						bflag = 2
				except Exception as sub_client_del_exp:
					sub_client_del_exp = str(sub_client_del_exp)
					self._LOG.error("Exception occurred during subclient deletion while subclient property check  :%s"% sub_client_del_exp)
					bflag = 1
			else:
				self._LOG.error("Given backupset does not exists in given client")
		except Exception as sub_client_del_exp:
			sub_client_del_exp = str(sub_client_del_exp)
			self._LOG.error("Exception occurred during subclient deletion :%s"%(sub_client_del_exp))
			bflag = 1
		finally:
			if bflag == 0:
				self._LOG.info("Subclient Deletion succeeded ")
			else:
				self._LOG.error("Subclient Deletion failed")
			return bflag


	def subclient_update(self, subclient_name, subclient_content=None, subclient_filters=None, overwrite='False'):
		"""
			Method is responsible for updating subclient
			Args :
			subclient_name (str) - name of the subclient
			subclient_content (list) --List of paths to be added as subclient content
			subclient_filters(list) -- List of paths to be added as subclient filters
			overwrite(str : True | False ) -- Overwrite existing content and filters  \
			or append to existing content and filters
			Returns :
			Flag : Boolean that represents the completion of subclient_update

		"""
		try:
			bflag = 1
			self._LOG.info("Subclient Update Operation ")
			self._LOG.info("Client Name : %s"% (self._client_name))
			self._LOG.info("Agent Name  :%s "% (self._agent_name))
			#self._LOG.info("BackupSet Name : %s"% (self._backupset_name))
			self._LOG.info("Subclient Name :%s"% (subclient_name))
			self._LOG.info("Going to update subclient")
			self._LOG.info("Lets check if any backupset exists")
			# Check if given backupset exists in that client 
			(status,backupsetobj) = self._check_backupset()
			if status is True:
				self._LOG.info("Given backupset exists in Client")
				try:
					check_subclient = backupsetobj.subclients.has_subclient(
						subclient_name)
					if check_subclient is True:
						self._LOG.info("Subclient with same name  exist  in this backupset.Lets update the subclient based on overwrite option")
						subclientobj = backupsetobj.subclients.get(
							str(subclient_name))
						try:
							self._LOG.info("Subclient Update Operation")
							if overwrite == 'True':
								if subclient_content is not None:
									self._LOG.info("Updating content")
									subclientobj.content = subclient_content
								if subclient_filters is not None:
									self._LOG.info("Updating filters")
									subclientobj.filter_content = subclient_filters
							elif overwrite == 'False':
								if subclient_content is not None:
									self._LOG.info("Updating content")
									subclientobj.content += subclient_content
								if subclient_filters is not None:
									self._LOG.info("Updating filters")
									subclientobj.filter_content += subclient_filters
							self._LOG.info("Subclient properties set with given contents")
							bflag = 0
						except Exception as subclient_content_exception:
							self._LOG.error("Error in Subclient Update Operation :%s"% (subclient_content_exception))
							bflag = 1
					else:
						self._LOG.error(
							"Subclient is not existing with given name under given backupset  :")
						bflag = 1
				except Exception as property_check_exception:
					property_check_exception = str(property_check_exception)
					self._LOG.error("Exception in subclient property check  : %s"%
							  (property_check_exception))
					bflag = 1
			else:
				self._LOG.error("Given backupset does not exist in given client")
				
		except Exception as subclient_content_add_exception:
			subclient_content_add_exception = str(subclient_content_add_exception)
			self._LOG.error("Exception in subclient creation : %s"%
					  (subclient_content_add_exception))
			bflag = 1
		finally:
			if bflag == 0:
				self._LOG.info("Subclient Update Operation Succeeded ")
			else:
				self._LOG.error("Subclient Update Operation Failed")
		return bflag
