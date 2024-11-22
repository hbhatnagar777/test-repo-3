# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides all the methods for parsing PST file

PstParser  --  This class contains all the methods pst parsing
"""
import concurrent.futures
import win32com.client
import pythoncom

class Pstparser:
    """PST parsing Helper class"""

    def __init__(self, pst_path):
        """
        Args:
            pst_path (str): path of pst file
        """
        self.outlook_app = win32com.client.Dispatch('Outlook.Application').GetNamespace("MAPI")
        self.pst_path = pst_path
        self.pst_email_count = 0
        self.parse_pst_get_email_count()

    def __find_pst_folder(self, outlookobj, pst_filepath):
        """
        Iterate through outlook store and return pst root folder
        Args:
            outlookobj (obj): object of outlook instance
            pst_filepath (str): path of pst file
        :return:
               folderobj (obj) : Root folder of the store
        """
        for store in outlookobj.stores:
            if store.IsDataFileStore and store.FilePath == pst_filepath:
                return store.GetRootFolder()
        return None

    def __enumerate_folders(self, folderobj):
        """
        Iterate through folders of outlook
        Args:
            folderobj (obj): object of outlook folder
        """
        for childfolder in folderobj.Folders:
            self.__enumerate_folders(childfolder)
        self.iterate_messages(folderobj)

    def iterate_messages(self, folderobj):
        """
        Iterate through messages of folder in outlook
        Args:
            folderobj (obj): object of outlook folder
        """

        for item in folderobj.Items:
            self.pst_email_count = self.pst_email_count+1
            #self.log.info("Email subject is %s",item.Subject)

    def parse_pst_get_email_count(self):
        """
        Parse through pst file
        Return:
            pst_email_count (int): number of emails in pst
        """
        self.outlook_app.AddStore(self.pst_path)
        pstfolderobj = self.__find_pst_folder(self.outlook_app, self.pst_path)
        try:
            self.__enumerate_folders(pstfolderobj)
            return self.pst_email_count
        except Exception as exp:
            raise Exception(exp)
        finally:
            self.outlook_app.RemoveStore(pstfolderobj)

def create_outlook(pstpath):
    """
        Create Outlook instance in a new thread
        Args:
            pstpath (str): path of pst file
        Return:
            pst_email_count (int): number of emails in pst
    """
    pythoncom.CoInitialize()
    outlook = Pstparser(pstpath)
    return outlook.pst_email_count

def parsepst(pstpath):
    """
        parse the given pst
        Args:
            pstpath (str): path of pst file
        Return:
            email_count (int): number of emails in pst
    """
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(create_outlook, pstpath)
        return_value = future.result()
        return return_value
