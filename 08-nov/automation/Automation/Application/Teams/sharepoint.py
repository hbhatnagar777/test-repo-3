# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Main file for performing sharepoint operations.

SharePoint is the only class defined in this file.

SharePoint: Class for representing a SharePoint.

SharePoint:
========
    _init_()                                        --  Initialize object of SharePoint.
    retry()                                         --  Retries function a no. of times or till desired code returned.
    _compute_document_libraries_to_sharepoint()     --  Compute document libraries to the sharepoint.
    create_note_book()                              --  Create note_book in the sharepoint.
    create_section()                                --  Create section in the note_book.
    create_section_page()                           --  Create section page in the sections.
    create_section_group()                          --  Create section group in the notebook.
    create_section_to_the_section_group()           --  Create section in the section group.
    _compute_document_libraries()                   --  Calculates the value for document libraries.
    create_document_library()                       --  Create a document library.
    upload_file_to_document_library()               --  Upload file to the document library.
    upload_folder_to_document_library()             --  Upload folder ot the document library.
    get_note_books()                                --  Get notebooks in a sharepoint.
    get_section_groups_in_notebook()                --  Get section groups in a notebook.
    get_sections_in_notebook()                      --  Get sections in a notebook.
    get_pages_in_section()                          --  Get pages in a section.
    get_sections_in_section_group()                 --  Get sections in a section group.
    convert_list_to_dict()                          --  Convert response list to a dict of items and their properties.

