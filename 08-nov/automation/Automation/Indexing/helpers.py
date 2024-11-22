# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main module which contains helpers to get indexing related information

IndexingHelpers: Helper class to get indexing related information and operations

IndexingHelpers:

    __init__()                  --  Initializes the indexing helper class

    get_index_cache()           --  Gets the index cache for the given media agent

    get_index_backup_clients()  --  Gets the index backup client names for the
    given entity (backupset/subclient)

    get_items_from_browse_response()    --  Reads the browse/find response and prepares a list of
    items found in it

    get_quota_size()            --  Gets the Application Size property for the given
    backupset/subclient

    get_agent_indexing_version()    --  Gets the Indexing version for the given client and the agent

    get_agent_indexing_level()  --  Gets the Indexing level of the agent on whether it is running in subclient level
    index or backupset level index

    get_index_cache_config()    --  Gets the index cache config details like min space, alert space etc

    get_checkpoint_by_job()      --  Get eligible checkpoint for job

    get_items_in_index()        --  Does a aggregate count query to get the number of items in the subclient

    get_rfc_server()            --  Returns the rfc server for the job

    set_agent_indexing_level()  --  Sets the Indexing level for the agent to backupset level or subclient level

    set_agent_indexing_version()    --  Sets the indexing version for the given client

    run_index_backup()      --  Runs index backup job for the given index backup subclient

    verify_checkpoint()     --  Verifies if checkpoint happened for the given DB by the given
    index backup job id

    verify_quota_size()     --  Validates the quota size of the DB calculated against the testdata
    on the disk

    verify_extents_files_flag()     --  Performs find operation and verifies if files above given
    threshold have extents

    verify_acl_only_flag()  --  Performs find operation and verifies if files have ACL only flag

    verify_pruned_jobs()         --  Reads the index table and verifies if the expected jobs are marked pruned or not

