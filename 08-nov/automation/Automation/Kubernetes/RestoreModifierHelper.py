# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""This file defines the classes and enums to create and interact with Restore Modifier objects on cluster

Classes defined:

    Modifier                --      Class for Modifier spec object
    ModifierAction          --      Enum for Modifier action
    ModifierParameters      --      Enum for Modifier parameters
    RestoreModifier         --      Class for RestoreModifier custom object
    RestoreModifierHelper   --      Restore Modifier Helper class
    Selector                --      Class for Selector spec object
    SelectorCriteria        --      Enum for Selector criteria
    SelectorField           --      Class for Selector field parameter

"""


from enum import Enum

from AutomationUtils import logger
from Kubernetes.constants import RestoreModifierConstants, FIELD_NAME, FIELD_NAMESPACE, FIELD_KIND, FIELD_VERSION, \
    FIELD_METADATA, FIELD_SPEC, FIELD_SELECTORS, FIELD_MODIFIERS, FIELD_LABELS, AutomationLabels
from Kubernetes.decorators import DebugSkip
from Kubernetes.exceptions import KubernetesException


class ModifierAction(Enum):
    """Enum for Modifier action values"""

    ADD = "Add"
    DELETE = "Delete"
    MODIFY = "Modify"


class ModifierParameters(Enum):
    """Enum for Modifier parameter values"""

    EXACT = "Exact"
    CONTAINS = "Contains"


class SelectorCriteria(Enum):
    """Enum for Selector criteria values"""

    CONTAINS = "Contains"
    NOTCONTAINS = "NotContains"
    REGEX = "Regex"


class SelectorField:
    """Class for specified field values of selectors spec"""

    def __init__(self, path: str = None, value: str = None, exact: bool = None, criteria: SelectorCriteria = None):
        """Initialize class variables

            Args:

                path            (str)   :   The field.path value in selectors[index].field

                value           (str)   :   The field.value value in selectors[index].field

                exact           (bool)  :   The field.exact value in selectors[index].field

                criteria        (SelectorCriteria)  :   The field.criteria value in selectors[index].field

        """
        self.__path = path
        self.__value = value
        self.__exact = exact
        self.__criteria = criteria
        self.__manifest = {}

    @property
    def manifest(self):
        """Return a dictionary with manifest of 'field' value
        """

        self.__manifest[RestoreModifierConstants.SELECTOR_FIELD_PATH.value] = self.__path
        self.__manifest[RestoreModifierConstants.SELECTOR_FIELD_VALUE.value] = self.__value
        self.__manifest[RestoreModifierConstants.SELECTOR_FIELD_EXACT.value] = self.__exact
        self.__manifest[RestoreModifierConstants.SELECTOR_FIELD_CRITERIA.value] = self.__criteria.value

        return self.__manifest


class Selector:
    """Class for specified values of selector spec"""

    def __init__(self, selector_id: str, name: str = None, namespace: str = None, kind: str = None,
                 labels: dict = None, field: SelectorField = None):
        """Initialize the class variables

            Args:

                selector_id         (str)   :   Value for selector[index].id

                name                (str)   :   Value for selector[index].name

                namespace           (str)   :   Value for selector[index].namespace

                kind                (str)   :   Value for selector[index].kind

                labels              (dict)  :   Value for selector[index].labels

                field               (SelectorField)     :   Value for selector[index].field
        """
        self.__id = selector_id
        self.__name = name
        self.__namespace = namespace
        self.__kind = kind
        self.__labels = labels
        self.__field = field
        self.__manifest = {}

        if not (self.__name or self.__namespace or self.__kind or self.__labels or self.__field):
            raise KubernetesException('RestoreModifierOperations', '101')

    @property
    def selector_id(self):
        """Return selector_id property"""
        return self.__id

    @property
    def manifest(self):
        """Return a dictionary with manifest of 'selectors' spec
        """

        self.__manifest["id"] = self.__id

        if self.__name:
            self.__manifest[RestoreModifierConstants.SELECTOR_NAME.value] = self.__name
        if self.__namespace:
            self.__manifest[RestoreModifierConstants.SELECTOR_NAMESPACE.value] = self.__namespace
        if self.__kind:
            self.__manifest[RestoreModifierConstants.SELECTOR_KIND.value] = self.__kind
        if self.__labels:
            self.__manifest[RestoreModifierConstants.SELECTOR_LABELS.value] = self.__labels
        if self.__field:
            self.__manifest[RestoreModifierConstants.SELECTOR_FIELD.value] = self.__field.manifest

        return self.__manifest


class Modifier:
    """Class for specified values of modifier spec"""

    def __init__(self, selector_id: str, action: ModifierAction, path=None, value=None,
                 new_value=None, parameters: ModifierParameters = None):
        """Initialize class variables

            Args:

                selector_id         (str)   :   Value of modifiers[index].selectorId

                action              (ModifierAction)   :   Value of modifiers[index].action

                path                (str/list/dict)     :   Value of modifiers[index].path

                value               (obj)   :   Value of modifiers[index].value

                new_value           (obj)   :   Value of modifiers[index].newValue

                parameters          (ModifierParameters)    :   Value of modifiers[index].parameters

        """

        self.__selector_id = selector_id
        self.__action = action
        self.__path = path
        self.__value = value
        self.__new_value = new_value
        self.__parameters = parameters
        self.__manifest = {}

        if self.__action == ModifierAction.ADD:
            if not self.__path:
                raise KubernetesException(
                    'RestoreModifierOperations', '102', 'Path is a required field for Add action'
                )

            if self.__value is None:
                raise KubernetesException(
                    'RestoreModifierOperations', '102', 'Value is a required field for Add action'
                )

        elif self.__action == ModifierAction.DELETE:
            if not self.__path:
                raise KubernetesException(
                    'RestoreModifierOperations', '102', 'Path is a required field for Delete action'
                )

        elif self.__action == ModifierAction.MODIFY:
            if not self.__path:
                raise KubernetesException(
                    'RestoreModifierOperations', '102', 'Path is a required field for Modify action'
                )

            if self.__value is None:
                raise KubernetesException(
                    'RestoreModifierOperations', '102', 'Value is a required field for Modify action'
                )

            if self.__new_value is None:
                raise KubernetesException(
                    'RestoreModifierOperations', '102', 'newValue is a required field for Modify action'
                )

        else:
            raise KubernetesException(
                'RestoreModifierOperations', '102', 'Invalid action value for modifier'
            )

    @property
    def selector_id(self):
        """Return selector_id property"""
        return self.__selector_id

    @property
    def manifest(self):
        """Return the manifest for modifier spec"""

        self.__manifest[RestoreModifierConstants.MODIFIER_SELECTOR_ID.value] = self.__selector_id
        self.__manifest[RestoreModifierConstants.MODIFIER_ACTION.value] = self.__action.value
        self.__manifest[RestoreModifierConstants.MODIFIER_PATH.value] = self.__path

        if self.__action == ModifierAction.ADD:
            self.__manifest[RestoreModifierConstants.MODIFIER_VALUE.value] = self.__value

        if self.__action == ModifierAction.MODIFY:
            self.__manifest[RestoreModifierConstants.MODIFIER_VALUE.value] = self.__value
            self.__manifest[RestoreModifierConstants.MODIFIER_NEW_VALUE.value] = self.__new_value

            if self.__parameters:
                self.__manifest[RestoreModifierConstants.MODIFIER_PARAMETERS.value] = self.__parameters.value

        return self.__manifest


class RestoreModifier:
    """Class for specified values of a restore modifier object"""

    def __init__(self, name, selectors: list[Selector], modifiers: list[Modifier]):
        """Initialize class variables

            Args:

                name        (str)   :   Name of the RestoreModifier object

                selectors   (list)  :   List of Selector objects

                modifiers   (list)  :   List of Modifier objects

        """
        self.__name: str = name
        self.__selectors: list[Selector] = selectors
        self.__modifiers: list[Modifier] = modifiers
        self.__manifest = {
            FIELD_VERSION: '/'.join([RestoreModifierConstants.GROUP.value, RestoreModifierConstants.VERSION.value]),
            FIELD_KIND: RestoreModifierConstants.KIND.value,
            FIELD_METADATA: {
                FIELD_NAME: self.__name,
                FIELD_NAMESPACE: RestoreModifierConstants.NAMESPACE.value,
                FIELD_LABELS: {
                    AutomationLabels.AUTOMATION_LABEL.value: ''
                }

            },
            FIELD_SPEC: {
                FIELD_SELECTORS: [],
                FIELD_MODIFIERS: []
            }
        }

        if not self.__selectors:
            raise KubernetesException(
                'RestoreModifierOperations', '103', 'Selector field is missing from RestoreModifier'
            )
        if not self.__modifiers:
            raise KubernetesException(
                'RestoreModifierOperations', '103', 'Modifier field is missing from RestoreModifier'
            )

    @property
    def name(self):
        """Return name property"""
        return self.__name

    @property
    def manifest(self):
        """Return manifest of a RestoreModifier object"""

        for selector_obj in self.__selectors:
            if selector_obj.manifest not in self.__manifest[FIELD_SPEC][FIELD_SELECTORS]:
                self.__manifest[FIELD_SPEC][FIELD_SELECTORS].append(selector_obj.manifest)
        for modifier_obj in self.__modifiers:
            if modifier_obj.manifest not in self.__manifest[FIELD_SPEC][FIELD_MODIFIERS]:
                self.__manifest[FIELD_SPEC][FIELD_MODIFIERS].append(modifier_obj.manifest)

        return self.__manifest


class RestoreModifierHelper:
    """Helper class for RestoreModifier functionality"""

    def __init__(self):
        """Initialize class variables"""
        self.__selectors: list[Selector] = []
        self.__modifiers: list[Modifier] = []
        self.__restore_modifiers: list[RestoreModifier] = []
        self.log = logger.get_log()

    def add_selector(self, selector: Selector):
        """Add a Selector object to selector list"""

        if selector not in self.__selectors:
            self.__selectors.append(selector)

    def add_modifier(self, modifier: Modifier):
        """Add a Modifier object to modifiers list"""

        if modifier not in self.__modifiers:
            self.__modifiers.append(modifier)

    def get_restore_modifier_json(self, kubehelper, name):
        """
        Returns a JSON of restore modifier object
        """

        modifier_json = kubehelper.get_custom_object(
            group=RestoreModifierConstants.GROUP.value,
            version=RestoreModifierConstants.VERSION.value,
            namespace=RestoreModifierConstants.NAMESPACE.value,
            plural=RestoreModifierConstants.PLURAL.value,
            name=name
        )
        self.log.info(f"Fetched JSON for Modifier : [{name}]")
        return modifier_json

    def generate_selector(self, selector_id: str, **kwargs):
        """Generate a Selector object for RestoreModifier

            Args:

                selector_id         (str)   :   ID of the selector

            Kwargs:

                name                (str)   :   Name field of selector

                namespace           (str)   :   Namespace field of selector

                kind                (str)   :   Kind field of selector

                labels              (str)   :   Labels field of selector

                path                (str)   :   Path field of a field selector

                value               (str)   :   Value field of a field selector

                exact               (bool)  :   Exact field of a field selector

                criteria            (SelectorField) :   Selector value of a field selector

            Returns:

                 Json manifest of the generated object

        """

        name = kwargs.get("name", None)
        namespace = kwargs.get("namespace", None)
        kind = kwargs.get("kind", None)
        labels = kwargs.get("labels", None)
        path = kwargs.get("path", None)
        value = kwargs.get("value", None)
        exact = kwargs.get("exact", None)
        criteria = kwargs.get("criteria", None)
        selector_field = None

        if path and value:
            selector_field = SelectorField(path=path, value=value, exact=exact, criteria=criteria)

        selector = Selector(
            selector_id=selector_id, name=name, namespace=namespace, kind=kind, labels=labels, field=selector_field
        )

        self.add_selector(selector)
        self.log.info(f"Created Selector object and added to list with manifest : [{selector.manifest}]")

        return selector.manifest

    def generate_field_selector(self, selector_id: str, path: str, value: str, exact: bool, criteria: str):
        """Generate a Selector with field specs

            Args:

                selector_id         (str)   :   ID of the selector

                path                (str)   :   Path value of the selector field

                value               (str)   :   Value field of the selector field

                exact               (bool)  :   Exact value of the selector field

                criteria            (str)   :   Criteria value of selector field

            Returns:

                 Json manifest of the generated object

        """
        if criteria == SelectorCriteria.CONTAINS.value:
            criteria = SelectorCriteria.CONTAINS
        elif criteria == SelectorCriteria.NOTCONTAINS.value:
            criteria = SelectorCriteria.NOTCONTAINS
        elif criteria == SelectorCriteria.REGEX.value:
            criteria = SelectorCriteria.REGEX
        else:
            return KubernetesException('RestoreModifierOperations', '104', 'Invalid criteria value')

        self.log.info("Generating a Selector object with 'field' parameter")
        return self.generate_selector(
            selector_id=selector_id,
            path=path,
            value=value,
            exact=exact,
            criteria=criteria
        )

    def generate_modifier(self, selector_id: str, action: ModifierAction, **kwargs):
        """Generate a modifier object

            Args:

                selector_id         (str)   :   ID of the selector

                action              (ModifierAction)   :   Action value for the modifier

            Kwargs:

                path                (str)   :   Path value of the modifier

                value               (obj)     :   Value of the modifier

                new_value           (obj)   :   New value for the value field

                parameters          (ModifierParameters)   :   Additional parameter values

            Returns:

                 Json manifest of the generated object

        """
        path = kwargs.get("path", None)
        value = kwargs.get("value", None)
        new_value = kwargs.get("new_value", None)
        parameters = kwargs.get("parameters", None)

        modifier = Modifier(
            selector_id=selector_id, action=action, path=path, value=value, new_value=new_value, parameters=parameters
        )

        self.add_modifier(modifier)
        self.log.info(f"Created Modifier object and added to list with manifest : [{modifier.manifest}]")

        return modifier.manifest

    def generate_add_modifier(self, selector_id: str, path: str, value):
        """Generate a modifier object with Add action

            Args:

                selector_id         (str)   :   ID of the selector

                path                (str)   :   Path value of the modifier

                value               (obj)   :   Value of the modifier

            Returns:

                 Json manifest of the generated object

        """
        self.log.info(f"Generating a Modifier object with {ModifierAction.ADD.value} action")
        return self.generate_modifier(
            selector_id=selector_id,
            action=ModifierAction.ADD,
            path=path,
            value=value
        )

    def generate_delete_modifier(self, selector_id: str, path: str):
        """Generate a modifier object with Delete action

            Args:

                selector_id         (str)   :   ID of the selector

                path                (str)   :   Path value of the modifier

            Returns:

                 Json manifest of the generated object

        """
        self.log.info(f"Generating a Modifier object with {ModifierAction.DELETE.value} action")
        return self.generate_modifier(
            selector_id=selector_id,
            action=ModifierAction.DELETE,
            path=path
        )

    def generate_modify_modifier(self, selector_id: str, path: str, value, new_value, parameters: str = None):
        """Generate a modifier object with Modify action

            Args:

                selector_id         (str)   :   ID of the selector

                path                (str)   :   Path value of the modifier

                value               (obj)   :   Value of the modifier

                new_value           (obj)   :   New value for the value field

                parameters          (str)   :   Additional parameter values

            Returns:

                 Json manifest of the generated object

        """

        if parameters == ModifierParameters.EXACT.value:
            parameters_enum = ModifierParameters.EXACT
        elif parameters == ModifierParameters.CONTAINS.value:
            parameters_enum = ModifierParameters.CONTAINS
        else:
            raise KubernetesException("RestoreModifierOperations", "103", "Invalid value for parameter field")

        self.log.info(f"Generating a Modifier object with {ModifierAction.MODIFY.value} action")
        return self.generate_modifier(
            selector_id=selector_id,
            action=ModifierAction.MODIFY,
            path=path,
            value=value,
            new_value=new_value,
            parameters=parameters_enum
        )

    def generate_restore_modifier(self, name: str, selectors: list[Selector] = None, modifiers: list[Modifier] = None):
        """Generate a modifier object with Add action

            Args:

                name                (str)   :   ID of the selector

                selectors           (list)  :   List of Selector objects. Use class variable if not passed

                modifiers           (list)  :   List of Modifier objects. Use class variable if not passed

            Returns:

                 Json manifest of the generated object

        """

        selectors = selectors or self.__selectors
        modifiers = modifiers or self.__modifiers

        sym_diff = {sel.selector_id for sel in selectors} ^ {mod.selector_id for mod in modifiers}
        if sym_diff:
            self.log.warning(f"Some selectorIds don't have corresponding selector or modifier : [{sym_diff}]")

        restore_modifier = RestoreModifier(name=name, selectors=selectors, modifiers=modifiers)
        self.__restore_modifiers.append(restore_modifier)

        return restore_modifier.manifest

    def create_restore_modifier_crs(self, kubernetes_helper, restore_modifiers: list[RestoreModifier] = None):
        """Create RestoreModifier CR on the cluster

            Args:

                kubernetes_helper       (KubernetesHelper)  :   Object of an initialized KubernetesHelper module

                restore_modifiers       (list)              :   List of RestoreModifier objects. Use class variables if
                                                                not passed
        """
        restore_modifiers = restore_modifiers or self.__restore_modifiers

        if not restore_modifiers:
            raise KubernetesException('RestoreModifierOperations', '103', 'No RestoreModifier object to create')

        for restore_modifier in restore_modifiers:
            self.log.info(
                f"Creating {RestoreModifierConstants.KIND.value} with name [{restore_modifier.name}] " +
                f"with manifest [{restore_modifier.manifest}]"
            )
            kubernetes_helper.create_cv_custom_resource(
                namespace=RestoreModifierConstants.NAMESPACE.value,
                group=RestoreModifierConstants.GROUP.value,
                version=RestoreModifierConstants.VERSION.value,
                plural=RestoreModifierConstants.PLURAL.value,
                body=restore_modifier.manifest
            )
            self.log.info(
                f"Created {RestoreModifierConstants.KIND.value} with name [{restore_modifier.name}]"
            )

    @DebugSkip()
    def delete_restore_modifier_crs(self, kubernetes_helper, restore_modifiers: list[RestoreModifier] = None):
        """Delete RestoreModifier CR on the cluster

            Args:

                kubernetes_helper       (KubernetesHelper)  :   Object of an initialized KubernetesHelper module

                restore_modifiers       (list)              :   List of RestoreModifier objects. Use class variables if
                                                                not passed
        """

        restore_modifiers = restore_modifiers or self.__restore_modifiers
        for restore_modifier in restore_modifiers:
            self.log.info(
                f"Deleting {RestoreModifierConstants.KIND.value} with name [{restore_modifier.name}] " +
                f"with manifest [{restore_modifier.manifest}]"
            )
            kubernetes_helper.delete_cv_custom_resource(
                name=restore_modifier.name,
                namespace=RestoreModifierConstants.NAMESPACE.value,
                group=RestoreModifierConstants.GROUP.value,
                version=RestoreModifierConstants.VERSION.value,
                plural=RestoreModifierConstants.PLURAL.value
            )
            self.log.info(
                f"Deleted {RestoreModifierConstants.KIND.value} with name [{restore_modifier.name}]"
            )

    def clear_all_selectors(self):
        """Clear all selectors from selector list
        """
        self.__selectors.clear()

    def clear_all_modifiers(self):
        """Clear all modifiers from modifiers list
        """
        self.__modifiers.clear()

    def clear_all_restore_modifiers(self):
        """Clear all RestoreModifiers from the list
        """
        self.__restore_modifiers.clear()
