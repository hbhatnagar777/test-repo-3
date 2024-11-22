# -*- coding: utf-8 -*-
# pylint: disable=W0703
# pylint: disable=abstract-method

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
File for performing operations on a machine/computer with IBMi Operating System.

This file consists of a class named: IBMiMachine, which can connect to the remote machine,
using SSH with KSH Shell.

The instance of this class can be used to perform various operations on a machine, like,

    #.  Generating test data
    #.  Get the list of items at the given path
    #.  Rename a File/Folder
    #.  Remove an existing Directory
    #.  Get the Size of a File/Folder
    #.  Get the information about the items on the given path

IBMiMachine
===========

    __init__()                      --  initialize object of the class

    initialize_param_from_testcase()--  Initialize the class parameters from testcase inputs

    reset_file_counts()             --  Reset all the file counters, so that only empty libraries
                                        are created next.

    generate_test_data()            --  generates and adds random test data on the specified path

    get_items_list()                --  Gets the list of items at the given path

    get_test_data_info()            --  Gets information about the items on the given path

    compare_acl()                   --  Compares the acl of source path with destination path
                                        and checks if they are same

    compare_xattr()                 --  Compares the xattr of source path with destination path
                                        and checks if they are same

    create_one_object()             --  Creates one data area object in the library provided.

    create_sourcePF()               --  Creates one source physical file with one member under
                                        the library.

    delete_file_object()            --  Delete file type object under the provided library.

    manage_usrprf()                 --  Create or delete the user profile object.

    manage_devopt()                 --  Create or delete DEVD object.

    manage_library()                --  Create or delete library object.

    object_existence()              --  Check the object existence on the disk and returns
                                        exception if object not found.

    is_object_exists                --  check object existence of the specific type in the desired library.

    populate_QDLS_data()            --  Populate a folder with objects.

    populate_lib_with_data()        --  Populate a library with objects.

    populate_ifs_data()				--	populates a directory on the client with files.

    path_to_lib()                   --  convert library path and returns name of the library

    lib_to_path()                   --  convert library name to IFS path and returns the library path

    halt_ssh_and_cv_services()      --  Stop Commvault services & SSH services on IBMi client for
                                            specific duration.

    run_ibmi_command()              --  run command on IBMi QSH command line

    manage_folder()                 --  create or delete folder in QDLS file system.

    create_savf()                   --  Create save file/s in a library with specific size.

    parse_log_file()                --  Parses the log file and returns all lines and strings
                                        matching the given regex

    apply_filter_and_exception()    --  Check if data path is part of filter

    reconnect()                     --  Reconnect the Pamariko session with the client.

    get_ibmi_version()              --  Gets the version and release of IBMi client.

Attributes
----------

    **os_flavour**                  --  The os_flavour of this class. Should be OS400

    **num_libraries**               --  The number of libraries created for this testcase

    **num_data_files**              --  The number of data files created for this testcase

    **num_savf_files**              --  The number of savf files created for this testcase

    **savf_file_size**              --  The size of the savf files created for this testcase

    **num_empty_files**             --  The number of empty files created for this testcase

    **num_members**                 --  The number of members per file created for this testcase

    **num_deletes**                 --  The number of files deleted during incremental

    **num_attribute_changes**       --  The number of files whose attribute is changed.

    **num_data_areas**              --  The number of data area objects that area created.

    **filter_list**                 --  The filter list for this testcase.

