import datetime
import time


class EpochTimeConverter:

    def __init__(self, date_string, time_string):
        self.date = date_string.split("-")
        self.time = time_string.split(":")

    def convert(self):
        date_time = datetime.datetime(int(self.date[0]), int(self.date[1]), int(self.date[2]), int(self.time[0]),
                                      int(self.time[1]), int(self.time[2]))

        unix_time = time.mktime(date_time.timetuple())
        return unix_time
