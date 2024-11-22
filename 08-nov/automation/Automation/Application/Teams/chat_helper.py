# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Main file for performing Chat operations.

Chat is the only class defined in this file.

Chat: Class for representing a Chat.

Chat:
========
    _init_()                                        --  Initialize object of Chat.
    post_message_to_chat()                          --  Post message to the Chat.
    get_all_messages_in_chat()                      --  Getting all messages in a Chat.
    update_chat_topic()                             --  Update Chat topic.
"""

import json
import Application.Teams.request_response as rr
from Application.Teams import teams_constants
apis = teams_constants.MS_GRAPH_APIS
const = teams_constants.TeamsConstants()
chat_type = const.ChatType


class Chat:

    def __init__(self, chat_id):
        """Initialize object of Chat.
                    Args:
                        chat_id    (int)   --  Id of the chat.
                    Raises:
                        Exception in case
                            Chat with given id could not be found.
                """

        url = apis['GET_CHAT']['url'].format(id=chat_id)
        flag, resp = rr.get_request(url=url)
        retry = 5
        while not flag and retry > 0:
            flag, resp = rr.get_request(url=url)
            retry -= 1
        if not flag:
            raise Exception(f"Failed to get chat details, reason {resp.reason}.")
        resp = json.loads(resp.content)
        self.id = resp["id"]
        self.topic = resp["topic"]
        self.chatType = resp["chatType"]

    def post_message_to_chat(self, message_type, message=None, **kwargs):

        """Post a message or image to the chat.
                   Args:
                       message_type    (str)   --  Specify whether post is text or image.
                       message     (str)   --   Message to be posted
                        Default : None
                   Returns:
                       message_id      (str)   --  ID of the posted message.

                   Raises:
                       Exception in case we fail to post the content to the chat.

               """

        api = apis['POST_TO_CHANNEL']
        msg_type = const.MessageType
        if message_type == msg_type.TEXT:
            if not message:
                message = const.TXT
        elif message_type == msg_type.IMAGE:
            if not message:
                message = const.IMG
        elif message_type == msg_type.GIF:
            if not message:
                message = const.GIF
        elif message_type == msg_type.EMOJI:
            if not message:
                message = const.EMOJI
        else:
            raise Exception(f"Message type {message_type} isn't supported / implemented yet!!")

        if message_type in [msg_type.TEXT, msg_type.IMAGE, msg_type.GIF, msg_type.EMOJI]:
            if message:
                data = json.loads(api['data'][message_type.name].format(content=message))
            else:
                raise Exception(
                    f"Message Content for {message_type.name} post for Chat {self.topic}  isn't specified")

        flag = False
        retry = 6
        url = apis['POST_TO_CHAT']['url']
        while not flag and retry > 0:
            flag, resp = rr.post_request(url=url, data=data, delegated=True, status_code=201, user=None)
            retry -= 1
        if not flag:
            raise Exception(f"Failed to post the message to the Chat, reason {resp.reason}.")
        return json.loads(resp.content)['id']

    def get_all_messages_in_chat(self):
        """Get all messages in a chat.
               Returns:
                    list of chat messages.
               Raises:
                   Exception in case we failed to get messages of the Chat.
            """

        url = apis['POST_TO_CHAT']['url'].format(id=self.id)
        flag = False
        retry = 6
        while not flag and retry > 0:
            flag, resp = rr.get_request(url=url)
            retry -= 1
        if not flag:
            raise Exception(f"Failed to get chat messages, reason {resp.reason}.")
        return json.loads(resp.content)

    def update_chat_topic(self, topic):
        """Update chat topic.
               Args:
                   topic  (str)   --  New Topic name.
               Raises:
                    Exception in case we fail to update the topic of the chat.
           """

        data = {
            "topic": topic
        }
        url = apis['GET_CHAT']['url'].format(id=self.id)
        flag, resp = rr.patch_request(url=url,data=data,delegated=True, status_code=200)
        retry = 5
        while not flag and retry > 0:
            flag, resp = rr.patch_request(url=url, data=data,delegated=True, status_code=200)
            retry -= 1
        if not flag:
            raise Exception(f"Failed to update chat topic, reason {resp.reason}.")
        self.topic = topic

