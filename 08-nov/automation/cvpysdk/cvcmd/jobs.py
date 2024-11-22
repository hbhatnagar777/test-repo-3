"""Main file for performing Operations on Job Objects """

import os
import logger
from cvpysdk import job
import xml.etree.cElementTree as etree
from xml.dom import minidom



class Jobs(object):

	"""
	Class for job related operation
	Methods :
	"""

	def __init__(self, loggingPath, commcell_object, jobid):
		"""
		Initialize the backup  for the given subclient
		Args:
				commcell_object - instance of commcell class
				type - Backup type
				jobid
		Returns:
				object - instance of the job  class
		"""
		self._commcell_object = commcell_object
		self._jobid = jobid
		self._LOG = logger.CVCLogger()
		self._LOG.initializelogger('cvc.log', loggingPath)
		self._LOG = self._LOG.log

	def get_job_summary(self):
		"""
		Method to fetch complete job summary :
		Args :
		Job Class object
		Returns :
		Status Flag : Marks the Job completion Status
		prints Job Summary details :
		"""
		bflag = 1
		#  Reads the Summary of job into dictionary object
		try:
			self._LOG.info("Job Summary Module")
			jobobj = job.Job(self._commcell_object, self._jobid)
			is_finished = jobobj.is_finished
			main_dict = jobobj.summary
			if main_dict is None:
				raise Exception("No data obtained for job summary")
			bflag = 0
			for key, value in main_dict.items():
				if key == 'subclient':
					for key1, value1 in main_dict['subclient'].items():
						self._LOG.info("{0} : {1}".format(key1, value1))
				else:
					self._LOG.info("{0} : {1}".format(key, value))
		except Exception as job_summary_exception:
			job_summary_exception = str(job_summary_exception)
			self._LOG.error("Issue Occurred while fetching Job Summary: %s"%job_summary_exception)
			print("Operation failed. Error while fetching job details")
			bflag = 1
		finally:
			if bflag == 0:
				print("Client Name : %s" % (jobobj.client_name))
				print("Agent Name  :%s " % (jobobj.agent_name))
				print("BackupSet Name : %s" % (jobobj.backupset_name))
				print("Subclient Name :%s" % (jobobj.instance_name))
				print("Job ID  :%s" % (jobobj.job_id))
				print("Job type  :%s" % (jobobj.job_type))
				print("Start Time  :%s" % (jobobj.start_time))
				print("End Time  :%s" % (jobobj.end_time))
				print("Job Status : %s" % (jobobj.status))
			return bflag

	def get_job_status(self, outputFilePath=None):
		"""
		Method  to get  current status of given Job  ID
		Returns :
		Job Current Status : Completed/Suspended/Waiting Etc
		Job Finish Status : True / False [Based on Finish nature of Job ID ]
		"""
		bflag = 1
		root = etree.Element('Task')

		# another child with text
		child1 = etree.Element('job_status')
		job_finish_status = False
		job_status = ""
		try:
			self._LOG.info("Job Get Status Module")
			jobobj = job.Job(self._commcell_object, self._jobid)
			# Check  if given job ID is valid
			check_job_valid = jobobj._is_valid_job()
			if check_job_valid is True:
				job_status = jobobj.status
				job_finish_status = jobobj.is_finished
				bflag = 0
			else:
				raise Exception("Invalid Job ID")
		except Exception as job_status_exception:
			self._LOG.error("Issue Occurred while fetching  current job status ")
			self._LOG.error(job_status_exception)
			bflag = 1
		finally:
			if bflag == 0:
				self._LOG.info("Getting job status successful")
				child1.text = job_status
				root.append(child1)
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
				self._LOG.error("Error while getting job status")

			return (bflag, job_finish_status, job_status)

	def action_on_job(self, operation):
		"""
		Method to perform  any of below operation for given Job ID
		kill
		resume
		pause
		"""
		bflag = 1
		try:
			self._LOG.info("inside Job operation method")
			jobobj = job.Job(self._commcell_object, self._jobid)
			if operation == 'kill':
				jobobj.kill()
				print("Job Killed")
			elif operation == 'pause':
				jobobj.pause()
				print("Job Paused")
			elif operation == 'resume':
				jobobj.resume()
				print("Job Resumed")
			else:
				self._LOG.error("Invalid operation on Job ID ")
			bflag = 0
		except Exception as job_action_exception:
			self._LOG.error("Issue in implementing the action on given job %s"%job_action_exception)
			bflag = 1
		finally:
			return bflag
