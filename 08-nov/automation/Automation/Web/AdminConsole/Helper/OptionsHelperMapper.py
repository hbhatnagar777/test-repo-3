from VirtualServer.VSAUtils import OptionsHelper, VirtualServerConstants


class OptionsMapping:
    """ Options Mapping for AdminConsoleVirtualServer and OptionsHelper. """

    def __init__(self, admin_console_obj):
        """
        A class which maps attributes in AdminConsoleVirtualServer to OptionsHelper
            for performing backup and restore validations in the command line way.

        Args:
            admin_console_obj   (object)    --  An AdminConsoleVirtualServer Object.
        """
        self.log = admin_console_obj.log
        self.admin_console_obj = admin_console_obj

    def copy_attributes(self, source_obj, destination_obj):
        """
        Copies values of similarly-named attributes of a source object
            to a destination object.

        Args:
            source_obj      (object)    --  A source object of any type.

            destination_obj (object)    --  A destination object of any type.
        """
        for attr in destination_obj.__dict__.keys():
            value = getattr(source_obj, attr.strip('_'), None)
            if value is not None:
                setattr(destination_obj, attr, value)


class BackupOptionsMapping(OptionsMapping):
    """ BackupOptions Mapping for AdminConsoleVirtualServer and BackupOptions. """

    def __init__(self, admin_console_obj):
        """
        A class to map backup options from AdminConsoleVirtualServer to BackupOptions
            and to perform backup validation for AdminConsole.

        Args:
            admin_console_obj   (object)    --  An AdminConsoleVirtualServer Object.
        """
        super(BackupOptionsMapping, self).__init__(admin_console_obj)
        self.backup_options = None

    def map_attributes(self, obj, dest):
        """
        Creates new attributes in AdminConsoleVirtualServer object with the
            exact names in BackupOptions that need to be mapped.
        """
        for key, value in VirtualServerConstants.backup_options_mapping.items():
            setattr(dest, key, getattr(obj, value, None))

    def _create_backup_options_object(self):
        """ Creates a BackupOptions object. """
        self.backup_options = OptionsHelper.BackupOptions(self.admin_console_obj.auto_vsa_subclient)
        self.copy_attributes(self.admin_console_obj, self.backup_options)
        self.map_attributes(self.admin_console_obj, self.backup_options)

    def validate_backup(self, **kwargs):
        """
        Run commandline backup validation.

        Raises:
            Exception:
               If backup validation does not complete successfully.
        """
        try:
            self._create_backup_options_object()
            self.admin_console_obj.auto_vsa_subclient.backup_option = self.backup_options
            self.admin_console_obj.auto_vsa_subclient.backup_job = self.admin_console_obj.backup_job_obj
            if self.backup_options._backup_method.lower() == "snap":
                self.admin_console_obj.auto_vsa_subclient.backupcopy_job = self.admin_console_obj.backupcopy_job
            self.admin_console_obj.auto_vsa_subclient. \
                post_backup_validation(validate_workload=self.admin_console_obj.validate_workload,
                                       skip_snapshot_validation=self.admin_console_obj.skip_snapshot_validation,
                                       validate_cbt=self.admin_console_obj.validate_cbt,
                                       vm_list=kwargs.get('vm_list', None),
                                       disk_filters=kwargs.get('vm_group_disk_filters', None))

        except Exception as exp:
            self.log.exception("Exception while validating backup: %s", str(exp))
            raise exp


