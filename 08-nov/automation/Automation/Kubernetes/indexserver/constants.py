# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" It contains constants for index server cluster on kubernetes"""

# controller fields
FIELD_TOTAL_DOCS = 'Total Docs'
FIELD_TOTAL_PVC = 'Total PVC'
FIELD_TOTAL_PVC_CAPACITY = 'Total PVC Capacity'
FIELD_TOTAL_PVC_USED = 'Total PVC Used'
FIELD_TOTAL_CORES_IN_PVC = 'Total Cores in Pvc'
FIELD_PVC_STATS = 'Pvc Stats'
FIELD_PVC_CAPACITY = 'capacity'
FIELD_PVC_USED = 'used'
FIELD_PVC_NAME = 'pvcName'
FIELD_INGRESS_SERVER_ID = 'ingressServerId'
FIELD_SERVER_ID = 'serverId'
FIELD_ALL_CORE_SERVER_ID = 'ServerIds'
FIELD_COLLECTION_NAME = 'collectionName'
FIELD_CV_COLLECTION = 'cvCollection'
FIELD_CORES = 'cores'
FIELD_CORE_SIZE = 'size'
FIELD_CORE_DOCS = 'numDocs'
FIELD_TOTAL_CORES = 'Totalcores'
FIELD_TOTAL_CORE_SIZE = 'Totalsize'
FIELD_TOTAL_CORE_SIZE_STR = 'Totalsizestr'
FIELD_TOTAL_CORE_DOCS = 'TotalnumDocs'
FIELD_TOTAL_CORE_DOCS_STR = 'TotalnumDocsstr'
FIELD_NUMFOUND = 'numFound'
FIELD_RESPONSE = 'response'
FIELD_RESPONSE_HEADER = 'responseHeader'
FIELD_STATUS = 'status'
FIELD_NAME = 'name'
FIELD_USAGES = 'usages'
FIELD_JVM_PERCENT = 'jvmMemoryUsagePercent'
FIELD_RESOURCE_REQ = 'resourceReqs'

# Cluster resources
RESOURCE_DEPLOYMENT = 'deployment'

# Kubernetes Index Server constants
DB_FIELD_COMMVAULT = r'\COMMVAULT'
DB_FIELD_COMMSERV = 'commserv'
DEFAULT_IS_RESOURCE_GROUP = "DIAutomationIndexServerGroup"
DEFAULT_IS_CLUSTER_NAME = "DIIndexServerCluster"
DEFAULT_IS_AZURE_LOCATION = "eastus2"
DEFAULT_TRAEFIK_YAML_FILE = "traefik.yaml"
DEFAULT_TRAEFIK_YAML = """apiVersion: traefik.io/v1alpha1
kind: Middleware
metadata:
  name: ipauth
  namespace: datacube
spec:
  ipWhiteList:
    sourceRange:
      - 0.0.0.0/0
      - ::/0
---
apiVersion: traefik.io/v1alpha1
kind: IngressRoute
metadata:
  labels:
    app: datacube-controller
  name: ping-controller
  namespace: datacube
spec:
  routes:
  - kind: Rule
    match: PathRegexp(`/solr/.*/admin/ping`)
    services:
    - name: datacube-controller
      port: 20000
"""
IS_ACR_NAME = 'cvanalyticscontainerregistry'
IS_HELM_APP_NAME = 'traefik'
TRAEFIK_URL = 'https://traefik.github.io/charts'
IS_NAME_SPACE = 'datacube'
IS_CONTROLLER_DEPLOYMENT = 'datacube-controller'
TRAEFIK_VALUES_YAML = [
    'ingressRoute.dashboard.enabled=true']
TRAEFIK_SERVICE_NAME = 'traefik'
IS_COMMSERV_CLIENT_PROP = 'K8sSolrSvcUrl'
DATA_TYPE_FILE = 'File'
NODE_VM_SIZE = 'Standard_d16ads_v5'
CTRLR_NODE_VM_SIZE = 'Standard_B4ms'
CTRLR_NODE_POOL_NAME = 'ctrnodepool'
APP_NODE_POOL_NAME = 'appnodepool'
APP_NODE_POOL_LABEL = 'app=datacube'
CTRLR_NODE_POOL_LABEL = 'app=dkubectrlr'
MAX_NUM_CORES_PER_POD = 10
CORE_STATUS_SYNC_IN_MINS = 5
IDEL_CORE_TIMEOUT_IN_SECS = "180"
SERVER_PICK_CRITERIA_MAX_CORES_AND_UNLOAD_CORES = {
    "ctrlrConfig": {
        "coreStatusSyncMins": CORE_STATUS_SYNC_IN_MINS,
        "dcubeConfig": {
            "analyticsProperties": {
                "props": {
                    "idleCoreTimeoutSecs": IDEL_CORE_TIMEOUT_IN_SECS,
                }
            }
        },
        "srvrPickCriteria": {
            "maxNumCores": MAX_NUM_CORES_PER_POD}}}
