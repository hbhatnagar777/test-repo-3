# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
 This module used to do common selenium element operation
"""
from time import sleep
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from AutomationUtils import logger
from Web.Common.page_object import WebAction
from Web.Common.exceptions import CVWebAutomationException

log_ = logger.get_log()

def check_title(driver, title, match=True):
    """
    check driver title and report error if title not match
    Args:
        title    string    Page title string
        match    boolean/string    True(default) exact match
                                    include include the string
    Return:
        titlecheck boolean True, title match; False, title not match
    """
    if match:
        if driver.title == title:
            titlecheck = True
        else:
            titlecheck = False
    elif match == "include":
        if driver.title.find(title) > -1:
            titlecheck = True
        else:
            titlecheck = False
    return titlecheck

def check_element(element, type_, value, **kwargs):
    """
    fine the element based on input
    Args:
        element    obj    selenium element to process
        type_     string    obj type to search, it should below to following type
                            xpath, tag, class, id, linktext
        value    string    the string value to looking
        **kwargs    dict    additional attribute to check
                            attribute    looking the attribute name and value
                            text         looking the element text
    Return:
        returnvalue obj/False    Fasle, no object is found
                                obj    matched element
    Exception:
        306    element type is not valid
        205    multiple result found
    """
    if type_ == "xpath":
        results = element.find_elements(By.XPATH, value)
    elif type_ == "tag":
        results = element.find_elements(By.TAG_NAME, value)
    elif type_ == "class":
        results = element.find_elements(By.CLASS_NAME, value)
    elif type_ == "id":
        results = element.find_elements(By.ID, value)
    elif type_ == "linktext":
        results = element.find_elements(By.LINK_TEXT, value)
    else:
        raise CVWebAutomationException(f"element type is not valid, {type_}")

    log_.debug(f"find total {len(results)} results")

    if len(results) == 0:
        log_.debug("no element found")
        returnvalue = False
    elif len(results) == 1:
        log_.debug("only one element found")
        returnvalue = results[0]
    elif kwargs:
        log_.debug(f"narrow down the result with additional value {kwargs}")
        returnvalue = False
        if kwargs.get("attribute"):
            attributes_ = kwargs["attribute"]
            attributename = list(attributes_.keys())
            if len(attributename) == 1:
                attributename = attributename[0]
                attributevalue = attributes_[attributename]
                log_.debug(f"will check {attributename} with vaule {attributevalue}")
                for _ in results:
                    if _.get_attribute(attributename) == attributevalue:
                        returnvalue = _
                        break
        elif len(kwargs.keys()) == 1:
            keyname = list(kwargs.keys())[0]
            value = kwargs[keyname]
            log_.debug(f" will check {keyname} with value {value}")
            for _ in results:
                if keyname == 'text':
                    checkkey = _.text
                else:
                    checkkey = _.get_attribute(keyname)
                if checkkey == value:
                    returnvalue = _
                    break
    else:
        count = 0
        for _ in results:
            if _.text != "":
                count += 1
                returnvalue = _
        log_.debug(f"found {count} no empty result")
        if count == 0:
            returnvalue = False
            log_.debug(f"all {len(results)} entries have empty result")
        else:
            raise CVWebAutomationException(f"check element find more elements,\
                                         total {len(results)}")
    return returnvalue

def check_element_text(element, type_, value, text):
    """
    check element text string, simple alias of check_element
    Args:
        reference to check_element
    Return:
        refredence to check_element
    """
    return check_element(element, type_, value, ** {"text" : text})

def check_element_attribute(element, type_, value, attributes):
    """
    check element attributes, simple alias of check_element
    Args:
        reference to check_element
    Return:
        refredence to ch
    """
    return check_element(element, type_, value, **{"attribute" : attributes})

def check_link_text(element, value):
    """
    check link by string, simple alias of check_element
    Args:
        reference to check_element
    Return:
        refredence to check_element
    """
    return check_element(element, "tag", "a", **{"text" : value})

def check_id(element, idname):
    """
    check element by id, simple alias of check_element
    Args:
        reference to check_element
    Return:
        refredence to check_element
    """
    return check_element(element, "id", idname)

def check_parent(element):
    """
    get parent obejct
    Args:
        element    obj    object in selenium driver
    """
    return check_element(element, "xpath", "..")

def check_dialog(element):
    """
    check if a dialog windows popup
    Args:
        element obj    object in selenium driver
    """
    return check_element(element, "tag", "div",
                         **{"attribute" : {
                             "uib-modal-window" : "modal-window"}})

def check_span_text(element, text):
    """
    check span by text, simple alias of check_element
    Args:
        reference to check_element
    Return:
        refredence to check_element
    """
    return check_element(element, "tag", "span",
                         ** {"text" : text})

def check_span_link(element, text):
    """
    check span by link text, simple alias of check_element
    Args:
        reference to check_element
    Return:
        refredence to check_element
    """
    span_ = check_element(element, "tag", "span", **{"text" : text})
    link = check_parent(span_)
    return link

def check_rows(element):
    """
    check valid row in the element
    Args:
        element    obj    parent obj
    Returns:
        goodrows    list good entry with role==row
    """
    divs_ = element.find_elements(By.TAG_NAME, "div")
    goodrows = []
    for _ in divs_:
        if _.get_attribute("role") == "row":
            if _.text.strip() != "":
                goodrows.append(_)
    return goodrows

def check_dchildren(element, pc =None, skip=True):
    """
    check direct children elements
    """
    cc = element.find_elements(By.XPATH, "./*")
    if len(cc) ==1:
        cc = cc[0]
#        log_.debug("only found one child item under this element")
        if skip:
#            log_.debug("want to check next children level to skip one entry level")
            cc = check_dchildren(cc, skip=True)

    if isinstance(cc, list) and isinstance(pc, int):
#        log_.debug(f"pick one child {pc} from {cc}")
        cc = cc[pc]
    return cc

@WebAction()
def select_button_text(element, value):
    """
    check button by text, simple alias of check_element
    Args:
        reference to check_element
    Return:
        refredence to check_element
    """
    return check_element(element, "tag", "button", **{"text" : value}).click()

@WebAction()
def select_multi(element, name, values):
    """
    process multiple selection element, like dropdown operation, check
    Args:
        element    obj    parent object
        name    string    name attribute text
        values    list    choiced values
    """
    if isinstance(name, dict):

        log_.debug(f"check attribute {name}")
        keyname = list(name.keys())[0]
        keyvalue = name[keyname]
        element_ = check_element(element, "tag", "isteven-multi-select",
                                 **{"attribute" : {
                                     keyname : keyvalue}})
    else:
        log_.debug(f"just find the element based on the name {name}")
        element_ = check_element(element, "tag", "isteven-multi-select",
                                 **{"attribute" : {"name" : name}})

    if isinstance(values, str):
        values = [values]
    # check the options is opened or not
    options_ = element_.text.split("\n")
    log_.debug(f"here are {len(options_)} options to pick:{options_}")
    if len(options_) == 1:
        try:
            element_.click()
            log_.debug("click the mulitple selection")
        except:
            check_element(element_,"tag","button").click()
            log_.debug("open the mutli selection")
        sleep(5)
    items = element_.find_elements(By.CLASS_NAME, "multiSelectItem")
    items_text = [item.text for item in items]
    log_.debug(f"found total {len(items)} options. here is the list {items_text}")

    for _ in items:
        # plan view may have two lines. have to remove the retention information
        # AD\nRPO: 1 day(s) | Copies: 2(Primary: undefined) | Entities: 5
        item_ = _.text.split("\n")
        if len(item_) >1:
            item_text = item_[0].strip()
        else:
            item_text = _.text
        if item_text in values:
            _.click()
            log_.debug(f"find the entry {item_text}, choice it")
    sleep(3)
    options_ = element_.text.split("\n")
    log_.debug(f"here are {len(options_)} options to pick:{options_}")
    if len(options_) == 1:
        log_.debug("select window already closed")
        sleep(2)
    else:
        log_.debug("close selection window")
        check_element(element_,"tag","button").click()
        log_.debug("selection window should be closed")

@WebAction()
def select_single(element, value):
    """
    process multiple selection element, like dropdown operation, check
    Args:
        element    (obj):    parent object
        name    (string):    name attribute text
        values    (list):    choiced values
    """
    values = [_.strip() for _ in element.text.split("\n")]
    log_.debug(f"here is the choice values from select {values}")
    if len(values) == 1:
        element.click()
        log_.debug("click the choice and wait the page get loaded")
        sleep(5)
        values = [_.strip() for _ in element.text.split("\n")]
        log_.debug(f"here is the opened value after click {values}")

    if not value in values:
        raise CVWebAutomationException(f"The element is  {element.text} and the value is {value}")

    if element.find_elements(By.TAG_NAME, "option"):
        elements = element.find_elements(By.TAG_NAME, "option")
        log_.debug(f"find {len(elements)} options, will continue")
        for _ in elements:
            if _.text == value:
                log_.debug(f"find the element with text same as {value},click it")
                _.click()
                break
    else:
        elements = element.find_elements(By.TAG_NAME, "input")
        log_.debug(f"find {len(elements)} input afters p22, will continue")
        check_element(element, "tag", "div",
                      **{"attribute" : {"title" : value}}).click()
    log_.debug("single value is picked, will continue")
    element.click()

@WebAction()
def select_content(element, value):
    """
    select content from the add content windows
    Args:
        element    (obj) :     web element to operation
        value    (string):    select content value

    """
    diag_ = check_dialog(element)
    content_title = check_element(diag_, "class", "setup-title").text
    log_.debug(f"content title is {content_title}")
    content_root = check_element(diag_, "class", "setup-content")
    if len(content_root.text.split("\n")) >1:
        log_.debug(f" there are more than 1 instance list here: {content_root.text}")
        for _ in content_root.find_elements(By.CLASS_NAME,"browse-item"):
            if _.text.startswith("DC="):
                content_ = _
                log_.debug(f"found the correct ad instance {_.text}")
                break
    else:
        log_.debug("only one instance there")
        content_ = content_root
    content_root_text = content_.text
    log_.debug(f"content root {content_root} has  name {content_root_text}")
    log_.info(f"select the following {value}")
    # only root is avaialble, do more check
    valuepath = value.split(",")
    log_.info(f"there are {len(valuepath)} level browse, {valuepath}")
    level = 0
    for level_value in valuepath:
        check_element(content_,"tag", "button").click()
        sleep(15)
        children_items = content_.find_elements(By.CLASS_NAME, "browse-item")
        childpick = None
        log_.debug(f"find the {len(children_items)} child entry: {[i.text for i in children_items]}")
        if children_items[-1].text == "More":
            log_.debug("there are more items on left panel, need expand more")
            children_items[-1].click()
            sleep(5)
            log_.debug("all items should be loaded")
            children_items = content_.find_elements(By.CLASS_NAME, "browse-item")
            log_.debug(f"click more and find the {len(children_items)} child entry:\
                     {[i.text for i in children_items]}")
        for _ in children_items:
            if _.text == level_value:
                childpick = _
                level +=1
                log_.debug(f"find match {level_value} item {childpick}")
                break
        if childpick:
            if level < len(valuepath):
                content_ = childpick
            else:
                childpick.find_element(By.TAG_NAME, "span").click()
                log_.debug(f"the {level_value} is picked")
                sleep(5)
                check_element(diag_, "tag", "button", **{"text":"Add"}).click()
                log_.info("the content is added")

@WebAction()
def select_form_submit(element):
    """ 
    submit a form by click the submit button
    Args:
        element    (obj) :     web element to operation
    """
    check_element(element,"tag","input",**{"type": "submit"}).click()

@WebAction()
def dialog_window(element, ops):
    """
    operation in diag windows
    Args:
        element    (obj):    parent obj
        ops    (list):   page operation defination. refrence page_ops
    """
    diag_ = check_dialog(element)
    log_.debug('start to process the options')
    page_ops(diag_, ops)

@WebAction()
def right_click(driver, element):
    """
    do riight click on the element
    Args:
        driver    (obj):    selenium browser driver
        element    (obj):    object to click right menu
    """
    actionchains = ActionChains(driver)
    actionchains.context_click(element).perform()

@WebAction()
def element_input(element, field, type_, value):
    """
    process input element
    Args:
        element   (obj):    parent element to check
        field    (string):    element name text
        type_    (string):    type of opration, choice from
                            "input", "checkone"
        value    (string):    input value to send
    """
    if type_ == "input":
        pick_element = check_element(element, "tag", "input",
                                     **{"attribute" : {"name" : field}})
        pick_element.clear()
        pick_element.send_keys(value)
    elif type_ == "checkone":

        pick_element = check_element(element, "tag", "isteven-multi-select",
                                     **{'attribute' : {"id" : field}})
        try:
            pick_element.click().perform()
        except:
            sleep(1)
        valuescheck = pick_element.find_elements(By.XPATH, "./span/div/div/div/div/label/span")
        for valuecheck in valuescheck:
            if valuecheck.text == value:
                valuecheck.click()
                break

@WebAction()
def dropdown_pick(element, value, **kwargs):
    """
    pick value from dropdown list
    Args:
        element    (obj):   parent element to operate
        value    (string):    the item we want to pick
        kwargs    (Dict):    addtiional obj to pick the element
                            mppper     dict     map the text to the element value
                            range    list    allow range,
                                    user in different user case,
                                    each user may see different values
    Exception:
        101    value is not in the choice range
    """
    if len(element.text.split("\n")) == 1:
        element.click()
    if kwargs.get("mapper"):
        link_mapper = kwargs['mapper']
    else:
        link_mapper = {value: value}

    if kwargs.get("range"):
        choice_range = kwargs['range']
    else:
        choice_range = list(link_mapper.keys())

    if value in choice_range:
        link_ = check_link_text(element, link_mapper[value])
        link_.click()
    else:
        raise CVWebAutomationException(f"{value} is not in the {choice_range}")

@WebAction()
def page_ops(element, ops):
    """
    process multiple operation in single page, operation is defined in list
    like create app.
    Args:
        element    (obj):    parent element to operate
        ops    (list):     list of indivdiaul operation
                        each opreation is a dict,
                        eargs    dict    additional argument required to find element
                        etype    used in check_element, reference check_element
                        evalue    used in check_element, reference check_element
                        action    string    choice from the below:
                                "click"    click the button or link
                                "check"    check element in checkbox
                        input    string    this is input box to send keys
                        select     string    select item in select element
    """
    log_.debug(f"here is the page operations input: {ops}")
    for _ in ops:
        if "sleep" in _:
            log_.debug("wait for soem time")
            sleep(_['sleep'])
        else:
            log_.debug(f"start to process {_}")
            if "eargs" in _:
                pick_element = check_element(element, _['etype'], _['evalue'], **_['eargs'])
            elif "etype" not in _:
                pick_element = element
            else:
                pick_element = check_element(element, _['etype'], _['evalue'])

            if "parent" in _:
                pick_element = check_parent(pick_element)

            if "clear" in _:
                pick_element.clear()

            log_.debug(f'process the {pick_element} with action')
            if "action" in _:
                if _['action'] == "click":
                    pick_element.click()
                    sleep(2)
                if _['action'] == "check":
                    if not pick_element.is_selected:
                        _['driver'].execute_script("arguments[0].click()", pick_element)
                    sleep(3)
            elif "input" in _:
                pick_element.send_keys(_['input'])
                sleep(1)
            elif "select" in _:
                select_single(pick_element, _['select'])
            elif "button" in _:
                select_button_text(pick_element, _['button'])
            elif "selectmulti" in _:
                select_multi(pick_element, *_['selectmulti'])