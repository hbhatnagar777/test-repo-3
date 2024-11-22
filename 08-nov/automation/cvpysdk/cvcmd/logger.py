"""
Main File  for Defining Logging class for CVC

"""
import os
import logging
from logging import Logger
from logging.handlers import RotatingFileHandler


class CVCLogger(object):
	"""
	Class for defining CVCLogger using Logging Module
	"""

	def __init__(self):
		self._log = None
		self._logfile = None

	@property
	def log(self):
		"""
		Returns Log attribute of CVCLogger object
		"""
		return self._log

	@log.setter
	def log(self, value):
		# Set the log
		self._log = value

	@property
	def logfile(self):
		"""
		Returns Logfile  attribute of CVCLogger object
		"""
		return self._logfile

	@logfile.setter
	def logfile(self, value):
		"""
		Sets Passed value to Attribute logfile of CVCLogger Object
		"""
		self._logfile = value

	def setuplogger(self, logfilename, loglocation):
		"""
		Method to set Location and Filename for respective log object
		"""
		return self.initializelogger(logfilename, loglocation)

	def initializelogger(self, logfilename, specifieddirectory):
		"""
		Method setting corresponding values for different attributes for Logging
		"""
		LOG_FORMAT = '%(process)d\t%(thread)d\t%(asctime)s\t%(levelname)-5s\t%(message)s'
		LOG_BYTE_SIZE = 5242880  # size in bytes of each log file.
		SAVED_LOG_COUNT = 5  # number of log files to keep
		LOG_WRITE_MODE = 'a'
		LOG_ENCODING = 'utf-8'
		creating_new_log_file = False
		try:
			if not os.path.exists(specifieddirectory):
				os.makedirs(specifieddirectory)

			logFile = os.path.join(specifieddirectory, logfilename)
			if not os.path.exists(logFile):
				creating_new_log_file = True

			try:
				# Initialize the logger
				logger = Logger(logfilename.split('.')[0])
				loglevel = logging.DEBUG
				filehandler = RotatingFileHandler(
					logFile,
					LOG_WRITE_MODE,
					LOG_BYTE_SIZE,
					SAVED_LOG_COUNT,
					encoding=LOG_ENCODING)
				filehandler.setLevel(loglevel)
				filehandler.setFormatter(logging.Formatter(LOG_FORMAT))
				logger.addHandler(filehandler)
				# once the log file is created successfully, we set the permisssions to 666
				if os.path.exists(logFile) and creating_new_log_file:
					import platform
					if platform.system() == 'Linux' or platform.system() == 'OS400':
						os.chmod(logFile, 0o600)
			except Exception as erno:
				print(erno)
				raise

			# Set the loggers.
			global log
			self.log = logger  # This allows creator access to the object
			self.logfile = logFile
			log = logger  # This allows future importers access to the object

			return True
		except Exception as err:
			print(err)
			raise
