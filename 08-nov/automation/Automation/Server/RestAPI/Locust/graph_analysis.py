from optparse import OptionParser
import os
from os.path import basename
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt


def autolabelh(rects):
    for rect in rects:
        width = rect.get_width()
        plt.text(width * 1.05, rect.get_y() + rect.get_height() / 2., '%d' % int(width), ha='left', va='center', fontdict={'size': 8})


def generate_med(file_name, img_file):
    # converts CSV to a 2D array for Locust
    data = np.genfromtxt(fname=file_name, dtype=None, delimiter=',', names=True, autostrip=True)
    # get name and median response time header
    headers = data.dtype.names
    name_header, response_header = headers[1], headers[4]
    method_header = headers[0]
    # sorting data according to median response time
    sorted_data = np.sort(data, order=[response_header])
    name, median_response_time, method = sorted_data[name_header], sorted_data[response_header], sorted_data[method_header]
    name1 = [i.decode("utf-8") for i in name]
    for i in range(len(name1)):
        name1[i] = str(method[i].decode("utf-8")) + " " + name1[i]
    # plots a bargraph
    bar = plt.barh(range(len(median_response_time)), median_response_time, align='edge', alpha=0.7)
    # adds names of the requests along the y-axis
    plt.yticks(range(len(name1)), name1, ha='right', va='bottom', size='small')
    plt.xlabel('Time in milliseconds')
    plt.ylabel('API Requests')
    plt.subplots_adjust(left=0.3)
    plt.grid(True)
    autolabelh(bar)
    title = "Median Response Time For Each Request"
    plt.suptitle(title, fontsize=12, weight='bold')
    plt.savefig(img_file, bbox_inches='tight')
    plt.close()

def generate_ui_success(file_name, img_file, ui_file_path):
    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    temp_file = file_name.split(".csv")[0] + "_temp.csv"
    f = open(temp_file, "w")
    csv = open(file_name, "r")
    lines = csv.readlines()
    for i in lines:
        if len(i.split(",")) == 3:
            f.write(i)
    f.close()
    csv.close()
    data = np.genfromtxt(fname=temp_file, dtype=None, delimiter=',', names=True, autostrip=True)
    headers = data.dtype.names
    page, time, ui_time = headers[0], headers[1], headers[2]
    # sorting data according to median response time
    sorted_data = np.sort(data, order=[time])
    name, time_data, ui_loadtime = sorted_data[page], sorted_data[time], sorted_data[ui_time]
    name1 = [i.decode("utf-8") for i in name]
    # plots a bargraph
    fig,ax = plt.subplots()
    ax.xaxis.set_tick_params(labeltop='on')
    fig.set_size_inches(10, min(15, len(time_data)))
    bar = plt.barh(np.arange(len(time_data)), time_data, align='edge', alpha=0.7, color=["orange"], edgecolor="black", height=0.9)
    # adds names of the requests along the y-axis
    plt.yticks(range(len(name1)), name1, ha='right', va='bottom', size='small')
    plt.xlabel('Time in milliseconds')
    plt.ylabel('Page')
    plt.subplots_adjust(left=0.3, top=0.95, bottom=0.3)
    plt.grid(True)
    autolabelh(bar)
    title = "Total Time Taken For Each Page APIs to load"
    plt.title(label=title,
              fontsize=40,
              color="Black")
    fig.tight_layout()
    plt.savefig(img_file, bbox_inches='tight')
    fig, ax = plt.subplots()
    ax.xaxis.set_tick_params(labeltop='on')
    fig.set_size_inches(10, min(15, len(time_data)))
    sorted_data = np.sort(data, order=[ui_time])
    name, time_data, ui_loadtime = sorted_data[page], sorted_data[time], sorted_data[ui_time]
    bar = plt.barh(np.arange(len(ui_loadtime)), ui_loadtime, align='edge', alpha=0.7, color=["orange"], edgecolor="black",
                   height=0.9)
    # adds names of the requests along the y-axis
    plt.yticks(range(len(name1)), name1, ha='right', va='bottom', size='small')
    plt.xlabel('UI Load Time in milliseconds')
    plt.ylabel('Page')
    plt.subplots_adjust(left=0.3, top=0.95, bottom=0.3)
    plt.grid(True)
    autolabelh(bar)
    title = "Total Time Taken For Each Page to load in UI"
    plt.title(label=title,
              fontsize=40,
              color="Black")
    fig.tight_layout()
    plt.savefig(ui_file_path, bbox_inches='tight')
    plt.close()


