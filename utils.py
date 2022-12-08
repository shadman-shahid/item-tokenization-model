from bs4 import BeautifulSoup
import requests
import json
import re
import calendar
from datetime import date
import pandas as pd
import numpy as np
import os
import itertools


class ExtractCalendar:
    def __init__(self, years, countries=['bangladesh']):
        self.months = {month: index for index, month in enumerate(calendar.month_abbr) if month}
        self.store_holidays(years, countries, save_to_disk=False)
        self.festivals = []
        for year in years:
            self.festivals.append(self.holiday[year].loc[self.holiday[year]['Holiday Name'].str.contains("Eid")]['Date'].to_list())
            self.festivals.append(self.holiday[year].loc[self.holiday[year]['Holiday Name'].str.contains("Puja")]['Date'].to_list())

        self.festivals = list(itertools.chain(*self.festivals))
    def extract_calendar(self, years, country='bangladesh', update=True, save=False):
        if not isinstance(years, list):
            years = [years]

        holiday_information = {}
        self.years = years
        for year in self.years:
            if os.path.isfile(f"./holidays/{country}_{year}.csv") and not update:
                holiday_temp = pd.read_csv("./holidays"+f"/{country}_{year}.csv", index_col=0)
                holiday_temp['Date'] = pd.to_datetime(holiday_temp['Date'])
                holiday_information[year] = holiday_temp
            else:
                holiday_information[year] = self.extract_single_calendar(year, country)

        return holiday_information

    def extract_single_calendar(self, year, country='bangladesh'):
        if os.path.isfile(f"./holidays/{country}_{year}.csv"):
            holiday_temp = pd.read_csv("./holidays" + f"/{country}_{year}.csv", index_col=0)
            holiday_temp['Date'] = pd.to_datetime(holiday_temp['Date'])
            holiday_df = holiday_temp
            return holiday_df

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

    def store_holidays(self, years, countries=['bangladesh'], save_to_disk=True):
        self.holiday = {}
        if not isinstance(years, list):
            years = [years]
        if not isinstance(countries, list):
            countries = [countries]
        if not os.path.isdir("./holidays"):
            os.mkdir("./holidays")

        for year in years:
            for country in countries:
                if os.path.isfile(f"./holidays/{country}_{year}.csv"):
                    holiday_temp = pd.read_csv("./holidays" + f"/{country}_{year}.csv", index_col=0)
                    holiday_temp['Date'] = pd.to_datetime(holiday_temp['Date'])
                    self.holiday[year] = holiday_temp
                else:
                    self.holiday[year] = self.extract_single_calendar(year, country)
                    if save_to_disk:
                        self.holiday[year].to_csv(f"./holidays/{country}_{year}.csv")

    def load_from_disk(self, path, years, country='bangladesh'):
        self.holiday = {}
        for year in years:
            self.holiday[year] = pd.read_csv(path+f"/{country}_{year}.csv", index_col=0)
        return self.holiday

    def is_holiday(self, _date, country='bangladesh'):
        if not isinstance(_date, date):
            try:
                _date = pd.to_datetime(_date).date()
            except:
                raise TypeError("The date type is not right")

        if not os.path.isfile(f"./holidays/{country}_{_date.year}.csv"):
            return _date in self.extract_single_calendar(_date.year, country)['Date'].tolist()
        else:
            return str(_date) in self.load_from_disk("./holidays", [_date.year], country)[int(_date.year)]['Date'].tolist()

    def is_festival(self, _date, country='bangladesh'):
        if not isinstance(_date, date):
            try:
                _date = pd.to_datetime(_date).date()
            except:
                raise TypeError("The date type is not right")
        if _date.year < 2015:
            return 'Not available'
        try:
            festivals = self.holiday[_date.year].loc[self.holiday[_date.year]['Holiday Name'].str.contains("Eid")]['Date'].to_list()
            festivals.append(self.holiday[_date.year].loc[self.holiday[_date.year]['Holiday Name'].str.contains("Puja")]['Date'].to_list())
        except:
            self.holiday[_date.year] = self.extract_single_calendar(self, _date.year)
            festivals = self.holiday[_date.year].loc[self.holiday[_date.year]['Holiday Name'].str.contains("Eid")]['Date'].to_list()
            festivals.append(self.holiday[_date.year].loc[self.holiday[_date.year]['Holiday Name'].str.contains("Puja")]['Date'].to_list())

        return pd.Timestamp(_date) in festivals