SharePoint Instance Attributes:
============================
**document_libraries**   --  A dictionary of the document libraries drives for each sharepoint.
"""

import json
import time

from functools import partial
from Application.Teams import request_response as rr
from Application.Teams.teams_constants import MS_GRAPH_APIS as apis
from Application.Teams import teams_constants

const = teams_constants.TeamsConstants()

file_type = const.FileType


class SharePoint:
    def __init__(self, sharepoint_id, cross_tenant_details=None):
        """Initialize object of SharePoint.
            Args:
                sharepoint_id  (str)  --  Id of a sharepoint site.
                """
        self._id = sharepoint_id
        self._document_libraries = {}
        self._note_book_id = None
        self._compute_document_libraries_to_sharepoint(cross_tenant_details=cross_tenant_details)

    @property
    def note_book_id(self):
        if self._note_book_id is None:
            flag, resp = self.create_note_book()
            self._note_book_id = resp['id']
        return self._note_book_id

    @staticmethod
    def retry(func, retries):
        """Retries func 'retries' number of times or until desired status code is returned.
            Args:
               func                 --  Function to retry.
               retries      (int)   --  Number of retries.

            Returns:
                resp    --  Returns object of Response.

        """
        flag, resp = False, None
        for i in range(retries):
            flag, resp = func()
            if flag:
                break
            time.sleep(5)
        return flag, resp

    def _compute_document_libraries_to_sharepoint(self, cross_tenant_details=None):
        """
        Compute document_libraries to sharepoint site.
         Args:
             cross_tenant_details (dict) -- Dict of cross tenant details.
                Default : None
        Raise :
           Exception Incase if we failed to compute document libraries to sharepoint site.

        """

        retry = partial(rr.get_request, url=apis['GET_DRIVES_IN_SHAREPOINT']['url'].format(site_id=self._id),
                        status_code=200,
                        cross_tenant_details=cross_tenant_details)
        flag, resp = self.retry(retry, retries=3)
        if flag:
            resp = json.loads(resp.content)
            for drive in resp['value']:
                if drive['name'] not in self._document_libraries:
                    retry = partial(rr.get_request, url=apis['GET_ROOT_ID']['url'].format(drive_id=drive['id']),
                                    status_code=200,
                                    cross_tenant_details=cross_tenant_details)
                    flag2, resp2 = self.retry(retry, retries=3)
                    if flag2:
                        resp2 = json.loads(resp2.content)
                        self._document_libraries[drive['name']] = {'drive_id': drive['id'], 'webUrl': drive['webUrl'],
                                                                   'root_id': resp2['id']}

        else:
            raise Exception("Failed to compute document libraries of a team.")

    @property
    def document_libraries(self, cross_tenant_details=None):
        """A dictionary of Document libraries of a sharepoint site.
            Args:
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None
            Returns:
                Dict -- document libraries of a sharepoint site.
        """

        if self._document_libraries == {}:
            self._compute_document_libraries_to_sharepoint(cross_tenant_details)
        return self._document_libraries

    def create_note_book(self, note_book_name=None):
        """
        create a notebook
        Args:
            note_book_name (str)  -- Name of the notebook to be created.
             Default - None
        Returns:
            str - Created Notebook id
        Raise:
          Exception Incase if we failed to create a notebook.

        """
        note_book_name = note_book_name if note_book_name else const.NOTEBOOK_NAME
        url = apis['CREATE_NOTE_BOOK']['url'].format(site_id=self._id)
        data = json.loads(apis['CREATE_NOTE_BOOK']['data'].format(name=note_book_name))
        for retry in range(3):
            flag, resp = rr.post_request(url=url, data=data, status_code=201)
            if flag:
                resp = json.loads(resp.content)
                return resp['id']
            else:
                time.sleep(15)

        raise Exception("Failed to create notebook.")

    def create_section(self, section_name=None, note_book_id=None):
        """
        Create a section.
        Args:
            section_name (str) -- name of the section to be created.
                Default - None
            note_book_id  (str) -- id of the notebook in which section to be created.
                Default - None
        Returns:
            str  -- returns id of a created section.
        Raise:
            Exception in case if we failed to create section.
        """

        section_name = section_name if section_name else const.SECTION_NAME
        note_book_id = note_book_id if note_book_id else self.note_book_id
        url = apis['CREATE_SECTION']['url'].format(site_id=self._id, notebook_id=note_book_id)
        data = json.loads(apis['CREATE_NOTE_BOOK']['data'].format(name=section_name))
        for retry in range(3):
            flag, resp = rr.post_request(url=url, data=data, status_code=201)
            if flag:
                resp = json.loads(resp.content)
                return resp['id']
            else:
                time.sleep(15)

        raise Exception("Failed to create section.")

    def create_section_page(self, section_id, page_name=None, content=None):
        """
        Create a section page.
        Args:
            section_id  (str)  -- id of a section in which page to be created.
            page_name  (str)   -- name of a page.
                Default - None
            content   (str)    --  content of a page.
                Default - None
        Returns:
            Str   -- id of a created page.
        Raise:
            Exception in case if we failed to create a page.
        """
        page_name = page_name if page_name else const.PAGE_NAME
        content = content if content else "This is sample onenote page with name " + page_name
        url = apis['CREATE_PAGE']['url'].format(site_id=self._id, section_id=section_id)
        data = """<html><head><title>{0}</title></head><body><p>{1}</p></body></html>""".format(page_name, content)
        for retry in range(3):
            flag, resp = rr.post_request(url=url, data=data, content_type='application/xhtml+xml', status_code=201)
            if flag:
                resp = json.loads(resp.content)
                return resp['id']
            else:
                time.sleep(15)

        raise Exception("Failed to create section page.")

    def create_section_group(self, sec_group_name=None, note_book_id=None):
        """
        Create section group in a notebook.
        Args:
            sec_group_name  (str)  -- name of the section group.
               Default - None
            note_book_id    (str)  -- id of a notebook in which section group to be created.
              Default - None
        Returns:
            Str    --  Returns id of a created section group.
        Raise:
            Exception incase if we failed to create a section group.
        """
        note_book_id = note_book_id if note_book_id else self.note_book_id
        sec_group_name = sec_group_name if sec_group_name else const.SECTION_GROUP_NAME
        url = apis['CREATE_SECTION_GROUP']['url'].format(site_id=self._id, notebook_id=note_book_id)
        data = json.loads(apis['CREATE_NOTE_BOOK']['data'].format(name=sec_group_name))
        for retry in range(3):
            flag, resp = rr.post_request(url=url, data=data, status_code=201)
            if flag:
                resp = json.loads(resp.content)
                return resp['id']
            else:
                time.sleep(15)

        raise Exception("Failed to create section group.")

    def create_section_to_the_section_group(self, sec_group_id, section_name=None):
        """
        Create a section in a section group.
        Args:
            sec_group_id  (str) -- id of a section group in which section to be created.
            section_name  (str) -- name of a section to be created.
                Default - None
        Returns:
            str   -- id of a created section.
        Raise:
             Exception incase if we failed to create a section in a section group.
        """

        section_name = section_name if section_name else const.SECTION_NAME
        url = apis['CREATE_SECTION_IN_GROUP']['url'].format(site_id=self._id, sec_group_id=sec_group_id)
        data = json.loads(apis['CREATE_NOTE_BOOK']['data'].format(name=section_name))
        for retry in range(3):
            flag, resp = rr.post_request(url=url, data=data, status_code=201)
            if flag:
                resp = json.loads(resp.content)
                return resp['id']
            else:
                time.sleep(30)

        raise Exception("Failed to create section to the section group.")

    def create_document_library(self, name=const.LIBRARY_NAME):
        """Create a Document library
                        Args:
                            name    (str)    -- name of the Document library needs to be created.
                                Default  --  const.LIBRARY_NAME
                        Returns:
                                flag and response if we created a document library sucessfully.
                        Raises:
                                Exception in case we fail to create a document library.
                        """
        data = json.loads(apis['CREATE_DOCUMENT_LIBRARY']['data'].format(name=name))
        for retry in range(3):
            flag, resp = rr.post_request(url=apis['CREATE_DOCUMENT_LIBRARY']['url'].format(site_id=self._id), data=data,
                                         status_code=201)
            if flag:
                self._compute_document_libraries_to_sharepoint()
                return True
            else:
                time.sleep(5)
        raise Exception("Failed to create document libraries to a team.")

    def upload_file_to_document_library(self, file_name=None, data=const.FILE_DATA, name='Documents',
                                        parent_id=None, f_type=file_type.TEXT):
        """Uploads a file to the Document library.
                            Args:
                                file_name   (str)   --  Name of the file.
                                    Default  -- None
                                data         (str)   --  Data of the file.
                                    Default  -- const.FILE_DATA
                                name          (str)   --  Name of document library.
                                   Default  --  Documents
                                parent_id   (int)   --  Id of parent folder.
                                   Default  -- None
                                f_type      (str)   --  Type of the file like text,pdf,png etc.
                                    Default -- TEXT
                            Returns:
                                bool    --  Returns True and response of created folder if folder was uploaded successfully,
                                else False.

                            Raises:
                                Exception in case we fail to upload the file to the document library.

                                """
        if not file_name:
            file_name = const.FILE_NAME
            if f_type == file_type.TEXT:
                file_name += ".txt"
            elif f_type == file_type.PDF:
                file_name += ".pdf"
            elif f_type == file_type.PY:
                file_name += ".py"
            elif f_type == file_type.DOCX:
                file_name += ".docx"
            elif f_type == file_type.C:
                file_name += ".c"
            elif f_type == file_type.CPP:
                file_name += ".cpp"
            elif f_type == file_type.PPTX:
                file_name += ".pptx"
            elif f_type == file_type.BIN:
                file_name += ".bin"
            elif f_type == file_type.JPG:
                file_name += ".jpg"
            elif f_type == file_type.PNG:
                file_name += ".png"
            elif f_type == file_type.JSON:
                file_name += ".json"
            elif f_type == file_type.MP3:
                file_name += ".mp3"
            elif f_type == file_type.XLSX:
                file_name += ".xlsx"
        parent_id = parent_id if parent_id else self.document_libraries[name]['root_id']
        url = apis['CREATE_FILE']['url'].format(drive_id=self.document_libraries[name]['drive_id'], parent_id=parent_id,
                                                file_name=file_name)
        for retry in range(3):
            flag, resp = rr.put_request(url=url, data=data, status_code=201)
            if not flag:
                time.sleep(5)
            else:
                resp = json.loads(resp.content)
                return flag, resp
        raise Exception("Failed to upload the file to the document library.")

    def upload_folder_to_document_library(self, folder_name=const.FOLDER_NAME, name='Documents',
                                          parent_id=None):

        """Uploads a folder to the Document library.
                    Args:
                        folder_name   (str)   --  Name of folder.
                            Default  -- const.FOLDER_NAME
                        name          (str)   --  Name of document library.
                           Default  --  Documents
                        parent_id   (int)   --  Id of parent folder.
                           Default  -- None

                    Returns:
                        bool    --  Returns True and response of created folder if folder was uploaded successfully,
                        else False.

                    Raises:
                        Exception in case we fail to upload the folder to the document library.

                """
        parent_id = parent_id if parent_id else self.document_libraries[name]['root_id']
        url = apis['GET_CHILDREN']['url'].format(drive_id=self.document_libraries[name]['drive_id'], item_id=parent_id)
        data = json.loads(apis['GET_CHILDREN']['data'].format(folder_name=folder_name))
        for retry in range(3):
            flag, resp = rr.post_request(url=url, data=data, status_code=201)
            if flag:
                resp = json.loads(resp.content)
                return flag, resp
            else:
                time.sleep(5)

        raise Exception("Failed to upload a folder to the document library.")

    def get_note_books(self):
        """
        Get notebooks ina sharepoint
        Returns:
            dict -- dict of notebooks and their properties.
        Raise:
            Exception incase if we failed to get notebooks.
        """
        url = apis['CREATE_NOTE_BOOK']['url'].format(site_id=self._id)
        retry = partial(rr.get_request, url=url, status_code=200)
        flag, resp = self.retry(retry, retries=3)
        if flag:
            resp = json.loads(resp.content)
            return self.convert_list_to_dict(resp)
        raise Exception("Failed to get notebooks.")

    def get_section_groups_in_notebook(self, notebook_id):
        """
        Get section groups in a notebook.
        Args:
            notebook_id  (str)  -- id of notebook.
        Returns:
            dict -- dict of section groups and their properties.
        Raise:
            Exception in case if we failed to get section groups in a notebook.
        """
        url = apis['CREATE_SECTION_GROUP']['url'].format(site_id=self._id, notebook_id=notebook_id)
        retry = partial(rr.get_request, url=url, status_code=200)
        flag, resp = self.retry(retry, retries=3)
        if flag:
            resp = json.loads(resp.content)
            return self.convert_list_to_dict(resp)
        raise Exception("Failed to get section groups.")

    def get_sections_in_notebook(self, notebook_id):
        """
                Get section  in a notebook.
                Args:
                    notebook_id  (str)  -- id of notebook.
                Returns:
                    dict -- dict of section and their properties.
                Raise:
                    Exception in case if we failed to get section in a notebook.
                """
        url = apis['CREATE_SECTION']['url'].format(site_id=self._id, notebook_id=notebook_id)
        retry = partial(rr.get_request, url=url, status_code=200)
        flag, resp = self.retry(retry, retries=3)
        if flag:
            resp = json.loads(resp.content)
            return self.convert_list_to_dict(resp)
        raise Exception("Failed to get sections.")

    def get_pages_in_section(self, section_id):
        """
                Get pages groups in a section.
                Args:
                    section_id  (str)  -- id of a section.
                Returns:
                    dict -- dict of pages and their properties.
                Raise:
                    Exception in case if we failed to get pages in a section.
                """

        url = apis['CREATE_PAGE']['url'].format(site_id=self._id, section_id=section_id)
        retry = partial(rr.get_request, url=url, status_code=200)
        flag, resp = self.retry(retry, retries=3)
        if flag:
            resp = json.loads(resp.content)
            return self.convert_list_to_dict(resp, pages=True)
        raise Exception("Failed to get section pages.")

    def get_sections_in_section_group(self, section_group_id):
        """
        Get section in a section group.
                Args:
                section_group_id  (str)  -- id of a section group.
                Returns:
                    dict -- dict of section and their properties.
                Raise:
                    Exception in case if we failed to get section in a section group.
                """
        url = apis['CREATE_SECTION_IN_GROUP']['url'].format(site_id=self._id, sec_group_id=section_group_id)
        retry = partial(rr.get_request, url=url, status_code=200)
        flag, resp = self.retry(retry, retries=3)
        if flag:
            resp = json.loads(resp.content)
            return self.convert_list_to_dict(resp)
        raise Exception("Failed to get sections in the section group.")

    @staticmethod
    def convert_list_to_dict(resp, pages=False):
        """
        convert response list in to a dict.
        Args:
            resp  (dict)  -- response received from request.
            pages (bool)  -- True if response belongs to pages otherwise False.
        Returns:
            Dict   --  dict of items and their properties .
        """
        items = {}
        key = 'title' if pages else 'displayName'
        if 'value' in resp and resp['value'] != []:
            for item in resp['value']:
                items[item[key]] = item
        return items
