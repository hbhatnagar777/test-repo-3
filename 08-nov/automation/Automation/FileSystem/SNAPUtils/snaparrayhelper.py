# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for verifying IntelliSnap operations on different arrays

SNAPverify is the class defined in this file

SNAPverify: Helper class to verify IntelliSnap operations

SNAPverify:
    __init__()                   --  initializes Snap verify object
    initial_verify()             --  initializes all the variables required for a method
    connect()                    --  tries to HostConnect with each alias
    verify_snap_creation()       --  verifies the snapshot creation on the array
    run_and_verify_snap_deletion()       --  deletes a snap and verifies the snapshot deletion
    delete_snap_from_array()     --  deletes a snap from array
    run_and_verify_reconcile()   --  calls delete_snap_from_array(), then runs and verifies snap reconcile
"""
import urllib3
from netapp_ontap import config
from netapp_ontap import HostConnection
from netapp_ontap.resources.volume import Volume
from netapp_ontap.resources import Snapshot
import purestorage
from purestorage import PureHTTPError
from AutomationUtils import logger
from AutomationUtils import cvhelper
from FileSystem.SNAPUtils.snapconstants import SNAPConstants
from FileSystem.SNAPUtils.snaphelper import SNAPHelper


class SNAPverify:
    """Helper class to perform snap operation verifications"""

    def __init__(self, commcell, client, agent, tcinputs, snapconstants):

        """Initializes Snapverify object

            Args:
                commcell        (object)    --  commcell object

                client          (object)    --  client object

                agent           (object)    --  agent object

                tcinputs        (dict)      --  Test case inputs dictionary
                snapconstants   (object)    --  Snapconstants Object
        """

        self.log = logger.get_log()
        self.commcell = commcell
        self.client = client
        self.agent = agent
        self.tcinputs = tcinputs
        self.snapconstants = snapconstants
        self.shelper = SNAPHelper(self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)

    def initial_verify(self, vendor, copy_name, jobid, operation=" "):
        """Method to initialize all the variables required for verification
            Args:
                vendor: str: vendor name
                copy_name: str: snap copy name
                jobid: snap job id
                operation: str : verification type: creation/deletion/reconcile
            Return:
                Returns a list [refid, user: str, password: str, snap_name: str, vol_name: str]

        """
        try:
            self.log.info(
                "Starting variable initialization for snap %s for jobid:%s", operation, str(jobid))

            obj = self.shelper.spcopy_obj(copy_name)
            copy_id = obj.copy_id
            snap_copy_details = self.snapconstants.execute_query(self.snapconstants.snap_copy_details,
                                                                 {'a': copy_id})
            source_copy_id, is_snap_copy, is_mirror_copy = snap_copy_details[0]
            if int(source_copy_id) == 0 and int(is_snap_copy) == 1:
                is_secondary = False
            elif int(source_copy_id) > 0 and (int(is_snap_copy) or int(is_mirror_copy)):
                is_secondary = True
            else:
                raise Exception("Check Copy Name/Id. Not a snap copy array:%s job %s", vendor, str(jobid))
            self.log.info("Array: %s", vendor)
            if vendor.lower() == "netapp":

                all_vars = []
                cluster = self.snapconstants.execute_query(self.snapconstants.has_cluster, {'a': jobid, 'b': copy_id})
                if cluster in [[[]], [], [['']], None]:
                    self.log.info("No cluster mapping found. Getting host details.")
                    cluster_details = self.snapconstants.execute_query(self.snapconstants.get_host_details,
                                                                       {'a': jobid, 'b': copy_id})
                else:
                    self.log.info("It is mapped to a cluster. Getting cluster details.")
                    cluster_details = self.snapconstants.execute_query(self.snapconstants.get_cluster_details,
                                                                   {'a': jobid, 'b': copy_id})
                total = len(cluster_details)
                for i in range(total):
                    snap_name = cluster_details[i][1]
                    if is_secondary:
                        get_vol_name = self.snapconstants.execute_query(self.snapconstants.get_secondary_vol,
                                                                        {'a': jobid, 'b': copy_id})
                    else:
                        get_vol_name = self.snapconstants.execute_query(self.snapconstants.get_primary_vol,
                                                                    {'a': cluster_details[i][0]})
                    vol_name = get_vol_name[0][1]
                    user = cluster_details[i][5]
                    password = cvhelper.format_string(self.commcell, cluster_details[i][6])
                    refid = cluster_details[i][2]
                    details = [refid, user, password, snap_name, vol_name]
                    all_vars.append(details)
                    self.log.info("Variables initialized for %s", str(i + 1))

                return all_vars

            if vendor.lower() in ['pure storage flasharray snap', 'pure storage flasharray']:

                all_vars = []
                cluster_details = self.snapconstants.execute_query(self.snapconstants.get_host_details,
                                                                       {'a': jobid, 'b': copy_id})

                total = len(cluster_details)
                for i in range(total):
                    snap_name = cluster_details[i][1]
                    vol_name = snap_name.split('.')[0]
                    user = cluster_details[i][5]
                    password = cvhelper.format_string(self.commcell, cluster_details[i][6])
                    refid = cluster_details[i][2]
                    details = [refid, user, password, snap_name, vol_name]
                    all_vars.append(details)
                    self.log.info("Variables initialized for %s", str(i + 1))

                return all_vars

            else:
                self.log.info("Failed. Not applicable for this vendor %s", vendor)
                return []
        except Exception as exp:
            self.log.info("***Variables initialization failed! %s, Array %s", str(exp), vendor)
            return []

    def connect(self, vendor, alias, user, pas):
        """Method to try HostConnection with alias
            Args:
                vendor: str: SnapVendorName  eg. Netapp, Pure etc.
                alias: list: host alias Names
                user: str: username to login to array
                pas: str : password to connect to array
            Return:
                Returns a list [boolean, connection object/failure msg]

        """
        if vendor.lower() == "netapp":
            self.log.info("***Trying to connect..")
            runs = len(alias)
            for host in alias:
                self.log.info(str(host))
                try:
                    runs -= 1
                    conn = HostConnection(host[0], user, pas, verify=False)
                    config.CONNECTION = conn
                    volume_obj = Volume(conn)
                    volume_content = volume_obj.get()
                    self.log.info('connected to volume object %s', str(volume_content))
                    self.log.info('connection SUCCESS for %s', host[0])
                    return [True, conn]
                except Exception as exp:
                    self.log.info('connection ERROR for %s %s', host[0], str(exp))
                    if runs:
                        continue
            return [False, 'connection ERROR for ' + str(alias)]

        if vendor.lower() in ['pure storage flasharray snap', 'pure storage flasharray']:
            self.log.info("***Trying to connect..")
            urllib3.disable_warnings()
            runs = len(alias)
            for host in alias:
                self.log.info(str(host))
                try:
                    runs -= 1
                    conn = purestorage.FlashArray(host[0], api_token=pas)
                    self.log.info('connection SUCCESS for %s', host[0])
                    return [True, conn]
                except Exception as exp:
                    self.log.info('connection ERROR for %s %s', host[0], str(exp))
                    if runs:
                        continue
            return [False, 'connection ERROR for ' + str(alias)]
        else:
            self.log.info("Service not configured for this vendor %s", vendor)
            return [False, 'connection ERROR']

    def verify_snap_creation(self, vendor, job_id, copy_name):
        """Method to verify the snapshot creation
            Args:
                vendor: str: vendor name
                job_id: snap backup job id
                copy_name: snap copy name
            Return:
                Returns a list [Status: Bool, Message: Str]
        """
        success = 0
        fail = 0
        if vendor.lower() == "netapp":
            try:
                self.log.info("****Starting snap creation verification for jobid:%s", str(job_id))

                initials = self.initial_verify(vendor, copy_name, job_id, "Creation verification")
                runs = len(initials)

                if not initials:
                    self.log.info("Variables not initialized. check initial_verify()")
                    raise Exception("Variables not initialized. Array %s, jobid %s", vendor, str(job_id))

                for i in initials:
                    runs -= 1
                    refid, user, host_password, snap_name, vol_name = i
                    host = self.snapconstants.execute_query(self.snapconstants.get_hostalias, {'a': refid})

                    self.log.info("All variables initialized for snap create verification method")
                    connection_status = self.connect(vendor, host, user, host_password)
                    if connection_status[0]:
                        conn = connection_status[1]
                    else:
                        self.log.info("host connection FAILURE %s %s , jobid %s", str(host), str(connection_status[1]),
                                      str(job_id))
                        fail += 1
                        if runs:
                            self.log.info("**Now trying for snapshot in other array**")
                            continue
                        raise Exception("host connection FAILURE")
                    self.log.info("host connection success")
                    config.CONNECTION = conn
                    vol_obj = Volume(conn)
                    vol_gen = vol_obj.get_collection()
                    volumes = list(vol_gen)

                    for volume in volumes:
                        if vol_name in volume['name']:
                            break
                    else:
                        fail += 1
                        if runs:
                            self.log.info("Verification failed. Volume:%s not found. Array: %s, jobid: %s", vol_name,
                                          vendor, str(job_id))
                            self.log.info("*Now verifying for other volume*")
                            continue
                        raise Exception("Volume:%s not found.", vol_name)
                    vol_uuid = volume['uuid']
                    snap_obj = Snapshot(volume)
                    snap_gen = snap_obj.get_collection(vol_uuid)
                    snaps = list(snap_gen)
                    count = 0
                    for snap in snaps:
                        if snap_name == snap['name']:
                            self.log.info("* %s Creation Successfully Verified.*", snap_name)
                            success += 1
                            if runs:
                                self.log.info("*Now verifying for snapshot in other array*")
                                count = 1
                                break

                            if fail:
                                raise Exception("failed for some snaps. jobid %s ,Volume: %s, Array: %s", str(job_id),
                                                vol_name, vendor)
                            self.log.info("Verification Status Success: %s Failed: %s", str(success), str(fail))
                            return [True, "Snapshot Creation Successfully Verified."]
                    if count:
                        continue
                    self.log.info("*Snapshot creation verification FAILED for snap %s!", snap_name)
                    if runs:
                        self.log.info("Unable to verify. Now verifying for snapshot in other array")
                        continue
                    raise Exception("Unable to verify.")

            except Exception as exp:
                fail += 1
                self.log.info("Verification Status Success: %d Failed: %d", success, fail)
                self.log.info("*Snapshot creation verification FAILED! JobId: %s ,%s", str(job_id), str(exp))
                return [False, str(exp)]

        if vendor.lower() in ['pure storage flasharray snap', 'pure storage flasharray']:
            try:
                self.log.info("*Starting snap creation verification for jobid:%s", str(job_id))

                initials = self.initial_verify(vendor, copy_name, job_id, "Creation verification")
                runs = len(initials)

                if not initials:
                    self.log.info("Variables not initialized. check initial_verify()")
                    raise Exception("Variables not initialized.")

                for i in initials:
                    runs -= 1
                    refid, user, host_password, snap_name, vol_name = i
                    host = self.snapconstants.execute_query(self.snapconstants.get_hostalias, {'a': refid})

                    self.log.info("All variables initialized for snap create verification method")
                    connection_status = self.connect(vendor, host, user, host_password)
                    if connection_status[0]:
                        array = connection_status[1]
                    else:
                        self.log.info("host connection FAILURE %s %s", str(host), str(connection_status[1]))
                        fail += 1
                        if runs:
                            self.log.info("Now trying for snapshot in other array*")
                            continue
                        raise Exception("host connection FAILURE")
                    self.log.info("host connection success")

                    vol_details = array.get_volume(vol_name, snap=True)
                    count = 0
                    for snap in vol_details:
                        if snap['name'] == snap_name:
                            self.log.info("* %s Creation Successfully Verified.*", snap_name)
                            success += 1
                            if runs:
                                self.log.info("Now verifying for snapshot in other array*")
                                count = 1
                                break

                            if fail:
                                raise Exception("failed for some snaps")
                            self.log.info("Verification Status Success: %d Failed: %d", success, fail)
                            return [True, "Snapshot Creation Successfully Verified."]
                    if vol_details in [[], [{}]] or count == 0:
                        fail += 1
                        self.log.info("*Snapshot creation verification FAILED for snap %s, jobid %s ,Volume: %s, "
                                      "Array: %s!", snap_name, str(job_id), vol_name, vendor)
                        if runs:
                            self.log.info("Unable to verify. Now verifying for snapshot in other array")
                            continue
                        raise Exception("Unable to verify.")
                    continue
            except Exception as exp:
                fail += 1
                self.log.info("Verification Status Success: %d Failed: %d", success, fail)
                self.log.info("* Snapshot creation verification FAILED! JobId: %s, Array: %s, %s", str(job_id), vendor,
                              str(exp))
                return [False, str(exp)]
        else:
            self.log.info("verification fail. Not available for %s", vendor)
            return [False, "Not available"]

    def run_and_verify_snap_deletion(self, vendor, job_id, copy_name):
        """Method to delete and then verify the snapshot deletion
            Args:
                vendor: str: vendor name
                job_id: snap job id
                copy_name: snap copy name
            Return:
                Returns a list [Status: Bool, Message: Str]
        """
        fail = 0
        success = 0
        if vendor.lower() == "netapp":
            try:
                initials = self.initial_verify(vendor, copy_name, job_id, "deletion verification")
                runs = len(initials)
                if not initials:
                    self.log.info("Variables not initialized. check for initial_verify()")
                    raise Exception("Variables not initialized.")
                self.log.info("*Starting snap deletion jobid:%s", str(job_id))
                self.shelper.delete_snap(job_id, copy_name)

                for i in initials:
                    runs -= 1
                    refid, user, host_password, snap_name, vol_name = i
                    host = self.snapconstants.execute_query(self.snapconstants.get_hostalias, {'a': refid})
                    self.log.info("All variables initialized for snap delete verification method")
                    connection_status = self.connect(vendor, host, user, host_password)
                    if connection_status[0]:
                        conn = connection_status[1]
                    else:
                        fail += 1
                        self.log.info("host connection FAILURE %s %s", str(host), str(connection_status[1]))
                        if runs:
                            self.log.info("Now verifying for snapshot in other array*")
                            continue
                        raise Exception("host connection FAILURE")
                    self.log.info("host connection success")
                    config.CONNECTION = conn
                    vol_obj = Volume(conn)
                    vol_gen = vol_obj.get_collection()
                    volumes = list(vol_gen)

                    for volume in volumes:
                        if vol_name in volume['name']:
                            break
                    else:
                        fail += 1
                        if runs:
                            self.log.info("Verification failed. Volume:%s not found.\n Now verifying for other array",
                                          vol_name)
                            continue
                        raise Exception("Verification failed. Volume:%s not found. Array: %s", vol_name, vendor)
                    vol_uuid = volume['uuid']
                    snap_obj = Snapshot(volume)
                    snap_gen = snap_obj.get_collection(vol_uuid)
                    snaps = list(snap_gen)
                    count = 0
                    for snap in snaps:
                        if snap_name == snap['name']:
                            fail += 1
                            self.log.info("* %s Snapshot Deletion verification FAILED.jobid %s ,Volume: %s, Array: %s ",
                                          snap_name, str(job_id), vol_name, vendor)
                            if runs:
                                self.log.info("Now verifying for snapshot in other array*")
                                count = 1
                                break
                            raise Exception("Snapshot Deletion verification FAILED!")
                    if count:
                        continue
                    self.log.info("*Snapshot Deletion Successfully Verified for %s.", snap_name)
                    success += 1
                    if runs:
                        self.log.info("Now verifying for snapshot in other array")
                        continue

                    if fail:
                        raise Exception("Failed for some snaps")
                    return [True, "Snapshot Deletion Successfully Verified"]

            except Exception as exp:
                self.log.info("Verification Status, Success: %d Failed: %d", success, fail)
                self.log.info("*Snapshot deletion verification FAILED! %s jobid %s Array: %s", str(exp), str(job_id)
                              , vendor)
                return [False, str(exp)]

        if vendor.lower() in ['pure storage flasharray snap', 'pure storage flasharray']:
            try:
                initials = self.initial_verify(vendor, copy_name, job_id, "Deletion verification")
                runs = len(initials)

                if not initials:
                    self.log.info("Variables not initialized. check initial_verify()")
                    raise Exception("Variables not initialized.")

                self.log.info("*Starting snap delete for jobid:%s", str(job_id))
                self.shelper.delete_snap(job_id, copy_name)
                self.log.info("* Starting snap delete verification for jobid:%s", str(job_id))
                for i in initials:
                    runs -= 1
                    refid, user, host_password, snap_name, vol_name = i
                    host = self.snapconstants.execute_query(self.snapconstants.get_hostalias, {'a': refid})

                    self.log.info("All variables initialized for snap delete verification method")
                    connection_status = self.connect(vendor, host, user, host_password)
                    if connection_status[0]:
                        array = connection_status[1]
                    else:
                        self.log.info("host connection FAILURE %s %s", str(host), str(connection_status[1]))
                        fail += 1
                        if runs:
                            self.log.info("Now trying for snapshot in other array*")
                            continue
                        raise Exception("host connection FAILURE")
                    self.log.info("host connection success")

                    vol_details = array.get_volume(vol_name, snap=True)
                    count = 0
                    for snap in vol_details:
                        if snap['name'] == snap_name:
                            self.log.info("* Verification failed. Snap %s NOT deleted from the array %s", snap_name,
                                          vendor)
                            fail += 1
                            if runs:
                                self.log.info("Now verifying for snapshot in other array*")
                                count = 1
                                break
                            raise Exception("Snapshot Deletion verification FAILED!")

                    if vol_details in [[], [{}]] or count == 0:
                        success += 1
                        self.log.info(
                            "*Snapshot deletion verification SUCCESS for snap %s!", snap_name)
                        if runs:
                            self.log.info("Now verifying for snapshot in other array")
                            continue
                        return [True, "Snapshot Deletion Successfully Verified"]
                    continue
            except Exception as exp:
                fail += 1
                self.log.info("Verification Status, Success: %d Failed: %d", success, fail)
                self.log.info("*Snapshot deletion verification FAILED! jobid %s, Array: %s, %s",
                              str(job_id), vendor, str(exp))
                return [False, str(exp)]
        else:
            self.log.info("*Starting snap deletion jobid:%s", str(job_id))
            self.shelper.delete_snap(job_id, copy_name)
            self.log.info("verification Not available for %s, skipping it", vendor)
            return [False, "Not available"]

    def delete_snap_from_array(self, vendor, job_id, copy_name):
        """Method to delete a snap from array
            Args:
                vendor: str: vendor name
                job_id: snap job id
                copy_name: str: snap copy name
            Return:
                Returns a list [Status: Bool, Message: Str]
        """
        fail = 0
        success = 0
        if vendor.lower() == "netapp":
            try:

                self.log.info("*Starting snap deletion from array for jobid:%s", str(job_id))
                initials = self.initial_verify(vendor, copy_name, job_id, "Deletion from Array")
                runs = len(initials)
                if not initials:
                    self.log.info("Variables not initialized. check for initial_verify()")
                    raise Exception("Variables not initialized.")

                for i in initials:
                    runs -= 1
                    refid, user, host_password, snap_name, vol_name = i
                    host = self.snapconstants.execute_query(self.snapconstants.get_hostalias, {'a': refid})

                    connection_status = self.connect(vendor, host, user, host_password)
                    if connection_status[0]:
                        conn = connection_status[1]
                    else:
                        fail += 1
                        self.log.info("host connection FAILURE %s %s", str(host), str(connection_status[1]))
                        if runs:
                            self.log.info("Now deleting snapshot in other array*")
                            continue
                        raise Exception("host connection FAILURE")
                    self.log.info("host connection success")
                    config.CONNECTION = conn
                    vol_obj = Volume(conn)
                    vol_gen = vol_obj.get_collection()
                    volumes = list(vol_gen)
                    for volume in volumes:
                        if vol_name in volume['name']:
                            break
                    else:
                        fail += 1
                        if runs:
                            self.log.info("Deletion failed. Volume:%s not found. Array %s", vol_name, vendor)
                            self.log.info("Now deleting snap in other array*")
                            continue
                        raise Exception("Volume:%s not found.", vol_name)

                    vol_uuid = volume['uuid']
                    snap_obj = Snapshot(volume)
                    snap_gen = snap_obj.get_collection(vol_uuid)
                    snaps = list(snap_gen)
                    count = 0
                    for snap in snaps:
                        if snap_name == snap['name']:
                            res = snap.delete()
                            res = res.http_response.json()
                            if str(res['state']).lower() == 'success':
                                success += 1
                                self.log.info("*Snapshot Deleted from array %s", str(res['state']))
                                if runs:
                                    self.log.info("Now deleting snapshot in other array*")
                                    count = 1
                                    break

                                if fail:
                                    raise Exception("Failed for some cases. Check Logs.")
                                return [True, "Snapshot Deleted from array Successful."]

                            fail += 1
                            self.log.info("*Snapshot deletion from array FAILED!Cause %s, Snap: %s, Array: %s",
                                          str(res['state']), snap_name, vendor)
                            if runs:
                                self.log.info("Now deleting snapshot in other volume")
                                count = 1
                                break
                            raise Exception("FAILED for {}.".format(snap_name))
                    if count:
                        continue
                    success += 1
                    self.log.info(
                        "*Snapshot not found in array. Seems snap %s was already deleted!", snap_name)
                    if runs:
                        self.log.info("Now deleting snapshot in other array")
                        continue

                    if fail:
                        raise Exception("Failed for some cases. Check Logs.")
                    return [True, "Seems snap {} was already deleted!".format(snap_name)]

            except Exception as exp:
                self.log.info("Verification Status, Success: %d Failed: %d", success, fail)
                self.log.info("*Snapshot deletion from array FAILED. Array %s, %s", vendor, str(exp))
                return [False, str(exp)]

        if vendor.lower() in ['pure storage flasharray snap', 'pure storage flasharray']:
            try:
                self.log.info("*Starting snap delete from Array for jobid:%s", str(job_id))
                initials = self.initial_verify(vendor, copy_name, job_id, "Deletion from Array")
                runs = len(initials)
                if not initials:
                    self.log.info("Variables not initialized. check initial_verify()")
                    raise Exception("Variables not initialized.")
                for i in initials:
                    runs -= 1
                    refid, user, host_password, snap_name, vol_name = i
                    host = self.snapconstants.execute_query(self.snapconstants.get_hostalias, {'a': refid})

                    self.log.info("All variables initialized for snap delete from array method")
                    connection_status = self.connect(vendor, host, user, host_password)
                    if connection_status[0]:
                        array = connection_status[1]
                    else:
                        self.log.info("host connection FAILURE %s %s", str(host), str(connection_status[1]))
                        fail += 1
                        if runs:
                            self.log.info("Now trying for snapshot in other array")
                            continue
                        raise Exception("host connection FAILURE")
                    self.log.info("host connection success")
                    try:
                        del_snap = array.destroy_volume(snap_name)
                        success += 1
                        self.log.info("* %s Snapshot Deleted from array success", del_snap['name'])
                        if runs:
                            continue
                        return [True, 'Snapshot Deleted from array success']
                    except PureHTTPError as perror:
                        res = eval(perror.text)
                        response = eval(str(res[0]))
                        if response['msg'] == 'No such volume or snapshot.':
                            fail += 1
                            self.log.info("deletion Failed. No such volume or snapshot. Snap: %s, Array: %s", snap_name,
                                          vendor)
                            if runs:
                                self.log.info("Now deleting snapshot in other array")
                                continue
                            raise Exception("No such snapshot exists in this volume.")

                        success += 1
                        self.log.info('Snapshot already Deleted from array success %s %s', response['msg'],
                                      snap_name)
                        if runs:
                            self.log.info("Now deleting snapshot in other array")
                            continue
                        return [True, 'Snapshot Deleted from array success']
            except Exception as exp:
                self.log.info("Verification Status, Success: %d Failed: %d", success, fail)
                self.log.info("*Snapshot deletion from array FAILED.Array %s, %s", vendor, str(exp))
                return [False, str(exp)]
        else:
            self.log.info("verification fail. Not available for %s", vendor)
            return [False, "Not available"]

    def run_and_verify_reconcile(self, vendor, job_id, copy_name):
        """Method to run and verify snap reconcile
            Args:
                vendor: str: vendor name
                job_id: deleted snap job id
                copy_name: str: snap copy name
            Return:
                Returns a list [Status: Bool, Message: Str]
        """
        success = 0
        fail = 0
        if vendor.lower() == "netapp":
            try:
                del_status = self.delete_snap_from_array(vendor, job_id, copy_name)
                if not del_status[0]:
                    self.log.info("Cannot run and verify reconcile when snap has not been deleted from array")
                    raise Exception("snap has not been deleted from array %s", vendor)
                reconcile_job = self.shelper.reconcile_snap(job_id)
                self.log.info("Snap reconcile jobid:%s , status: %s", str(reconcile_job.job_id),
                              str(reconcile_job.status))
                self.log.info("*Starting snap reconcile verification for jobid:%s", str(job_id))
                snaps = self.snapconstants.execute_query(self.snapconstants.get_snap_status, {'a': job_id})
                self.log.info("Snapshot status received from query: %s", str(snaps))

                for status in snaps:
                    if status[0] in ['97', [['97']], 97, ['97']]:
                        self.log.info("*Snapshot Reconcile verification Success for %s", str(status[1]))
                        success += 1
                    else:
                        self.log.info("*Snapshot Reconcile verification FAILED for %s, Array %s", str(status[1]), vendor)
                        fail += 1
                if fail:
                    raise Exception('for {} arrays'.format(fail))
                self.log.info("Verification status, success: %d, failed: %d", success, fail)
                return [True, "Reconcile Verification Success "]

            except Exception as exp:
                self.log.info("Verification status, success: %d, failed: %d", success, fail)
                self.log.info("Snapshot Reconcile verification FAILED!Array: %s, %s", vendor, str(exp))
                return [False, str(exp)]

        if vendor.lower() in ['pure storage flasharray snap', 'pure storage flasharray']:
            try:
                del_status = self.delete_snap_from_array(vendor, job_id, copy_name)
                if not del_status[0]:
                    self.log.info("Cannot run and verify reconcile when snap has not been deleted from array")
                    raise Exception("snap has not been deleted from array. ")
                reconcile_job = self.shelper.reconcile_snap(job_id)
                self.log.info("Snap reconcile jobid:%s , status: %s", str(reconcile_job.job_id),
                              str(reconcile_job.status))
                self.log.info("*Starting snap reconcile verification for jobid:%s", str(job_id))
                snaps = self.snapconstants.execute_query(self.snapconstants.get_snap_status, {'a': job_id})
                self.log.info("Snapshot status received from query: %s", str(snaps))

                for status in snaps:
                    if status[0] in ['97', [['97']], 97, ['97']]:
                        self.log.info("*Snapshot Reconcile verification Success for %s", str(status[1]))
                        success += 1
                    else:
                        self.log.info("*Snapshot Reconcile verification FAILED for %s, Array: %s", str(status[1]),
                                      vendor)
                        fail += 1
                if fail:
                    raise Exception('failed for %d arrays', fail)
                self.log.info("Verification status, success: %d, failed: %d", success, fail)
                return [True, "Reconcile Verification Success "]

            except Exception as exp:
                self.log.info("Verification status, success: %d, failed: %d", success, fail)
                self.log.info("Snapshot Reconcile verification FAILED! Array %s, %s", vendor, str(exp))
                return [False, str(exp)]
        else:
            self.log.info("verification fail. Not available for %s", vendor)
            return [False, "Not available"]
