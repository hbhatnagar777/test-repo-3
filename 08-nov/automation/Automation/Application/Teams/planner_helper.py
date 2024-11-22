# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Main file for performing Planner operations to a Team.

Planner is the only class defined in this file.

Planner: Class for representing a planner of a Team.

Planner:
========
    _init_()                                 --  Initialize object of Planner.
    retry()                                  -- Retry a method for required times.
    create_plan()                            -- Create a plan.
    create_bucket()                          -- Create a bucket in a plan.
    create_task()                            -- Create a task in a plan.
    get_plans_in_the_group()                 -- Get plans in a group or team.
    get_buckets_in_plan()                    -- Get buckets in a plan.
    get_tasks_in_bucket()                    -- Get tasks in a bucket.
    delete_planner_item()                    -- Delete Planner item.
    rename_planner_item()                    -- Rename planner item.
    create_planner_tab_with_plan()           -- Create tab with given plan.
    post_comment_to_task()                   -- Post comment to the task.
    get_planner_item_details()               -- Get a plan or bucket or task details.
"""

import json
import time

from functools import partial
from Application.Teams import request_response as rr
from Application.Teams.teams_constants import MS_GRAPH_APIS as apis
from Application.Teams import teams_constants

const = teams_constants.TeamsConstants()
planner_item_type = const.PlannerItemType


class Planner:

    def __init__(self, team_id):
        self._default_plan = None
        self._default_bucket = None
        self._team_id = team_id

    @property
    def plan(self):
        if self._default_plan is None:
            flag, resp = self.create_plan()
            resp = json.loads(resp.content)
            self._default_plan = resp['id']

        return self._default_plan

    @property
    def bucket(self):
        if self._default_bucket is None:
            flag, resp = self.create_bucket()
            resp = json.loads(resp.content)
            self._default_bucket = resp['id']

        return self._default_bucket

    @staticmethod
    def convert_list_to_dict(resp, buckets=False):
        items = {}
        key = 'name' if buckets else 'title'
        if 'value' in resp and resp['value'] != []:
            for item in resp['value']:
                items[item[key]] = item
        return items

    @staticmethod
    def retry(func, retries):
        """Retries func 'retries' number of times or until desired status code is returned.
            Args:
               func                 --  Function to retry.
               retries      (int)   --  Number of retries.

            Returns:
                resp    --  Returns object of Response.

        """

        for i in range(retries):
            flag, resp = func()
            if flag:
                break
            time.sleep(30)
        return flag, resp

    def create_plan(self, name=const.PLAN_NAME):
        data = {
            "title": name,
            "owner": self._team_id
        }
        retry = partial(rr.post_request, url=apis['CREATE_PLAN']['url'], status_code=201, data=data, delegated=True)
        return self.retry(retry, retries=3)

    def create_bucket(self, plan_id=None, name=const.BUCKET_NAME):

        plan_id = plan_id if plan_id else self.plan
        data = {
            "name": name,
            "planId": plan_id
        }
        retry = partial(rr.post_request, url=apis['CREATE_BUCKET']['url'], status_code=201, data=data, delegated=True)
        return retry(retry, retries=3)

    def create_task(self, plan_id=None, bucket_id=None, task_name=const.TASK_NAME):
        plan_id = plan_id if plan_id else self.plan
        bucket_id = bucket_id if bucket_id else self.bucket
        data = {
            "@odata.etag": "W/\"JzEtVGFzayAgQEBAQEBAQEBAQEBAQEBBTCc=\"",
            "planId": "zGPrjsv1Kk6XsUNdhw1eDMkAC8nW",
            "bucketId": "C2KWmQceeEG2jtEFMURsWskAJjOY",
            "title": "ww",
            "percentComplete": 50,
            "specifiedCompletionRequirements": "none",
            "previewType": "checklist",
            "completedDateTime": None,
            "completedBy": None,
            "priority": 1,
            "recurrence": {
                "seriesId": "ZMDAifnr_UaJxXz6XXUlFw",
                "occurrenceId": 1,
                "previousInSeriesTaskId": None,
                "nextInSeriesTaskId": None,
                "recurrenceStartDateTime": "2023-08-11T10:00:00Z",
                "schedule": {
                    "patternStartDateTime": "2023-08-11T10:00:00Z",
                    "nextOccurrenceDateTime": "2023-09-11T10:00:00Z",
                    "pattern": {
                        "type": "absoluteMonthly",
                        "interval": 1,
                        "firstDayOfWeek": "sunday",
                        "dayOfMonth": 11,
                        "daysOfWeek": [],
                        "index": "first",
                        "month": 0
                    }
                }
            },
            "appliedCategories": {
                "category2": True
            },
            "assignments": {
                "d435aa41-ef5e-4d57-80f4-eea4eb377398": {
                    "@odata.type": "#microsoft.graph.plannerAssignment",
                    "assignedDateTime": "2023-08-10T18:55:32.6785363Z",
                },
                "04901919-97cb-405a-bd53-7f43a2c17b12": {
                    "@odata.type": "#microsoft.graph.plannerAssignment",
                    "assignedDateTime": "2023-08-10T18:55:31.8583978Z",
                },
                "ebc502b7-10e8-4ef6-989d-4567b25a3a9d": {
                    "@odata.type": "#microsoft.graph.plannerAssignment",
                    "assignedDateTime": "2023-08-10T18:55:30.6239709Z",
                }
            }
        }
        retry = partial(rr.post_request, url=apis['CREATE_TASK']['url'], status_code=201, data=data)
        return self.retry(retry, retries=3)

    def get_plans_in_the_group(self):
        retry = partial(rr.get_request,
                        url=apis['GET_PLANS_IN_TEAM']['url'].format(group_id=self._team_id), status_code=200)
        flag, resp = retry(retry, retries=3)

        if flag:
            return Planner.convert_list_to_dict(json.loads(resp.content))
        raise Exception(f"Failed to get list of plans in a group id {self._team_id}")

    @staticmethod
    def get_buckets_in_plan(plan_id):
        retry = partial(rr.get_request,
                        url=apis['GET_BUCKETS_IN_PLAN']['url'].format(plan_id=plan_id), status_code=200)
        flag, resp = retry(retry, retries=3)
        if flag:
            return Planner.convert_list_to_dict(json.loads(resp.content), buckets=True)
        raise Exception(f"Failed to get list of buckets in a plan id {plan_id}")

    @staticmethod
    def get_tasks_in_bucket(bucket_id):
        retry = partial(rr.get_request,
                        url=apis['GET_TASKS_IN_BUCKET']['url'].format(bucket_id=bucket_id), status_code=200)
        flag, resp = retry(retry, retries=3)
        if flag:
            return Planner.convert_list_to_dict(json.loads(resp.content))
        raise Exception(f"Failed to get list of tasks in a bucket id {bucket_id}")

    @staticmethod
    def delete_planner_item(item_type, item_id):
        path_variable = "tasks"
        if item_type == planner_item_type.PLAN:
            path_variable = "plans"
        elif item_type == planner_item_type.BUCKET:
            path_variable = "buckets"

        retry = partial(rr.delete_request,
                        url=apis['DELETE_PLANNER_ITEMS']['url'].format(item_type=path_variable, id=item_id),
                        status_code=204)
        flag, resp = retry(retry, retries=3)

        if flag:
            return True
        raise Exception(f"Failed to delete a {path_variable[:-1]} with id {item_id}")

    @staticmethod
    def rename_planner_item(item_type, item_id, new_name):
        data = ""
        path_variable = ""
        if item_type == planner_item_type.PLAN:
            path_variable = "plans"
            new_name = new_name if new_name else const.PLAN_NAME
            data = {
                "title": new_name
            }
        elif item_type == planner_item_type.BUCKET:
            path_variable = "buckets"
            new_name = new_name if new_name else const.BUCKET_NAME
            data = {
                "name": new_name
            }
        else:
            raise Exception("rename not implemented for given planner item.")
        retry = partial(rr.patch_request,
                        url=apis['DELETE_PLANNER_ITEMS']['url'].format(item_type=path_variable, id=item_id),
                        status_code=200, data=data)
        flag, resp = retry(retry, retries=3)
        if flag:
            return True
        raise Exception(f"Failed to update a {path_variable[:-1]} with id {item_id} with name {new_name}")

    def create_planner_tab_with_plan(self, channel_id, plan_id, planner_tab_name=const.PLANNER_TAB_NAME):

        tab_data = {
  "displayName": planner_tab_name,
  "teamsApp@odata.bind" :  "https://graph.microsoft.com/v1.0/appCatalogs/teamsApps/com.microsoft.teamspace.tab.planner",
  "configuration":{
      "entityId": "tt.c_"+channel_id+"_p_"+plan_id,
      "contentUrl": "https://tasks.teams.microsoft.com/teamsui/{{tid}}/Home/PlannerFrame?page=7&auth_pvr=OrgId&auth_upn={{userPrincipalName}}&groupId={{groupId}}&planId={id}&channelId={{channelId}}&entityId={{entityId}}&tid={{tid}}&userObjectId={{userObjectId}}&subEntityId={{subEntityId}}&sessionId={{sessionId}}&theme={{theme}}&mkt={{locale}}&ringId={{ringId}}&PlannerRouteHint={{tid}}&tabVersion=20200228.1_s".format(id=plan_id),
      "removeUrl": "https://tasks.teams.microsoft.com/teamsui/{{tid}}/Home/PlannerFrame?page=13&auth_pvr=OrgId&auth_upn={{userPrincipalName}}&groupId={{groupId}}&planId={id}&channelId={{channelId}}&entityId={{entityId}}&tid={{tid}}&userObjectId={{userObjectId}}&subEntityId={{subEntityId}}&sessionId={{sessionId}}&theme={{theme}}&mkt={{locale}}&ringId={{ringId}}&PlannerRouteHint={{tid}}&tabVersion=20200228.1_s".format(id=plan_id),
      "websiteUrl": "https://tasks.office.com/d3ee719b-9e5c-478b-87c9-c4ffbfd27c96/Home/PlanViews/{id}?Type=PlanLink&Channel=TeamsTab".format(id=plan_id)
  }
}

        retry = partial(rr.post_request,
                        url=apis['GET_TABS']['url'].format(team_id=self._team_id, channel_id=channel_id),
                        status_code=201, data=tab_data)
        flag, resp = retry(retry, retries=3)

        if flag:
            return True
        raise Exception(f"Failed to create a tab with plan id {plan_id}")

    def post_comment_to_task(self, task_id, comment="automated_comment"+str(const.cnt)):

        data = {
            "post": {
                "body": {
                    "contentType": "1",
                    "content": comment
                }
            }
        }
        resp = Planner.get_planner_item_details(task_id, planner_item_type.TASK)
        covr_thread_id = resp["conversationThreadId"]
        retry = partial(rr.post_request,
                        url=apis['ADD_COMMENT_TO_TASK']['url'].format(self._team.id, covr_thread_id),
                        status_code=202, data=data)
        flag, resp = retry(retry, retries=3)

        if flag:
            return True
        raise Exception(f"Failed to post a comment to task with id {task_id}")

    @staticmethod
    def get_planner_item_details(item_id, item_type):
        path_variable = "tasks"
        if item_type == planner_item_type.PLAN:
            path_variable = "plans"
        elif item_type == planner_item_type.BUCKET:
            path_variable = "buckets"

        retry = partial(rr.get_request,
                        url=apis['DELETE_PLANNER_ITEMS']['url'].format(item_type=path_variable, id=item_id),
                        status_code=200)
        flag, resp = retry(retry, retries=3)

        if flag:
            return json.loads(resp.content)
        raise Exception(f"Failed to get {path_variable[:-1]} with id {id} details")



