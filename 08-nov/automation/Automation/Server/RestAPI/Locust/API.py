import json
import time
import re
from random import *
import string
import tool_helper
from datetime import datetime


def setup_request(func):
    """setup_request function for API calls"""

    def inner(self, taskset, **kwargs):
        variables = tool_helper.load_unload('r')
        taskset.client.verify = False
        user = choice(variables["locust_user_list"])
        tempjson = tool_helper.get_tempjson()
        param = None
        if tempjson:
            if func.__name__ in tempjson:
                param = tempjson.get(func.__name__)
        if user in variables:
            self.headers = tool_helper.headers({'Authtoken': variables[user]})
            func(self, taskset, abc="abc", username=user, user_id=str(variables['locust_user_id'][user]), param=param)
        else:
            print("locust user not logged in")

    return inner


class API:
    def __init__(self):
        self.headers = None

    @setup_request
    def get_organization(self, taskset, **kwargs):
        params = {
            "Fl": "providers.connectName,providers.primaryContacts,providers.associatedEntitiesCount,providers.provider,providers.enabled,providers.flags,providers.shortName,providers.status,providers.organizationCloudServiceDetails,providers.operators",
            "Sort": "connectName:1",
            "Limit": "20",
            "fq": "providers.status:eq:ACTIVE"
        }
        if kwargs.get("param"):
            params.update(kwargs['param'])
        response = taskset.client.get("/webconsole/api/Organization", params=params,
                                      headers=self.headers,
                                      name="/Organization")
        tool_helper.api_response("GET DETAILS OF ORGANIZATIONS RESPONSE", response)
        variables = tool_helper.load_unload('r')
        data = response.json()
        variables["companyID"] = str(data.get('providers')[0].get('provider').get('providerId'))
        tool_helper.load_unload('w', variables)

    @setup_request
    def get_users(self, taskset, **kwargs):
        params = {}
        if kwargs.get("param"):
            params.update(kwargs["param"])
        response = taskset.client.get("/webconsole/api/User", params=params,
                                      headers=self.headers,
                                      name="/users")
        tool_helper.api_response("GET DETAILS OF USERS RESPONSE", response)
        data = response.json()
        if len(data.get("users")):
            variables = tool_helper.load_unload('r')
            elem = randint(0, len(data.get('users')) - 1)
            variables["user_id_24"] = str(data['users'][elem]['userEntity']['userId'])
            tool_helper.load_unload('w', variables)

    @setup_request
    def get_pools(self, taskset, **kwargs):
        params = {}
        if kwargs.get("param"):
            params.update(kwargs.get('param'))
        response = taskset.client.get("/webconsole/api/StoragePool", headers=self.headers, name="/StoragePool",
                                      params=params)
        tool_helper.api_response("GET DETAILS OF STORAGE POOLS RESPONSE", response)
        data = response.json()
        if data.get("storagePoolList"):
            elem = randint(0, len(data['storagePoolList']) - 1)
            variables = tool_helper.load_unload('r')
            variables['diskID'] = str(data['storagePoolList'][elem]['storagePoolEntity']['storagePoolId'])
            tool_helper.load_unload('w', variables)

    def create_plan(self, taskset, **kwargs):
        variables = tool_helper.load_unload('r')
        user = choice(variables["locust_user_list"])
        if user in variables:
            headers = tool_helper.headers({'Authtoken': variables[user]})
            response = taskset.client.post("/webconsole/api/v2/Plan", data=json.dumps(
                {
                    "plan": {
                        "summary": {
                            "slaInMinutes": 240,
                            "description": "att-3 plan",
                            "restrictions": 1,
                            "type": 2,
                            "subtype": 33554437,
                            "planOwner": {
                                "userName": "admin",
                                "userId": 1
                            },
                            "plan": {
                                "planName": "locustPlan" + str(
                                    ''.join(choice(string.ascii_lowercase) for i in range(17)))
                            }
                        },
                        "inheritance": {
                            "isSealed": True
                        },
                        "storage": {
                            "storagePolicy": {},
                            "copy": [
                                {
                                    "active": 1,
                                    "isDefault": 1,
                                    "dedupeFlags": {
                                        "enableDASHFull": 1,
                                        "useGlobalDedupStore": 1,
                                        "enableDeduplication": 1,
                                        "enableClientSideDedup": 1
                                    },
                                    "storagePolicyFlags": {
                                        "blockLevelDedup": 1
                                    },
                                    "retentionRules": {
                                        "retainBackupDataForDays": 30,
                                        "retentionFlags": {
                                            "enableDataAging": 1
                                        }
                                    },
                                    "useGlobalPolicy": {
                                        "storagePolicyName": variables["storagePoolName"],
                                        "storagePolicyId": 0
                                    }
                                }
                            ]
                        },
                        "schedule": {
                            "task": {
                                "taskType": 4,
                                "taskFlags": {
                                    "isEdgeDrive": False,
                                    "isEZOperation": False,
                                    "disabled": False
                                }
                            },
                            "subTasks": [
                                {
                                    "subTask": {
                                        "subTaskName": "Daily Incremental",
                                        "subTaskType": 2,
                                        "flags": 65536,
                                        "operationType": 2,
                                        "subTaskId": 1
                                    },
                                    "pattern": {
                                        "freq_subday_interval": 14400,
                                        "freq_type": 4,
                                        "active_end_time": 86340,
                                        "active_start_time": 0,
                                        "freq_interval": 1,
                                        "name": "Daily Incremental",
                                        "freq_recurrence_factor": 1
                                    },
                                    "options": {
                                        "backupOpts": {
                                            "bkpLatestVersion": True,
                                            "backupLevel": 2,
                                            "incLevel": 1,
                                            "runIncrementalBackup": True,
                                            "doNotTruncateLog": False,
                                            "cdrOptions": {
                                                "incremental": True,
                                                "dataVerificationOnly": False,
                                                "full": False
                                            },
                                            "dataOpt": {
                                                "stopWinService": True,
                                                "stopDhcpService": True,
                                                "useCatalogServer": True,
                                                "optimizedBackup": True,
                                                "followMountPoints": True,
                                                "bkpFilesProctedByFS": True,
                                                "granularrecovery": True,
                                                "verifySynthFull": True,
                                                "daysBetweenSyntheticBackup": 0
                                            },
                                            "nasOptions": {
                                                "snapShotType": 0,
                                                "backupQuotas": True
                                            },
                                            "vaultTrackerOpt": {
                                                "mediaStatus": {
                                                    "bad": True,
                                                    "overwriteProtected": True,
                                                    "full": True
                                                }
                                            },
                                            "mediaOpt": {
                                                "numberofDays": 30,
                                                "retentionJobType": 2,
                                                "waitForInlineBackupResources": True,
                                                "allowOtherSchedulesToUseMediaSet": True
                                            }
                                        },
                                        "commonOpts": {
                                            "jobRetryOpts": {
                                                "runningTime": {
                                                    "totalRunningTime": 3600
                                                }
                                            }
                                        }
                                    }
                                },
                                {
                                    "subTask": {
                                        "subTaskName": "Last Saturday of the Month Regular Full",
                                        "subTaskType": 2,
                                        "flags": 0,
                                        "operationType": 2,
                                        "subTaskId": 1
                                    },
                                    "pattern": {
                                        "freq_subday_interval": 0,
                                        "freq_type": 32,
                                        "active_start_time": 72000,
                                        "freq_interval": 7,
                                        "freq_relative_interval": 5,
                                        "name": "Last Saturday of the Month Regular Full",
                                        "freq_recurrence_factor": 1,
                                        "daysToRun": {
                                            "week": 5,
                                            "day": 7
                                        }
                                    },
                                    "options": {
                                        "backupOpts": {
                                            "truncateLogsOnSource": False,
                                            "sybaseSkipFullafterLogBkp": False,
                                            "bkpLatestVersion": True,
                                            "backupLevel": 1,
                                            "incLevel": 1,
                                            "runIncrementalBackup": True,
                                            "doNotTruncateLog": False,
                                            "vsaBackupOptions": {
                                                "backupFailedVMsOnly": False
                                            },
                                            "cdrOptions": {
                                                "incremental": False,
                                                "dataVerificationOnly": False,
                                                "full": True
                                            },
                                            "dataOpt": {
                                                "useCatalogServer": True,
                                                "followMountPoints": True,
                                                "enforceTransactionLogUsage": False,
                                                "skipConsistencyCheck": False,
                                                "createNewIndex": True,
                                                "daysBetweenSyntheticBackup": 0,
                                                "autoCopy": False
                                            },
                                            "mediaOpt": {}
                                        },
                                        "commonOpts": {
                                            "perfJobOpts": {}
                                        }
                                    }
                                },
                                {
                                    "subTask": {
                                        "subTaskName": "Weekly Synthetic Fulls",
                                        "subTaskType": 2,
                                        "flags": 0,
                                        "operationType": 2,
                                        "subTaskId": 1
                                    },
                                    "pattern": {
                                        "freq_subday_interval": 0,
                                        "freq_type": 8,
                                        "active_start_time": 72000,
                                        "freq_interval": 32,
                                        "name": "Weekly Synthetic Fulls",
                                        "freq_recurrence_factor": 1,
                                        "daysToRun": {
                                            "Monday": False,
                                            "Thursday": False,
                                            "Friday": True,
                                            "Sunday": False,
                                            "Wednesday": False,
                                            "Tuesday": False,
                                            "Saturday": False
                                        },
                                        "repeatPattern": [
                                            {
                                                "exception": True,
                                                "onDay": 64,
                                                "occurrence": 16
                                            }
                                        ]
                                    },
                                    "options": {
                                        "backupOpts": {
                                            "truncateLogsOnSource": False,
                                            "sybaseSkipFullafterLogBkp": False,
                                            "bkpLatestVersion": True,
                                            "backupLevel": 4,
                                            "incLevel": 1,
                                            "runIncrementalBackup": True,
                                            "doNotTruncateLog": False,
                                            "vsaBackupOptions": {
                                                "backupFailedVMsOnly": False
                                            },
                                            "cdrOptions": {
                                                "incremental": False,
                                                "dataVerificationOnly": False,
                                                "full": False
                                            },
                                            "dataOpt": {
                                                "useCatalogServer": True,
                                                "followMountPoints": True,
                                                "enforceTransactionLogUsage": False,
                                                "skipConsistencyCheck": False,
                                                "createNewIndex": True,
                                                "daysBetweenSyntheticBackup": 0,
                                                "autoCopy": False
                                            },
                                            "mediaOpt": {}
                                        },
                                        "commonOpts": {
                                            "perfJobOpts": {}
                                        }
                                    }
                                },
                                {
                                    "subTask": {
                                        "subTaskName": "Daily aux copy",
                                        "subTaskType": 1,
                                        "flags": 0,
                                        "operationType": 4003,
                                        "subTaskId": 1
                                    },
                                    "pattern": {
                                        "freq_subday_interval": 1800,
                                        "freq_type": 4,
                                        "active_end_time": 86340,
                                        "active_start_time": 0,
                                        "freq_interval": 1,
                                        "name": "Daily aux copy",
                                        "freq_recurrence_factor": 1
                                    },
                                    "options": {
                                        "backupOpts": {
                                            "bkpLatestVersion": True,
                                            "backupLevel": 2,
                                            "incLevel": 1,
                                            "runIncrementalBackup": True,
                                            "doNotTruncateLog": False,
                                            "cdrOptions": {
                                                "incremental": True,
                                                "dataVerificationOnly": False,
                                                "full": False
                                            },
                                            "dataOpt": {
                                                "stopWinService": True,
                                                "stopDhcpService": True,
                                                "useCatalogServer": True,
                                                "optimizedBackup": True,
                                                "followMountPoints": True,
                                                "bkpFilesProctedByFS": True,
                                                "granularrecovery": True,
                                                "verifySynthFull": True,
                                                "daysBetweenSyntheticBackup": 0
                                            },
                                            "nasOptions": {
                                                "snapShotType": 0,
                                                "backupQuotas": True
                                            },
                                            "vaultTrackerOpt": {
                                                "mediaStatus": {
                                                    "bad": True,
                                                    "overwriteProtected": True,
                                                    "full": True
                                                }
                                            },
                                            "mediaOpt": {
                                                "numberofDays": 30,
                                                "retentionJobType": 2,
                                                "waitForInlineBackupResources": True,
                                                "allowOtherSchedulesToUseMediaSet": True
                                            }
                                        },
                                        "commonOpts": {
                                            "jobRetryOpts": {
                                                "runningTime": {
                                                    "totalRunningTime": 3600
                                                }
                                            }
                                        }
                                    }
                                }
                            ]
                        },
                        "options": {
                            "quota": 0
                        }
                    }
                }
            ),
                                           headers=headers,
                                           name="Create Plan")

            tool_helper.api_response("CREATE PLAN RESPONSE", response)
            variables = tool_helper.load_unload('r')
            if response.status_code == 200:
                variables["flag"] = 1
                planId = response.json()['plan']['summary']['plan']['planId']
                tool_helper.check_key(variables, user + "_planList", "plan_list", planId)
        else:
            print("Locust user is not logged in")

    def create_organization(self, taskset, **kwargs):
        variables = tool_helper.load_unload('r')
        user = choice(variables["locust_user_list"])
        if user in variables:
            headers = tool_helper.headers({'Authtoken': variables[user]})
            response = taskset.client.post("/webconsole/api/Organization", data=json.dumps(
                {
                    "organizationInfo": {
                        "planDetails": [
                            {
                                "numCopies": 2,
                                "description": "Server plan",
                                "type": 2,
                                "numDevices": 0,
                                "subtype": 33554437,
                                "isElastic": False,
                                "numAssocEntities": 0,
                                "restrictions": 1,
                                "numCompanies": 37,
                                "planStatusFlag": 0,
                                "rpoInMinutes": 86400,
                                "numUsers": 0,
                                "permissions": [
                                    {
                                        "permissionId": 31,
                                        "entityInfo": {
                                            "companyId": 0,
                                            "companyName": "",
                                            "multiCommcellId": 0
                                        }
                                    },
                                    {
                                        "permissionId": 157,
                                        "entityInfo": {
                                            "companyId": 0,
                                            "companyName": "",
                                            "multiCommcellId": 0
                                        }
                                    },
                                    {
                                        "permissionId": 158,
                                        "entityInfo": {
                                            "companyId": 0,
                                            "companyName": "",
                                            "multiCommcellId": 0
                                        }
                                    },
                                    {
                                        "permissionId": 159,
                                        "entityInfo": {
                                            "companyId": 0,
                                            "companyName": "",
                                            "multiCommcellId": 0
                                        }
                                    }
                                ],
                                "plan": {
                                    "planSubtype": 33554437,
                                    "_type_": 158,
                                    "planType": 2,
                                    "planSummary": "RPOHours:1440,NumberOfCopies:2,AssociatedEntitiesCount:0",
                                    "planName": variables["company_plan"],
                                    "planId": 0,
                                    "entityInfo": {
                                        "companyId": 0,
                                        "companyName": "",
                                        "multiCommcellId": 0
                                    }
                                },
                                "planOwner": {
                                    "_type_": 13,
                                    "userName": "Administrator",
                                    "userId": 1,
                                    "entityInfo": {
                                        "companyId": 0,
                                        "companyName": "",
                                        "multiCommcellId": 0
                                    }
                                }
                            }

                        ],
                        "organization": {
                            "connectName": "locustCompany" + str(
                                ''.join(choice(string.ascii_lowercase) for i in range(17))),
                            "emailDomainNames": [
                                "commvault.com"
                            ],
                            "shortName": {
                                "domainName": "locustCompany" + str(
                                    ''.join(choice(string.ascii_lowercase) for i in range(17)))
                            }
                        },
                        "organizationProperties": {
                            "primaryDomain": "",
                            "primaryContacts": [
                                {
                                    "fullName": "locustCompany" + str(
                                        ''.join(choice(string.ascii_lowercase) for i in range(17))),
                                    "email": "locustCompany" + str(
                                        ''.join(choice(string.ascii_lowercase) for i in range(17))) + "@commvault.com"
                                }
                            ]
                        }
                    }
                }
            ),
                                           headers=headers,
                                           name="Create Organization")

            tool_helper.api_response("CREATE ORGANIZATION RESPONSE", response)
            variables = tool_helper.load_unload('r')
            if response.status_code == 200:
                variables["flag"] = 1
                organizationId = response.json()["response"]["entity"]["providerId"]
                tool_helper.check_key(variables, user + "_orgList", "org_list", organizationId)
        else:
            print("locust user not logged in")

    def create_storagePool(self, taskset, **kwargs):
        variables = tool_helper.load_unload('r')
        user = choice(variables["locust_user_list"])
        if user in variables:
            headers = tool_helper.headers({'Authtoken': variables[user], 'Accept-Encoding': 'gzip'})
            response = taskset.client.post("/webconsole/api/StoragePool?Action=create", data=json.dumps(
                {
                    "storagePolicyName": "locustStoragePool" + str(
                        ''.join(choice(string.ascii_lowercase) for i in range(17))),
                    "type": 1,
                    "copyName": "locustStoragePoolCopy" + str(
                        ''.join(choice(string.ascii_lowercase) for i in range(17))),
                    "numberOfCopies": 1,
                    "clientGroup": {
                        "_type_": 28,
                        "clientGroupId": 0,
                        "clientGroupName": ""
                    },
                    "storage": [
                        {
                            "path": "C:\\Users\\Administrator\\Desktop\\lib\\storagePool" + str(
                                ''.join(choice(string.ascii_lowercase) for i in range(17))),
                            "mediaAgent": {
                                "mediaAgentId": 0,
                                "_type_": 11,
                                "mediaAgentName": variables["mediaAgentName"]
                            },
                            "credentials": {}
                        }
                    ],
                    "storagePolicyCopyInfo": {
                        "copyType": 1,
                        "isFromGui": True,
                        "active": 1,
                        "isDefault": 1,
                        "numberOfStreamsToCombine": 1,
                        "dedupeFlags": {
                            "enableDASHFull": 1,
                            "hostGlobalDedupStore": 1,
                            "enableDeduplication": 1
                        },
                        "storagePolicyFlags": {
                            "blockLevelDedup": 1,
                            "enableGlobalDeduplication": 1
                        },
                        "DDBPartitionInfo": {
                            "maInfoList": [
                                {
                                    "mediaAgent": {
                                        "mediaAgentId": 0,
                                        "_type_": 11,
                                        "mediaAgentName": variables["mediaAgentName"]
                                    },
                                    "subStoreList": [
                                        {
                                            "diskFreeWarningThreshholdMB": 10240,
                                            "diskFreeThresholdMB": 5120,
                                            "accessPath": {
                                                "path": "C:\\Users\\Administrator\\Desktop\\Check1" + str(
                                                    ''.join(choice(string.ascii_lowercase) for i in range(17)))
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        "library": {
                            "libraryName": variables["libraryName"],
                            "_type_": 9,
                            "libraryId": 0
                        },
                        "mediaAgent": {
                            "mediaAgentId": 0,
                            "_type_": 11,
                            "mediaAgentName": variables["mediaAgentName"]
                        }
                    }
                }

            ),
                                           headers=headers,
                                           name="Create Storage Pool")
            tool_helper.api_response("CREATE STORAGE POOL RESPONSE", response)
            variables = tool_helper.load_unload('r')
            if response.status_code == 200:
                variables["flag"] = 1
                storagePoolId = response.json()["archiveGroupCopy"]["storagePolicyId"]
                tool_helper.check_key(variables, user + "_poolList", "pool_list", storagePoolId)
        else:
            print("locust user not logged in")

    @setup_request
    def get_commcellDetails(self, taskset, **kwargs):
        response = taskset.client.get(
            "/commandcenter/api/cr/reportsplusengine/datasets/a0f077a5-2dfe-4010-a957-57a24cae89a8/data",
            headers=self.headers, name="Get commcell details")
        tool_helper.api_response("GET COMMCELL DETAILS RESPONSE", response)

    @setup_request
    def get_environmentDetails(self, taskset, **kwargs):

        response = taskset.client.get(
            "/commandcenter/api/cr/reportsplusengine/datasets/d0a73c45-b06d-4358-8d7e-d55d428ba75c/data?cache=true&parameter.i_DashboardType=commcell&datasource=2",
            headers=self.headers, name="Get environment details")
        tool_helper.api_response("GET ENVIRONMENT DETAILS RESPONSE", response)

    @setup_request
    def get_jobsIn24Hours(self, taskset, **kwargs):
        response = taskset.client.get(
            "/commandcenter/api/cr/reportsplusengine/datasets/075e703a-b29f-46d6-ad29-7c1a60f7e4f3/data"
            "?cache=true&parameter.i_DashboardType=commcell&datasource=2",
            headers=self.headers, name="Get jobs in 24 hours details")
        tool_helper.api_response("GET JOBS IN 24 HOURS RESPONSE", response)

    @setup_request
    def get_dashboardDataResponse(self, taskset, **kwargs):
        response = taskset.client.get(
            "/commandcenter/api/cr/reportsplusengine/datasets/b7d18c11-c4d8-435c-a978-16ef7c36fef8/data",
            headers=self.headers, name="Get dashboard data details")
        tool_helper.api_response("GET DASHBOARD DATA RESPONSE", response)

    @setup_request
    def get_SLADetails(self, taskset, **kwargs):
        response = taskset.client.get(
            "/commandcenter/api/cr/reportsplusengine/datasets/GetSLACounts/data?cache=true&parameter"
            ".i_DashboardType=commcell&datasource=2",
            headers=self.headers, name="Get SLA details")
        tool_helper.api_response("GET SLA DATA RESPONSE", response)

    @setup_request
    def get_MetricsCommUniqId(self, taskset, **kwargs):
        response = taskset.client.get(
            "/commandcenter/api/cr/reportsplusengine/datasets/d08a6b3b-d27d-4c5a-90ba-2f74fd55387b/data",
            headers=self.headers, name="Get MetricsCommUniqId details")
        tool_helper.api_response("GET MetricsCommUniqId DATA RESPONSE", response)

    @setup_request
    def get_diskSpace(self, taskset, **kwargs):
        response = taskset.client.get(
            "/commandcenter/api/cr/reportsplusengine/datasets/2b366703-52e1-4775-8047-1f4cfa13d2db/data"
            "?cache=true&parameter.i_DashboardType=commcell&orderby=%22Date%20to%20be%20Full%22&datasource=2",
            headers=self.headers, name="Get Disk Space details")
        tool_helper.api_response("GET DISK SPACE DATA RESPONSE", response)

    @setup_request
    def get_top5largestservers(self, taskset, **kwargs):
        response = taskset.client.get(
            "/commandcenter/api/cr/reportsplusengine/datasets/841800ea-53c4-4249-91fa-76ea0d60f6a4/data"
            "?cache=true&parameter.i_dashboardType=commcell&datasource=2",
            headers=self.headers, name="Get 5 largest servers details")

        tool_helper.api_response("GET 5 LARGEST SERVERS RESPONSE", response)

    @setup_request
    def get_health(self, taskset, **kwargs):
        response = taskset.client.get(
            "/commandcenter/api/cr/reportsplusengine/datasets/b50b20ed-5fc4-4b4c-f7c4-fc6b84eb35cc/data"
            "?cache=true&parameter.commUniId=10000",
            headers=self.headers, name="Get Commserver Health details")
        tool_helper.api_response("GET COMMSERVER HEALTH RESPONSE", response)

    @setup_request
    def get_metricDefault(self, taskset, **kwargs):
        response = taskset.client.get(
            "/commandcenter/api/cr/reportsplusengine/datasets/METRICS_DEFAULT/data?cache=true&parameter"
            ".param8=12&parameter.param2=1&parameter.param3=0&parameter.param1=-1&parameter.param6=NULL&operation"
            "=METRICS_EXECUTE_SP&parameter.param7=0&parameter.spName=RptCapacityLicenseSurvey&parameter.param4"
            "=10000&parameter.param5=NULL",
            headers=self.headers, name="Get Metric Default details")
        tool_helper.api_response("GET METRIC DEFAULT RESPONSE", response)

    @setup_request
    def get_clientCount(self, taskset, **kwargs):
        response = taskset.client.get(
            "/webconsole/api/clients/count?type=fileserver,vm,laptop",
            headers=self.headers, name="/clients/count")
        tool_helper.api_response("GET CLIENT COUNT RESPONSE", response)

    @setup_request
    def get_anomalies(self, taskset, **kwargs):
        response = taskset.client.get(
            "/webconsole/api/CommServ/Anomaly/Jobs",
            headers=self.headers, name="Get Anomaly Details")
        tool_helper.api_response("GET ANOMALIES RESPONSE", response)

    @setup_request
    def get_anomalousEntityCount(self, taskset, **kwargs):
        response = taskset.client.get(
            "/webconsole/api/CommServ/Anomaly/Entity/Count?anomalousEntityType=14",
            headers=self.headers, name="/CommServ/Anomaly/Entity/Count?anomalousEntityType=14")
        tool_helper.api_response("GET ANOMALOUS ENTITY COUNT RESPONSE", response)

    @setup_request
    def get_storage(self, taskset, **kwargs):
        response = taskset.client.get(
            "/commandcenter/api/cr/reportsplusengine/datasets/7C658447-17A5-4475-A463-7D3B2AFEC89A"
            ":bbaa0eca-ddd1-4792-98bb-922274ba2bc2/data",
            headers=self.headers, name="Get storage details")
        tool_helper.api_response("GET STORAGE RESPONSE", response)

    @setup_request
    def get_capacityLicenseDetails(self, taskset, **kwargs):
        response = taskset.client.get(
            "/commandcenter/api/cr/reportsplusengine/datasets/d7faef75-cf66-40a2-98ce-a2d0cc2a144b"
            ":feabb5ca-b6b7-4572-b0cb-39352c7e1b67/data/?cacheId=e76a6d07-2b1b-47b2-d97e-7a7f1a9793be&offset=0"
            "&fields=%5BDial%5D%20AS%20%5BDial%5D%2C%5BPurchased%5D%20AS%20%5BPurchased%5D%2C%5BPermTotal%5D%20AS"
            "%20%5BPermTotal%5D%2C%5BEval%5D%20AS%20%5BEval%5D%2C%5BUsage%5D%20AS%20%5BUsage%5D%2C%5BTermDate%5D"
            "%20AS%20%5BTermDate%5D%2C%5BEvalExpiryDate%5D%20AS%20%5BEvalExpiryDate%5D&isExport=false"
            "&componentName=Capacity%20Licenses&parameter.GUID=-1&limit=5&rawData=false",
            headers=self.headers, name="Get capacity license details")
        tool_helper.api_response("GET CAPACITY LICENSE", response)

    @setup_request
    def get_searchEntity(self, taskset, **kwargs):
        response = taskset.client.get(
            "/webconsole/api/Entities/Search?name=client&pageNum=1&pageSize=4&exactMatch=0",
            headers=self.headers, name="Get Search Entity Details")
        tool_helper.api_response("GET SEARCH ENTITY RESPONSE", response)

    @setup_request
    def get_basicSearch(self, taskset, **kwargs):
        response = taskset.client.get(
            "/webconsole/api/Entities/Search?name=client",
            headers=self.headers, name="Get Basic Search Details")
        tool_helper.api_response("GET BASIC SEARCH RESPONSE", response)

    @setup_request
    def get_multicommcell(self, taskset, **kwargs):
        response = taskset.client.get(
            "/webconsole/api/CommcellRedirect/Multicommcell",
            headers=self.headers, name="/CommcellRedirect/Multicommcell")
        tool_helper.api_response("GET MULTICOMMCELL RESPONSE", response)

    @setup_request
    def get_searchDetails(self, taskset, **kwargs):
        response = taskset.client.get(
            "/webconsole/api/Entities/Search?operationType=Archive&name=client&detailedProperty=1",
            headers=self.headers)
        tool_helper.api_response("GET SEARCH DETAILS RESPONSE", response)

    @setup_request
    def get_multicommcellsearch(self, taskset, **kwargs):
        response = taskset.client.get(
            "/webconsole/api/Entities/Search?name=client&ismultiCommcellSearch=1",
            headers=self.headers, name="Get multicommcell search entity Details")
        tool_helper.api_response("GET MULTICOMMCELL SEARCH RESPONSE", response)

    @setup_request
    def papi_company(self, taskset, **kwargs):
        response = taskset.client.get(
            "/webconsole/api/V4/company",
            headers=self.headers, name="/V4/company")
        tool_helper.api_response("GET PAPI COMPANY RESPONSE", response)

    @setup_request
    def papi_user(self, taskset, **kwargs):
        response = taskset.client.get(
            "/webconsole/api/V4/user",
            headers=self.headers, name="/V4/user")
        tool_helper.api_response("GET PAPI USER RESPONSE", response)
        variables = tool_helper.load_unload('r')
        data = response.json()
        if data.get('numberOfUsers') and not variables.get('user_id'):
            variables['user_id'] = str(data.get("users")[0].get("id"))
            tool_helper.load_unload('w', variables)

    @setup_request
    def papi_userGroup(self, taskset, **kwargs):
        response = taskset.client.get(
            "/webconsole/api/V4/usergroup",
            headers=self.headers, name="/V4/usergroup")
        tool_helper.api_response("GET PAPI USERGROUP RESPONSE", response)
        data = response.json()
        variables = tool_helper.load_unload('r')
        if len(data.get('userGroups')):
            elem = randint(0, len(data.get('userGroups')))
            variables['usergroup_id'] = data.get('userGroups')[elem].get('id')
            tool_helper.load_unload('w', variables)

    @setup_request
    def getusergroup(self, taskset, **kwargs):
        """GET USER GROUP API"""
        params = {
            "level": "10",
            "flag": "5",
            "start": "0",
            "limit": "25",
            "sort": "userGroupEntity.userGroupName%3A1&fl=userGroups.userGroupEntity.userGroupName%2CuserGroups"
                    ".userGroupEntity.userGroupId%2CuserGroups.plan%2CuserGroups.description%2CuserGroups.provider"
                    "%2CuserGroups.enabled%2CuserGroups.serviceType "
        }
        if kwargs.get("param"):
            params.update(kwargs['param'])
        response = taskset.client.get(
            "/webconsole/api/usergroup", params=params,
            headers=self.headers, name="/usergroup")
        tool_helper.api_response("GET USERGROUP RESPONSE", response)
        data = response.json()
        if len(data.get("userGroups")):
            variables = tool_helper.load_unload('r')
            elem = randint(0, len(data['userGroups']) - 1)
            variables["usergroup_id"] = data['userGroups'][elem]['userGroupEntity']['userGroupId']
            tool_helper.load_unload('w', variables)

    @setup_request
    def getusergroup_details(self, taskset, **kwargs):
        variables = tool_helper.load_unload('r')
        if variables.get("usergroup_id"):
            response = taskset.client.get(
                "/webconsole/api/usergroup/{}".format(variables['usergroup_id']),
                headers=self.headers, name="/usergroup/<ID>")
            tool_helper.api_response("GET USERGROUP DETAILS RESPONSE", response)
            response = taskset.client.get(
                "/webconsole/api/usergroup/{}/Security".format(variables['usergroup_id']),
                headers=self.headers, name="/usergroup/<ID>/Security")
            tool_helper.api_response("GET USERGROUP DETAILS RESPONSE", response)

    @setup_request
    def get_role(self, taskset, **kwargs):
        params = {
            "start": "0",
            "limit": "25",
            "sort": "roleProperties.role.roleName%3A1",
            "fl": "roleProperties.role"
        }
        response = taskset.client.get(
            "/webconsole/api/Security/roles", params=params,
            headers=self.headers, name="/Security/roles")
        tool_helper.api_response("GET ROLES RESPONSE", response)
        data = response.json()
        if data.get('roleProperties'):
            variables = tool_helper.load_unload('r')
            elem = randint(0, len(data['roleProperties']) - 1)
            variables["roleId"] = str(data['roleProperties'][elem]['role']['roleId'])
            tool_helper.load_unload('w', variables)

    @setup_request
    def get_role_details(self, taskset, **kwargs):
        variables = tool_helper.load_unload('r')
        if variables.get("roleId"):
            response = taskset.client.get(
                "/webconsole/api/role/" + variables['roleId'],
                headers=self.headers, name="/role/<ID>")
            tool_helper.api_response("GET ROLE DETAILSS RESPONSE", response)
            response = taskset.client.get(
                "/webconsole/api/Security/allroles",
                headers=self.headers, name="/Security/allroles")
            tool_helper.api_response("GET ROLE SECURITY RESPONSE", response)

    @setup_request
    def papi_role(self, taskset, **kwargs):
        response = taskset.client.get(
            "/webconsole/api/V4/role",
            headers=self.headers, name="V4/role")
        tool_helper.api_response("GET PAPI ROLE RESPONSE", response)

    @setup_request
    def papi_diskStorage(self, taskset, **kwargs):
        response = taskset.client.get(
            "/webconsole/api/V4/Storage/Disk/3?showInheritedAssociation",
            headers=self.headers, name="V4/Storage/Disk/3?showInheritedAssociation")
        tool_helper.api_response("GET PAPI STORAGE RESPONSE", response)

    def create_user(self, taskset, **kwargs):
        variables = tool_helper.load_unload('r')
        user = choice(variables["locust_user_list"])
        if user in variables:
            headers = tool_helper.headers({'Authtoken': variables[user], 'Accept-Encoding': 'gzip'})
            response = taskset.client.post("/webconsole/api/User", data=json.dumps({
                "users":
                    [
                        {
                            "description": "User created for load testing",
                            "agePasswordDays": 10,
                            "password": "I0VMbG9Xb3JsZCExMg==",
                            "email": "locustCreatedUser" + str(time.time()) + str(randint(0, 10000)) + "@locust.com",
                            "fullName": "Locust User",
                            "enableUser": True,
                            "userEntity":
                                {
                                    "userName": "locustCreatedUser" + str(time.time())+"num"+str(randint(0, 10000))
                                }
                        }
                    ]
            }),
                                           headers=headers,
                                           name="Create User")
            tool_helper.api_response("CREATE USER RESPONSE", response)
            variables = tool_helper.load_unload('r')
            if response.status_code == 200:
                variables["flag"] = 1
                id = response.json()['response'][0]['entity']['userId']
                tool_helper.check_key(variables, user + "_userlist", "user_list", id)
        else:
            print("Locust user hasn't logged in yet")

    def delete_user(self, taskset, **kwargs):
        variables = tool_helper.load_unload('r')
        user = choice(variables["locust_user_list"])
        if user in variables:
            if variables[user + "_userlist"]:
                if len(variables[user + "_userlist"]) > 0:
                    print("Delete CREATED USER")
                    headers = tool_helper.headers({'Authtoken': variables[user], 'Accept-Encoding': 'gzip'})
                    i = variables[user + "_userlist"].pop(randrange(len(variables[user + "_userlist"])))
                    response = taskset.client.delete("/webconsole/api/User/%i" % i,
                                                     headers=headers,
                                                     name="DELETE User")
                    print("Response content:", response.text)
                    if response.status_code == 200:
                        print("User Deleted")
                        tool_helper.load_unload('w', variables)
                    else:
                        print("Failed to delete user")
                        tool_helper.load_unload('w', variables)

            else:
                print("No user to delete")
        else:
            print("Locust user not logged in")

    def deactivate_organization(self, taskset, authtoken, organization_id=0):
        variables = tool_helper.load_unload('r')
        print("Deactivate Organization")
        headers = tool_helper.headers({'Authtoken': authtoken, 'Accept-Encoding': 'gzip'})
        response = taskset.client.post("/webconsole/api/Organization/%i/action/deactivate" % organization_id,
                                       data=json.dumps({
                                           "deactivateOptions": {
                                               "disableBackup": True,
                                               "disableRestore": True,
                                               "disableLogin": True
                                           }}),
                                       headers=headers,
                                       name="Deactivate Organization")
        print("Response status code", response.status_code)
        print("Response content:", response.json())
        if response.status_code == 200:
            print("Deactivated Organization")
            return response.status_code

        else:
            print("Organization Deactivation failed")
            return response.status_code

    def delete_organization(self, taskset, **kwargs):
        variables = tool_helper.load_unload('r')
        print("DELETE Organization")
        user = choice(variables["locust_user_list"])
        if user in variables:
            headers = tool_helper.headers({'Authtoken': variables[user], 'Accept-Encoding': 'gzip'})
            if len(variables[user + "_orgList"]) != 0:
                organization_id = variables[user + "_orgList"].pop(randrange(len(variables[user + "_orgList"])))
                res = self.deactivate_organization(taskset, variables[user], organization_id)
                if res == 200:
                    response = taskset.client.delete("/webconsole/api/Organization/%i" % organization_id,
                                                     headers=headers,
                                                     name="Delete Organization")
                    print("Response status code", response.status_code)
                    print("Response content:", response.json())
                    if response.status_code == 200:
                        print("Organization Deleted")
                        tool_helper.load_unload('w', variables)
                    else:
                        print("Failed to delete Organization")
                else:
                    print("Organization was not deactivated")
            else:
                print("No organization to delete")
        else:
            print("Locust user not logged in")

    def delete_plan(self, taskset, **kwargs):
        variables = tool_helper.load_unload('r')
        print("Delete Plan")
        user = choice(variables["locust_user_list"])
        if user in variables:
            if len(variables["plan_list"]) != 0:
                headers = tool_helper.headers({'Authtoken': variables[user], 'Accept-Encoding': 'gzip'})
                plan_id = variables[user + "_planList"].pop(randrange(len(variables[user + "_planList"])))
                response = taskset.client.delete("/webconsole/api/v2/Plan/%i?confirmDelete=true" % plan_id,
                                                 headers=headers,
                                                 name="DELETE Plan")
                print(response.text)
                if response.status_code == 200:
                    print("Plan Deleted")
                    tool_helper.load_unload('w', variables)
                else:
                    print("Failed to delete plan")

            else:
                print("No plan to delete")
        else:
            print("Locust user not logged in")

    def delete_pool(self, taskset, **kwargs):
        variables = tool_helper.load_unload('r')
        print("Delete Storage")
        user = choice(variables["locust_user_list"])
        if user in variables:
            if len(variables["pool_list"]) != 0:
                headers = tool_helper.headers({'Authtoken': variables[user], 'Accept-Encoding': 'gzip'})
                storage_id = variables[user + "_poolList"].pop(randrange(len(variables[user + "_poolList"])))
                response = taskset.client.delete("/webconsole/api/StoragePool/%i" % storage_id,
                                                 headers=headers,
                                                 name="DELETE Storage")
                if response.status_code == 200:
                    print("Pool Deleted")
                    tool_helper.load_unload('w', variables)
                else:
                    print("Failed to delete pool")

            else:
                print("No pool to delete")
        else:
            print("Locust user not logged in")

    def get_topologies(self, taskset, **kwargs):
        """Get API for the topologies listing"""
        variables = tool_helper.load_unload('r')
        user = choice(variables["locust_user_list"])
        if user in variables:
            headers = tool_helper.headers({'Authtoken': variables[user], 'Accept': 'application/json'})
            response = taskset.client.get(
                "/webconsole/api/FirewallTopology",
                headers=headers, name="/FirewallTopology")
            tool_helper.api_response("GET TOPOLOGIES RESPONSE", response)
            response_data = response.json()
            if response.status_code == 200 and not variables.get("topology_id"):
                variables["topology_id"] = response_data.get("firewallTopologies")[0].get("topologyEntity").get(
                    "topologyId")
                tool_helper.load_unload("w", variables)
        else:
            print("Locust user not logged in ")

    def get_topology_details(self, taskset, **kwargs):
        """Get API for the topologies listing"""
        variables = tool_helper.load_unload('r')
        user = choice(variables["locust_user_list"])
        if user in variables:
            if variables.get("topology_id"):
                headers = tool_helper.headers({'Authtoken': variables[user], 'Accept': 'application/json'})
                response = taskset.client.get(
                    "/webconsole/api/FirewallTopology/{}".format(variables.get("topology_id")),
                    headers=headers, name="/FirewallTopology/{}")
                tool_helper.api_response("GET TOPOLOGY DETAILS RESPONSE", response)
                response_data = response.json()
            else:
                print("Details api before the listing API")
        else:
            print("Locust user not logged in ")

    @setup_request
    def get_dips(self, taskset, **kwargs):
        """GET DATAINTERFACE PAIRS API"""
        response = taskset.client.get("/webconsole/api/CommServ/DataInterfacePairs", name="CommServ/DataInterfacePairs",
                                      headers=self.headers)
        tool_helper.api_response("GET DATA INTERFACE PAIRS RESPONSE", response)

    # Listing APIs for the License Page
    @setup_request
    def get_commcell_registration(self, taskset, **kwargs):
        """GET API for the get commcell registration """
        response = taskset.client.get(
            "/webconsole/api/Commcell/2/registration",
            headers=self.headers, name="/Commcell/2/registration")
        tool_helper.api_response("GET COMMCELL REGISTRATION  RESPONSE", response)

    @setup_request
    def get_license_availability(self, taskset, **kwargs):
        """GET API for the get license availability """
        response = taskset.client.get(
            "/webconsole/api/License/AvailabilityStatus",
            headers=self.headers, name="/License/AvailabilityStatus")
        tool_helper.api_response("GET LICENSE AVAILABILITY  RESPONSE", response)

    @setup_request
    def get_commcell_registration_info(self, taskset, **kwargs):
        """GET API For the registration info"""
        response = taskset.client.get(
            "/webconsole/api/CommcellRegistrationInformation",
            headers=self.headers, name="/CommcellRegistrationInformation")
        tool_helper.api_response("GET COMMCELL REGISTRATION INFO", response)

    # TESTCASE 60786
    @setup_request
    def papi_regions(self, taskset, **kwargs):
        """Listing API for the Regions using PAPI"""
        variables = tool_helper.load_unload('r')
        url = "/Regions?propertyLevel=BasicProperties" if variables.get("version") <= '24' else "/v4/Regions"
        response = taskset.client.get(
            "/webconsole/api" + url,
            headers=self.headers, name=url)
        tool_helper.api_response("GET PAPI REGIONS LISTING  RESPONSE", response)
        if variables.get("version") <= '24':
            elem = randint(0, len(response.json().get('regions')) - 1)
            variables["regionId"] = str(response.json().get("regions")[elem].get('regionEntity').get('regionId'))
        else:
            variables["regionId"] = str(response.json().get('regions')[0].get('id'))
        tool_helper.load_unload('w', variables)

    @setup_request
    def papi_region_details(self, taskset, **kwargs):
        """Details API for the Regions using PAPI"""
        variables = tool_helper.load_unload('r')
        print(variables["version"])
        url = "/Regions/{}/clients" if variables.get("version") <= '24' else "/v4/Regions/{}"
        if variables.get("regionId"):
            response = taskset.client.get("/webconsole/api" + url.format(variables['regionId'])
                                          , headers=self.headers, name=url)
            tool_helper.api_response("GET PAPI REGION DETAILS RESPONSE ", response)
        else:
            print("Region ID is not available")

    # TESTCASE
    def get_tags(self, taskset, **kwargs):
        """Listing APIs for the tags in CC"""
        variables = tool_helper.load_unload('r')
        user = choice(variables["locust_user_list"])
        if user in variables:
            headers = tool_helper.headers({'Authtoken': variables[user], 'Accept': 'application/json'})
            response = taskset.client.get(
                "/webconsole/api/EDiscovery/Tags",
                headers=headers, name="/EDiscovery/Tags")
            if response.status_code == 200 and not variables.get("tagID"):
                variables["tagID"] = response.json().get('listOftagSetList')[0].get('tagSetsAndItems')[0].get('tags')[
                    0].get("tagId")
                tool_helper.load_unload("w", variables)
            tool_helper.api_response("GET TAGS RESPONSE", response)

    @setup_request
    def get_tag_details(self, taskset, **kwargs):
        """Details API for tag in command center"""
        variables = tool_helper.load_unload('r')
        if variables.get("tagID"):
            response = taskset.client.get(
                "/webconsole/api/EDiscovery/Tags?tagSetId={}".format(str(variables["tagID"])),
                headers=self.headers, name="/Tags?tagSetId={}")
            tool_helper.api_response("GET TAG DETAILS RESPONSE", response)
        else:
            print("Tag ID is not set")

    # TESTCASE 60771
    @setup_request
    def get_papi_virtualmachines(self, taskset, **kwargs):
        """Listing API for the virtual machines using PAPI"""
        params = {
            "forUser": "true",
            "additionalProperties": "true",
            "start": "0",
            "limit": "20",
            "sort": "name",
            "fl": "vmStatusInfoList"
        }
        if kwargs.get("param"):
            params.update(kwargs["param"])
        response = taskset.client.get("/webconsole/api/v4/VirtualMachines", params=params,
                                      headers=self.headers, name="/v4/VirtualMachines")
        tool_helper.api_response("GET VIRTUAL MACHINES RESPONSE PAPI", response)
        data = response.json()
        if data.get("virtualMachinesCount") > 0:
            variables = tool_helper.load_unload('r')
            vmdetails = dict()
            variables["subclientID"] = data.get("virtualMachines")[0].get('vmGroup').get("id")
            vmdetails["client_id"] = data.get("virtualMachines")[0].get("additionalProperties").get("client").get("id")
            variables["VMDetails"] = vmdetails
            variables["get_jobs_param"] = {
                "viewLevel": "VMCLIENT",
                "applicationIdList": "106",
                "jobTypeList": "Backup,SYNTHFULL",
                "clientIdList": vmdetails["client_id"]
            }
            tool_helper.load_unload("w", variables)
        else:
            print("There are no virtual machines. Details APIs will not be called")

    @setup_request
    def get_vm_details(self, taskset, **kwargs):
        """Details API for the Virtual machine"""
        params = {
            "forUser": "true",
            "status": 0,
            "excludeVendorId": "20",
            "additionalProperties": "false",
            "start": "0",
            "limit": "20",
            "sort": "name:1",
            "fl": "vmStatusInfoList"
        }
        response = taskset.client.get("""/webconsole/api/VM""",
                                      headers=self.headers, name="/VM", params=params)
        tool_helper.api_response("GET VIRTUAL MACHINE DETAILS RESPONSE", response)
        data = response.json()
        if data.get("totalRecords"):
            variables = tool_helper.load_unload("r")
            elem = randint(0, len(data.get("vmStatusInfoList")) - 1)
            vmdetails = dict()
            variables["subclientID"] = str(data.get("vmStatusInfoList")[elem].get("subclientId"))
            vmdetails["client_id"] = str(data.get("vmStatusInfoList")[elem].get("client").get("clientId"))
            variables["VMDetails"] = vmdetails
            variables["get_jobs_param"] = {
                "viewLevel": "VMCLIENT",
                "applicationIdList": "106",
                "jobTypeList": "Backup,SYNTHFULL",
                "clientIdList": vmdetails["client_id"]
            }
            tool_helper.load_unload("w", variables)

    @setup_request
    def get_subclient_details(self, taskset, **kwargs):
        """Details API for the subclient when subclient ID is present"""
        variables = tool_helper.load_unload('r')
        if variables.get("subclientID"):
            subclient_id = variables.get('subclientID')
            response = taskset.client.get(f"/webconsole/api/Subclient/{subclient_id}?propertyLevel=3",
                                          headers=self.headers, name="/Subclient/{subclient_id}?propertyLevel=3")
            tool_helper.api_response("GET SUBCLIENT DETAILS Response", response)
        else:
            print("VM details or VM group are unavailable : get_subclient_details")

    @setup_request
    def get_vmallocationpolicy(self, taskset, **kwargs):
        """Details API for the subclient / VM"""
        params = {}
        variables = tool_helper.load_unload('r')
        if variables.get("VMAllocation_param"):
            params.update(variables['VMAllocation_param'])
        response = taskset.client.get(f"/webconsole/api/VMAllocationPolicy", params=params,
                                      headers=self.headers, name="/VMAllocationPolicy")
        data = response.json()
        if data:
            variables["recovery_target_id"] = str(data.get('policy')[0].get("entity").get("vmAllocPolicyId"))
            tool_helper.load_unload('w', variables)
        tool_helper.api_response("GET VM ALLOCATION POLICY DETAILS Response", response)

    @setup_request
    def get_permission_details(self, taskset, **kwargs):
        """Details API for the security / permission of VM"""
        variables = tool_helper.load_unload('r')
        if variables.get("VMDetails"):
            client_id = variables.get("VMDetails").get("client_id")
            response = taskset.client.get(f"/webconsole/api/Security/CLIENT_ENTITY/{str(client_id)}/Permissions",
                                          headers=self.headers, name="/Security/CLIENT_ENTITY/{client_id}/Permissionss")
            tool_helper.api_response("GET SECURITY PERMISSION DETAILS Response", response)
        else:
            print("VM details are unavailable")

    # TESTCASE 60840
    @setup_request
    def get_disk_papi(self, taskset, **kwargs):
        """Listing API for the disks PAPI"""
        params = {
            "additionalProperties": "true"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        response = taskset.client.get("/webconsole/api/v4/Storage/Disk", params=params, headers=self.headers,
                                      name="/v4/Storage/Disk")
        tool_helper.api_response("GET DISKS PAPI", response)
        variables = tool_helper.load_unload('r')
        data = response.json()
        if len(data) > 0:
            elem = randint(0, len(data.get('diskStorage')) - 1)
            variables["diskID"] = data.get("diskStorage")[elem].get('id')
            tool_helper.load_unload('w', variables)
        else:
            print("there are no disks")

    @setup_request
    def get_disk_details(self, taskset, **kwargs):
        """Details api for the disk"""
        variables = tool_helper.load_unload('r')
        if variables.get("diskID"):
            response = taskset.client.get(f"""/webconsole/api/StoragePool/{variables["diskID"]}""",
                                          headers=self.headers, name="/StoragePool/{diskID}")
            tool_helper.api_response("GET disk details", response)

        else:
            print("Disk id is not set")

    # TESTCASE 59866
    @setup_request
    def get_plan(self, taskset, **kwargs):
        """Details api for the plan"""
        params = {
            "start": 0,
            "limit": "25",
            "sort": "plans.plan.planName:1",
            "fl": "plans.missingEntities,plans.numAssocEntities,"
                  "plans.numCopies,plans.parent,plans.permissions,plans.plan.planId,plans.plan.planName,"
                  "plans.planStatusFlag,plans.restrictions,plans.rpoInMinutes,plans.subtype,plans.type,plans.targetApps"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        response = taskset.client.get("""/webconsole/api/v2/plan""", params=params,
                                      headers=self.headers,
                                      name="/v2/plan")
        tool_helper.api_response("GET PLANS RESPONSE", response)
        variables = tool_helper.load_unload('r')
        data = response.json()
        if data.get("filterQueryCount") > 0:
            elem = randint(0, len(data['plans']))
            variables["planID"] = data.get('plans')[elem].get('plan').get('planId')
            tool_helper.load_unload('w', variables)
        else:
            print("there are no plans")

    @setup_request
    def get_plan_details(self, taskset, **kwargs):
        """GET PLAN DETAILS"""
        variables = tool_helper.load_unload('r')
        if variables.get("planID"):
            response = taskset.client.get(f"""/webconsole/api/v2/Plan/{variables["planID"]}?propertyLevel=15""",
                                          headers=self.headers,
                                          name="/Plan/{planID}")
            tool_helper.api_response("GET PLAN DETAILS RESPONSE", response)
        else:
            print("Plan ID is not set yet")

    # TESTCASE 60778
    @setup_request
    def get_laptops(self, taskset, **kwargs):
        """GET LAPTOPS"""
        params = {
            "Fl": "clientsFileSystem",
            "Sort": "deviceSummary.clientName:1",
            "Limit": "20",
            "Start": "0"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        response = taskset.client.get("""/webconsole/api/Device""", params=params,
                                      headers=self.headers,
                                      name="/Device")
        tool_helper.api_response("GET LAPTOPS RESPONSE", response)
        variables = tool_helper.load_unload('r')
        data = response.json()
        if data.get("filterQueryCount") > 0:
            variables["laptopID"] = str(data.get('clientsFileSystem')[0].get('client').get('clientId'))
            variables["subclientID"] = str(data.get('clientsFileSystem')[0].get('subClient').get('subclientId'))
            tool_helper.load_unload('w', variables)
        else:
            print("there are no plans")

    @setup_request
    def get_laptop_details(self, taskset, **kwargs):
        """GET LAPTOP DETAILS"""
        variables = tool_helper.load_unload('r')
        if variables.get("laptopID"):
            response = taskset.client.get(f"""/webconsole/api/device/{variables["laptopID"]}""",
                                          name="/device/{laptopID}",
                                          headers=self.headers)
            tool_helper.api_response("GET LAPTOP DETAILS RESPONSE", response)
        else:
            print("laptop id is not set")

    @setup_request
    def get_laptop_security(self, taskset, **kwargs):
        """GET LAPTOP SECURITY"""
        variables = tool_helper.load_unload('r')
        if variables.get("laptopID"):
            response = taskset.client.get(f"""/webconsole/api/Security/3/{variables["laptopID"]}""",
                                          name="/Security/3/{laptopID}",
                                          headers=self.headers)
            tool_helper.api_response("GET LAPTOP SECURITY RESPONSE", response)
        else:
            print("laptop id is not set")

    @setup_request
    def get_alertrule_laptop(self, taskset, **kwargs):
        """GET ALERTRULE"""
        variables = tool_helper.load_unload('r')
        params = {
            "clientId": "0",
            "subClientId": variables["subclientID"]
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        if variables.get("subclientID"):
            response = taskset.client.get("""/webconsole/api/AlertRuleForEntity""", params=params,
                                          name="/AlertRuleForEntity",
                                          headers=self.headers)
            tool_helper.api_response("GET LAPTOP ALERTRULE RESPONSE", response)
        else:
            print("Subclient id is not set")

    @setup_request
    def get_laptop_permissions(self, taskset, **kwargs):
        """GET PERMISSIONS"""
        variables = tool_helper.load_unload('r')
        if variables.get("laptopID"):
            response = taskset.client.get(
                f"""/webconsole/api/Security/CLIENT_ENTITY/{variables["laptopID"]}/Permissions?includeNotMappedPermission=false""",
                name="/Security/CLIENT_ENTITY/{laptopID}/Permissions",
                headers=self.headers)
            tool_helper.api_response("GET LAPTOP PERMISSIONS RESPONSE", response)
        else:
            print("laptop id is not set")

    @setup_request
    def get_laptop_schedule(self, taskset, **kwargs):
        """GET LAPTOP SCHEDULE"""
        variables = tool_helper.load_unload('r')
        if variables.get("subclientID"):
            response = taskset.client.get(
                f"""/webconsole/api/SchedulePolicy?subclientId={variables["subclientID"]}""",
                name="/SchedulePolicy?subclientId={subclientID}",
                headers=self.headers)
            tool_helper.api_response("GET LAPTOP SCHEDULES RESPONSE", response)
        else:
            print("Subclient id is not set")

    @setup_request
    def get_tag_entity(self, taskset, **kwargs):
        """GET laptop tags"""
        variables = tool_helper.load_unload('r')
        tag = variables.get('laptopID', variables.get('tag_entity'))
        if tag:
            response = taskset.client.get(
                f"""/webconsole/api/Tags/CLIENT_ENTITY/{tag}""",
                name="/Tags/CLIENT_ENTITY/{tag}",
                headers=self.headers)
            tool_helper.api_response("GET TAGS RESPONSE", response)
        else:
            print("laptop id is not set")

    def get_laptop_jobs(self, taskset, **kwargs):
        """GET laptop jobs"""
        variables = tool_helper.load_unload('r')
        if variables.get("laptopID"):
            payload = f"""<?xml version="1.0" encoding="UTF-8"?><JobManager_JobListRequest scope="1" category="0">
                        <pagingConfig sortField="jobId" sortDirection="0" offset="0" limit="1"/>
                        <jobFilter completedJobLookupTime="300" showAgedJobs="0">
                            <jobTypeList val="4"/>
                            <clientList clientId="{variables["laptopID"]}"/>
                        </jobFilter>
                        </JobManager_JobListRequest>"""
            user = choice(variables["locust_user_list"])
            if user in variables:
                headers = tool_helper.headers(
                    {'Authtoken': variables[user], 'Accept': 'application/json', 'Content-Type': "application/xml"})
                response = taskset.client.post("""/webconsole/api/jobs""", data=payload, headers=headers,
                                               name="/jobs")
                tool_helper.api_response("GET LAPTOP JOBS RESPONSE", response)
            else:
                print("Locust user not logged in")

    # TESTCASE 61962
    @setup_request
    def get_tapes_papi(self, taskset, **kwargs):
        """GET TAPES PAPI"""
        response = taskset.client.get("/webconsole/api/v4/Storage/Tape", headers=self.headers, name="/v4/Storage/Tape")
        tool_helper.api_response("GET TAPES PAPI RESPONSE", response)
        variables = tool_helper.load_unload('r')
        data = response.json()
        if len(data.get('tapeStorage')) > 0:
            variables["tapeID"] = str(data.get('tapeStorage')[0].get('id'))
            tool_helper.load_unload('w', variables)
        else:
            print("No tapes are present")

    @setup_request
    def get_tapelibrary_details(self, taskset, **kwargs):
        """GET laptop tags"""
        variables = tool_helper.load_unload('r')
        if variables.get("tapeID"):
            response = taskset.client.get(
                f"""/webconsole/api/Library/{variables["tapeID"]}""",
                name="/Library/{apeID}",
                headers=self.headers)
            tool_helper.api_response("GET TAPE LIBRARY DETAILS RESPONSE", response)
        else:
            print("Tape id is not set")

    @setup_request
    def get_libariesTape(self, taskset, **kwargs):
        """GET laptop tags"""
        response = taskset.client.get("""/webconsole/api/Library?libraryType=Tape""",
                                      name="/Library?libraryType=Tape",
                                      headers=self.headers)
        tool_helper.api_response("GET LIBRARIES OF TYPE TAPE RESPONSE", response)
        data = response.json()
        if data.get("libraryList"):
            variables = tool_helper.load_unload('r')
            elem = randint(0, len(data.get("libraryList")) - 1)
            variables['tapeID'] = str(data['libraryList'][elem]['library']['libraryId'])
            tool_helper.load_unload('w', variables)

    # TESTCASE 60837
    @setup_request
    def get_alerts(self, taskset, **kwargs):
        """GET ALERTS"""
        params = {
            "pageNo": "1",
            "pageCount": "10"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        response = taskset.client.get("/webconsole/api/Alert", params=params, headers=self.headers, name="/Alert")
        tool_helper.api_response("GET ALERTS RESPONSE", response)
        variables = tool_helper.load_unload('r')
        data = response.json()
        if data.get('totalNoOfAlerts') and data.get('totalNoOfAlerts') > 0:
            variables["alertID"] = str(data.get('feedsList')[0].get('liveFeedId'))
            tool_helper.load_unload('w', variables)
        else:
            print("No alerts are present")

    @setup_request
    def get_alert_details(self, taskset, **kwargs):
        """GET ALERT DETAILS"""
        variables = tool_helper.load_unload('r')
        if variables.get('alertID'):
            response = taskset.client.get(f"/webconsole/api/Alert/{variables['alertID']}", headers=self.headers,
                                          name="/Alert/{'alertID'}")
            tool_helper.api_response("GET ALERT DETAILS RESPONSE", response)
        else:
            print('Alert ID not found')

    @setup_request
    def get_alert_definitions(self, taskset, **kwargs):
        """GET ALERT RULE"""
        response = taskset.client.get("/webconsole/api/AlertRule?pageNo=1&pageCount=1", headers=self.headers,
                                      name="/AlertRule")
        tool_helper.api_response("GET ALERTRULE RESPONSE", response)
        variables = tool_helper.load_unload('r')
        data = response.json()
        if data.get('myReceiveTotal') > 0:
            variables["alertRuleID"] = str(data.get('alertList')[0].get('alert').get('id'))
            tool_helper.load_unload('w', variables)
        else:
            print("No alert rules are present")

    @setup_request
    def get_alert_definitionDetail(self, taskset, **kwargs):
        """GET ALERT RULE DETAILS"""
        variables = tool_helper.load_unload('r')
        if variables.get('alertRuleID'):
            response = taskset.client.get(f"/webconsole/api/AlertRule/{variables['alertRuleID']}", headers=self.headers,
                                          name="/AlertRule/{'alertRuleID'}")
            tool_helper.api_response("GET ALERT RULE DETAILS RESPONSE", response)
        else:
            print('AlertRule ID not found')

    # TESTCASE 60785
    def get_jobs(self, taskset, **kwargs):
        """GET JOBS USING POST API"""
        variables = tool_helper.load_unload('r')
        payload = """ <?xml version="1.0" encoding="UTF-8"?><JobManager_JobListRequest scope="1" category="0">
                        <jobFilter completedJobLookupTime="300" showAgedJobs="0"/>
                    </JobManager_JobListRequest>"""
        user = choice(variables["locust_user_list"])
        if user in variables:
            headers = tool_helper.headers(
                {'Authtoken': variables[user], 'Accept': 'application/json', 'Content-Type': "application/xml"})
            response = taskset.client.post("""/webconsole/api/jobs""", data=payload, headers=headers,
                                           name="/jobs")
            data = response.json()
            if data.get('totalRecordsWithoutPaging'):
                variables["jobID"] = str(data.get('jobs')[0].get('jobSummary').get('jobId'))
                tool_helper.load_unload('w', variables)
            tool_helper.api_response("GET JOBS RESPONSE", response)

        else:
            print("Locust user not logged in")

    def get_job_details(self, taskset, **kwargs):
        """GET JOBS USING POST API"""
        variables = tool_helper.load_unload('r')
        if variables.get('jobID'):
            payload = f"""<?xml version="1.0" encoding="UTF-8"?><JobManager_JobDetailRequest jobId="{variables['jobID']}">
                                <commcell commCellId="2"/>
                        </JobManager_JobDetailRequest>"""
            user = choice(variables["locust_user_list"])
            if user in variables:
                headers = tool_helper.headers(
                    {'Authtoken': variables[user], 'Accept': 'application/json', 'Content-Type': "application/xml"})
                response = taskset.client.post("""/webconsole/api/JobDetails""", data=payload, headers=headers,
                                               name="/JobDetails")
                tool_helper.api_response("GET JOB DETAILS RESPONSE", response)

            else:
                print("Locust user not logged in")

    @setup_request
    def get_job_events(self, taskset, **kwargs):
        """GET JOB EVENTS"""
        user_id = kwargs.get('user_id')
        variables = tool_helper.load_unload('r')
        params = {
            "userId": user_id,
            "jobId": variables.get('jobID')
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        if variables.get('jobID'):
            response = taskset.client.get("/webconsole/api/events", params=params,
                                          name="/events",
                                          headers=self.headers)
            tool_helper.api_response("GET JOB EVENTS RESPONSE", response)
        else:
            print("JOB ID is not set yet")

    # TESTCASE 61967
    @setup_request
    def get_events(self, taskset, **kwargs):
        """GET EVENTS API"""
        user_id = kwargs.get('user_id')
        params = {
            "userId": user_id,
            "level": "10"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        response = taskset.client.get('/webconsole/api/Events', params=params, name="/event", headers=self.headers)
        variables = tool_helper.load_unload('r')
        tool_helper.api_response("GET EVENTS RESPONSE", response)
        data = response.json()
        if data.get('commservEvents'):
            variables["eventID"] = str(data.get('commservEvents')[0].get('id'))
            tool_helper.load_unload('w', variables)
        else:
            print('No events present in the response')

    @setup_request
    def get_event_details(self, taskset, **kwargs):
        """GET EVENTS DETAILS """
        variables = tool_helper.load_unload('r')
        if variables.get('eventID'):
            response = taskset.client.get(f"/webconsole/api/events/{variables['eventID']}", name="/events/{'eventID'}",
                                          headers=self.headers)
            tool_helper.api_response("GET EVENTS DETAILS RESPONSE", response)
        else:
            print('Event ID is not set')

    # TESTCASE 61969
    @setup_request
    def get_client_anomaly(self, taskset, **kwargs):
        """GET CLIENT ANOMALY"""
        response = taskset.client.get("/webconsole/api/client/Anomaly", headers=self.headers, name="/client/Anomaly")
        tool_helper.api_response("GET CLIENT ANOMALY RESPONSE", response)

    @setup_request
    def get_clientcount_anomaly(self, taskset, **kwargs):
        """GET CLIENT COUNT ANOMALY"""
        response = taskset.client.get("/webconsole/api/clients/count?type=fileserver,vm,laptop", headers=self.headers,
                                      name="/clients/count")
        tool_helper.api_response("GET CLIENT COUNT ANOMALY RESPONSE", response)

    def get_reports(self, taskset, **kwargs):
        """GET REPORTS USING POST API"""
        variables = tool_helper.load_unload('r')
        payload = f""" <?xml version="1.0" encoding="UTF-8"?><WebReport_TagViewEditReq userId="1"/>"""
        user = choice(variables["locust_user_list"])
        if user in variables:
            headers = tool_helper.headers(
                {'Authtoken': variables[user], 'Accept': 'application/json', 'Content-Type': "application/xml"})
            response = taskset.client.post("""/webconsole/api/ReportsTagViewEdit""", data=payload, headers=headers,
                                           name="/ReportsTagViewEdit")
            tool_helper.api_response("GET REPORTS RESPONSE", response)

        else:
            print("Locust user not logged in")

    # testcase 60839 - Commcell page apis
    @setup_request
    def get_commcell_activitycontrol(self, taskset, **kwargs):
        """GET COMCELL ACTIVITY CONTROL"""
        response = taskset.client.get("/webconsole/api/Commcell/ActivityControl", name="/Commcell/ActivityControl",
                                      headers=self.headers)
        tool_helper.api_response("GET COMMCELL ACTIVITY CONTROL", response)

    @setup_request
    def get_commserv(self, taskset, **kwargs):
        """GET COMMSERV API"""
        response = taskset.client.get("/webconsole/api/commserv", name="/commserv",
                                      headers=self.headers)
        tool_helper.api_response("GET COMMSERV RESPONSE", response)

    @setup_request
    def get_emailserver(self, taskset, **kwargs):
        """GET COMMSERV API"""
        response = taskset.client.get("/webconsole/api/Emailserver", name="/Emailserver",
                                      headers=self.headers)
        tool_helper.api_response("GET EMAILSERVER RESPONSE", response)

    @setup_request
    def get_password_encryption_config(self, taskset, **kwargs):
        """GET PASSWORD ENCRYPTION CONFIG API"""
        response = taskset.client.get("/webconsole/api/commcell/passwordencryptionconfig",
                                      name="/commcell/passwordencryptionconfig",
                                      headers=self.headers)
        tool_helper.api_response("GET PASSWORD ENCRYPTION CONFIG RESPONSE", response)

    @setup_request
    def get_security_commcell(self, taskset, **kwargs):
        """GET Security API"""
        response = taskset.client.get("/webconsole/api/Security/1/2", name="/Security/1/2",
                                      headers=self.headers)
        tool_helper.api_response("GET COMMCELL SECURITY  RESPONSE", response)

    @setup_request
    def get_plan_commcell(self, taskset, **kwargs):
        """GET PLAN COMMCELL API"""
        params = {
            "planType": "all",
            "url": "Fl=plans.missingEntities,plans.numAssocEntities,plans.numCopies,plans.parent,plans.permissions,plans.plan.planId,plans.plan.planName,plans.planStatusFlag,plans.restrictions,plans.rpoInMinutes,plans.subtype,plans.type",
            "limit": "20",
            "Sort": "plans.rpoInMinutes:-1",
            "Start": "0"
        }
        if kwargs.get("param"):
            params.update(kwargs['param'])
        response = taskset.client.get("/webconsole/api/v2/Plan", name="/v2/Plan",
                                      headers=self.headers)
        tool_helper.api_response("GET PLAN COMMCELL RESPONSE", response)
        data = response.json()
        if data.get("filterQueryCount"):
            variables = tool_helper.load_unload('r')
            elem = randint(0, len(data.get("plans")) - 1)
            variables['planid'] = data.get("plans")[elem]['plan']['planId']
            tool_helper.load_unload('w', variables)

    @setup_request
    def get_commcell_properties(self, taskset, **kwargs):
        """GET COMMCELL PROPERTIES API"""
        response = taskset.client.get("/webconsole/api/Commcell/Properties", name="/Commcell/Properties",
                                      headers=self.headers)
        tool_helper.api_response("GET COMMCELL PROPERTIES RESPONSE", response)

    def get_slaconfig(self, taskset, **kwargs):
        """GET SLA CONFIG POST API"""
        variables = tool_helper.load_unload('r')
        payload = f"""<?xml version="1.0" encoding="UTF-8"?><WebReport_GetSLAPropertyReq>
                        <entities>
                            <entity subclientId="0" clientGroupId="0" commCellId="2" clientId="0" _type_="1"/>
                        </entities>
                    </WebReport_GetSLAPropertyReq>"""
        user = choice(variables["locust_user_list"])
        if user in variables:
            headers = tool_helper.headers(
                {'Authtoken': variables[user], 'Accept': 'application/json', 'Content-Type': "application/xml"})
            response = taskset.client.post("""/webconsole/api/GetSLAConfiguration""", data=payload, headers=headers,
                                           name="/GetSLAConfiguration")
            tool_helper.api_response("GET SLA CONFIGURATION RESPONSE", response)

        else:
            print("Locust user not logged in")

    # testcase 60783
    @setup_request
    def get_papi_servers(self, taskset, **kwargs):
        """GET SERVERS PAPI API"""
        params = {
            "fq": "clientProperties.isServerClient:eq:true",
            "showOnlyInfrastructureMachines": "1",
            "additionalProperties": "true",
            "start": "0",
            "limit": "20",
            "sort": "client.clientEntity.displayName:1",
            "fl": "clientProperties.client,clientProperties.clientProps"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        response = taskset.client.get("""/webconsole/api/v4/Servers""",
                                      name="/v4/Servers", headers=self.headers, params=params)
        tool_helper.api_response("GET PAPI SERVERS RESPONSE", response)
        variables = tool_helper.load_unload('r')
        data = response.json()
        if data.get('totalServers'):
            param = {
                "Hiddenclients": "false",
                "includeIdaSummary": "true",
                "propertyLevel": "10",
                "excludeInfrastructureClients": "false",
                "infrastructureMachineFilter": "1",
                "fq": "clientProperties.isServerClient%3Aeq%3Atrue",
                "start": "0",
                "limit": "20",
                "sort": "client.clientEntity.displayName:1",
                "fl": "clientProperties.client,clientProperties.clientProps,overview"
            }

            # Parameters for get_client_server to reuse APIs
            variables["get_client_param"] = param
            variables["serverID"] = str(data.get('servers')[0].get('id'))
            tool_helper.load_unload('w', variables)
        else:
            print("No servers are present")

    @setup_request
    def get_client_server(self, taskset, **kwargs):
        """GET CLIENT FILE SERVER"""
        params = {
            "Hiddenclients": "false",
            "includeIdaSummary": "true"
        }
        variables = tool_helper.load_unload('r')
        if variables.get('get_client_param'):
            params.update(variables['get_client_param'])
        if kwargs.get('param'):
            params.update(kwargs['param'])
        response = taskset.client.get("/webconsole/api/client", params=params, headers=self.headers,
                                      name="/client")
        data = response.json()

        # G suite page part
        if data.get("CloudAppsClientsList"):
            elem = randint(0, len(data.get('CloudAppsClientsList')) - 1)
            variables['subclient_param'] = {
                "clientId": data.get('CloudAppsClientsList')[elem].get('client').get('clientId')
            }
            variables['clientId'] = data.get('CloudAppsClientsList')[elem].get('client').get('clientId')
            variables['hyperVapplicationId'] = "134"
            variables['hypervId'] = variables['clientId']
            tool_helper.load_unload('w', variables)
        # TC : 60773 FS SP24
        if data.get("clientProperties"):
            elem = randint(0, len(data.get('clientProperties')) - 1)
            variables["fileserverID"] = str(data['clientProperties'][elem]['client']['clientEntity']['clientId'])
            variables["subclient_param"] = {
                "clientId": variables["fileserverID"],
                "backupsetId": variables.get("backupsetId"),
                "applicationId": 33,
                "propertyLevel": 5,
                "includeBackupInfo": "true"
            }
            tool_helper.load_unload('w', variables)
        if data.get("VSPseudoClientsList"):
            elem = randint(0, len(data.get("VSPseudoClientsList")) - 1)
            variables["fileserverID"] = str(data['VSPseudoClientsList'][elem]["client"]["clientId"])
            tool_helper.load_unload('w', variables)
        tool_helper.api_response("GET CLIENT API RESPONSE", response)

    @setup_request
    def get_client_details(self, taskset, **kwargs):
        """GET CLIENT DETAILS"""
        params = {
            "Hiddenclients": "false",
            "includeIdaSummary": "true",
            "propertyLevel": "10",
            "excludeInfrastructureClients": "false",
            "infrastructureMachineFilter": "!",
            "fq": "clientProperties.isServerClient%3Aeq%3Atrue",
            "start": "0",
            "limit": "20",
            "sort": "client.clientEntity.displayName:1",
            "fl": "clientProperties.client,clientProperties.clientProps,overview"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        variables = tool_helper.load_unload('r')
        if variables.get("serverID", variables.get("fileserverID")):
            response = taskset.client.get(
                f"""/webconsole/api/client/{variables.get("serverID", variables.get("fileserverID"))}""",
                name="/client/{serverID}", headers=self.headers, params=params)
            tool_helper.api_response("GET CLIENT DETAILS", response)
        else:
            print("The server ID is not set")

    @setup_request
    def get_client_patchoptions(self, taskset, **kwargs):
        """GET CLIENT PATCH DETAILS"""
        variables = tool_helper.load_unload('r')
        if variables.get("serverID"):
            response = taskset.client.get(
                f"""/webconsole/api/client/getAdvancedPatchOptions?clientID={variables['serverID']}""",
                name="/getAdvancedPatchOptions?clientID={serverID}", headers=self.headers)
            tool_helper.api_response("GET CLIENT PATCH DETAILS", response)
        else:
            print("The server ID is not set")

    @setup_request
    def get_server_details(self, taskset, **kwargs):
        """GET SERVER DETAILS"""
        variables = tool_helper.load_unload('r')
        id = variables.get("serverID", variables.get("fileserverID"))
        if id:
            response = taskset.client.get(
                f"""/webconsole/api/Server/{id}""", name="/Server/{'serverID'}", headers=self.headers)
            tool_helper.api_response("GET SERVER DETAILS", response)
        else:
            print("The server ID is not set")

    # SERVER GROUP TC : 60784
    @setup_request
    def get_papi_server_groups(self, taskset, **kwargs):
        """GET SERVER GROUP PAPI API"""
        params = {
            "fq": "groups.clientGroup.clientGroupName:neq:Index+Servers",
            "start": "0",
            "limit": "25",
            "sort": "name:1",
            "fl": "groups.clientGroup,groups.discoverRulesInfo,groups.groupAssocType,groups.Id,groups.name"
        }
        if kwargs.get("param"):
            params.update(kwargs["param"])
        response = taskset.client.get("""/webconsole/api/v4/ServerGroup""", params=params,
                                      name="/v4/ServerGroup", headers=self.headers)
        tool_helper.api_response("GET PAPI SERVER GROUPS RESPONSE", response)
        variables = tool_helper.load_unload('r')
        data = response.json()
        if data.get('serverGroups'):
            variables["servergroupID"] = str(data.get('serverGroups')[0].get('id'))
            tool_helper.load_unload('w', variables)
        else:
            print("No servers are present")

    @setup_request
    def get_papi_servergroup_details(self, taskset, **kwargs):
        """GET SERVER DETAILS"""
        variables = tool_helper.load_unload('r')

        if variables.get("servergroupID"):
            params = {
                "fl": "groups.clientGroup,groups.discoverRulesInfo,groups.groupAssocType,groups.Id,groups.name",
                "fq": f"groups.clientGroup.clientGroupId:eq:{variables['servergroupID']}",
                "start": "0",
                "limit": "25",
                "sort": "name:1"
            }
            if kwargs.get("param"):
                params.update(kwargs["param"])
            response = taskset.client.get("""/webconsole/api/v4/ServerGroup""", params=params,
                                          name="/v4/ServerGroup details", headers=self.headers)
            tool_helper.api_response("GET SERVER GROUP DETAILS", response)
        else:
            print("The servergroup ID is not set")

    @setup_request
    def get_clientgroup_permissions(self, taskset, **kwargs):
        """GET CLIENT GROUP PERMISSIONS"""
        variables = tool_helper.load_unload('r')
        if variables.get("servergroupID"):
            response = taskset.client.get(
                f"""/webconsole/api/Security/CLIENT_GROUP_ENTITY/{variables['servergroupID']}/Permissions""",
                name="Security/CLIENT_GROUP_ENTITY/{servergroupID}/Permissions", headers=self.headers)
            tool_helper.api_response("GET CLIENT GROUP PERMISSIONS RESPONSE", response)
        else:
            print("The servergroup ID is not set")

    @setup_request
    def get_client_servergroups(self, taskset, **kwargs):
        """GET CLIENTS FOR SERVERGROUP"""
        variables = tool_helper.load_unload('r')
        params = {
            "fq": f"clientProperties.clientGroups.clientGroupId:eq:{variables['servergroupID']}",
            "showOlyInfrastructureMachines": "0",
            "additionalProperties": "true",
            "start": "0",
            "limit": "20",
            "sort": "client.clientEntity.displayName:1",
            "fl": "clientProperties.client,clientProperties.clientProps,overview"
        }
        if kwargs.get("param"):
            params.update(kwargs["param"])

        if variables.get("servergroupID"):
            response = taskset.client.get(
                f"""/webconsole/api/v4/Servers""", params=params,
                name="/v4/Servers", headers=self.headers)
            tool_helper.api_response("GET CLIENT FOR SECURITY RESPONSE", response)
        else:
            print("The servergroup ID is not set")

    # Testcase 60841 : Organization
    @setup_request
    def get_organization_details(self, taskset, **kwargs):
        """GET ORGANIZATION DETAILS"""
        variables = tool_helper.load_unload('r')
        params = {

        }
        if variables.get("companyID"):
            if kwargs.get("param"):
                params.update(kwargs['param'])
            response = taskset.client.get(
                f"""/webconsole/api/organization/{variables['companyID']}""", params=params,
                name="/organization/{companyID}", headers=self.headers)
            tool_helper.api_response("GET ORGANIZATION DETAILS", response)
        else:
            print("Company ID is not set")

    @setup_request
    def get_company_security(self, taskset, **kwargs):
        """GET COMPANY SECURITY"""
        variables = tool_helper.load_unload('r')
        if variables.get("companyID"):
            response = taskset.client.get(
                f"""/webconsole/api/Security/61/{variables['companyID']}""", name="/Security/61/{companyID}",
                headers=self.headers)
            tool_helper.api_response("GET COMPANY SECURITY RESPONSE", response)
        else:
            print("The company ID IS not set")

    @setup_request
    def get_company_associated_entity(self, taskset, **kwargs):
        """GET COMPANY ASSOCIATED ENTITIES"""
        variables = tool_helper.load_unload('r')
        params = {
            "fq": "clientProperties.client.idaList.0.AgentProperties.isMarkedDeleted:eq:false"
        }
        if variables.get("companyID"):
            if kwargs.get("param"):
                params.update(kwargs.get("param"))
            response = taskset.client.get(
                f"""/webconsole/api/company/{variables['companyID']}/AssociatedEntities""", params=params,
                name="/company/{companyID}/AssociatedEntities",
                headers=self.headers)
            tool_helper.api_response("GET COMPANY ASSOCIATED RESPONSE", response)
        else:
            print("The company ID IS not set")

    @setup_request
    def get_company_anomalies(self, taskset, **kwargs):
        """GET COMPANY ASSOCIATED ENTITIES"""
        response = taskset.client.get(f"""/webconsole/api/CommServ/Anomaly/Entity/Count?anomousEntityType=6""",
                                      name="/CommServ/Anomaly/Entity/Count?anomousEntityType=6",
                                      headers=self.headers)
        tool_helper.api_response("GET COMPANY ANOMALIES RESPONSE", response)

    # TESTCASE 60776 PAPI FILE SERVERS

    @setup_request
    def get_papi_fileservers(self, taskset, **kwargs):
        """GET FILE SERVERS PAPI"""
        params = {
            "showOnlyInfrastructureMachines": 0,
            "additionalProperties": "true",
            "start": "0",
            "limit": "20",
            "sort": "client.clientEntity.displayName:1",
            "fl": "clientProperties.client,clientProperties.clientProps,overview"
        }
        if kwargs.get("param"):
            params.update(kwargs.get("param"))
        response = taskset.client.get("""/webconsole/api/v4/FileServers""", params=params,
                                      name="/v4/FileServers",
                                      headers=self.headers)
        tool_helper.api_response("GET FILESERVERS USING PAPI RESPONSE", response)
        data = response.json()
        if data.get("fileServerCount"):
            variables = tool_helper.load_unload('r')
            variables["fileserverID"] = str(data.get("fileServers")[0].get('id'))
            subclient_param = {
                "clientId": str(data.get("fileServers")[0].get('id')),
                "backupsetId": variables.get("backupsetId"),
                "applicationId": 33,
                "propertyLevel": 5,
                "includeBackupInfo": "true"
            }
            variables['get_client_param'] = {
                "Hiddenclients": "false",
                "includeIdaSummary": "true",
                "propertyLevel": "10",
                "excludeInfrastructureClients": "false",
                "infrastructureMachineFilter": 1,
                "fq": "clientProperties.isServerClient=true",
                "start": 0,
                "limit": 20,
                "sort": "client.clientEntity.displayName:1",
                "fl": "clientProperties.client,clientProperties.clientProps,overview"
            }
            variables["subclient_param"] = subclient_param
            tool_helper.load_unload('w', variables)

        else:
            print("No fileservers")

    @setup_request
    def get_client_shares(self, taskset, **kwargs):
        """GET CLIENT 3DFS SHARES"""
        variables = tool_helper.load_unload('r')
        if variables.get("fileserverID"):
            response = taskset.client.get("/webconsole/api/Client/{}/3DFSShares".format(variables['fileserverID']),
                                          name="/Client/{fileserverID}/3DFSShares", headers=self.headers)
            tool_helper.api_response("GET CLIENT 3DFS SHARES RESPONSE", response)
        else:
            print("File server ID is not set")

    @setup_request
    def get_client_hierarchy(self, taskset, **kwargs):
        """GET CLIENT HIERARCHY"""
        variables = tool_helper.load_unload('r')
        if variables.get("fileserverID"):
            response = taskset.client.get(
                "/webconsole/api/Client/{}/Hierarchy?backedUp=true".format(variables['fileserverID']),
                name="/webconsole/api/Client/{fileserverID}/Hierarchy", headers=self.headers)
            tool_helper.api_response("GET CLIENT HEIRARCHY RESPONSE", response)
        else:
            print("File server ID is not set")

    @setup_request
    def get_backupsets(self, taskset, **kwargs):
        """GET BACKUPSETS API"""
        variables = tool_helper.load_unload('r')
        params = {
            "clientId": variables['fileserverID'],
            "applicationId": "33",
            "excludeLaptopAndDummyBackupsets": "0",
            "propertyLevel": "5"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        if variables.get("fileserverID"):
            response = taskset.client.get("/webconsole/api/Backupsets", params=params,
                                          name="backupsets fileserver", headers=self.headers)
            tool_helper.api_response("GET BACKUPSETS API RESPONSE FOR FILE SERVERS", response)
            data = response.json()
            if data.get("backupsetProperties"):
                variables["backupsetId"] = data.get('backupsetProperties')[0].get('backupSetEntity').get('backupsetId')
                tool_helper.load_unload('w', variables)
        else:
            print("Filserver ID is not set")

    @setup_request
    def get_subclient_fileserver(self, taskset, **kwargs):
        """GET SUBCLIENT DETAILS OF THE FILESERVER"""
        variables = tool_helper.load_unload('r')
        params = {}
        if kwargs.get('param'):
            params.update(kwargs['param'])
        if variables.get("subclient_param"):
            params.update(variables["subclient_param"])
            response = taskset.client.get("/webconsole/api/Subclient", params=params,
                                          name="/Subclient", headers=self.headers)
            tool_helper.api_response("GET SUBCLIENTS API RESPONSE FOR FILE SERVERS", response)
        else:
            print("Filserver ID is not set")

    @setup_request
    def get_role_papi(self, taskset, **kwargs):
        """GET ROLE FILESERVERS"""
        params = {
            "start": "0",
            "limit": "25",
            "sort": "roleProperties.role.roleName%3A1&fl=roleProperties.role"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        response = taskset.client.get("/webconsole/api/v4/Role", params=params,
                                      name="/v4/Role", headers=self.headers)
        tool_helper.api_response("GET ROLE API RESPONSE ", response)

    @setup_request
    def get_jobs_calendar(self, taskset, **kwargs):
        """GET JOBS CALENDAR FOR FILESERVER"""
        variables = tool_helper.load_unload('r')
        params = {
            "dataListResponse": "true",
            "completedJobLookupTime": 172800,
            "agedJobs": "false",
            "jobTypeList": "Backup,SYNTHFULL",
            "fromStartTime": "0",
            "clientIdList": variables.get("fileserverID"),
            "viewLevel": None,
            "toStartTime": "0",
            "applicationIdList": variables.get("applicationIdList", "106"),
            "timezone": "Asia/Kolkata",
            "lastBackup": "true",
            "statusList": "Completed,Completed.w.one.or.more.error"
        }
        if kwargs.get("param"):
            params.update(kwargs["param"])
        if variables.get("get_jobs_param"):
            params.update(variables["get_jobs_param"])

        response = taskset.client.get(f"""/webconsole/api/Jobs/Calendar""",
                                      headers=self.headers, name="/Jobs/Calendar", params=params)
        tool_helper.api_response("GET JOBS CALENDAR Response", response)

    # TESTCASE 60772 Databases
    @setup_request
    def get_db_instances(self, taskset, **kwargs):
        """GET DB INSTANCES PAGE APIS"""
        response = taskset.client.get("""/webconsole/api/databases/instances""", name="/databases/instances",
                                      headers=self.headers)
        tool_helper.api_response("GET DATABASE INSTANCES REPONSE", response)
        data = response.json()
        if data.get("dbInstance"):
            variables = tool_helper.load_unload('r')
            elem = randint(0, len(data["dbInstance"]) - 1)
            variables["dbInstanceID"] = str(data.get("dbInstance")[elem].get("instance").get("instanceId"))
            variables["fileserverID"] = str(data.get("dbInstance")[elem].get("instance").get("clientId"))
            variables["applicationIdList"] = 81
            subclient_param = {
                "clientId": str(data.get("dbInstance")[elem].get("instance").get("clientId")),
                "applicationId": "81",
                "instanceId": variables["dbInstanceID"],
                "backupsetId": 0,
                "propertyLevel": 30
            }
            get_jobs_param = {
                "instanceId": variables["dbInstanceID"],
                "completedJobLookupTime": 345600,
                "agedJobs": "true",
                "applicationIdList": "81",
                "adminConsoleOffset": "-19800",
                "jobTypeList": "Backup",
                "clientIdList": str(data.get("dbInstance")[elem].get("instance").get("clientId"))
            }
            variables["subclient_param"] = subclient_param
            variables["get_jobs_param"] = get_jobs_param
            tool_helper.load_unload('w', variables)

    @setup_request
    def get_db_instance_details(self, taskset, **kwargs):
        """GET DB INSTANCE DETAILS"""
        variables = tool_helper.load_unload('r')
        if variables.get("dbInstanceID"):
            response = taskset.client.get(f"""/webconsole/api/Instance/{variables["dbInstanceID"]}?propertyLevel=30""",
                                          name="/Instance/{dbInstanceID}", headers=self.headers)
            tool_helper.api_response("GET DB INSTANCE DETAILS API RESPONSE", response)
        else:
            print("DB INSTANCE ID IS NOT SET")

    @setup_request
    def get_sql_instance(self, taskset, **kwargs):
        """GET SQL INSTANCE DETAILS"""
        variables = tool_helper.load_unload('r')
        if variables.get("dbInstanceID"):
            response = taskset.client.get(
                f"""/webconsole/api/sql/instance/{variables["dbInstanceID"]}?propertyLevel=20""",
                name="/sql/instance/{InstanceID}", headers=self.headers)
            tool_helper.api_response("GET SQL INSTANCE DETAILS API RESPONSE", response)
        else:
            print("DB INSTANCE ID IS NOT SET")

    @setup_request
    def get_databases(self, taskset, **kwargs):
        """GET DATABASES """
        response = taskset.client.get("/webconsole/api/databases", name="/databases", headers=self.headers)
        tool_helper.api_response("GET DATABASES RESPONSE ", response)
        variables = tool_helper.load_unload('r')
        if response.json().get('dbInstance'):
            data = response.json()
            for i in data["dbInstance"]:
                if i.get("instance").get("instanceId") == int(variables["dbInstanceID"]):
                    variables["db_backupsetID"] = str(i.get("backupset").get("backupsetId"))
                    break
            if variables["db_backupsetID"] != "0":
                tool_helper.load_unload('w', variables)
        else:
            print('Instance ID is not set')

    @setup_request
    def get_database_details(self, taskset, **kwargs):
        """GET DATABASE DETAILS"""
        variables = tool_helper.load_unload('r')
        if variables.get('db_backupsetID') and variables.get("dbInstanceID"):
            response = taskset.client.get(
                f"""/webconsole/api/sql/instance/{variables["dbInstanceID"]}/database/{variables["db_backupsetID"]}""",
                name="sql/instance/{dbInstanceID}/database/{db_backupsetID}", headers=self.headers)
            tool_helper.api_response("GET DATABASE DETAILS", response)
        else:
            print("Either backetset or instance ID is not set")

    @setup_request
    def get_database_clones(self, taskset, **kwargs):
        """GET DATABASE CLONES"""
        response = taskset.client.get("""/webconsole/api/databases/clones""",
                                      name="/databases/clones", headers=self.headers)
        tool_helper.api_response("GET DATABASE CLONES API RESPONSE", response)

    # WORKFLOW PAGE APIs : TESTCASE : 60791
    def get_workflows(self, taskset, **kwargs):
        """GET WORFLOWS POST API"""
        variables = tool_helper.load_unload('r')
        payload = """ <?xml version="1.0" encoding="UTF-8"?><Workflow_GetExecutableWorkflowsRequest/>"""
        user = choice(variables["locust_user_list"])
        if user in variables:
            headers = tool_helper.headers(
                {'Authtoken': variables[user], 'Accept': 'application/json', 'Content-Type': "application/xml"})
            response = taskset.client.post("""/webconsole/api/GetWorkflows""", data=payload, headers=headers,
                                           name="/GetWorkflows")
            tool_helper.api_response("GET WORKFLOWS API RESPONSE", response)
            data = response.json()
            if data.get("container") and len(data.get('container')) > 1:
                variables["workflowId"] = str(data.get("container")[0].get("entity").get("workflowId"))
                tool_helper.load_unload('w', variables)
        else:
            print("Locust User not logged in")

    @setup_request
    def get_workflow_details(self, taskset, **kwargs):
        """GET WORKFLOW DETAILS"""
        variables = tool_helper.load_unload('r')

        if variables.get("workflowId"):
            params = {
                "workflowId": variables["workflowId"],
                "reactForm": "true"
            }
            if kwargs.get('param'):
                params.update(kwargs['param'])

            if variables.get("version") <= "24":
                payload = {
                    "Workflow_GetExecutableWorkflowsRequest": {
                        "workflow": {
                            "workflowId": variables["workflowId"]
                        }
                    }
                }
                response = taskset.client.post("/webconsole/api/GetWorkflows", name="/GetWorkflows/<ID>",
                                               data=json.dumps(payload), headers=self.headers)
                tool_helper.api_response("GET WORKFLOW DETAILS RESPONSE", response)
            else:
                response = taskset.client.get(
                    f"""/commandcenter/api/cr/apps/workflows/form""", params=params,
                    name="/cr/apps/workflows/form", headers=self.headers)
                tool_helper.api_response("GET WORKFLOW DETAILS API RESPONSE", response)
        else:
            print("workflow id is not set")

    @setup_request
    def get_identityservers(self, taskset, **kwargs):
        """GET IDENTITY SERVERS"""
        response = taskset.client.get(f"""/webconsole/api/IdentityServers""",
                                      name="/IdentityServers", headers=self.headers)
        tool_helper.api_response("GET IDENTITY SERVERS API RESPONSE", response)
        data = response.json()
        variables = tool_helper.load_unload('r')
        if len(data.get("identityServers")) and not variables.get("identityserver"):
            variables["identityserver"] = str(data.get("identityServers")[0].get("IdentityServerId"))
            tool_helper.load_unload('w', variables)
        else:
            print("No Identity servers present")

    @setup_request
    def get_identityserver_details(self, taskset, **kwargs):
        """GET IDENTITY SERVER DETAILS"""
        variables = tool_helper.load_unload('r')
        if variables.get("identityserver"):
            response = taskset.client.get(
                f"/webconsole/api/Commcell/DomainController?domainId={variables['identityserver']}",
                name="/Commcell/DomainController?domainId={identityserver}")
            tool_helper.api_response("GET IDENTITY SERVER DETAILS", response)
        else:
            print("Identity server not set")

    @setup_request
    def get_kms(self, taskset, **kwargs):
        """GET KEY MANAGEMENT SERVERS"""
        response = taskset.client.get("/webconsole/api/Commcell/KeyManagementServers",
                                      name="/Commcell/KeyManagementServers",
                                      headers=self.headers)
        tool_helper.api_response("GET KEY MANAGEMENT SERVERS RESPONSE", response)
        data = response.json()
        variables = tool_helper.load_unload('r')
        if len(data.get("keyProviders")) > 1 and not variables.get("keyProviderId"):
            print("key management server")
            variables["keyProviderId"] = str(data.get("keyProviders")[1].get("provider")['keyProviderId'])
            tool_helper.load_unload('w', variables)
        else:
            print("No kms available")

    @setup_request
    def get_kms_details(self, taskset, **kwargs):
        """GET KMS DETAILS """
        variables = tool_helper.load_unload('r')
        if variables.get("keyProviderId"):
            response = taskset.client.get(f"/webconsole/api/Commcell/KeyManagementServers/{variables['keyProviderId']}",
                                          name="/Commcell/KeyManagementServers/{keyProviderId}", headers=self.headers)
            tool_helper.api_response("GET KMS DETAILS RESPONSE", response)
        else:
            print("KMS ID IS NOT SET")

    @setup_request
    def get_credentials(self, taskset, **kwargs):
        """GET CREDENTIALS API :  CREDENTIAL MANAGERS IN SECURITY PAGE"""
        variables = tool_helper.load_unload('r')
        if variables.get("user_id_24"):
            response = taskset.client.get("/webconsole/api/commcell/Credentials?propertyLevel=20",
                                          name="/commcell/Credentials", headers=self.headers)
            tool_helper.api_response("GET CREDENTAILS PAPI RESPONSE", response)
        else:
            response = taskset.client.get("/webconsole/api/v4/Credential", name="/v4/Credential", headers=self.headers)
            tool_helper.api_response("GET CREDENTAILS PAPI RESPONSE", response)

    @setup_request
    def user_details(self, taskset, **kwargs):
        """GET USER DETAILS RESPONSE"""
        variables = tool_helper.load_unload('r')
        if variables.get("user_id"):
            response = taskset.client.get(f"/webconsole/api/v4/user/{variables['user_id']}?additionalProperties=true",
                                          name="/v4/user/{'user_id}", headers=self.headers)
            tool_helper.api_response("GET USER DETAILS RESPONSE", response)
        elif variables.get("user_id_24"):
            response = taskset.client.get(f"/webconsole/api/user/{variables['user_id_24']}?additionalProperties=true",
                                          name="/user/{user_id}", headers=self.headers)
            tool_helper.api_response("GET USER DETAILS RESPONSE", response)
        else:
            print("USER ID IS NOT SET")

    @setup_request
    def usergroup_details(self, taskset, **kwargs):
        """GET USER GROUP DETAILS"""
        user = kwargs.get("username")
        variables = tool_helper.load_unload('r')
        if variables.get("usergroup_id"):
            response = taskset.client.get(
                f"/webconsole/api/v4/usergroup/{variables['usergroup_id']}?additionalProperties=true",
                name="/v4/usergroup/{'usergroup_id}", headers=self.headers)
            tool_helper.api_response("GET USER GROUP DETAILS RESPONSE", response)
        elif variables.get(user + "_usergrouplist"):
            if len(variables[user + "_usergrouplist"]):
                print("Delete created USERGROUP")
                i = variables[user + "_usergrouplist"][randrange(len(variables[user + '_usergrouplist']))]
                response = taskset.client.get(f"/webconsole/api/v4/UserGroup/{i}", headers=self.headers,
                                              name="/v4/UserGroup/{ID}")
                tool_helper.api_response("GET USER GROUP DETAILS RESPONSE", response)
        else:
            print("USER GROUP ID IS NOT SET")

    # DISASTER RECOVERY : TC 60780
    @setup_request
    def get_replication(self, taskset, **kwargs):
        """GET REPLICATION GROUPS"""
        variables = tool_helper.load_unload('r')
        params = {
            "applicationId": "0",
            "appGroupId": "0"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        response = taskset.client.get("/webconsole/api/ReplicationGroups", params=params,
                                      name="/ReplicationGroups", headers=self.headers)
        data = response.json().get("replicationGroups")

        if data and not variables.get("taskID"):
            variables["taskID"] = str(data[0].get("taskDetail").get("task").get('taskId'))
        variables["VMAllocation_param"] = {
            "showResourceGroupPolicy": "true",
            "showNonResourceGroupPolicy": "false",
            "deep": "true"
        }
        tool_helper.load_unload('w', variables)
        tool_helper.api_response('GET REPLICATION GROUPS RESPONSE', response)

    @setup_request
    def get_replicationgroup_detail(self, taskset, **kwargs):
        """GET REPLICATION GROUP DETAILS"""
        variables = tool_helper.load_unload('r')
        if variables.get("taskID"):
            response = taskset.client.get(f"/webconsole/api/Task/{variables['taskID']}/Details",
                                          name="/Task/{taskID}/Details",
                                          headers=self.headers)
            tool_helper.api_response("GET REPLICATION GROUP DETAILS", response)
        else:
            print("TASK ID IS NOT SET")

    @setup_request
    def get_vmallocationpolicy_details(self, taskset, **kwargs):
        """GET VM ALLOCAITON DETAILS USED IN THE RECOVERY TARGET DETAILS"""
        variables = tool_helper.load_unload('r')
        if variables.get("recovery_target_id"):
            response = taskset.client.get(f"""/webconsole/api/VMAllocationPolicy/{variables["recovery_target_id"]}""",
                                          name="/VMAllocationPolicy/recovery_target_id",
                                          headers=self.headers)
            tool_helper.api_response("GET VM ALLOCATION/RECOVERY TARGET DETAILS API", response)
        else:
            print("Recovery target ID is not set")

    @setup_request
    def get_replication_monitor(self, taskset, **kwargs):
        """GET REPLICATION MONITOR"""
        params = {
            "applicationId": "0",
            "taskId": "0",
            "instanceId": "0",
            "subclientId": "0"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        response = taskset.client.get(
            """/webconsole/api/V2/Replications/Monitors/streaming""", params=params,
            name="/V2/Replications/Monitors/streaming",
            headers=self.headers)
        tool_helper.api_response("GET REPLICATION MONITORS RESPONSE", response)

    @setup_request
    def get_failover_groups(self, taskset, **kwargs):
        """GET FAILOVER GROUPS DETAILS"""
        params = {
            "advanced": "false",
            "operationType": "272"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        response = taskset.client.get(
            """/webconsole/api/DRGroups""", params=params,
            name="/DRGroups",
            headers=self.headers)
        tool_helper.api_response("GET FAILOVER GROUPS RESPONSE", response)

    # 60775 TESTCASE
    @setup_request
    def get_papi_vmGroups(self, taskset, **kwargs):
        """GET THE LIST OF VM GROUPS"""
        params = {
            "start": 0,
            "limit": 20,
            "sort": "sc.subClientEntity.subclientName%3A1",
            "fl": "subClientProperties"
        }
        if kwargs.get("param"):
            params.update(kwargs["param"])
        response = taskset.client.get(f"/webconsole/api/v4/VMGroups", name="/v4/VMGroups",
                                      headers=self.headers, params=params)
        tool_helper.api_response("GET VM GROUPS DETAILS PAPI API", response)
        data = response.json()
        variables = tool_helper.load_unload('r')
        if data.get('vmGroupCount') and not variables.get('VMGROUPID'):
            elem = randint(0, len(data.get('vmGroups')) - 1)
            variables['VMGroupdetails'] = {
                "VMGROUPID": str(data.get('vmGroups')[elem].get('vmGroup').get("id")),
                "hyperVisorID": str(data.get('vmGroups')[elem].get('Hypervisor').get("id"))
            }
            get_jobs_param = {
                "dateListResponse": "true",
                "completedJobLookupTime": 604800,
                "agedJobs": "false",
                "applicationIdList": "106",
                "adminConsoleOffset": "-19800",
                "jobTypeList": "Backup,SYNTHFULL",
                "clientIdList": variables['VMGroupdetails']['hyperVisorID'],
                "statusList": "Completed,Completed%20w/%20one%20or%20more%20errors",
                "viewLevel": "VMGROUP"
            }
            # Added this for the get_jobs_calendar
            variables["get_jobs_param"] = get_jobs_param
            # Added this to execute get_client_details API
            variables["serverID"] = str(data.get('vmGroups')[elem].get('Hypervisor').get("id"))
            variables["subclientID"] = str(data.get('vmGroups')[elem].get('vmGroup').get("id"))
            tool_helper.load_unload('w', variables)
        else:
            print("No VM GROUP EXISTS")

    @setup_request
    def get_papi_vmGroupdetails(self, taskset, **kwargs):
        """GET VM GROUP DETAILS USING PAPI"""
        variables = tool_helper.load_unload('r')
        if variables.get('VMGroupdetails'):
            response = taskset.client.get(f"/webconsole/api/v4/VMGroup/{variables['VMGroupdetails']['VMGROUPID']}",
                                          name="/v4/VMGroup/{VMGROUPID}", headers=self.headers)
            tool_helper.api_response("GET VM GROUP DETAILS", response)
        else:
            print("No vm group ID is set")

    # TESTCASE 60774
    # HyperV

    @setup_request
    def get_papi_hyperV(self, taskset, **kwargs):
        """GET LIST OF HYPERVISORS PAPI"""
        params = {
            "additionalProperties": "true",
            "start": "0",
            "limit": "20",
            "sort": "VSPseudoClientsList.client.displayName%3A1",
            "fl": "VSPseudoClientsList"
        }
        if kwargs.get("param"):
            params.update(kwargs["param"])
        response = taskset.client.get("/webconsole/api/v4/Hypervisor", params=params, name="/v4/Hypervisor",
                                      headers=self.headers)
        variables = tool_helper.load_unload('r')
        tool_helper.api_response("GET PAPI HYPERVISORS RESPONSE", response)
        data = response.json()
        if data.get('HypervisorCount') and not variables.get("hypervId"):
            variables['hyperVapplicationId'] = "134"
            elem = randint(0, len(data.get('Hypervisors')) - 1)
            variables["hypervId"] = str(data.get("Hypervisors")[elem].get('id'))
            variables["HypervisorType"] = data.get("Hypervisors")[elem].get('HypervisorType')
            variables['tag_entity'] = str(variables["hypervId"])
            variables["get_jobs_param"] = {
                "dateListResponse": "true", "lastBackup": "true",
                "completedJobLookupTime": "604800",
                "agedJobs": "false",
                "jobTypeList": "Backup,SYNTHFULL",
                "fromStartTime": "0",
                "toStartTime": "0",
                "applicationIdList": "106",
                "statusList": "Completed,Completed%20w/%20one%20or%20more%20errors",
                "clientIdList": variables["hypervId"],
                "viewLevel": "VMGROUP"
            }
            variables['get_client_param'] = {
                "additionalProperties": "true",
                "PseudoClientType": "VSPseudoClientsList",
                "status": "0",
                "excludeVendorId": "20",
                "sort": "VSPseudoClientsList.client.displayName:1",
                "fl": "VSPseudoClientsList"
            }
            tool_helper.load_unload('w', variables)

    @setup_request
    def get_papi_hypervDetails(self, taskset, **kwargs):
        """GET HYPER V DETAILS USING PAPI"""
        variables = tool_helper.load_unload('r')
        if variables.get("hypervId"):
            response = taskset.client.get("/webconsole/api/v4/Hypervisor/{}".format(variables['hypervId']),
                                          name="v4/Hypervisor/{ID}",
                                          headers=self.headers)
            tool_helper.api_response("GET HYPER V DETAILS USING PAPI", response)
        else:
            print("HYPERV ID is not set")

    @setup_request
    def get_vsaclientlist(self, taskset, **kwargs):
        """GET VSA CIENT LIST"""
        user_id = kwargs.get('user_id')
        variables = tool_helper.load_unload('r')
        if variables.get('HypervisorType'):
            params = {
                "userId": user_id,
                "filter": variables['HypervisorType']
            }
            if kwargs.get("param"):
                params.update(kwargs["param"])
            response = taskset.client.get("/webconsole/api/VSAClientList", name="/VSAClientList", headers=self.headers,
                                          params=params)
            tool_helper.api_response("GET VSA CLIENT LIST", response)
        else:
            print("HyperV type is not set")

    @setup_request
    def get_instance_hyperv(self, taskset, **kwargs):
        """GET INSTANCE DETAILS FOR A HYPERV"""
        variables = tool_helper.load_unload('r')
        if variables.get("hypervId", variables.get("fileserverID")):
            params = {
                "clientId": variables.get('hypervId', variables.get("fileserverID")),
                "applicationId": variables.get('hyperVapplicationId', kwargs.get('hyperVapplicationId'))
            }
            if kwargs.get("param"):
                params.update(kwargs["param"])
            response = taskset.client.get("/webconsole/api/Instance", params=params,
                                          name="/api/Instance",
                                          headers=self.headers)
            tool_helper.api_response("GET Instance Details for hyperv", response)
            variables["subclient_param"] = {
                "clientId": variables.get('hypervId', variables.get("fileserverID")),
                "applicationId": variables.get('hyperVapplicationId', kwargs.get('hyperVapplicationId')),
                "PropertyLevel": "5",
                "includeVMPseudoSubclients": "false",
                "excludeVendorId": "20",
                "Fl": "overview,subClientProperties.subClientEntity,subClientProperties.status,"
                      "subClientProperties.planEntity,subClientProperties.vsaSubclientProp,"
                      "subClientProperties.commonProperties.isDefaultSubclient,"
                      "subClientProperties.commonProperties.lastBackupTime,"
                      "subClientProperties.commonProperties.lastBackupSize,"
                      "subClientProperties.fsSubClientProp.extendStoragePolicyRetention,"
                      "subClientProperties.indexingInfo.indexingStatus,"
                      "subClientProperties.commonProperties.lastBackupJobInfo,"
                      "subClientProperties.commonProperties.snapCopyInfo.isSnapBackupEnabled",
                "Sort": "sc.subClientEntity.subclientEntityName.subclientName:1",
                "Limit": "20",
                "Start": "0"
            }
            tool_helper.load_unload('w', variables)
        else:
            print("HyperV id is not set")

    @setup_request
    def get_application(self, taskset, **kwargs):
        """GET APPLICATION API USED IN HYPERV DETAILS"""
        param = kwargs.get('param')
        application = param.get("applicationID")
        response = taskset.client.get("/webconsole/api/Application/" + application,
                                      name="/Application/ID",
                                      headers=self.headers)
        tool_helper.api_response("GET APPLICATION FOR HyperV DETAILS", response)

    @setup_request
    def get_mediaagent_recoveryenabler(self, taskset, **kwargs):
        """GET MEDIA AGENT RECOVERY ENABLED : HYPERV"""
        response = taskset.client.get("/webconsole/api/MediaAgent/RecoveryEnabler?osType=CLIENT_PLATFORM_OSTYPE_UNIX",
                                      name="/MediaAgent/RecoveryEnabler", headers=self.headers)
        tool_helper.api_response("GET MEDIA AGENT RECOVERY ENABLER", response)

    # TESTCASE : 60779
    @setup_request
    def get_office_apps(self, taskset, **kwargs):
        """GET OFFICE APPS LIST"""
        param = kwargs.get("param")
        params = {
            "agentType": "7"
        }
        if param:
            params.update(param)
        response = taskset.client.get("/webconsole/api/Office365/entities", params=params, name="/Office365/entities",
                                      headers=self.headers)
        tool_helper.api_response("GET OFFICE 365 APPS RESPONSE", response)
        data = response.json()
        variables = tool_helper.load_unload('r')
        if data.get("o365Client"):
            elem = randint(0, len(data.get('o365Client')) - 1)
            variables['office365app_id'] = str(data.get('o365Client')[elem].get("clientId"))
            variables["backupsetId"] = str(data.get('o365Client')[elem].get("O365BackupSet")[0].get('backupsetId'))
            variables["officeapp_type"] = str(data.get('o365Client')[elem].get("O365BackupSet")[0].get('type'))
            variables["subclient_entity"] = str(data.get('o365Client')[elem].get("O365BackupSet")[0].get('subclientId'))
            tool_helper.load_unload('w', variables)
        else:
            print("No office 365 apps present/ ID is already added")

    @setup_request
    def get_office_app_details(self, taskset, **kwargs):
        """GET OFFICE APP DETAILS"""
        variables = tool_helper.load_unload('r')
        param = {
            "opType": 0,
            "backupsetId": variables.get('backupsetId')
        }
        if kwargs.get("param"):
            param.update(kwargs["param"])
        if variables.get('office365app_id'):
            response = taskset.client.get(f"/webconsole/api/Office365/Client/{variables['office365app_id']}",
                                          name="/Office365/Client/{office365app_id}", headers=self.headers,
                                          params=param)
            tool_helper.api_response("GET OFFICE 365 APP DETAILS RESPONSE", response)
        else:
            print("Office app id is not set ")

    # TYPE 1 : Outlook
    # TYPE 2 : SHAREPOINT
    # TYPE 3 : Onedrive
    # TYPE 6 : Teams
    @setup_request
    def get_security_subclient(self, taskset, **kwargs):
        """GET SECURITY SUBCLIENT"""
        variables = tool_helper.load_unload('r')
        if variables.get('subclient_entity'):
            response = taskset.client.get(
                f"/webconsole/api/Security/SUBCLIENT_ENTITY/{variables['subclient_entity']}/Permissions",
                name="/Security/SUBCLIENT_ENTITY/{subclient_entity}/Permissions", headers=self.headers)
            tool_helper.api_response("GET SECURITY SUBCLIENT ENTITY RESPONSE", response)
        else:
            print("subclient_entity id is not set ")

    @setup_request
    def get_cloudapp_userpolicy(self, taskset, **kwargs):
        """GET CLOUDAPPS USER POLICY"""
        variables = tool_helper.load_unload('r')
        if variables.get('subclient_entity') and variables['officeapp_type'] != '3':
            payload = f"""<?xml version="1.0" encoding="UTF-8"?><Ida_GetCloudAppPolicyAssociationReq discoverByType="1" bIncludeDeleted="0">
                        <cloudAppAssociation>
                            <subclientEntity subclientId="{variables['subclient_entity']}"/>
                        </cloudAppAssociation>
                        <pagingInfo pageNumber="0" pageSize="15"/>
                        <searchInfo isSearch="0" searchKey=""/>
                        <sortInfo sortColumn="1" sortOrder="0"/>
                    </Ida_GetCloudAppPolicyAssociationReq>
                """
            headers = self.headers
            headers['Content-Type'] = 'application/xml'
            response = taskset.client.post("/webconsole/api/Office365/CloudApps/UserPolicyAssociation", headers=headers,
                                           name="/Office365/CloudApps/UserPolicyAssociation", data=payload)
            tool_helper.api_response("GET CLOUD APPS USER POLICY ASSOCIATION RESPONSE", response)
        else:
            if not variables['officeapp_type'] != '3':
                print("The subclient Id Not set : get cloudapp user policy association ")

    @setup_request
    def office_appspecific_api(self, taskset, **kwargs):
        """Office app specific api for outlook / sharepoint"""
        variables = tool_helper.load_unload('r')
        if variables.get("backupsetId"):
            if variables["officeapp_type"] == '2':
                response = taskset.client.get(f"/webconsole/api/Backupset/{variables['backupsetId']}?propertyLevel=30",
                                              name="/Backupset/{backupsetId}", headers=self.headers)
                tool_helper.api_response("GET BACKUPSET DETAILS API RESPONSE", response)
            elif variables['officeapp_type'] == '1':
                payload = f"""
                 <?xml version="1.0" encoding="UTF-8"?><Ida_GetEmailPolicyAssociationReq level="30" discoverType="1">
                    <emailAssociation>
                        <advanceOptions isSelectInactiveMailboxes="0" isSelectDoNotArchiveMailboxes="1"/>
                        <subclientEntity subclientId="{variables['subclient_entity']}"/>
                    </emailAssociation>
                    <pagingInfo pageNumber="0" pageSize="15"/>
                    <searchInfo isSearch="0" searchKey=""/>
                    <sortInfo sortColumn="1" sortOrder="0"/>
                </Ida_GetEmailPolicyAssociationReq>
                """
                headers = self.headers
                headers['Content-Type'] = 'application/xml'
                response = taskset.client.post("/webconsole/api/Exchange/Mailboxes", headers=headers,
                                               name="/Exchange/Mailboxes", data=payload)
                tool_helper.api_response("POST EXCHANGE MAILBOXES", response)
        else:
            print("Backupset ID not set: office_appspecific API")

    # TESTCASE : 62048
    @setup_request
    def get_active_directory_clients(self, taskset, **kwargs):
        """GET ACTIVE DIRECTORY CLIENTS API"""
        response = taskset.client.get("/webconsole/api/ActiveDirectory/Clients?apptypeId=0",
                                      name="/ActiveDirectory/Clients",
                                      headers=self.headers)
        tool_helper.api_response("GET ACTIVE DIRECTORY CLIENT LIST RESPONSE ", response)
        data = response.json()
        variables = tool_helper.load_unload('r')
        if data.get("adClient"):
            elem = randint(0, len(data.get('adClient')))
            variables['office365app_id'] = str(data.get('adClient')[elem].get("subClientEntity").get("clientId"))
            variables["backupsetId"] = str(data.get('adClient')[elem].get("subClientEntity").get('backupsetId'))
            variables["subclient_entity"] = str(data.get('adClient')[elem].get("subClientEntity").get('subclientId'))
            variables['subclient_param'] = {
                "clientId": variables['office365app_id'],
                "applicationId": "41",
                "backupsetId": variables["backupsetId"],
                "propertyLevel": "30"
            }
            variables['agent_param'] = {
                "clientId": variables['office365app_id'],
                "propertyLevel": 20
            }
            tool_helper.load_unload('w', variables)
        else:
            print("No active directory is configured")

    @setup_request
    def get_agent(self, taskset, **kwargs):
        """GET AGENT API """
        param = kwargs.get("param",{})
        variables = tool_helper.load_unload('r')
        if variables.get("agent_param"):
            param.update(variables['agent_param'])
            response = taskset.client.get("/webconsole/api/Agent", params=param, name="/Agent", headers=self.headers)
            tool_helper.api_response("GET AGENT API RESPONSE", response)
            response = taskset.client.get("/webconsole/api/instance/CloudApps", name="/instance/CloudApps",
                                          headers=self.headers)
            tool_helper.api_response("GET INSTANCE CLOUDAPPS API RESPONSE : PAGE Devops", response)

    # EXCHANGE PAGE
    @setup_request
    def get_exchange_clients(self, taskset, **kwargs):
        """GET EXCHANGE CLIENTS API"""
        response = taskset.client.get("/webconsole/api/Exchange/clients", name="/Exchange/clients",
                                      headers=self.headers)
        tool_helper.api_response("GET EXCHANGE CLIENTS RESPONSE : EXCHANGE PAGE", response)
        data = response.json()
        if data.get("exchangeClientList"):
            variables = tool_helper.load_unload('r')
            elem = randint(0, len(data.get('exchangeClientList')))
            variables["backupsetId"] = str(data.get('exchangeClientList')[elem].get("subclient").get("backupsetId"))
            variables["subclient_entity"] = str(
                data.get('exchangeClientList')[elem].get("subclient").get('subclientId'))
            variables["officeapp_type"] = "1"
            variables['office365app_id'] = str(data.get('exchangeClientList')[elem].get("subclient").get('clientId'))
            tool_helper.load_unload('w', variables)
            response = taskset.client.get(
                "/webconsole/api/Exchange/clients?subclientId=" + variables["subclient_entity"],
                headers=self.headers, name="exchange client with subclient ID")
            tool_helper.api_response("GET EXCHANGE CLIENTS API RESPONSE WTH SUBCLIENT ID", response)
            # Use get_client_server for /client?PseudoClientType=Cloudapps : G suite page

    # TESTCASE 62048 : SHAREPOINT PAGE APIs
    @setup_request
    def get_sharepoint_clients(self, taskset, **kwargs):
        """GET THE LIST OF SHAREPOINT CLIENTS"""
        response = taskset.client.get("/webconsole/api/Office365/SharePoint/Clients", headers=self.headers,
                                      name="/Office365/SharePoint/Clients")
        tool_helper.api_response("GET LIST OF SHAREPOINT CLIENTS", response)
        data = response.json()
        variables = tool_helper.load_unload('r')
        if data.get("o365Client"):
            elem = randint(0, len(data.get('o365Client')) - 1)
            variables["backupsetId"] = str(data.get('o365Client')[elem].get("O365BackupSet")[0].get('backupsetId'))
            variables["officeapp_type"] = "2"
            variables['subclient_param'] = {
                "clientId": str(data.get('o365Client')[elem].get("clientId")),
                "applicationId": "78",
                "instanceId": "0",
                "backupsetId": variables["backupsetId"],
                "propertyLevel": "30"
            }
            tool_helper.load_unload('w', variables)
        else:
            print("Share point clients aren't present")

    @setup_request
    def get_client_v2_plan(self, taskset, **kwargs):
        """GET CLIENT V2 Plan API"""
        variables = tool_helper.load_unload('r')
        params = {
            "propertyLevel": "20"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        if variables.get("clientId"):
            response = taskset.client.get("/webconsole/api/Client/{}/V2/Plan".format(variables['clientId']),
                                          params=params, headers=self.headers,
                                          name="/Client/{ID}/V2/Plan")
            tool_helper.api_response("GET CLIENT V2 PLAN API RESPONSE", response)
        else:
            print("CLIENT ID IS NOT SET : Get client v2 plan")

    # TESTCASE 60767
    # GUIDED SETUP PAGE
    @setup_request
    def get_commserve_ftp(self, taskset, **kwargs):
        """GET COMMSERV FTPSERVICE PACK"""
        params = {
            "ReleaseName": "11.0.0"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        response = taskset.client.get("/webconsole/api/Commserv/FTPServicePack", params=params, headers=self.headers,
                                      name="/Commserv/FTPServicePack")
        tool_helper.api_response("GET COMMSERV FTPSERVICE PACK RESPONSE", response)

    @setup_request
    def get_schedules(self, taskset, **kwargs):
        """GET SCHEDULES API"""
        params = {
            "operationType": "DOWNLOAD_UPDATES",
            "isSystem": "true",
            "getAllDetails": "true"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        response = taskset.client.get("/webconsole/api/Schedules", params=params, headers=self.headers,
                                      name="/Schedules")
        tool_helper.api_response("GET SCHEDULES API RESPONSE", response)

    @setup_request
    def get_papi_cloudstorage(self, taskset, **kwargs):
        """GET PAPI CLOUD STORAGE"""
        params = {
            "additionalProperties": "true"
        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        response = taskset.client.get("/webconsole/api/v4/CloudStorage", name="/v4/CloudStorage", headers=self.headers)
        tool_helper.api_response("GET PAPI CLOUD STORAGE RESPONSE", response)
        data = response.json()
        if data.get("cloudStorage"):
            variables = tool_helper.load_unload('r')
            elem = randint(0, len(data.get('cloudStorage')) - 1)
            variables['cloudstorageid'] = str(data.get('cloudStorage')[elem].get('id'))
            tool_helper.load_unload('w', variables)
        else:
            print("Cloud storage does not exists")

    # Hyperscale X :
    @setup_request
    def get_hyperscalex_papi(self, taskset, **kwargs):
        """GET HYPERSCALE X PAPI"""
        param = {"additionalProperties": "true"}
        if kwargs.get('param'):
            param.update(kwargs['param'])
        response = taskset.client.get("/webconsole/api/v4/Storage/HyperScale", params=param, name="/v4/Storage/HyperScale",
                                      headers=self.headers)
        tool_helper.api_response("GET HYPERSCALE X PAPI RESPONSE", response)
        data = response.json()
        if data.get("hyperScaleStorage"):
            variables = tool_helper.load_unload('r')
            elem = randint(0, len(data.get('hyperScaleStorage')) -1 )
            variables["diskID"] = data["hyperScaleStorage"][elem]['id']
            tool_helper.load_unload('w', variables)

    # TESTCASE 60845
    # FILE STORAGE OPTIMIZATION
    @setup_request
    def get_ediscovery_clients(self, taskset, **kwargs):
        """GET THE LIST OF THE EDISCOVERED ELIGIBLE CLIENTS"""
        params = {
            "datasourceType": "5%2C40",
            "clientGroup": "0",
            "limit": "10",
            "offset": "0",
            "sortBy": "1",
            "sortDir": "0"
        }
        if kwargs.get("param"):
            params.update(kwargs['param'])

        response = taskset.client.get("/webconsole/api/v2/EdiscoveryClients/Clients", headers=self.headers,
                                      name="/v2/EdiscoveryClients/Clients", params=params)
        tool_helper.api_response("GET EDISCOVERY CLIENTS RESPONSE", response)
        data = response.json()
        if data.get("totalClientCount"):
            variables = tool_helper.load_unload('r')
            variables['client_id_fsoptimization'] = str(data.get('nodeList')[0].get('clientEntity').get('clientId'))
            tool_helper.load_unload('w', variables)

        response = taskset.client.get("/webconsole/api/EDiscoveryClients/GetEligibleDCPlans",
                                      headers=self.headers, name="EDiscoveryClients/GetEligibleDCPlans")
        tool_helper.api_response("GET EDISCOVERYCLIENTS GETELIGIBLEDC PLANS RESPONSE", response)

    @setup_request
    def get_ediscovery_client_details(self, taskset, **kwargs):
        """GET THE DETAILS OF A EDISCOVERY CLIENT"""
        variables = tool_helper.load_unload('r')
        params = {
            "includeDocCount": 0
        }
        if kwargs.get("param"):
            params.update(kwargs['param'])
        if variables.get("client_id_fsoptimization"):
            response = taskset.client.get(
                f"/webconsole/api/v2/EDiscoveryClients/Clients/{variables['client_id_fsoptimization']}",
                headers=self.headers, params=params, name="/v2/EDiscoveryClients/Clients/{ID}")
            tool_helper.api_response("GET EDISCOVERY CLIENT DETAILS API RESPONSE", response)

    @setup_request
    def get_case_managers(self, taskset, **kwargs):
        """GET THE LIST OF CASE MANAGERS"""
        response = taskset.client.get("/webconsole/api/EDiscoveryClients/CaseManagerDetails",
                                      name="EDiscoveryClients/CaseManagerDetails", headers=self.headers)
        tool_helper.api_response("GET CASE MANAGERS API RESPOSNE", response)

    @setup_request
    def entity_managers(self, taskset, **kwargs):
        """GET ENTITY MANAGERS"""
        response = taskset.client.get("/webconsole/api/EntityExtractionRules?getDisabled=true",
                                      name="/EntityExtractionRulse", headers=self.headers)
        tool_helper.api_response("GET ENTITY MANAGERS API RESPONSE", response)
        response = taskset.client.get("/webconsole/api/dcube/classifiers?getDisabled=true", name="/dcube/classifiers",
                                      headers=self.headers)
        tool_helper.api_response("GET DCUBE CLASSIFIERS RESPONSE", response)

    @setup_request
    def request_manager(self, taskset, **kwargs):
        """GET LIST OF REQUEST MANAGERS(ACTIVATE)"""
        payload = {
            "WebReport_GetCommcellProfileReq": ""
        }
        response = taskset.client.post("/webconsole/api/GetCommcellProfileReq", name="/GetCommcellProfileReq",
                                       data=json.dumps(payload), headers=self.headers)
        tool_helper.api_response("GET REQUEST MANAGERS : GetCommcellProfileReq RESPONSE", response)
        response = taskset.client.get("/webconsole/api/getCIServerList?mode=2", name="/getCIServerList",
                                      headers=self.headers)
        tool_helper.api_response("GET REQUEST MANAGERS : getCIServerList RESPONSE", response)

    # TESTCASE 60881
    @setup_request
    def get_clientgroup_api(self, taskset, **kwargs):
        """GET CLIENT GROUP API FOR SP24 SERVER GROUP PAGE"""
        params = {
            "Fl": "groups.clientGroup,groups.discoverRulesInfo,groups.groupAssocType,groups.Id,groups.isDiscoveredClientGroup,groups.isSmartClientGroup,groups.name",
            "Sort": "groups.name%3A1",
            "limit": "20",
            "start": "0"

        }
        if kwargs.get('param'):
            params.update(kwargs['param'])
        response = taskset.client.get("/webconsole/api/ClientGroup", params=params, headers=self.headers,
                                      name="/ClientGroup API")
        tool_helper.api_response("GET CLIENT GROUPS LIST API RESPONSE", response)
        data = response.json()
        if data.get("filterQueryCount"):
            variables = tool_helper.load_unload("r")
            elem = randint(0, len(data["groups"]) - 1)
            variables["clientgroupid"] = str(data.get("groups")[elem]["Id"])
            tool_helper.load_unload('w', variables)

    @setup_request
    def get_cg_details(self, taskset, **kwargs):
        """GET CLIENT GROUP DETAILS"""
        variables = tool_helper.load_unload('r')
        if variables.get("clientgroupid"):
            id = variables['clientgroupid']
            get_client_param = {
                "Hiddenclients": "false",
                "includeIdaSummary": "true",
                "propertyLevel": "10",
                "clientGroupId": id,
                "includevm": "true",
                "excludeInfrastructureClients": "false",
                "Fl": "clientProperties.client,clientProperties.clientProps,overview",
                "Sort": "client.clientEntity.displayName:1",
                "Limit": "20",
                "start": "0",
                "fq": "clientProperties.clientGroups.clientGroupId:eq" + id
            }
            tool_helper.load_unload('w', variables)
            variables['get_client_param'] = get_client_param
            response = taskset.client.get("/webconsole/api/Clientgroup/" + id, headers=self.headers,
                                          name="/Clientgroup/id")
            tool_helper.api_response("GET CLIENT GROUP DETAILS API", response)

    # C R U D
    @setup_request
    def create_usergroup_papi(self, taskset, **kwargs):
        """CREATE USER GROUP"""
        payload = {
            "userGroupType": "LOCAL",
            "name": "PAPIUserGroup_Locust" + kwargs.get('username') + str(datetime.now()) + str(randint(0, 1000)),
            "description": "PAPIUserGroup created for Automation",
            "enforceFSQuota": "false",
            "quotaLimitInGB": 0,
        }
        response = taskset.client.post("/webconsole/api/v4/UserGroup", data=json.dumps(payload), headers=self.headers,
                                       name="/v4/UserGroup")
        tool_helper.api_response("CREATE USER GROUP PAPI RESPONSE", response)
        variables = tool_helper.load_unload('r')
        if response.status_code == 200:
            data = response.json()
            variables["flag"] = 1
            id = str(data['id'])
            tool_helper.check_key(variables, kwargs.get('username') + "_usergrouplist", "user_group_list", id)

    # usergroup_details : to read

    @setup_request
    def update_usergroup_papi(self, taskset, **kwargs):
        """UPDATE THE USERGROUP PAPI"""
        user = kwargs.get("username")
        variables = tool_helper.load_unload('r')
        if variables.get(user + "_usergrouplist"):
            if len(variables[user + "_usergrouplist"]) > 0:
                i = variables[user + "_usergrouplist"][randrange(len(variables[user + "_usergrouplist"]))]
                payload = {
                    "newDescription": "Modifying description via automation",
                    "enabled": "false",
                    "enforceFSQuota": "true",
                    "quotaLimitInGB": 85920917,
                    "enableTwoFactorAuthentication": "ON",
                    "laptopAdmins": "false",
                    "userOperationType": "ADD"
                }
                response = taskset.client.put("/webconsole/api/v4/UserGroup/{}".format(i), headers=self.headers,
                                              name="/v4/UserGroup/{ID}", data=json.dumps(payload))
                tool_helper.api_response("UPDATE CLIENT GROUP USING PAPI RESPONSE", response)
            else:
                print("No user group for this user")

    @setup_request
    def delete_usergroup_papi(self, taskset, **kwargs):
        """DELETE USER GROUP PAPI"""
        user = kwargs.get("username")
        variables = tool_helper.load_unload('r')
        if variables.get(user + "_usergrouplist"):
            if len(variables[user + "_usergrouplist"]) > 0:
                i = variables[user + "_usergrouplist"].pop(randrange(len(variables[user + "_usergrouplist"])))
                params = {
                    "skipOwnerShipTransfer": "true"
                }
                response = taskset.client.delete(f"/webconsole/api/v4/UserGroup/{i}", name="/v4/UserGroup/{id}",
                                                 headers=self.headers,
                                                 params=params)
                if response.status_code == 200:
                    print("User Group Successfully deleted")
                    tool_helper.api_response("DELETE USER GROUP RESPONSE", response)
                else:
                    variables[user + "_usergrouplist"].append(i)
                    tool_helper.load_unload('w', variables)
                    print("User group could not be deleted")
            else:
                print("No user group is present")

        # CRUD ROLE PAPi

    # CRUD ROLE
    @setup_request
    def papi_create_role(self, taskset, **kwargs):
        """API TO CREATE ROLE"""
        role_name = f"locust_role_{kwargs.get('username')}" + str(datetime.now()) + str(randint(0, 1000))
        data = {
            "name": role_name,
            "permissionList": [
                {
                    "permission": {
                        "id": 0,
                        "name": "string"
                    },
                    "category": {
                        "id": 0,
                        "name": "string"
                    }
                }
            ],
            "enabled": "true",
            "visibleToAll": "true"
        }
        response = taskset.client.post("/webconsole/api/v4/Role", data=json.dumps(data), name="/v4/Role C",
                                       headers=self.headers)
        tool_helper.api_response("CREATE ROLE API RESPONSE", response)
        if response.status_code == 200:
            variables = tool_helper.load_unload('r')
            output = response.json()
            variables["flag"] = 1
            id = str(output['id'])
            tool_helper.check_key(variables, kwargs.get('username') + "_rolelist", "role_list", id)

    @setup_request
    def get_role_details_papi(self, taskset, **kwargs):
        """GET ROLE DETAILS PAPI"""
        variables = tool_helper.load_unload('r')
        user = kwargs.get('username')
        if variables.get(user + "_rolelist"):
            if len(variables[user + "_rolelist"]):
                i = variables[user + "_rolelist"][randrange(len(variables[user + '_rolelist']))]
                response = taskset.client.get(f"/webconsole/api/v4/role/{i}", headers=self.headers,
                                              name="/v4/role/{id} R")
                tool_helper.api_response("GET ROLE DETAILS RESPONSE", response)

    @setup_request
    def papi_update_role(self, taskset, **kwargs):
        """API TO UPDATE THE ROLE"""
        role_name = f"locust_role_{kwargs.get('username')}" + str(datetime.now()) + str(randint(0, 1000))
        data = {
            "newName": role_name,
            "permissionList": [
                {
                    "permission": {
                        "id": 0,
                        "name": "string"
                    },
                    "category": {
                        "id": 0,
                        "name": "string"
                    }
                }
            ],
            "enabled": 'true',
            "visibleToAll": 'true',
            "security": [
                {
                    "user": {
                        "id": 0,
                        "name": "string"
                    },
                    "userGroup": {
                        "id": 0,
                        "name": "string"
                    },
                    "role": {
                        "id": 0,
                        "name": "string"
                    }
                }
            ]
        }
        user = kwargs.get('username')
        variables = tool_helper.load_unload('r')
        if variables.get(user + "_rolelist"):
            if len(variables[user + "_rolelist"]) > 0:
                i = variables[user + "_rolelist"][randrange(len(variables[user + "_rolelist"]))]
                response = taskset.client.put("/webconsole/api/v4/role/{}".format(i), headers=self.headers,
                                              name="/v4/role/{ID} U", data=json.dumps(data))
                tool_helper.api_response("UPDATE ROLE USING PAPI RESPONSE", response)
            else:
                print("No Role remains for this user")

        else:
            print("No role remains for user")

    @setup_request
    def delete_role(self, taskset, **kwargs):
        """DELETE ROLE USING PAPI"""
        user = kwargs.get("username")
        variables = tool_helper.load_unload('r')
        if variables.get(user + "_rolelist"):
            if len(variables[user + "_rolelist"]) > 0:
                i = variables[user + "_rolelist"].pop(randrange(len(variables[user + "_rolelist"])))
                response = taskset.client.delete(f"/webconsole/api/v4/role/{i}", name="/api/v4/role/{id} D",
                                                 headers=self.headers)
                if response.status_code == 200:
                    print("Role Successfully deleted")
                    tool_helper.api_response("DELETE ROLE RESPONSE", response)
                else:
                    variables[user + "_rolelist"].append(i)
                    print("Role could not be deleted")
                tool_helper.load_unload('w', variables)
            else:
                print("No role is present")

        # CRUD SERVER GROUP

    # CRUD SERVER GROUP
    @setup_request
    def create_servergroup(self, taskset, **kwargs):
        """CREATE SERVER GROUP USING API"""
        payload = {
            "clientGroupOperationType": 1,
            "clientGroupDetail": {
                "description": "client group created for PAPI Testing",
                "clientGroup": {
                    "clientGroupName": "Locust_" + str(datetime.now()) + str(randint(0, 1000)),
                }
            }
        }
        response = taskset.client.post("/webconsole/api/ClientGroup", data=json.dumps(payload),
                                       name="/ClientGroup C",
                                       headers=self.headers)
        tool_helper.api_response("CREATE SERVER GROUP API RESPONSE", response)
        if response.status_code == 200:
            variables = tool_helper.load_unload('r')
            output = response.json()
            variables["flag"] = 1
            id = str(output['clientGroupDetail']['clientGroup']['clientGroupId'])
            tool_helper.check_key(variables, kwargs.get('username') + "_clientgrouplist", "clientgroup_list", id)

    @setup_request
    def get_servergroup_id_details_api(self, taskset, **kwargs):
        """GET CLIENT GROUP DETAILS USING PAPI"""
        user = kwargs.get('username')
        variables = tool_helper.load_unload('r')
        if variables.get(user + "_clientgrouplist"):
            if len(variables[user + "_clientgrouplist"]) > 0:
                i = variables[user + "_clientgrouplist"][randrange(len(variables[user + "_clientgrouplist"]))]
                response = taskset.client.get("/webconsole/api/v4/ServerGroup/{}".format(i),
                                              name="/v4/ServerGroup/{ID} C",
                                              headers=self.headers)
                tool_helper.api_response("GET SERVERGROUP DETAILS API RESPONSE", response)

    @setup_request
    def update_clientgroup(self, taskset, **kwargs):
        """Update the client group"""

        payload = {
            "clientGroupOperationType": 2,
            "clientGroupDetail": {
                "description": "client computer group description modified",
                "clientGroup": {
                    "clientGroupName": "{{clientGroupName}}"
                },
                "jobStartTime": 7200
            }
        }
        user = kwargs.get('username')
        variables = tool_helper.load_unload('r')
        if variables.get(user + "_clientgrouplist"):
            if len(variables[user + "_clientgrouplist"]) > 0:
                i = variables[user + "_clientgrouplist"][randrange(len(variables[user + "_clientgrouplist"]))]
                response = taskset.client.post("/webconsole/api/ClientGroup/{}".format(i),
                                               name="/ClientGroup/{ID} U",
                                               headers=self.headers, data=json.dumps(payload))
                tool_helper.api_response("Update client group response", response)
            else:
                print("No client group remains for the user")
        else:
            print("client groups does not exists")

    @setup_request
    def delete_servergroup_api(self, taskset, **kwargs):
        """DELETE SERVERGROUP API"""
        user = kwargs.get('username')
        variables = tool_helper.load_unload('r')
        if variables.get(user + "_clientgrouplist"):
            if len(variables[user + "_clientgrouplist"]) > 0:
                i = variables[user + "_clientgrouplist"].pop(randrange(len(variables[user + "_clientgrouplist"])))
                response = taskset.client.delete("/webconsole/api/v4/ServerGroup/{}".format(i),
                                                 name="v4/ServerGroup/{ID} DEL",
                                                 headers=self.headers)
                tool_helper.api_response("Delete server group api response", response)
                if response.status_code != 200:
                    variables[user + "_clientgrouplist"].append(i)
                tool_helper.load_unload('w', variables)
            else:
                print("No server group remains for this user")

    # WEBCONSOLE
    # TC 60846
    @setup_request
    def get_configured_repositories(self, taskset, **kwargs):
        """GET CONFIGURED REPOSITORIES"""
        response = taskset.client.get("/webconsole/api/GetConfiguredRepositories", headers=self.headers,
                                      name="/GetConfiguredRepositories")
        tool_helper.api_response("GET CONFIGURED REPOSITORIES API RESPONSE", response)

    @setup_request
    def listpackages(self, taskset, **kwargs):
        response = taskset.client.get("/webconsole/api/listPackages", headers=self.headers, name="/listPackages")
        tool_helper.api_response("GET LIST PACKAGES API RESPONSE", response)

    @setup_request
    def dcube_enginestats(self, taskset, **kwargs):
        # MONITORING PAGE API OF WEBCONSOLE
        response = taskset.client.get("/webconsole/api/dcube/enginestats", headers=self.headers,
                                      name="dcube engine stats")
        tool_helper.api_response("GET DCUBE ENGINE STATS RESPONSE", response)

    # Infrastructure Page APIs
    @setup_request
    def get_mediaagents_papi(self, taskset, **kwargs):
        variables = tool_helper.load_unload("r")
        if int(variables.get("version")) >= 25:
            response = taskset.client.get("/webconsole/api/v4/MediaAgent", headers=self.headers, name="/v4/MediaAgent")
            tool_helper.api_response("GET MEDIA AGENTS PAPI RESPONSE", response)
            data = response.json()
            if data.get('mediaAgents'):
                elem = randint(0, len(data['mediaAgents']) - 1)
                variables["mediaagent_id"] = data['mediaAgents'][elem].get("id")
                tool_helper.load_unload('w', variables)
        else:
            response = taskset.client.get("/webconsole/api/V2/MediaAgents?filterType=NONE", headers=self.headers,
                                          name="/v2/MediaAgent")
            tool_helper.api_response("GET MEDIA AGENTS API RESPONSE", response)
            data = response.json()
            if data.get('mediaAgentList'):
                elem = randint(0, len(data['mediaAgentList']) - 1)
                variables["mediaagent_id"] = data['mediaAgentList'][elem].get('mediaAgent').get("mediaAgentId")
                tool_helper.load_unload('w', variables)

    @setup_request
    def get_mediaagent_details(self, taskset, **kwargs):
        variables = tool_helper.load_unload("r")
        if variables.get("mediaagent_id"):
            response = taskset.client.get(f"/webconsole/api/v2/mediaagents/{variables['mediaagent_id']}",
                                          headers=self.headers,
                                          name="/v2/mediaagents/ID")
            tool_helper.api_response("GET MEDIA AGENT DETAILS API RESPONSE", response)
            response = taskset.client.get(f"/webconsole/api/Security/11/{variables['mediaagent_id']}",
                                          headers=self.headers,
                                          name="security/11/<MA_ID>")
            tool_helper.api_response("GET MEDIA SECURITY DETAILS API RESPONSE", response)
            response = taskset.client.get(
                f"/webconsole/api/NFSObjectStores/Cache?mediaagentId={variables['mediaagent_id']}",
                headers=self.headers,
                name="security/11/<MA_ID>")
            tool_helper.api_response("GET NFS OBJECTSTORE API RESPONSE", response)

        else:
            print("No media agent id saved")

    @setup_request
    def get_hybrid_filestore(self, taskset, **kwargs):
        variables = tool_helper.load_unload("r")
        if int(variables.get("version")) >= 25:
            response = taskset.client.get("/webconsole/api/V4/HybridFileStores", name="/v4/hybridfilestores",
                                          headers=self.headers)
            tool_helper.api_response("GET HYBRID FILE STORES LIST API RESPONSE", response)
        else:
            response = taskset.client.get("/webconsole/api/NFSObjectStores/Stores", name="/NFSObjectStores/Stores",
                                          headers=self.headers)
            tool_helper.api_response("GET HYBRID FILE STORES LIST API RESPONSE", response)

    @setup_request
    def get_storage_arrays(self, taskset, **kwargs):
        variables = tool_helper.load_unload("r")
        response = taskset.client.get("/webconsole/api/StorageArrays", headers=self.headers, name="/StorageArrays")
        tool_helper.api_response("GET STORAGE ARRAYS API RESPONSE", response)
        data = response.json()
        if data.get("arrayList"):
            elem = randint(0, len(data['arrayList']) - 1)
            variables["storageArrayID"] = data["arrayList"][elem]['arrayName']['id']
            tool_helper.load_unload("w", variables)

    @setup_request
    def get_storagearray_details(self, taskset, **kwargs):
        variables = tool_helper.load_unload("r")
        if variables.get("mediaagent_id"):
            response = taskset.client.get(f"/webconsole/api/StorageArrays/{variables['storageArrayID']}",
                                          headers=self.headers,
                                          name="/StorageArrays/{ID}")
            tool_helper.api_response("GET STORAGE ARRAY DETAILS API RESPONSE", response)
            response = taskset.client.get(f"/webconsole/api/Security/153/{variables['storageArrayID']}",
                                          headers=self.headers,
                                          name="security/153/<SA_ID>")
            tool_helper.api_response("GET STORAGE ARRAY SECURITY DETAILS API RESPONSE", response)

    @setup_request
    def get_resourcepool_papi(self, taskset, **kwargs):
        variables = tool_helper.load_unload("r")
        if int(variables.get("version")) >= 25:
            response = taskset.client.get("/webconsole/api/v4/ResourcePool", headers=self.headers,
                                          name="/v4/ResourcePool")
            tool_helper.api_response("GET RESOURCE POOL API RESPONSE", response)
            data = response.json()
            if data.get("resourcePools"):
                elem = randint(0, len(data['resourcePools']) - 1)
                variables["resourcePoolID"] = data["resourcePools"][elem]['id']
                tool_helper.load_unload('w', variables)
        else:
            response = taskset.client.get("/webconsole/api/ResourcePools", headers=self.headers,
                                          name="/ResourcePool")
            tool_helper.api_response("GET RESOURCE POOL API RESPONSE", response)
            data = response.json()
            if data.get("resourcePoolList"):
                elem = randint(0, len(data["resourcePoolList"]) - 1)
                variables["resourcePoolID"] = data["resourcePoolList"][elem].get("resourcePool").get("resourcePoolId")
                tool_helper.load_unload('w', variables)

    @setup_request
    def get_resourcepool_details(self, taskset, **kwargs):
        variables = tool_helper.load_unload("r")
        if variables.get("resourcePoolID"):
            response = taskset.client.get(f"/webconsole/api/ResourcePool/{variables['resourcePoolID']}",
                                          headers=self.headers,
                                          name="/ResourcePool/{ID}")
            tool_helper.api_response("GET RESOURCE POOL DETAILS API RESPONSE", response)

    @setup_request
    def get_indexserver_papi(self, taskset, **kwargs):
        variables = tool_helper.load_unload("r")
        if int(variables.get("version")) >= 26:
            response = taskset.client.get("/webconsole/api/v4/IndexServers", headers=self.headers,
                                          name="/v4/IndexServers")
            tool_helper.api_response("GET Index Servers API RESPONSE", response)
            data = response.json()
            if data.get("indexServers"):
                elem = randint(0, len(data['indexServers']) - 1)
                variables["serverID"] = data["indexServers"][elem]['id']
                tool_helper.load_unload('w', variables)
        else:
            response = taskset.client.get("/webconsole/api/IndexServers", headers=self.headers,
                                          name="/IndexServers")
            tool_helper.api_response("GET Index Servers API RESPONSE", response)
            data = response.json()
            if data.get("indexServers"):
                elem = randint(0, len(data['indexServers']) - 1)
                variables["serverID"] = data["indexServers"][elem]['clients']['clientId']
                tool_helper.load_unload('w', variables)

        tool_helper.api_response("GET Index Servers Cloud API RESPONSE", response)

    @setup_request
    def get_vm_groups(self, taskset, **kwargs):
        params = {
            "clientId": "0",
            "applicationId": "106",
            "PropertyLevel": "5",
            "includeVMPseudoSubclients": "false",
            "excludeVendorId": "20",
            "Fl": "overview,subClientProperties.subClientEntity,subClientProperties.status,"
                  "subClientProperties.planEntity,subClientProperties.vsaSubclientProp,"
                  "subClientProperties.commonProperties.isDefaultSubclient,"
                  "subClientProperties.commonProperties.lastBackupTime,"
                  "subClientProperties.commonProperties.lastBackupSize,"
                  "subClientProperties.fsSubClientProp.extendStoragePolicyRetention,"
                  "subClientProperties.indexingInfo.indexingStatus,"
                  "subClientProperties.commonProperties.lastBackupJobInfo,"
                  "subClientProperties.commonProperties.snapCopyInfo.isSnapBackupEnabled ",
            "Sort": "sc.subClientEntity.subclientName:1",
            "Limit": "20",
            "Start": "0"
        }
        response = taskset.client.get("/webconsole/api/Subclient", params=params, headers=self.headers,
                                      name="/Subclient 1")

        tool_helper.api_response("GET SUBCLIENT API:1 RESPONSE", response)
        data = response.json()
        params["Fl"] = "subClientProperties.subClientEntity.applicationId," \
                       "subClientProperties.vsaSubclientProp.vendorType," \
                       "subClientProperties.indexingInfo.indexingStatus "
        response = taskset.client.get("/webconsole/api/Subclient", params=params, headers=self.headers,
                                      name="/Subclient 2")
        tool_helper.api_response("GET SUBCLIENT API:2 RESPONSE", response)
        if data.get("subClientProperties"):
            elem = randint(0, len(data["subClientProperties"]) - 1)
            variables = tool_helper.load_unload("r")
            variables["hypervId"] = str(data["subClientProperties"][elem]["subClientEntity"]["clientId"])
            variables["subclientID"] = str(data["subClientProperties"][elem]["subClientEntity"]["subclientId"])
            variables["subclient_entity"] = 79
            variables["fileserverID"] = variables["hypervId"]
            tool_helper.load_unload('w', variables)
            payload = {
                "JobManager_JobListRequest": {
                    "pagingConfig": "",
                    "jobFilter": {
                        "client": str(data["subClientProperties"][elem]["subClientEntity"]["clientId"]),
                        "jobTypeList": [
                            "4",
                            "14"
                        ],
                        "entity": {"subclientId": variables["subclientID"], "applicationId": "106",
                                   "backupsetId": data["subClientProperties"][elem]["subClientEntity"]["backupsetId"]}
                    }
                }
            }
            response = taskset.client.post("/webconsole/api/Jobs",
                                           name="/Jobs", data=json.dumps(payload), headers=self.headers)
            tool_helper.api_response("GET Jobs API RESPONSE", response)
        params = {
            "permissionId": 2
        }
        response = taskset.client.get("/webconsole/api/VSPseudoClientsForPermission",
                                      name="/VSPseudoClientsForPermission", params=params, headers=self.headers)
        tool_helper.api_response("GET VSPseudoClientsFor Permission API RESPONSE", response)

    @setup_request
    def create_alert(self, taskset, **kwargs):
        payload = {
            "alertDetail": {
                "alertType": 3,
                "notifTypeListOperationType": 0,
                "alertSeverity": 0,
                "notifType": [
                    1,
                    8192
                ],
                "criteria": {
                    "criteria": 1
                },
                "EntityList": {
                    "associationsOperationType": 0,
                    "associations": [
                        {
                            "clientId": 2,
                            "_type_": 3
                        }
                    ]
                },
                "userList": {
                    "userListOperationType": 0,
                    "userList": [
                        {
                            "_type_": 13,
                            "userId": 1
                        }
                    ]
                },
                "alertrule": {
                    "alertName": "locust_alert_" + str(datetime.now()) + str(randint(0, 1000))
                }
            }
        }
        response = taskset.client.post("/webconsole/api/AlertRule",
                                       name="/AlertRule", data=json.dumps(payload), headers=self.headers)
        tool_helper.api_response("Create Alert API RESPONSE", response)
        if response.status_code == 200:
            variables = tool_helper.load_unload('r')
            output = response.json()
            variables["flag"] = 1
            id = str(output.get("alertEntity").get("alertId"))
            tool_helper.check_key(variables, kwargs.get('username') + "_alertlist", "alert_list", id)

    @setup_request
    def create_schedule_policy(self, taskset, **kwargs):
        payload = {
            "taskInfo": {
                "associations": [
                    {
                        "clientId": 2
                    }
                ],
                "task": {
                    "description": "locust-scale schedule policy",
                    "taskType": 4,
                    "policyType": 0,
                    "taskName": "locust_schedule_policy_" + str(datetime.now()) + str(randint(0, 1000))
                },
                "appGroup": {
                    "appGroups": [
                        {
                            "_type_": 78,
                            "appGroupId": 1
                        },
                        {
                            "_type_": 78,
                            "appGroupId": 5
                        }
                    ]
                },
                "subTasks": [
                    {
                        "subTask": {
                            "subTaskName": "Sunday afternoons",
                            "subTaskType": 2,
                            "operationType": 2
                        },
                        "pattern": {
                            "freq_type": 8,
                            "active_end_time": 0,
                            "active_start_time": 50400,
                            "active_start_date": int(time.time()),
                            "freq_interval": 1,
                            "freq_recurrence_factor": 1,
                            "daysToRun": {
                                "Sunday": True
                            },
                            "calendar": {
                                "calendarName": "Standard"
                            },
                            "timeZone": {
                                "TimeZoneName": "(UTC-05:00) Eastern Time (US & Canada)"
                            }
                        },
                        "options": {
                            "backupOpts": {
                                "backupLevel": 2
                            }
                        }
                    }
                ]
            }
        }
        response = taskset.client.post("/webconsole/api/Task",
                                       name="/Task", data=json.dumps(payload), headers=self.headers)
        tool_helper.api_response("CREATE SCHEDULE POLICY API RESPONSE", response)
        variables = tool_helper.load_unload('r')
        if "tasks" not in variables:
            variables["tasks"] = []
        if response.status_code == 200:
            data = response.json()
            task_name = payload["taskInfo"]["task"]["taskName"]
            variables["tasks"].append({str(data.get('taskId')): str(task_name)})
            tool_helper.load_unload('w', variables)

    @setup_request
    def create_pseudo_client(self, taskset, **kwargs):
        payload = {
            "registerClient": False,
            "clientInfo": {
                "clientType": randint(0, 38),
                "openVMSProperties": {
                    "cvdPort": 0
                },
                "ibmiInstallOptions": {}
            },
            "entity": {
                "hostName": "locust_client_hostname_" + str(datetime.now()) + str(randint(0, 1000)),
                "clientName": "locust_client_" + str(datetime.now()) + str(randint(0, 1000))
            }
        }
        response = taskset.client.post("/webconsole/api/pseudoClient",
                                       name="/pseudoClient", data=json.dumps(payload), headers=self.headers)
        tool_helper.api_response("GET PseudoClient API RESPONSE", response)


    # Testcase 62428
    @setup_request
    def create_subclients(self, taskset, **kwargs):
        variables = tool_helper.load_unload('r')
        user = choice(variables["locust_user_list"])
        if user in variables:
            headers = tool_helper.headers({'Authtoken': variables[user]})
            response = taskset.client.post("/webconsole/api/Subclient", data=json.dumps(
                {
                    "subClientProperties":{
                        "contentOperationType":"ADD",
                        "subClientEntity":{
                            "clientName": sample(kwargs.get("param")['clients'].split(','), 1)[0],
                            "appName":"File System",
                            "backupsetName": "DefaultBackupset",
                            "subclientName":"subclient" + str(datetime.now()) + str(randint(0, 1000))
                        },
                        "commonProperties":{
                            "enableBackup":True,
                            "prepostProcess":{
                                "runAs":"USE_LOCAL_SYS_ADMIN",
                                "runPostBackup":"NO"
                            }
                        },
                        "planEntity":{
                            "planId": int(sample(kwargs.get("param")['plan_ids'].split(','), 1)[0])
                        }
                    }
                }
            ),
                headers=headers,
                name="Create Subclients")

            tool_helper.api_response("CREATE SUBCLIENT RESPONSE", response)

        else:
            print("Locust user is not logged in")

    @setup_request
    def get_schedule_policy_details(self, taskset, **kwargs):
        variables = tool_helper.load_unload('r')
        if "tasks" in variables:
            random_task = choice(variables["tasks"])
            random_taskid = list(random_task.keys())[0]
            response = taskset.client.get(f"""/webconsole/api/SchedulePolicy/{random_taskid}""",
                                          headers=self.headers,
                                          name="/SchedulePolicy/{taskId}")
            tool_helper.api_response("GET SCHEDULE POLICY RESPONSE", response)

    @setup_request
    def update_schedule_policy(self, taskset, **kwargs):
        variables = tool_helper.load_unload('r')
        if "tasks" in variables:
            random_task = choice(variables["tasks"])
            random_taskid = list(random_task.keys())[0]
            random_taskname = list(random_task.values())[0]
            payload = {
                "taskInfo": {
                    "taskOperation": 6,
                    "associations": [
                        {
                            "clientGroupId": 2,
                            "_type_": 28
                        }
                    ],
                    "task": {
                        "description": "Schedule policy for locust testcase modified random number:" + str(randint(0, 1000)),
                        "taskName": str(random_taskname),
                        "taskId": int(random_taskid)
                        }
                }
            }
            response = taskset.client.put(f"""/webconsole/api/Task""",
                                          headers=self.headers,
                                          name="/Task",
                                          data=json.dumps(payload))
            #print(payload)
            tool_helper.api_response("UPDATE SCHEDULE POLICY RESPONSE", response)

locust_instance = API()
