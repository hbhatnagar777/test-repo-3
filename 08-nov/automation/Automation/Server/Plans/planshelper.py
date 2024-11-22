# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for REST API based Plans

PlansHelper is the only class defined in this file

PlansHelper
===========

    __init__()                --  initializes planshelper object

    get_storage_pool()        --  Returns any random online storage pool

    create_base_plan()        --  Creates and returns a Plan

    validate_plan_props()     --  Validates the creation of a plan from SDK

    delete_plan()             --  Deletes the passed plan

    inherit_plan()            --  Creates and returns a derived Plan

    plan_to_company()         --  Associates plan to company

    modify_inheritance()      --  Modify override restrictions of a base plan

    cleanup_plans()           --  Delete plans that were marked for deletion
                                  during previous runs

    validate_overriding()     --  Validates override restrictions of base plans

    validate_inheritance()    --  Validates whether inheritance is
                                  appropriately followed on derivation

    validate_tenant_roles()   --  Validates whether a user required roles on
                                  a company

    company_default_plan()    --  Sets or unsets the default plan of a company

    validate_default_plan()   --  Validates the default company of a plan

    validate_schedules()      --  Validates the schedules created by a plan

    modify_rpo()              --  Modifies the RPO/SLA of the plan

    validate_rpo()            --  Validates the RPO of a plan

    disable_schedule()        --  Disables the incremental or full schedule

    rename_plan()             --  Renames the plan

    validate_entity_names()   --  Validates the policy names

    add_copy()                --  Adds a new storage copy to the plan

    delete_copy()             --  Deletes a copy from the plan

    validate_copies()         --  Validates the backup copy of the plan

    entity_to_plan()          --  Associates a backup entity to a plan

    validate_subclient_association() -- Validates subclient association

    validate_backupset_association() -- Validates backupet association

    dissociate_entity()       --  Dissociates entities from plan

    validate_dissociation()   --  Validates dissociation of entity

    policy_to_subclient()     --  Associates a plans storage policy to
                                  a subclient
                                  
    associate_user_to_plan()  -- associate the user to given plan name

    _get_plan_status()        -- fetches plan status from DB

    validate_plans_cache_data()     --  validates the data returned from Mongo cache for plans collection

    validate_sort_on_cached_data()  --  validates sort parameter on entity cache API call

    validate_limit_on_cache()       --  validates limit parameter on entity cache API call

    validate_search_on_cache()      --  validates search parameter on entity cache API call

    validate_filters_on_cache()     --  validates fq param on entity cache API call

