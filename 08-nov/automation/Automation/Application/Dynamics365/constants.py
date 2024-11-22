# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
    Constants file for Dynamics 365 Automation (Web and SDK)
"""
from enum import Enum

CLIENT_NAME = "Dynamics365Client_%s"
"""Default name for Dynamics 365 Client"""

QUERY_TABLE_FILTERS = "IsIntersect eq false &$count=true"
"""Filter that we use to query the tables from Dynamics 365 CRM"""

TABLES_NOT_PROCESSED = ['TeamMobileOfflineProfileMembership', 'UserMobileOfflineProfileMembership', 'Attachment',
                        'App Action', 'App Action Migration', 'App Action Rule', 'Image Attribute Configuration',
                        'Data Lake Folder', 'Data Lake Folder Permission', 'Data Processing configuration',
                        'Entity Image Configuration', 'FeatureControlSetting', 'Flow Machine Image',
                        'Flow Machine Image Version', 'Goal Metric', 'PM Template', 'Record Filter',
                        'Service Plan Mapping']
"""Tables that we do not backup/ are not supported for Dynamics 365 CRM client"""

DISCOVER_PROCESS_NAME = 'CVOffice365Discover'
"""Name of discovery process for Dynamics 365"""


class D365JobPhases(Enum):
    BACKUP = 4
    ARCHIVE_INDEX = 6
    FINALIZE = 7


ENTITIES_INCLUDED = ["account", "appointment", "kbarticle", "kbarticletemplate", "activitymimeattachment",
                     "bookableresource", "bookableresourcebookingheader", "bookableresourcecategory",
                     "bookableresourcecategoryassn", "bookableresourcecharacteristic", "bookableresourcegroup",
                     "bookingstatus", "businessunit", "campaign", "campaignactivity", "campaignresponse", "incident",
                     "incidentresolution", "category", "channelproperty", "channelpropertygroup", "characteristic",
                     "competitor", "connection", "contact", "contract", "contractdetail", "contracttemplate",
                     "transactioncurrency", "discount", "discounttype", "Sharepointdocumentlocation", "email",
                     "emailserverprofile", "emailsignature", "template", "entitlement", "entitlementtemplate",
                     "expiredprocess", "fax", "feedback", "postfollow", "goal", "metric", "invoice", "invoicedetail",
                     "knowledgearticle", "knowledgearticleincident", "knowledgearticleviews", "lead",
                     "leadtoopportunitysalesprocess", "letter", "mailbox", "mailmergetemplate",
                     "list", "newprocess", "annotation", "opportunity", "opportunityclose", "opportunityproduct",
                     "customeropportunityrole", "opportunitysalesprocess", "salesorder", "orderclose",
                     "salesorderdetail",
                     "organization", "phonecall", "phonetocaseprocess", "position", "post", "pricelevel",
                     "productpricelevel",
                     "product", "productassociation", "productsubstitute", "publisher", "queue", "queueitem", "quote",
                     "quoteclose", "quotedetail", "ratingmodel", "ratingvalue", "goalrollupquery",
                     "salesliteratureitem",
                     "salesliterature", "service", "serviceappointment", "sharepointsite", "site", "subject", "task",
                     "teamtemplate", "territory", "theme", "uom", "uomschedule", "systemuser", "convertrule",
                     "bulkoperation"]
