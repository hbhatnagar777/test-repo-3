"""Main file for performing backup Operation """

import os
import logger
import xml.etree.cElementTree as etree
from xml.dom import minidom
from cvpysdk.commcell import Commcell


class Backup(object):

	"""
	Class for backup operation
	Methods :
	backup() : Initiate backup on specific subclient
	ondemand_backup() : Takes Storage Policy name and content to initiate ondemand backup

	"""

	def __init__(self, loggingPath, commcell_object, backup_type, client_name, agent_name,
				 backupset_name, subclient_name, subclient_id=None):
		"""
		Initialize the backup  for the given subclient
		Args:
				subclient_name - subclient_name
				commcell_object - instance of commcell class
				type - Backup type
				client_name - Client Name
				agent_name - default is "File System" Agent
				backupset_name
				subclient_name
		Returns:
				object - instance of the backup class
		"""
		self._commcell_object = commcell_object
		self._type = backup_type
		self._client_name = client_name
		self._agent_name = agent_name
		self._backupset_name = backupset_name
		self._subclient_name = subclient_name
		self._subclient_id = subclient_id
		self._LOG = logger.CVCLogger()
		self._LOG.initializelogger('cvc.log', loggingPath)
		self._LOG = self._LOG.log


	def _subclient_object_creation(self, operation):
		"""
		Method to create subclient  object with given arguments

		Args:
		Backup Class object
		operation : To define Traditional or Ondemand Backup

		Returns :
		Object of subclient
		"""
		try:
			flag = 1
			self._LOG.info(operation)
			self._LOG.info("Client Name : %s"% (self._client_name))
			clientobj = self._commcell_object.clients.get(
				str(self._client_name))
			self._LOG.info("client object created successfully")
			self._LOG.info("Agent Name  : %s "% (self._agent_name))
			agentobj = clientobj.agents.get(str(self._agent_name))
			self._LOG.info("agent object created successfully")
			if self._subclient_id is not None:
				scflag = 0
				bkdict = agentobj.backupsets._backupsets
				for bk in bkdict:
					bkobj = agentobj.backupsets.get(bk)
					scdict = bkobj.subclients._subclients
					for sc in scdict:
						if scdict[sc]['id'] == self._subclient_id:
							scflag = 1
							self._subclient_name = sc
							self._backupset_name = bk
							break
				if scflag == 0:
					self._LOG.error("Operation failed. Subclient ID does not exist")
					raise Exception("Invalid Subclient ID")
			if self._backupset_name is None:
				self._backupset_name = agentobj.backupsets.default_backup_set
			backupsetobj = agentobj.backupsets.get(str(self._backupset_name))
			self._LOG.info("BackupSet Name : %s"% (self._backupset_name))
			self._LOG.info("backupset object created successfully")
			if self._subclient_name is None:
				self._subclient_name = backupsetobj.subclients.default_subclient
			subclientobj = backupsetobj.subclients.get(
				str(self._subclient_name))                        
			if self._subclient_id is not None:
				self._LOG.info("Subclient ID : %s"% (self._subclient_id))
			self._LOG.info("Subclient Name : %s"% (self._subclient_name))
			self._LOG.info("subclient object created successfully")
			self._LOG.info("Backup level : " + str(self._type))
			flag = 0
		except Exception as subclient_exception:
			subclient_exception = str(subclient_exception)
			self._LOG.error("Exception Raised in Subclient object : %s"%
					  (subclient_exception))
			flag = 1
		finally:
			return (flag, subclientobj)

	def backup(self, outputFilePath=None):
		"""This method is responsible for initiating simple backup job on given subclient
		Args:
			Backup Class Instance
			Output File Path
		Returns :
			Prints Backup Job Details
			Flag : Boolean that represents the Initiation of backup
		"""
		# create XML
		root = etree.Element('Task')
		child = etree.Element('JobID')
		try:
			bflag = 1
			jobid = None
			operation = "Normal Backup"
			(status, subclientobj) = self._subclient_object_creation(operation)
			if status == 1:
				self._LOG.error("Issue in creating the subclient object during backup")
				bflag = 1
			else:
				try:
					jobobj = subclientobj.backup(self._type)
					bflag = 0
					jobid = jobobj.job_id
				except Exception as backup_job_initate_exception:
					self._LOG.error("Error in initiating Job  : %s"%
							 (backup_job_initate_exception))
					bflag = 1
		except Exception as backup_class_exception:
			backup_class_exception = str(backup_class_exception)
			self._LOG.error("Exception Raised in Backup Class : %s"%
					  (backup_class_exception))
		finally:
			if bflag == 0:
				child.text = jobid
				root.append(child)
				if outputFilePath is None:
					treeString = etree.tostring(root, 'utf-8')
					reparsed = minidom.parseString(treeString)
					print(reparsed.toprettyxml(indent="    "))

				else:
					treeString = etree.tostring(root, 'utf-8')
					reparsed = minidom.parseString(treeString)
					outputFile = open(outputFilePath, "w")
					outputFile.write(reparsed.toprettyxml(indent="    "))
					print("Refer to " + outputFilePath + " for details ")
					outputFile.close()

			else:
				self._LOG.error("Backup Job Initiation Encountered Error")
			return (bflag, jobid)

	def ondemand_backup(self, dpath, dsp):
		"""
		Method is responsible for ondemand backup of specified content
		Args :
			Backup Class Instance
			New Contents
			Storage Policy

		Returns :
			Prints Backup Job Details
			Flag : Boolean that represents the completion of backup
			"""
		try:
			jobid = None
			bflag = 1
			cflag = 1
			self._LOG.info("Ondemand Backup initiation : ")
			self._LOG.info("Client Name : %s"% (self._client_name))
			self._LOG.info("Agent Name  :%s "% (self._agent_name))
			self._LOG.info("BackupSet Name : %s"% (self._backupset_name))
			self._LOG.info("Subclient Name :%s"% (self._subclient_name))
			self._LOG.info("Going to add the list of files as new subclient content")
			self._LOG.info(dpath)
			self._LOG.info(
				"Lets check if any subclient already exist with the same name :")

			# creating instance of backupset object :
			clientobj = self._commcell_object.clients.get(
				str(self._client_name))
			self._LOG.info("client object created successfully")
			agentobj = clientobj.agents.get(str(self._agent_name))
			self._LOG.info("agent object created successfully")
			if self._backupset_name is None:
				self._backupset_name = agentobj.backupsets.default_backup_set
			backupsetobj = agentobj.backupsets.get(str(self._backupset_name))

			# Checking if subclient with given name exist in provided backupset
			try:
				check_subclient = backupsetobj.subclients.has_subclient(
					self._subclient_name)
				if check_subclient is True:
					self._LOG.info("Ondemand Subclient exist already")
					self._LOG.info(
						"We are going to add this content to existing subclient ondemand ")
					self._LOG.info(
						"Ondemand Subclient exist already .We are going to add this content to existing subclient ondemand ")
					subclientobj = backupsetobj.subclients.get('ondemand')
					subclientobj.content += dpath
					jobobj = subclientobj.backup(self._type)
					bflag = 0
					jobid = jobobj.job_id
				else:
					# If "Ondemand" subclient is not existing , it attempts to create new
					# subclient "ondemand" under user provided backup set
					self._LOG.info("Ondemand subclient is not existing.creating new subclient")
					self._LOG.info(
						"Ondemand subclient is not existing.creating new subclient")
					subclient_name = self._subclient_name.lower()
					backupset_name = self._backupset_name.lower()
					# com = 'Subclient class instance for Subclient: ' + '\"' + \
					#     subclient_name + '\"' + ' of Backupset: ' + '\"' + backupset_name + '\"'
					# com = str(com)
					try:
						subclient_creation_status = backupsetobj.subclients.add(
							self._subclient_name, dsp)
						cflag = 0
					except Exception as subclient_creation_exception:
						self._LOG.error("Error Occurred .Refer Logs for details ")
						subclient_creation_exception = str(
							subclient_creation_exception)
						self._LOG.error(
							"Exception occurred during subclient creation")
						self._LOG.error(subclient_creation_exception)
					if cflag == 0:
						self._LOG.info(
							"Ondemand subclient created successfully")
						backupsetobj = agentobj.backupsets.get(
							str(self._backupset_name))
						subclientobj = backupsetobj.subclients.get(
							str(self._subclient_name))
						try:
							subclientobj.content = dpath
						except Exception as subclient_content_add_exception:
							self._LOG.error("Error in Subclient content Addition")
							self._LOG.error("Issue in adding content to subclient")
							self._LOG.error(subclient_content_add_exception)
						jobobj = subclientobj.backup(self._type)
						bflag = 0
						jobid = jobobj.job_id
					else:
						self._LOG.error("Error Occurred .Refer Logs for details ")
						self._LOG.error(
							"Issue in creating a new subclient : %s "% (subclient_creation_status))
						return (bflag, jobid)
			except Exception as subclient_create_exception:
				self._LOG.error("Error Occurred .Refer Logs for details ")
				subclient_create_exception = str(subclient_create_exception)
				self._LOG.error(
					"Exception in subclient property check  : %s"% (subclient_create_exception))
				return (bflag, jobid)
		except Exception as ondemand_backup_exception:
			ondemand_backup_exception = str(ondemand_backup_exception)
			self._LOG.error("Exception during on demand backup : %s"%
					  (ondemand_backup_exception))

		finally:
			if bflag == 0:
				self._LOG.info("Ondemand Backup Job Initiated successfully. Job ID : " + str(jobid))
			else:
				self._LOG.error("Ondemand Backup Job Initiation  Encountered Error")
			return (bflag, jobid)

	def adHocBackup(self, adHocOptions, outputFilePath=None):
		"""
		Method is responsible for ad hoc backup of specified content
		Args :
			Backup Class Instance
			Output File Path

		Returns :
			Prints Backup Job Details
			Flag : Boolean that represents the completion of backup
			"""        

		# create XML
		root = etree.Element('Task')
		child = etree.Element('JobID')
		try:
			bflag = 1
			jobid = None
			operation = "Ad Hoc Backup"
			(status, subclientobj) = self._subclient_object_creation(operation)

			if status == 1:
				self._LOG.error("Issue in creating the subclient object during backup")
				bflag = 1
			else:
				try:
					jobobj = subclientobj.backup(backup_level='Incremental', advanced_options=adHocOptions)
					bflag = 0
					jobid = jobobj.job_id
				except Exception as adhoc_backup_job_initate_exception:
					self._LOG.error("Error in initiating Job  : %s"%
							 (adhoc_backup_job_initate_exception))
					bflag = 1
		except Exception as backup_class_exception:
			backup_class_exception = str(backup_class_exception)
			self._LOG.error("Exception Raised in Backup Class : %s"%
					  (backup_class_exception))
		finally:
			if bflag == 0:
				child.text = jobid
				root.append(child)
				if outputFilePath is None:
					treeString = etree.tostring(root, 'utf-8')
					reparsed = minidom.parseString(treeString)
					print(reparsed.toprettyxml(indent="    "))

				else:
					treeString = etree.tostring(root, 'utf-8')
					reparsed = minidom.parseString(treeString)
					outputFile = open(outputFilePath, "w")
					outputFile.write(reparsed.toprettyxml(indent="    "))
					print("Refer to " + outputFilePath + " for details ")
					outputFile.close()

			else:
				self._LOG.error("Backup Job Initiation Encountered Error")
			return (bflag, jobid)