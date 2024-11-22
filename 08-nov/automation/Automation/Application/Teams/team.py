# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Main file for performing Team operations.

Team is the only class defined in this file.

Team: Class for representing a Team.

Team:
========
    _init_()                                        --  Initialize object of Team.
    check_if_channel_with_name_exists()             --  Checks if channel exists.
    retry()                                         --  Retries function a no. of times or till desired code returned.
    add_team_members()                              --  Add members to a team.
    create_channel()                                --  Create a channel.
    refresh_team_channels()                         --  update team with the latest channels.
    _compute_document_libraries()                   --  Calculates the value for document libraries.
    create_document_library()                       --  Create a document library.
    upload_file_to_document_library()               --  Upload file to the document library.
    upload_folder_to_document_library()             --  Upload folder ot the document library.
    archive_team()                                  -- Archive a team.
    un_archive_team()                               -- Un archive a team.

Team Instance Attributes:
============================
    **document_libraries**   --  A dictionary of the document libraries drives for each Team.

"""

import json
import time
from functools import partial

from Application.Teams import request_response as rr
from Application.Teams.user import Users, User
from Application.Teams.channel import Channel
from Application.Teams.teams_constants import MS_GRAPH_APIS as apis
from Application.Teams import teams_constants
from Application.Teams.sharepoint import SharePoint
from Application.Teams.TimeConverter.epoch_time_converter import EpochTimeConverter
const = teams_constants.TeamsConstants()

file_type = const.FileType


class Team:
    """Class for a Team."""

    def __init__(self, name, cross_tenant_details=None):
        """Initialize object of Team.
            Args:
                name    (str)   --  Name of the team.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Raises:
                Exception in case
                    Team with given name could not be found.
                    Fetching list of existing teams for validation purposes failed.

        """

        self._document_libraries = {}
        self.sharepoint_site_obj = None
        retry = 3
        while retry:
            flag, resp = rr.get_request(url=apis['LIST_GROUPS']['url'].format(name=name), status_code=200,
                                        cross_tenant_details=cross_tenant_details)
            if flag and json.loads(resp.content)['value'] != []:
                break
            time.sleep(5)
            retry -= 1

        if flag and 'value' in json.loads(resp.content) and json.loads(resp.content)['value'] != []:
            resp = json.loads(resp.content)['value'][0]
            self.name = resp['displayName']
            self.id = resp['id']
            self.description = resp['description']
            self.mail = resp['mail']
            created_date_time = resp['createdDateTime']
            created_date_time = created_date_time.split(".")
            created_date_time = created_date_time[0].split("T")
            created_date = created_date_time[0]
            created_time = created_date_time[1].replace("Z", "")
            epoch_time_converter = EpochTimeConverter(created_date, created_time)
            unix_time = str(epoch_time_converter.convert())
            unix_time = unix_time.split(".")
            self.teamsCreatedTime = int(unix_time[0])
            self.guid = self.id.upper().replace("-", "X")

            flag, resp = rr.get_request(url=apis['GET_SITE_ID']['url'].format(group_id=self.id),
                                        cross_tenant_details=cross_tenant_details)

            retry = 3
            while not flag and retry > 0:
                time.sleep(3)
                flag, resp = rr.get_request(url=apis['GET_SITE_ID']['url'].format(group_id=self.id),
                                            cross_tenant_details=cross_tenant_details)
                retry -= 1

            if flag:
                resp = json.loads(resp.content)
                self.sharepoint_site_id = resp['id']
                self.sharepoint_site_obj = SharePoint(self.sharepoint_site_id,
                                                      cross_tenant_details=cross_tenant_details)
            else:
                raise Exception("Failed to fetch sharepoint site id of a team.")

            # FETCH MEMBERS AND STORE DISPLAY NAME OF MEMBERS OF TEAM
            flag, resp = rr.get_request(url=apis['GET_MEMBERS']['url'].format(id=self.id),
                                        cross_tenant_details=cross_tenant_details)
            if flag and 'value' in json.loads(resp.content):
                resp = (json.loads(resp.content)['value'])[0]
                self.owner = resp['displayName']
                self.members = [self.owner]
                self.channels = {"General": Channel(name="General", team_id=self.id, team_name=self.name,
                                                    cross_tenant_details=cross_tenant_details)}
            else:
                raise Exception("Failed to fetch information about the team's members.")

        else:
            raise Exception("Failed to fetch list of teams for validation, ensure that the team exists.")

    def check_if_channel_with_name_exists(self, name, cross_tenant_details=None):
        """Checks if the channel with given name exists in the team.
            Args:
                name    (str)   --  Name of Channel.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                bool    --  True if channel exists, False otherwise.

            Raises:
                Exception in case of a failure to fetch the list of Channels.

        """

        flag, resp = rr.get_request(url=apis['CHANNEL']['url'].format(team_id=self.id), status_code=200,
                                    cross_tenant_details=cross_tenant_details)
        if flag:
            resp = json.loads(resp.content)
            if list(filter(lambda ch: ch['displayName'] == name, [channel for channel in resp['value']])):
                return True
            return False
        raise Exception("Could not fetch a the list of channels for the given team.")

    @staticmethod
    def retry(func, retries):
        """Retries func 'retries' number of times or until desired status code is returned.
            Args:
               func                 --  Function to retry.
               retries      (int)   --  Number of retries.

            Returns:
                resp    --  Returns object of Response.

        """

        for i in range(retries):
            flag, resp = func()
            if flag:
                break
            time.sleep(5)
        return flag, resp

    def add_team_members(self, members, cross_tenant_details=None):
        """
        Add team members.
            Args:
                members (list)  --  Can be a list of User objects or user names provided as strings.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                bool    --  If we were able to add members to the team successfully.

            Raises:
                Exception in case we fail to add team members.

        """
        api = apis['ADD_MEMBERS_TO_GROUP']
        url = api['url'].format(group_id=self.id)
        tmp_members = []
        if isinstance(members[0], User):
            for member in members:
                if member.display_name not in self.members:
                    tmp_members.append(member)
        else:
            for member in members:
                if member not in self.members:
                    tmp_members.append(Users.get_user(member, cross_tenant_details))
        members = tmp_members.copy()
        member_list = json.dumps(list(api['members_url'].format(user_id=m.id) for m in members))
        data = json.loads(api['data'].format(member_list=member_list))

        # partial USED HERE AS ALL ARGUMENTS SPECIFIED IN PARTIAL SENT ALONG TO request_response
        retry = partial(rr.patch_request, url=url, data=data, status_code=204, cross_tenant_details=cross_tenant_details)
        flag, resp = Team.retry(retry, retries=3)
        if flag:
            # UPDATE TEAM WITH NEW MEMBERS
            self.members.append(member.display_name for member in tmp_members if member.display_name not in self.members)
            return flag
        raise Exception(f"Failed to add the team members, reason:  {resp.reason}, status code: {resp.status_code}.")

    def create_channel(self, name, private=False, shared=False, description=None, cross_tenant_details=None, **kwargs):
        """Create a channel.
            Args:
                name            (str)   --  Name of the channel.
                private         (bool)  --  If true, will be private else standard or shared, default is standard.
                    default :   False
                shared         (bool)  --  If true, will be shared else standard or private, default is standard.
                    default :   False
                description     (str)   --  Optionally provide a description for the channel.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                obj --  object, instance of Channel.

            Raises:
                Exception if channel fails to be created.

        """

        membership_type = "private" if private else ("shared" if shared else "standard")

        if not self.check_if_channel_with_name_exists(name, cross_tenant_details):

            api = apis['CHANNEL']
            data = json.loads(api['data'].format(name=name, description=description, membership_type=membership_type))

            status_code = 201
            if shared:
                status_code = 202
            if membership_type == "private" or membership_type == "shared":
                owners = [json.loads(api['PRIVATE']['owners'].format(id=o.id)) for o in kwargs.get('owners')]
                members = [json.loads(api['PRIVATE']['members'].format(id=m.id)) for m in kwargs.get('members')]
                data.update(json.loads(api['PRIVATE']['data'].format(members=json.dumps(owners + members))))

            # partial USED HERE AS ALL ARGUMENTS SPECIFIED IN PARTIAL SENT ALONG TO request_response
            retry = partial(rr.post_request, url=api['url'].format(team_id=self.id), data=data, status_code=status_code,
                            cross_tenant_details=cross_tenant_details)
            flag, resp = Team.retry(retry, retries=3)
            if flag:
                if not shared:
                    resp = json.loads(resp.content)
                    self.channels[resp['displayName']] = Channel(name=resp['displayName'], team_id=self.id,
                                                                 team_name=self.name)
                    return self.channels[resp['displayName']]
                else:
                    self.channels[name] = Channel(name, self.id, self.name, cross_tenant_details=cross_tenant_details)
                    return self.channels[name]
            raise Exception(f"Failed to create channel, reason : {resp.reason}")

    def create_tab(self, channel_name, tab_name, display_name):
        """Creates a tab.
                            Args:
                                channel_name   (str)   --  Name of standard channel under which custom tab needs to be created.
                                tab_name       (str)   --  Name of tab
                                display_name   (str)   --  Display name of tab

                            Returns:
                                bool    --  If we were able to add tab successfully.

                            Raises:
                                Exception in case we fail to add tab.
                        """

        api = apis['ADD_TAB']
        retry = partial(rr.get_request,url=api['tab_id_url'].format(tab_name=tab_name), status_code=200)
        flag, resp = Team.retry(retry, retries=3)
        if flag:
            resp = json.loads(resp.content)
            tab_id = resp['value'][0]['id']
            data = json.loads(api['data'].format(display_name=display_name, tab_id=tab_id))
            retry = partial(rr.post_request,url=api['url'].format(team_id=self.id, channel_id=self.channels[channel_name].channel_id),data=data, status_code=201)
            flag, resp = Team.retry(retry, retries=3)
            resp = json.loads(resp.content)
            if flag:
                return flag
            raise Exception(f"Failed to create tab, reason : {resp.reason}")
        raise Exception(f"Failed to fetch tab id, reason : {resp.reason}")

    def _process_resp_pages(self, resp, pages=10, cross_tenant_details=None):
        """Process all pages of response.

            Args:
                resp    (obj)   --  Response object, instance of Response.
                pages   (int)   --  Number of pages.
                    default:    10
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                List of names.
        """

        if "@odata.nextLink" in resp.keys() and pages > 1:
            next_resp = json.loads(rr.get_request(url=resp["@odata.nextLink"], cross_tenant_details=cross_tenant_details).text)
            return [value['displayName'] for value in resp['value']]+Team._process_resp_pages(next_resp, pages=pages-1)
        return [value['displayName'] for value in resp['value']]

    def refresh_team_channels(self, cross_tenant_details=None):
        """Update team with the latest channels
                Args:
                    cross_tenant_details    (dict)  --  Details of Cross Tenant
                        Default:    None
                Returns:
                    True if we update team with the latest channels.
                Raises:
                     Exception if we failed to update team with the latest changes.
        """

        retry = partial(rr.get_request, url=apis['CHANNEL']['url'].format(team_id=self.id), status_code=200,
                        cross_tenant_details=cross_tenant_details)
        flag, resp = Team.retry(retry, retries=3)
        if flag:
            resp = json.loads(resp.content)
            for channel in resp['value']:
                if channel['displayName'] not in self.channels:
                    self.channels[channel['displayName']] = Channel(channel['displayName'], self.id, self.name,
                                                                    cross_tenant_details=cross_tenant_details)
            return True

        raise Exception("Failed to refresh channels of a team.")

    def _compute_document_libraries_to_team(self, cross_tenant_details=None):
        """Compute document libraries to the team.
                   Args:
                       cross_tenant_details    (dict)  --  Details of Cross Tenant
                Raises:
                        Exception in case we fail to compute document libraries to the team.
               """

        retry = partial(rr.get_request, url=apis['GET_DRIVES']['url'].format(team_id=self.id), status_code=200,
                        cross_tenant_details=cross_tenant_details)
        flag, resp = Team.retry(retry, retries=3)
        if flag:
            resp = json.loads(resp.content)
            for drive in resp['value']:
                if drive['name'] not in self._document_libraries:
                    retry = partial(rr.get_request, url=apis['GET_ROOT_ID']['url'].format(drive_id=drive['id']),
                                    status_code=200,
                                    cross_tenant_details=cross_tenant_details)
                    flag2, resp2 = Team.retry(retry, retries=3)
                    if flag2:
                        resp2 = json.loads(resp2.content)
                        self._document_libraries[drive['name']] = {'drive_id': drive['id'], 'webUrl': drive['webUrl'],
                                                                   'root_id': resp2['id']}

        else:
            raise Exception("Failed to compute document libraries of a team.")

    @property
    def document_libraries(self, cross_tenant_details=None):
        """A dictionary of Document libraries of a team.
            Args:
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                        Default  --    None
            Returns:
                    A dictionary of Document libraries of a team with their properties.
        """

        if self._document_libraries == {}:
            self._compute_document_libraries_to_team(cross_tenant_details)
        return self._document_libraries

    def create_document_library(self, name=const.LIBRARY_NAME):
        """Create a Document library
                Args:
                    name    (str)    -- name of the Document library needs to be created.
                        Default  --  const.LIBRARY_NAME
                Returns:
                    bool - True if we created a document library sucessfully..
                """

        return self.sharepoint_site_obj.create_document_library(name)

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
                        bool    --  Returns True if folder was uploaded successfully,
                        else False

                        """

        return self.sharepoint_site_obj.upload_file_to_document_library(file_name=file_name, data=data, name=name,
                                                                    parent_id=parent_id, f_type=f_type)

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
                        bool    --  Returns True  folder was uploaded successfully,
                        else False.

                """

        return self.sharepoint_site_obj.upload_folder_to_document_library(folder_name=folder_name, name=name,
                                                                      parent_id=parent_id)

    def archive_team(self):
        """
        Archive a team.
        Returns :
          bool    - True if we archive a team otherwise False.
        Raise:
            Exception in case if we failed to archive a team.
        """
        retry = partial(rr.post_request, url=apis['ARCHIVE_TEAM']['url'].format(id=self.id), status_code=202)
        flag, resp = Team.retry(retry, retries=3)
        if flag:
            return True
        raise Exception("Failed to archive a team")

    def un_archive_team(self):
        """
            Un Archive a team.
                Returns :
                  bool    - True if we un archive a team otherwise False.
                Raise:
                    Exception in case if we failed to un archive a team.
                """
        retry = partial(rr.post_request, url=apis['UN_ARCHIVE_TEAM']['url'].format(id=self.id), status_code=202)
        flag, resp = Team.retry(retry, retries=3)
        if flag:
            return True
        raise Exception("Failed to un archive a team")