"""

from fnmatch import fnmatch
from .constants import IBMI_ADD_DATA
from .constants import IBMI_GET_DATA
from .unix_machine import UnixMachine


class IBMiMachine(UnixMachine):
    """Class for performing operations on a IBMi OS remote client."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self, machine_name, commcell_object=None, username=None, password=None):
        """
        Initializes instance of the IBMiMachine class.

            Args:
                machine_name    (str)       : name/ip address of the client to connect to.
                   default:None

                commcell_object (object)    : instance of the Commcell class from CVPySDK
                   default:None

                username        (str)       : username for the client to connect to
                   default:None

                password        (str)       : password for the above specified user
                   default:None
       """
        super(IBMiMachine, self).__init__(machine_name, commcell_object, username, password)
        assert self.os_flavour == 'OS400', "IBMi machine class used for non AS400 device"
        # Default values. Testcase specific values are added in initialize_param_from_testcase
        self._num_libraries = 2
        self._num_data_files = 0
        self._num_savf_files = 0
        self._num_empty_files = 5
        self._num_members = 3
        self._num_deletes = 0
        self._num_attribute_changes = 0
        self._size_of_savf_file = 5000
        self._num_data_areas = 1
        self._filter_list = list()

    def reset_file_counts(self):
        """
        Reset all the file counters, so that only empty libraries are created next.

        Returns:
            None
        """
        self.num_data_files = 0
        self.num_savf_files = 0
        self.num_empty_files = 0
        self.num_members = 0
        self.num_deletes = 0
        self.num_attribute_changes = 0
        self._size_of_savf_file = 0
        self.num_data_areas = 0

    @property
    def num_libraries(self):
        """Returns the number of libraries that are generated for this test"""
        return self._num_libraries

    @num_libraries.setter
    def num_libraries(self, value):
        """Sets the number of libraries to be generated on the client"""
        self._num_libraries = value

    @property
    def filter_list(self):
        """Returns the filter list for this test"""
        return self._filter_list

    @filter_list.setter
    def filter_list(self, value):
        """Sets the filter list on the client"""
        self._filter_list = value

    @property
    def num_data_files(self):
        """Returns the number of data files that are generated for this test"""
        return self._num_data_files

    @num_data_files.setter
    def num_data_files(self, value):
        """Sets the number of data files to be generated on the client"""
        self._num_data_files = value

    @property
    def num_savf_files(self):
        """Returns the number of savf files that are generated for this test"""
        return self._num_savf_files

    @num_savf_files.setter
    def num_savf_files(self, value):
        """Sets the number of savf files to be generated on the client"""
        self._num_savf_files = value

    @property
    def savf_file_size(self):
        """Returns the size of save files used for commands"""
        return self._size_of_savf_file

    @savf_file_size.setter
    def savf_file_size(self, size_of_file):
        """
        Sets the size of save file to be used by commands

        Args:
            size_of_file    (int)   :   Size of the savf file to be created

        Returns:
            None
        """
        self._size_of_savf_file = size_of_file

    @property
    def num_empty_files(self):
        """Returns the number of empty files that are generated for this test"""
        return self._num_empty_files

    @num_empty_files.setter
    def num_empty_files(self, value):
        """Sets the number of empty files to be generated on the client"""
        self._num_empty_files = value

    @property
    def num_members(self):
        """Returns the number of members in each file that are generated for this test"""
        return self._num_members

    @num_members.setter
    def num_members(self, value):
        """Sets the number of members in each file to be generated on the client"""
        self._num_members = value

    @property
    def num_deletes(self):
        """Returns the number of objects deleted for for this test"""
        return self._num_deletes

    @num_deletes.setter
    def num_deletes(self, value):
        """Sets the number of libraries to be deleted on the client"""
        self._num_deletes = value

    @property
    def num_attribute_changes(self):
        """Returns the number of attribute changes for this test"""
        return self._num_attribute_changes

    @num_attribute_changes.setter
    def num_attribute_changes(self, value):
        """Sets the number of libraries for which attribute will change"""
        self._num_attribute_changes = value

    @property
    def num_data_areas(self):
        """Returns the number of data area objects for this test"""
        return self._num_data_areas

    @num_data_areas.setter
    def num_data_areas(self, value):
        """Sets the number of data area objects to be created"""
        self._num_data_areas = value

    def initialize_param_from_testcase(self, tcinputs):
        """
        Initialize the class parameters from testcase inputs

        Args:
            tcinputs    (dict)      :   Dictionary of testcase inputs

        Returns:
            None
        """
        # These start with default values during initialization in __init__. Once helper gets
        # created, it initializes these values depending on testcase configurations.
        self._num_libraries = int(tcinputs.get('NumLibraries', '1'))
        self._num_data_files = int(tcinputs.get('NumDataFiles', '2'))
        self._num_savf_files = int(tcinputs.get('NumSavfFiles', '1'))
        self._num_empty_files = int(tcinputs.get('NumEmptyFiles', '0'))
        self._num_members = int(tcinputs.get('NumMembers', '1'))
        self._num_deletes = int(tcinputs.get('NumDeletes', '0'))
        self._num_attribute_changes = int(tcinputs.get('NumAttributeChanges', '0'))
        self._size_of_savf_file = int(tcinputs.get('SizeOfSavfFile', '5000'))
        self._num_data_areas = int(tcinputs.get('NumDataAreas', '1'))

    def generate_test_data(self,
                           file_path,
                           **kwargs):
        """
        Generates and adds test data at the given path with the specified options.
        If path is IFS, calls the Unix implementation with appropriate parameters.

            Args:
                file_path               (str)       : directory where the data will be generated.

                **kwargs                (dict)      : Dictionary of optional arguments

                    options                         :

                            dirs        (int)       : number of directories in each level
                                default: 3

                            files       (int)       : number of files in each directory
                                default: 5

                            file_size   (int)       : Size of the files in KB
                                default: 20

                            levels      (int)       : number of levels to be created
                                default: 1

                            hlinks      (bool)      : whether to create hardlink files
                                default: True

                            slinks      (bool)      : whether to create symbolic link files
                                default: True

                            sparse      (bool)      : whether to create sparse files
                                default: True

                            sparse_hole_size (int)  : Size of the holes in sparse files in KB
                                default: 1024

                            long_path   (bool)      : whether to create long files
                                default: False

                            long_level  (int)       : length of the long path
                                default: 1500

                            acls        (bool)      : whether to create files with acls
                                default: False

                            unicode     (bool)      : whether to create unicode files
                                default: False

                            problematic (bool)      : whether to create problematic data
                                default: False

                            xattr       (bool)      : whether to create files with xattr
                                default: False

                            options     (str)       : to specify any other additional parameters.
                                default: ""

            Returns:
                bool : boolean value True is returned if no errors during data generation.

            Raises:
                Exception:
                    if any error occurred while generating the test data.
        """
        # pylint: disable=arguments-differ
        # This function uses kwargs while super class method uses arguments
        options = kwargs.get('options', "")
        if '/QSYS.LIB' not in file_path:
            # ACLs, unicode, long path and xattr are all going to be false for IBMi IFS data
            return super(IBMiMachine, self).generate_test_data(
                file_path=file_path,
                dirs=kwargs.get('dirs', 3),
                files=kwargs.get('files', 5),
                file_size=kwargs.get('file_size', 20),
                levels=kwargs.get('levels', 1),
                slinks=kwargs.get('slinks', True),
                hlinks=False,
                sparse=kwargs.get('sparse', True),
                sparse_hole_size=kwargs.get('sparse_hole_size', 1024),
                acls=False,
                unicode=False,
                xattr=False,
                long_path=False,
                long_level=kwargs.get('long_level', 1500),
                problematic=kwargs.get('problematic', False),
                options=options

            )

        file_path = file_path[10:].rstrip(".LIB")

        script_arguments = "-path \"{0}\"".format(file_path)
        script_arguments = "{0} {1}".format(script_arguments, options)
        script_arguments = ("{0} -numSavfFile {1} -numEmptyFile  {2} -numDataFile {3} "
                            " -numMember {4} -numAttribute {5} -sizeSavf {6} -numDataArea {7}"
                            .format(script_arguments,
                                    self._num_savf_files,
                                    self._num_empty_files,
                                    self._num_data_files,
                                    self._num_members,
                                    self._num_attribute_changes,
                                    self._size_of_savf_file,
                                    self._num_data_areas
                                    )
                            )

        output = self.execute(IBMI_ADD_DATA, script_arguments)
        if output.exit_code != 0:
            raise Exception(
                "Error occurred while generating test data {0} {1}".format(
                    str(output.output),
                    str(output.exception)
                )
            )
        return True

    def compare_acl(self, source_path, destination_path):
        """
        Compares the acl of source path with destination path
        and checks if they are same. IBMi doesn't support ACLs
        so this always returns True

             Args:
                source_path         (str)   : source path to compare

                destination_path    (str)   : destination path to compare

            Returns:
                bool, str : Returns True if acls of source and destination are same
                diff output between source and destination
            Raises:
                Exception:
                    if any error occurred while comparing the acl of paths.
        """
        return True, ""

    def compare_xattr(self, source_path, destination_path):
        """
        Compares the xattr of source path with destination path
        and checks if they are same. IBMi doesn't support XATTR, so this always
        returns True.

             Args:
                source_path         (str)   :  source path to compare

                destination_path    (str)   : destination path to compare

            Returns:
                bool, str : Returns True if xattr of source and destination are same
                diff output between source and destination

            Raises:
                Exception:
                    if any error occurred while comparing the xattr of paths.
        """
        return True, ""

    def get_test_data_info(self,
                           data_path,
                           name=False,
                           meta=False,
                           checksum=False,
                           **kwargs):
        """
        Gets information about the items on the given path based on the given options

            Args:
                data_path           (str)   : directory from where the data should be retrieved.

                name                (bool)  : whether to get name of all the files
                    default: False

                meta                (bool)  : whether to get meta data of all files
                    default: True

                checksum            (bool)  : whether to get OS checksum of all files
                    default: False

                **kwargs            (dict)  : Optional arguments

                    Options                 :

                        machinesort (bool)  : whether to sort the results on the machine
                            default: False

                        acls        (bool)  : whether to get acls of all files
                            default: False

                        xattr       (bool)  : whether to get xattr of all files
                            default: False

                        dirtime     (bool)  : whether to get time stamp of all directories
                            default: False

                        options     (str)   : to specify any other additional parameters.
                            default: ""

            Returns:
                list: list of output lines while executing the script.

            Raises:
                Exception:
                    if any error occurred while getting the data information.
        """
        # pylint: disable=arguments-differ
        # This function uses kwargs while super class method uses arguments
        options = kwargs.get('options', "")
        machinesort = kwargs.get('machinesort', False)

        script_arguments = "-path \"{0}\"".format(data_path)
        script_arguments = "{0}{1}".format(script_arguments,
                                           " -name yes" if name else " -name no")
        script_arguments = "{0}{1}".format(script_arguments,
                                           " -meta yes" if meta else " -meta no")
        script_arguments = "{0}{1}".format(script_arguments,
                                           " -sum yes" if checksum else " -sum no")
        script_arguments = "{0}{1}".format(script_arguments,
                                           " -sorted yes" if machinesort else " -sorted no")
        script_arguments = "{0}{1}".format(script_arguments, options)

        output = self.execute(IBMI_GET_DATA, script_arguments)
        if output.exit_code != 0:
            raise Exception(
                "Error occurred while getting the data information {0} {1}".format(
                    str(output.output),
                    str(output.exception)
                )
            )
        else:
            if self.filter_list:
                output_list = output.output.split('\n')
                while '' in output_list:
                    output_list.remove('')

                output_list[:] = [item for item in output_list
                                  if self.apply_filter_and_exception(item, data_path=data_path)]
                return '\n'.join(output_list)

            return output.output

    def get_items_list(self,
                       data_path,
                       sorted_output=True,
                       include_parents=False,
                       include_folders=False):
        """
        Gets the list of items at the given path.

            Args:
                data_path           (str)   : directory path to get the items list

                sorted_output       (bool)  : to specify whether the list should be sorted.
                    default: True

                include_parents     (bool)  : to specify whether parent paths should be include
                    default: False

                include_folders     (bool)  : to specify whether folder names should be included
                    default: False

            Returns:
                list : list of the items

            Raises:
                Exception:
                    if any error occurred while getting the items list.
        """

        if include_folders:
            find_cmd = r'find "{0}" '.format(data_path)
        else:
            find_cmd = r'find "{0}" ! -type d '.format(data_path)

        output = self.execute(find_cmd)

        if output.exit_code != 0:
            raise Exception(
                "Error occurred while getting items list from machine {0} {1}".format(
                    str(output.output),
                    str(output.exception)
                )
            )
        else:
            output_list = output.output.split('\n')

            if sorted_output:
                output_list.sort()
            while '' in output_list:
                output_list.remove('')

            return list(filter(self.apply_filter_and_exception,
                               output_list))

    def create_one_object(self, library_path, object_name='SINGLE'):
        """
        Creates one data area object in the library  provided.

            Args:
                library_path        (str)   : library path in which to create the object

                object_name         (str)   : name to use for the object
                    default: SINGLE

            Returns:
                None

            Raises:
                Exception:
                    if any error occurred while creating object.
        """
        library = self.path_to_lib(library_path)
        command = ("system 'CRTDTAARA DTAARA({0}/{1}) TYPE(*CHAR) "
                   "LEN(100) VALUE('TEST')'").format(library, object_name)

        output = self.execute(command)
        if output.exit_code != 0 and "{0} exists".format(object_name) not in str(output.exception):
            raise Exception(
                "Error occurred while creating single object {0} {1}".format(
                    str(output.output),
                    str(output.exception)
                )
            )

    def create_sourcepf(self, library='QSYS', object_name='SRCPF'):
        """
        Creates one source physical file with one member under the library.

            Args:
                library             (str)   : name of the library
                    default: QSYS

                object_name         (str)   : name to use for the object
                    default: SRCPF

            Returns:
                None

            Raises:
                Exception:
                    if any error occurred while creating object.
        """
        command = "system 'CRTSRCPF FILE({1}/{0}) MBR(*FILE)'".format(object_name, library)

        output = self.execute(command)
        if output.exit_code != 0 and "already exists" not in str(output.exception):
            raise Exception(
                "Error occurred while creating source PF object {0} {1}".format(
                    str(output.output),
                    str(output.exception)
                )
            )

    def delete_file_object(self, library='QSYS', object_name='SRCPF'):
        """
        delete file type object under the provided library.

            Args:
                library             (str)   : name of the library
                    default: QSYS
                object_name         (str)   : name to use for the object
                    default: SRCPF

            Returns:
                None

            Raises:
                Exception:
                    if any error occurred while creating object.
        """
        command = "system 'DLTF FILE({1}/{0})'".format(object_name, library)

        output = self.execute(command)
        if output.exit_code != 0 and "not found" not in str(output.exception):
            raise Exception(
                "Error occurred while deleting QHST object {0} {1}".format(
                    str(output.output),
                    str(output.exception)
                )
            )

    def manage_usrprf(self, operation='create', object_name='AUTOMATION'):
        """
        create or delete the user profile object.

            Args:
                operation           (str)   : create or delete of the user profile
                    default: create
                object_name         (str)   : name to use for the object
                    default: AUTOMATION

            Returns:
                None

            Raises:
                Exception:
                    if any error occurred while creating or deleting the user profile.
        """
        if operation == "create":
            command = "system 'QSYS/CRTUSRPRF USRPRF({0})'".format(object_name)
            output = self.execute(command)
            if output.exit_code != 0 and "already exists" not in str(output.exception):
                raise Exception(
                    "Error occurred while creating user profile:{2} object {0} {1}".format(
                        str(output.output),
                        str(output.exception),
                        object_name
                    )
                )
        elif operation == "delete":
            command = "system 'QSYS/DLTUSRPRF USRPRF({0})'".format(object_name)
            output = self.execute(command)
            if output.exit_code != 0 and "not found" not in str(output.exception):
                raise Exception(
                    "Error occurred while deleting user profile:{2} object {0} {1}".format(
                        str(output.output),
                        str(output.exception),
                        object_name
                    )
                )
        else:
            raise Exception("Invalid operation value {0}".format(operation))

    def manage_devopt(self, operation='create', object_name='AUTOMATION'):
        """
        create or delete DEVD object.

            Args:
                operation           (str)   : create or delete
                    default: create
                object_name         (str)   : name to use for the object
                    default: AUTOMATION

            Returns:
                None

            Raises:
                Exception:
                    if any error occurred while creating or deleting the devd object.
        """
        if operation == "create":
            command = "system 'QSYS/CRTDEVOPT DEVD({0}) RSRCNAME(*VRT) ONLINE(*NO)'".format(object_name)
            output = self.execute(command)
            if output.exit_code != 0 and "already exists" not in str(output.exception):
                raise Exception(
                    "Error occurred while creating DEVD object:{2} object {0} {1}".format(
                        str(output.output),
                        str(output.exception),
                        object_name
                    )
                )
        elif operation == 'delete':
            command = "system 'QSYS/DLTDEVD DEVD({0})'".format(object_name)
            output = self.execute(command)
            if output.exit_code != 0 and "not found" not in str(output.exception):
                raise Exception(
                    "Error occurred while deleting DEVD object:{2} object {0} {1}".format(
                        str(output.output),
                        str(output.exception),
                        object_name
                    )
                )
        else:
            raise Exception("Invalid operation value {0}".format(operation))

    def manage_library(self, operation='create', object_name='AUTOMATION'):
        """
        create or delete library object.

            Args:
                operation           (str)   : create or delete
                    default: create
                object_name         (str)   : name to use for the object
                    default: AUTOMATION

            Returns:
                None

            Raises:
                Exception:
                    if any error occurred while creating or deleting the devd object.
        """
        if operation == "create":
            if ('QSYS' in object_name or
                    'QTCP' in object_name or
                    'QHLP' in object_name or
                    object_name == 'QGPL'):
                raise Exception(" system Library cannot be created.")
            command = "system 'QSYS/CRTLIB LIB({0}) TYPE(*TEST)'".format(object_name)
            output = self.execute(command)
            if output.exit_code != 0 and "already exists" not in str(output.exception):
                raise Exception(
                    "Error occurred while creating DEVD object:{2} object {0} {1}".format(
                        str(output.output),
                        str(output.exception),
                        object_name
                    )
                )
        elif operation == 'delete':
            if ('QSYS' in object_name or
                    'QTCP' in object_name or
                    'QHLP' in object_name or
                    object_name == 'QGPL'):
                raise Exception(" system Library {0} cannot be deleted.".format(object_name))
            command = "system 'QSYS/DLTLIB LIB({0})'".format(object_name)
            output = self.execute(command)
            if output.exit_code != 0 and "CPF2110" not in str(output.exception):
                raise Exception(
                    "Error occurred while deleting LIB object:{2} object {0} {1}".format(
                        str(output.output),
                        str(output.exception),
                        object_name
                    )
                )
        else:
            raise Exception("Invalid operation value {0}".format(operation))

    def object_existence(self, library_name='QSYS', object_name='AUTOMATION', obj_type='*USRPRF'):
        """
        check object existence of the specific type in the desired library.

            Args:
                library_name        (str)   : name of the library
                    default: QSYS
                object_name         (str)   : name of the object
                    default: AUTOMATION
                obj_type            (str)   : type of the object

            Returns:
                None

            Raises:
                Exception:
                    if any error occurred when object does not exists.
        """
        command = "system 'CHKOBJ OBJ({0}/{1}) OBJTYPE({2})'".format(
            library_name,
            object_name,
            obj_type
        )
        output = self.execute(command)
        if output.exit_code != 0:
            raise Exception(
                "Error occurred while checking object existence {3}/{2}.  {0} {1}".format(
                    str(output.output),
                    str(output.exception),
                    object_name,
                    library_name
                )
            )

    def is_object_exists(self, library_name='QSYS', object_name='AUTOMATION', obj_type='*USRPRF'):
        """
        check object existence of the specific type in the desired library.

            Args:
                library_name        (str)   : name of the library
                    default: QSYS
                object_name         (str)   : name of the object
                    default: AUTOMATION
                obj_type            (str)   : type of the object

            Returns:
                True or False

            Raises:
                Exception:
                    if any error occurred when object does not exists.
        """
        command = "system 'CHKOBJ OBJ({0}/{1}) OBJTYPE({2})'".format(
            library_name,
            object_name,
            obj_type
        )
        output = self.execute(command)
        if output.exit_code == 0:
            return True
        elif output.exit_code != 0 and "not found" in str(output.exception):
            return False
        else:
            raise Exception(
                "Error occurred while checking object existence {3}/{2}.  {0} {1}".format(
                    str(output.output),
                    str(output.exception),
                    object_name,
                    library_name
                )
            )

    def populate_QDLS_data(self, folder_name='ABCD', tc_id='00000', count=1, delete=True):
        """
        Populate a folder with objects.

            Args:
                folder_name     (str)   : name of the library
                    default: ABCD
                tc_id           (str)   : test case ID.
                    default: '00000'
                count           (int)   : number of objects to be created

                delete          (bool)  : delete before populating the data

            Returns:
                None

            Raises:
                Exception:
                    if any error occurred when folder is locked.
        """
        if delete:
            self.log.info("folder {0} will be deleted if exists".format(folder_name))
            self.manage_folder(operation='delete', folder_name=folder_name)
            self.log.info("folder {0} will be created".format(folder_name))
            self.manage_folder(operation='create', folder_name=folder_name)
        cnt = 0
        while cnt < count:
            doc_obj = "A{0}{1}".format(tc_id, cnt)
            self.create_file(file_path="/QDLS/{0}/{1}.DOC".format(folder_name, doc_obj),
                             content=" Automation object for TC#{0}".format(tc_id))
            cnt += 1
        self.log.info("{1} set of document objects are added to folder {0}".format(folder_name, count))

    def populate_ifs_data(self, directory_name,
                          tc_id='00000',
                          count=1,
                          delete=True,
                          prefix="A"):
        """populates a directory on the client with files.

                Args:
                    directory_name  (str)   --  name / full path of the directory to create

                    tc_id           (str)   : test case ID.
                        default: '00000'
                    count           (int)   : number of objects to be created

                    delete          (bool)  : delete before populating the data

                    prefix           (str)   : prefix of file names to be created.
                        default: 'A'

                Returns:
                    None    -   if directory creation was successful with objects

                Raises:
                    Exception:
                        if directory failed to populate with required data
        """
        if delete:
            self.log.info("directory {0} will be deleted if exists".format(directory_name))
            self.remove_directory(directory_name)
            self.log.info("directory {0} will be created".format(directory_name))
            self.create_directory(directory_name=directory_name)
        cnt = 0
        while cnt < count:
            txt_file = "{0}{1}{2}".format(prefix, tc_id, cnt)
            self.create_file(file_path="{0}/{1}.txt".format(directory_name, txt_file),
                             content=" Automation object for TC#{0}".format(tc_id))
            cnt += 1
        self.log.info("{1} text files added to directory {0}".format(directory_name, count))

    def path_to_lib(self, library_path):
        """
                convert library path and returns name of the library

                Args:
                    library_path    (str)   : The complete path
        """
        return library_path[10:-4]

    def lib_to_path(self, library_name):
        """
                convert library name to IFS path and returns the library path

                Args:
                    library_name    (str)   : Name of the library
        """
        return "/QSYS.LIB/{0}.LIB".format(library_name)

    def halt_ssh_and_cv_services(self,
                                 duration: int,
                                 script_path: str):
        """
            Stop Commvault services and SSH on IBMi client &
            Start the commvault services and SSH on IBMi client after specified duration.
            duration : int --> Duration to keep SSH & CV services down on IBMi client (in seconds)
            script_path : str --> Temporary path of the shell script to be created
        """
        self.log.info("Sending a message to IBMi users that services are going down and stop Commvault services")
        self.run_ibmi_command("system \"SNDBRKMSG MSG('Scheduled automation will end *SSHD & "
                              "Commvault services for {0} seconds. TC#70523') TOMSGQ(*ALLWS)\"".format(str(duration)))

        self.log.info("Stop Commvault services on IBMi client")
        self.run_ibmi_command("system \"SBMJOB CMD(COMMVAULT STOP) JOB(END_CVLT) JOBQ(QCTL)\"")

        self.log.info("Create a shell script on IBMi client machine that ends SSH and "
                      "start CV services & SSH on IBMi client after {0} seconds".format(duration))
        commands_to_run = ["rm -rf {0}".format(script_path),
                           "echo '#!/bin/sh' >{0}".format(script_path),
                           "echo system 'COMMVAULT STOP' >>{0}".format(script_path),
                           "echo 'system 'ENDTCPSVR *SSHD''>>{0}".format(script_path),
                           "echo 'sleep {0}' >>{1}".format(str(duration), script_path),
                           "echo 'system 'STRTCPSVR *SSHD'' >>{0}".format(script_path),
                           "echo system 'COMMVAULT START' >>{0}".format(script_path),
                           "echo 'exit 0' >>{0}".format(script_path),
                           "chmod 777 {0}".format(script_path)
                           ]
        for each_command in commands_to_run:
            self.run_ibmi_command(command=each_command)

        self.log.info("Execute the shell script to end SSH on IBMi client")
        self.run_ibmi_command(command="system \"SBMJOB CMD(QSH CMD('{0}')) "
                                      "JOB(AUTOMATION) JOBQ(QCTL)\"".format(script_path))

    def run_ibmi_command(self, command,
                         validate=True):
        """
                run command on IBMi QSH command line.

                Args:
                    command     (str)   : command to run on IBMi QSH command line

                    validate    (bool)  : Validate the command or not.
        """

        self.log.info("Executing command [{0}]".format(command))
        output = self.execute(command)

        if output.exit_code != 0 and validate:
            raise Exception("Error occurred while running the command output[{0}],".format(str(output)))
        return output

    def manage_folder(self, folder_name='AUTO', operation='create'):
        """
        create or delete folder in QDLS.

            Args:
                operation           (str)   : create or delete
                    default: create
                fodler_name         (str)   : name to use for the object
                    default: AUTOM

            Returns:
                None

            Raises:
                Exception:
                    if any error occurred while creating or deleting the QDLS folder.
        """
        if operation == "create":
            if (folder_name == 'QDIADOCS' or
                    folder_name == 'QFOSDIA' or
                    folder_name == 'QGA400RT' or
                    folder_name == 'QIWSADM' or
                    folder_name == 'QOTTMFLR'
            ):
                raise Exception(" system folders cannot be created.")
            command = "system 'CRTFLR FLR({0}) INFLR(*NONE) TEXT(AUTOMATION)'".format(folder_name)
            output = self.execute(command)
            if output.exit_code != 0 and "already exists" not in str(output.exception):
                raise Exception("Error occurred while creating folder:{2} object {0} {1}".format(
                    str(output.output),
                    str(output.exception),
                    folder_name)
                )
            else:
                self.log.info("folder [{0}] is created.".format(folder_name))
        elif operation == 'delete':
            if (folder_name == 'QDIADOCS' or
                    folder_name == 'QFOSDIA' or
                    folder_name == 'QGA400RT' or
                    folder_name == 'QIWSADM' or
                    folder_name == 'QOTTMFLR'
            ):
                raise Exception(" system folders cannot be deleted.")
            command = "system 'DLTDLO DLO(*ALL) FLR({0})'".format(folder_name)
            output = self.execute(command)
            if output.exit_code != 0 and "not found" not in str(output.exception):
                raise Exception("Error occurred while deleting folder :{2} object {0} {1}".format(
                    str(output.output),
                    str(output.exception),
                    folder_name))
            else:
                self.log.info("folder [{0}] is deleted.".format(folder_name))
        else:
            raise Exception("Invalid operation value {0}".format(operation))

    def populate_lib_with_data(self, library_name='ABCD', tc_id='00000', count=1, prefix="A"):
        """
        Populate a library with objects.

            Args:
                library_name        (str)   : name of the library
                    default: ABCD
                tc_id         (str)   : test case ID.
                    default: '00000'
                count            (int)   : number of objects to be created

            Returns:
                None

            Raises:
                Exception:
                    if any error occurred when library is locked.
        """
        self.manage_library(operation='delete', object_name=library_name)
        self.log.info("Library {0} will be created".format(library_name))
        self.manage_library(operation='create', object_name=library_name)
        cnt = count
        while cnt > 0:
            obj = "{0}{1}{2}".format(prefix, tc_id, cnt)
            self.create_one_object(library_path="/QSYS.LIB/{0}.LIB".format(library_name)
                                   , object_name=obj)
            self.create_sourcepf(library=library_name, object_name=obj)
            cnt -= 1
        self.log.info("Library [{0}] is created with {1} set of srcpf and "
                      "dtaara objects".format(library_name, count))

    def create_savf(self, lib, count=1, size=5000):
        """
        Creates Save file/s under the specific library with specified size.
        Args:
                lib     (str): Name of the library
                count   (int): Number of savf objects to create
                size    (int): size of each save file
        :return: True
        """
        script_arguments = "-path \"{0}\" -numSavfFile 1 -sizeSavf {1}".format(lib, size)
        output = self.execute(IBMI_ADD_DATA, script_arguments)
        if output.exit_code != 0:
            raise Exception(
                "Error occurred while generating test data {0} {1}".format(
                    str(output.output),
                    str(output.exception)
                )
            )
        return True

    def parse_log_file(self, log_file, regex, jobid=None):
        """
        Parses the log file and returns all lines and strings matching the given regex

        Args:
            log_file    (str)   : The complete path of the log file

            regex       (str)   : The regular expression to search for

            jobid       (str)   : The job id for which the regular expression applies
                default: None

        Returns:
            list    : List of all matching string and lines

        Raises:
            Exception:
                Raises exception if error occurs while parsing logs
        """
        if jobid is not None:
            command = "grep '{0}' {1} | grep '{2}'".format(jobid, log_file, regex)
        else:
            command = "grep '{0}' {1}".format(regex, log_file)

        output = self.execute(command)
        if output.exit_code != 0:
            raise Exception(
                "Error occurred while parsing logs {0} {1}".format(
                    str(output.output),
                    str(output.exception)
                )
            )
        else:
            return output.output.split('\n')

    def apply_filter_and_exception(self, data_entry, data_path=None):
        """
        Check if the data is part of filter

        Args:
            data_entry       (str) : String of data to be checked with filter.

            data_path        (str) : Path for which list was generated.
                default: None

        Returns:
            bool : Returns True if data is not filtered.
        """
        # Enhancement: This should handle exceptions as well. Currently library backups and
        # scanless backups don't support exceptions any way.
        # This also handles only simple wildcards. Commvault specific wildcards not supported.
        if not self.filter_list or self.filter_list is None:
            return True

        # In case of metadata/check sums, check the last element
        file = data_entry.split(' ')[-1]
        # File/Folder names returned from ksh scripts have leading /, which has to be ignored.
        library_data = self.join_path(data_path, file[1:]) if data_path is not None else file

        for filters in self.filter_list:
            filters = '{0}*'.format(filters)
            if fnmatch(library_data, filters) is True:
                return False

        return True

    def reconnect(self):
        self._login_with_credentials()

    def get_folder_size(self, folder_path, in_bytes=False):
        """Gets the size of a folder on the client.

        Args:
            folder_path     (str)   --  path of the folder to get the size of

            in_bytes        (bool)  --  if true returns the size in bytes

        Returns:
            float   -   size of the folder on the client (in MB)

        Raises:
            Exception:
                if failed to get the size of the folder

        """
        command = 'du -ks "{0}"'.format(folder_path)
        output = self.execute(command)

        if output.exception_message:
            raise Exception(output.exception_message)
        elif output.exception:
            raise Exception(output.exception)

        size = float(output.formatted_output.split()[0])

        if in_bytes:
            return size * 1024
        else:
            return round(size / 1024.0, 2)

    def get_ibmi_version(self, value="*CURRENT"):
        """Gets the version and release of IBMi client.
        Args:
            value     (str)   --  Version to return
            Valid values : "*SUPPORTED", "*CURRENT"

        Returns:
            str   -   Version of the IBMi client
        Raises:
            Exception:
                if failed to get the version from client

                """
        command = 'uname -a'
        output = self.execute(command)

        if output.exception_message:
            raise Exception(output.exception_message)
        elif output.exception:
            raise Exception(output.exception)
        version = int(output.formatted_output.split()[3])
        release = int(output.formatted_output.split()[2])
        if value == "*CURRENT":
            return "V{0}R{1}M0".format(version, release)
        else:
            return "V{0}R{1}M0".format(version, release - 1)
