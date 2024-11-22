from cvpysdk.commcell import Commcell
import config, json, logging, traceback
logging.basicConfig(filename="vmdkrestore.log", format='%(asctime)s %(message)s', filemode='w')
logger=logging.getLogger()
logger.setLevel(logging.DEBUG)


class vmdkrestore():
    def __init__(self, sub_obj):
        self.diskExtension = [".vmdk", ".vmx", ".log", ".nvram"]
        self.sub_obj = sub_obj

    def _prepare_restore_json(self, disk_restore_option):
        """

        :param disk_restore_option: dict to populate the json
        :return: restore json
        """

        request_json = {
          "taskInfo": {
            "task": {
              "taskFlags": {
                "disabled": False
              },
              "policyType": "DATA_PROTECTION",
              "taskType": "IMMEDIATE",
              "initiatedFrom": "GUI",
              "ownerName": "admin"
            },
            "associations": [
              {
                "subclientId": int(self.sub_obj.subclient_id),
                "client": {},
                "applicationId": 106,
                "_type_": "CLIENT_ENTITY"
              }
            ],
            "subTasks": [
              {
                "subTask": {
                  "subTaskName": "",
                  "subTaskType": "RESTORE",
                  "operationType": "RESTORE"
                },
                "options": {
                  "restoreOptions": {
                    "browseOption": {
                      "commCellId": 2,
                      "timeRange": {
                        "fromTime": 0,
                        "toTime": int(disk_restore_option["to_time"])
                      },
                      "backupset": {
                        "instanceName": "VMware",
                        "backupsetId": int(self.sub_obj._backupset_object.backupset_id),
                        "clientId": int(self.sub_obj._client_object.client_id),
                        "applicationId": 106
                      },
                      "noImage": True,
                      "useExactIndex": False,
                      "mediaOption": {
                        "copyPrecedence": {
                          "copyPrecedence": 0
                        }
                      },
                      "listMedia": False,
                      "toTime": int(disk_restore_option["to_time"]),
                      "fromTime": 0,
                      "showDeletedItems": True
                    },
                    "destination": {
                      "destPath": [
                        disk_restore_option["destination_path"]
                      ],
                      "destClient": {
                        "clientName": disk_restore_option['client']
                      },
                      "inPlace": False,
                      "isLegalHold": False
                    },
                    "restoreACLsType": "ACL_DATA",
                    "volumeRstOption": {
                      "volumeLeveRestore": False,
                      "volumeLevelRestoreType": "VMDK_FILES"
                    },
                    "virtualServerRstOption": {
                      "diskLevelVMRestoreOption": {
                        "esxServerName":disk_restore_option["esx_server"],
                        "passUnconditionalOverride": False,
                        "useVcloudCredentials": True
                      },
                      "isDiskBrowse": True,
                      "userPassword": {
                        "userName": "root"
                      },
                      "viewType": "DEFAULT"

                    },
                    "fileOption": {
                      "sourceItem":  disk_restore_option["paths"]
                    },
                    "commonOptions": {
                      "overwriteFiles": False,
                      "detectRegularExpression": True,
                      "unconditionalOverwrite": True,
                      "stripLevelType": "PRESERVE_LEVEL",
                      "preserveLevel": 1,
                      "stripLevel": 0,
                      "restoreACLs": True,
                      "isFromBrowseBackup": True,
                      "clusterDBBackedup": False
                    }
                  },
                  "adminOpts": {
                    "updateOption": {
                      "invokeLevel": "NONE"
                    }
                  },
                  "commonOpts": {
                    "notifyUserOnJobCompletion": True
                  }
                }
              }
            ]
          }
        }

        logger.info(json.dumps(request_json))
        return request_json

    def vmdk_restore(self, proxy_client, destination_path, to_time, esx_server_name, uservm_names):
        """

        :param proxy_client: access node for restore
        :param destination_path: destination path to restire the disk
        :param to_time: to time for backup
        :return:
        """

        try:

            #get the vm names that are backed up
            vm_names , vm_ids = self.sub_obj._get_vm_ids_and_names_dict_from_browse()

            logger.info("backed up vms to are  "+ ','.join(vm_names))

            if not vm_names:
                print("No Vms to restore in subclient"+ _sub_obj.name)
                return

            _disk_restore_option = {}
            disk_name = []
            restore_jobs = []
            final_vmlist = []

            if uservm_names:
                final_vmlist = list(set(uservm_names) & set(vm_names))
            else:
                final_vmlist = vm_names

            logger.info("vms to be restored are are  " + ','.join(final_vmlist))

            for each_vm in final_vmlist:
                # fetching all disks from the vm

                source_list = []

                browse_content , files_dict = self.sub_obj.browse_in_time(vm_path="\\" + vm_ids[each_vm],
                                                                          to_date= to_time)
                for path in browse_content:
                    if any(path.lower().endswith(Ext) for Ext in self.diskExtension):
                        source_list.append("\\" + vm_ids[each_vm] + "\\" + path.split("\\")[-1])

                logger.info("file list for vm is "+ ','.join(source_list))

                _disk_restore_option["volume_level_restore"] = 3
                _disk_restore_option["destination_vendor"] = \
                    self.sub_obj._backupset_object._instance_object._vendor_id

                _disk_restore_option['client'] = proxy_client
                _disk_restore_option["to_time"] = to_time

                logger.info(" disk paths to be restored is " + ','.join(source_list) + " for vm "+each_vm)
                if '/' in destination_path:
                    destination_path = destination_path + "/" + each_vm
                else:
                    destination_path = destination_path + "\\" + each_vm

                self.sub_obj._set_restore_inputs(
                    _disk_restore_option,
                    in_place=False,
                    copy_precedence=0,
                    destination_path=destination_path,
                    paths=source_list,
                    esx_server= esx_server_name
                )

                request_json = self._prepare_restore_json(_disk_restore_option)
                restore_job = self.sub_obj._process_restore_response(request_json)
                logger.info("Ran restore job "+ restore_job.job_id+ " for vm "+ each_vm+" disks")
                restore_jobs.append(restore_job.job_id)

            return restore_jobs

        except BaseException as error:
            logger.error("An error has occured in building path and submitting restore " + traceback.format_exc())


