# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Main file for storing Teams related constants.

TeamsConstants: Stores all constants.

TeamsConstants Instance Attributes:
===================================

    **PUB_TEAM_NAME**       --  Generates a name for a Public Team, the name includes a timestamp.

    **PVT_TEAM_NAME**       --  Generates a name for a Private Team, the name includes a timestamp.

    **STD_CHANNEL_NAME**    --  Generates a name for a Standard Channel.

    **PVT_CHANNEL_NAME**    --  Generates a name for Private Channel.

    **SRD_CHANNEL_NAME**    --  Generates a name for shared Channel.

    **TXT**                 --  Generates a random text string resembling a GUID.

    **FILE_NAME**           --  Generates a name for a file.

    **FILE_DATA**           --  Generates data for a file.

    **FOLDER_NAME**         --  Generates a name for a folder.

    **LIBRARY_NAME**        --  Generate a name for a Document library.


MS_GRAPH_APIS:  Dictionary of all the GRAPH APIs.

"""

import uuid
import json
import enum

from datetime import datetime as dt


class TeamsConstants:
    """Teams is only accessible via Command Center, there is no concept of multiple backupsets or multiple subclients.
    These values will be constants."""

    cnt = (str(i) for i in range(1, 10000))
    AGENT_NAME = "Cloud Apps"
    BACKUPSET = "defaultBackupSet"
    SUBCLIENT = "default"
    INSTANCE = "MsTeams"
    INDEX_APP_TYPE = 200128
    MEMBERS = ['DAU_1', 'DAU_2', 'DAU_3']
    CHANNEL_DESCRIPTION = 'Description'
    IMG = "iVBORw0KGgoAAAANSUhEUgAAAA0AAAAJCAYAAADpeqZqAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcE" \
          "hZcwAAFiUAABYlAUlSJPAAAAAcSURBVChTY3wro/KfgUTABKVJAqOaoIBemhgYABlNAj6z++JMAAAAAElFTkSuQmCC"
    GIF = "https://media3.giphy.com/media/f5xmRWRu4zxxh2mE5v/giphy.gif?cid" \
          "=de9bf95eevnce0lknjlbneccchvdkn991jea1gtmw2zmvdke&amp;rid=giphy.gif"
    EMOJI = "laugh"
    SUBJECT = "Sample Subject"
    TITLE = "Sample Title"

    class MessageType(enum.Enum):
        TEXT = 1
        IMAGE = 2
        GIF = 3
        EMOJI = 4
        PRAISE = 5
        ANNOUNCEMENT = 6

    class CloudRegion(enum.Enum):
        Default = 1
        Germany = 2
        China = 3
        Gcc = 4
        GccHigh = 5
        Dod = 6

    class FileType(enum.Enum):
        TEXT = 1
        PDF = 2
        DOCX = 3
        PY = 4
        JSON = 5
        C = 6
        CPP = 7
        PPTX = 8
        BIN = 9
        JPG = 10
        PNG = 11
        XLSX = 12
        MP3 = 13

    class PlannerItemType(enum.Enum):
        PLAN = 1
        BUCKET = 2
        TASK = 3

    class ChatType(enum.Enum):
        GROUP = 1
        ONEONONE = 2

    class CloudAppFieldOperator(enum.Enum):
        Contains = 0
        Regex = 1
        StartsWith = 3
        EndsWith = 4
        DoesNotContain = 5
        Before = 100
        After = 101
        OnOrBefore = 102
        OnOrAfter = 103
        Less = 200
        Greater = 201
        LessThanOrEqualTo = 202
        GreaterThanOrEqualTo = 203
        Equals = 1000
        NotEqual = 1001

    class CloudAppFieldType(enum.Enum):
        Generic = 1
        Date = 2
        Time = 3
        DateTime = 4
        Number = 5
        String = 6

    class CloudAppField(enum.Enum):
        Team_SMTP_Address = 2
        Team_Display_Name = 1
        Team_Created_Time = 4

    class CloudAppDiscoveryType(enum.Enum):
        """Type of the discovery needs to run when we adding a content"""
        Team = 12
        AllTeams = 13
        User = 28
        AllUsers = 29
        Group = 27
        CustomCategory = 100

    class CloudAppEdiscoveryType(enum.Enum):
        """Type of the discovery needs to be run when we get list of entities from CVTEAMSDISCOVER.dat File"""
        Teams = 8
        Users = 7
        Groups = 22

    @property
    def PUB_TEAM_NAME(self):
        """Returns a name for a public team."""
        PUB_TEAM_NAME = dt.now().strftime("AT_PUB_%d%h%Y_%H%M")
        return PUB_TEAM_NAME

    @property
    def PVT_TEAM_NAME(self):
        """Returns a name for a public team."""
        PVT_TEAM_NAME = dt.now().strftime("AT_PVT_%d%h%Y_%H%M")
        return PVT_TEAM_NAME

    @property
    def STD_CHANNEL_NAME(self):
        """Returns a name for a standard channel."""
        STD_CHANNEL_NAME = f'STD_CHANNEL_{next(TeamsConstants.cnt)}'
        return STD_CHANNEL_NAME

    @property
    def PVT_CHANNEL_NAME(self):
        """Returns a name for a private channel."""
        PVT_CHANNEL_NAME = f'PVT_CHANNEL_{next(TeamsConstants.cnt)}'
        return PVT_CHANNEL_NAME

    @property
    def SRD_CHANNEL_NAME(self):
        """Returns a name for a private channel."""
        SRD_CHANNEL_NAME = f'SRD_CHANNEL_{next(TeamsConstants.cnt)}'
        return SRD_CHANNEL_NAME

    @property
    def TXT(self):
        """Returns randomly generated text data."""
        TXT = f'{uuid.uuid4().hex} {dt.now().strftime("DATE = %d/%h/%Y TIME = %H:%M:%S")}'
        return TXT

    @property
    def FILE_NAME(self):
        """Returns a file name."""
        return f"file_{next(TeamsConstants.cnt)}"

    @property
    def FILE_DATA(self):
        """Returns data for a file."""
        FILE_DATA = ''.join(([uuid.uuid4().hex for i in range(100)]))
        return FILE_DATA

    @property
    def FOLDER_NAME(self):
        """Returns a folder name."""
        return f"FOLDER_{next(TeamsConstants.cnt)}"

    @property
    def LIBRARY_NAME(self):
        """Returns a library name."""
        return f"DOCUMENT_LIBRARY_{next(TeamsConstants.cnt)}"

    @property
    def NOTEBOOK_NAME(self):
        """Returns a Notebook name."""
        return f"NOTEBOOK_{next(TeamsConstants.cnt)}"

    @property
    def SECTION_NAME(self):
        """Returns a Section name."""
        return f"SECTION_{next(TeamsConstants.cnt)}"

    @property
    def PAGE_NAME(self):
        """Returns a Page name."""
        return f"PAGE_{next(TeamsConstants.cnt)}"

    @property
    def SECTION_GROUP_NAME(self):
        """Returns a Section group name."""
        return f"SECTION_GROUP_{next(TeamsConstants.cnt)}"

    @property
    def PLAN_NAME(self):
        """Returns a Plan name."""
        return f"PLAN_{next(TeamsConstants.cnt)}"

    @property
    def TASK_NAME(self):
        """Returns a Task name."""
        return f"TASK_{next(TeamsConstants.cnt)}"

    @property
    def BUCKET_NAME(self):
        """Returns a Bucket name."""
        return f"BUCKET_{next(TeamsConstants.cnt)}"

    @property
    def PLANNER_TAB_NAME(self):
        """Returns a Planner Tab name."""
        return f"PLANNER_TAB_{next(TeamsConstants.cnt)}"


MS_GRAPH_APIS = {

    "USERS": {

        'url': "https://graph.microsoft.com/v1.0/users",

        'data': '{{'
                '"accountEnabled": true,'
                '"displayName": "{name}",'
                '"mailNickname": "{nick_name}",'
                '"userPrincipalName": "{email}",'
                '"passwordProfile": {{ '
                '"forceChangePasswordNextSignIn": false,'
                '"password": "{pwd}" '
                '}}'
                '}}'
    },

    "GET_USER": {'url': "https://graph.microsoft.com/v1.0/users/{user_principal_name}"},

    "GET_MEMBERS": {'url': "https://graph.microsoft.com/v1.0/groups/{id}/members"},

    "GET_GROUP": {'url': "https://graph.microsoft.com/beta/groups/{id}"},
    "GET_GROUP_BY_DISPLAY_NAME": {
        'url': "https://graph.microsoft.com/beta/groups?$select=id&$filter=displayName eq '{name}'"
    },

    "LIST_GROUPS": {
        'url': "https://graph.microsoft.com/beta/groups?$select=id,displayName,description,mail,createdDateTime&$filter=startswith(displayName,'{name}')"},

    "ADD_TEAM": {

        'url': "https://graph.microsoft.com/v1.0/teams",

        'data': "{{"
                '"template@odata.bind": "https://graph.microsoft.com/v1.0/teamsTemplates(\'standard\')",'
                '"displayName": "{name}",'
                '"description": "{description}",'
                '"members": ['
                '{{'
                '"@odata.type": "#microsoft.graph.aadUserConversationMember",'
                '"roles": ["owner"],'
                '"user@odata.bind": "https://graph.microsoft.com/v1.0/users(\'{id}\')"'
                '}}'
                ']'
                '}}'
    },

    "ADD_MEMBERS_TO_GROUP": {

        'url': "https://graph.microsoft.com/v1.0/groups/{group_id}",

        'data': '{{'
                '"members@odata.bind": {member_list}'
                '}}',

        'members_url': "https://graph.microsoft.com/v1.0/users/{user_id}"
    },

    "CHANNEL": {

        'url': "https://graph.microsoft.com/v1.0/teams/{team_id}/channels",

        'data': '{{'
                '"displayName": "{name}",'
                '"description": "{description}",'
                '"membershipType": "{membership_type}"'
                '}}',

        'PRIVATE': {
            'data': "{{"
                    '"members": {members}'
                    "}}",

            'owners': '{{'
                      '"@odata.type": "#microsoft.graph.aadUserConversationMember",'
                      '"user@odata.bind": "https://graph.microsoft.com/v1.0/users(\'{id}\')",'
                      '"roles": ' + json.dumps(['owner']) + ''
                                                            '}}',

            'members': '{{'
                       '"@odata.type": "#microsoft.graph.aadUserConversationMember",'
                       '"user@odata.bind": "https://graph.microsoft.com/v1.0/users(\'{id}\')",'
                       '"roles": ' + json.dumps([]) + ''
                                                      '}}'
        }
    },

    "ADD_TAB": {

        'tab_id_url': "https://graph.microsoft.com/v1.0/appCatalogs/teamsApps/?$filter=startswith(displayName,'{tab_name}')",

        'url': "https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/tabs",

        'data': '{{'
                '"displayName": "{display_name}",'
                '"teamsApp@odata.bind" : "https://graph.microsoft.com/v1.0/appCatalogs/teamsApps/{tab_id}"'
                '}}'

    },

    "LIST_CHANNELS": {'url': "https://graph.microsoft.com/v1.0/teams/{team_id}/channels"},

    "LIST_POSTS": {'url': "https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/messages"},

    "GET_CHANNEL": {'url': "https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}"},

    "GET_DRIVES": {'url': "https://graph.microsoft.com/beta/groups/{team_id}/drives"},

    "filesFolder": {'url': "https://graph.microsoft.com/beta/teams/{team_id}/channels/{channel_id}/filesFolder"},

    "GET_CHILDREN": {"url": "https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/children",
                            'data': '{{'
                                     '"name": "{folder_name}",'
                                     '"folder": {{}}'
                                     '}}'
                             },

    "CREATE_FILE": {"url": "https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{parent_id}:/{file_name}:/content"
                    },

    "GET_FIILE_DATA": {"url": "https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content"},

    "POST_TO_CHANNEL": {

        'url': "https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/messages",

        'data': {

            'TEXT': '{{'
                    '"body": {{'
                    '"contentType": "html",'
                    '"content": "{content}"'
                    '}}'
                    '}}',

            'IMAGE': '{{"body": {{"contentType": "html", "content": "<div><img height=\\"99\\" src=\\"../hostedContents/1/$value\\"'
                     ' width=\\"99\\"></div>"}}, "hostedContents": [{{"@microsoft.graph.temporaryId": "1",'
                     '"contentBytes": "{content}",'
                     '"contentType": "image/png"}}]}}',

            'GIF': '{{'
                   '"body": {{'
                   '"contentType": "html",'
                   '"content": "<div><img alt=\'GIF Image\' height=\'250\' '
                   'src=\'{content}\' '
                   'width=\'250\' </div>"'
                   '}}'
                   '}}',

            'EMOJI': '{{'
                     '"body": {{'
                     '"contentType": "html",'
                     '"content": "<div><span class=\'animated-emoticon-50\'><img itemid=\'{content}\' '
                     'itemtype=\'http://schema.skype.com/Emoji\' src=\'null\' </div>" '
                     '}}'
                     '}}',

            'PRAISE': '{{"body": {{"contentType": "html", "content": "<div><div><attachment '
                      'id=\'deea5ef098394989a6db5ec55f77ee1a\'></attachment></div></div> <div><at id=\'0\'>{'
                      'to_user}</at> </div>"}}, "attachments": [{{"id": "deea5ef098394989a6db5ec55f77ee1a", '
                      '"contentType": "application/vnd.microsoft.card.adaptive", "content": "{{  \'type\': '
                      '\'AdaptiveCard\',  \'body\': [    {{      \'items\': [        {{'
                      '          \'horizontalAlignment\': \'center\',          \'isSubtle\': true,'
                      '          \'text\': \'{from_user} sent praise to\',          \'wrap\': true,'
                      '          \'type\': \'TextBlock\'        }},        {{          '
                      '\'horizontalAlignment\': \'center\',          \'size\': \'large\',         '
                      ' \'text\': \'{to_user}\',          \'weight\': \'bolder\',          '
                      '\'wrap\': true,          \'type\': \'TextBlock\'        }},        {{'
                      '          \'altText\': \'Awesome\',          \'horizontalAlignment\': '
                      '\'center\',          \'url\': '
                      '\'https://praise.myanalytics.cdn.office.net/2022.4.25.1/assets/badgesV2/en-us/AwesomeBadge'
                      '.png\',          \'width\': \'124px\',          \'height\': \'auto\','
                      '          \'spacing\': \'medium\',          \'type\': \'Image\'      '
                      '  }},        {{          \'horizontalAlignment\': \'center\',          '
                      '\'size\': \'large\',          \'text\': \'\',          \'wrap\': true,'
                      '          \'spacing\': \'medium\',          \'type\': \'TextBlock\'  '
                      '      }},        {{          \'text\': \'**[Review your praise history]('
                      'https://teams.microsoft.com/l/entity/57e078b5-6c0e-44a1-a83f-45f75b030d4a/MyAssist?context=%7B'
                      '%22subEntityId%22%3A%22%7B%5C%22PageUrl%5C%22%3A%5C%22%2FPersonalApp%2FHome%2FPraise%2F%5C%22'
                      '%2C%5C%22Queries%5C%22%3A%5B%7B%5C%22Name%5C%22%3A%5C%22Source%5C%22%2C%5C%22Value%5C%22%3A%5C'
                      '%22PraiseClinet%5C%22%7D%5D%7D%22%7D)**\',          \'spacing\': \'extraLarge\','
                      '          \'separator\': true,          \'type\': \'TextBlock\'        '
                      '}}      ],      \'type\': \'Container\'    }}  ],'
                      '  \'$schema\': \'https://adaptivecards.io/schemas/adaptive-card.json\','
                      '  \'version\': \'1.1\'}}"}}], "mentions": [{{"id": 0, "mentionText": "{'
                      'to_user}", "mentioned": {{"user": {{"id": "{to_user_id}", "displayName": "{to_user}", '
                      '"userIdentityType": "aadUser"}}}}}}]}}',

            'ANNOUNCEMENT': '{{ "subject":"{subject}","body":{{"contentType":"text","content":"<attachment '
                            'id=\\"fa5c31e1538142d28fc1c5dd28fb4019\\"></attachment>{content}"}},"attachments":[{{'
                            '"id":"fa5c31e1538142d28fc1c5dd28fb4019",'
                            '"contentType":"application/vnd.microsoft.teams.messaging-announcementBanner",'
                            '"content":"{{\\"title\\":\\"{title}\\",\\"cardImageType\\":\\"colorTheme\\",'
                            '\\"cardImageDetails\\":{{\\"colorTheme\\":\\"indigo\\"}}}}"}}]}} '

        }
    },

    "UPLOAD_FILE": {'url': "https://graph.microsoft.com/v1.0/drives/{drive}/root:/{channel}/{file}:/content"},

    "DELETE_TEAM": {'url': "https://graph.microsoft.com/v1.0/groups/{id}"},

    "ALL_GROUPS": {'url': "https://graph.microsoft.com/v1.0/groups?$filter=resourceProvisioningOptions/Any(x:x eq 'Team')"
                   },
    "UPDATE_FILE": {"url": "https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}/content"},

    "MOVE_ITEM": {"url": "https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}"},

    "GET_TABS": {'url': "https://graph.microsoft.com/v1.0/teams/{team_id}/channels/{channel_id}/tabs"},

    "DELETE_ITEM": {"url": "https://graph.microsoft.com/v1.0/drives/{drive_id}/items/{item_id}"},
    "GET_ROOT_ID": {'url': "https://graph.microsoft.com/v1.0/drives/{drive_id}/root"},

    "GET_SITE_ID": {'url': "https://graph.microsoft.com/v1.0/groups/{group_id}/sites/root"},

    "CREATE_DOCUMENT_LIBRARY": {'url': "https://graph.microsoft.com/v1.0/sites/{site_id}/lists",
                               'data': '{{'
                                    '"displayName": "{name}",'
                                    '"list": {{'
                                        '"template": "documentLibrary"'
                                    '}}'
                                 '}}'
                                },

    "CREATE_NOTE_BOOK": {'url': "https://graph.microsoft.com/v1.0/sites/{site_id}/onenote/notebooks",
                         'data': '{{'
                                 '"displayName": "{name}"'
                                 '}}'
                         },

    "CREATE_SECTION": {
        'url': "https://graph.microsoft.com/v1.0/sites/{site_id}/onenote/notebooks/{notebook_id}/sections",
        },
    "CREATE_PAGE": {'url': "https://graph.microsoft.com/v1.0/sites/{site_id}/onenote/sections/{section_id}/pages"
                    },
    "CREATE_SECTION_GROUP": {
        'url': "https://graph.microsoft.com/v1.0/sites/{site_id}/onenote/notebooks/{notebook_id}/sectionGroups"
        },

    "CREATE_SECTION_IN_GROUP": {
        'url': "https://graph.microsoft.com/v1.0/sites/{site_id}/onenote/sectionGroups/{sec_group_id}/sections"
        },
    "GET_DRIVES_IN_SHAREPOINT": {'url': "https://graph.microsoft.com/v1.0/sites/{site_id}/drives"},

    "GET_CHANNEL_SHAREPOINT_ID": {
        'url': "https://graph.microsoft.com/v1.0/sites/cvidc365.sharepoint.com:/sites/{team_name-channel_name}"},

    "CREATE_PLAN": {'url': "https://graph.microsoft.com/beta/planner/plans"},

    "CREATE_BUCKET": {'url': "https://graph.microsoft.com/v1.0/planner/buckets"},

    "CREATE_TASK": {'url': "https://graph.microsoft.com/beta/planner/tasks"},

    "GET_PLANS_IN_TEAM": {'url': "https://graph.microsoft.com/beta/groups/{group_id}/planner/plans"},

    "GET_BUCKETS_IN_PLAN": {'url': "https://graph.microsoft.com/beta/planner/plans/{plan_id}/buckets"},

    "GET_TASKS_IN_BUCKET": {'url': "https://graph.microsoft.com/beta/planner/buckets/{bucket_id}/tasks"},

    "DELETE_PLANNER_ITEMS": {'url': "https://graph.microsoft.com/beta/planner/{item_type}/{id}"},

    "ADD_COMMENT_TO_TASK": {'url': "https://graph.microsoft.com/v1.0/groups/{id}/threads/{id}/reply"},

    "CREATE_CHAT": {'url': "https://graph.microsoft.com/v1.0/chats"},

    "GET_CHAT": {'url': "https://graph.microsoft.com/v1.0/chats/{id}"},

    "POST_TO_CHAT": {'url': "https://graph.microsoft.com/v1.0/chats/{id}/messages"},

    "GET_CHAT_MEMBERS": {'url': "https://graph.microsoft.com/v1.0/chats/{id}/members"},

    "ARCHIVE_TEAM":{'url': "https://graph.microsoft.com/v1.0/teams/{id}/archive"},

    "UN_ARCHIVE_TEAM":{'url': "https://graph.microsoft.com/v1.0/teams/{id}/unarchive"}

}