# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
#This is helper class for 3dfs which derives from the FSHelper
# All 3dfs test cases have to inherit this class to perform basic 3dfs operations
# ConfigureArchive store utility is used

    populate_dfs_inputs() - populates 3dfs inputs
    export_share() - exports 3dfs share
    unexport_share() - unexport share
    errorcode_export_unexport() - Evaluates the exported shared output XML
    mount_nfsclient() - Mount the share on the nfs client
    umount_nfsclient() - unmount the share from nfs client
    data_copy_compare() - compares data between the source and share on destination


"""
import time
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from .fshelper import FSHelper
#from xml.etree import ElementTree

class threedfshelper(FSHelper):
    "helper class to perform 3dfs operations"
    # Initialize test case inputs

    def __init__(self, testcase):
        """Initialize instance of the UnixFSHelper class."""
        super(threedfshelper, self).__init__(testcase)

    @staticmethod
    def populate_dfs_inputs(cv_testcase, mandatory=True):
        """Initializes all the test case inputs after validation
               Args:
                   cv_testcase    (obj)    --    Object of CVTestCase
                   mandatory      (bool)   --    whether to check for mandatory inputs
                                                  and raise exception if not found
                  Returns:
                   None
               Raises:
                   Exception:
                       if a valid CVTestCase object is not passed.
                       if CVTestCase object doesn't have agent initialized
               """
        cv_testcase.log.info(" in populate dfs inputs")
        if not isinstance(cv_testcase, CVTestCase):
            raise Exception(
                "Valid test case object must be passed as argument"
            )

        cv_testcase.serverma = cv_testcase.tcinputs.get('3dfsServerName')
        cv_testcase.sharename = cv_testcase.tcinputs.get('shareName')
        cv_testcase.clientname = cv_testcase.tcinputs.get('backupClient')
        cv_testcase.version_index = cv_testcase.tcinputs.get('versionIndex')
        cv_testcase.dfsma = cv_testcase.tcinputs.get('3dfsServerIP')
        cv_testcase.nfsclient = cv_testcase.tcinputs.get('nfsClient')
        cv_testcase.usrname = cv_testcase.tcinputs.get('nfsClientUsr')
        cv_testcase.passwd = cv_testcase.tcinputs.get('nfsClientPassword')

        if cv_testcase.serverma is None:
            raise Exception(" 3dfs server is not provided")

        if cv_testcase.sharename is None:
            raise Exception(" share name is empty")

        if cv_testcase.clientname is None:
            raise Exception(" client Name cant be empty")

        cv_testcase.test_path = cv_testcase.tcinputs.get('TestPath', None)
        cv_testcase.machine = cv_testcase.tcinputs.get('backupClient', None)
        FSHelper.populate_tc_inputs(cv_testcase, mandatory=False)

    def mount_nfsclient(self, nfsclient, usrname,
                        passwd, dfsma, share_name, mountpoint_name):
        """ Mount the specified share

            Args:
                nfsclient (Str)-- NFS client machine on which share is exported

                usrname (Str) --  NFS client user name credentials

                passwd(Str) -- NFS client password

                dfsMA (Strg)  --  3dfs server MA

                share_name (Str) -- Name of the share which has to be unexported

                mountpoint_name (Type -String) -- directory name on which share will be mounted
            Returns:
                None

            Raises:
                 Exception:
                    if any error occurred while unmounting the share.

           """
        try:
            # login to nfs client host and mount the share
            nfs_machine = Machine(nfsclient, username=usrname, password=passwd)
            self.log.info("Mount point: %s", mountpoint_name)
            result = nfs_machine.create_directory(mountpoint_name)
            time.sleep(120)
            self.log.info("Waiting for share to refresh")
            if not result:
                raise Exception("Failed to create {0}".format(share_name))
            mount_cmd = "mount {0}:{1} {2}".format(dfsma, share_name, mountpoint_name)
            self.log.info("mount command : {0} %s", mount_cmd)
            retval = nfs_machine.execute_command(mount_cmd)
            if retval.exception_message:
                raise Exception(retval.exception_code, retval.exception_message)
            elif retval.exception:
                raise Exception(retval.exception_code, retval.exception)
        except Exception as excp:
            raise Exception("Share is not mounted on nfs client: " + str(excp))

    def unmount_nfsclient(self, nfsclient, usrname, passwd, mountpoint_name):
        """ Unmount the specified share

        Args:
            nfsclient (Type -String)--  NFS client machine on which share is exported
            usrname ((Type -String))--  NFS client user n ame
            passwd (Type -String) -- NFS client password
            mountpoint_name (Type -String)-- directory name on which share is mounted

        Returns:
            None

        Raises:
            Exception:
            if any error occurred while unmounting the share.
        """
        try:
            # login to nfs client host and mount the share
            nfs_machine = Machine(nfsclient, username=usrname, password=passwd)
            umount_cmd = "umount " + " " + mountpoint_name
            self.log.info(umount_cmd)
            retval = nfs_machine.execute_command(umount_cmd)
            if retval.exception_message:
                raise Exception(retval.exception_code, retval.exception_message)
            elif retval.exception:
                raise Exception(retval.exception_code, retval.exception)

        except Exception as excp:
            raise Exception("Share is not unmounted on nfs client: " + str(excp))

    # Commenting the method as this is not used in existing test case. this is place holder
    """
    def export_share(self, server_ma, nfsclient, share_name,
                     client_name, subclient_name,
                     backupset_name, version_index, machine):
        #Exports the share on the requested nfs client

        Args:
            server_ma (Type-String)--  3dfs server MA
            nfsclient (Type-integer)--  NFS client machine IP on which share has to be exported
            share_name (Type-String)--  Name of the share which has to be exported
            client_name (Type-String)--  Display name of the Backup machine
            subclient_name (Type-String)--  Subclient name as displayed on backup machine
            Backupset_name (Type-String)--  Name of the backupset on backup machine
            version_index Type-String)--  FSMType (v1/v2)
            machine (Type -String)--  Source machine

            Returns:
                XML of the exported share

            Raises:
                Exception:
                    if any error occurred
                        while exporting the share.
        
        
        try:
            basefolder = machine.get_registry_value('Base', 'dBASEHOME')
            self.log.info("Base Folder Path : " + basefolder)
            #EG:
            #response = "python3 " + baseFolder + "/CvConfigureArchiveStore create -m "
            # + serverma + " -n " +
            # nfsclient + " -s " +
            # shareName + " -c " +
            # clientName + " -sc " +
            # subclientName + " -b " +
            # backupsetName + " -v " + versionIndex
            #mount_cmd = "mount {0}:{1} {2}".format(dfsMA, share_name, share_name)
            response = " {0}/CvConfigureArchiveStore create -m {1} -n {2} -s {3} -c {4} " \
                       "-sc {5} -b {6} -v{7}".format(basefolder, server_ma, nfsclient,
                                                     share_name, client_name,
                                                     subclient_name, backupset_name,
                                                     version_index)
            self.log.info(response)
            retval = machine.execute_command(response)
            if retval.exception_message:
                raise Exception(retval.exception_code, retval.exception_message)
            elif retval.exception:
                raise Exception(retval.exception_code, retval.exception)
            else:
                list1 = retval.formatted_output
                separator = " "
                xmlout = separator.join(str(item) for innerlist in list1 for item in innerlist)
                self.log.info(xmlout)
                #return retval to the calling function
                return xmlout
        except Exception as excp:
            self.log.info(excp)
    """
    """ #Commenting the method as this is not used in existing test case. this is place holder
    def unexport_share(self, server_ma, nfsclient, share_name, version_index, machine):
             #Unexports the share
             Args:
                serverMA(Type -String)   -- 3dfs server MA
                nfsclient (Type-integer) --  NFS client machine on which share is exported
                shareName(Type -String)  -- Name of the share which has to be unexported
                versionIndex(Type -String)--  FSMType (v1/v2)
                machine (Type -String)         --  Source machine

            Returns:
                None

            Raises:
                Exception:
                    if any error occurred while unexporting the share.
        try:
            base_folder = machine.get_registry_value('Base', 'dBASEHOME')
            self.log.info("Base Folder Path : " + base_folder)
            #Eg:
            #response = "python3 " + baseFolder + "/CvConfigureArchiveStore delete -m " +
            # serverMA +
            #" -n " + nfsclient +
            # " -s " + shareName +
            # " -v " + versionIndex

            response = "python3 {0}/CvConfigureArchiveStore delete -m " \
                       "{1} -n {2} -s {3} -v {4}".format(
                           base_folder, server_ma, nfsclient, share_name, version_index)
            self.log.info(response)
            retval = machine.execute_command(response)

            if retval.exception_message:
                raise Exception(retval.exception_code, retval.exception_message)
            elif retval.exception:
                raise Exception(retval.exception_code, retval.exception)

            list1 = retval.formatted_output
            separator = " "
            xmlout = separator.join(str(item) for innerlist in list1 for item in innerlist)
            self.log.info(xmlout)
            #return retval to the calling function
            return xmlout

        except Exception as excp:
            self.log.info(excp)
    """
    #Commenting the method as this is not used in existing test case. this is place holder
    """
    def errorcode_export_unexport(self, retval, operation):
         # Mount the specified share
         Args:
         retval(Str)-- XML value that is obtained on performing Export/UnExport share

         EG:
         <App_Export3dfsResp>\n <error>\n <errorCode>0</errorCode>\n  </error>\n
         <sShare>/share-20gd1-50cache</sShare>\n  <sAccessPath></sA

         operation (int) -- Value 1 indicates, Exporting share. Value 0-indicated error code needed
                      for Unexporting share operation

        Returns:
               If method is called during Export share, share name is returned on success.

               Raises:

        Exception:
                      If XML is not parsed correctly
        try:
            #Appending xml tag as it is needed for element tree
            input_xml = "<?xml version=\"1.0\"?> " + str(retval)
            self.log.info(input_xml)
            ecode = ElementTree.fromstring(input_xml)
            self.log.info(" printing ecode value")
            if operation:
                result = ecode.find("error")
                result1 = result.find("errorCode")
            else:
                result1 = ecode.find("errorCode")
            self.log.info("printing result1 {0}".format(result1.text))
            if result1.text == "0":
                if operation:
                    self.log.info("Share exported successfully!")
                else:
                    self.log.info("Share unexported successfully!")
            else:
                result1 = result.find("errorMessage")
                self.log.info("Printing error message")
                self.log.info(result1.text)
            if operation:
                share = ecode.find("sShare")
                self.log.info("share name is")
                self.log.info(share.text)
                share_name = share.text
                return share_name
            return ""

        except Exception as excp:
            self.log.error(excp)
            raise Exception("Export/Unexport share was un successfull")
    """

    def data_copy_compare(self, nfsclient, sourcemachine,
                          mountpoint_name, usrname,
                          passwd, test_path):
        """Compares the checksum of source path with exported share on nfs client
            and checks if they are same. (This is Unix checksum)

             Args:
                nfsclient (int) -- Destination machine on which share is exported
                machine (object)   -- Source machine
                mountpoint_name (str) -- directory name on which share is exported
                usrname (str)   -- NFS cliennt username
                passwd   (str)       -- NFS client password
                test_path  -- source path

        """
        time.sleep(90)
        self.log.info("Waiting for share to refresh")
        # get the checksum of source and destination
        sourcelist = sourcemachine.get_checksum_list(test_path)
        nfs_machine = Machine(nfsclient, username=usrname, password=passwd)
        #get the checksum of destination list
        destpath = mountpoint_name + test_path
        destlist = nfs_machine.get_checksum_list(destpath)
        self.log.info("comparing the lists")
        self.compare_lists(sourcelist, destlist, sort_list=False)
        self.log.info("comparision done")