"""

import xmltodict

from cvpysdk.client import Client
from cvpysdk.backupset import Backupset
from cvpysdk.subclient import Subclient

from AutomationUtils import logger
from AutomationUtils import commonutils
from AutomationUtils.database_helper import get_csdb
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.options_selector import OptionsSelector

from Indexing.misc import MetallicConfig


class IndexingHelpers(object):
    """This is a helper class for indexing related information and operations"""

    def __init__(self, commcell):
        """Initializes the Indexing helper class"""

        self.log = logger.get_log()
        self._commcell = commcell
        self._cs_db = get_csdb()

        metallic = MetallicConfig(self._commcell)
        admin_cc = self._commcell
        if metallic.is_configured:
            self._cs_db = metallic.csdb
            admin_cc = metallic.metallic_admin_cc

        self._cv_ops = CommonUtils(self._commcell)
        self._option_selector = OptionsSelector(admin_cc)

    def get_index_cache(self, media_agent):
        """Gets the index cache for the given media agent

            Args:
                media_agent     (obj)   --      The media agent CvPySDK client object

            Returns:
                (str)       -       The index cache of the media agent

        """

        if not isinstance(media_agent, Client):
            raise Exception('Please provide MA client object to get index cache')

        ma_id = media_agent.client_id

        self._cs_db.execute(
            """
                select attrVal from app_clientprop where
                componentNameId = {0} and
                attrName = 'Idx: cache path'
            """.format(ma_id)
        )

        if not self._cs_db.rows:
            raise Exception('Unable to get IndexCache directory for the MA [{0}]'.format(
                media_agent.client_name
            ))

        return self._cs_db.fetch_one_row()[0]

    def get_index_backup_clients(self, entity_obj):
        """Gets the index backup client names for the given entity (backupset/subclient)

            Args:
                entity_obj     (obj)   --      The CvPySDK object of the backupset/subclient

            Returns:
                (list)       -       List of index backup client names

        """

        client_names = []

        if isinstance(entity_obj, Backupset):

            self.log.info('Getting index backup clients for backupset [{0}]'.format(
                entity_obj.backupset_name
            ))

            self._cs_db.execute("""
                select distinct sp.name from archGroup sp
                join app_application sc on sc.dataArchGrpID = sp.id
                join APP_BackupSetName bkset on bkset.id = sc.backupSet

                where sc.subclientStatus = 0
                and bkset.id = '{0}'
            """.format(entity_obj.backupset_id))

            for row in self._cs_db.rows:
                client_names.append(row[0])

        elif isinstance(entity_obj, Subclient):

            self.log.info('Getting index backup client for subclient [{0}]'.format(
                entity_obj.subclient_name
            ))

            client_names.append(entity_obj.storage_policy)

        if not client_names:
            raise Exception('No subclients found in the backupset to get index backup client')

        return [name + '_IndexServer' for name in client_names]

    def get_items_from_browse_response(self, response):
        """Reads the browse/find response and prepares a list of items found in it

            Args:
                response    (list)   --  The browse/find response obtained with _raw_response
                set to True during the browse request

            Returns:
                List of items (file/folder) with all the metadata

        """

        all_items = []

        for browse_response in response['browseResponses']:
            if 'browseResult' in browse_response:
                if ('queryId' in browse_response['browseResult']
                        and (browse_response['browseResult']['queryId'] == 'dataQuery'
                             or browse_response['browseResult']['queryId'] == '0')):

                    browse_items = browse_response['browseResult'].get('dataResultSet', list())

                    self.log.info('Items in results [{0}]'.format(len(browse_items)))

                    for item in browse_items:
                        all_items.append(item)

        return all_items

    def get_quota_size(self, backupset_obj=None, subclient_obj=None):
        """Gets the Application Size property for the given backupset/subclient

            Args:
                backupset_obj   (obj)   --  The backupset obj to get size for

                subclient_obj   (obj)   --  The subclient obj to get size for

            Returns:
                (float) - The quota size for the given entity

        """

        quota_size = 0

        if backupset_obj is not None:
            self._cs_db.execute("""
                select attrVal from app_backupsetprop where componentNameId={0} and 
                attrname = 'Application Size'
            """.format(backupset_obj.backupset_id))

            quota_size = self._cs_db.fetch_one_row()[0]

        if subclient_obj is not None:
            self._cs_db.execute("""
                select attrVal from APP_SubClientProp where componentNameId={0} and 
                attrname = 'Application Size'
            """.format(subclient_obj.subclient_id))

            quota_size = self._cs_db.fetch_one_row()[0]

        if not quota_size:
            self.log.error('Cannot get quota size for the given entity')
            return 0.0

        return float(quota_size)

    def get_agent_indexing_version(self, client_obj, agent_short_name=None):
        """Gets the Indexing version for the given client and the agent

            Args:
                client_obj          (obj)   --      The CvPySDK client object to check indexing mode for

                agent_short_name    (str)   --      The internal agent short name to check indexing mode.
                Example - VSA for VSA iDA. None for Windows FS iDA. Refer GetIndexingV2PropNameByAppType.func
                file for the IndexingV2_* name

            Returns:
                (str)   -   v1/v2 based on the indexing version of the agent.

        """

        client_id = client_obj.client_id
        prop_name = 'IndexingV2' if agent_short_name is None else 'IndexingV2_' + agent_short_name

        self._cs_db.execute("""
            select attrVal from app_clientprop where componentNameId = '{0}' and attrname = '{1}'
        """.format(client_id, prop_name))

        result = self._cs_db.fetch_one_row()[0]

        if result == '0':
            return 'v1'
        else:
            return 'v2'

    def get_agent_indexing_level(self, agent_obj):
        """Gets the Indexing level of the agent on whether it is running in subclient level index or
        backupset level index

            Args:
                agent_obj       (obj)   --      The CvPySDK agent object to check the indexing level for

            Returns:
                (str) - subclient/backupset based on the indexing level set on the agent.

        """

        client_id = agent_obj._client_object.client_id
        agent_id = agent_obj.agent_id

        self._cs_db.execute("""
            select attrVal from app_idaprop idaprop
            join app_idaname idaname on idaprop.componentNameId = idaname.id
            where idaname.clientId = {0} and idaname.appTypeId = {1}
            and idaprop.attrname = 'Subclient Index'
        """.format(client_id, agent_id))

        output = self._cs_db.fetch_one_row()[0]

        if output == '1':
            return 'subclient'
        else:
            return 'backupset'

    def get_index_cache_config(self, client_obj):
        """Gets the index cache config details like min space, alert space etc

            Args:
                client_obj      (obj)       --      The client to get the index cache details for

            Returns:
                (dict)      --      Below index cache configuration details
                - min_space
                - alert_space
                - index_cache_path
                - age_days
                - cleanup_percent

        """

        self._cs_db.execute("""
        SELECT  [Idx: min space] as 'min_space', [Idx: alert space] as 'alert_space', 
        [Idx: cache path] as 'index_cache_path', [Idx: age days] as 'age_days',
        [Idx: cleanup percent] as 'cleanup_percent'
            FROM (
                 SELECT componentNameId, attrname, attrval FROM app_clientprop
                 where attrname like '%Idx:%' and componentNameId = {0}
                ) as source
            PIVOT (
             MAX(attrVal) FOR attrname IN ([Idx: min space], [Idx: alert space], 
             [Idx: cache path], [Idx: age days], [Idx: cleanup percent])
            ) as target
        """.format(client_obj.client_id))

        return self._cs_db.fetch_one_row(named_columns=True)[0]

    def get_checkpoint_by_job(self, index_db, job):
        """Get eligible checkpoint for job

        Eligible checkpoints: checkpoint_start_time <= job_start_time < checkpoint_end_time
        Precedence order for eligible checkpoints:
            1 - Already restored checkpoint
            2 - Most recent checkpoint

            Args:
                index_db   (CTreeDB)          --    Object of class CTreeDB
                job       (cvpysdk.job.Job)   --    Object of class Job to find checkpoint for

            Returns:
                (dict) - dictionary with checkpoint attributes

        """

        checkpoints = index_db.get_index_db_checkpoints()
        job_start_time = job._summary['jobStartTime']

        exp_checkpoint = None
        for checkpoint in checkpoints:

            if checkpoint['startTime'] == 'Null':
                continue

            if int(checkpoint['startTime']) <= job_start_time < int(checkpoint['endTime']):
                checkpoint_db_name = f"{checkpoint['dbName']}_{checkpoint['commCellId']}_" \
                                     f"{checkpoint['startTime']}_{checkpoint['endTime']}"
                checkpoint_path = index_db.isc_machine.os_sep.join([index_db.backupset_path, checkpoint_db_name])
                if exp_checkpoint is None:
                    exp_checkpoint = checkpoint
                if index_db.isc_machine.check_directory_exists(checkpoint_path):
                    exp_checkpoint = checkpoint
                    break

        return exp_checkpoint

    def get_items_in_index(self, entity_obj):
        """Does a aggregate count query to get the number of items in the subclient

            Args:
                entity_obj      (obj)   --      The CvPySDK backupset/subclient object

            Returns:
                (int)   --  The number of items in the backupset/subclient. 0 if unable to fetch browse results.

            Raises:
                Exception, if the entity_obj is not of the required type.

        """

        if not isinstance(entity_obj, Backupset) and not isinstance(entity_obj, Subclient):
            raise Exception('Entity object must be cvpysdk backupset/subclient object')

        dummy_var, response = entity_obj.find({
            'path': '/**/*',
            '_custom_queries': [{
                'type': 'AGGREGATE',
                'queryId': 'count_query',
                'aggrParam': {
                    'aggrType': 'COUNT'
                }
            }],
            '_raw_response': True
        })

        count = 0
        self.log.info(f'Count query response: [{response}]')

        for browse_response in response['browseResponses']:
            if 'browseResult' in browse_response:
                browse_result = browse_response['browseResult']
                count = browse_result['aggrResultSet'][0]['result']

        return commonutils.get_int(count, default=0)

    def get_rfc_server(self, job_id):
        """ To get the rfc server of a job
                Args:
                        job_id         (int)   --   Job id of the backup job who's RFC server is to be fetched

                    Returns:
                        (obj)      --      RFC server client obj for the given job
        """

        get_rfc_info_xml = f"select attributeValue from jmjoboptions where attributeid = 85 and jobid = '{job_id}'"
        self._cs_db.execute(get_rfc_info_xml)
        rows_result = self._cs_db.fetch_all_rows()
        if len(rows_result) != 0:
            rfc_info_xml = rows_result[0][0]
        else:
            raise Exception(f'Job: {job_id} has no RFC XML attribute created')

        if not rfc_info_xml:
            raise Exception('Failed to fetch RFC XML')
        rfc_info_dict = xmltodict.parse(rfc_info_xml)
        rfc_server_name = rfc_info_dict['App_JobOptionsRFCDetails']['@clientName_RFCServer']
        if not rfc_server_name:
            raise Exception('Failed to fetch RFC server from XML')
        rfc_server = self._commcell.clients.get(rfc_server_name)
        return rfc_server

    def set_agent_indexing_level(self, agent_obj, level='backupset'):
        """Sets the Indexing level for the agent to backupset level or subclient level

            Args:
                agent_obj       (obj)       --      The CVPySDK agent object to set the indexing level for

                level           (str)       --      The indexing level to set on the agent

            Returns:
                (bool)      --      True/False upon successful/failed operation respectively

        """

        client_id = agent_obj._client_object.client_id
        agent_id = agent_obj.agent_id
        prop_val = '1' if level.lower() == 'subclient' else '0'

        try:
            self._option_selector.update_commserve_db("""
                declare @prop_id as int;

                select @prop_id = idaprop.id from app_idaprop idaprop
                join app_idaname idaname on idaprop.componentNameId = idaname.id
                where idaname.clientId = '{0}' and idaname.appTypeId = '{1}'
                and idaprop.attrname = 'Subclient Index'

                if @prop_id is not null
                begin
                    select @prop_id
                    update app_idaprop set attrval = '{2}' where id = @prop_id
                end
            """.format(client_id, agent_id, prop_val))
        except Exception as e:
            self.log.exception(e)
            return False

        return True

    def set_agent_indexing_version(self, version, client_obj, agent_short_name=None):
        """Sets the indexing version for the given client

            Args:
                version             (str)   --      The version of the client to set. Allowed values v1 and v2

                client_obj          (obj)   --      The CvPySDK client object to check indexing mode for

                agent_short_name    (str)   --      The internal agent short name to check indexing mode.
                Example - VSA for VSA iDA. None for Windows FS iDA. Refer GetIndexingV2PropNameByAppType.func
                file for the IndexingV2_* name. (Case sensitive)

            Returns:
                (bool)      --      True on successful change, False otherwise.

        """

        client_name = client_obj.client_name
        version = version.lower()

        if version == 'v1':

            self.log.info('Moving client [%s] to V1 mode', client_name)

            self._option_selector.update_commserve_db(f"""
                update app_clientprop set attrVal = 0, created = 0 
                where id = ( select cprop.id from app_clientprop cprop, app_client client 
                    where client.id = cprop.componentNameId 
                    and cprop.attrName = 'IndexingV2' 
                    and client.name = '{client_name}'
                )
            """)

            if self.get_agent_indexing_version(client_obj, agent_short_name) == 'v1':
                self.log.info('Client is moved to V1 version successfully')
                return True
            else:
                raise Exception('Client indexing version has not updated to [%s]', version)

        elif version == 'v2':

            self.log.info('Moving client [%s] to V2 mode', client_name)

            idx_agent_id_map = {
                '': 1,
                'Oracle': 2,
                'NAS': 3,
                'VSA': 4
            }

            agent_short = '' if agent_short_name is None else agent_short_name
            agent_command_id = idx_agent_id_map.get(agent_short, None)

            if not agent_command_id:
                raise Exception(f'Agent short name [{agent_short}] is invalid. Please map the ID in the function')

            import hashlib
            auth_string = f'SetIndexingV2Property_c={client_name}_{agent_command_id}'
            auth_code = hashlib.md5(auth_string.encode('utf-8')).hexdigest()

            command = f'-sn setindexingv2property.sql -si {auth_code} -si c={client_name} -si {agent_command_id}'

            self.log.info('Running qscript command [%s] auth string [%s]', command, auth_string)
            self._commcell._qoperation_execscript(command)

            if self.get_agent_indexing_version(client_obj, agent_short) == 'v2':
                self.log.info('Client is moved to V2 version successfully')
                return True
            else:
                raise Exception('Client indexing version has not updated to [%s]', version)

        self.log.error('Invalid indexing version [%s]', version)
        return False

    def run_index_backup(self, subclient_obj):
        """Runs index backup job for the given index backup subclient

            Args:
                subclient_obj  (obj)  --  The CvPySDK subclient object of the index backup client

            Returns:
                (obj)       -       The job object of the index backup job which is started

        """

        if not isinstance(subclient_obj, Subclient):
            raise Exception('Please provide subclient object to run index backup job')

        self.log.info('Running index backup for Index backup client [{0}]'.format(
            subclient_obj._client_object.client_name
        ))

        job = subclient_obj.backup('Full')
        self.log.info('Started index backup job [%s]', job.job_id)

        if not job.wait_for_completion():
            raise Exception("Job {0} Failed with {1}".format(job.job_id, job.delay_reason))

        self.log.info('Index backup job [%s] completed successfully', job.job_id)

        return job

    def verify_checkpoint(self, index_backup_job_id, db_guid):
        """Verifies if checkpoint happened for the given DB by the given index backup job id

            Args:
                index_backup_job_id     (int/str)   --      Job ID of the index backup job

                db_guid                 (str)   --          DB GUID to verify checkpoint

            Returns:
                (bool)       -       True, if checkpoint happened for the DB by the given job.
                                     False, otherwise

        """

        self.log.info('Verifying checkpoint for DB [{0}] by job [{1}]'.format(
            db_guid, index_backup_job_id
        ))

        self._cs_db.execute("""
            select isValid from archFile where name like 'IdxCheckPoint_%:{0}'
            and jobid = {1}
        """.format(db_guid, index_backup_job_id))

        if not self._cs_db.rows:
            self.log.error('Checkpoint did not happen for DB')
            return False
        else:
            row = self._cs_db.fetch_one_row()
            if row[0] == '1':
                self.log.info('Checkpoint is successful for DB')
                return True
            else:
                self.log.error('Checkpoint did not happen for DB')
                return False

    def verify_quota_size(self, backupset_obj, cl_machine, threshold=10240000):
        """Validates the quota size of the DB calculated against the testdata on the disk.

            Args:
                backupset_obj       (obj)   --  The CvPySDK backupset object

                cl_machine          (obj)   --  The machine object of the client

                threshold           (int)   --  The difference in size which is acceptable

            Returns:
                True, if quota is validated

            Raises:
                Exception, if quota size ia incorrect

            Note:
                Right now the API only supports verifying quota for the given backupset and not for a subclient.
                This is because when index is at backupset level, we cannot get the quota at subclient level.

        """

        self.log.info('********** VALIDATING QUOTA SIZE CALCULATED **********')

        actual_quota_size = 0
        expected_quota_size = 0
        backupset_obj.subclients.refresh()
        subclients = backupset_obj.subclients.all_subclients

        level = self.get_agent_indexing_level(backupset_obj._agent_object)
        if level == 'backupset':
            actual_quota_size = self.get_quota_size(backupset_obj=backupset_obj)

        for sc_name in subclients:
            sc_obj = backupset_obj.subclients.get(sc_name)
            sc_content = sc_obj.content
            self.log.info(sc_content)

            for path in sc_content:
                if path == '\\':
                    continue

                self.log.info('Getting folder size for path [{0}]'.format(path))
                dir_size = cl_machine.get_folder_size(path, in_bytes=True)
                self.log.info('Folder size of [{0}] is [{1}]'.format(path, dir_size))

                try:
                    dir_size = int(dir_size)
                except ValueError:
                    raise Exception('Got unexpected folder size for path [{0}]'.format(path))

                expected_quota_size += dir_size

            if level == 'subclient':
                self.log.info('Getting quota size set by Indexing from CS DB for subclient [{0}]'.format(sc_name))
                from_db_size = self.get_quota_size(subclient_obj=sc_obj)
                self.log.info('Size from index [{0}]'.format(from_db_size))
                actual_quota_size += int(from_db_size)

        self.log.info('Expected quota size from disk is [{0}]'.format(expected_quota_size))
        self.log.info('Actual quota size computed by Indexing is [{0}]'.format(actual_quota_size))

        diff_size = abs(actual_quota_size - expected_quota_size)

        self.log.info('Difference in quota size is [{0}]'.format(diff_size))

        if diff_size > threshold:
            raise Exception('Difference in quota size [{0}] is more than expected [{1}]'.format(
                diff_size, threshold))

        self.log.info('Quota size difference is under limits. Quota size is validated !')
        return True

    def verify_extents_files_flag(self, entity_obj, threshold_size, file_paths=None):
        """Performs find operation and verifies if files above given threshold have extents

            Args:
                entity_obj      (obj)   --  The backupset/subclient object to do find operation

                threshold_size  (int)   --  The threshold size above which to verify extents for

                file_paths      (str/list)   --  The file/list of files to check the extents flag

            Returns:
                None, if all the expected large files have extents

            Raises:
                Exception, if any large file did not have extent or incorrect number

        """

        if file_paths is not None and isinstance(file_paths, str):
            file_paths = [file_paths]

        dummy_var, response = entity_obj.find({
            'path': '/**/*',
            'show_deleted': True,
            '_raw_response': True
        })

        items = self.get_items_from_browse_response(response)
        extent_files = 0

        self.log.info('Verifying extents for files with size >= [{0}]'.format(threshold_size))

        if len(items) == 0:
            raise Exception('Find results are empty')

        for item in items:
            path = item['path']
            size = item['size']
            item_type = 'directory' if item['flags'].get('directory', False) else 'file'

            if item_type == 'directory':
                continue

            if file_paths is not None and path not in file_paths:
                continue

            if size < threshold_size:

                if 'hasExtents' in item['flags'] and item['flags']['hasExtents']:
                    raise Exception('Smaller file [{0}] has extents information'.format(path))

                continue

            if 'hasExtents' not in item['flags'] or not item['flags']['hasExtents']:
                raise Exception(
                    'Large file [{0}] does not have extents flag. Size [{1}]'.format(path, size))

            if 'fsExtentsContainerMetadata' not in item['advancedData']['browseMetaData']:
                raise Exception(
                    'Large file [{0}] does not have extents metadata.Size[{1}]'.format(path, size))

            extents = item['advancedData']['browseMetaData']['fsExtentsContainerMetadata'][
                'numOfExtents']
            extent_size = item['advancedData']['browseMetaData']['fsExtentsContainerMetadata'][
                'extentSize']
            expected_extents = round(size / extent_size)

            if abs(extents - expected_extents) > 1:
                self.log.error(
                    'Expected extents [{0}] Extents from index [{1}] '
                    'File size [{2}] Extent size [{3}]'.format(
                        expected_extents, extents, size, extent_size
                    ))
                raise Exception(
                    'Less/more number of extents were seen backed up for the large file')

            extent_files += 1

        if extent_files == 0:
            raise Exception('No large files were found in the response')
        else:
            self.log.info('Verified that [{0}] large files have extent info in Index'.format(
                extent_files))

    def verify_acl_only_flag(self, entity_obj, file_paths):
        """Performs find operation and verifies if files have ACL only flag

            Args:
                entity_obj      (obj)   --  The backupset/subclient object to do find operation

                file_paths      (str/list)   --  The file/list of files to check the ACL only flag

            Returns:
                None, if all the expected large files have extents

            Raises:
                Exception, if any large file did not have extent or incorrect number
        """

        if isinstance(file_paths, str):
            file_paths = [file_paths]

        dummy_var, response = entity_obj.find({
            'path': '/**/*',
            'show_deleted': True,
            '_raw_response': True
        })

        items = self.get_items_from_browse_response(response)
        flag = False

        if len(items) == 0:
            raise Exception('Find results are empty')

        for item in items:
            path = item['path']

            if path not in file_paths:
                continue

            if 'aclOnlyContainer' not in item['flags'] or not item['flags']['aclOnlyContainer']:
                raise Exception('File [{0}] does not have aclOnly flag'.format(path))

            if 'hasExtents' not in item['flags'] or not item['flags']['hasExtents']:
                raise Exception('File has ACL flag but does not have extents flag [{0}]'.format(
                    path
                ))

            if 'fsExtentsContainerMetadata' not in item['advancedData']['browseMetaData']:
                raise Exception(
                    'File [{0}] does not have extents metadata.'.format(path))

            self.log.info('Verified file [{0}] is ACL only version'.format(path))
            flag = True

        if not flag:
            raise Exception('No files had ACL only flag set')

        self.log.info('All given files have ACL only flag.')

    def verify_pruned_jobs(self, db_obj, expected_pruned_jobs, refresh=False):
        """Reads the index table and verifies if the expected jobs are marked pruned or not

                Args:
                    db_obj                  (obj)   --  The Ctree DB object of the entity

                    expected_pruned_jobs    (list)  --  List of backup job IDs expected to be pruned.

                    refresh                 (bool)  --  Decide whether to re-export the DB after any changes to the DB

                Returns:
                    None

                Raises:
                    Exception       --      When the jobs are marked pruned incorrectly.

        """

        if refresh and db_obj.exported_db:
            self.log.info('********** Refreshing index DB **********')
            db_obj.exported_db.cleanup()
            db_obj.exported_db.export()

        image_table = db_obj.get_table(table='ImageTable')
        self.log.info(image_table.rows)

        pruned_jobs = []
        pruned_image_ids = []
        afile_image_ids = []

        for row in image_table.rows:
            if row['Flags'] == '132':
                pruned_jobs.append(row['JobId'])
                pruned_image_ids.append(row['ImageId'])

        self.log.info(f'Expected pruned jobs: {expected_pruned_jobs}')
        self.log.info(f'Actual pruned jobs: {pruned_jobs}')

        if set(expected_pruned_jobs) == set(pruned_jobs):
            self.log.info('Jobs are pruned in index as expected')
        else:
            raise Exception('Incorrect jobs are pruned. Please check.')

        self.log.info('********** Checking archive file table for pruned flag **********')

        afile_table = db_obj.get_table(table='ArchiveFileTable')
        self.log.info(afile_table.rows)

        for row in afile_table.rows:
            if row['IdxFlags'] == '2':
                afile_image_ids.append(row['ImageId'])

        self.log.info(f'Actual pruned afile image IDs: {afile_image_ids}')
        self.log.info(f'Expected pruned afile image IDs: {pruned_image_ids}')

        if set(pruned_image_ids) == set(afile_image_ids):
            self.log.info('********** Afiles are marked pruned as expected **********')
        else:
            raise Exception('Afiles are not marked correctly in the afile table')

    def verify_rfc_backup(self, job_id):
        """ To verify if the rfc arch file for a job exists
             Args:

                    job_id      (str)   --   Job ID of the job

         """

        self.log.info('Checking if RFC afile is present for job: %s', job_id)
        query = "SELECT * FROM archFile WHERE fileType = 7 AND isValid = 1 AND jobId =" + job_id
        self._cs_db.execute(query)
        row = self._cs_db.fetch_one_row()
        if not row[0]:
            raise Exception(f'Job ID {job_id} did not contain RFC_AFILE')

        self.log.info('RFC afile is created for job: %s', job_id)
        self.log.info('Backup of RFC files verified for child job %s', job_id)