if __name__ == '__main__':

    try:
        config = config.get_config()
        _cs_obj = Commcell(config.CS, config.username, config.password)
        #_vm_clientobj = _cs_obj.clients.get("amithvmtiny1_63299")
        _client_obj = _cs_obj.clients.get(config.hypervisor)
        logger.info("created client object for client "+ config.hypervisor)
        _agent_obj = _client_obj.agents.get('Virtual Server')
        _instancekeys = next(iter(_agent_obj.instances._instances))
        _instance_obj   = _agent_obj.instances.get(_instancekeys)
        logger.info("created instance object for instance " + _instancekeys)
        esx_server_name = _instance_obj.server_host_name[0]
        logger.info(esx_server_name)
        #_instance_obj.associated_clients = ['hvidc1','hvidc2']
        _backupset_obj = _instance_obj.backupsets.get(config.backupset)
        user_vmnames = config.vm_names
        success_subclient = []
        failed_subclient = []
        subclient_list = list(config.subclient)

        for each_subclient in subclient_list:
            logger.info("Running restore for subclient "+ each_subclient)
            _sub_obj = _backupset_obj.subclients.get(each_subclient)
            vmdk_res = vmdkrestore(_sub_obj)
            restore_job_list = vmdk_res.vmdk_restore(config.destinationclient,config.destinationpath,
                                                     config.to_time, esx_server_name, user_vmnames)
            if restore_job_list:
                logger.info("successfully completed restore jobs for subclient "+ each_subclient + "is "+ ', '.join(restore_job_list))
                success_subclient.append(each_subclient)
            else:
                logger.info("Failed to launch restore for subclient "+each_subclient)
                failed_subclient.append(each_subclient)

        logger.info("subclients succeeded " + ', '.join(success_subclient))
        logger.info("subclients failed "+ ', '.join(failed_subclient))

    except BaseException as error:
        logger.error("An error has occured in building path and submitting restore "+ traceback.format_exc())