def generate_ui_failure(file_name, img_file, title, ylabel, column_start=0):
    plt.rcParams["font.weight"] = "bold"
    plt.rcParams["axes.labelweight"] = "bold"
    data = np.genfromtxt(
        fname=file_name,
        dtype=None, delimiter=',', names=True, autostrip=True)
    # get name and median response time header
    headers = data.dtype.names
    page, cur_time, prev_time = headers[column_start], headers[column_start + 1], headers[column_start + 2]
    # sorting data according to median response time
    first_column = headers[0]
    fig, ax = plt.subplots()
    width = 0.5
    ax.xaxis.set_tick_params(labeltop='on')
    if np.size(data) > 1:
        sorted_data = np.sort(data, order=[cur_time])
        name, current_time, prev_time_data = sorted_data[page], sorted_data[cur_time], sorted_data[prev_time]
        first_col_data = sorted_data[first_column]
        first_col_data = [i.decode("utf-8") for i in first_col_data]
        ylabel_data = [i.decode("utf-8") for i in name]
        if column_start == 1:
            ylabel_data = [first_col_data[i] + " " + ylabel_data[i] for i in range(len(first_col_data))]
        fig.set_size_inches(12, min(25, len(current_time)))
        ticks = len(current_time) * 2
        ylabel_1 = np.arange(ticks, step=2)

        ylabel_2 = np.arange(ticks, step=2) + width
    else:
        sorted_data = data
        name, current_time, prev_time_data = sorted_data[page], [sorted_data[cur_time].item()], [
            sorted_data[prev_time].item()]
        ylabel_data = [name.item().decode("utf-8")]
        fig.set_size_inches(12, 8)
        ylabel_1 = np.arange(2)
        ylabel_1 = np.delete(ylabel_1, 1)
        ylabel_2 = np.arange(2) + width
        ylabel_2 = np.delete(ylabel_2, 1)

    bar1 = plt.barh(ylabel_1, current_time, align='edge', alpha=0.7,
                    color=["red"], edgecolor="black", height=0.5, label="Current Time")
    bar2 = plt.barh(ylabel_2, prev_time_data, align='edge', alpha=0.7,
                    color=["green"], label="Previous Time",
                    edgecolor="black", height=0.5)
    # adds names of the requests along the y-axis
    plt.yticks(np.arange(len(ylabel_data) * 2, step=2) + 0.5, ylabel_data, ha='right', va='bottom', size='small')
    plt.xlabel('Time in milliseconds')
    plt.ylabel(ylabel)
    plt.subplots_adjust(left=0.3)
    plt.grid(True)
    plt.legend()
    autolabelh(bar1)
    autolabelh(bar2)
    plt.title(label=title, fontsize=40, color="Black")
    fig.tight_layout()
    plt.savefig(img_file, bbox_inches='tight')
    plt.close()

def generate_avg(file_name, img_file):
    # converts CSV to a 2D array for Locust
    data = np.genfromtxt(fname=file_name, dtype=None, delimiter=',', names=True, autostrip=True)
    # get name and median response time header
    headers = data.dtype.names
    name_header, response_header = headers[1], headers[5]
    method_header = headers[0]
    # sorting data according to median response time
    sorted_data = np.sort(data, order=[response_header])
    name, median_response_time, method = sorted_data[name_header], sorted_data[response_header], sorted_data[method_header]
    name1 = [i.decode("utf-8") for i in name]
    for i in range(len(name1)):
        name1[i] = str(method[i].decode("utf-8")) + " " + name1[i]
    # plots a bargraph
    bar = plt.barh(range(len(median_response_time)), median_response_time, align='edge', alpha=0.7)
    # adds names of the requests along the y-axis
    plt.yticks(range(len(name1)), name1, ha='right', va='bottom', size='small')
    plt.xlabel('Time in milliseconds')
    plt.ylabel('API Requests')
    plt.subplots_adjust(left=0.3)
    plt.grid(True)
    autolabelh(bar)
    title = "Average Response Time For Each Request"
    plt.suptitle(title, fontsize=12, weight='bold')
    plt.savefig(img_file, bbox_inches='tight')
    plt.close()


def generate_req(file_name, img_file):
    # converts CSV to a 2D array
    data = np.genfromtxt(fname=file_name, dtype=None, delimiter=',', names=True, autostrip=True)
    # get name and median response time header
    headers = data.dtype.names
    name_header, response_header = headers[1], headers[2]
    method_header = headers[0]
    # sorting data according to median response time
    sorted_data = np.sort(data, order=[response_header])
    name, median_response_time, method = sorted_data[name_header], sorted_data[response_header], sorted_data[method_header]
    name1 = [i.decode("utf-8") for i in name]
    for i in range(len(name1)):
        name1[i] = str(method[i].decode("utf-8")) + " " + name1[i]
    # plots a bargraph
    bar = plt.barh(range(len(median_response_time)), median_response_time, align='edge', alpha=0.7)
    # adds names of the requests along the y-axis
    plt.yticks(range(len(name1)), name1, ha='right', va='bottom', size='small')
    plt.xlabel('Number of requests')
    plt.ylabel('API Requests')
    plt.subplots_adjust(left=0.3)
    plt.grid(True)
    autolabelh(bar)
    title = "Total Number of Requests"
    plt.suptitle(title, fontsize=12, weight='bold')
    plt.savefig(img_file, bbox_inches='tight')
    plt.close()


def generate_fail(file_name, img_file):
    # converts CSV to a 2D array
    data = np.genfromtxt(fname=file_name, dtype=None, delimiter=',', names=True, autostrip=True)
    # get name and median response time header
    headers = data.dtype.names
    name_header, response_header = headers[1], headers[3]
    method_header = headers[0]
    # sorting data according to median response time
    sorted_data = np.sort(data, order=[response_header])
    name, median_response_time,method = sorted_data[name_header], sorted_data[response_header], sorted_data[method_header]
    name1 = [i.decode("utf-8") for i in name]
    for i in range(len(name1)):
        name1[i] = str(method[i].decode("utf-8")) + " " + name1[i]
    # plots a bargraph
    bar = plt.barh(range(len(median_response_time)), median_response_time, align='edge', alpha=0.7)
    # adds names of the requests along the y-axis
    plt.yticks(range(len(name1)), name1, ha='right', va='bottom', size='small')
    plt.xlabel('Number of failures')
    plt.ylabel('API Requests')
    plt.subplots_adjust(left=0.3)
    plt.grid(True)
    autolabelh(bar)
    title = "Total Number of Failures"
    plt.suptitle(title, fontsize=12, weight='bold')
    plt.savefig(img_file, bbox_inches='tight')
    plt.close()
