# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file to maintain all the constants used by policy to plan migration helper"""
retrieve_eligible_subclients_query = """
SET NOCOUNT ON
--ELIGIBLE POLICIES
IF OBJECT_ID('tempdb.dbo.#ApplicableStoragePolicyId') is not NULL 
       DROP table #ApplicableStoragePolicyId

Create table #ApplicableStoragePolicyId(
       StoragePolicyId INT,
     HasDifferentLogAndDataStorage INT,
     appTypeId INT,
     subClientId INT,
   backupSet INT
)

/*Processing the Storage Policies which are not associated to any Laptop client */
INSERT INTO #ApplicableStoragePolicyId
SELECT DISTINCT A.dataArchGrpID, (CASE WHEN A.dataArchGrpID = A.logArchGrpID THEN 0 ELSE 1 END) ,A.appTypeId, A.id, A.backupSet
  FROM APP_Application A WITH(NOLOCK) 
  INNER JOIN App_Client C WITH(NOLOCK) ON A.clientId=C.id
  inner join archGroup AG WITH(NOLOCK) on AG.id=A.dataArchGrpID
  LEFT OUTER JOIN App_PlanRule PR WITH(NOLOCK) ON PR.storagePolicyId = A.dataArchGrpID
  left outer join App_PlanProp PP WITH(NOLOCK) ON PP.attrName = 'Storage policy' AND CAST(PP.attrVal AS INT) = A.dataArchGrpId
  LEFT OUTER JOIN APP_SubClientProp PROP1 WITH(NOLOCK) ON A.id = PROP1.componentNameId AND PROP1.cs_attrName = CHECKSUM(N'DDB Backup') AND PROP1.attrName = 'DDB Backup' AND PROP1.attrVal = N'1' AND PROP1.modified = 0
  LEFT OUTER JOIN APP_SubClientProp PROP2 WITH(NOLOCK) ON A.id = PROP2.componentNameId AND PROP2.cs_attrName = CHECKSUM(N'Index SubClient') AND PROP2.attrName = 'Index SubClient' AND PROP2.attrVal = N'1' AND PROP2.modified = 0 
  LEFT OUTER JOIN APP_SubClientProp PROP3 WITH(NOLOCK) ON A.id = PROP3.componentNameId AND PROP3.attrName='Is Turbo Subclient' AND PROP3.cs_attrName = CHECKSUM(N'Is Turbo Subclient') AND PROP3.modified = 0
  LEFT OUTER JOIN APP_BackupSetProp B WITH(NOLOCK) ON B.componentNameId = A.backupSet AND A.appTypeId=1030/*Subclient*/
   LEFT OUTER JOIN APP_BackupSetProp BK WITH(NOLOCK) ON BK.componentNameId = A.backupSet AND A.appTypeId<>1030 AND BK.attrName='Associated subclient Policy'/*backupset associated to subclient policy*/ and BK.modified=0
WHERE ((C.status & 4096 = 0/*Not laptop*/) AND (C.status & 268435456/*sharepoint farm*/ = 0) AND (C.status & (268435456)/*Edge*/ = 0))
AND (PROP3.attrVal IS NULL OR PROP3.attrVal=''OR PROP3.attrVal=0) AND PROP1.attrVal IS NULL AND PROP2.attrVal IS NULL /*Means not archived subclient*/
AND PR.storagePolicyId IS NULL /*Not region based storage policy*/
and AG.type!=2 and AG.origCCCommcellId <=2
AND PP.attrVal IS NULL AND A.dataArchGrpID <> 1 /*Ignore CV default plicy*/
AND B.attrVal is NULL /*Ignore storage policies which has subclient policies*/ and A.subclientStatus & 2 = 0/*deleted*/ AND A.subclientStatus & 4 = 0/*uninstalled*/
    AND BK.attrVal IS NULL /*Ignore subclients whose backupset is associated to subclient policy*/
--
--

INSERT INTO #ApplicableStoragePolicyId
SELECT DISTINCT A.dataArchGrpID, (CASE WHEN A.dataArchGrpID = A.logArchGrpID THEN 0 ELSE 1 END) ,A.appTypeId, A.id, BP.id
FROM APP_BackupSetProp B
INNER JOIN APP_BackupSetName BP ON B.componentNameId = BP.id --AND BP.status&65536/*CV_STATUS_EDGE_POLICY_BSET*/=0
INNER JOIN APP_Application A ON B.componentNameId = A.backupSet AND A.appTypeId=1030/*Subclient*/
INNER JOIN App_Client C ON C.id = A.clientId AND ((C.status & 4096 = 0/*Not laptop*/) AND (C.status & 268435456/*sharepoint farm*/ = 0) AND (C.status & (268435456)/*Edge*/ = 0))
INNER JOIN archGroup AG ON AG.id = A.dataArchGrpID
LEFT OUTER JOIN App_PlanProp PP WITH(NOLOCK) ON PP.attrName='Storage policy' AND CAST(PP.attrVal AS INT)=A.dataArchGrpID
LEFT OUTER JOIN APP_SubClientProp PROP3 WITH(NOLOCK) ON A.id = PROP3.componentNameId AND PROP3.attrName='Is Turbo Subclient' AND PROP3.cs_attrName = CHECKSUM(N'Is Turbo Subclient') AND PROP3.modified = 0
LEFT OUTER JOIN APP_SubClientProp PROP1 WITH (NOLOCK) ON A.id = PROP1.componentNameId AND PROP1.cs_attrName = CHECKSUM(N'DDB Backup') AND PROP1.attrName = 'DDB Backup' AND PROP1.attrVal = N'1' AND PROP1.modified = 0
LEFT OUTER JOIN APP_SubClientProp PROP2 WITH (NOLOCK) ON A.id = PROP2.componentNameId AND PROP2.cs_attrName = CHECKSUM(N'Index SubClient') AND PROP2.attrName = 'Index SubClient' AND PROP2.attrVal = N'1' AND PROP2.modified = 0
LEFT OUTER JOIN App_PlanRule PR WITH(NOLOCK) ON PR.storagePolicyId = A.dataArchGrpID
WHERE B.attrName = 'Associated subclient Policy Ida Type' AND B.modified = 0
AND (PP.attrVal IS NULL OR PP.attrVal='')/*Means not associated to plan*/
AND (PROP3.attrVal IS NULL OR PROP3.attrVal=''OR PROP3.attrVal=0) AND PROP1.attrVal IS NULL AND PROP2.attrVal IS NULL /*Means not archived/DDB backup/index subclient*/
AND AG.id <>1 and AG.type!=2  and AG.origCCCommcellId <=2 /*Ignore CV_DEFAULT, CommServDR, migrated Storage policy */
AND (PR.storagePolicyId IS NULL OR PR.storagePolicyId='') /*Ignore plan's region based storage policies*/
and AG.type!=2 and AG.origCCCommcellId <=2
AND A.appTypeId<>1030
ORDER BY A.dataArchGrpID
--
-- START - DELETE EDGE DRIVE BACKUPSETS/LAPTOP ---------------------------------------------------------------------------------------
DELETE S
FROM #ApplicableStoragePolicyId S
INNER JOIN
(
       SELECT S.StoragePolicyId
       FROM #ApplicableStoragePolicyId S
       INNER JOIN APP_BackupSetName BP ON BP.id = S.backupSet
       WHERE BP.status&65536/*CV_STATUS_EDGE_POLICY_BSET*/>0
) B ON B.StoragePolicyId = S.StoragePolicyId
--
DELETE S
FROM #ApplicableStoragePolicyId S
JOIN APP_Application A ON A.dataArchGrpID = S.StoragePolicyId
JOIN App_Client C ON A.clientId = C.id
WHERE ((C.status & 4096 > 0/*laptop*/) OR (C.status & 268435456/*sharepoint farm*/ > 0) OR (C.status & (268435456)/*Edge*/ > 0))


IF OBJECT_ID(N'tempdb.dbo.#taskSubclientAssoc') IS NOT NULL DROP TABLE #taskSubclientAssoc
CREATE TABLE #taskSubclientAssoc(taskName NVARCHAR(MAX), taskId INT, appId int, dataArchGrpId int, appTypeId INT, clientId INT, subclientStatus INT, flags INT, deleted int, taskType INT)

INSERT INTO #taskSubclientAssoc (taskName, taskId, appId, dataArchGrpId, appTypeId, clientId, subclientStatus, flags, deleted, taskType)
SELECT A.taskName, A.taskId, A.id, A.dataArchGrpID, A.appTypeId, A.clientId, A.subclientStatus, A.flags, A.deleted, A.taskType
FROM
    (
        SELECT TASK.taskName, TASK.taskId, APP.id, APP.dataArchGrpID, APP.appTypeId, APP.clientId, app.subclientStatus, TASK.flags, TASK.deleted, TASK.taskType
          FROM TM_Task TASK WITH(NOLOCK) 
          INNER JOIN TM_AssocEntity ASSOC WITH(NOLOCK) ON TASK.taskId = ASSOC.taskId AND ASSOC.exclude = 0
          INNER JOIN APP_Application APP ON 
          ( (ASSOC.clientId > 0
              AND (ASSOC.clientId = APP.clientId
              AND (ASSOC.apptypeId = 0 OR ASSOC.apptypeId = APP.appTypeId
              AND (ASSOC.instanceId = 0 OR ASSOC.instanceId = APP.instance
              AND (ASSOC.backupsetId = 0 OR ASSOC.backupsetId = APP.backupSet
              AND (ASSOC.subclientId = 0 OR ASSOC.subclientId = APP.id)
            )))))
          )
        UNION -- GET ASSOCiATIONS at CLIENT GROUP LEVEL
        SELECT  TASK.taskName, TASK.taskId, APP.id, APP.dataArchGrpID, APP.appTypeId, APP.clientId, app.subclientStatus, TASK.flags, TASK.deleted, TASK.taskType
          FROM TM_Task TASK WITH(NOLOCK) 
          INNER JOIN TM_AssocEntity ASSOC WITH(NOLOCK) ON TASK.taskId = ASSOC.taskId AND ASSOC.exclude = 0
          INNER JOIN APP_Application APP ON 
          ( 
            (ASSOC.clientGroupId IN (SELECT clientGroupId FROM APP_ClientGroupAssoc CGA WITH (NOLOCK) WHERE CGA.clientId = APP.clientId) AND ASSOC.clientId = 0)
          )
        UNION -- GET ASSOCiATIONS at ALL_CLIENTS LEVEL
        SELECT  TASK.taskName, TASK.taskId, APP.id, APP.dataArchGrpID, APP.appTypeId, APP.clientId, app.subclientStatus, TASK.flags, TASK.deleted, TASK.taskType
          FROM TM_Task TASK WITH(NOLOCK) 
          INNER JOIN TM_AssocEntity ASSOC WITH(NOLOCK) ON TASK.taskId = ASSOC.taskId AND ASSOC.exclude = 0 AND ASSOC.assocType = 2/*ALL_CLIENTS*/
          INNER JOIN APP_Application APP ON APP.clientId > 0 AND ASSOC.clientId = 0
        UNION -- GET ASSOCiATIONS at ALL_CLIENT_GROUPS_ENTITY LEVEL
        SELECT  TASK.taskName, TASK.taskId, APP.id, APP.dataArchGrpID, APP.appTypeId, APP.clientId, app.subclientStatus, TASK.flags, TASK.deleted, TASK.taskType
          FROM TM_Task TASK WITH(NOLOCK) 
          INNER JOIN TM_AssocEntity ASSOC WITH(NOLOCK) ON TASK.taskId = ASSOC.taskId AND ASSOC.exclude = 0 AND ASSOC.assocType = 27/*ALL_CLIENT_groups_ENTITY*/
          INNER JOIN APP_Application APP ON 
          (
            (APP.clientId IN (SELECT clientId FROM APP_ClientGroupAssoc WITH (NOLOCK)) AND ASSOC.clientGroupId = 0)
          )
        EXCEPT
        SELECT TASK.taskName, TASK.taskId, APP.id, APP.dataArchGrpID, APP.appTypeId, APP.clientId, app.subclientStatus, TASK.flags, TASK.deleted, TASK.taskType
          FROM TM_Task TASK WITH(NOLOCK) 
          INNER JOIN TM_AssocEntity ASSOC WITH(NOLOCK) ON TASK.taskId = ASSOC.taskId AND ASSOC.exclude = 1
          INNER JOIN APP_Application APP ON 
          ( (ASSOC.clientId > 0
              AND (ASSOC.clientId = APP.clientId
              AND (ASSOC.apptypeId = 0 OR ASSOC.apptypeId = APP.appTypeId
              AND (ASSOC.instanceId = 0 OR ASSOC.instanceId = APP.instance
              AND (ASSOC.backupsetId = 0 OR ASSOC.backupsetId = APP.backupSet
              AND (ASSOC.subclientId = 0 OR ASSOC.subclientId = APP.id)
            )))))
          )
        EXCEPT
        SELECT  TASK.taskName, TASK.taskId, APP.id, APP.dataArchGrpID, APP.appTypeId, APP.clientId, app.subclientStatus, TASK.flags, TASK.deleted, TASK.taskType
          FROM TM_Task TASK WITH(NOLOCK) 
          INNER JOIN TM_AssocEntity ASSOC WITH(NOLOCK) ON TASK.taskId = ASSOC.taskId AND ASSOC.exclude = 1
          INNER JOIN APP_Application APP ON 
          ( 
            (ASSOC.clientGroupId IN (SELECT clientGroupId FROM APP_ClientGroupAssoc CGA WITH (NOLOCK) WHERE CGA.clientId = APP.clientId) AND ASSOC.clientId = 0)
          )
      ) A --inner join #ApplicableStoragePolicyId AST on AST.subclientId=A.id and AST.StoragePolicyId=A.dataArchGrpID



-- REMOVE APPTYPES WHICH ARE NOT iN FILTER
DELETE TS
FROM #taskSubclientAssoc TS
INNER JOIN TM_AssocFilter TF ON TF.taskId = TS.taskId
LEFT OUTER JOIN 
    (
        SELECT  AF.taskId, AG.appTypeId 
            FROM TM_AssocFilter AF
            INNER join APP_AppTypeGroupAssoc AG ON AF.filter_type = 1/*appTypeGroup*/ AND AF.filter_value = AG.appGroupId and AG.typeOfGroup = 0
        UNION ALL
        SELECT taskId, filter_value FROM TM_AssocFilter WHERE filter_type = 2/*appTypeId*/
    ) EA ON EA.taskId = TS.taskId AND EA.appTypeId = TS.appTypeId
WHERE EA.taskId IS NULL
--
--select taskId, appId,dataArchGrpId from #taskSubclientAssoc group by taskId, appId, dataArchGrpId


select A.subClientId, A.StoragePolicyId, STUFF((SELECT ', ' + CAST(TS.taskId as nvarchar(50)) from #taskSubclientAssoc TS where TS.appId=A.subclientId
          FOR XML PATH('')), 1, 1, '') as SchedulePolicyId from #ApplicableStoragePolicyId A order by A.subClientId

IF OBJECT_ID(N'tempdb.dbo.#taskSubclientAssoc') IS NOT NULL DROP TABLE #taskSubclientAssoc
--
IF OBJECT_ID('tempdb.dbo.#storagePolicyTbl') IS NOT NULL DROP TABLE #storagePolicyTbl
IF OBJECT_ID('tempdb.dbo.#ApplicableStoragePolicyId') IS NOT NULL DROP table #ApplicableStoragePolicyId
        """
"""str: query to get the subclients that are going to be impacted by the conversion"""
