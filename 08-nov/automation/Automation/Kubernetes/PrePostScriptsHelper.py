# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This file defines the classes for the Pre, Post script custom resources (CVTask and CVTaskSet)

Classes defined:

    CVTask                  --      Generates and creates the CVTask resource

    CVTaskSet               --      Generates and creates the CVTaskSet resource

"""

from Kubernetes.constants import CVTaskConstants, CVTaskSetConstants, FIELD_NAME, FIELD_KIND, FIELD_VERSION, \
    FIELD_METADATA, FIELD_SPEC


class CVTask:
    """Generates the CVTask manifest"""

    def __init__(self, name):
        """Initializes the CVTask class

            Args:
                name        (str)       --      The name of the CVTask

        """

        self.__name = name
        self.__manifest = {
        FIELD_VERSION: '/'.join([CVTaskConstants.GROUP.value, CVTaskConstants.VERSION.value]),
            FIELD_KIND: CVTaskConstants.KIND.value,
            FIELD_METADATA: {
                FIELD_NAME: self.__name
            },
            FIELD_SPEC: {}
        }

    @property
    def name(self):
        """Return name property

            Returns:
                (str)   --  The name of the CVTask

        """
        return self.__name

    @property
    def manifest(self):
        """Return manifest of a CVTask object

            Returns:
                (dict)   --  The dict of the CVTask obj

        """
        return self.__manifest

    def set_pre_backup_snapshot(self, command_type: str, command: str, args: list[str] = None):
        """Sets the pre backup snapshot command of the task

            Args:
                command_type        (str)   --      The type of the command

                command             (str)   --      The command of the task

                args                (list)  --      THe list of arguments for the command

            Returns:
                None

        """

        self.set_command(CVTaskConstants.FIELD_PRE_BACKUP_SNAPSHOT.value, command_type, command, args)

    def set_post_backup_snapshot(self, command_type: str, command: str, args: list[str] = None):
        """Sets the post backup snapshot command of the task

            Args:
                command_type        (str)   --      The type of the command

                command             (str)   --      The command of the task

                args                (list)  --      THe list of arguments for the command

            Returns:
                None

        """

        self.set_command(CVTaskConstants.FIELD_POST_BACKUP_SNAPSHOT.value, command_type, command, args)

    def set_command(self, field, command_type: str, command: str, args: list[str] = None):
        """Sets the command for the specific pre/post backup field

            Args:
                field               (str)   --      The field of the cvtask to set the command for

                command_type        (str)   --      The type of the command

                command             (str)   --      The command of the task

                args                (list)  --      THe list of arguments for the command

            Returns:
                None

        """

        self.__manifest[FIELD_SPEC][field] = {
            'commandType': command_type,
            'command': command
        }

        if args:
            self.__manifest[FIELD_SPEC][field]['args'] = args

    def create(self, kube_help, namespace):
        """Creates the CVTask resource

            Args:
                kube_help           (obj)       --      The KubernetesHelper object

                namespace           (str)       --      The namespace to deploy the CVTask

            Returns:
                None

        """

        kube_help.create_cv_custom_resource(
            namespace=namespace,
            group=CVTaskConstants.GROUP.value,
            version=CVTaskConstants.VERSION.value,
            plural=CVTaskConstants.PLURAL.value,
            body=self.manifest
        )


class CVTaskSet:
    """Generates the CVTaskSet class"""

    def __init__(self, name):
        """Initializes the CVTaskSet class

            Args:
                name        (str)       --      The name of the CVTaskSet

        """

        self.__name = name
        self.__app_name = None
        self.__app_namespace = None
        self.__label_selectors = None
        self.__manifest = {
            FIELD_VERSION: '/'.join([CVTaskSetConstants.GROUP.value, CVTaskSetConstants.VERSION.value]),
            FIELD_KIND: CVTaskSetConstants.KIND.value,
            FIELD_METADATA: {
                FIELD_NAME: self.__name
            },
            FIELD_SPEC: {
                CVTaskSetConstants.FIELD_TASKS.value: []
            }
        }

    @property
    def name(self):
        """Return name property

            Returns:
                (str)   --  The name of the CVTaskSet

        """
        return self.__name

    @name.setter
    def name(self, value):
        """Sets the name value

            Args:
                value       (str)       --      The name of the CVTaskSet

        """
        self.__manifest[FIELD_METADATA][FIELD_NAME] = value

    @property
    def app_name(self):
        """Returns the AppName

            Returns:
                (str)   --  The AppName of the CVTaskSet

        """
        return self.__app_name

    @app_name.setter
    def app_name(self, value):
        """Sets the AppName value to the manifest

            Args:
                value       (str)   --      The AppName of the CVTaskSet

        """

        if value is None:
            raise Exception('Invalid value for app name')

        self.__app_name = value
        self.__manifest[FIELD_SPEC][CVTaskSetConstants.FIELD_APP_NAME.value] = value

    @property
    def app_namespace(self):
        """Returns the AppNamespace value

            Returns:
                (str)   --  The AppNameSpace of the CVTaskSet

        """
        return self.__app_namespace

    @app_namespace.setter
    def app_namespace(self, value):
        """Sets the AppNameSpace value to the manifest

            Args:
                value       (str)   --      The value for the AppNameSpace property

        """

        if value is None:
            raise Exception('Invalid value for app namespace')

        self.__app_namespace = value
        self.__manifest[FIELD_SPEC][CVTaskSetConstants.FIELD_APP_NAMESPACE.value] = value

    @property
    def label_selectors(self):
        """Returns the label selector value

            Returns:
                (list)   --  The labelSelector of the CVTaskSet

        """
        return self.__label_selectors

    @label_selectors.setter
    def label_selectors(self, value: list[list[str]]):
        """Sets the label selector property

            Args:
                value       (list)      --      The label selector value

        """

        if value is None:
            raise Exception('Invalid value for label selectors')

        self.__label_selectors = value
        self.__manifest[FIELD_SPEC][CVTaskSetConstants.FIELD_LABEL_SELECTORS.value] = value

    @property
    def manifest(self):
        """Return manifest of a CVTaskSet object

            Returns:
                (dict)   --  The CVTaskSet manifest

        """

        return self.__manifest

    def add_task(self, task_name, **kwargs):
        """Adds a task to the CvTaskSet manifest

            Args:
                task_name       (str)   --      The name of the task set

            kwargs:
                task_id         (str)   --      An ID for the tasks set

                task_namespace  (str)   --      The namespace of the task set to deploy to

                container_name  (str)   --      The name of the container to execute tasks on

                execution_level (str)   --      The scope of the task execution

                execution_order (int)   --      The order of execution of the task

                is_disabled     (bool)  --      Status of the task

            Returns:
                None

        """

        task = {
            CVTaskSetConstants.FIELD_CV_TASK_NAME.value: task_name
        }

        task_id = kwargs.get('task_id', None)
        task_namespace = kwargs.get('task_namespace', None)
        container_name = kwargs.get('container_name', None)
        execution_level = kwargs.get('execution_level', None)
        execution_order = kwargs.get('execution_order', None)
        is_disabled = kwargs.get('is_disabled', None)

        if task_id:
            task[CVTaskSetConstants.FIELD_CV_TASK_ID.value] = task_id

        if task_namespace:
            task[CVTaskSetConstants.FIELD_CV_TASK_NAMESPACE.value] = task_namespace

        if container_name:
            task[CVTaskSetConstants.FIELD_CONTAINER_NAME.value] = container_name

        if execution_level:
            task[CVTaskSetConstants.FIELD_EXECUTION_LEVEL.value] = execution_level

        if execution_order:
            task[CVTaskSetConstants.FIELD_EXECUTION_ORDER.value] = execution_order

        if is_disabled:
            task[CVTaskSetConstants.FIELD_IS_DISABLED.value] = is_disabled

        self.__manifest[FIELD_SPEC][CVTaskSetConstants.FIELD_TASKS.value].append(task)

    def create(self, kube_help, namespace):
        """Creates the CVTaskSet resource

            Args:

                kube_help       (obj)       --      The KubernetesHelper object

                namespace       (str)       --      The namespace to deploy the cvtaskset to

            Returns:
                None

        """

        kube_help.create_cv_custom_resource(
            namespace=namespace,
            group=CVTaskSetConstants.GROUP.value,
            version=CVTaskSetConstants.VERSION.value,
            plural=CVTaskSetConstants.PLURAL.value,
            body=self.manifest
        )

    def delete(self, kube_help, namespace):
        """Deletes the CVTaskSet resource

            Args:
                kube_help       (obj)       --      The KubernetesHelper object

                namespace       (str)       --      The namespace to delete the cvtaskset from

            Returns:
                (bool)      --      True if successfully deleted, False otherwise

        """

        try:
            kube_help.delete_cv_custom_resource(
                namespace=namespace,
                group=CVTaskSetConstants.GROUP.value,
                version=CVTaskSetConstants.VERSION.value,
                plural=CVTaskSetConstants.PLURAL.value,
                name=self.name
            )
            return True

        except Exception as e:
            return False
