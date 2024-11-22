"""
Main file for all the Vsa testcase utilities of Virtual Sever

classes defined:
    VSATestCaseUtils   - Class for vsa test case

"""

import pprint
import time
# import traceback
import threading
import concurrent.futures
from VirtualServer.VSAUtils.AutoScaleUtils import AutoScaleValidation
from .VirtualServerHelper import AutoVSAVSClient, AutoVSAVSInstance
from .VirtualServerHelper import VirtualServerUtils as VS_Utils
from . VirtualServerConstants import hypervisor_type


class VSATestCaseUtils(object):
    """
    Class for vsa test case

    Methods:
        assign_sub_client()             -   Assign subclient object

        _initialize_options_helper()    -   Creation of optionhelper object

        _is_not_used()                  -   Skipping if class object is not used

        _update_options()               -   Update optionshelper object's values

        _log_error()                    -   Generate and log error messages

        run_backup()                    -   Running backup

        run_guest_file_restore()        -   Running guest file restores

        run_disk_restore()              -   Running disk restore

        run_attach_disk_restore()       -   Running attach disk restore

        run_virtual_machine_restore()   -   Running Full vm restore

    """

    def __init__(self, testcase, product, feature, **kwargs):
        """
        Initializes Testcase objects

        Args:
            testcase                (object):       testcase object

            product                 (str):   testcase's product

            feature                 (str):   testcase's feature

            **kwargs                         : Arbitrary keyword arguments
        """
        testcase.product = product
        testcase.feature = feature
        testcase.show_to_user = True
        testcase.ind_status = True
        testcase.failure_msg = ''
        testcase.tcinputs = {}
        for key, value in kwargs.items():
            exec('testcase.{} = value'.format(key))
        self.backup_options, self.attach_disk_restore_options, \
        self.disk_restore_options, self.file_restore_options, \
        self.vm_restore_options, self.live_sync_options, \
        self.sub_client_obj, self.log = (None for _ in range(8))

    def initialize(self, tc_obj):
        """
        Initialize subclient
        Args:
            tc_obj                      (object):       Testcase object

        Returns:
            auto_subclient              (object):       Subclient object

        """
        auto_subclient = VS_Utils.subclient_initialize(tc_obj)
        if not auto_subclient:
            exp = 'Check if the input JSON is correct and subclient has VMS'
            self._log_error(tc_obj, 'Subclient initializing', exp)
            raise exp
        else:
            self.assign_sub_client(auto_subclient)
            return auto_subclient

    def assign_sub_client(self, sub_client):
        """
        Assigning subclient object

        Args:
            sub_client                  (object):       Subclient object

        """
        self.sub_client_obj = sub_client
        self.log = sub_client.log

    def _initialize_options_helper(self, option, tc_obj=None):
        """
        Initializing options helper

        Args:
            option                  (str):       Name of option helper to be initialized

            tc_obj                  (object):           Testcase object

        Returns:
            option_helper_object     (object)

        """
        # noinspection PyUnresolvedReferences
        from . import OptionsHelper
        self.log.debug('Creating {}'.format(option))
        if tc_obj:
            return eval('OptionsHelper.{}(self.sub_client_obj, tc_obj)'.format(option))
        return eval('OptionsHelper.{}(self.sub_client_obj)'.format(option))

    def _is_not_used(self):
        """
        Skipping if class object is not used
        """
        pass

    def _update_options(self, options_helper_obj, **kwargs):
        """
        Updating/adding values for option helper

        Args:
            options_helper_obj              (object):       Optionshelper object

            **kwargs                        (dict):         Dictionary for optional variables

        """
        self._is_not_used()
        self.log.debug("Setting/Updating info for {}".format(type(options_helper_obj)))
        for key, value in kwargs.items():
            self.log.debug('Setting {}={}'.format(key, value))
            exec('options_helper_obj.{} = value'.format(key))

    def _log_error(self, tc_obj, error_msg, exception):
        """
        Logging errors

        Args:
            tc_obj                  (object):       testcase object

            error_msg               (str):   Error String

            exception               (exception):          Exception message

        """
        _error = 'Failure during/before {}: {}'. \
            format(error_msg, exception)
        tc_obj.log.exception(_error)
        tc_obj.ind_status = False
        tc_obj.failure_msg += '<br>' + _error + '<br>'
        # self.log.exception(traceback.print_exc())

    def update_pre_backup_config_checks(self, **kwargs):
        """
        Makes the changes on the bpre config backup checks
        Args:
            **kwargs                         : Arbitrary keyword arguments Properties as of
                                                BackupOptions in OptionsHelper

        """
        for checks in kwargs:
            if checks.startswith('skip_'):
                if checks[5:] in self.backup_options.pre_backup_config_checks:
                    self.backup_options.pre_backup_config_checks[checks[5:]]['validate'] = False

    def run_backup(self, tc_obj, **kwargs):
        """
        Run backup

        Args:
            tc_obj                  (object):       Testcase object

            **kwargs                         : Arbitrary keyword arguments Properties as of
                                                BackupOptions in OptionsHelper

        """
        try:
            VS_Utils.decorative_log('Backup')
            if not self.backup_options:
                self.backup_options = self._initialize_options_helper('BackupOptions')
            self._update_options(self.backup_options, **kwargs)
            if any(key.startswith('skip_') for key in kwargs):
                self.update_pre_backup_config_checks(**kwargs)
            if not kwargs.get('msg'):
                if not self.backup_options.backup_method == 'SNAP':
                    kwargs['msg'] = '{} Streaming Backup'.format(self.backup_options.backup_type)
                else:
                    kwargs['msg'] = '{} Snap Backup and Backup Copy'.format(
                        self.backup_options.backup_type)
            if kwargs.get('collect_file_details'):
                if not self.backup_options.collect_metadata:
                    raise Exception('Collect file details is not enabled')
            else:
                if self.backup_options.collect_metadata:
                    raise Exception('Collect file details is enabled')
            testdata_size = kwargs.get('testdata_size')
            if testdata_size:
                self.backup_options.advance_options["testdata_size"] = testdata_size
            self.log.info("---_____Backup Options_____---")
            self.log.debug(pprint.pformat(vars(self.backup_options)))
            self.sub_client_obj.backup(self.backup_options, **kwargs)
        except Exception as exp:
            self._log_error(tc_obj, kwargs.get('msg', 'Backup'), exp)
            raise exp
        finally:
            pass

    def live_mount_obj(self, vmpolicy, auto_commcell):

        """
        Creates Hypervisor Helper object for Virtual Lab/Live Mount validations

        vmpolicy (obj)    :  virtual machine policy object

        auto_commcell  (obj) : commcell object

        Returns:

             hypervisor helper object
        """
        virtualization_client_name = (
            vmpolicy.properties()['dataCenter']['instanceEntity']['clientName'])
        virtualization_client = auto_commcell.commcell.clients.get(
            virtualization_client_name)
        virtualization_agent = virtualization_client.agents.get('Virtual Server')
        instance_keys = next(iter(virtualization_agent.instances._instances))
        source_instance = virtualization_agent.instances.get(instance_keys)
        auto_virtualization_client = AutoVSAVSClient(
            auto_commcell, virtualization_client)
        auto_virtualization_instance = AutoVSAVSInstance(
            auto_client=auto_virtualization_client,
            agent=virtualization_agent,
            instance=source_instance)

        VS_Utils.decorative_log("Creating HypervisorHelper object.")
        hvobj = auto_virtualization_instance.hvobj

        return hvobj

    def run_guest_file_restore(self, tc_obj, **kwargs):
        """
        Run guest file restore

        Args:
            tc_obj                  (object):       Testcase object

           **kwargs                         : Arbitrary keyword arguments Properties as of
                                                FileLevelRestoreOptions in OptionsHelper

        """
        try:
            VS_Utils.decorative_log('Guest file restores')
            if not self.file_restore_options:
                self.file_restore_options = self. \
                    _initialize_options_helper('FileLevelRestoreOptions')
                VS_Utils.set_inputs(tc_obj.tcinputs, self.file_restore_options)
            self._update_options(self.file_restore_options, **kwargs)
            if not kwargs.get('msg'):
                if self.file_restore_options.browse_from_snap:
                    _msg = 'Guest file restores from Snap Backup from '
                elif self.file_restore_options.browse_from_backup_copy:
                    _msg = 'Guest file restores from Backup copy from '
                else:
                    _msg = 'Guest file restores from '
                kwargs['msg'] = _msg + self.backup_options.backup_type
            self.log.info("---_____File Restores Options_____---")
            self.log.debug(pprint.pformat(vars(self.file_restore_options)))
            if not kwargs.get('skip_restore'):
                if kwargs.get('child_level'):
                    for vm in self.sub_client_obj.vm_list:
                        self.sub_client_obj.guest_file_restore(self.file_restore_options,
                                                               discovered_client=vm, **kwargs)
                    del self.file_restore_options.child_level
                else:
                    self.sub_client_obj.guest_file_restore(self.file_restore_options, **kwargs)
            else:
                self.log.info("---_____Skipping Restore_____---")
                del self.file_restore_options.skip_restore
        except Exception as exp:
            self._log_error(tc_obj, kwargs.get('msg', 'Guest File level Restore'), exp)
            if tc_obj.instance.instance_name in (hypervisor_type.VIRTUAL_CENTER.value.lower(),
                                                 hypervisor_type.AMAZON_AWS.value.lower()) and kwargs.get(
                    'browse_from_snap',
                    False) is True:
                self.log.info("Sleeping for 12 minutes for snap to get unmounted")
                time.sleep(720)
        finally:
            pass

    def run_disk_restore(self, tc_obj, **kwargs):
        """
        Run disk restore

        Args:
            tc_obj                  (object):       Testcase object

            **kwargs                         : Arbitrary keyword arguments Properties as of
                                                DiskRestoreOptions in OptionsHelper

        """
        try:
            VS_Utils.decorative_log("Disk Restores")
            if not self.disk_restore_options:
                self.disk_restore_options = self._initialize_options_helper('DiskRestoreOptions')
                VS_Utils.set_inputs(tc_obj.tcinputs, self.disk_restore_options)
            self._update_options(self.disk_restore_options, **kwargs)
            if not kwargs.get('msg'):
                if self.disk_restore_options.browse_from_snap:
                    kwargs['msg'] = 'Disk restore from Snap'
                else:
                    kwargs['msg'] = 'Disk restore from Streaming/Backup Copy'
            self.log.info("---_____Disk Restore Options_____---")
            self.log.debug(pprint.pformat(vars(self.disk_restore_options)))
            if kwargs.get('child_level'):
                for vm in self.sub_client_obj.vm_list:
                    self.sub_client_obj.disk_restore(self.disk_restore_options,
                                                     discovered_client=vm, **kwargs)
                del self.disk_restore_options.child_level
            else:
                self.sub_client_obj.disk_restore(self.disk_restore_options, **kwargs)
        except Exception as exp:
            self._log_error(tc_obj, kwargs.get('msg', 'Disk level restore'), exp)
        finally:
            pass

    def run_attach_disk_restore(self, tc_obj, **kwargs):
        """
        Run Attach disk restore

        Args:
            tc_obj                  (object):       Testcase object

            **kwargs                         : Arbitrary keyword arguments Properties as of
                                                AttachDiskRestoreOptions in OptionsHelper

        """
        try:
            VS_Utils.decorative_log("Attach disk restore")
            if not self.attach_disk_restore_options:
                self.attach_disk_restore_options = self. \
                    _initialize_options_helper('AttachDiskRestoreOptions', tc_obj)
                VS_Utils.set_inputs(tc_obj.tcinputs, self.attach_disk_restore_options)
            self._update_options(self.attach_disk_restore_options, **kwargs)
            if not kwargs.get('msg'):
                if self.attach_disk_restore_options.browse_from_snap:
                    kwargs['msg'] = 'Attach Disk restore from Snap'
                else:
                    kwargs['msg'] = 'Attach Disk restore from Streaming/Backup Copy'
            self.log.info("---_____Attach Disk Restore Options_____---")
            self.log.debug(pprint.pformat(vars(self.attach_disk_restore_options)))
            if kwargs.get('child_level'):
                for vm in self.sub_client_obj.vm_list:
                    self.sub_client_obj.attach_disk_restore(self.attach_disk_restore_options,
                                                            discovered_client=vm, **kwargs)
                del self.attach_disk_restore_options.child_level
            else:
                self.sub_client_obj.attach_disk_restore(self.attach_disk_restore_options, **kwargs)
        except Exception as exp:
            self._log_error(tc_obj, kwargs.get('msg', 'Attach disk level restore'), exp)
        finally:
            pass

    def run_virtual_machine_restore(self, tc_obj, **kwargs):
        """
        Run Full vm restore

        Args:
            tc_obj                  (object):       Testcase object

            **kwargs                         : Arbitrary keyword arguments Properties as of
                                                FullVMRestoreOptions in OptionsHelper

        """
        try:
            VS_Utils.decorative_log("Full vm restore")
            if not self.vm_restore_options:
                self.vm_restore_options = self. \
                    _initialize_options_helper('FullVMRestoreOptions', tc_obj)
                VS_Utils.set_inputs(tc_obj.tcinputs, self.vm_restore_options)
            self._update_options(self.vm_restore_options, **kwargs)
            if not kwargs.get('msg'):
                if self.vm_restore_options.in_place_overwrite:
                    kwargs['msg'] = 'Full vm inplace restore from {job_type}'. \
                        format(job_type='Snap' if self.vm_restore_options.browse_from_snap else
                    'Streaming/Backup Copy')
                else:
                    kwargs['msg'] = 'Full vm out of place restore from {job_type}'.format(
                        job_type="Snap" if self.vm_restore_options.browse_from_snap
                        else 'Streaming/Backup Copy')
            self.log.info("---_____VM Restore Options_____---")
            self.log.debug(pprint.pformat(vars(self.vm_restore_options)))
            if not kwargs.get('skip_restore'):
                if kwargs.get('child_level'):
                    for vm in self.sub_client_obj.vm_list:
                        try:
                            self.sub_client_obj.virtual_machine_restore(self.vm_restore_options,
                                                                    discovered_client=vm, **kwargs)
                        except Exception as exp:
                            self.log.exception("Exception in restoring vm {0} and exception is {1}".format(vm, exp))
                            raise exp
                    del self.vm_restore_options.child_level
                else:
                    self.sub_client_obj.virtual_machine_restore(self.vm_restore_options, **kwargs)
            else:
                self.log.info("---_____Skipping Restore_____---")
                del self.vm_restore_options.skip_restore
        except Exception as exp:
            self._log_error(tc_obj, kwargs.get('msg', 'Full Vm restore'), exp)
        finally:
            pass

    def run_multiple_backups(self, tc_obj, backups_to_run=None, **kwargs):
        """
        Run multiple vm backups

        Args:
            tc_obj                  (object):       Testcase object

            backups_to_run           (list):        Backups to run

            **kwargs                         : Arbitrary keyword arguments
                                                Properties as of BackupOptions in OptionsHelper

        Returns:
            _backup_jobs            (list):       List of dict of objects for job option, backup job and time stamp
        """
        try:
            import copy
            if not backups_to_run:
                backups_to_run = ['FULL', 'INCREMENTAL']
            _backup_jobs = []
            _backup_count = 1
            kwargs['backup_type'] = backups_to_run[0]
            VS_Utils.decorative_log('Backup Count {}'.format(_backup_count))
            self.backup_options = self.run_backup(tc_obj, **kwargs)
            _backup_jobs.append({
                'backup_option': copy.copy(self.backup_options),
                'backup_job': copy.copy(self.sub_client_obj.backup_job),
                'time_stamp': self.sub_client_obj.timestamp
            })
            self.backup_options.modify_data = True
            self.backup_options.delete_data = True
            self.backup_options.cleanup_testdata_before_backup = False
            for _backup_type in backups_to_run[1:]:
                _backup_count += 1
                VS_Utils.decorative_log('Backup Count {}'.format(_backup_count))
                self.backup_options.backup_type = _backup_type
                self.backup_options.testdata_path = None
                self.log.info(pprint.pformat(vars(self.backup_options)))
                self.sub_client_obj.backup(self.backup_options, **kwargs)
                _backup_jobs.append({
                    'backup_option': copy.copy(self.backup_options),
                    'backup_job': copy.copy(self.sub_client_obj.backup_job),
                    'time_stamp': self.sub_client_obj.timestamp
                })
            return _backup_jobs
        except Exception as exp:
            self._log_error(tc_obj, kwargs.get('msg', 'Multiple backups'), exp)
            raise exp
        finally:
            pass

    def run_multiple_guest_files_restores(self, tc_obj, backup_jobs, **kwargs):
        """
        Run multiple guest files restores

        Args:
            tc_obj                  (object):       Testcase object

            backup_jobs             (list):         List of dict of objects for job option, backup job and time stamp
                                                    _backup_jobs.append({
                                                            'backup_option': BackupOptions object,
                                                            'backup_job': Backup job Object,
                                                            'time_stamp': Timestamp for data verification
                                                            }

            **kwargs                      :         Arbitrary keyword arguments Properties as of
                                                        FileLevelRestoreOptions in OptionsHelper

        """
        try:
            kwargs['restore_type'] = 'guest'
            kwargs['skip_restore'] = True
            self.run_guest_file_restore(tc_obj, **kwargs)
            del kwargs['skip_restore']
            self._run_multiple_restores(tc_obj, backup_jobs, **kwargs)
        except Exception as exp:
            self._log_error(tc_obj, kwargs.get('msg', 'Multiple File level '), exp)
        finally:
            pass

    def run_multiple_virtual_machine_restore(self, tc_obj, backup_jobs, **kwargs):
        """
        Run multiple vm restores

        Args:
            tc_obj                  (object):       Testcase object

            backup_jobs             (list):         List of dict of objects for job option, backup job and time stamp
                                                    _backup_jobs.append({
                                                            'backup_option': BackupOptions object,
                                                            'backup_job': Backup job Object,
                                                            'time_stamp': Timestamp for data verification
                                                            }

            **kwargs                      :         Arbitrary keyword arguments Properties as of
                                                        FullVMRestoreOptions in OptionsHelper

        Returns:
            vm_restore_options            (object):       full vm restore object
        """
        try:
            kwargs['restore_type'] = 'virtual machine'
            kwargs['skip_restore'] = True
            self.run_virtual_machine_restore(tc_obj, **kwargs)
            del kwargs['skip_restore']
            self._run_multiple_restores(tc_obj, backup_jobs, **kwargs)
            return self.vm_restore_options
        except Exception as exp:
            self._log_error(tc_obj, kwargs.get('msg', 'Multiple Full VM Restore '), exp)
        finally:
            pass

    def _run_multiple_restores(self, tc_obj, backup_jobs, **kwargs):
        """
        Run multiple restores

        Args:
            tc_obj                  (object):       Testcase object

            backup_jobs             (list):         List of dict of objects for job option, backup job and time stamp
                                                    _backup_jobs.append({
                                                            'backup_option': BackupOptions object,
                                                            'backup_job': Backup job Object,
                                                            'time_stamp': Timestamp for data verification
                                                            }

            **kwargs                      :         Arbitrary keyword arguments Properties as of
                                                        Restore ype selected  in OptionsHelper
        """
        try:
            from AutomationUtils.machine import Machine
            import socket
            _controller = Machine(socket.gethostbyname_ex(socket.gethostname())[2][0])
            _count = 0

            def multiple_restores(_jobs):
                VS_Utils.decorative_log(
                    "{} from Job {}".format(kwargs.get('restore_type', 'Restore'),
                                            _jobs['backup_job'].job_id))
                self.sub_client_obj.timestamp = _jobs['time_stamp']
                self.sub_client_obj.testdata_path = _controller.os_sep.join(
                    self.sub_client_obj.testdata_path.split(_controller.os_sep)[:-1] + [
                        _jobs['time_stamp']])
                self.sub_client_obj.backup_folder_name = _jobs['backup_option'].backup_type
                if 'guest' in kwargs.get('restore_type'):
                    kwargs['to_date'] = _jobs['backup_job'].end_timestamp
                    kwargs['from_date'] = _jobs['backup_job'].start_timestamp
                    self.run_guest_file_restore(tc_obj, **kwargs)
                elif 'virtual machine' in kwargs.get('restore_type'):
                    kwargs['_end_time'] = _jobs['backup_job'].end_time
                    self.run_virtual_machine_restore(tc_obj, **kwargs)
                else:
                    raise Exception("Type of restore is not mentioned")

            if kwargs.get('run_type') == 'parallel':
                threads = []
                for _jobs in backup_jobs:
                    browse_thread = threading.Thread(target=multiple_restores, args=(_jobs,))
                    threads.append(browse_thread)
                    time.sleep(10)
                    _count += 1
                    VS_Utils.decorative_log("restore count: {}".format(_count))
                    browse_thread.start()
                for index, thread in enumerate(threads):
                    time.sleep(10)
                    thread.join()

            else:
                for _jobs in backup_jobs:
                    _count += 1
                    VS_Utils.decorative_log("restore count: {}".format(_count))
                    multiple_restores(_jobs)
        except Exception as exp:
            self._log_error(tc_obj, 'Issue during ' + kwargs.get('restore_type', 'Restore'), exp)
        finally:
            pass

    def run_all_restores_in_parallel(self, tc_obj, restore_types=None, **kwargs):
        """
        Running all restores in parallel
        Args:
            tc_obj                          (object):   testcase object

            restore_types                   (list):     Types of restores to be performed

            **kwargs                            :   Arbitrary keyword arguments Properties as of
                                                        Restore ype selected  in OptionsHelper

        Returns:

        """
        try:
            if not restore_types:
                restore_types = ['guest_file_restore', 'disk_restore', 'attach_disk_restore',
                                 'virtual_machine_restore']
            kwargs['is_part_of_thread'] = True
            max_workers = len(restore_types)
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                self.log.info("sleeping for 5 seconds before starting new thread")
                time.sleep(5)
                restores = {
                    executor.submit(self.threading_restores, tc_obj, rest_type, **kwargs): rest_type
                    for rest_type in restore_types}
            del restores
        except Exception as exp:
            self._log_error(tc_obj, 'Issue during Parallel Restore', exp)
        finally:
            pass

    def threading_restores(self, tc_obj, restore_type, **kwargs):
        """
        Creating Threads for restores
        Args:
            tc_obj                          (object):   testcase object

            restore_type                   (str):     Types of restore to be performed

            **kwargs                            :   Arbitrary keyword arguments Properties as of
                                                        Restore ype selected  in OptionsHelper
        Returns:

        """
        self._is_not_used()
        threading.current_thread().name = restore_type
        self.log.info(f'Current Parent thread name: {threading.current_thread().name}')
        restore_type = 'run_' + restore_type
        eval('self.{}(tc_obj, **kwargs)'.format(restore_type))
        threading.current_thread()._is_stopped = True

    def run_auto_scale_validation(self, tc_obj, **kwargs):
        """
        Runs auto scale validation
        Args:
            tc_obj         (object):   testcase object
            **kwargs               :   Arbitrary keyword arguments Properties as of
                                       backup options

        """
        try:
            if not self.backup_options:
                self.backup_options = self._initialize_options_helper('BackupOptions')
            self._update_options(self.backup_options, **kwargs)
            auto_scale_utils_obj = AutoScaleValidation(self.sub_client_obj, **kwargs)
            auto_scale_utils_obj.start_backup_job(self.backup_options)
            job_monitor_thread = threading.Thread(target=auto_scale_utils_obj.monitor_job, kwargs={**kwargs})
            proxy_monitor_thread = threading.Thread(target=auto_scale_utils_obj._validate_proxy_status)
            job_monitor_thread.start()
            time.sleep(150)
            proxy_monitor_thread.start()
            job_monitor_thread.join()
            if auto_scale_utils_obj.job_monitor_error_string:
                raise Exception("Error in while submitting backup : {0}".format(
                    auto_scale_utils_obj.job_monitor_error_string))
            proxy_monitor_thread.join()
            if auto_scale_utils_obj.validator_error_string:
                raise Exception("Error while performing validation : {0}".format(
                    auto_scale_utils_obj.validator_error_string))

            auto_scale_utils_obj.post_backup_validation()
            if auto_scale_utils_obj.validator_error_string:
                raise Exception("Error while performing post backup validation : {0}".format(
                                auto_scale_utils_obj.validator_error_string))

        except Exception as exp:
            self._log_error(tc_obj, kwargs.get('msg', 'auto scale validation failed'), exp)
            raise exp
