# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for initializing the logger for Automation.

This module handles the initialization of logger object and the handlers for the log files.

**Logger**:     Class for initializing a new logger object if there does not exists a logger object
for the thread it is called from.


If a logger object is already available for the calling thread, then the same object is returned.

Otherwise a new logger object is created and returned with the file handler attached for the
file name given in the initialization.


If it is intended to get the logger object for the current thread with the same handlers, then the
**get_log()** method should be called to get the appropriate logger object.


**Logger** class should only be initialized if you wish to create / reuse a logger object for a new
log file, and remove all the file handlers that had been associated earlier to it.


Logger:
    __init__()      --  initialize objects of Logger class

    _initialize()   --  creates the logger object

    log()           --  returns log object

    log_file()      --  returns log file name

    log_dir()       --  returns log directory path



get_log_dir()       --  returns the automation log directory path

getLog()            --  returns the log object for current thread if exists else
create a new standalone logger for current thread

get_log()           --  returns the log object for current thread if exists else
create a new standalone logger for current thread


"""

import os
import logging

from logging.handlers import RotatingFileHandler
from threading import current_thread

from . import constants


class LoggingFilter(logging.Filter):
    """Filter to add additional information to the logger."""

    def __init__(self, job_id):
        """Initializes the object of the LoggingFilter class, to add custom filters to the log.

            This filter adds the job ID to the log.

            Args:
                job_id  (str)   --  job ID for the Automation job

            Returns:
                object  -   instance of the logging.Filter class

        """
        super(LoggingFilter, self).__init__()
        self.job_id = job_id

    def filter(self, record):
        record.jobID = self.job_id
        return True


class Logger(object):
    """Logger class for Automation"""

    def __init__(self, log_dir, file_name, job_id='###'):
        """Initialize the Logger object.

            Args:
                log_dir     (str)   --  Log Directory path

                file_name   (str)   --  Log file name

                job_id      (str)   --  jobID from the input JSON workflow request.

        """
        self._log = None
        self._log_dir = log_dir
        self._log_file = str(file_name) + ".log"
        self._initialize(job_id)

    def _initialize(self, job_id):
        """Initializes logger object"""
        # Create log directory
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

        log_file = os.path.join(self.log_dir, self.log_file)

        logger = logging.getLogger(str(current_thread().ident))     # current_thread().getName()

        # remove the stale handlers, if any
        logger.handlers = []

        logging_filter = LoggingFilter(job_id)
        logger.addFilter(logging_filter)

        log_level = logging.DEBUG
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=constants.LOG_BYTE_SIZE,
            backupCount=constants.LOG_BACKUP_COUNT,
            encoding=constants.LOG_FILE_ENCODING
        )

        logger.setLevel(log_level)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(constants.FORMAT_STRING))

        logger.addHandler(file_handler)

        self.log = logger

    @property
    def log(self):
        """Treats log as read-only property."""
        return self._log

    @log.setter
    def log(self, value):
        """Sets the log property."""
        self._log = value

    @property
    def log_file(self):
        """Treats log file as read-only property."""
        return self._log_file

    @log_file.setter
    def log_file(self, value):
        """Sets the log file property."""
        self._log_file = value

    @property
    def log_dir(self):
        """Treats log directory as read-only property."""
        return self._log_dir

    @log_dir.setter
    def log_dir(self, value):
        """Sets the log directory property."""
        self._log_dir = value


def getLog(thread_id=None):
    """Returns the logger object for the current thread if exists
        else creates a standalone log file with job id as the process id
    """
    if thread_id is None:
        log = logging.getLogger(str(current_thread().ident))    # current_thread().getName()

        if not log.hasHandlers():
            __ = Logger(constants.LOG_DIR, constants.STANDALONE_LOG_FILE_NAME, os.getpid())
            log = logging.getLogger(str(current_thread().ident))

        return log
    else:
        return logging.getLogger(str(thread_id))


def get_log_dir():
    """Returns the CVAutomation Log Directory path"""
    return constants.LOG_DIR


def get_log():
    """Returns the log object corresponding to the current thread if exists
        else creates a new standalone log file with job id as the process id
    """
    return getLog()

def get_custom_logger(log_name, log_file, msg_prefix, job_id='###'):
    """Gets a custom logger based on the inputs given.

        Args:

            log_name    (str)   --  The unique name of the logger

            log_file    (str)   --  The absolute path of the log file

            msg_prefix  (str)   --  The string to append before the message

            job_id      (str)   --  The job id

        Returns:

            logger      (obj)   --  The logger object
    
    """
    logger = logging.getLogger(log_name)
    
    # remove the stale handlers, if any
    logger.handlers = []

    logger.addFilter(LoggingFilter(job_id))

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=constants.LOG_BYTE_SIZE,
        backupCount=constants.LOG_BACKUP_COUNT,
        encoding=constants.LOG_FILE_ENCODING
    )

    log_level = logging.DEBUG
    logger.setLevel(log_level)
    file_handler.setLevel(log_level)

    format_string = constants.FORMAT_STRING.replace('%(message', f"{msg_prefix}%(message")
    file_handler.setFormatter(logging.Formatter(format_string))

    logger.addHandler(file_handler)

    return logger