"""
import random
import inspect
import datetime
import time
import locale

from AutomationUtils import logger
from AutomationUtils.database_helper import CommServDatabase
from cvpysdk.commcell import Commcell

class PlansHelper(object):
    """Helper class to perform Plans REST API operations"""

    def __init__(self, commserve='', username='', password='', commcell_obj=None):
        """Initializes plans object and gets the commserv database object if
            not specified

            Args:
                commserve       (str)   --  hostname of the commcell

                username        (str)   --  username of the user to perform
                                            operations

                password        (str)   --  password of the user

                commcell_obj    (str)   --  commcell object for creating
                                            PlansHelper
        """
        self.log = logger.get_log()
        self.commcell_obj = commcell_obj or Commcell(commserve, username, password)
        self.csdb = CommServDatabase(self.commcell_obj)
        self.plans_obj = self.commcell_obj.plans
        self.base_plan = None
        self.derived_plans = []
        self.storage_pool = None

    def dedupe_check(self, pool_name):
        """filter function to check if a storage pool is dedupe"""
        return (
            'dedupDBDetailsList'
            in self.commcell_obj.storage_pools.get(
                pool_name
            )._storage_pool_properties['storagePoolDetails']
        )

    def get_storage_pool(self, dedupe: bool = None) -> str:
        """Returns a random online storage pool.

        Args:
            dedupe (bool): Set to True/False if a dedupe/nondedupe pool is to be retrieved.

        Returns:
            str: Storage pool name.
        """
        storage_pools = self.commcell_obj.storage_pools.all_storage_pools.keys()

        if isinstance(dedupe, bool):
            dedupe_filter = self.dedupe_check if dedupe else lambda s: not self.dedupe_check(s)
            filtered_pools = list(filter(dedupe_filter, storage_pools))
        else:
            filtered_pools = list(storage_pools)

        if not filtered_pools:
            raise ValueError("No suitable storage pool found.")

        storage_pool = random.choice(filtered_pools)

        # To get case-sensitive storage pool name
        query = f"SELECT NAME FROM ARCHGROUP WITH(NOLOCK) WHERE NAME = '{storage_pool}'"
        self.csdb.execute(query)
        return self.csdb.fetch_all_rows()[0][0]

    def create_base_plan(self, plan_name, subtype, storage_pool, sla_in_minutes=1440, override_entities=None):
        """ Create a plan on commcell

            Args:
                plan_name        (str)    : Plan name to create

                subtype          (str)   --  Type of plan to add

                                                "Server"    -   Server Plans

                                                "FSServer"  -   File System Plans

                                                "Laptop"    -   Laptop Plans

                storage_pool_name (str)   : Storage pool to associate to the plan

                sla_in_minutes    (str)   : SLA in minutes

                override_entities   (dict)  --  Specify the entities with respective overriding.

            Returns:
                plan_object     (obj)   --  object of new plan
        """
        try:
            args = [plan_name, subtype, storage_pool, sla_in_minutes, override_entities]
            if self.plans_obj.has_plan(plan_name):
                self.log.info("Plan [{0}] already exists on commcell".format(plan_name))
                self.base_plan = self.plans_obj.get(plan_name)
            else:
                self.log.info(
                    "Creating plan [{0}], subtype [{1}], storage_pool [{2}]".format(plan_name, subtype, storage_pool)
                )
                self.base_plan = self.plans_obj.add(*args)

            return self.base_plan

        except Exception as excp:
            self.log.error("{0} plan creation failed - {0}".format(plan_name))
            raise Exception("\n[{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def validate_plan_props(self, plan_obj):
        """Validates the creation of a plan from SDK
        Args:
            plan_obj        (obj)   -- object of plan to be validated

        """
        if plan_obj.plan_name.lower() not in self.plans_obj.all_plans:
            self.log.error("Plan has not been successfully created in SDK")
            raise Exception("Plan creation failure")

        if not self.commcell_obj.storage_policies.has_policy(
                plan_obj.storage_policy.name):
            self.log.error("Storage policy not successfully created")
            raise Exception("Plan storage validation failure")

        if not self.commcell_obj.schedule_policies.has_policy(
                plan_obj.schedule_policies['data'].schedule_policy_name):
            self.log.error("Data schedule policy not successfully created")
            raise Exception("Plan schedule validation failure")

        if plan_obj.subtype == 33554437:
            if not self.commcell_obj.schedule_policies.has_policy(
                    plan_obj.schedule_policies['log'].schedule_policy_name):
                self.log.error("Log schedule policy not successfully created")
                raise Exception("Plan schedule validation failure")

            if len(plan_obj.subclient_policy) != 3:
                self.log.error("Three subclient policie snot created for the plan")
                raise Exception("Plan content creation failure")

        if plan_obj.subtype == 33554439:
            if not self.commcell_obj.client_groups.has_clientgroup(
                    plan_obj._client_group.clientgroup_name):
                self.log.error("Client group was not successfully created")
                raise Exception("Plan clientgroup validation failure")

            if not self.commcell_obj.user_groups.has_user_group(
                    plan_obj._user_group):
                self.log.error("User group was not successfully created")
                raise Exception("Plan usergroup validation failure")

    def delete_plan(self, plan_name):
        """Deletes the passed plan
        Args:
            plan_name        (str)   -- object of plan to be validated

        Returns:
            bool                     -- plan validation confirmation
        """
        try:
            self.plans_obj.delete(plan_name)
            self.log.info("Delete plan {0}".format(plan_name))
            self.plans_obj.refresh()
            return True
        except Exception as exp:
            self.log.error('Plan deletion failed due to {0}'.format(str(exp)))
            return False

    def inherit_plan(self,
                     base_plan_name,
                     derived_plan_name,
                     storage_pool=None,
                     sla_in_minutes=None,
                     override_entities=None):
        """Creates and returns a derived Plan
        Args:
            base_plan_name        (str)   -- name of plan to be inherited

            derived_plan_name     (str)   -- name of the derived plan to be
                                             created

            storage_pool          (str)   -- storage pool name to be used

            sla_in_minutes        (int)   -- SLA/RPO in minutes

            override_entities     (int)   -- override restrictions for the plan

        Returns:
            obj                           -- object of the derived plan
        """
        self.plans_obj.refresh()
        try:
            if self.plans_obj.has_plan(base_plan_name):

                plan_obj = self.plans_obj.get(base_plan_name)
                derived_plan = plan_obj.derive_and_add(
                    derived_plan_name,
                    storage_pool,
                    sla_in_minutes,
                    override_entities
                )
                self.derived_plans.append(derived_plan)
                return derived_plan
            else:
                self.log.error("Passed plan object does not exist")
                raise Exception("Base plan does not exist")
        except Exception as exp:
            raise exp

    def plan_to_company(self, company_name, plan_name):
        """Associates plan to company
            Args:
                company_name    (str)   --  name of the company

                plan_name       (str)   --  name of the plan
        """
        try:
            company = self.commcell_obj.organizations.get(company_name)
            self.plans_obj.refresh()
            if self.plans_obj.has_plan(plan_name):
                company.plans = [plan_name]
                self.log.info("Plan {0} associated with copmpany {1}".format(
                    plan_name, company_name)
                )
            else:
                self.log.error("Plan [{0}] does not exist".format(plan_name))
                raise Exception("Plan not found")
        except Exception as exp:
            self.log.error(
                "Plan {0} association to company failed {1} due to {2}".format(
                    plan_name,
                    company_name,
                    str(exp)
                )
            )
            raise Exception(exp)

    def validate_tenant_roles(self, plan_name, user_group):
        """Validates whether a user has the required permissions on a company
            Args:
                plan_name   (str)   --  name of the plan

                user_group   (str)   --  name of the user group
        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            self.log.error("Plan [{0}] does not exist".format(plan_name))
            raise Exception("Plan not found")

        if user_group in plan_obj.security_associations \
            and 'Plan Subscription Role' in plan_obj.security_associations[user_group] \
                and 'Derived Plan Creator Role' in plan_obj.security_associations[user_group]:
            self.log.info('Tenant admin has required roles on the plan {0}'.format(plan_name))
        else:
            self.log.error('Tenant admin does not have adequate roles on the plan {0}'.format(plan_name))
            raise Exception("Security assocation error")

    def company_default_plan(self, company_name, plan_name=None):
        """Sets are removes the default plan of a company
            Args:
                company_name    (str)   --  name of the company whose default plan must be set

                plan_name       (str)   --  name of the plan to be set as the default plan
                                            None: for having no default plans set
        """
        try:
            company = self.commcell_obj.organizations.get(company_name)
            if plan_name and self.plans_obj.has_plan(plan_name):
                company.default_plan = plan_name
            else:
                company.default_plan = None
            self.log.info("Default plan successfully modified")
        except Exception as exp:
            self.log.error(
                "Plan {0} association to company failed {1} due to {2}".format(
                    plan_name,
                    company_name,
                    str(exp)
                )
            )
            raise Exception(exp)

    def validate_default_plan(self, company_name, plan_name):
        """Validates whether the plan is associatedwit hthe company
            Args:
                company_name    (str)   --  name of the company whose default plan must be validated

                plan_name       (str)   --  name of the plan to be valited

            Returns:
                bool        -- True of validated successfully
        """
        try:
            company = self.commcell_obj.organizations.get(company_name)
            return company.default_plan == plan_name
        except Exception as exp:
            self.log.error(
                "Plan {0} default plan association to company failed {1}".format(
                    plan_name,
                    company_name
                )
            )
            raise Exception(exp)

    def modify_inheritance(self, plan_name, override_entities):
        """Modify override restrictions of a base plan
            Args:
                plan_name           (str)   --  name of the plan

                override_entities   (dict)  --  override restrictions to be
                                                added
        """
        try:
            if self.plans_obj.has_plan(plan_name):
                base_plan = self.plans_obj.get(plan_name)
                base_plan.override_entities = override_entities
                return base_plan
            else:
                self.log.error("Plan [{0}] does not exist".format(plan_name))
                raise Exception("Base plan not found")
        except Exception as exp:
            self.log.error(
                "Failed to modify override restrictions due to - {1}".format(
                    str(exp)
                )
            )
            raise Exception(exp)

    def cleanup_plans(self, marker):
        """Delete plans that were marked for deletion during previous runs

            Args:
                marker      (str)   --  marker tagged to plans for deletion
        """
        self.plans_obj.refresh()
        for plan in self.plans_obj.all_plans:
            if marker.lower() in plan:
                try:
                    self.plans_obj.delete(plan)
                    self.log.info("Deleted plan - {0}".format(plan))
                except Exception as exp:
                    self.log.error(
                        "Unable to delete plan {0} due to {1}".format(
                            plan,
                            str(exp)
                        )
                    )

    def validate_overriding(self,
                            base_plan_name,
                            override_entities):
        """Validates override restrictions of base plans

            Args:
                base_plan_name      (str)   --  base plan name

                override_entities   (dict)  --  override restrictions to be
                                                validated

            Returns:
                bool                    -- inheriance validation case
        """
        if self.plans_obj.has_plan(base_plan_name):
            base_plan = self.plans_obj.get(base_plan_name)
        else:
            raise Exception("Base plan not found")

        for entities in override_entities:
            if entities == 'privateEntities' and sorted(override_entities[entities]) != sorted(base_plan.override_entities['privateEntities']):
                self.log.error("Private entities restriction not matched")
                raise Exception(
                    "Override restriction of private entities failed"
                )
            if entities == 'enforcedEntities':
                enf_list = list(
                    filter(
                        lambda e: e not in [8, 128, 4096], base_plan.override_entities[
                            'enforcedEntities'
                        ]
                    )
                )
                if sorted(override_entities[entities]) != sorted(enf_list):
                    self.log.error("Enforced enitties restriction not matched")
                    raise Exception(
                        "Override restriction of enforced entities failed"
                    )
        self.log.info(
            "Override restriction rules of {0} validated successfully".format(
                base_plan_name
            )
        )

    def validate_inheritance(self,
                             base_plan_name,
                             derived_plan_name,
                             override_entities):
        """Validates whether inheritance is appropriately followed on derivation

            Args:
                base_plan_name      (str)   --  base plan name

                derived_plan_name   (str)   --  derived plan name

                override_entities   (dict)  --  override entity details
        """
        self.plans_obj.refresh()
        if self.plans_obj.has_plan(base_plan_name):
            base_plan = self.plans_obj.get(base_plan_name)
        else:
            raise Exception("Base plan not found")

        if self.plans_obj.has_plan(derived_plan_name):
            derived_plan = self.plans_obj.get(derived_plan_name)
        else:
            raise Exception("Derived plan not found")

        for entities in override_entities:
            for entity in override_entities[entities]:
                if entities == 'privateEntities':
                    if (entity == 1 and
                            base_plan.storage_policy == derived_plan.storage_policy):
                        raise Exception("Failure in overriding storage")
                    if (entity == 4 and
                            base_plan.schedule_policies == derived_plan.schedule_policies):
                        raise Exception("Failure in overriding RPO/Schedules")
                    if (entity in [256, 512, 1024] and
                            base_plan.subclient_policy == derived_plan.subclient_policy):
                        raise Exception("Failure in overriding backup content")
                    self.log.info("Private entities successfully overridden")

                if entities == 'enforcedEntities':
                    if (entity == 1 and
                            base_plan.storage_policy.storage_policy_id !=
                            derived_plan.storage_policy.storage_policy_id):
                        raise Exception("Failure in inheriting storage")
                    if (entity == 4 and
                            base_plan.schedule_policies['data'].schedule_policy_id !=
                            derived_plan.schedule_policies['data'].schedule_policy_id or
                            base_plan.schedule_policies['log'].schedule_policy_id !=
                            derived_plan.schedule_policies['log'].schedule_policy_id):
                        raise Exception("Failure in inheriting RPO/Schedules")
                    if (entity in [256, 512, 1024] and
                            base_plan.subclient_policy != derived_plan.subclient_policy):
                        raise Exception("Failure in inheriting backup content")
                    self.log.info("Enforced entities successfully inherited")
        self.log.info("Inheritance validated successfully")

    def validate_schedules(self, plan_name):
        """Validates whether plan has appropriate schedules as defined

            Args:
                plan_name   (str)       --  name of the plan to be validated

            Returns:
                bool        -- True if validated successfully

        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            raise Exception("Plan not found")

        required_sched = {
            'dataInc': False,
            'dataFull': False,
            'synthFull': False,
            'logInc': False
        }
        for schedule_type in plan_obj.schedule_policies.keys():
            schedules = plan_obj.schedule_policies[schedule_type].all_schedules

            for schedule in schedules:
                try:
                    schedule_dict = plan_obj.schedule_policies[schedule_type].get_schedule(
                        schedule_id=schedule['schedule_id']
                    )
                    if schedule_type == 'data':
                        if schedule_dict['options']['backupOpts']['backupLevel'] == 2 \
                                and schedule_dict['subTask']['flags'] == 65536:
                            required_sched['dataInc'] = True
                            self.log.info("Plan {0} contains data incremental schedule".format(plan_name))
                        if schedule_dict['options']['backupOpts']['backupLevel'] == 1 \
                                and schedule_dict['subTask']['flags'] == 4194304:
                            required_sched['dataFull'] = True
                            self.log.info("Plan {0} contains data full schedule".format(plan_name))
                        if schedule_dict['options']['backupOpts']['backupLevel'] == 4:
                            required_sched['synthFull'] = True
                            self.log.info("Plan {0} contains data synth full schedule".format(plan_name))
                    else:
                        if schedule_dict['options']['backupOpts']['backupLevel'] == 2 \
                                and schedule_dict['subTask']['flags'] == 65536:
                            required_sched['logInc'] = True
                            self.log.info("Plan {0} contains log incremental schedule".format(plan_name))
                except Exception as exp:
                    self.log.error("Schedule options not matching" + str(exp))
                    return False
        return all(list(required_sched.values()))

    def modify_rpo(self, plan_name, frequency, full_schedule=False):
        """Edits the RPO schedule of a plan

            Args:
                plan_name   (str)   --  name of the plan whose RPO is to be edited

                frequency   (dict)  --  dictionary which specifies the frequency of the RPO schedule
                                            Examples:
                                                {
                                                    'minutes': 5
                                                },
                                                {
                                                    'hours': 4
                                                },
                                                {
                                                    'days': {
                                                        'runEvery': 2,
                                                        'startTime': '03:30'
                                                    }
                                                },
                                                {
                                                    'weeks': {
                                                        'runEvery': 2,
                                                        'days': ['Monday', 'Fiday'],
                                                        'startTime': '03:30'
                                                    }
                                                },
                                                {
                                                    'months': {
                                                        'runEvery': 2,
                                                        'daysToRun': {'week': 'First', 'day': 'Sunday'},
                                                        'startTime': '03:30'
                                                    }
                                                },
                                                {
                                                    'year': {
                                                        'runEvery': 2,
                                                        'freq_interval': 10
                                                        'freq_relative_interval': 2,
                                                        'freq_recurrence_factor': 6
                                                        'startTime': '03:30'
                                                    }
                                                }

                full_schedule   (bool)  --  if modification to be made to full schedule
        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            raise Exception("Plan not found")

        schedule_json = {'pattern': {}}
        if 'minutes' in frequency:
            schedule_json['pattern'].update({
                'freq_type': 'After_job_completes',
                'active_end_time': '23:59',
                'freq_interval': frequency['minutes'],
                'freq_recurrence_factor': 1
            })
        elif 'hours' in frequency:
            schedule_json['pattern'].update({
                'freq_type': 'After_job_completes',
                'active_end_time': '23:59',
                'freq_interval': frequency['hours'] * 60,
                'freq_recurrence_factor': 1
            })
        elif 'days' in frequency:
            schedule_json['pattern'].update({
                "freq_type": "Daily",
                "freq_interval": frequency['days']['runEvery'],
                "freq_recurrence_factor": frequency['days']['runEvery'],
                "repeat_days": frequency['days']['runEvery'],
                "active_start_time": frequency['days']['startTime'],
                "active_end_time": '23:59'
            })
        elif 'weeks' in frequency:
            schedule_json['pattern'].update({
                "freq_type": "Weekly",
                "freq_recurrence_factor": frequency['weeks']['runEvery'],
                "active_start_time": frequency['weeks']['startTime'],
                "active_end_time": '23:59',
                'weekdays': dict.fromkeys(frequency['weeks']['days'], True)
            })
        elif 'months_relative' in frequency.keys():
            schedule_json['pattern'].update({
                "freq_type": "Monthly_Relative",
                "freq_relative_interval": frequency['months_relative']['freq_relative_interval'],
                "freq_interval": frequency['months_relative']['freq_interval'],
                "freq_recurrence_factor": frequency['months_relative']['runEvery'],
                "active_start_time": frequency['months_relative']['startTime'],
                "active_end_time": '23:59'
            })
        elif 'months' in frequency.keys():
            schedule_json['pattern'].update({
                "freq_type": "Monthly",
                "freq_relative_interval": 0,
                "freq_interval": frequency['months']['freq_interval'],
                "freq_recurrence_factor": frequency['months']['runEvery'],
                "active_start_time": frequency['months']['startTime'],
                "active_end_time": '23:59'
            })
        elif 'year_relative' in frequency.keys():
            schedule_json['pattern'].update({
                "freq_type": "Yearly_Relative",
                "freq_interval": frequency['year_relative']['freq_interval'],
                "freq_relative_interval": frequency['year_relative']['freq_relative_interval'],
                "freq_recurrence_factor": frequency['year_relative']['freq_recurrence_factor'],
                "active_start_time": frequency['year_relative']['startTime'],
                "active_end_time": '23:59'
            })
        elif 'year' in frequency.keys():
            schedule_json['pattern'].update({
                "freq_type": "Yearly",
                "freq_interval": frequency['year']['freq_interval'],
                "freq_relative_interval": 0,
                "freq_recurrence_factor": frequency['year']['freq_recurrence_factor'],
                "active_start_time": frequency['year']['startTime'],
                "active_end_time": '23:59'
            })
        else:
            raise Exception("Invalid input")

        plan_obj.modify_schedule(schedule_json, full_schedule)
        self.log.info("RPO modified successfully")

    def validate_rpo(self, plan_name, sla_in_minutes, pattern=None, policy_type='data', full_schedule=False):
        """Validates the RPO of the plan
            Args:
                plan_name   (str)   --  name of the plan

                sla_in_minutes  (str)   --  RPO/SLA value to be validated

                pattern         (dict)  --  pattern of the RPO schedule,

                policy_type     (str)   --  type of policy to be validated

                full_schedule   (bool)  --  check if schedule to be validated is full schedule

            Returns:
                bool        -- True if validated successfully
        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            raise Exception("Plan not found")

        if plan_obj.sla_in_minutes == sla_in_minutes:
            self.log.info("Plan {0} has appropriate RPO of {1} minutes".format(plan_name, sla_in_minutes))
        else:
            return False

        if pattern:
            if policy_type == 'log':
                plan_pattern = plan_obj.schedule_policies[policy_type].get_schedule(
                    schedule_name='Incremental automatic schedule for logs'
                )['pattern']
            elif full_schedule:
                plan_pattern = plan_obj.schedule_policies[policy_type].get_schedule(
                        schedule_name='Full backup schedule'
                    )['pattern']
            else:
                plan_pattern = plan_obj.schedule_policies[policy_type].get_schedule(
                    schedule_name='Incremental backup schedule'
                )['pattern']
            hours = plan_pattern['active_start_time'] // 3600
            minutes = plan_pattern['active_start_time'] // 60 - hours * 60
            if 'days' in pattern:
                if pattern['days']['runEvery'] == plan_pattern['freq_interval'] and \
                        pattern['days']['startTime'] == "%02d:%02d" % (hours, minutes):
                    self.log.info("Plan {0} schedule pattern validated".format(
                        plan_name
                    ))
                    return True
                else:
                    self.log.error("Plan {0} schedule pattern validation failed".format(
                        plan_name
                    ))
                    return False
            elif 'weeks' in pattern:
                if pattern['weeks']['runEvery'] == plan_pattern['freq_recurrence_factor'] and \
                        pattern['weeks']['startTime'] == "%02d:%02d" % (hours, minutes) and \
                        not set(pattern['weeks']['days']) - \
                        set([(day) for day in plan_pattern['daysToRun'] if plan_pattern['daysToRun'][day]]):
                    self.log.info("Plan {0} schedule pattern validated".format(
                        plan_name
                    ))
                    return True
                else:
                    self.log.error("Plan {0} schedule pattern validation failed".format(
                        plan_name
                    ))
                    return False
            else:
                plan_pattern['freq_type'] == 1024
                self.log.info("Plan {0} has an automatic log schedule".format(plan_name))
                return True
        else:
            return True

    def disable_schedule(self, plan_name, schedule_name='Full'):
        """Disables any of the schedule of the plan

            Args:
                plan_name   (str)   --  name of the plan whose schedule must be disabled

                schedule_name (str) --  name of the schedule that must be disabled
        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            raise Exception("Plan not found")

        if schedule_name == 'Full':
            plan_obj.disable_full_schedule()
        else:
            plan_obj.schedule_policies['data'].delete_schedule(schedule_name=schedule_name)
        self.log.info("RPO modified successfully")

    def rename_plan(self, plan_name, new_plan_name):
        """renames a plan
            Args:
                plan_name   (str)   --  Plan's existing name

                new_plan_name (str) --  Plan's new name
        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            raise Exception("Plan not found")

        plan_obj.plan_name = new_plan_name

    def validate_entity_names(self, plan_name):
        """Validates whether base plan name string is a part of the  child entities
            Args:
                plan_name   (str)   --  name of the plan
        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            raise Exception("Plan not found")

        if plan_name not in plan_obj.storage_policy.name:
            self.log.error("Storage policy name does not resemble plan name")
            raise Exception("Plan entity renaming failure")

        if plan_name not in plan_obj.schedule_policies['data'].schedule_policy_name:
            self.log.error("Schedule policy name does not resemble plan name")
            raise Exception("Plan entity renaming failure")

        if plan_name not in plan_obj.subclient_policy.name:
            self.log.error("Storage policy name does not resemble plan name")
            raise Exception("Plan entity renaming failure")

        self.log.info("Plan entities renamed accordingly")

    def add_copy(self, plan_name, pool_name, retention=30, extended_retention=None):
        """Adds a storage copy to the plan
            Args:
                plan_name   (str)   --  plan to which storage is to be added

                pool_name   (str)   --  storage pool name which must be added as a copy to the plan

                retention   (int)   --  retention period of the copy

                extended_retention (tuple)  -   extended retention rules of a copy
                                                Example: [1, True, "EXTENDED_ALLFULL", 0, 0]
        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            raise Exception("Plan not found")

        copy_name = 'Copy - ' + str(len(plan_obj.storage_copies) + 1)
        copies = plan_obj.add_storage_copy(
            copy_name,
            pool_name,
            retention,
            extended_retention
        )

        if copy_name in copies:
            self.log.info('Storage copy {0} added successfully to plan {1}'.format(
                copy_name,
                plan_name
            ))
        else:
            self.log.error('Failed to add copy {0}  to plan {1}'.format(
                copy_name,
                plan_name
            ))
            raise Exception("Failure in adding storage copy to plan")

        return copy_name

    def delete_copy(self, plan_name, copy_name):
        """Deletes the backup copy from the plan's storage policy
            Args:
                plan_name   (str)   --  plan whose stroage is to be deleted

                copy_name   (str)   --  name of the copy to be deleted
        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            raise Exception("Plan not found")

        try:
            if plan_obj.storage_policy.has_copy(copy_name):
                plan_obj.storage_policy.delete_secondary_copy(copy_name)
                self.log.info("Successfully deleted copy {0} of plan - {1}".format(copy_name, plan_name))
                return True
            else:
                raise Exception("Copy {0} not found".format(copy_name))
        except Exception:
            self.log.error("Failed to delete copy {0} of plan {1}".format(copy_name, plan_name))
            return False

    def validate_copies(self, plan_name, primary_copy, secondary_copy={}):
        """validates the storage copies of a plan

            Args:
                plan_name   (str)   --  name of the plan to be validated

                primary_copy (str)  --  name of the primary copy storage pool

                secondary_copy (dict)   -- mapping of secondary copies and their retentions

            Returns:
                (bool)    --  whether validation of copies was succiessful
        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            raise Exception("Plan not found")

        if 'Primary' in plan_obj.storage_copies:
            if plan_obj.storage_copies['Primary']['storagePool'] \
                    == primary_copy.lower():
                self.log.info('Primary copy of plan - {0} validated'.format(plan_name))
            else:
                self.log.error('Primary copy does not match the one created with the plan - {0}'.format(plan_name))
                return False

        if secondary_copy:
            for copy in secondary_copy.keys():
                if copy in plan_obj.storage_copies \
                    and secondary_copy[copy]['storagePool'] == plan_obj.storage_copies[copy]['storagePool'] \
                        and secondary_copy[copy]['retention'] == plan_obj.storage_copies[copy]['retainBackupDataForDays']:
                    self.log.info('Secondary copy values matched for plan {0}'.format(plan_name))
                else:
                    self.log.error('Secondary copies does not match the added copies for plan - {0}'.format(plan_name))
                    return False
                if 'extendedRetention' in secondary_copy[copy]:
                    secondary_copy[copy]['extendedRetention'] = list(secondary_copy[copy]['extendedRetention'])
                    if secondary_copy[copy]['extendedRetention'][2] == "EXTENDED_ALLFULL":
                        secondary_copy[copy]['extendedRetention'][2] = 2
                    elif secondary_copy[copy]['extendedRetention'][2] == "EXTENDED_WEEK":
                        secondary_copy[copy]['extendedRetention'][2] = 4
                    elif secondary_copy[copy]['extendedRetention'][2] == "EXTENDED_MONTH":
                        secondary_copy[copy]['extendedRetention'][2] = 8
                    elif secondary_copy[copy]['extendedRetention'][2] == "EXTENDED_QUARTER":
                        secondary_copy[copy]['extendedRetention'][2] = 16
                    elif secondary_copy[copy]['extendedRetention'][2] == "EXTENDED_HALFYEAR":
                        secondary_copy[copy]['extendedRetention'][2] = 32
                    elif secondary_copy[copy]['extendedRetention'][2] == "EXTENDED_YEAR":
                        secondary_copy[copy]['extendedRetention'][2] = 64
                    if tuple(secondary_copy[copy]['extendedRetention']) == plan_obj.storage_copies[copy]['extendedRetention']:
                        self.log.info('Secondary copy extended retention values matched for plan {0}'.format(plan_name))
                    else:
                        self.log.error('Secondary copies retention rule does not match for - {0}'.format(plan_name))
                        return False
        self.log.info('All storage copies of {0} plan validate successfully'.format(plan_name))
        return True

    def entity_to_plan(self, plan_name, client_name, backup_set, subclient=None):
        """Associates plan to FS backupset or subclient
            Args:
                plan_name   (str)   --  name of the plan that must be associated

                client_name (str)   --  client in which the backupset or subclient belongs

                backup_set  (str)   --  name of the backupset to which the plan must be asocaited with

                subclient   (str)   --  name of the subclient to which the plan must be assocaited with
        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            raise Exception("Plan not found")

        if self.commcell_obj.clients.has_client(client_name):
            client_obj = self.commcell_obj.clients.get(client_name)
            if client_obj.agents.has_agent('File System'):
                agent_obj = client_obj.agents.get('File System')
                if agent_obj.backupsets.has_backupset(backup_set):
                    backup_set_obj = agent_obj.backupsets.get(backup_set)
                    if not subclient:
                        backup_set_obj.plan = plan_obj
                        self.log.info('Plan {0} successfully assocaited to backupset {1}'.format(
                            plan_name,
                            backup_set
                        ))
                        return
                    else:
                        subclient_obj = backup_set_obj.subclients.get(subclient)
                        subclient_obj.plan = plan_obj
                        self.log.info('Plan {0} successfully assocaited to subclient {1}'.format(
                            plan_name,
                            subclient
                        ))
                        return
        self.log.error('Client {0}, backupset {1} not found.'.format(client_name, backup_set))
        raise Exception("Entity not found")

    def validate_subclient_association(self, plan_name, client_name, backup_set, subclient, validate_rpo=False):
        """Associates plan to or subclient
            Args:
                plan_name   (str)   --  name of the plan that must be associated

                client_name (str)   --  client in which the backupset or subclient belongs

                backup_set  (str)   --  name of the backupset to which the plan must be asocaited with

                subclient   (str)   --  name of the subclient

            Returns:
                (bool)      - True if validation successful
        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            raise Exception("Plan not found")

        if self.commcell_obj.clients.has_client(client_name):
            client_obj = self.commcell_obj.clients.get(client_name)
            if client_obj.agents.has_agent('File System'):
                agent_obj = client_obj.agents.get('File System')
                if agent_obj.backupsets.has_backupset(backup_set):
                    backup_set_obj = agent_obj.backupsets.get(backup_set)
                    subclient_obj = backup_set_obj.subclients.get(subclient)
                    if subclient_obj.plan == plan_name:
                        self.log.info('Plan {0} associated to subclient {1}'.format(
                            plan_name,
                            subclient
                        ))

                        if subclient_obj.storage_policy.lower() == plan_obj.storage_policy.storage_policy_name:
                            self.log.info('Plan storage policy associated to subclient')
                        else:
                            self.log.error('Storage policy not assocaited to subclient')
                            return False

                        for schedule in plan_obj.schedule_policies['data'].all_schedules:
                            if schedule['schedule_id'] in subclient_obj.schedules.schedules:
                                self.log.info("Plan's {0} is associated with subclient".format(
                                    schedule['schedule_name'])
                                )
                            else:
                                self.log.error("Schedule {0} failed to associate with subclient".format(
                                    schedule['schedule_name'])
                                )
                                return False

                        rpo_bracket = datetime.datetime.now() + datetime.timedelta(minutes=plan_obj.sla_in_minutes)
                        if validate_rpo:
                            if subclient_obj.next_backup_time and \
                                    datetime.datetime.strptime(subclient_obj.next_backup_time, "%c") < rpo_bracket:
                                self.log.info("The next backup time of the subclient falls under the RPO of the plan")
                            else:
                                self.log.info("The next backup time exceeds the RPO of the plan, RPO vlaidation failure")
                                return False

                        for entity in plan_obj.associated_entities:
                            if subclient_obj.subclient_id == str(entity['subclientId']) or entity['backupsetName'].lower() == backup_set.lower():
                                self.log.info('Subclient is listed in associated entities of the plan')
                                return True
        return False

    def validate_backupset_association(self, plan_name, client_name, backup_set):
        """Associates plan to FS backupset or subclient
            Args:
                plan_name   (str)   --  name of the plan that must be associated

                client_name (str)   --  client in which the backupset or subclient belongs

                backup_set  (str)   --  name of the backupset to which the plan must be asocaited with

            Returns:
                (bool)      - True if validation successful
        """
        self.log.info('Validating plan association to backupset...')
        try:
            backup_set_obj = self.commcell_obj.clients.get(client_name).agents.get('File System').backupsets.get(backup_set)
            backup_set_obj.plan = plan_name
            if backup_set_obj.plan.plan_name.lower() != plan_name.lower(): return False
            self.log.info('Plan successfully associated to backupset')
            
            if not self.validate_subclient_association(
                            plan_name,
                            client_name,
                            backup_set,
                            backup_set_obj.subclients.default_subclient
                            ): return False
            self.log.info('Plan is successfully associated to backupset and its default subclient.')
        except Exception as exp:
            self.log.info(f'Plan association failed : {exp}')
            return False
        return True

    def dissociate_entity(self, client_name, backup_set, subclient=None):
        """Dissociates plan from FS backupset or subclient
            Args:
                client_name (str)   --  client in which the backupset or subclient belongs

                backup_set  (str)   --  name of the backupset to which the plan must be asocaited with

                subclient   (str)   --  name of the subclient to which the plan must be assocaited with

            Returns:
                (bool)      --  True if validation successful
        """
        if self.commcell_obj.clients.has_client(client_name):
            client_obj = self.commcell_obj.clients.get(client_name)
            if client_obj.agents.has_agent('File System'):
                agent_obj = client_obj.agents.get('File System')
                if agent_obj.backupsets.has_backupset(backup_set):
                    backup_set_obj = agent_obj.backupsets.get(backup_set)
                    if not subclient:
                        backup_set_obj.plan = None
                        self.log.info('Plan dissociated from backupset {0}'.format(backup_set))
                        return True
                    else:
                        subclient_obj = backup_set_obj.subclients.get(subclient)
                        subclient_obj.plan = None
                        self.log.info('Plan dissociated from subclient {0}'.format(subclient))
                        return True
        self.log.error('Client {0}, backupset {1} not found.'.format(client_name, backup_set))
        return False

    def validate_dissociation(self, client_name, backup_set, subclient):
        """Validates the dissociation of plan from subclient
            Args:client_name (str)   --  client in which the backupset or subclient belongs

                backup_set  (str)   --  name of the backupset to which the plan must be asocaited with

                subclient   (str)   --  name of the subclient
        """
        if self.commcell_obj.clients.has_client(client_name):
            client_obj = self.commcell_obj.clients.get(client_name)
            if client_obj.agents.has_agent('File System'):
                agent_obj = client_obj.agents.get('File System')
                if agent_obj.backupsets.has_backupset(backup_set):
                    backup_set_obj = agent_obj.backupsets.get(backup_set)
                    subclient_obj = backup_set_obj.subclients.get(subclient)
                    if not subclient_obj.plan:
                        self.log.info('Plan dissociated from to subclient')
                        if not subclient_obj.storage_policy:
                            self.log.info('Plan storage policy associated to subclient')
                        else:
                            self.log.error('Storage policy not assocaited to subclient')
                            raise Exception('Storage assocaition failed')
                        return True
        return False

    def policy_to_subclient(self, plan_name, client_name, backup_set, subclient):
        """Associates a plan's storage policy to a subclient
            Args:
                plan_name   (str)   --  plan whose storage policy is to be associated to subclient

                client_name (str)   --  client in which the backupset or subclient belongs

                backup_set  (str)   --  name of the backupset to which the plan must be asocaited with

                subclient   (str)   --  name of the subclient

            Returns:
                (bool)      -- True if association is successful
        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            raise Exception("Plan not found")

        if self.commcell_obj.clients.has_client(client_name):
            client_obj = self.commcell_obj.clients.get(client_name)
            if client_obj.agents.has_agent('File System'):
                agent_obj = client_obj.agents.get('File System')
                if agent_obj.backupsets.has_backupset(backup_set):
                    backup_set_obj = agent_obj.backupsets.get(backup_set)
                    subclient_obj = backup_set_obj.subclients.get(subclient)
                    subclient_obj.storage_policy = plan_obj.storage_policy.storage_policy_name
                    self.log.info('Storage policy of plan {0} assocaited to subclient {1}'.format(
                        plan_name,
                        subclient
                    ))
                    return True
        self.log.error('Client {0}, backupset {1} not found.'.format(client_name, backup_set))
        raise Exception('Entity not found')

    def validate_autocopy(self, plan_name, schedule_name):
        """Validates the association of aux copy schedule policy with the plan's storage policy
            Args:
                plan_name   (str)   --  plan whose storage policy is to be validated

                schedule_name   (str) --    Aux copy schedule policy name

            Returns:
                (bool)      -- True if autocopy validation is successful
        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            raise Exception("Plan not found")

        if self.commcell_obj.schedule_policies.has_policy(schedule_name):
            associations = self.commcell_obj.schedule_policies.get(schedule_name)._associations
            if (any(e['storagePolicyName'].lower() ==
                    plan_obj.storage_policy.storage_policy_name for e in associations)):
                self.log.info("Plan {0} has autocopy {1} associated".format(plan_name, schedule_name))
                return True
            else:
                self.log.error("Plan {0} does not have autocopy {1}".format(plan_name, schedule_name))
                return False
        else:
            self.log.error("Autocopy schedule - {0} not found".format(schedule_name))
            return False

    def set_operation_window(self, plan_name, window_list, full=False):
        """Sets or deletes the operation window of a plan
            Args:
                plan_name   (str)   --  plan whose operation window is to be set

                window_list   (str) --  operation window rule
                                          None: delete window

                full        (bool)  --  True if operation window is full
        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            raise Exception("Plan not found")

        try:
            exec('plan_obj.{0}operation_window = {1}'.format(
                ('full_' if full else ''), ('window_list' if window_list else 'None')))
            self.log.info("Operation window set for plan {0}".format(plan_name))
            return
        except Exception as exp:
            self.log.error("Failed to set operation window set for plan {0}".format(plan_name))
            raise Exception("Failed to set operaion window due to - {0}".format(exp))

    def validate_operation_window(self, plan_name, window_list, full=False):
        """Validate the operation window of a plan
            Args:
                plan_name   (str)   --  plan whose operation window is to be set

                window_list   (str) --  operation window rule
                                          None: delete window

                full        (bool)  --  True if operation window is full

            Returns:
                (bool)     --   True if validated successfully
        """
        if self.plans_obj.has_plan(plan_name):
            plan_obj = self.plans_obj.get(plan_name)
        else:
            raise Exception("Plan not found")

        try:
            op_dict = eval('plan_obj.{0}operation_window'.format('full_' if full else ''))
            if op_dict:
                if (op_dict['dayTime'][0]['startTime'] == window_list[1]['startTime']
                        and op_dict['dayTime'][0]['endTime'] == window_list[1]['endTime']):
                    self.log.info("Operation window set for plan {0}".format(plan_name))
                    return True
                else:
                    self.log.error("Operation window deletion for plan {0} validation failed".format(plan_name))
                    return False
            if not window_list and not op_dict:
                self.log.info("Operation window deletion for plan {0} validated".format(plan_name))
                return True
            else:
                self.log.error("Operation window deletion for plan {0} validation failed".format(plan_name))
                return False

        except Exception as exp:
            self.log.error("Failed to set operation window set for plan {0}".format(plan_name))
            raise Exception("Failed to set operaion window due to - {0}".format(exp))

    def create_ndd_storage(self, req_payload):
        """Creates a non-dedupe storage pool
            Args:
                storage_name    (str)   -   name of the storage pool

                media_agent_name   (str)   - media agent name

                moutpath   (str)   -   path for storage pool

            Returns:
                (str)   - name of the storage pool
        """
        storage_pool = "%sStoragePool?Action=create" % (self.commcell_obj._web_service)

        flag, response = self.commcell_obj._cvpysdk_object.make_request(
            'POST',
            url=storage_pool,
            payload=req_payload
        )

        if flag:
            if response.json() and 'archiveGroupCopy' in response.json():
                self.commcell_obj.storage_pools.refresh()
                return response.json()['archiveGroupCopy']['storagePolicyName']
        else:
            raise Exception("Non dedupe storage pool creation failed")
            
    def validate_applicable_solution_edit(self, plan_name: str = str(), solutions: list = list()):
        """Method to validate applicable solution edits"""
        plan_obj = self.plans_obj.get(plan_name)
        try:
            plan_obj.applicable_solutions = solutions
            self.log.info(f'Applicable solutions set to => {plan_obj.applicable_solutions}')
        except Exception as err:
            self.log.info(f'Applicable Solution Edit Failed via API: [{err}]')
            return False
        return sorted(plan_obj.applicable_solutions) == sorted(solutions)

    def get_assoc_entity_count_from_api(self)->dict:
        """Method to get the associated Entity Count from plan summary API response"""
        result_dict = self.plans_obj.get_plans_cache(hard=True, fl=['numAssocEntities'])
        result_dict = {key: value['numAssocEntities'] for key, value in result_dict.items() if 'numAssocEntities' in value}
        self.log.info("successfully fetched the associated entities count for all plans from MongoDB")
        return result_dict

    def get_assoc_entity_count_for_plan(self,plan_name:str)->int:
        """Method to get associated entity count for a plan
        Note: this method would only fetch the count on basis of subclient level association
        """
        if self.plans_obj.has_plan(plan_name):
            plan_id = self.plans_obj.get(plan_name).plan_id
            self.log.info(f"calculating associated entity count for plan {plan_name} ...")
            self.csdb.execute("select count(1) from APP_SubclientProp asp with (noLock) inner join APP_Application ap with (noLock) on "
                              "asp.componentNameId= ap.id and ap.subclientStatus <> 4 where asp.attrName "
                              f"like 'Associated Plan' and asp.modified=0 and asp.attrVal = {plan_id}")
            return self.csdb.fetch_all_rows()[0][0]
        else:
            raise Exception("Plan not found")

    def validate_plans_assoc_entity_count(self, plan_name:str, client_name:str, backup_set:str, operation:str)->bool:
        """
        Method to associate/dissociate the backupset to the plan and validate the API response count getting modified
        Also, verify if Associated entity count from API response return is same as that of count in CSDB
        Args:
            plan_name       (str)   : name of the test plan
            client_name     (str)   : name of the client
            backup_set      (str)   : name of the backup set where subclients would be created
            operation       (str)   : desired operation between the subclient and plan
                                                example : "association"/"dissociation"

        returns:
            (boolean) - validation result
        """
        api_count1 = self.get_assoc_entity_count_from_api()[plan_name]
        self.log.info(f"Count returned in API response before validation for plan {plan_name} is {api_count1}")

        if operation.lower() == "association":
            if self.validate_backupset_association(plan_name,client_name,backup_set):
                self.log.info(f"successfully associated {backup_set} to {plan_name}")
            else:
                raise Exception(f"plan association failed for backupset : {backup_set}")
        elif operation.lower() == "dissociation":
            self.dissociate_entity(client_name,backup_set)
            if self.validate_dissociation(client_name, backup_set,"default"):
                self.log.info(f"successfully dissociated {backup_set} to {plan_name}")
            else:
                raise Exception(f"plan dissociated failed for backupset : {backup_set}")
        time.sleep(60)
        api_count2 = int(self.get_assoc_entity_count_from_api()[plan_name])
        csdb_count = int(self.get_assoc_entity_count_for_plan(plan_name))

        self.log.info(f"Count returned in API response After validation for plan {plan_name} is {api_count2}")
        self.log.info(f"Count returned from csdb After validation for plan {plan_name} is {csdb_count}")
        if api_count1 != api_count2:
            self.log.info("validation for API response passed")
            if api_count2 != csdb_count:
                raise Exception(f"validation failed! API response's count ({api_count2}) does not matches with"
                                f" CSDB's count ({csdb_count})")
            self.log.info("validation successful! API response's count matches with CSDB's count")
            return True
        else:
            raise Exception(f"validation failed!")
        
    def associate_user_to_plan(self, plan_name, userlist, send_invite=True):
        """associates the users to the plan.

           Arguments:
           
                plan_name(str) - plan name to associate the user 
           
                userlist(list /str) - user to be associated to the plans.

            Raises:
                SDKException:
                    if response is empty

                    if response is not success

        """
        try:
            if isinstance(userlist, str):
                input_users = [userlist]
            if self.plans_obj.has_plan(plan_name):
                plan_obj = self.plans_obj.get(plan_name)
                plan_obj.associate_user(input_users, send_invite)
            else:
                raise Exception("Plan not found")

        except Exception as exp:
            self.log.error("Failed to associate the user to the plan")
            raise Exception(exp)

    def _get_plan_status(self, plan_id: int) -> int:
        """Method to get plan status from DB"""
        self.csdb.execute(f'select flag from app_plan where id = {plan_id}')
        status = int(self.csdb.rows[0][0])
        return status

    def validate_plans_cache_data(self) -> bool:
        """
        Validates the data returned from Mongo cache for plans collection.

        Returns:
            bool: True if validation passes, False otherwise
        """
        self.log.info("Starting validation for plans cache...")
        cache = self.plans_obj.get_plans_cache(enum=False)
        out_of_sync = []

        for plan, cache_data in cache.items():
            self.log.info(f'Validating cache for plan: {plan}')
            plan_obj = self.plans_obj.get(plan)
            plan_prop = plan_obj.get_plan_properties()
            validations = {
                'planId': int(plan_obj.plan_id),
                'planType': int(plan_obj.subtype),
                'numCopies': len(plan_obj.storage_copies),
                'numAssocEntities': int(self.get_assoc_entity_count_for_plan(plan)),
                'rpoInMinutes': plan_prop.get('additionalProperties', {}).get("RPO"),
                'planStatusFlag': self._get_plan_status(cache_data.get('planId')),
            }

            for key, expected_value in validations.items():
                self.log.info(f'Comparing key: {key} for plan: {plan}')
                if expected_value is not None and cache_data.get(key) != expected_value:
                    out_of_sync.append((plan, key))
                    self.log.error(f'Cache not in sync for prop "{key}". Cache value: {cache_data.get(key)}; '
                                   f'csdb value: {expected_value}')

            if cache_data.get('storage'):
                self.log.info(f'Comparing key: storage for plan: {plan}')
                if len(cache_data.get('storage')) != len(plan_obj.resources):
                    out_of_sync.append((plan, 'storage'))
                    self.log.error(
                        f'Cache not in sync for prop "storage". Cache value: {len(cache_data.get("storage"))}; '
                        f'csdb value: {len(plan_obj.resources)}')

            if cache_data.get('company') == 'Commcell':
                company_in_cache = cache_data.get('company').lower()
            else:
                company_in_cache = self.commcell_obj.organizations.get(cache_data.get('company')).domain_name.lower()

            self.log.info(f'Comparing key: company for plan: {plan}')
            if company_in_cache != plan_obj.company.lower():
                out_of_sync.append((plan, 'company'))
                self.log.error(f'Cache not in sync for prop "company". Cache value: {cache_data.get("company")} '
                               f'; csdb value: {plan_obj.company}')

        if out_of_sync:
            raise Exception(f'Validation Failed. Cache out of sync: {out_of_sync}')
        else:
            self.log.info('Validation successful. All the plans cache are in sync')
            return True

    def validate_sort_on_cached_data(self) -> bool:
        """
        Method to validate sort parameter on entity cache API call

        Returns:
            bool: True if validation passes, False otherwise
        """
        # setting locale for validating sort
        locale.setlocale(locale.LC_COLLATE, 'English_United States')

        self.log.info("starting Validation for sorting on plans cache...")
        columns = ['planName', 'planType', 'numAssocEntities', 'rpoInMinutes', 'numCopies', 'planStatusFlag', 'storage',
                   'company', 'tags']
        unsorted_col = []
        for col in columns:
            optype = random.choice([1, -1])
            # get sorted cache from Mongo
            cache_res = self.plans_obj.get_plans_cache(fl=[col], sort=[col, optype])
            # sort the sorted list
            if col == 'planName':
                cache_res = list(cache_res.keys())
                res = sorted(cache_res, key=lambda x: locale.strxfrm(str(x)), reverse=optype == -1)
            else:
                cache_res = [[key, value.get(col)] for key, value in cache_res.items() if col in value]
                if all(isinstance(item[1], int) for item in cache_res):
                    res = sorted(cache_res, key=lambda x: x[1], reverse=optype == -1)
                else:
                    res = sorted(cache_res, key=lambda x: locale.strxfrm(str(x[1])), reverse=optype == -1)

            # check if sorted list got modified
            if res == cache_res:
                self.log.info(f'sort on column {col} working.')
            else:
                self.log.error(f'sort on column {col} not working')
                unsorted_col.append(col)
        if not unsorted_col:
            self.log.info("validation on sorting cache passed!")
            return True
        else:
            raise Exception(f"validation on sorting cache Failed! Column : {unsorted_col}")

    def validate_limit_on_cache(self) -> bool:
        """
        Method to validate limit parameter on entity cache API call

        Returns:
            bool: True if validation passes, False otherwise
        """
        cache = self.plans_obj.get_plans_cache()

        # generate random limit
        test_limit = random.randint(1, len(cache.keys()))
        limited_cache = self.plans_obj.get_plans_cache(limit=['0', str(test_limit)])
        # check the count of entities returned in cache
        if len(limited_cache) == test_limit:
            self.log.info('Validation for limit on cache passed!')
            return True
        else:
            self.log.error(f'limit returned in cache : {len(limited_cache)}; expected limit : {test_limit}')
            raise Exception(f"validation for limit on cache Failed!")

    def validate_search_on_cache(self) -> bool:
        """
        Method to validate search parameter on entity cache API call

        Returns:
            bool: True if validation passes, False otherwise
        """
        self.log.info("starting Validation for search on plans cache...")
        # creating a test plan
        plan_name = f"caching_automation_{random.randint(0, 100000)} - plans"
        storage = self.get_storage_pool()
        plan = self.create_base_plan(plan_name, 'Server', storage)

        if plan:
            # calling the API with search param
            response = self.plans_obj.get_plans_cache(search=plan.plan_name)
            # checking if test company is present in response
            if len(response.keys()) == 1 and [True for key in response.keys() if key == plan.plan_name]:
                self.log.info('Validation for search on cache passed')
                return True
            else:
                self.log.error(f'{plan.plan_name} is not returned in the response')
                raise Exception("Validation for search on cache failed!")
        else:
            raise Exception('Failed to create plan. Unable to proceed.')

    def validate_filters_on_cache(self, filters: list, expected_response: list) -> bool:
        """
        Method to validate fq param on entity cache API call

        Args:
            filters (list) -- contains the columnName, condition, and value
                e.g. filters = [['planName', 'contains', 'test'], ['numAssocEntities', 'between', '0-1']]
            expected_response (list) -- expected list of plans to be returned in response

        Returns:
            bool: True if validation passes, False otherwise
        """
        self.log.info("starting Validation for filters on plans cache...")
        if not filters or not expected_response:
            raise ValueError('Required parameters not received')

        try:
            res = self.plans_obj.get_plans_cache(fq=filters)
        except Exception as exp:
            self.log.error("Error fetching plans cache")
            raise Exception(exp)

        missing_plans = [plan for plan in expected_response if plan not in res.keys()]

        if missing_plans:
            raise Exception(f'Validation failed. Missing plans: {missing_plans}')
        self.log.info("validation for filter on cache passed!")
        return True
