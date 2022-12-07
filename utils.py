from bs4 import BeautifulSoup
import requests
import json
import re
import calendar
from datetime import date
import pandas as pd
import numpy as np
import os


class ExtractCalendar:
    def __init__(self):
        self.months = {month: index for index, month in enumerate(calendar.month_abbr) if month}

    def extract_calendar(self, years, country):
        holiday_information = {}
        self.years = years

        for year in self.years:
            holiday_information[year] = self.extract_single_calendar(year, country)
        #     columns = holiday_information[year].columns
        # print(columns)
        return holiday_information

    def extract_single_calendar(self, year, country):
        url = f"https://www.officeholidays.com/countries/{country}/{year}"
        html_content = requests.get(url).text

        # Parse HTML code for the entire site
        soup = BeautifulSoup(html_content, "lxml")
        table = soup.find('table', attrs={"class": "country-table"})

        body = table.find("tbody")
        head = table.find("thead")
        columns = []
        holiday_info = []
        for item in head.find_all("th"):
            columns.append(item.text.rstrip("\n"))

        for row in body.findAll('tr'):  # A row at a time
            row_set = []  # this will old entries for one row
        #     i = 0
            for row_item in row.findAll("td"):  # loop through all row entries
                if row_item.find('time'):
                    if row_item.find('time').has_attr('datetime'):
                        row_set.append(pd.to_datetime(row_item.find('time')['datetime']).date())
                else:
                    aa = re.sub("(\xa0)|(\n)|,", "", row_item.text)
                    row_set.append(aa.strip())
            holiday_info.append(row_set)
            holiday_df = pd.DataFrame(holiday_info, columns=columns)
        return holiday_df

    def store_holidays(self, years, countries, save_to_disk=True):
        self.holiday = {}
        for year in years:
            for country in countries:
                self.holiday[year] = self.extract_single_calendar(year, country)
                if save_to_disk:
                    if not os.path.isdir("./holidays"):
                        os.mkdir("./holidays")
                    self.holiday[year].to_csv(f"./holidays/{country}_{year}.csv")

    def load_from_disk(self, path, years, country):
        self.holiday = {}
        for year in years:
            self.holiday[year] = pd.read_csv(path+f"/{country}_{year}.csv", index_col=0)

        return self.holiday

    def is_holiday(self, _date, country, live=False):
        if live:
            return _date in self.extract_single_calendar(_date.year, country)['Date'].tolist()
        else:
            return str(_date) in self.load_from_disk("./holidays", [_date.year], country)[int(_date.year)]['Date'].tolist()
