# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing onepass operations

cvonepas_helper: Helper class to perform file system onepass operations

cvonepas_helper:
    __init__()              --  initializes cvonepas_helper helper object

    populate_inputs()       -- use to pass all the input values
                               to related variables

    get_client_machine()    -- return client machine object

    set_client_machine()    --  create new client machine object
                                and assign to self.client_machine

    create_backupset()      -- create new backupset

    create_subclient()      --  creates new subclient

    run_archive()           --  run onpass subclient archive job

    set_scan_type()         -- change subclient scan type setting

    verify_stub()           --  verify stub creation

    recall()                --  do onepass recall process

    restore_in_place_restoreStub_unconditional()
                            --  Run onepass in place restore with
                                restore stub option enabled

    verify_restore_result() --  verify onepass restore result

    create_archiveset()     -- creates new archiveset

    move_file_gxhsm()       --  Moves file using gxhsm utility in windows.

    restub_checks()         --  Checks for re-stubbing feature
"""

from FileSystem.FSUtils.fshelper import ScanType, FSHelper
from AutomationUtils.machine import Machine
from AutomationUtils.unix_machine import UnixMachine
from AutomationUtils.cvtestcase import CVTestCase


class cvonepas_helper(FSHelper):
    """Helper class to perform file system operations"""

    def __init__(self, testcase):
        """Initialize instance of the OnePass class.

            Args:
                testcase    (object)  --    Object of CVTestCase

            Returns:
                None

            Raises:
                Exception:
                    if a valid CVTestCase object is not passed.
                    if CVTestCase object doesn't have agent initialized
        """
        if not isinstance(testcase, CVTestCase):
            raise Exception(
                "Valid test case object must be passed as argument"
            )
        super(cvonepas_helper, self).__init__(testcase)
        self.client_machine = None
        self.media_agent = ''
        self.library_name = ''
        self.client_name = ''
        self.client_host_name = ''
        self.client_host_user_name = ''
        self.client_host_password = ''
        self.archiveset_name = 'DefaultArchiveSet'
        self.file_archiver_instance_name = ''
        self.access_path = ''
        self.agent_name = ''
        self.actual_client = None
        self.agent_machine_host_name = ''
        self.agent_name_list = []
        self.nas_turbo_type = 'Local'
        self.subclient_prop = {}
        self.restore_path = ''
        self.org_hashcode = {}
        self.recall_hash = {}
        self.restore_hashcode = {}
        self.feature = "Data Protection"
        self.product = "FileSystem"
        self.subclient_props = {}
        self.slash_format = '\\'
        self.scan_type = ['Change Journal', 'Classic File Scan',
                          'DC for FS backups']
        self.test_file_list = [("shouldbearchived.txt", True),
                               ("shouldnotbearchived.txt", False)]

    def populate_inputs(self, mandatory=True):
        """Initializes all the test case inputs after validation
            Args:
                mandatory      (bool)   --  whether to check  mandatory inputs
                                            and raise exception if not found

            Returns:
                None

            Raises:
                 Exception:
                     if a valid CVTestCase object is not passed.
                     if CVTestCase object doesn't have agent initialized
        """
        log = self.testcase.log
        log.info("*" * 80)
        log.info("at populate_inputs function")
        case = self.testcase
        try:
            log.info('start parsing test case input parameters')
            # initial all the input value in parent class first
            self.populate_tc_inputs(case)
            self.product = case.products_list.FILESYSTEM
            self.feature = case.features_list.DATAPROTECTION
            case.show_to_user = True
            self.access_path = case.tcinputs.get('TestPath', None)
            self.subclient_props['storage_policy_name'] = case.tcinputs.get(
                'StoragePolicyName', None)
            self.client_name = case.tcinputs.get('ClientName', None)
            self.client_host_name = case.tcinputs.get('HostName', None)
            self.client_host_user_name = case.tcinputs.get('UserName', None)
            self.client_host_password = case.tcinputs.get('Password', None)
            self.actual_client = case.tcinputs.get('ActualClient', None)
            self.agent_name_list = case.tcinputs.get('DataAccessNodes', [])
            if self.agent_name_list:
                self.agent_name = self.agent_name_list[0]
            else:
                self.agent_name = self.client_name
            self.nas_turbo_type = case.tcinputs.get('NASTurboType', 'Local')
            if len(self.agent_name_list) > 1:
                self.nas_turbo_type = 'NetworkShare'

            if (self.subclient_props['storage_policy_name'] is None and
                    mandatory is True):
                raise Exception(
                    "StoragePolicyName is a"
                    " mandatory string input for the test case"
                    )
            if(self.access_path is None and mandatory):
                raise Exception(
                    "TestPath is a"
                    " mandatory string input for the test case"
                )

            if ((case.agent.agent_name.lower() == "file system") or
                    case.agent.agent_name is None):
                # provide default value
                self.testcase.instance = case.agent.instances.get(
                    "DefaultInstanceName"
                    )
            else:
                # not support for other agent
                self.testcase.instance = None

            self.set_client_machine()

        except Exception as excp:
            log.exception('exception raised at with error : %s' % str(excp))
            raise Exception('Backupset Creation Failed with error')

    def get_client_machine(self):
        """Returns the machine object."""

        log = self.testcase.log
        log.info("*" * 80)
        log.info("at get_client_machine function")
        try:
            if self.client_machine is None:
                raise Exception('Client machine  not initialized')
            return self.client_machine
        except Exception as excp:
            log.exception("exception raised with error %s" % str(excp))
            raise Exception("exception raise at get_client_machine function")

    def set_client_machine(self):
        """ set machine object

            for traditional file system and onepass local Agent, we will
            use actual client machine to create machine object
            for pseudo client, we will create machine object point
            to agent machine
            for multi-nodes pseudo client, we will use the first node
            as main node, and create machine object point to first node
            since all the agent machine should be active machine on CS,
            so we will create agent machine object based on cvd method
            to minimize the input requirements (no extra agent machine
            login account info needed)

            Args:
                None

            Return:
                None

            Raises:
                 Exception:
                     if fail to create machine object.
        """

        log = self.testcase.log
        log.info("*" * 80)
        log.info("at set_client_machine function")
        try:
            cv_testcase = self.testcase
            if (cv_testcase.agent.agent_name.lower() == "file system" and
                    self.nas_turbo_type == 'Local'):
                _actual_client = self.client_name
                _actual_client_host_name = self.client_host_name
                _actual_client_username = self.client_host_user_name
                _actual_client_password = self.client_host_password
            else:
                # in case for multi-node, only use the
                # fist node as access machine
                if self.actual_client is None:
                    _actual_client = self.agent_name_list[0]
                else:
                    _actual_client = self.actual_client
                # for sudo client,since proxy machine should be active machine
                _actual_client_host_name = None
                # for sudo client, we will rely on cvd to do
                # actual client side access
                _actual_client_username = None
                # to simplify the input parameters for each test case
                _actual_client_password = None

            if (_actual_client_username is not None and
                    _actual_client_password is not None):
                # If credentials are given, directly login using credentials
                self.client_machine = Machine(_actual_client_host_name,
                                              _actual_client_username,
                                              _actual_client_password)
            else:
                # If no credentials are given, use cvd for all communications
                self.client_machine = Machine(_actual_client,
                                              cv_testcase.commcell)
            if isinstance(self.client_machine, UnixMachine):
                self.slash_format = '/'
            else:
                self.slash_format = '\\'

        except Exception as excp:
            log.exception("exception raised at with error %s" % str(excp))
            raise Exception("exception raise at set_client_machine function")

    def create_backupset(self, name=None, delete=False, is_nas_turbo_backupset=False):
        """
        this is wrap function, it will just pass the request to
        superclass create_backupset function

         Args:
                name: (str)

                            --need provide string value of testcase.id

                            default: None, function will assign backupset
                                     Name  as Backupset_testcase.Id

                delete:         (bool)

                            default: False - will not recreate backupset
                                             if existed
                                     True - will recreate backupset

                is_nas_turbo_backupset  (bool): True for NAS based client.

            Return:
                parent class create_backupset function

        """
        log = self.testcase.log
        log.info("*" * 80)
        log.info("at create_backupset function")
        if name is None:
            _backpupset_name = 'Backupset_{0}'.format(str(self.testcase.id))
        else:
            _backpupset_name = name

        return super(cvonepas_helper, self).create_backupset(
            _backpupset_name,
            delete,
            is_nas_turbo_backupset
            )


    def create_archiveset(self, name=None, delete=False, is_nas_turbo_backupset=False):
        """Creates new archiveset with specified parameters
             under the current testcase Instance.

            Checks if the archiveset exists or not.
            If the archiveset exists, deletes the existing archiveset
            and creates new one with the testcase id.

            Args:
                name   (str)  -- name of the archiveset

                delete (bool) -- indicates whether existing archiveset should be deleted
                    default: False

                is_nas_turbo_backupset  (bool): True for NAS based client.

            Returns:
                None

            Raises:
                Exception - Any error occurred during archiveset creation

        """
        log = self.testcase.log
        log.info("*" * 80)
        log.info("at create_archiveset function")
        if name is None:
            archiveset_name = 'Archiveset_{0}'.format(str(self.testcase.id))
        else:
            archiveset_name = name

        try:
            self.log.info("Checking if archiveset %s exists.", archiveset_name)
            archivesets_object = self.testcase.instance.backupsets
            if archivesets_object.has_backupset(archiveset_name):
                if delete:
                    self.log.info("Archiveset exists, deleting Archiveset %s", archiveset_name)
                    archivesets_object.delete(archiveset_name)
                    self.log.info("Creating Archiveset %s", archiveset_name)
                else:
                    self.log.info("Archiveset exists, using existing Archiveset %s", archiveset_name)
                    self.testcase.backupset = archivesets_object.get(archiveset_name)
                    return
            else:
                self.log.info("Archiveset doesn't exist, creating Archiveset %s", archiveset_name)
            self.testcase.backupset = (
                archivesets_object.add_archiveset(archiveset_name, is_nas_turbo_backupset=is_nas_turbo_backupset)
            )
        except Exception as excp:
            self.log.error('Archiveset Creation Failed with error: %s', excp)
            raise Exception('Archiveset Creation Failed with error: {0}'.format(str(excp)))




    def create_subclient(self, name=None, storage_policy=None,
                         content=None, filter_content=None,
                         exception_content=None, trueup_option=True,
                         trueup_days=30, scan_type=ScanType.OPTIMIZED,
                         data_readers=4, allow_multiple_readers=True,
                         read_buffer_size=512,
                         block_level_backup=None,
                         delete=False,
                         data_access_nodes=None):
        """
        This function is a wrap  function and will pass value to
        parent class create_subclient function

            Args:
                storage_policy:  (str) -- associated storage policy Name

                name:     (str) -- name of subclient, function will
                                                set default name
                                                dfault: None

                content:  (list) -- subclient content, function will
                                                set default content if not
                                                default: None

                filter_content:   (list) -- filter list
                                                default: None

                exception_content:(list) -- exception list
                                                default: None

                trueup_option:     (bool) -- enable / disable true up
                                                default: True

                trueup_days:        (int)  -- trueup after n days
                                                default: 30

                scan_type:          (ScanType(Enum))
                                               --scan type as one of below
                                                         RECURSIVE
                                                         OPTIMIZED
                                                         CHANGEJOURNAL
                                                default: ScanType.OPTIMIZED

                data_readers:           (int) --number of data readers
                                                default: 2


                allow_multiple_readers: (bool)--enable / disable
                                                allow multiple readers
                                                default: False



                read_buffer_size:   (int) --read buffer size in KB
                                                default: 512

                delete:             (bool) -- indicates whether existing
                                                subclient should be deleted
                                                default: False

                block_level_backup  (str) -- blocklevel backup data switch
                                               default: None

                data_access_nodes   (list) --creates a subclient with
                                             access nodes for NAS onepas
                                             default : None
            Returns:
                 parent class create_subclient function will assigned value

            Raises:
                 Exception - Any error occurred during Subclient creation


        """
        # Create Subclient, TestContent and  Path info
        log = self.testcase.log
        log.info('at create_subclient function')
        try:
            log.info('start create new test_set')
            if storage_policy is not None:
                _storage_policy = storage_policy
            else:
                _storage_policy = self.subclient_props['storage_policy_name']
            if name is None:
                self.subclient_props['subclient_name'] = r'SC_{0}_{1}'.format(
                    str(self.testcase.id), scan_type.name
                    )
            else:
                self.subclient_props['subclient_name'] = name

            if content is None:
                self.subclient_props['subclient_content'] = [
                    (
                        self.access_path +
                        '{0}{1}_{2}_data'.format(
                            self.slash_format,
                            str(self.testcase.id),
                            scan_type.name
                            )
                    )
                    ]
            else:
                self.subclient_props['subclient_content'] = content
            _src_path1 = self.subclient_props['subclient_content'][0]
            _restore_path = _src_path1.replace('data', 'restore')
            self.subclient_props['outofplace_restore_path'] = _restore_path
            if data_access_nodes is not None:
                _data_access_node = data_access_nodes
            else:
                _data_access_node = self.agent_name_list
            self.subclient_props['filter'] = filter_content
            self.subclient_props['exception'] = exception_content
            self.subclient_props['trueup_enabled'] = trueup_option
            self.subclient_props['trueup_days'] = trueup_days
            self.subclient_props['scan_type'] = scan_type
            self.subclient_props['multiple_readers'] = allow_multiple_readers
            self.subclient_props['data_readers'] = data_readers
            self.subclient_props['data_buffer'] = read_buffer_size
            return super(cvonepas_helper, self).create_subclient(
                self.subclient_props['subclient_name'],
                _storage_policy,
                self.subclient_props['subclient_content'],
                self.subclient_props['filter'],
                self.subclient_props['exception'],
                self.subclient_props['trueup_enabled'],
                self.subclient_props['trueup_days'],
                self.subclient_props['scan_type'],
                self.subclient_props['data_readers'],
                self.subclient_props['multiple_readers'],
                self.subclient_props['data_buffer'],
                block_level_backup=block_level_backup,
                delete=delete,
                data_access_nodes=_data_access_node
                )
        except Exception as excp:
            log.exception("exception raised at  with error %s" % str(excp))
            raise Exception("exception raise at create_subclient function")

    def set_scan_type(self, scan_type):
        """
        set subclient scan type

            Args:
                  scan_type  (ScanType(Enum))
                                        --scan type as one of below
                                                RECURSIVE
                                                OPTIMIZED
                                                CHANGEJOURNAL
                                                default: ScanType.OPTIMIZED

            Return:
                None

            Raises:
                 Exception - Any error occurred during Subclient creation
        """

        log = self.testcase.log
        log.info('at set_scan_type function')
        try:
            self.testcase.subclient.scan_type = scan_type.name
        except Exception as excp:
            log.exception("exception raised with error %s" % str(excp))
            raise Exception("exception raise at set_scan_type function")

    def prepare_turbo_testdata(self, content_path, test_file_list,
                               size1=0, size2=0, backup_type='Full'):
        """
        This function will generate test files mainly for onepass use
            Args:

                content_path (str): the folder path

                test_file_list (list):
                         e.g
                         [('shouldbearchive.txt 'True'),
                         ('shouldnotbearchive.txt 'False')]
                         each item in testFileList will be tuple type
                         include fileName and 'True'/'False'
                         fileName- the name of the file it will create
                         'True' - means this file will meet migration rule
                         and will create file with size as Size1
                         'False'- means this file will not meet migration rule
                         and will create file with size as Size2

                size1   (int) -size of file using byte as unit, default is 0

                size2   (int) -size of file using byte as unit, default is 0

                backup_type  (str) backup job type, default is 'Full'

            Return:

                self.client_machine.get_checksum_list(content_path)

            Raises:
                Exception:
                    if error occurred

        """
        log = self.testcase.log
        # begin to backup
        log.info("start parepare turbo test data ")
        try:
            if not isinstance(self.client_machine, Machine):
                raise Exception("client machine didn't initial," +
                                " please call set_client_machine " +
                                "initial client first")

            _client = self.client_machine
            if backup_type == 'Full':
                if _client.remove_directory(content_path) == (1, None):
                    raise Exception("Exception raised ")
                _status = _client.create_directory(content_path)
                if _status is not True:
                    raise Exception("Failed to create modify directory")

            for _file, _status in test_file_list:
                if _status is True:
                    _size = size1
                else:
                    _size = size2

                _file_full_name = _client.join_path(content_path, _file)
                _client.create_file(_file_full_name, '', file_size=int(_size))

            return self.client_machine.get_checksum_list(content_path)

        except Exception as excp:
            raise Exception("exception raised with error %s" % str(excp))

    def run_archive(self, backup_level='INCREMENTAL', do_not_wait=False, repeats=1):
        """ This function is a wrap function to run an archive job
        for related subclient

            Args:
                 backup_level  (str)
                                Full ->FULL job,
                                INCREMENTAL->INCREMENTAL job,
                                DIFFERENTIAL->DIFFERENTIAL job,
                                SYNTHETIC_FULL->
                                    SYNTHETIC_FULL -runIncrementalBackup false,
                                SynFullBackupWithIncBefore->
                                    SYNTHETIC_FULL -runIncrementalBackup true,
                                SynFullBackupWithIncAfter->
                                    SYNTHETIC_FULL -runIncrementalBackup true

                do_not_wait    (bool) True  - will return job instance and
                                              not wait job finish
                                      False - will wait job finish then
                                              return the job instance

                repeats         (int)   Number of times archive operation must be repeated.

             Returns:
                 object - instance of the Job class for this archive job if
                          its an immediate return Job
                          instance of the Job class for the archive job if
                          its a finished Job

             Raises:
                 SDKException:
                     if backup level specified is not correct
        """
        job_list = []
        for repeat in range(repeats):
            log = self.testcase.log
            # begin to backup
            log.info("start archive job with backup type: " + backup_level)
            backup_map = \
                {
                    'Full': ('Full', False, 'BEFORE_SYNTH'),
                    'INCREMENTAL': ('Incremental', False, 'BEFORE_SYNTH'),
                    'DIFFERENTIAL': ('Differential', False, 'BEFORE_SYNTH'),
                    'SYNTHETIC_FULL': ('Synthetic_full', False, 'BEFORE_SYNTH'),
                    'SynFullBackupWithIncBefore': ('Synthetic_full',
                                                   True, 'BEFORE_SYNTH'),
                    'SynFullBackupWithIncAfter': ('Synthetic_full',
                                                  True, 'AFTER_SYNTH'),
                }

            (_backup_level, _inc_backup, _inc_level) = backup_map[backup_level]
            log.info('at run_Archive function')
            log.info('start job with inc value = %s' % backup_level)
            try:
                if(do_not_wait is True and
                   backup_level not in ('SynFullBackupWithIncBefore',
                                        'SynFullBackupWithIncAfter')):
                    current_job = self.testcase.subclient.backup(_backup_level,
                                                                 _inc_backup,
                                                                 _inc_level)
                    return [current_job]
                elif (do_not_wait is True and
                      backup_level in ('SynFullBackupWithIncBefore',
                                       'SynFullBackupWithIncAfter')):
                    log.error('do not wait option is only applicable for ' +
                              'SynFullBackupWithIncBefore and ' +
                              ' SynFullBackupWithIncAfter backuptype')
                    raise Exception('exception raise at run_Archive function')
                else:
                    if _inc_backup:
                        _backup_type_fullname = backup_level + ' with incremental ' \
                                                + _inc_level
                    else:
                        _backup_type_fullname = backup_level
                    log.info("Starting {0} Backup ".format(_backup_type_fullname))
                    job = self.run_backup(backup_level=_backup_level,
                                               incremental_backup=_inc_backup,
                                               incremental_level=_inc_level)
                    job_list.extend(job)
            except Exception as excp:
                log.error('Job error : %s' % str(excp))
                raise Exception('Exception raise with error:%s' % str(excp))
        return job_list

    def verify_stub(self, path=None, test_data_list=None, is_nas_turbo_type=False):
        """ this function will verify whether stub rules get honor

            Args:
               path     (str)  parent folder path
                    default -   None function will automatically assign
                                        self.subclient_props['subclient_content'][0]

               is_nas_turbo_type  (bool): True for NAS based client.
                    default -   False

               test_data_list (list) with each item as tuple type
                        e.g
                            [('shouldbearchive.txt 'True'),
                            ('shouldnotbearchive.txt 'False')]
                            fileName- the name of the file it will create
                            'True' - means this file will meet migration rule
                                    and will create file with size as Size1
                            'False'- means file will not meet migration rule
                                    and will create file with size as Size2

                            default: None, function will automatically
                                     assign self.test_file_list

             Return:
                 None

             Raises:
                 exception:
                     if should stub file didn't stub or
                     should not stub file get stubbed

        """
        log = self.testcase.log
        log.info('start to verify_stub job')
        try:
            if path is None:
                _path = self.subclient_props['subclient_content'][0]
            else:
                _path = path

            if test_data_list is None:
                _test_file_list = self.test_file_list
            else:
                _test_file_list = test_data_list
            # Verify the stub result
            for _filename, _status in _test_file_list:
                _stub_file_name = self.client_machine.join_path(_path, _filename)
                _ret_val = self.client_machine.is_stub(_stub_file_name, is_nas_turbo_type)
                if _ret_val != _status:
                    log.error("%s doesn't follow stub rule" % _stub_file_name)
                    raise Exception("Exception raised at verify_stub function")
                if _status is True:
                    log.info(" create [%s] file's stub " % _stub_file_name)
                else:
                    log.info(" system follow the migration rules setting, " +
                             " and didn't create stub file for file " +
                             " that doesn't meet migration rule")
        except Exception as excp:
            log.error('exception raised with error :%s ' % str(excp))
            raise Exception('exception raised at verify_stub function')

    def recall(self, org_hashcode=None, path=None):
        """ This function will do stub recall and verify recall result
            should match original file

            Args:
                org_hashcode  (list)  with each item is a tuple object
                                    e.g
                                    {('file1.txt' hashcode_valule),
                                    ('file2.txt' hashcode_valule)}
                                    default: None ,
                                    function will use self.org_hashcode

                path               (str)  parent folder path
                                    default: None, function will use
                                    subclient content path

            Return:
                None

            Raises:
                    exception:
                        if recalled stub file hash code doesn't match
                        original file hash value
        """
        log = self.testcase.log
        log.info('start recall the existing stubs')

        if (org_hashcode is None) and (not self.org_hashcode):
            raise Exception("fail to get file original hash code information")
        elif org_hashcode is not None:
            _org_hashcode = org_hashcode
        else:
            _org_hashcode = self.org_hashcode

        if path is None:
            _path = self.subclient_props['subclient_content'][0]
        else:
            _path = path

        self.recall_hash = self.client_machine.get_checksum_list(_path)
        # compared the recalled file hash code with original hash code
        _matched, _code = self.client_machine._compare_lists(
            self.recall_hash,
            _org_hashcode
            )
        if _matched is False:
            raise Exception("At least one recalled stub content " +
                            " does not match with the original")
        log.info("Recalled stubs are matching with the original content")

    def restore_in_place_restore_stub(self, paths=None,
                                      from_time=None, to_time=None,
                                      delete_original_path=True):
        """Restores the files/folders specified
            in the input paths list to the same location.
            by default _restore_in_place function will set restore ACL = True,
            unconditional overwrite = True
            then do in palce restore, this is a wrap function to explicitly
            set restoreDatainsteadofStub= True

            Args:
                paths                   (list)  --  list of full paths
                                                    of files/folders to restore

                from_time           (str)       --  time to
                                                    retore the contents after
                    format: YYYY-MM-DD HH:MM:SS
                    default: None

                to_time           (str)         --  time to
                                                    retore the contents before
                    format: YYYY-MM-DD HH:MM:SS
                    default: None

                delete_original_path (bool)
                        default - True, it will delete existing path
                                        before restore
                                  False, will not clean restore path
            Returns:
                object - instance of the Job class for this restore job

            Raises:
                Exception - Any error occurred while running restore
                            or restore didn't complete successfully.
        """
        log = self.testcase.log

        log.info('start onepass unconditional restore stub operation')
        try:
            if delete_original_path is True:
                for _item in paths:
                    self.client_machine.remove_directory(_item)

            job = self.restore_in_place(
                paths=paths,
                from_time=from_time,
                to_time=to_time,
                restoreDataInsteadOfStub=False,
                overwriteFiles=True,
                onePassRestore=True
            )

            log.info(
                "Started restore in place job with job id: " + str(job.job_id)
            )

            if not job.wait_for_completion():
                raise Exception(
                    "Failed to run restore in place job with error: "
                    + job.delay_reason
                )

            if not job.status.lower() == "completed":
                raise Exception(
                    "Job status is not Completed, job has status: "
                    + job.status
                )

            log.info("Successfully finished onepass in place restore stub job")
            return job
        except Exception as excp:
            log.error('Job error : ' + str(excp))
            raise Exception('Job error : ' + str(excp))

    def verify_restore_result(self, source_path=None, dest_path=None,
                              verify_acl=False):

        """this function will verify restore result

            Args:
                source_path  (str) original path of test data

                dest_path    (str)  restored data path

                verify_acl   (bool) True - will verify ACL
                                    False - will not verify ACL

                                    default: False
            Return:
                None

            Raises:
                Exception - Any error occurred while running restore
                            or restore didn't complete successfully.
        """
        log = self.testcase.log
        log.info('start to verify in place restore result')
        try:
            _client = self.client_machine
            if source_path is None:
                _source_path = self.subclient_props['subclient_content'][0]
            else:
                _source_path = source_path
            if dest_path is None:
                _dest_path = self.subclient_props['outofplace_restore_path']
            else:
                _dest_path = dest_path

            if ((_source_path == self.subclient_props['subclient_content'][0])
                    and self.org_hashcode is not None):
                _source_hash = self.org_hashcode
            else:
                _source_hash = _client.get_checksum_list(_source_path)

            _restore_hash = _client.get_checksum_list(_dest_path)
            _matched, _code = _client._compare_lists(
                _restore_hash,
                _source_hash
                )
            if _matched is False:
                raise Exception("At least one restored data content "
                                "does not match with the original")

            if verify_acl is False:
                _return_status = _matched
            else:
                _acl, _code = self.client_machine.compare_acl(
                    _source_path,
                    _dest_path
                    )
                _return_status = _acl & _matched

            if _return_status is True:
                log.info("restore data matches with original data," +
                         "pass restore verification")
                return _return_status
            else:
                log.info("restore data doesn't match with original data," +
                         "fail restore verification process ")
                raise Exception('fail to pass restore verification,' +
                                'raise exception here')

        except Exception as excp:
            log.error('Job error : %s' % str(excp))
            raise Exception('Job error : %s' % str(excp))

    def move_file_gxhsm(self, source_path, destination_path):
        """
        Moves file using gxhsm utility in windows.

        Args:
                    source_path   (str)   --  full path of the file to be moved(including file name).

                    destination_path    (str) -- full path of the destination where file to be moved.

                Returns:
                    None    -   if the file was moved successfully

                Raises:
                    Exception:
                        if no file exists at the given path

                        if failed to move the file
        """
        installation_path = self.testcase.client_machine.client_object.install_directory
        if not installation_path:
            raise Exception("Failed to get installation path of client")
        cmd = "\""+installation_path+"\\Base\""

        output = self.testcase.client_machine.execute_command(command="cd "+cmd+";"+".\\GXHSMUtility -m {0} {1}"
                                                              .format(source_path, destination_path))
        if output.exit_code != 0:
            raise Exception("Move stub failed.")
        else:
            self.log.info("Move stub successful.")
        self.log.info(output.formatted_output)

    def restub_checks(self, jobs, total_stubbed, flag=True):
        """
            Check if re-stubbing feature is working as expected

        Args:
                    jobs   (obj)   --  the job object which has details of run jobs

                    total_stubbed    (int) -- number of files expected to be stubbed

                    flag    (bool)  -- if re-stub should happen without backing up the data

                Returns:
                    None    -   if the feature check is successful

                Raises:
                    Exception:
                        if backup size or number of stubbed files count is not as pe feature expectation
        """
        if flag:
            if total_stubbed > 100 and int(jobs[0].details['jobDetail']['detailInfo']['sizeOfApplication']) > 20480:
                self.log.info("The recalled data is not re-backed up")
            elif int(jobs[0].details['jobDetail']['detailInfo']['sizeOfApplication']) > 2048 and total_stubbed < 100:
                self.log.info("Please check for the application size of job{}".format(jobs[0].job_id))
                raise Exception("Data got re-backed up")
            else:
                self.log.info("The recalled data is not re-backed up")

            if int(jobs[0].details['jobDetail']['detailInfo']["stubbedFiles"]) != total_stubbed:
                self.log.info("The files stubbed is not matching the previous stubbed count")
                raise Exception("Not all files got stubbed as expected")
            else:
                self.log.info("All the recalled files got stubbed")
        else:
            job_one = jobs[0]
            job_two = jobs[1]

            if int(job_one.details['jobDetail']['detailInfo']['sizeOfApplication']) == 0:
                self.log.info("Please check job{}, as no data got backed up".format(job_one.job_id))
                raise Exception("Data did not get backed up")
            else:
                self.log.info("The recalled data is backed up as expected")

            job_stubbed = int(job_one.details['jobDetail']['detailInfo']["stubbedFiles"])
            job_stubbed = job_stubbed + int(job_two.details['jobDetail']['detailInfo']["stubbedFiles"])

            if job_stubbed != total_stubbed:
                self.log.info("The files stubbed is not matching the previous stubbed count")
                raise Exception("Not all files got stubbed as expected")
            else:
                self.log.info("All the recalled files got stubbed")
