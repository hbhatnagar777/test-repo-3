# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ---------------------------------------------------------------------------

"""Helper file for performing update operations

Buildhelper: Helper class to perform install operations.

Buildhelper:

    create_db_object() -- Creates and returns a database object for interacting with MSSQL databases.

    updatecenter_db_execute() -- Creates a database object, executes the query, and returns the results.

    get_build_id() --     Retrieves the build ID based on the installed service pack number, transaction number, and revision number.

    updatePrecertStatus() --  Updates the pre-certification status of the given list of updates.

"""
from AutomationUtils import config
from AutomationUtils import logger
from AutomationUtils import database_helper
from Install.installer_constants import BATCHBUILD_CURRENTBATCHSTAGE, BATCHBUILD_PRECERT_BATCH, BATCHBUILD_PRECERT_BATCH_MEDIA


class Buildhelper:
    """
    Helper class to perform build related operations.
    """

    def __init__(self):
        """
        Constructor for update related files.
        """
        self.log = logger.get_log()
        self.config_json = config.get_config()
        self.buildid = None

    def create_db_object(self, server, user, password, database, autocommit):
        """
        Creates and returns a database object for interacting with MSSQL databases.

        Args:
            server (str): The server name.
            user (str): The username.
            password (str): The password.
            database (str): The database name.
            autocommit (bool): Whether to enable autocommit.

        Returns:
            database_helper.MSSQL: The database object.
        """
        return database_helper.MSSQL(server=server, user=user, password=password, database=database, autocommit=autocommit)

    def updatecenter_db_execute(self, query, data=None, commit=False):
        """
        Creates a database object, executes the query, and returns the results.

        Args:
            query (str): The SQL query to execute.
            commit (bool, optional): Whether to commit the changes. Defaults to False.

        Returns:
            Any: The results of the query.
        """
        with self.create_db_object(self.config_json.buildteam.server,
                                   self.config_json.buildteam.dbuser,
                                   self.config_json.buildteam.dbpassword,
                                   self.config_json.buildteam.dbname,
                                   commit) as dbobj:
            return dbobj.execute(query, data, commit=commit)

    def get_build_id(self, installed_spnum, installed_transnum, installed_revnum):
        """
        Retrieves the build ID based on the installed service pack number, transaction number, and revision number.

        Args:
            installed_spnum (int): The installed service pack number.
            installed_transnum (int): The installed transaction number.
            installed_revnum (int): The installed revision number.

        Returns:
            int: The build ID.

        Raises:
            Exception: If unable to get the build ID info from Updatecenter.
        """
        query = "SELECT nBuildID FROM MediaRecutInfo WHERE nRevisionNumber = %s AND nTransactionID = %s AND nSPID IN (SELECT nSPID FROM CVSP WHERE sSPName = '%s')"
        query = query % (installed_spnum, installed_transnum, installed_revnum)
        buildTeamInfo = self.updatecenter_db_execute(query)

        if len(buildTeamInfo.rows) <= 0:
            raise Exception(f"Unable to get the build ID info from Updatecenter with query: {query}")

        self.buildid = buildTeamInfo.rows[0][0]

        return self.buildid

    def update_cupack(self, installed_spnum, cunumber, installed_revnum, status="InProgress"):
        """
        Updates the CU pack with the given parameters.

        Args:
            installed_spnum (int): The installed service pack number.
            cunumber (int): The CU pack number.
            installed_revnum (int): The installed revision number.
            status (str, optional): The status of the CU pack. Defaults to "InProgress".

        Raises:
            Exception: If an error occurs during the update process.
        """
        if status == "Certified":
            limited_status = "Limited Certified"
        else:
            limited_status = status

        updatepack_withmedia = 0
        if cunumber == 1:
            updatepack_withmedia = 1

        self.log.info("Updating CU pack with values: build id [%s], spname [%s], cupack num [%s], recutnum [%s], status [%s], updatepackmedia [%s]" % (
            str(self.buildid), installed_spnum, str(cunumber), installed_revnum, status, str(updatepack_withmedia))
        )

        _query = "EXECUTE [dbo].[CertifyUpdatePack] %d, '%s', %d, %d, '%s', '%s', %d, %d" % (
            int(self.buildid), installed_spnum, int(cunumber), int(installed_revnum),
            status, limited_status, 0, updatepack_withmedia
        )

        self.log.info("Query used to update the CU pack: %s" % str(_query))
        ret = self.updatecenter_db_execute(_query, commit=True)
        if len(ret.rows) <= 0 or ret.rows[0][0] != 0:
            self.log.error("Error in updating the CU pack: %s" % str((ret.rows)))
            raise Exception("Error in updating the CU pack: %s" % str((ret.rows)))
        else:
            self.log.info("Successfully updated CU pack: %s" % str((ret.rows)))

    def get_released_updates(self):
        """
        Retrieves the list of released updates for the given build ID.
        """
        released_updates_query = """
            SELECT sUpdateName
            FROM UpdateInfo U
            INNER JOIN UpdateSetInfo US ON US.nUpdateSetID = U.nUpdateSetID
            AND US.nUpdateContenttypeid NOT IN (10, 5, 13, 14, 15, 16, 17, 11)
            INNER JOIN FormInfo F ON F.nFormID = US.nFormID
            AND F.nBuildID = US.nBuildID
            AND (US.nBuildID = %s)
            AND F.nFormStateID IN (12, 13)
            WHERE U.nUpdateStateID = 2
            AND U.bFriendlyUpdate = 0
            AND U.sUpdateName <> ''
            AND U.sPreCertStatus = 'Certified'
            ORDER BY sUpdateName ASC
        """
        released_updates_query = released_updates_query % (str(self.buildid))
        releasedupdates_info = self.updatecenter_db_execute(released_updates_query)
        return [result[0] for result in releasedupdates_info.rows]

    def updatePrecertStatus(self, listOfUpdates, status='Certified'):
        """
        Updates the pre-certification status of the given list of updates.

        Args:
            listOfUpdates (list): The list of updates.
            status (str, optional): The pre-certification status. Defaults to 'Certified'.

        Raises:
            Exception: If an error occurs during the update process.
        """
        try:
            # This file has the SQL script needed to update the DB
            querylines = "UPDATE UpdateInfo SET sPreCertStatus='%s' WHERE sUpdateName='%s' and(%s)"

            for update in listOfUpdates:
                if update.strip() == '':
                    continue

                if status == 'Certified':
                    qFilter = "sPreCertStatus IN ('InProgress', 'BatchPrecert')"
                elif status == "InProgress":
                    qFilter = "sPreCertStatus IN ('InProgress') OR sPreCertStatus IS NULL"
                else:
                    qFilter = "sPreCertStatus IS NULL"

                updateQuery = querylines % (status, str(update), qFilter)
                dbobj = self.updatecenter_db_execute(updateQuery, commit=True)
                if dbobj.rowcount >= 1:
                    self.log.info("Successfully marked [%s] as [%s]." % (str(update), str(status)))
                else:
                    self.log.error("Failed to mark [%s] as [%s]." % (str(update), str(status)))
                    raise
            self.log.info("Successfully marked [%s] updates as [%s]." % (str(len(listOfUpdates)), str(status)))
        except Exception as err:
            self.log.exception(str(err))
            raise
    
    def certify_and_setvisibility(self, listofupdates, installed_spnum, installed_revnum, visibility = 0, status="InProgress",bupdate=1, cupack=-100,media=0):
        """
        Updates the pre-certification status of the given list of updates.

        Args:
            listOfUpdates (list): The list of updates.
            installed_spnum (int): The installed service pack number.
            cupack (int): The CU pack number.
            installed_revnum (int): The installed revision number.
            status (str, optional): The status of the Updates / CU pack. Defaults to "InProgress".
            visibility (int, optional): The visibility flag. Defaults to 0.
            bupdate (int, optional): The update flag. Defaults to 1.
            media (int, optional): The media flag. Defaults to 0.

        Raises:
            Exception: If an error occurs during the update process.
        """
        try:
            listofupdates = ','.join(listofupdates)
            pack_status =  'Limited Certified' if status == 'Certified' else status
            cu_num = 0
            is_cupack = 0            
            if cupack > 0:
                cu_num= cupack
                is_cupack = 1
            
            _query = f"""EXECUTE [dbo].[CertifyAndSetVisibility] {self.buildid}, {installed_spnum},{installed_revnum}, 0, 1, {visibility}, {bupdate}, '{listofupdates}', '{status}', {is_cupack}, {media}, {cu_num}, '{pack_status}', {media}"""
            self.log.info(f"Query used to update certify_and_setvisibility: {_query}")
            ret = self.updatecenter_db_execute(_query, commit=True)
            if len(ret.rows) <= 0 or ret.rows[0][0] != 0:
                self.log.error("Error in updating the CU pack: %s" % str((ret.rows)))
                raise Exception("Error in updating the CU pack: %s" % str((ret.rows)))
            else:
                self.log.info("Successfully updated for updates or pack or media: %s" % str((ret.rows)))
                self.log.info("Successfully marked [%s] updates as [%s]." % (str(len(listofupdates)), str(status)))
                return ret.rows
        except Exception as err:
            self.log.exception(str(err))
            raise

    def _get_build_property(self, property_name):
        """
        Helper method to retrieve a specific property value from the BuildProperties table.

        Args:
            property_name (str): The name of the property to retrieve.

        Returns:
            str or None: The property value if found, otherwise None.
        """
        query = "SELECT sPropertyValue FROM BuildProperties WHERE sPropertyName='{}' and nBuildID={}".format(property_name, self.buildid)
        build_team_info = self.updatecenter_db_execute(query)
        return build_team_info.rows[0][0] if build_team_info.rows else None
    
    def get_precert_mode(self):
        """
        Retrieves the pre-certification mode for the current build.

        Returns:
            The pre-certification mode data for the current build, or None if no data is available.
        """
        query = f"EXEC GetPreCertStatus @i_nBuildID = {self.buildid}"
        precert_info = self.updatecenter_db_execute(query)
        data = precert_info.rows[0] if precert_info.rows else None
        if int(data[3]) != 0:
            self.log.error(f"PreCertification Mode: {data}")
            raise Exception(f"PreCertification Mode: {data}")
        return data

    def is_batch_media_mode(self, force_batch=False):
        """
        Check if the system is in batch media mode.

        Args:
            force_batch (bool, optional): Force the batch mode check. Defaults to False.

        Returns:
            bool: True if in batch media mode, False otherwise.
        """
        try:
            if force_batch:
                return True

            batch_stage = self._get_build_property(BATCHBUILD_CURRENTBATCHSTAGE)
            return batch_stage == BATCHBUILD_PRECERT_BATCH_MEDIA if batch_stage else False
        except Exception as err:
            raise

    def is_batch_mode(self, force_batch=False):
        """
        Check if the system is in batch mode.

        Args:
            force_batch (bool, optional): Force the batch mode check. Defaults to False.

        Returns:
            bool: True if in batch mode, False otherwise.
        """
        try:
            if force_batch:
                return True

            batch_stage = self._get_build_property(BATCHBUILD_CURRENTBATCHSTAGE)
            return batch_stage == BATCHBUILD_PRECERT_BATCH if batch_stage else False
        except Exception as err:
            raise

    def get_media_recut_info(self, spname, precertified):
        """
        Retrieves the MediaRecutInfo based on the service pack name and precertification status.

        Args:
            spname (str): The service pack name.
            precertified (bool): Whether the update is precertified.

        Returns:
            str: return latest revision number of the media recut info.
        """
        try:
            query = """
            DECLARE @nBuildID INT = %s
            DECLARE @sSPName VARCHAR(56) = '%s'
            DECLARE @bPrecertified INT = %s            
            DECLARE @nSPID INT
            DECLARE @nRecutRequestID INT

            SELECT @nSPID = nSPID FROM CVSP WHERE sSPName = @sSPName
            SELECT TOP 1 nRecutRequestID, nSPID, nTransactionID, nRevisionNumber FROM MediaRecutInfo
            WHERE nSPID = @nSPID AND nBuildID = @nBuildID AND bPrecertified = @bPrecertified 
            %s
            ORDER BY nRevisionNumber DESC
            """

            if precertified:
                query = query % (str(self.buildid), str(spname), str(precertified), "")
            else:
                swhereclause = 'AND nRevisionNumber IN (SELECT MAX(nRevisionNumber) from MediaRecutInfo WHERE nSPID = @nSPID AND nBuildID = @nBuildID )'
                query = query % (str(self.buildid), str(spname), str(precertified), swhereclause)

            self.log.info("Query to fetch MediaRecutInfo: %s" % query)
            latest_media_recutinfo = self.updatecenter_db_execute(query)

            if len(latest_media_recutinfo.rows) > 0:
                latest_revnum = latest_media_recutinfo.rows[0]
                return latest_revnum
        except Exception as err:
            self.log.error("Failed to fetch MediaRecutInfo: %s" % query)
            self.log.exception(str(err))
            raise

    def get_visibility_flag_media_recut_info(self, n_build_id, n_rev_num):
        """
        Retrieves the visibility flag from the MediaRecutInfo table based on the given build ID and revision number.

        Args:
            n_build_id (int): The build ID.
            n_rev_num (int): The revision number.

        Returns:
            str: The SQL query to retrieve the visibility flag.

        Raises:
            Exception: If an error occurs while executing the SQL query.
        """

        try:
            query = "SELECT nVisibilityFlag FROM MediaRecutInfo WHERE nBuildID = %d and nRevisionNumber=%d " % (n_build_id, n_rev_num)
            self.log.info("Query to fetch visibility flag: %s" % query)
            lstVisibilityFlag = self.updatecenter_db_execute(query)
            nCurrentVisiblityFlag = int(lstVisibilityFlag.rows[0][0])

            visibilityflag = nCurrentVisiblityFlag + 16
            return visibilityflag
        except Exception as err:
            self.log.error("Failed to fetch visibility flag: %s" % query)
            self.log.exception(str(err))
            raise

    def update_visibility_flag_audit(self, n_build_id, n_rev_num, n_visibility_flag=0, s_xml_name='FeatureReleaseList.xml', s_user_alias='PrecertSystem'):
        """
        Updates the visibility flag audit based on the given parameters.

        Args:
            n_build_id (int): The build ID.
            n_rev_num (int): The revision number.
            s_xml_name (str): The XML name.
            s_user_alias (str): The user alias.
            n_visibility_flag (int, optional): The visibility flag. Defaults to 0.

        Returns:
            None

        Raises:
            Exception: If an error occurs while executing the SQL query.
        """
        try:
            query = """
            DECLARE @nBuildID INT = %d
            DECLARE @nRevisionNumber INT = %d
            DECLARE @sXMLName NVARCHAR(256) = '%s'
            DECLARE @sUserAlias NVARCHAR(256) = '%s'
            DECLARE @sComments NVARCHAR(max) = ''

            DECLARE @nNewVisibilityFlag INT = %d
            DECLARE @nCurrentVisibilityFlag INT = 0;
            SELECT @nCurrentVisibilityFlag = nVisibilityFlag FROM MediaRecutInfo WHERE nBuildID = @nBuildID AND nRevisionNumber = @nRevisionNumber

            IF @nCurrentVisibilityFlag != @nNewVisibilityFlag
            BEGIN
                SELECT @sComments = 'VisibilityFlag changed from ['+CAST(@nCurrentVisibilityFlag AS varchar(126))+'] to ['+CAST(@nNewVisibilityFlag AS varchar(126))+']'

                INSERT INTO VisibilityFlagAudit(nBuildID, nRevisionNumber, sXMLName, sUserAlias, sComments, timeModified)
                    VALUES(@nBuildID, @nRevisionNumber, @sXMLName, @sUserAlias, @sComments, GETDATE())
            END
            """

            query = query % (int(n_build_id), int(n_rev_num), str(s_xml_name), str(s_user_alias), int(n_visibility_flag))
            self.log.info("Query to update visibility flag audit: %s" % query)
            self.updatecenter_db_execute(query, commit=True)
        except Exception as err:
            self.log.error("Failed to  update visibility flag audit: %s" % query)
            self.log.exception(str(err))
            raise

    def update_media_recut_info_query(self, n_recut_request_id, b_precertified, n_visibility_flag=0):
        """
        Generates the SQL query to update the MediaRecutInfo table.

        Args:
            n_recut_request_id (int): The recut request ID.
            b_precertified (int): The precertification flag.
            n_visibility_flag (int, optional): The visibility flag. Defaults to 0.

        Raises:
            Exception: If an error occurs while executing the SQL query.
        """
        try:
            query = """
            DECLARE @nRecutRequestID INT = %d
            DECLARE @bPrecertified INT = %d
            DECLARE @nVisibilityFlag INT = %d

            UPDATE MediaRecutInfo
            SET bPrecertified = @bPrecertified, nVisibilityFlag = @nVisibilityFlag
            WHERE nRecutRequestID = @nRecutRequestID
            """

            query = query % (int(n_recut_request_id), int(b_precertified), int(n_visibility_flag))
            self.log.info("Query to update MediaRecutInfo: %s" % query)
            self.updatecenter_db_execute(query, commit=True)
        except Exception as err:
            self.log.error("Failed to update MediaRecutInfo: %s" % query)
            self.log.exception(str(err))
            raise

    def update_cu_config_visibility_flag_audit(self, n_build_id, n_recut_num, cache_rev_num, n_visibility_flag=0):
        """
        Updates the visibility flag audit for CU Config based on the given parameters.

        Args:
            n_build_id (int): The build ID.
            n_recut_num (int): The recut number.
            cache_rev_num (int): The cache revision number.
            n_visibility_flag (int, optional): The visibility flag. Defaults to 0.

        Raises:
            Exception: If an error occurs while executing the SQL query.
        """
        try:
            query = """
            UPDATE updatepackInfo
            SET sCertifiedStatus = 'Full Certified', timeCertified = GETUTCDATE()
            WHERE nBuildID = %d AND nRevisionNumber = %d AND nRecutRequestID = %d
            """
            query = query % (int(n_build_id), int(cache_rev_num), int(n_recut_num))
            self.log.info("Query to update CU Config visibility flag audit: %s" % query)
            self.updatecenter_db_execute(query, commit=True)
        except Exception as err:
            self.log.error("Failed to update CU Config visibility flag audit: %s" % query)
            self.log.exception(str(err))
            raise

    def modify_build_property(self, property_name, property_value):
        """
        Modifies a build property in the database.

        Args:
            property_name (str): The name of the property to modify.
            property_value (str): The new value of the property.

        Raises:
            Exception: If an error occurs while executing the SQL query.
        """
        try:
            # This file has the SQL script needed to update the DB.
            rel_mgr_app_sp = f"EXECUTE [dbo].[ModifyBuildProperty] {int(self.buildid)}, {str(property_name)}, {str(property_value)}"

            # Run the stored procedure
            self.updatecenter_db_execute(rel_mgr_app_sp, commit=True)

            self.log.info("Successfully set build property [%s] to [%s] for build [%s]." % (
                str(property_name), str(property_value), str(self.buildid)))
            return True
        except Exception as err:
            self.log.error("Failed to set build property [%s] to [%s] for build [%s]." % (
                str(property_name), str(property_value), str(self.buildid)))
            self.log.exception(str(err))
            raise
