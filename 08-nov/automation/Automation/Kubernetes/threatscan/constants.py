# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" It contains constants for threat scan cluster on kubernetes"""
# helm related
CV_REPO_PATH = 'https://commvault.github.io/helm-charts'
CV_REPO_NAME = 'commvault'
ACCESS_NODE_REPO_CHART_NAME = 'commvault/accessnode'
ACCESS_NODE_CHART_NAME = 'accessnode'
CE_CHART_NAME = 'contentextractor'
INDEX_SERVER_CHART_NAME = 'indexserver'
LABEL_IMAGE_PULL_SECRET = 'image.pullSecret='
LABEL_IMAGE_LOC = 'image.location='
LABEL_CLIENT_NAME = 'clientName='
LABEL_DEPLOYMENT = 'deployment'

# kubectl related
DEPLOYMENT_NAME_LABEL = 'app.kubernetes.io/name='
DEPLOYMENT_APP_LABEL = 'app='
IS_APP_NAME = 'datacube'
