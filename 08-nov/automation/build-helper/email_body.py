# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ------------------------------------------------------------------------------

from abc import ABC
from xml.etree import cElementTree as ETree

UPDATE_CENTER_URL = "https://updatecenter.commvault.com/Form.aspx?BuildID={}&FormID={}"
TEMPLATE = """<!DOCTYPE html>
<html>

<head>
    <meta charset="utf-8"/>
    <title>Title</title>

    <style>
    #tbl{ width:30%; border: 2px solid black;padding: 8px; font-size:15px; font-family: Georgia;}
    #td1{background-color: #b3c6ff; font-family: Georgia;}
    #td2{border: 1px solid #b3c6ff; font-family: Georgia;}
    </style>
</head>


<body>
    <div id="segment">

    </div>
<br></br>
Thanks,<br></br>
Core Automation Team
</body>
</html>"""



def construct_email_body(pylint_outputs, form):
    """Constructs email body with the help of pylint output objects"""
    color_dict = {
        2: "#ff6666",
        3: "#ff944d",
        4: "#5cd65c",
        5: "#5cd65c"
    }
    html = ETree.fromstring(TEMPLATE)
    body = html.find('.//div[@id="segment"]')

    table = SuccessTable(body, form)
    table.construct_table()

    ETree.SubElement(body, "br")

    ordered_list = ETree.SubElement(body, "ol")

    for output in pylint_outputs:
        list_ = ETree.SubElement(ordered_list, "li")
        h3 = ETree.SubElement(list_, "h3")
        h3.text = output.label
        h3.set("font-family", "Georgia")
        h3.set("color", "#b30000")
        ETree.SubElement(ordered_list, "br")

        table = ETree.SubElement(ordered_list, "table")
        table.set("id", "tbl")

        table_row = ETree.SubElement(table, "tr")
        table_data = ETree.SubElement(table_row, "td")
        table_data.text = "Pylint Score"
        table_data.set("id", "td1")
        table_data = ETree.SubElement(table_row, "td")
        table_data.text = f"{output.score:.2f}/10"
        table_data.set("id", "td2")
        table_data.set("style", f"background-color:{color_dict.get(int(output.score // 2), '#ff6666')}")

        for key, value in output.message.items():
            table_row = ETree.SubElement(table, "tr")
            table_data = ETree.SubElement(table_row, "td")
            table_data.text = str(key).capitalize()
            table_data.set("id", "td1")
            table_data = ETree.SubElement(table_row, "td")
            table_data.text = str(value)
            table_data.set("id", "td2")
            if key == 'error':
                if value > 0:
                    table_data.set("style", "background-color:#ff6666")
                else:
                    table_data.set("style", "background-color:#5cd65c")
        unordered_list = ETree.SubElement(ordered_list, "ul")

        for error in output.get_error_lines():
            list_ = ETree.SubElement(unordered_list, "li")
            list_.text = error
        ETree.SubElement(ordered_list, "br")

        for fatal in output.get_fatal_lines():
            list_ = ETree.SubElement(unordered_list, "li")
            list_.text = fatal
        ETree.SubElement(ordered_list, "br")
        '''
        h4 = ETree.SubElement(ordered_list, "h4")
        anchor = ETree.SubElement(h4, "a")
        anchor.text = f"Pylint Output file : {output.label}"
        anchor.set("href", output.path)'''

        ETree.SubElement(ordered_list, "br")

    return ETree.tostring(html, encoding='unicode', method='html')


def construct_failure_message(message, form):
    """Constructs failure message"""
    html = ETree.fromstring(TEMPLATE)
    body = html.find('.//div[@id="segment"]')

    paragraph = ETree.SubElement(body, "p")
    paragraph.text = "Pylint execution encountered the following problem:"

    ETree.SubElement(body, "br")

    table = ExceptionTable(body, form, message)
    table.construct_table()

    return ETree.tostring(html, encoding='unicode', method='html')


class Table(ABC):

    def __init__(self, body, form):
        self.body = body
        self.table = ETree.SubElement(self.body, "table")
        self.form = form

    def construct_table(self):
        raise NotImplementedError


class SuccessTable(Table):

    def construct_table(self):
        return
        self.table.set("id", "tbl")
        self.table.set("style", "width:60%")

        form_details = {}

        for key, value in form_details.items():
            table_row = ETree.SubElement(self.table, "tr")
            table_data = ETree.SubElement(table_row, "td")
            table_data.set("id", "td1")
            table_data.text = str(key)
            table_data = ETree.SubElement(table_row, "td")
            table_data.set("id", "td2")
            if key == 'Form ID':
                anchor = ETree.SubElement(table_data, "a")
                anchor.text = str(value)
                anchor.set("href", UPDATE_CENTER_URL.format("self.form.build_id", "self.form.form_id"))
            else:
                table_data.text = str(value)


class ExceptionTable(SuccessTable):

    def __init__(self, body, form, message):
        super().__init__(body, form)
        self.message = message

    def construct_table(self):
        if self.form is not None:
            super().construct_table()

        if self.message is None:
            return

        for key, value in self.message.items():
            table_row = ETree.SubElement(self.table, "tr")
            table_data = ETree.SubElement(table_row, "td")
            table_data.text = str(key).capitalize()
            table_data.set("id", "td1")
            table_data = ETree.SubElement(table_row, "td")
            table_data.text = str(value)
            table_data.set("id", "td2")
