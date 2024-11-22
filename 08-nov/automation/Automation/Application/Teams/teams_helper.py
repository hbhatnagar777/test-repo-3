# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for Teams related operations

TeamsHelper:
    __init__()                  --  Initializes TeamsHelper object.
    _process_resp_pages()       --  Processes pages of response, called by create_from_existing_team().
    create_from_existing_team() --  Create Team object from existing team in tenant rather than create new team.
    create_public_team()        --  Create a public team.
    create_private_team()       --  Create a private team.
    add_team_members()          --  Add members to a team.
    create_standard_channel()   --  Create a standard channel.
    create_private_channel()    --  Create a private channel.
    post_text_to_channel()      --  Post text to a channel.
    upload_file()               --  Upload a file to a channel.
    discover()                  --  Discover teams.
    set_content()               --  Add teams to content.
    backup()                    --  Run a backup for the Teams agent.
    get_latest_ci_job()         --  Get latest content indexing job
    out_of_place_restore()      --  Restore team to another location, team items are restored to a destination team.
    compare_message()           --  Compares source and destination message
    compare_team_items()        --  Compares the items, posts, channels etc of two teams to see if they are identical.
    restore_posts_to_html()     --  Restore team posts as HTML
    get_children_in_folder()    --  Get all children of an item(channel/folder)
    get_list_of_folders_in_channel()    -- Get list of all folders in a channel
    get_posts_content_from_html()       -- Helper method to read posts from restored html file
    restore_html_posts_cmp()            -- Compare restored html file to original posts
    delete_team()                       -- Delete a team
    set_all_users_content()             -- Add all teams to content
    get_associated_teams()              -- Get all associated teams for a client
    get_associated_teams_type()         -- Get all associated teams type for a client
    verify_auto_association()           -- Verifies auto association for a teams client
    verify_manual_association()         -- Verifies auto association for a teams client
    verify_manual_association()         -- Verifies auto association for a teams client
    remove_team_association()           -- Removes user association from a teams client
    remove_all_users_content()          -- Removes all user content from a teams client
    remove_all_users_association()      -- Removes all user associations from a teams client
    exclude_teams_from_backup()         -- Removes user association from a teams client
    verify_exclude_teams()              -- Verifies excluded teams for a client
    get_all_teams_in_tenant()           -- Get all teams available in a tenant and returns.
    read_xml()                          -- Read xml from a file location
    get_hostname_and_dir()              -- Get Hostname and Job Results Directory location for a subclient
    get_folders_in_jr()                 -- Method to get the number of folders in the JR directory
    match_delta_token()                 -- Matches delta token before and after the job
    out_of_place_restore_to_file_location()   --  Restore team to file location
    compare_channels_files_folder()     -- Compares the files folder of two channels to see
                                           if they are identical or compare two document libraries.
    out_of_place_files_restore          --   Restore files to another team.
    create_shared_channel()             -- create a shared channel.
    restore_to_original_location()      -- Restore a team to original location.
    get_tabs_in_the_channel()           -- Get a list of tab names of a channel.
    compare_document_libraries_of_teams() -- Compare two teams document libraries.
    compare_one_note_of_sharepoint_sites() -- Compare one notes of sharepoint sites.
    compare_sections()            --   Compare sections.
    compare_section_groups()        --   Comapre section groups.
    create_chat()                   --   Create Chat.
    enable_chat_backup()            -- Enable user chat backup.
    disable_chat_backup()           -- Disable user chat backup.
    get_all_users_in_tenant()       -- Return a list of users email in a tenant.
    compare_teams_plans()           -- Compare teams plans.
    compare_buckets()               -- Compare buckets.
    compare_plans()                 -- Compare plans.
