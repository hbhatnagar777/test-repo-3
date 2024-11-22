# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing Channel operations.

Channel is the only class defined in this file.

Channel: Class for representing channels in a team.

Channel:
========
    _init_()                        --  Initialize object of Channel.
    _compute_sharepoint_drives()    --  Calculates the value for _sharepoint_drives
    post_to_channel()               --  Post a message or image to the channel.
    upload_file()                   --  Uploads a file to the channel.
    list_messages()                 --  List all of the Channel's messages.
    _compute_files_folder_size()    --  Returns the size of a files folder of a channel.
    upload_folder()                 --  upload  a folder to the channel.
    delete_item()                   --  Delete a item from channel.
    update_file()                   --  Update the file with the latest data .

Channel Instance Attributes:
============================
    **sharepoint_drives**   --  A dictionary of the Share point drives for each channel.

"""

import json
import time

import Application.Teams.request_response as rr
from Application.Teams import teams_constants

apis = teams_constants.MS_GRAPH_APIS
const = teams_constants.TeamsConstants()

channel_drive_ids = {}  # TEAM NAME : # CHANNEL DRIVE ID


class Channel:
    """Class for representing a Channel in a Team."""

    def __init__(self, name, team_id, team_name, cross_tenant_details=None):
        """Initialize object of Channel.
            Args:
                name            (name)  --  Name of the channel, unique to each team.
                team_id       (str)   --  Id of the team.
                team_name     (str)  --- Name of the teams
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Raises:
                Exception in case we fail to obtain team or channel information for initializing the object.

        """

        
        self.team_id = team_id
        self.team_name = team_name
        retry = 5
        while retry:
            flag, resp = rr.get_request(url=apis['CHANNEL']['url'].format(team_id=self.team_id), status_code=200,
                                        cross_tenant_details=cross_tenant_details)
            if flag and 'value' in json.loads(resp.content):
                resp = list(ch for ch in (json.loads(resp.content))['value'] if ch['displayName'] == name)
                if resp != []:
                    break
            time.sleep(10)
            retry -= 1

        # GET THE CHANNEL ID, CHANNEL NAME AND MEMBERSHIP TYPE
        if flag and resp != []:
            resp = list(ch for ch in resp if ch['displayName'] == name)[0]
            self.channel_id = resp['id']
            self.name = resp['displayName']
            self.membership_type = resp['membershipType']
            self.description = resp['description']
            self._sharepoint_drives = {}
        else:
            raise Exception("Failed to obtain channel information, required for initializing Channel object.")

    def _compute_sharepoint_drives(self, cross_tenant_details=None):
        """Calculates the value for Share point drives.
            Args:
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Raises:
                Exception if the folder channel is not ready or if we can't retrieve drives for the team.

        """

        if not self._sharepoint_drives:

            url = apis['filesFolder']['url'].format(team_id=self.team_id, channel_id=self.channel_id)
            flag, resp = rr.get_request(url=url, status_code=200, cross_tenant_details=cross_tenant_details)

            if flag:
                resp = json.loads(resp.content)
                self._sharepoint_drives['webUrl'] = resp['webUrl']
                self._sharepoint_drives['folder'] = resp['folder']
                self._sharepoint_drives['root_id'] = resp['id']
                if resp.get('parentReference', False) and resp['parentReference'].get('driveId', False):
                    self._sharepoint_drives['driveId'] = resp['parentReference']['driveId']
                    channel_drive_ids[self.team_name] = self._sharepoint_drives['driveId']
                else:
                    self.sharepoint_drives['driveId'] = channel_drive_ids[self.team_name]

            elif not flag and resp.status_code == 404 and self.team_name not in channel_drive_ids.keys():
                url = apis['GET_DRIVES']['url'].format(team_id=self.team_id)
                flag, resp = rr.get_request(url=url, status_code=200, cross_tenant_details=cross_tenant_details)
                if flag:
                    resp = json.loads(resp.content)
                    channel_drive_ids[self.team_name] = resp['value'][0]['id']
                    self._sharepoint_drives['driveId'] = channel_drive_ids[self.team_name]
                else:
                    raise Exception("Could not fetch drives for the team.")
            else:
                raise Exception("The folder location for the channel was not ready.")

    @property
    def sharepoint_drives(self, cross_tenant_details=None):
        """A dictionary of the MS Sharepoint sites for each channel.
            Args:
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None
        """

        self._compute_sharepoint_drives(cross_tenant_details)
        return self._sharepoint_drives

    def post_to_channel(self, message_type, message, cross_tenant_details=None, **kwargs):
        """Post a message or image to the channel.
            Args:
                message_type    (str)   --  Specify whether post is text or image.
                message     (str)   --   Message to be posted
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                message_id      (str)   --  ID of the posted message.

            Raises:
                Exception in case we fail to post the content to the channel.

        """
        api = apis['POST_TO_CHANNEL']
        msg_type = const.MessageType

        if not kwargs.get("is_reply", False):
            url = api['url'].format(team_id=self.team_id, channel_id=self.channel_id)
        else:
            url_temp = api['url'] + '/{message_id}/' + 'replies'
            if "message_id" in kwargs:
                url = url_temp.format(
                    team_id=self.team_id, channel_id=self.channel_id, message_id=kwargs.get("message_id"))
            else:
                raise Exception(
                    f"Topic Message ID for posting reply for Channel {self.name} Team {self.team_name} isn't specified")

        if message_type in [msg_type.TEXT, msg_type.IMAGE, msg_type.GIF, msg_type.EMOJI]:
            if message:
                data = json.loads(api['data'][message_type.name].format(content=message))
            else:
                raise Exception(
                    f"Message Content for {message_type.name} post for Channel {self.name} "
                    f"Team {self.team_name} isn't specified")

        elif message_type == msg_type.PRAISE:
            if "to_user" in kwargs:
                to_user_id = apis['GET_USER']['url'].format(user_principal_name=kwargs.get("to_user"))
                if "from_user" in kwargs:
                    data = json.loads(
                        api['data'][message_type.name].format(from_user=kwargs.get("from_user"),
                                                              to_user=kwargs.get("to_user"), to_user_id=to_user_id))
                else:
                    raise Exception(
                        f"Recipient of {message_type.name} post for Channel {self.name} "
                        f"Team {self.team_name} isn't specified")
            else:
                raise Exception(
                    f"Sender of {message_type.name} post for Channel {self.name} Team {self.team_name} isn't specified")

        else:
            if "subject" in kwargs:
                if "title" in kwargs:
                    if message:
                        data = json.loads(
                            api['data'][message_type.name].format(subject=kwargs.get("subject"),
                                                                  title=kwargs.get("title"), content=message))
                    else:
                        raise Exception(
                            f"Message Content for {message_type.name} post for Channel {self.name} "
                            f"Team {self.team_name} isn't specified")
                else:
                    raise Exception(
                        f"Title for {message_type.name} post for Channel {self.name} "
                        f"Team {self.team_name} isn't specified")
            else:
                raise Exception(
                    f"Subject for {message_type.name} post for Channel {self.name} "
                    f"Team {self.team_name} isn't specified")

        flag, resp = rr.post_request(url=url, data=data, delegated=True, status_code=201,
                                     cross_tenant_details=cross_tenant_details)
        if not flag:
            raise Exception(f"Failed to post the message to the channel, reason {resp.reason}.")
        return json.loads(resp.content)['id']

    def upload_file(self, file_name, data, cross_tenant_details=None, parent_id=None):
        """Uploads a file to the channel.
            Args:
                file_name   (str)   --  Name of file.
                data        (str)   --  Data of file.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None
                parent_id   (str)   --   id of a parent folder
                    Default:    None

            Returns:
                bool    --  Returns True if file was uploaded successfully, else False.

            Raises:
                Exception in case we fail to upload the file to the channel.

        """
        url = ""
        if parent_id:
            url = apis['CREATE_FILE']['url'].format(drive_id=self.sharepoint_drives['driveId'], parent_id=parent_id,
                                                    file_name=file_name)
        else:
            url = apis['UPLOAD_FILE']['url'].format(drive=self.sharepoint_drives['driveId'], channel=self.name,
                                                    file=file_name)
        for retry in range(3):
            flag, resp = rr.put_request(url=url, data=data, status_code=201, cross_tenant_details=cross_tenant_details)
            if not flag:
                time.sleep(30)
            else:
                return flag, json.loads(resp.content)
        raise Exception("Failed to upload the file to the channel.")

    def list_messages(self, cross_tenant_details=None):
        """List all of the Channel's messages.
            Args:
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                list    --  List of messages

            Raises:
                Exception in case we fail to fetch the IDs of the messages or the content of any of the messages.

        """
        url = apis['LIST_POSTS']['url'].format(team_id=self.team_id, channel_id=self.channel_id)
        flag, resp = rr.get_request(url=url, delegated=True, status_code=200, cross_tenant_details=cross_tenant_details)
        if flag:
            val = json.loads(resp.content)
            if val:
                messages = [message for message in val['value'] if
                            val['value'] != [] and message['body']['content'] != '<systemEventMessage/>']
                return messages
            raise Exception(f"Failed to list channel messages.")

    def list_replies(self, message_id, cross_tenant_details=None):
        """List all of the Channel's post messages replies.
            Args:
                message_id      (str)   -- ID of the topic message
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                list    --  List of messages

            Raises:
                Exception in case we fail to fetch the IDs of the messages or the content of any of the messages.

        """
        temp_url = apis['LIST_POSTS']['url'] + '/{message_id}' + '/replies'
        url = temp_url.format(team_id=self.team_id, channel_id=self.channel_id, message_id=message_id)
        flag, resp = rr.get_request(url=url, delegated=True, status_code=200, cross_tenant_details=cross_tenant_details)
        if flag:
            val = json.loads(resp.content)
            if val:
                replies = [reply for reply in val['value'] if
                           val['value'] != [] and reply['body']['content'] != '<systemEventMessage/>']
                return replies
            raise Exception(f"Failed to list channel messages.")

    def upload_folder(self, folder_name=None, parent_id=None):
        """Uploads a folder to the channel.
                    Args:
                        folder_name   (str)   --  Name of folder.
                        parent_id   (int)   --  Id of parent folder.

                    Returns:
                        bool    --  Returns True and Id of created folder if folder was uploaded successfully,
                        else False.

                    Raises:
                        Exception in case we fail to upload the folder to the channel.

                """
        folder_name = const.FOLDER_NAME if not folder_name else folder_name
        parent_id = self.sharepoint_drives['root_id'] if not parent_id else parent_id
        url = apis['GET_CHILDREN']['url'].format(drive_id=self.sharepoint_drives['driveId'], item_id=parent_id)
        data = json.loads(apis['GET_CHILDREN']['data'].format(folder_name=folder_name))
        for retry in range(3):
            flag, resp = rr.post_request(url=url, data=data, status_code=201)
            if flag:
                return flag, json.loads(resp.content)
            else:
                time.sleep(30)

        raise Exception("Failed to upload a folder.")

    def _compute_files_folder_size(self):
        """Get the files folder size of a channel
            Returns:
                size of files folder in Bytes.
            Raises:
                Exception if the folder channel is not ready or if we can't retrieve drives for the team.
        """
        url = apis['filesFolder']['url'].format(team_id=self.team_id, channel_id=self.channel_id)
        flag, resp = rr.get_request(url=url, status_code=200)
        if flag:
            resp = json.loads(resp.content)
            return resp["size"]

        raise Exception("Failed to get the files folder size of a channel.")

    def delete_item(self, item_id, cross_tenant_details=None):
        """To delete item of a channel
                    Args:
                        item_id     (str)   --  Id of a item to be deleted.
                        cross_tenant_details    (dict)  --  Details of Cross Tenant
                            Default    --  None

                    Raises:
                        Exception in case we fail to delete item.

                """

        url = apis['DELETE_ITEM']['url'].format(drive_id=self.sharepoint_drives['driveId'], item_id=item_id)
        for retry in range(3):
            flag, resp = rr.delete_request(url=url, status_code=204, cross_tenant_details=cross_tenant_details)
            if not flag:
                time.sleep(30)
            else:
                break

        if not flag:
            raise Exception("Failed to delete a item.")

    def update_file(self, file_id, data, cross_tenant_details=None):
        """To update the file content
                Args:
                    file_id     (str)   --  Id of a file to be updated.
                    data        (str)   -- Data of a file to be updated
                    cross_tenant_details    (dict)  --  Details of Cross Tenant
                        Default   --    None

                Raises:
                    Exception in case we fail to update a file.

                        """
        url = apis['UPDATE_FILE']['url'].format(drive_id=self.sharepoint_drives['driveId'], item_id=file_id)
        for retry in range(3):
            flag, resp = rr.put_request(url=url, data=data, status_code=200, cross_tenant_details=cross_tenant_details)
            if not flag:
                time.sleep(30)
            else:
                break

        if not flag:
            raise Exception("Failed to update a file.")

    def move_item(self, item_id, destination_parent_id, cross_tenant_details=None):
        """To move the item to another folder
            Args:
                item_id     (str)   --  Id of item to be moved.
                destination_parent_id        (str)   -- id of the destination_parent
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default   --    None

            Raises:
                Exception in case we failed to move a item.

                    """
        data = {
              "parentReference": {
                "id": f"{destination_parent_id}"
              }
            }
        url = apis['MOVE_ITEM']['url'].format(drive_id=self.sharepoint_drives['driveId'], item_id=item_id)
        for retry in range(3):
            flag, resp = rr.patch_request(url=url, data=data, status_code=200, cross_tenant_details=cross_tenant_details)
            if not flag:
                time.sleep(10)
            else:
                break

        if not flag:
            raise Exception("Failed to move a item.")
