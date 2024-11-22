"""Main file for performing Restore Operation """

import os
import getpass
import platform
import xml.etree.cElementTree as etree
from xml.dom import minidom

from entity import Entity


class Restore(Entity):
    """Class for restore operation

    Methods :
    restore() = Performs restore of given subclient and the given list of items In-place
    restore_out_of_place(destclient,destpath) = Performs restore of given
    subclient and the given list of items Out-of-place

    """
    def __init__(
            self,
            package_instance,
            commcell_object,
            client_name,
            agent_name,
            backupset_name,
            subclient_name,
            logger_object):
        """ Initialize the Restore class instance

            Args:
                package_instance   (str)   -- Instance where commvault is installed

                commcell_object (obj)   -- instance of commcell class

                client_name     (str)   -- Client to perform restore on

                agent_name      (str)   -- Agent to perform restore on

                backupset_name  (str)   -- Backupset to be used for restore

                subclient_name  (str)   -- Subclient to be used for restore

                logger_object   (str)   -- Instance of Logger class

        """
        self._LOG = logger_object
        self.live_restore_path = ''
        self.agent_name = agent_name
        super(Restore, self).__init__(
            logger_object=logger_object,
            commcell_object=commcell_object,
            client_name=client_name,
            agent_name=agent_name,
            backupset_name=backupset_name,
            subclient_name=subclient_name,
            package_instance=package_instance
        )

    def restore(
            self,
            paths=None,
            from_time=None,
            to_time=None,
            output_file_path=None,
            fs_options=None,
            unconditional_overwrite=False,
            copy_precedence=None,
            vsa_guid="",
    ):
        """This method is responsible for initiating in-place restore job on given subclient

        Args :

            paths               (list)  -- List of full paths of files/folders to restore

            from_time           (str)   -- Time to retore the contents after
                        format: YYYY-MM-DD HH:MM:SS

                    default: None

            to_time             (str)   -- Time to retore the contents before
                    format: YYYY-MM-DD HH:MM:SS

                default: None

            output_file_path    (str)   -- Full file path to be used for output

            fs_options      (dict)          -- dictionary that includes all advanced options

                    options:

                        preserve_level      : preserve level option to set in restore

                        proxy_client        : proxy that needed to be used for restore

                        impersonate_user    : Impersonate user options for restore

                        impersonate_password: Impersonate password option for restore
                                                in base64 encoded form

                        all_versions        : if set to True restores all the versions of the
                                                specified file

                        versions            : list of version numbers to be backed up

                        validate_only       : To validate data backed up for restore

                        no_of_streams   (int)       -- Number of streams to be used for restore

            unconditional_overwrite (bool)  --  unconditional overwrite files during restore
                                                    default: False

            copy_precedence         (int)   --  copy precedence value of storage policy copy
                                                    default: None

            vsa_guid        (str)   --  VSA GUID used to browse VM

        Returns :
            Prints restore job details
            Flag : Boolean that represents the completion of restore

        """
        # create XML
        root = etree.Element('Task')

        # another child with text
        child = etree.Element('JobID')

        # Setting no of streams to 2
        if platform.system() != 'OS400':
            if isinstance(fs_options, dict):
                fs_options['no_of_streams'] = 2
            else:
                fs_options = {'no_of_streams': 2}

        # Setting advanced options for restore job
        if platform.system().lower() == 'linux':
            description = f"Submitted by user: [{getpass.getuser()}] uid: [{os.geteuid()}]"
        else:
            description = f"Submitted by user: [{getpass.getuser()}]"

        self._LOG.info(description)
        advanced_options = {
            "job_description": description
        }

        if from_time or to_time:
            advanced_options["timezone"] = Entity.client.timezone
            self._LOG.info(f"Client timezone: {Entity.client.timezone}")

        restore_paths = []
        for path in paths:
            restore_paths.append(Entity._get_absolute_path(path, self.live_restore_path, vsa_guid))
            if self.agent_name == 'virtual server':
                fs_options['file_browse'] = 1

        self._LOG.info(restore_paths)
        try:
            jobid = None
            bflag = 1
            
            if vsa_guid and Entity.backupset is None and Entity.subclient is None :
                fs_options['deduce_bkset_subcl'] = True
                backupset_name = str(next(iter(Entity.agent.backupsets.all_backupsets))) # setting backupset_name to first backupset in the dict returned by all_backupsets()
                Entity.backupset_name = backupset_name
                Entity.backupset =  Entity.agent.backupsets.get(backupset_name)
                subclient_name = Entity.backupset.subclients._default_subclient # setting subclient_name to default subclient
                Entity.subclient_name = subclient_name
                Entity.subclient =  Entity.backupset.subclients.get(subclient_name)
                self._LOG.info(
                    "Backupset and subclient Unspecified for VSA, will use %s and %s as a dummy backupset and subclient objects for creating request options and json",
                    backupset_name, subclient_name
                )
                
            if Entity.subclient is None:
                self._LOG.info("Proceeding with Restore at backupset level [Name: %s ID: %s]",
                               Entity.backupset_name, Entity.backupset.backupset_id)
                jobobj = Entity.backupset.restore_in_place(
                    paths=restore_paths,
                    overwrite=unconditional_overwrite,
                    from_time=from_time,
                    to_time=to_time,
                    fs_options=fs_options,
                    copy_precedence=copy_precedence,
                    advanced_options=advanced_options
                )
                bflag = 0
                jobid = jobobj.job_id
            else:
                self._LOG.info("Proceeding with Restore at Subclient level [Name: %s ID: %s]",
                               Entity.subclient_name, Entity.subclient.subclient_id)
                jobobj = Entity.subclient.restore_in_place(
                    paths=restore_paths,
                    overwrite=unconditional_overwrite,
                    from_time=from_time,
                    to_time=to_time,
                    fs_options=fs_options,
                    copy_precedence=copy_precedence,
                    advanced_options=advanced_options
                )
                bflag = 0
                jobid = jobobj.job_id

            if fs_options.get('deduce_bkset_subcl') == True:
                Entity.backupset_name = None
                Entity.backupset = None
                Entity.subclient_name = None
                Entity.subclient = None

        except Exception as restore_exception:
            restore_exception = str(restore_exception)
            self._LOG.error("Exception Raised in Restore In-Place : %s", restore_exception)
            bflag = 1
        finally:
            if bflag == 0:
                child.text = jobid
                root.append(child)
                if output_file_path is None:
                    treeString = etree.tostring(root, 'utf-8')
                    reparsed = minidom.parseString(treeString)
                    print(reparsed.toprettyxml(indent="    "))
                else:
                    treeString = etree.tostring(root, 'utf-8')
                    reparsed = minidom.parseString(treeString)
                    outputFile = open(output_file_path, "w")
                    outputFile.write(reparsed.toprettyxml(indent="    "))
                    print("Refer to " + output_file_path + " for details ")
                    outputFile.close()
            else:
                self._LOG.error("Restore Job Initiation Encountered Error")
            return bflag, jobid

    def restore_out_of_place(
            self,
            paths=None,
            destination_client=None,
            destination_path=None,
            from_time=None,
            to_time=None,
            output_file_path=None,
            fs_options=None,
            unconditional_overwrite=False,
            copy_precedence=None,
            vsa_guid="",
    ):
        """This method is responsible for initiating out-of-place restore job on given subclient

        Args :
            paths               (list)  -- List of full paths of files/folders to restore

            destination_client  (str) --  Name of the destination client to be used

            destination_path    (str)        --  full path of the restore location on client

            from_time           (str)   -- Time to retore the contents after
                        format: YYYY-MM-DD HH:MM:SS

                    default: None

            to_time             (str)   -- Time to retore the contents before
                    format: YYYY-MM-DD HH:MM:SS

                default: None

            output_file_path    (str)   -- Full file path to be used for output

            fs_options      (dict)          -- dictionary that includes all advanced options

                    options:

                        preserve_level      : preserve level option to set in restore

                        proxy_client        : proxy that needed to be used for restore

                        impersonate_user    : Impersonate user options for restore

                        impersonate_password: Impersonate password option for restore
                                                in base64 encoded form

                        all_versions        : if set to True restores all the versions of the
                                                specified file

                        versions            : list of version numbers to be backed up

                        media_agent         : Media Agent need to be used for Browse and restore

                        validate_only       : To validate data backed up for restore

                        no_of_streams   (int)       -- Number of streams to be used for restore

            unconditional_overwrite (bool)  --  unconditional overwrite files during restore
                                                    default: False

            copy_precedence         (int)   --  copy precedence value of storage policy copy
                                                    default: None

            vsa_guid        (str)   --  VSA GUID used to browse VM

        Returns :
            Prints restore job details
            Flag : Boolean that represents the completion of restore

        """
        root = etree.Element('Task')

        # another child with text
        child = etree.Element('JobID')

        # Setting no of streams to 2
        if platform.system() != 'OS400':
            if isinstance(fs_options, dict):
                fs_options['no_of_streams'] = 2
            else:
                fs_options = {'no_of_streams': 2}

        # Setting advanced options for restore job
        if platform.system().lower() == 'linux':
            advanced_options = {
                "job_description": f"Submitted by user [{getpass.getuser()}] uid [{os.geteuid()}]"
            }
        else:
            advanced_options = {
                "job_description": f"Submitted by user [{getpass.getuser()}]"
            }

        if from_time or to_time:
            advanced_options["timezone"] = Entity.client.timezone
            self._LOG.info(f"Client timezone: {Entity.client.timezone}")

        restore_paths = []
        for path in paths:
            restore_paths.append(Entity._get_absolute_path(path, self.live_restore_path, vsa_guid))
            if self.agent_name == 'virtual server':
                fs_options['file_browse'] = 1

        self._LOG.info(restore_paths)
        try:
            jobid = None
            bflag = 1
            
            if vsa_guid and Entity.backupset is None and Entity.subclient is None :
                fs_options['deduce_bkset_subcl'] = True
                backupset_name = str(next(iter(Entity.agent.backupsets.all_backupsets))) # setting backupset_name to first backupset in the dict returned by all_backupsets()
                Entity.backupset_name = backupset_name
                Entity.backupset =  Entity.agent.backupsets.get(backupset_name)
                subclient_name = Entity.backupset.subclients._default_subclient # setting subclient_name to default subclient
                Entity.subclient_name = subclient_name
                Entity.subclient =  Entity.backupset.subclients.get(subclient_name)
                self._LOG.info(
                    "Backupset and subclient Unspecified for VSA, will use %s and %s as a dummy backupset and subclient objects for creating request options and json",
                    backupset_name, subclient_name
                )
                

            if Entity.subclient is None:
                self._LOG.info("Proceeding with Restore at backupset level [Name: %s ID: %s]",
                               Entity.backupset_name, Entity.backupset.backupset_id)
                jobobj = Entity.backupset.restore_out_of_place(
                    client=destination_client,
                    destination_path=destination_path,
                    paths=restore_paths,
                    overwrite=unconditional_overwrite,
                    from_time=from_time,
                    to_time=to_time,
                    fs_options=fs_options,
                    copy_precedence=copy_precedence,
                    advanced_options=advanced_options
                )
                bflag = 0
                jobid = jobobj.job_id
            else:
                self._LOG.info("Proceeding with Restore at Subclient level [Name: %s ID: %s]",
                               Entity.subclient_name, Entity.subclient.subclient_id)
                jobobj = Entity.subclient.restore_out_of_place(
                    client=destination_client,
                    destination_path=destination_path,
                    paths=restore_paths,
                    overwrite=unconditional_overwrite,
                    from_time=from_time,
                    to_time=to_time,
                    fs_options=fs_options,
                    copy_precedence=copy_precedence,
                    advanced_options=advanced_options
                )
                bflag = 0
                jobid = jobobj.job_id
                
            if fs_options.get('deduce_bkset_subcl') == True:
                Entity.backupset_name = None
                Entity.backupset = None
                Entity.subclient_name = None
                Entity.subclient = None

        except Exception as restore_exception:
            restore_exception = str(restore_exception)
            self._LOG.error("Exception Raised in Restore Out-of-Place : %s", restore_exception)
            bflag = 1
        finally:
            if bflag == 0:
                child.text = jobid
                root.append(child)
                if output_file_path is None:
                    treeString = etree.tostring(root, 'utf-8')
                    reparsed = minidom.parseString(treeString)
                    print(reparsed.toprettyxml(indent="    "))
                else:
                    treeString = etree.tostring(root, 'utf-8')
                    reparsed = minidom.parseString(treeString)
                    outputFile = open(output_file_path, "w")
                    outputFile.write(reparsed.toprettyxml(indent="    "))
                    print("Refer to " + output_file_path + " for details ")
                    outputFile.close()
            else:
                self._LOG.error("Restore out-of-place Job Encountered Error")
            return bflag, jobid
