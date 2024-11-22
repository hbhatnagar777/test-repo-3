"""Utilities for the TestCase"""
import os
import glob
from AutomationUtils import logger
from AutomationUtils.mail_box import MailBox
from AutomationUtils.mail_box import EmailSearchFilter
from AutomationUtils.wrapper7z import Wrapper7Z
from AutomationUtils.config import get_config
from cvpysdk.license import LicenseDetails
from Web.Common.exceptions import CVTestStepFailure
from Web.API.customreports import CustomReportsAPI

_CONFIG = get_config()


class SendLogUtils:
    """Utilities for the TestCase"""

    def __init__(self, testcase, machine_object):
        """

        Args:
            testcase:
            machine_object: Object of machine where send logs bundle has to accessed
        """
        self.testcase = testcase
        self.machine_object = machine_object
        self.commcell = testcase.commcell
        licence = LicenseDetails(self.commcell)
        self.commcell_id = licence.commcell_id_hex
        self.commcell_name = self.commcell.commserv_name
        self.mail = None
        self.sysyteminfo_path = None
        self.log = logger.get_log()
        self.uncPathAccessed = False

    def _jobid_path(self, sendlog_jobid, jobids=None):
        if jobids:
            jobid_path = 'J' + sendlog_jobid + '_ForJob' + '_'.join(jobids)
        else:
            jobid_path = 'J' + sendlog_jobid
        return jobid_path

    def _job_folder_path(self, current_path, jobid_path):
        glob_pattern_path = os.path.join(current_path, f'{jobid_path}*')
        job_folder_path = glob.glob(glob_pattern_path)
        return job_folder_path[0]

    def verify_email(self, download_directory, subject=None):
        """
        Verifying email for sendLog job
        Args:
            download_directory: Email will get downloaded in given directory
            subject: Subject of the email

        Returns:

        """
        try:
            self.mail = MailBox()
            self.mail.connect()
            if subject:
                email_filter = EmailSearchFilter(subject)
            else:
                email_filter = EmailSearchFilter(
                    "CommCell ID " + self.commcell_id + " Logs for machines: " + self.commcell_name)
            if email_filter:
                self.mail.download_mails(search_filter=email_filter,
                                         download_dir=download_directory)
        except Exception as exp:
            raise CVTestStepFailure(
                f"Email verification get failed  [{exp}]"
            )
        finally:
            self.mail.disconnect()

    def send_log_bundle_path(self, file_path, sendlog_jobid, jobids=None):
        """
        verifies SendLogs Content present at local drive location or not
        Args:
            file_path (str): Where send log bundle exist
            sendlog_jobid (str) : sendlogs job id
            jobids (list) : list of backup job ids
        Returns:
            sendLog : path of the sendlog file
        Raises:
            Exception:
                If send log file pattern not present for filename on path
        """
        if jobids is None:
            jobids = []
        self.log.info(f"Checking sendlogs bundle exist in path {file_path}")
        file_list = self.machine_object.get_files_in_path(folder_path=file_path)
        temp, file_name = self.createZipFilePattern(sendlog_jobid, jobids)
        for sendLog in file_list:
            if 'sendLogFiles' in sendLog and sendLog.endswith((temp, file_name)):
                self.log.info(f"Send Log file {sendLog} present at {file_path}")
                return sendLog
        raise CVTestStepFailure(
            f"Send log file {temp} not present at [{file_path}]"
        )

    def createZipFilePattern(self, sendlog_jobid, jobids):
        """
        Creates the zip file pattern to check for various logs and files present
        Args:
            sendlog_jobid (str) : sendlogs job id
            jobids (list) : list of backup job ids

        Returns:
            temp, filename (str, str) : string of patterns
        """
        temp = sendlog_jobid
        for job_id in jobids:
            temp += '_J' + job_id
        temp += ".7z"
        file_name = temp + ".001"
        return temp, file_name

    def get_uncompressed_path(self, sendlog_jobid, jobids=None):
        """
        Creates the uncompressed filename based on sendlogs job id and other jobids
        Args:
            sendlog_jobid (str) : sendlogs job id
            jobids (list) : list of backup job ids

        Returns:
           Uncompressed filename (str) : filename pattern
        """

        jobid_path = self._jobid_path(sendlog_jobid, jobids)
        if not self.uncPathAccessed:
            self.access_UNC_path()
            self.uncPathAccessed = True
        self.log.info(f"The uncompressed logs path is at {_CONFIG.Reports.uncompressed_logs_path}")
        current_path = os.path.join(_CONFIG.Reports.uncompressed_logs_path, self.commcell_id)
        job_folder_path = self._job_folder_path(current_path, jobid_path)
        return os.path.join(job_folder_path, "UncompressedLogs")

    def get_compressed_path(self, sendlog_jobid, jobids=None):
        """
        Creates the compressed filename based on sendlog job id and other jobids
        Args:
            sendlog_jobid (str) : sendlogs job id
            jobids (list) : list of backup job ids

        Returns:
            Compressed filename (str) : filename pattern
        """

        jobid_path = self._jobid_path(sendlog_jobid, jobids)
        if not self.uncPathAccessed:
            self.access_UNC_path()
            self.uncPathAccessed = True
        self.log.info(f"The compressed logs path is at {_CONFIG.Reports.uncompressed_logs_path}")
        current_path = os.path.join(_CONFIG.Reports.uncompressed_logs_path, self.commcell_id)
        job_folder_path = self._job_folder_path(current_path, jobid_path)
        return os.path.join(job_folder_path, "CompressedLogs")

    def DB_bundle_path(self, file_path, sendlog_jobid, jobids):
        """
        verifies Databases Content present at local drive location or not
        Args:
            file_path (str): Where DB log bundle exist
            sendlog_jobid (str) : sendlogs job id
            jobids (list) : list of backup job ids

        Returns:
            dbfile (str) : path of the Database File

        Raises:
            Exception:
                If Database file pattern not present for filename on path

        """
        self.log.info(f"Checking DB bundle exist in path {file_path}")
        file_list = self.machine_object.get_files_in_path(folder_path=file_path)
        temp, file_name = self.createZipFilePattern(sendlog_jobid, jobids)
        for dbfile in file_list:
            if 'DBFiles' in dbfile and dbfile.endswith((temp, file_name)):
                self.log.info("Database file [*{temp}] present at " + dbfile)
                return dbfile

        raise CVTestStepFailure(
            f"Database file [*{temp}] not present for [{sendlog_jobid}] at [{file_path}]"
        )

    def verify_entities(self, file_list, entities_dict, path, partial_name_verify=False):
        """
        Verifies list of files in the entities dictionary are present in the given file list
        Args:
            file_list (list) : list of file paths
            entities_dict (dict) :  dictioniary with file name , status values
            path (str) : sendlogs bundle path
            partial_name_verify (bool) : whether to fully/partially verify the entity name
        Raises:
            Exception:
                if given file names are not present in the file path 

        """
        flag = 0
        for each_file in file_list:
            if "\\" in each_file:  # Windows path
                entity = each_file.split('\\')[-1]
            else:  # Unix path
                entity = each_file.split('/')[-1]
            if partial_name_verify:
                for each_entity in entities_dict.keys():
                    if each_entity.lower() in entity.lower():
                        entities_dict[each_entity] = True
                        self.log.info(f'{each_entity} present at {path} with filename: {entity}')
                        break
            else:
                if entity in entities_dict:
                    entities_dict[entity] = True
                    self.log.info(f'{entity} present at {path}')

            if all(entities_dict.values()):
                break

        for entity, found in entities_dict.items():
            if not found:
                self.log.info(f'{entity} not present at {path}')
                flag = 1

        if flag:
            raise CVTestStepFailure(
                f"Some files are missing from the bundle. Kindly check the logs and debug further"
            )

    def is_index_file_exists(self, file_path, client_name, backupset_guid):
        """
        verifies if index files are present in the sendlogs bundle
        Args:
            file_path (str): Where send log bundle exist
            client_name (str) : client name
            backupset_guid (str) : backup set guid

        Returns:

        """

        file_path = os.path.join(file_path, client_name, "Index Cache",
                                 backupset_guid)
        self.log.info("Index file path  : " + file_path)
        file_list = self.machine_object.get_files_in_path(folder_path=file_path)
        entities_dict = {'ImageTable.dat': False, 'ImageTable.idx': False,
                         'SIMetaDataTable.dat': False, 'SIMetaDataTable.idx': False,
                         'ArchiveFileTable.dat': False, 'ArchiveFileTable.idx': False,
                         '.dbInfo': False}
        self.verify_entities(file_list, entities_dict, file_path)

    def log_file_verification_with_full_name(self, file_path, file_names):
        """
        verifying in comm server log existence of cvd,evmgr,Job manager log,.........
        Args:
            file_path   (str): full path for file want to check
            file_names (list): Full Name of file that want to check

        Returns:

        """
        for file_name in file_names:
            if self.machine_object.check_file_exists(os.path.join(file_path, file_name)):
                self.log.info(f"[{file_name}] present in send log file in {file_path}")
            else:
                raise CVTestStepFailure(
                    f"[{file_name}] file not present at location:[{file_path}]"
                )

    def log_file_verification_with_partial_name(self, file_path, file_name):
        """
        In this case we don't have exact file name due to name change in every job
        Args:
            file_path (str): full path for file want to check
            file_name (str): File name  either full or partial name

        Returns:

        """

        file = self.machine_object.get_files_in_path(folder_path=file_path)
        for file_var in file:
            if file_name in file_var:
                self.log.info(f"[{file_name}] present at location [{file_path}]")
                return file_var

        raise CVTestStepFailure(
            f"{file_name} not present in SendLog files "
        )

    def verify_machine_logs_and_os_logs(
            self, client_object, file_path, full_file_name, partial_file_name):
        """
        Unzip and verify content by full name of file or given partial name of file
        Args:
            client_object           : Client object for machine where file exist
            file_path (str)         : full path for file that want to check
            full_file_name (list)   : full name of file
            partial_file_name (list): full or partial name of file

        Returns:

        """
        wrapper = Wrapper7Z(commcell=self.commcell, client=client_object, log=self.log,
                            zipfilepath=file_path)
        wrapper.extract()
        file_path = file_path[:-3]
        self.log_file_verification_with_full_name(file_path, full_file_name)
        for file_name in partial_file_name:
            self.log_file_verification_with_partial_name(file_path, file_name)

    def unzip_send_log_file(self, client_obj, file_path=''):
        """

        Args:
            client_obj      : Client of Machine there send log bundle exist
            file_path (str) : Where send log bundle exist

        Returns:

        """
        self.log.info("Send Log content is wrapping .....")
        wrapper = Wrapper7Z(
            commcell=self.commcell, client=client_obj, log=self.log, zipfilepath=file_path)
        wrapper.extract()
        if "windows" in client_obj.os_info.lower():
            temp = file_path.find('.7z') - len(file_path)
            file_path = file_path[:int(temp)]
            return file_path
        else:
            return os.path.dirname(file_path)

    def create_directory_for_given_path(self, directory_path):
        """

        Args:
            directory_path: folder name, don't give directory name like (C:\\)

        Returns:

        """
        if "windows" in self.machine_object.os_info.lower():
            directory_name = os.path.join("C:\\", directory_path)
        else:
            directory_name = f'/root/{directory_path}'

        if self.machine_object.create_directory(
                directory_name=directory_name, force_create=True):
            return directory_name
        raise CVTestStepFailure(
            f" Failed to create folder name {directory_name}"
        )

    def get_request_id(self):
        """get request id for the troubleshooting request from the database

        Args:

        Returns:
            Returns remote troubleshooting request id
        """
        cloud_cre_api = CustomReportsAPI(_CONFIG.Reports.PUBLIC_CLOUD,
                                         username=_CONFIG.Cloud.username,
                                         password=_CONFIG.Cloud.password)
        query = r"""
            select top 1 requestid 
            from CloudRequest 
            where requesttypeid = 17 
            order by RequestId desc
        """

        response = cloud_cre_api.execute_sql(query, database_name="CloudServices",
                                             connection_type="METRICS")
        if not response:
            raise CVTestStepFailure(
                "Retreiving request id from Clouservices Database failed"
            )
        return response[0][0]

    def access_UNC_path(self, logs_path=_CONFIG.Reports.uncompressed_logs_path,
                        unc_user=_CONFIG.Reports.sendlogs_username,
                        unc_password=_CONFIG.Reports.sendlogs_userpassword):
        """
            Accessing send logs path
        """
        command = 'net use %s %s /user:%s /persistent:yes' % (
            logs_path, unc_password, unc_user)
        retCode = os.system(command)
        if retCode != 0:
            self.log.error(
                "Error executing net use remote command - retcode :: " + str(retCode))
            raise CVTestStepFailure(
                f"Error in accessing UNC path"
            )
        else:
            self.log.info('Successfully executed net use remote command')

    def change_http_setting(self):
        """
            Modify send logs http site in GxGlobalParam
        """
        http_url = 'https://' + _CONFIG.Reports.SENDLOGS_HTTP_UPLOAD + '/commandcenter'
        self.log.info('Changing the http site to ' + http_url)
        self.commcell.add_additional_setting(category='CommServDB.GxGlobalParam',
                                             key_name='SendLogsCurrentHTTPSite',
                                             data_type='STRING',
                                             value=http_url)