"""

import json
import time
import html
from Application.Teams import request_response as rr
from Application.Teams.planner_helper import Planner
from Application.Teams.team import Team
from Application.Teams.channel import Channel
from Application.Teams.user import Users
from Application.Teams import teams_constants
from bs4 import BeautifulSoup as bs
from AutomationUtils import logger
from AutomationUtils.machine import Machine
from collections import OrderedDict
from xmltodict import parse
import AutomationUtils.config as config
import re
from Database.dbhelper import DbHelper
from AutomationUtils.windows_machine import WindowsMachine
import xml.etree.ElementTree as ET
from Application.Exchange.exchange_sqlite_helper import SQLiteHelper
from Application.Teams.solr_helper import SolrHelper
from concurrent.futures import ThreadPoolExecutor
from Application.Teams.Registry.team_registry import TeamRegistry
from Application.Teams.user import User
from Automation.Server.JobManager.jobmanager_constants import JobOpCode

apis = teams_constants.MS_GRAPH_APIS
const = teams_constants.TeamsConstants()
config = config.get_config()
msg_type = const.MessageType
file_type = const.FileType
chat_type = const.ChatType


class TeamsHelper:
    """Performs teams related operations such as creating a team, adding channels to it, using MS GRAPH.
    It also performs operations such as discovering a team, launching a team using CVPYSDK."""

    def __init__(self, client_obj, testcase_obj=None):
        """Initializes the helper object.
            Args:
                client_obj   (obj)   --  Instance of Client.
                testcase_obj    (obj)   -- Instance of test case
                    Default: None
        """
        self._agent = client_obj.agents.get(const.AGENT_NAME)
        self._instance = self._agent.instances.get(const.INSTANCE)
        self._backupset = self._agent.backupsets.get(const.BACKUPSET)
        self._subclient = self._backupset.subclients.get(const.SUBCLIENT)
        self._commcell_object = client_obj._commcell_object
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._team_registry = TeamRegistry.get_instance(TeamRegistry)
        self.log = logger.get_log()
        if testcase_obj:
            self._tc_obj = testcase_obj
            self._csdb = DbHelper(self._tc_obj.commcell)._csdb

    @property
    def commcell_object(self):
        return self._commcell_object

    # RECURSIVE FUNCTION TO PROCESS BY DEFAULT FIRST 10 PAGES OF THE RESPONSE
    def _process_resp_pages(self, resp, pages=10, mail=False, user_principal_name=False, cross_tenant_details=None):
        """Processes pages of response.
            Args:
                resp    (obj)   --  Response object, instance of Response.
                pages   (int)   --  Number of pages(Default: 10)
                mail    (bool)  --  (Default: False)
                user_principal_name  (bool)  -- (Default : False)
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                List of  entity names when called by create_from_existing_team().

        """

        key = 'displayName'
        if mail:
            key = 'mail'
        elif user_principal_name:
            key = 'userPrincipalName'
        if "@odata.nextLink" in resp.keys() and pages > 1:
            _, next_resp = rr.get_request(url=resp["@odata.nextLink"])
            next_resp = json.loads(next_resp.content)
            return [value[key] for value in resp['value']] + self._process_resp_pages(next_resp, pages=pages - 1,
                                                                                      mail=mail, cross_tenant_details=
                                                                                      cross_tenant_details)
        return [value[key] for value in resp['value']]


    def create_from_existing_team(self, name, cross_tenant_details=None):
        """Create Team object from existing team in tenant rather than create new team.
            Args:
                name    (str)   --  Name of team.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                obj --  Instance of Team if it exists else None.

            Raises:
                Exception in case we failed to retrieve details of existing team or list groups.

        """
        team = self._team_registry.get(name)
        if team:
            return team
        flag, resp = rr.get_request(url=apis['LIST_GROUPS']['url'].format(name=name), status_code=200,
                                    cross_tenant_details=cross_tenant_details)

        if flag:
            resp = json.loads(resp.content)
            if name in self._process_resp_pages(resp, cross_tenant_details=cross_tenant_details):
                flag, resp = rr.get_request(url=apis['GET_GROUP']['url'].format(id=resp['value'][0]['id']),
                                            status_code=200, cross_tenant_details=cross_tenant_details)
                if flag:
                    resp = json.loads(resp.content)
                    team = Team(name=resp['displayName'], cross_tenant_details=cross_tenant_details)
                    self._team_registry.add(team.name, team)
                    time.sleep(10)
                    # UPDATE TEAM WITH THE LIST OF CHANNELS
                    flag, resp = rr.get_request(url=apis['LIST_CHANNELS']['url'].format(team_id=team.id),
                                                status_code=200, cross_tenant_details=cross_tenant_details)
                    if flag and 'value' in json.loads(resp.content):
                        team.channels.update(
                            {channel['displayName']: Channel(channel['displayName'], team.id, team.name,
                                                             cross_tenant_details) for channel in
                             json.loads(resp.content)['value']})
                        return team
                    raise Exception(f"Failed to list channels for the team {team.name}.")
                raise Exception("Failed to retrieve details of the existing team.")
        raise Exception(f"Failed to list groups, unable to create from existing team, reason {resp.reason}.")

    def check_if_team_with_same_display_name_exists(self, name, cross_tenant_details=None):
        """Checks if team with specified name already exists.
            Args:
                name    (str)   --  Display name of the team to check.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                bool    --  True if team exists, False if it doesn't.

            Raises:
                Exception in case we're unable to list the existing groups to check this.

        """

        flag, resp = rr.get_request(url=apis['GET_GROUP_BY_DISPLAY_NAME']['url'].format(name=name), status_code=200,
                                    cross_tenant_details=cross_tenant_details, delegated=True)
        if flag:
            resp = json.loads(resp.content)
            if len(resp['value']) > 0:
                return True
            return False
        raise Exception(
            f"Unable to list teams hence unable to confirm if the team exists, reason:  "
            f"{resp.reason}, status code: {resp.status_code} ")

    def create_team(self, name, owner, cross_tenant_details=None, **kwargs):
        """Create a team along with the members if they don't already exist and returns object of Team.
            Args:
                name        (str)   --  Name of the team.
                owner       (str)   --  Owner of the team.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None
                \\*\\*kwargs  (dict)  --  Optional arguments.
                    Available kwargs Options:
                        description (str)   --  Description of the team.
                        members     (list)  --  List of member names
                            Example:    ['DAU_1', 'DAU_2']

            Returns:
                obj --  Instance of Team.

            Raises:
                Exception in case we are unable to get owner details or we failed to create the team.

        """
        api = apis['ADD_TEAM']

        if self.check_if_team_with_same_display_name_exists(name, cross_tenant_details):
            return self.create_from_existing_team(name, cross_tenant_details)
        owner_id = None
        # FIRST CHECK IN USER REGISTRY
        user = Users.user_registry.get(''.join(owner))
        if user:
            owner_id = user.id
        else:
            flag, owner = Users.get_user_details(''.join(owner), cross_tenant_details) if isinstance(owner, str) else owner
            if flag:
                owner = User(owner, cross_tenant_details)
                Users.user_registry.add(owner.display_name, owner)
                owner_id = owner.id

        if owner_id:
            data = json.loads(
                api['data'].format(name=name, description=kwargs.get('description', name), id=owner_id))
            if kwargs.get('private', False):
                data['visibility'] = 'Private'
            flag, resp = rr.post_request(url=api['url'], data=data, status_code=202,
                                         cross_tenant_details=cross_tenant_details)
            if flag:
                # time.sleep(30)
                team = Team(name, cross_tenant_details)
                # time.sleep(15)
                # CREATE MEMBERS IF THEY DO NOT EXIST
                members = kwargs.get('members')[1:]
                members = list(
                    map(lambda m:
                        Users.get_user(m, cross_tenant_details), members))
                team.add_team_members(members, cross_tenant_details) if kwargs.get('members',
                                                                                   False) and members else None
                self._team_registry.add(name, team)
                return team
            raise Exception("Failed to create the team.")
        raise Exception("Failed to get owner details.")

    def create_public_team(self, name=None, members=const.MEMBERS, cross_tenant_details=None):
        """Create a public team with the optional list of provided members.
            Args:
                name    (str)   --  Name of team.
                members (list)  --  List of member names.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                obj --  Instance of Team.
        """

        return self.create_team(name=name if name else const.PUB_TEAM_NAME, owner=members[0], members=members,
                                cross_tenant_details=cross_tenant_details)

    def create_private_team(self, name=None, members=const.MEMBERS, cross_tenant_details=None):
        """Create a private team with the optional list of provided members.
            Args:
                name    (str)   --  Name of team.
                members (list)  --  List of member names.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                obj --  Instance of Team.

        """

        return self.create_team(name if name else const.PVT_TEAM_NAME, owner=members[0], members=members,
                                cross_tenant_details=cross_tenant_details, private=True)

    def add_team_members(self, team, members, cross_tenant_details=None):
        """Add members to a team.
            Args:

                team    (obj)   --  Instance of 'Team' to which members need to be added.
                members (list)  --  List of member display names, the member will be created if found to not exist.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                tuple   (bool, obj)   --  bool, True if team members were added successfully, False otherwise
                Response object.

            Raises:
                Exception in case the arguments are not of the specified data type.

        """

        if isinstance(team, Team) and isinstance(members, list):
            return team.add_team_members(members, cross_tenant_details=cross_tenant_details)
        raise Exception("Argument 'team' must be an instance of 'Team' & 'members' must be a list .")

    def create_standard_channel(self, team, name=None, description=const.CHANNEL_DESCRIPTION,
                                cross_tenant_details=None):
        """Creates a standard channel.
            Args:
                team        (obj)   --  Team under which standard channel needs to be created.
                name        (str)   --  Name of standard channel
                description (str)   --  Description for channel.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                obj --  Instance of Channel

            Raises:
                Exception if the team is NOT an instance of Team.

        """

        if isinstance(team, Team):
            time.sleep(5)
            name = name if name else const.STD_CHANNEL_NAME
            self.log.info(f"\t\tCreating channel {name}")
            return team.create_channel(name, description=description, cross_tenant_details=cross_tenant_details)
        raise Exception("Argument 'team' must be an instance of 'Team'.")

    def create_private_channel(self, team, name=None, description=const.CHANNEL_DESCRIPTION, owners=None, members=None,
                               cross_tenant_details=None):
        """Creates a private channel.
            Args:
                team        (obj)   --  Team under which standard channel needs to be created.
                name        (str)   --  Name of standard channel
                description (str)   --  Description for channel.
                owners      (list)  --  List of owners, pass User.name for each user who needs to be added as owner.
                members     (list)  --  List of member, pass User.name for each user who needs to be added as member.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                obj --  Instance of Channel.

            Raises:
                Exception if the team is NOT an instance of Team.
        """

        if isinstance(team, Team):
            time.sleep(5)
            owners = list(map(Users.get_user, owners if [owners[0]] else [const.MEMBERS[0]]))
            members = list(map(Users.get_user, members if members else const.MEMBERS[1:]))
            name = name if name else const.PVT_CHANNEL_NAME
            self.log.info(f"\t\tCreating private channel {name}")
            return team.create_channel(name, private=True, description=description, owners=owners, members=members,
                                       cross_tenant_details=cross_tenant_details)
        raise Exception("Argument 'team' must be an instance of 'Team'.")

    def post_text_to_channel(self, channel, message_type, message=None, cross_tenant_details=None, **kwargs):
        """Post a text message to a channel.
            Args:
                channel (obj)   --  Instance of Channel to which the image should be uploaded.
                message_type  (str)  -- Type of message to be sent e.g. text, image, gif etc
                message     (str)   -- Message to be posted
                    Default:    None
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                message_id (str)  -- ID of the posted message
        """

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
        elif message_type == msg_type.PRAISE:
            if not kwargs.get("from_user"):
                kwargs["from_user"] = const.MEMBERS[0]
            if not kwargs.get("to_user"):
                if len(const.MEMBERS) > 1:
                    kwargs["to_user"] = const.MEMBERS[1]
                else:
                    raise Exception(f"Can't post praise posts as there are no members in the channel {channel.name}")
        elif not kwargs.get("is_reply") and message_type == msg_type.ANNOUNCEMENT:
            if not message:
                message = const.TXT
            if not kwargs.get("subject"):
                kwargs["subject"] = const.SUBJECT
            if not kwargs.get("title"):
                kwargs["title"] = const.TITLE
        else:
            raise Exception(f"Message type {message_type} isn't supported / implemented yet!!")

        return channel.post_to_channel(message_type, message, cross_tenant_details=cross_tenant_details, **kwargs)


    def create_custom_tab(self,team,channel_name,tab_name,display_name):
        """Creates a custom tab.
                    Args:
                        team           (obj)   --  Team under which custom tab needs to be created.
                        channel_name   (str)   --  Name of standard channel under which custom tab needs to be created.
                        tab_name       (str)   --  Name of tab
                        display_name   (str)   --  Display name of tab

                    Returns:
                        bool    --  If we were able to add tab successfully.
                """

        return team.create_tab(channel_name,tab_name,display_name)

    def upload_file(self, channel, file=None, data=const.FILE_DATA, cross_tenant_details=None, parent_id=None,
                    f_type=file_type.TEXT):

        """Uploads a file to the provided team's channel.
            Args:
                channel (obj)   --  Instance of Channel to which the image should be uploaded.
                file    (str)   --  Name of file.(Default: 10)
                data    (str)   --  Data of the file.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None
                parent_id (str) --  id of a parent
                    Default:    None
                f_type   (str)  -- Type of the file need to be uploaded e.g. TEXT,PDF,PY,MP3,JPG,PNG etc.
                    Default:    TEXT

            Returns:
                bool    --  Returns True if file was uploaded successfully, else False.

        """

        if not file:
            file = const.FILE_NAME
            if f_type == file_type.TEXT:
                file += ".txt"
            elif f_type == file_type.PDF:
                file += ".pdf"
            elif f_type == file_type.PY:
                file += ".py"
            elif f_type == file_type.DOCX:
                file += ".docx"
            elif f_type == file_type.C:
                file += ".c"
            elif f_type == file_type.CPP:
                file += ".cpp"
            elif f_type == file_type.PPTX:
                file += ".pptx"
            elif f_type == file_type.BIN:
                file += ".bin"
            elif f_type == file_type.JPG:
                file += ".jpg"
            elif f_type == file_type.PNG:
                file += ".png"
            elif f_type == file_type.JSON:
                file += ".json"
            elif f_type == file_type.MP3:
                file += ".mp3"
            elif f_type == file_type.XLSX:
                file += ".xlsx"

        return channel.upload_file(file, data, cross_tenant_details=cross_tenant_details, parent_id=parent_id)

    def discover(self, discovery_type=const.CloudAppEdiscoveryType.Teams, refresh_cache=True):
        """Launches discovery and returns the list of teams.
        Each object in list represents a team and is of type tuple having (team name, team email ID)
            Args:
                discovery_type  (Enum)  -- Type of the discovery
                      Example : users,Teams,Groups.
                refresh_cache (boolean) -- True if we want to refresh cache or else False
                     Default  --  True
            Returns:
                dict    --  Returns dictionary with team name as key and a list of matching team properties (in JSON).

        """

        return self._subclient.discover(discovery_type=discovery_type.value, refresh_cache=refresh_cache)

    def set_content(self, teams, plan, discovery_type=const.CloudAppDiscoveryType.Team):
        """Add teams to the subclient.
            Args:
                teams   (list)  --  List of team email IDs that need to be protected.
                plan    (str)   --  Name of the Office 365 plan to be associated to the teams.
                discovery_type (enum)  --  Type of the discovery  example: Teams,users etc.

            Returns:
                bool    --  True if teams were added successfully.

        """

        return self._subclient.content(teams, plan, discovery_type=discovery_type)

    def backup(self, teams=None, wait_to_complete=True, convert_job_to_full=False,
               discovery_type=const.CloudAppDiscoveryType.Team):
        """Run an Incremental backup.
            Args:
                teams               (list)  --  List of team email IDs that need to be protected.
                wait_to_complete    (bool)  --  Wait for job to complete if True.
                convert_job_to_full (bool)  --  Convert_job to full if True
                discovery_type   (CloudAppDiscoveryType)  -- Type of the entity (ex Team,user,group etc)

            Returns:
                obj   --  Instance of Job.

            Raises:
                Exception in case the backup failed to complete.

        """

        backup_job = self._subclient.backup(teams, convert_job_to_full)
        if wait_to_complete and not backup_job.wait_for_completion():
            raise Exception(f"Failed to run backup {backup_job.job_id}")
        return backup_job

    def get_latest_ci_job(self):
        """
        Get latest completed/running Content Indexing job of the client
        Operation Code (opType) for Content Indexing is 113
        """
        ci_job = self._subclient.find_latest_job(job_filter=JobOpCode.CONTENT_INDEXING_OPCODE.value)
        if ci_job.job_id:
            if not ci_job.wait_for_completion():
                self.log.exception("Pending Reason %s", ci_job.pending_reason)
                raise Exception(f"Failed to run teams CI job {ci_job.job_id}")

            self.log.info('%s job completed successfully.', ci_job.job_type)
        return ci_job.job_id

    def out_of_place_restore(self, team, destination_team, wait_to_complete=True, dest_helper_obj=None):
        """Restore team to another location, Channels, Files, Posts and Wiki are restored to a destination team.
            Args:
                team                (str)   --  The email ID of the team that needs to be restored.
                destination_team    (str)   --  The email ID of the team to be restored to.
                wait_to_complete    (bool)  --  Wait for job to complete if True.
                dest_helper_obj     (obj)   -- Helper object for destination tenant/client
                    Default:    None

            Returns:
                obj   --  Instance of job.

            Raises:
                Exception in case the restore failed to complete.

        """
        restore_job = self._subclient.out_of_place_restore(team, destination_team,
                                                           dest_subclient_obj=dest_helper_obj._subclient if isinstance(
                                                               dest_helper_obj, TeamsHelper) else None)
        if wait_to_complete and not restore_job.wait_for_completion():
            raise Exception(f"Failed to run restore {restore_job.job_id}")
        return restore_job

    def restore_posts_to_html(self, team, destination_team=None, wait_to_complete=True):
        """Restore team posts as HTML.
            Args:
                team                (str)   --  The email ID of the team that needs to be restored.
                destination_team    (str)   --  The email ID of the team to be restored to.
                wait_to_complete    (bool)  --  Wait for job to complete if True.

            Returns:
                obj   --  Instance of job.

            Raises:
                Exception in case the restore failed to complete.

        """
        restore_job = self._subclient.restore_posts_to_html(team, destination_team)
        if wait_to_complete and not restore_job.wait_for_completion():
            raise Exception(f"Failed to run restore {restore_job.job_id}")
        return restore_job

    @staticmethod
    def compare_message(source, destination, reply=False):
        """Compares source and destination message.
            Args:
                source      (str)   --  Source message
                destination (str)   --  Destination message
                reply       (bool)  --  Whether the message is a reply or not
                    default:        False
            Returns:
                bool    -- True if message is identical, False otherwise.

        """

        flag = False
        if not reply and source['subject'] != destination['subject']:
            return False

        if "attachment" in source['body']['content']:
            if "attachment" in destination['body']['content']:
                if source['attachments'] != destination['attachments']:
                    return False
                else:
                    flag = True
            else:
                return False
        else:
            if "attachment" in destination['body']['content']:
                return False

        if not flag:
            if "hostedContent" in source['body']['content']:
                if "hostedContent" in destination['body']['content']:
                    return True
                else:
                    return False
            else:
                if "hostedContent" in destination['body']['content']:
                    return False

        if source['body']['content'] != re.sub(r'\<h2.*?h2\>', '', destination['body']['content']).lstrip('\n'):
            if source['body']['content'] != re.sub(r'\[.*?\] ', '', destination['body']['content']).lstrip('\n'):
                return False
        return True

    def compare_team_items(self, first_team_name, second_team_name, cross_tenant_details=None, dest_helper_obj=None):
        """Compares two existing teams, by comparing items such as channels, posts, files etc.
            Args:
                first_team_name     (str)   --  Email ID of the first team.
                second_team_name    (str)   --  Email ID of the second team.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None
                dest_helper_obj     (obj)   -- Helper object of destination tenant/client
                    Default:    None

            Returns:
                bool    --  True if teams are identical, False otherwise.

        """

        t1 = self.create_from_existing_team(first_team_name)
        if not dest_helper_obj:
            t2 = self.create_from_existing_team(second_team_name)
        else:
            if isinstance(dest_helper_obj, TeamsHelper):
                t2 = dest_helper_obj.create_from_existing_team(second_team_name, cross_tenant_details)
            else:
                raise Exception("Please specify a valid destination helper object")
        t1.refresh_team_channels()
        t2.refresh_team_channels(cross_tenant_details=cross_tenant_details)

        # FIRST COMPARE CHANNELS
        if sorted(list(t1.channels.keys())) == sorted(list(t2.channels.keys())):
            for c in sorted(list(t1.channels.keys())):
                # COMPARE CHANNEL MEMBERSHIP TYPE
                if t1.channels[c].membership_type != t2.channels[c].membership_type:
                    self.log.info(
                        f"EXPECTED Membership type of channel {t1.channels[c].name} = "
                        f"{t1.channels[c].membership_type}")
                    self.log.info(
                        f"OBSERVED Membership type of channel {t2.channels[c].name} = "
                        f"{t2.channels[c].membership_type}")
                    return False

                # COMPARE POSTS OF EACH CHANNEL
                source_channel_msgs = self.executor.submit(t1.channels[c].list_messages)
                destination_channel_msgs = self.executor.submit(t2.channels[c].list_messages, cross_tenant_details)
                source_channel_msgs = source_channel_msgs.result()
                destination_channel_msgs = destination_channel_msgs.result()
                if len(source_channel_msgs) == len(destination_channel_msgs):
                    for i in range(len(source_channel_msgs)):
                        if TeamsHelper.compare_message(source_channel_msgs[i], destination_channel_msgs[i]):
                            source_msg_replies = t1.channels[c].list_replies(message_id=source_channel_msgs[i]['id'])
                            destination_msg_replies = t2.channels[c].list_replies(
                                message_id=destination_channel_msgs[i]['id'], cross_tenant_details=cross_tenant_details)

                            if len(source_msg_replies) == len(destination_msg_replies):
                                for j in range(len(source_msg_replies)):
                                    if not TeamsHelper.compare_message(source_msg_replies[j],
                                                                       destination_msg_replies[j], True):
                                        raise Exception(f"Replies didn't match for Channel {c} for Source Team {t1.name}"
                                                        f" and Destination Team {t2.name}")
                            else:
                                raise Exception(
                                    f"Count of replies didn't match for Channel {c} for Source Team {t1.name} "
                                    f"and Destination Team {t2.name}")
                        else:
                            raise Exception(
                                f"Topic didn't match for Channel {c} for Source Team {t1.name} "
                                f"and Destination Team {t2.name}")
                else:
                    raise Exception(
                        f"Count of Topic didn't match for Channel {c} for Source Team {t1.name} "
                        f"and Destination Team {t2.name}")

                self.log.info(f"Posts match successful for Channel {c} for Source Team {t1.name} "
                              f"and Destination Team {t2.name}")

                self.log.info("Starting the comparison of Files")

                if not (self.compare_channels_files_folder(t1.channels[c], t2.channels[c],
                                                           cross_tenant_details=cross_tenant_details)):
                    raise Exception(f"Channels Files Folder didn't match for channel {c} Source Team {t1.name} and "
                                    f"Destination Team {t2.name}")
                self.log.info("Starting the comparison of Tabs")
                source_tabs = self.executor.submit(self.get_tabs_in_the_channel, t1, t1.channels[c])
                destination_tabs = self.executor.submit(self.get_tabs_in_the_channel, t2, t2.channels[c],
                                                        cross_tenant_details=cross_tenant_details)
                source_tabs = source_tabs.result()
                destination_tabs = destination_tabs.result()

                if not(source_tabs == destination_tabs):
                    raise Exception(f"Channels Tabs didn't match for channel {c} Source Team {t1.name} and "
                                    f"Destination Team {t2.name}")
        else:
            raise Exception(f"Channels didn't match for Source Team {t1.name} and Destination Team {t2.name}")

        return True

    def post_text_reply_to_channel(self, channel, message_type, message=None, message_id=None,
                                   cross_tenant_details=None, **kwargs):
        """Post a text reply message to a channel's text topic.
            Args:
                channel (obj)   --  Instance of Channel to which the reply is to be sent.
                message_type  (str)  -- Type of message to be sent e.g. text, image, gif etc
                message     (str)   -- Message to be posted
                    Default:    None
                message_id  (str)   -- ID of the topic message
                    Default:    None
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None
            Returns:
                message_id (str)  -- ID of the posted message
        """
        if not message_id:
            kwargs["message_id"] = self.post_text_to_channel(channel, msg_type.TEXT,
                                                             cross_tenant_details=cross_tenant_details)
        else:
            kwargs["message_id"] = message_id

        kwargs["is_reply"] = True

        return self.post_text_to_channel(channel, message_type, message, **kwargs,
                                         cross_tenant_details=cross_tenant_details)

    def get_children_in_folder(self, drive_id, item_id, cross_tenant_details=None):
        """Get all children of an item(channel/folder)
                Args:
                    drive_id    (str): Drive_id of the team
                    item_id     (str): item id of the object whose children are required
                    cross_tenant_details    (dict)  --  Details of Cross Tenant
                        Default:    None

                Returns:
                    list of children folder object{
                        "Name",
                        "parentReference",
                        "id"
                    }
        """
        url = apis["GET_CHILDREN"]["url"].format(
            drive_id=drive_id, item_id=item_id)
        self.log.info(f"\t\tGetting Children from URL:\n\t\t\t\t\t\t{url}")
        flag, resp = rr.get_request(url=url, cross_tenant_details=cross_tenant_details)
        if flag:
            response = resp.json()
            if response and "value" in response:
                return list(
                    map(
                        lambda x: {"name": x['name'], "parentReference": x["parentReference"],
                                   "id": x["id"], "size": x["size"], "fileSystemInfo": x["fileSystemInfo"],
                                   "file": x["file"] if "file" in x else {}
                                   }, response["value"]
                    )
                )
        return []

    def get_list_of_folders_in_channel(self, team, channel_name, cross_tenant_details=None):
        """Get list of all folders in a channel
                Args:
                    team            (obj): Team object for a team
                    channel_name    (str): Channel name
                    cross_tenant_details    (dict)  --  Details of Cross Tenant
                        Default:    None

                Returns:
                    list of children folder object{
                        "Name",
                        "parentReference",
                        "id"
                    }
        """
        channel = team.channels[channel_name]
        if channel:
            url = apis["filesFolder"]["url"].format(
                team_id=team.id, channel_id=channel.channel_id)
            self.log.info(f"\t\tGetting FilesFolder from url: \n\t\t\t\t\t\t{url}")
            flag, resp = rr.get_request(url=url, cross_tenant_details=cross_tenant_details)
            if flag:
                response = resp.json()
                if 'id' in response and 'parentReference' in response:
                    item_id = response['id']
                    drive_id = response['parentReference']['driveId']
                    return self.get_children_in_folder(drive_id, item_id, cross_tenant_details)
                self.log.info("\t\tSomething went wrong while getting FilesFolder")
                return
            self.log.info("\t\tError in calling FilesFolder URL")
            return
        self.log.info(f"\t\tChannel {channel_name} not present in team: {team.name}")

    def get_posts_content_from_html(self, drive_id, item_id, cross_tenant_details=None):
        """Helper method to read posts from restored html file
                Args:
                    drive_id        (str): Drive id of the team
                    item_id         (str): Item id of the file
                    cross_tenant_details    (dict)  --  Details of Cross Tenant
                        Default:    None
        """
        url = apis["GET_FIILE_DATA"]["url"].format(drive_id=drive_id, item_id=item_id)
        self.log.info(f"\t\tGetting html file data from url: \n\t\t\t\t\t\t{url}")
        flag, resp = rr.get_request(url=url, cross_tenant_details=cross_tenant_details)
        if flag:
            response = resp.text
            self.log.info("\t\tParsing html data")
            data = bs(response, "lxml")
            msgs = data.findAll('div', attrs={'class': 'message-body'})
            return list(map(lambda m: html.escape(m.text.strip()), msgs))
        self.log.info("\t\tError in calling GET_FILE_DATA url")

    def restore_html_posts_cmp(self, team, old_list_obj, channel_name=None):
        """Compare restored html file to original posts
                Args:
                    team         (obj) : Team object
                    old_list_obj (list): List of children folders that existed before restore post to html was ran
                    channel_name (str) : Channel name where the file was restored

                Returns:
                    Boolean stating if restore was successful
        """
        _channel = channel_name if channel_name else const.STD_CHANNEL_NAME
        self.log.info(f"\n\tGetting folders in {_channel} channel of team {team.name}")
        new_list_obj = self.get_list_of_folders_in_channel(team, _channel)
        old_li = list(map(lambda x: x["name"], old_list_obj))
        restored_obj = []
        for item in new_list_obj:
            if item["name"] not in old_li:
                restored_obj.append(item)
        if not restored_obj or len(restored_obj) > 1:
            self.log.info("\t\tError in getting restored folder from teams")
            return False
        else:
            restored_obj = restored_obj[0]
        self.log.info(f"\t\tRestored folder calculated is: {restored_obj['name']}")
        restored_files = self.get_children_in_folder(restored_obj["parentReference"]["driveId"], restored_obj["id"])
        restored_data = []
        for file in restored_files:
            data = self.get_posts_content_from_html(
                restored_obj["parentReference"]["driveId"], file["id"])
            restored_data.extend(data)
        if not restored_data:
            return False
        url = apis["LIST_POSTS"]["url"].format(
            team_id=team.id, channel_id=team.channels[_channel].channel_id)
        self.log.info(f"\t\tGetting list of posts from URL:\n\t\t{url}")
        flag, resp = rr.get_request(url=url, delegated=True)
        if flag and resp.json():
            content = resp.json()
            if 'value' in content:
                post_data = list(
                    map(lambda x: x['body']['content'].strip(),
                        filter(lambda n: n['messageType'] == 'message', content['value'])))
                post_data.reverse()
                return all(list(map(lambda x, y: x == y, restored_data, post_data)))
            else:
                self.log.info("\t\tSomething went wrong while getting list of posts")
        else:
            self.log.info("\t\tError in calling url to get list of posts")
        return False

    def delete_team(self, team, cross_tenant_details=None):
        """Delete a team
                Args:
                    team    (str or Team obj): Email add or the team object of the team to be deleted
                    cross_tenant_details    (dict)  --  Details of Cross Tenant
                        Default:    None

                Raises:
                    Exception if the passed team name is invalid
        """
        if isinstance(team, Team):
            group_id = team.id
        else:
            team_obj = self._subclient.get_team(team)
            if team_obj:
                group_id = team_obj.id
            else:
                raise Exception(f"The specified team:{team} couldn't be found")
        flag, resp = rr.delete_request(url=apis["DELETE_TEAM"]["url"].format(id=group_id), delegated=True,
                                       cross_tenant_details=cross_tenant_details)
        if resp.status_code != 204:
            raise Exception("Error while deleting team")

    def set_all_users_content(self, plan_name):
        """Add all teams to content
                Args:
                    plan_name(str): Name of the plan to be associated with All teams content
        """
        self._subclient.set_all_users_content(plan_name)

    def get_associated_teams(self, **kwargs):
        """Get all associated teams for a client
                Variable Args:
                    pageNumber  (int): Page number of the results
                    pageSize    (int): Size of the page of results

                Returns:
                    List of all team associations and their details
        """
        pagingInfo = {}
        if 'pageSize' in kwargs:
            pagingInfo['pageSize'] = int(kwargs.get('pageSize'))
        if 'pageNumber' in kwargs:
            pagingInfo['pageNumber'] = int(kwargs.get('pageNumber'))
        return self._subclient.get_associated_teams(pagingInfo)

    def get_associated_teams_type(self):
        """Get all associated teams type for a client
            Returns:
                dict of all manual and auto associations for a client
        """
        disc_users = self.get_associated_teams()
        users = {'manual': [], 'auto': []}
        if disc_users:
            disc_users = {user['userAccountInfo']['smtpAddress'].lower(): user['userAccountInfo'] for user in
                          disc_users}
            for team, value in disc_users.items():
                if value['isAutoDiscoveredUser']:
                    users['auto'].append(team)
                else:
                    users['manual'].append(team)
        return users

    def verify_auto_association(self, users=None):
        """Verifies auto association for a teams client
                Args:
                    users   (list): List of input teams for which verification is required. If user list is not
                                    provided then all users are tested for discovery type as Auto

                Returns:
                    Boolean result
        """
        disc_users = self.get_associated_teams()
        if disc_users:
            auto_users = {user['userAccountInfo']['smtpAddress'].lower(): user['userAccountInfo'] for user in
                          disc_users}
            if users:
                for user in users:
                    if user.lower() in auto_users and not auto_users[user.lower()]['isAutoDiscoveredUser']:
                        self.log.info(f"\t\tTeam \"{user}\" should have been auto")
                        return False
            else:
                for user in auto_users.values():
                    if not user['isAutoDiscoveredUser']:
                        self.log.info(f"\t\tTeam \"{user}\" should have been auto")
                        return False
        return True

    def verify_manual_association(self, users=None):
        """Verifies auto association for a teams client
                Args:
                    users   (list): List of input users for which verification is required. If user list is not
                                    provided then all users are tested for discovery type as Auto

                Returns:
                    Boolean result
        """
        disc_users = self.get_associated_teams()
        if disc_users:
            man_users = {user['userAccountInfo']['smtpAddress'].lower(): user['userAccountInfo'] for user in disc_users}
            if users:
                for user in users:
                    if user.lower() in man_users and man_users[user.lower()]['isAutoDiscoveredUser']:
                        self.log.info(f"\t\tTeam \"{user}\" should have been manual")
                        return False
            else:
                for user in man_users.values():
                    if user['isAutoDiscoveredUser']:
                        self.log.info(f"\t\tTeam \"{user}\" should have been manual")
                        return False
        return True

    def remove_team_association(self, teams):
        """Removes user association from a teams client
                Args:
                    teams   (list): List of input users smtp whose association is to be removed
        """
        disc_users = self.get_associated_teams()
        if disc_users:
            disc_users = {user['userAccountInfo']['smtpAddress'].lower(): user['userAccountInfo'] for user in
                          disc_users}
            users_assoc = []
            if disc_users:
                for user in teams:
                    if user.lower() in disc_users:
                        users_assoc.append(disc_users[user.lower()])
            self._subclient.remove_team_association(users_assoc)

    def remove_all_users_content(self):
        """Removes all user content from a teams client"""
        self._subclient.remove_all_users_content()

    def remove_all_users_association(self):
        """Removes all user associations from a teams client"""
        discover_users = self.get_associated_teams()
        if discover_users:
            discover_users = [user['userAccountInfo'] for user in discover_users]
            self.log.info("\t\t Removing all teams association from client")
            self._subclient.remove_team_association(discover_users)

    def exclude_teams_from_backup(self, teams):
        """Removes user association from a teams client
                Args:
                    teams   (list): List of input teams whose association is to be removed
        """
        disc_users = self.get_associated_teams()
        if disc_users:
            disc_users = {user['userAccountInfo']['smtpAddress'].lower(): user['userAccountInfo'] for user in
                          disc_users}
            users_assoc = []
            if teams:
                for team in teams:
                    if team.lower() in disc_users:
                        users_assoc.append(disc_users[team.lower()])
                self._subclient.exclude_teams_from_backup(users_assoc)

    def verify_exclude_teams(self, teams):
        """Verifies excluded teams for a client
                Args:
                    teams   (list): List of input teams which are supposed to be excluded from backup

                Returns:
                    Boolean result
        """
        disc_users = self.get_associated_teams()
        if disc_users:
            disc_users = {user['userAccountInfo']['smtpAddress'].lower(): user['accountStatus'] for user in disc_users}
            for team in teams:
                if team.lower() in disc_users and disc_users[team.lower()] != 2:
                    self.log.info(f"\t\tTeam \"{team}\" should have been excluded")
                    return False
        return True

    def get_all_teams_in_tenant(self):
        """Get all teams available in a tenant and returns.

            Returns:
                list    --    Returns list with team mails.

            Raises:
                Exception in case if we failed to get the teams from tenant.

        """

        flag, resp = rr.get_request(url=apis['ALL_GROUPS']['url'], status_code=200)
        if flag:
            resp = json.loads(resp.content)
            return self._process_resp_pages(resp, mail=True)
        raise Exception('Failed to get teams from tenant')

    def read_xml(self, file_path, machine_name, user_name=None, password=None):
        """Method to read xml from a file location
                Args:
                    file_path(str):     Full path of the xml file
                    machine_name(str):  Name of the machine
                    user_name(str):     Username of the account having access to machine
                                        (None if the machine is part of Commvault infra)
                    password(str):      Password of the account having access to machine
                                        (None if the machine is part of Commvault infra)

                Returns:
                    OrderedDict of attributes of xml
        """
        machine = Machine(machine_name, commcell_object=self.commcell_object, username=user_name,
                          password=password)
        xml_file_contents = machine.read_file(file_path=file_path)
        xml_file_obj = OrderedDict(parse(xml_file_contents, process_namespaces=True))
        return xml_file_obj

    def get_hostname_and_dir(self):
        """Method to get Hostname and Job Results Directory location for a subclient
            Args:
                It takes no args

            Returns:
                Tuple: Contains hostname and Jr directory
        """

        query = f"select attrVal from app_instanceprop where componentnameid = {self._instance.instance_id} and attrName = 'Proxy Clients' "
        self._csdb.execute(query)
        result = self._csdb.fetch_one_row()
        xml = ET.fromstring(result[0])
        client_id = int(xml.findall('./memberServers/client')[0].attrib['clientId'])
        query = f"select net_hostname, jobResultDir from app_client where id = {client_id}"
        self._csdb.execute(query)
        result = self._csdb.fetch_one_row()
        return result

    def get_folders_in_jr(self, folders_needed, job_id):
        """Method to get the number of folders in the JR directory
        Args:
            folders_needed(int) : Numbers of folders needed in JR directory
            job_id(str)  :   Job ID for which the check is to be made

        Returns:
            True if the check is successful

        Raises:
            Exception if job is running for a long time
        """

        result = self.get_hostname_and_dir()
        job_dir = result[1] + f'\\CV_JobResults\\2\\2\\{job_id}'

        destination_client = WindowsMachine(result[0], self._tc_obj.commcell)

        start_time = time.time()
        while True:
            time.sleep(10)

            if len(destination_client.get_folders_in_path(job_dir)) - 1 >= folders_needed:
                return True

            if (time.time() - start_time) / 60 >= 30:
                raise Exception("Job is running for a very long time")

    def match_delta_token(self, old, username, password, delete_folders_at_end=False):
        """Method to match delta token before and after the job
        Args:
            old(dict) :   Contains TeamsIncrInfo.dat file values before the job
            username(str)   :   Username to access Subclient Directory of remote machine
            password(str)   :   Password of the username to access Subclient Directory of remote machine
            delete_folders_at_end(bool) :   Whether the Teams folders are to be deleted at the end or not

        Returns:
            dict : Contains latest TeamsIncrInfo.dat file values

        """

        def set_dict_values(folder_id, key):
            """Method to set the dictionary values
            Args:
                folder_id(str)  :   Folder currently being processed
                key(str)    :   Key being processed (whether Channel Data or Drive Data)

            Returns:
                None

            Raises:
                Exception if Incremental URL is same before and after the Job

            """

            if folder_id in old:
                if key not in old.get(folder_id):
                    old[folder_id][key] = {}
            else:
                old[folder_id] = {key: {}}

            for row in records:
                if row[0] in old.get(folder_id).get(key):
                    if old.get(folder_id).get(key).get(row[0]) != row[1]:
                        old[folder_id][key][row[0]] = row[1]
                        self.log.info("Incremental URL has changed, check successfull")
                    else:
                        raise Exception("Incremental URL is same, failing")
                else:
                    old[folder_id][key][row[0]] = [row[1]]

        result = self.get_hostname_and_dir()
        subclient_dir = result[1] + '\\CV_JobResults\\iDataAgent\\Cloud Apps Agent\\2\\' + str(self._subclient.subclient_id)

        destination_client = WindowsMachine(result[0], self._tc_obj.commcell)

        folder_list = destination_client.get_folders_in_path(subclient_dir)

        try:

            sqlite_helper_obj = SQLiteHelper(self._tc_obj, destination_client, username, password)
            for folder in folder_list:
                records = sqlite_helper_obj.execute_dat_file_query(folder, file_name="TeamsIncrInfo.dat",
                                                                   query="select channelId, convIncrUrl from ChannelData")
                if records:
                    set_dict_values(folder.split('\\')[-1], "ChannelData")

                records = sqlite_helper_obj.execute_dat_file_query(folder, file_name="TeamsIncrInfo.dat",
                                                                   query="select * from DriveData")
                if records:
                    set_dict_values(folder.split('\\')[-1], "DriveData")

        except Exception as ex:
            self.log.exception(ex)

        finally:
            if delete_folders_at_end:
                for folder in folder_list:
                    destination_client.remove_directory(folder)

        return old

    def out_of_place_restore_to_file_location(self, source_team_mail, dest_client, dest_path, wait_to_complete=True):
        """Restore a team to file location.

                    Args:
                        source_team_mail      (str)      --  The email ID of the team that needs to be restored.
                        dest_client           (str)      --  The name of the client to be restored to.
                        dest_path             (str)      --  The path of the client to be restored to.
                        wait_to_complete      (bool)     --  Wait for job to complete if True.
                    Returns:
                        obj   --  Instance of Restore job.

                    Raises:
                        Exception:
                             If restore failed to run.
                             If response is empty.
                             If response is not success.

                """
        discovered_teams = self.discover()
        source_team = discovered_teams[source_team_mail]

        selected_items = []
        values = []
        try:
            solrhelper_obj = SolrHelper(self)
            response = solrhelper_obj.create_url_and_get_response(
                select_dict={"keyword": f"{source_team['displayName']}"},
                op_params={'rows': '20'})
            response = json.loads(response.content)

            for i in response["response"]["docs"]:
                if i['TeamsItemName'] in ["Posts", "Files"] and i["TeamsItemType"] == 15 and i["slevel_Url_2"] != "General":
                    selected_items.append({
                        "itemId": i["contentid"],
                        "path": i["Url"],
                        "itemType": 15,
                        "isDirectory": True
                    }
                    )
                    values.append(i["contentid"])
        except Exception as ex:
            self.log.exception(ex)
        restore_job = self._subclient.restore_out_of_place_to_file_location(source_team_mail, dest_client, dest_path,
                                                                            selected_items, values)
        if wait_to_complete and not restore_job.wait_for_completion():
            raise Exception(f"Failed to run restore {restore_job.job_id}")
        return restore_job

    def compare_channels_files_folder(self, source_channel, destination_channel, cross_tenant_details=None):

        """compare two channels files folder structure or two document libraries.

                Args:
                    source_channel        (obj or dict)   --  Instance of channel object or dict of document library
                    destination_channel   (obj or dict)   --  Instance of channel object or dict of document library
                    cross_tenant_details  (dict)  --  Details of a destination client
                Returns:
                    True if both channels files folder structure is same otherwise false.

                        """

        if isinstance(source_channel, Channel):
            source_items = [source_channel.sharepoint_drives['root_id']]
            destination_items = [destination_channel.sharepoint_drives['root_id']]
            src_drive_id = source_channel.sharepoint_drives['driveId']
            dest_drive_id = destination_channel.sharepoint_drives['driveId']
        else:
            source_items = [source_channel['root_id']]
            destination_items = [destination_channel['root_id']]
            src_drive_id = source_channel['drive_id']
            dest_drive_id = destination_channel['drive_id']

        # COMPARE PARENT ITEMS LENGTH
        while len(source_items) == len(destination_items) and len(source_items) > 0:
            source_temp_items = []
            destination_temp_items = []
            source_channel_hash = []
            destination_channel_hash = []
            for i in range(len(source_items)):
                source_channel_names = []
                destination_channel_names = []
                source = self.executor.submit(self.get_children_in_folder, src_drive_id, source_items[i])
                destination = self.executor.submit(self.get_children_in_folder, dest_drive_id, destination_items[i],
                                                   cross_tenant_details=cross_tenant_details)
                source = source.result()
                destination = destination.result()
                for j in source:
                    if j['name'] == 'General':
                        continue
                    source_temp_items.append(j['id'])
                    source_channel_names.append(j['name'])
                    source_channel_hash.append(j['file']['hashes']['quickXorHash'] if j['file'] != {} else '0')
                for j in destination:
                    if j['name'] == 'General':
                        continue
                    destination_temp_items.append(j['id'])
                    destination_channel_names.append(j['name'])
                    destination_channel_hash.append(j['file']['hashes']['quickXorHash'] if j['file'] != {} else '0')
                # COMPARE CHILDREN NAMES AND THEIR HASH VALUE FOR FILES AND FOLDERS
                if (source_channel_names != destination_channel_names) or (destination_channel_hash
                                                                           != source_channel_hash):
                    return False
            source_items = []
            destination_items = []
            for i in range(len(source_temp_items)):
                if '.' not in source_channel_names[i]:
                    source_items.append(source_temp_items[i])
                    destination_items.append(destination_temp_items[i])
        return True

    def out_of_place_files_restore(self, source_team_mail, destination_team_mail, channel, files,
                                   wait_to_complete=True):
        """Restore  files to another team

                    Args:
                        source_team_mail         (str)      --  The email ID of the team that needs to be restored.
                        destination_team_mail    (str)      --  The name of the client to be restored to.
                        channel                  (obj)      --  The object of the channel to be restored.
                        files                    (list)     --  List of file names that needs to be restored.
                        wait_to_complete         (bool)     --  Wait for job to complete if True.
                    Returns:
                        obj   --  Instance of Restore job.

                    Raises:
                        Exception:
                            If restore failed to run.
                            If response is empty.
                            If response is not success.

                """

        discovered_teams = self.discover()
        source_team = discovered_teams[source_team_mail]

        selected_items = []
        selected_files = []
        values = []
        try:
            solrhelper_obj = SolrHelper(self)
            response = solrhelper_obj.create_url_and_get_response(
                select_dict={"keyword": f"{source_team['displayName']}"},
                op_params={'rows': '40'})
            response = json.loads(response.content)

            for i in response["response"]["docs"]:
                if i["TeamsItemType"] == 10 and i['TeamsItemName'] in files:
                    selected_files.append(
                        {
                            "itemName": i['TeamsItemName'],
                            "itemType": "File"
                        }
                    )
                    selected_items.append({
                        "itemId": i["contentid"],
                        "path": i["Url"],
                        "itemType": 10,
                        "isDirectory": False
                    }
                    )
                    values.append(i["contentid"])
        except Exception as ex:
            self.log.exception(ex)
        restore_job = self._subclient.restore_files_to_out_of_place(source_team_mail, destination_team_mail, channel,
                                                                    selected_items, values, selected_files)
        if wait_to_complete and not restore_job.wait_for_completion():
            raise Exception(f"Failed to run restore {restore_job.job_id}")
        return restore_job

    def create_shared_channel(self, team, name=None, description=const.CHANNEL_DESCRIPTION, owners=None, members=None,
                              cross_tenant_details=None):
        """Creates a shared channel.
            Args:
                team        (obj)   --  Team under which standard channel needs to be created.
                name        (str)   --  Name of standard channel
                description (str)   --  Description for channel.
                owners      (list)  --  List of display names of users.
                members     (list)  --  List of display names of users.
                cross_tenant_details    (dict)  --  Details of Cross Tenant
                    Default:    None

            Returns:
                obj --  Instance of Channel.

            Raises:
                Exception if the team is NOT an instance of Team.
        """
        if isinstance(team, Team):
            time.sleep(5)
            owners = list(map(Users.get_user, [owners[0]] if owners else [const.MEMBERS[0]]))
            members = list(map(Users.get_user, members[1:] if members else const.MEMBERS[1:]))
            name = name if name else const.SRD_CHANNEL_NAME
            self.log.info(f"\t\tCreating shared channel {name}")
            return team.create_channel(name, shared=True, description=description, owners=owners, members=members,
                                       cross_tenant_details=cross_tenant_details)
        raise Exception("Argument 'team' must be an instance of 'Team'.")

    def restore_to_original_location(self, team_mail, skip_items=True, restore_posts_as_html=False, wait_to_complete=True):
        """Restore a team to original location.
                            Args:
                                team_mail                (str)   --  The email ID of the team that needs to be restored.
                                skip_items                (bool)  --  To skip the items.
                                     Default - True
                                restore_posts_as_html  (bool)  --  To restore pots as html under Files tab.
                                     Default - False
                                wait_to_complete    (bool)  -- To wait for the job completion.
                                     Default - True

                            Returns:
                                obj   --  Instance of job.

                            Raises:
                                Exception:
                                    If restore failed to run.
                        """

        restore_job = self._subclient.restore_to_original_location(team_mail, skip_items=skip_items,
                                                       restore_posts_as_html=restore_posts_as_html)
        if wait_to_complete and not restore_job.wait_for_completion():
            raise Exception(f"Failed to run restore {restore_job.job_id}")
        return restore_job

    def get_tabs_in_the_channel(self, team, channel, cross_tenant_details=None):

        """Get tabs in a channel.
                    Args:
                        team    (obj)   --  Instance of a team.
                        channel (obj)   --  Instance of Channel to which the image should be uploaded.
                        cross_tenant_details    (dict)  --  Details of Cross Tenant
                            Default:    None

                    Returns:
                        List of tab names under channel
                """

        flag, resp = rr.get_request(url=apis['GET_TABS']['url'].format(team_id=team.id, channel_id=channel.channel_id),
                                    status_code=200, cross_tenant_details=cross_tenant_details)
        tabs = []
        retry = 3
        while retry > 0 and not flag:
            time.sleep(40)
            flag, resp = rr.get_request(url=apis['GET_TABS']['url'].format(team_id=team.id,
                                                                           channel_id=channel.channel_id),
                                        status_code=200, cross_tenant_details=cross_tenant_details)
            retry -= 1
        if flag:
            resp = json.loads(resp.content)
            for i in resp['value']:
                tabs.append(i['displayName'])
            return sorted(tabs)

        raise Exception('Failed to get tabs of a channel.')

    def compare_document_libraries_of_teams(self, src_team, dts_team):
        """compare two teams document libraries.
                Args:
                    src_team        (obj)   --  Instance of team object.
                    dts_team        (obj)   --  Instance of team object.
                Returns:
                    True if both teams documents libraries were same otherwise false.

                        """

        src_document_libraries = src_team.document_libraries
        dts_document_libraries = dts_team.document_libraries
        if sorted(list(src_document_libraries.keys())) == sorted(list(dts_document_libraries.keys())):
            for library in src_document_libraries:
                if not self.compare_channels_files_folder(src_document_libraries[library],
                                                          dts_document_libraries[library]):
                    self.log.info(f"Files or Folders did not match for {library} document library for both teams")
                    return False
        else:
            self.log.info(f"document libraries names did not match for {src_team.mail}, {dts_team.mail}")
            return False
        return True

    def compare_one_note_of_sharepoint_sites(self, src_share_point, dts_share_point):
        """compare two sharepoint site one notes.
                       Args:
                           src_share_point        (obj)   --  Instance of sharepoint object.
                           dts_share_point        (obj)   --  Instance of sharepoint object.
                       Returns:
                           True if both sharepoint site one notes were same otherwise False.

                               """

        # COMPARE NOTE_BOOKS OF TWO SHAREPOINT SITE
        source_notebooks = src_share_point.get_note_books()
        destination_notebooks = dts_share_point.get_note_books()
        if len(source_notebooks) == len(destination_notebooks):
            for notebook in source_notebooks:
                # COMPARE SECTION GROUPS OF TWO NOTEBOOKS
                src_sec_grps = src_share_point.get_section_groups_in_notebook(source_notebooks[notebook]['id'])
                dts_sec_grps = dts_share_point.get_section_groups_in_notebook(destination_notebooks[notebook]['id'])
                if len(src_sec_grps) == len(dts_sec_grps):
                    for sec_grp in src_sec_grps:
                        if not self.compare_section_groups(src_sec_grps[sec_grp]['id'], dts_sec_grps[sec_grp]['id'],
                                                           src_share_point, dts_share_point):
                            self.log.info(f"{sec_grp} DID NOT MATCHED")
                            return False
                else:
                    self.log.info(f"SECTION GROUPS DID NOT MATCHED FOR {notebook}")
                    return False
                # COMPARE SECTIONS OF TWO NOTEBOOKS
                src_sections = src_share_point.get_sections_in_notebook(source_notebooks[notebook]['id'])
                dts_sections = dts_share_point.get_sections_in_notebook(destination_notebooks[notebook]['id'])
                if len(src_sections) == len(dts_sections):
                    for section in src_sections:
                        if not self.compare_sections(src_sections[section]['id'], dts_sections[section]['id'],
                                                     src_share_point,
                                                     dts_share_point):
                            self.log.info(f"{section} DID NOT MATCHED")
                            return False
                else:
                    self.log.info(f"SECTIONS DID NOT MATCHED FOR {notebook}")
                    return False
        else:
            self.log.info("NOTE_BOOKS DID NOT MATCHED")
            return False
        return True

    def compare_sections(self, section1, section2, src_share_point, dts_share_point):
        """compare two Sections.
                       Args:
                           section1       (int)    -- Section Id.
                           section2       (int)   --   Section Id.
                           src_share_point       (obj)   --  Instance of sharepoint object.
                           dts_share_point        (obj)   --  Instance of sharepoint object.
                       Returns:
                           True if both Sections were same otherwise False.

                               """
        src_pages = sorted(list(src_share_point.get_pages_in_section(section1).keys()))
        dts_pages = sorted(list(dts_share_point.get_pages_in_section(section2).keys()))
        if src_pages != dts_pages:
            self.log.info("SECTION PAGES DID NOT MATCHED")
            return False
        return True

    def compare_section_groups(self, section_grp1, section_grp2, src_share_point, dts_share_point):
        """compare two section groups.
                       Args:
                           section_grp1   (int)    -- Section group id.
                           section_grp2   (int)    -- Section group id.
                           src_share_point        (obj)   --  Instance of sharepoint object.
                           dts_share_point        (obj)   --  Instance of sharepoint object.
                       Returns:
                           True if both section groups were same otherwise False.

                               """
        src_sections = src_share_point.get_sections_in_section_group(section_grp1)
        dts_sections = dts_share_point.get_sections_in_section_group(section_grp2)
        if len(src_sections) == len(dts_sections):
            for section in src_sections:
                if not self.compare_sections(src_sections[section]['id'], dts_sections[section]['id'], src_share_point,
                                             dts_share_point):
                    self.log.info(f"{section} DID NOT MATCHED")
                    return False
        else:
            self.log.info("SECTIONS DID NOT MATCHED")
            return False
        return True

    @staticmethod
    def create_chat(members=const.MEMBERS, topic=None, c_type=chat_type.GROUP):
        """Create a Chat.
               Args:
                   members    (list)   --  List of principal names of a members.
                   Default :  const members
                   topic       (str)   --   Name of the Chat.
                    Default : None
                   c_type    (enum)     --  Type of the Chat to be created.
               Returns:
                   chat_id      (str)   --  ID of the created Chat.

               Raises:
                   Exception in case we failed to create a chat.
           """

        chat = ""
        if c_type == chat_type.GROUP:
            chat = "group"
        else:
            chat = "oneOnOne"

        if len(members) < 2:
            raise Exception("Members length should be greater than ONE")

        if topic is None:
            topic = ""
            count = 0
            for email in members:
                if count > 2:
                    topic += "+"+str(len(members)-3)
                    break
                topic += email[:email.find("@")]+" "
                count += 1
        api = apis['CREATE_CHAT']['url']
        owners = [json.loads(apis['CHANNEL']['PRIVATE']['owners'].format(id=o)) for o in members]
        data = {
            "chatType": chat,
            "topic": topic,
            "members": owners
        }

        flag, resp = rr.post_request(url=api, data=data, delegated=True, status_code=201)
        retry = 5
        while not flag and retry > 0:
            flag, resp = rr.post_request(url=api, data=data, delegated=True, status_code=201)
            retry -= 1
        if not flag:
            raise Exception(f"Failed to create a Chat, reason {resp.reason}.")
        return json.loads(resp.content)['id']

    def enable_chat_backup(self):
        """Enable User Chat Backup
            Returns:
                response      (dict)   --  returns dict of instance properties.
        """

        instance_prop_json = self._instance._get_instance_properties_json()
        instance_prop_json['instanceProperties']['cloudAppsInstance']['v2CloudAppsInstance']['advanceSettings'][
            'isPersonalChatOperationsEnabled'] = True
        return self._instance.update_instance(instance_prop_json)

    def disable_chat_backup(self):
        """Disable User Chat Backup
            Returns:
                response      (dict)   --  returns dict of instance properties.
        """
        instance_prop_json = self._instance._get_instance_properties_json()
        instance_prop_json['instanceProperties']['cloudAppsInstance']['v2CloudAppsInstance']['advanceSettings'][
            'isPersonalChatOperationsEnabled'] = False
        return self._instance.update_instance(instance_prop_json)

    def get_all_users_in_tenant(self):
        """Get all users available in a tenant and returns.

            Returns:
                list    --    Returns list with users mails.

            Raises:
                Exception in case if we failed to get the users from tenant.

        """

        flag, resp = rr.get_request(url=apis['USERS']['url'], status_code=200)
        if flag:
            resp = json.loads(resp.content)
            return self._process_resp_pages(resp, user_principal_name=True)
        raise Exception('Failed to get users from tenant')

    def compare_buckets(self, source_bucket_id, destination_bucket_id):
        """compare buckets"""
        source_tasks = self.executor.submit(Planner.get_tasks_in_bucket, source_bucket_id)
        destination_tasks = self.executor.submit(Planner.get_tasks_in_bucket, destination_bucket_id)
        source_tasks = source_tasks.result()
        destination_tasks = destination_tasks.result()
        source_tasks_names = list(source_tasks.keys())
        destination_tasks_names = list(destination_tasks.keys())
        source_tasks_names.sort()
        destination_tasks_names.sort()
        if len(source_tasks_names) != len(destination_tasks_names):
            self.log.info("Tasks count not matched for buckets")
            return False
        else:
            if source_tasks_names != destination_tasks_names:
                self.log.info("Tasks name not matched for buckets")
        return True

    def compare_plans(self, source_plan_id, destination_plan_id):
        """compare plans"""
        source_buckets = self.executor.submit(Planner.get_buckets_in_plan, source_plan_id)
        destination_buckets = self.executor.submit(Planner.get_buckets_in_plan, destination_plan_id)
        source_buckets = source_buckets.result()
        destination_buckets = destination_buckets.result()
        source_buckets_names = list(source_buckets.keys())
        destination_buckets_names = list(destination_buckets.keys())
        source_buckets_names.sort()
        destination_buckets_names.sort()
        if len(source_buckets_names) != len(destination_buckets_names):
            self.log.info("Buckets count not matched for plans")
            return False
        else:
            if source_buckets_names != destination_buckets_names:
                self.log.info("Bucket names not matched for plans")
                return False
        for bucket in source_buckets_names:
            if not self.compare_buckets(source_buckets[bucket]['id'], destination_buckets[bucket]['id']):
                self.log.info(f"comparison failed for {bucket}")
                return False
        return True

    def compare_teams_plans(self, source_team_id, destination_team_id, exclude_default_plan=True):
        """compare teams plans"""
        source_planner_helper = Planner(source_team_id)
        destination_planner_helper = Planner(destination_team_id)
        source_plans = self.executor.submit(source_planner_helper.get_plans_in_the_group)
        destination_plans = self.executor.submit(destination_planner_helper.get_plans_in_the_group)
        source_plans = source_plans.result()
        destination_plans = destination_plans.result()
        source_plans_names = list(source_plans.keys())
        destination_plans_names = list(destination_plans.keys())
        default_plan_name = "Tasks"
        if exclude_default_plan:
            if default_plan_name in source_plans_names:
                source_plans_names.remove(default_plan_name)
            if default_plan_name in destination_plans_names:
                destination_plans_names.remove(default_plan_name)
        source_plans_names.sort()
        destination_plans_names.sort()
        if len(source_plans_names) != len(destination_plans_names):
            self.log.info("plans count not matched")
            return False
        else:
            if source_plans_names != destination_plans_names:
                self.log.info("plan names not matched")
                return False
        for plan in source_plans_names:
            if not self.compare_plans(source_plans[plan]['id'], destination_plans[plan]['id']):
                self.log.info(f"comparison failed for {plan}")
                return False
        return True