class RestoreOptionsMapping(OptionsMapping):
    """ RestoreOptions Mapping for AdminConsoleVirtualServer and RestoreOptions. """

    def __init__(self, admin_console_obj):
        """
        A class to map restore options from AdminConsoleVirtualServer to RestoreOptions
            and to perform restore validation for AdminConsole.

        Args:
            admin_console_obj   (object)    --  An AdminConsoleVirtualServer Object.
        """
        super(RestoreOptionsMapping, self).__init__(admin_console_obj)
        self.options = None

    def add_and_copy_missing_vm_restore_options(self, source_obj, dest_obj):
        """
        Adds any hypervisor specific restore option missing in dest_obj(FullVMRestoreOptions) and
        copies value from source_obj(AdminConsoleVirtualServer)

        Args:
            source_obj (object): AdminConsoleVirtualServer or its subclasses object.
            dest_obj (object): FullVMRestoreOptions object.

        """
        instance_type = self.admin_console_obj.restore_destination_client.instance_type
        for key, value in VirtualServerConstants.get_restore_option_mapping(instance_type).items():
            source_value = getattr(source_obj, value, None)
            if not hasattr(dest_obj, key):
                setattr(dest_obj, key, None)
            if source_value is not None:
                setattr(dest_obj, key, source_value)


    def map_attributes(self, obj):
        """
        Creates new attributes in AdminConsoleVirtualServer object with the
            exact names in RestoreOptions that need to be mapped.

        Args:
            obj         (Object)        -- An object of AdminConsoleVirtualServer or one of its subclasses.
        """
        for key, value in VirtualServerConstants.get_restore_option_mapping(obj._instance).items():
            setattr(obj, key, getattr(obj, value, None))

    def _create_options_object(self, options, method, **kwargs):
        """
        Instantiates subclasses of RestoreOptions depending on the restore method used.

        Args:
            options     (dict)          -- A dictionary with restore options.

            method      (str)    -- Name of the restore method used.
        """
        if method == "Full VM":
            self.options = OptionsHelper.FullVMRestoreOptions(
                self.admin_console_obj.auto_vsa_subclient, self.admin_console_obj.testcase_obj,
                populate_restore_inputs=False)
        elif method == "Live Sync":
            self.options = OptionsHelper.LiveSyncOptions(
                self.admin_console_obj.auto_vsa_subclient, self.admin_console_obj.testcase_obj)
        elif method == "Conversion":
            self.options = OptionsHelper.FullVMRestoreOptions(
                kwargs["auto_subclient"], self.admin_console_obj.testcase_obj)

        # The restore_options are all copied to admin_console_obj.
        if options:
            target_obj = self.admin_console_obj.restore_obj if method == "Conversion" else self.admin_console_obj
            for key in options:
                if key == 'storage_policy':
                    setattr(target_obj, key, options[key].name)
                else:
                    setattr(target_obj, key, options[key])

        # All the destination attributes are added in admin_console_obj,
        # which are derived by already present attributes there.
        if method == "Conversion":
            self.map_attributes(self.admin_console_obj.restore_obj)
        else:
            self.map_attributes(self.admin_console_obj)

        # All the destination attributes that were added in admin_console_obj above,
        # are now copied to the restore options object and finish populating it.
        if method == "Conversion":
            self.add_and_copy_missing_vm_restore_options(self.admin_console_obj.restore_obj, self.options)
            self.copy_attributes(self.admin_console_obj.restore_obj, self.options)
            self.options.source_client_hypervisor = self.admin_console_obj.hvobj
        else:
            self.add_and_copy_missing_vm_restore_options(self.admin_console_obj, self.options)
            self.copy_attributes(self.admin_console_obj, self.options)

    def validate_restore(self, source_vm, restore_vm, options):
        """
        Run commandline restore validation.

        Args:
            source_vm           (str)    --  Name of the source VM.

            restore_vm          (str)    --  Name of the restored VM.

            options     (dict)          --  A dictionary containing restore options.

        Raises:
            Exception:
               If restore validation does not complete successfully.
        """
        self._create_options_object(options, "Full VM")
        self.admin_console_obj.auto_vsa_subclient.vm_restore_validation(
            source_vm, restore_vm, self.options)

    def validate_live_sync(self, live_sync_name, options):
        """
        Run commandline live sync validation.

        Args:
            live_sync_name      (str)    -- Name of the Schedule or Replication Group.

            options             (Object)        -- A LiveSyncOptions object for replication options used.
        """
        self._create_options_object(options, "Live Sync")
        self.admin_console_obj.auto_vsa_subclient.validate_live_sync(
            live_sync_name, live_sync_options=self.options)

    def validate_conversion_restore(self, source_vm, restore_vm, options=None):
        """
        Run commandline restore validation for conversion retores.

        Args:
            source_vm           (str)    --  Name of the source VM.

            restore_vm          (str)    --  Name of the restored VM.

            options     (dict)          --  A dictionary containing restore options.
        """
        self._create_options_object(options=options, method="Conversion",
                                    auto_subclient=self.admin_console_obj.restore_obj.auto_vsa_subclient)
        self.admin_console_obj.auto_vsa_subclient.vm_restore_validation(
            source_vm, restore_vm, self.options)
