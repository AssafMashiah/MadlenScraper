#!/usr/bin/env python
# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
from requests import get
import seaborn as sns
sns.set()
from xlsxwriter import Workbook
import time

userAgents = ['Galaxy/1.0', 'Mozilla/5.0', 'Mozilla/3.0', 'Opera/9.80']

citiesUrl = "http://cdn.madlan.co.il/widgets/schools/2017/0.40/heatmap.json"
response = get(citiesUrl)
content = response.content.split('"id":')
check = content[1].split(',')[0]
cities = []
for i in range(1, len(content)):
    str = content[i].split(',')[0]
    str = str[1:-1]
    temp = str.split()
    if "\\u0027" in str:
        str = str.replace("\\u0027", "'")
    if "\\" in str:
        str  = str.replace("\\", "")
    cities.append(str)
cities.sort()

schoolLocation = []
for t in range(0, len(cities)):
    madlan = "https://www.madlan.co.il/education/ajax?areaId=" + cities[t]

    response = get(madlan, headers={'User-Agent': userAgents[t%4]})

    if response.status_code == 403:
        time.sleep(3)
        response = get(madlan, headers={'User-Agent': userAgents[(t+2)%4]})

    if response.status_code == 403:
        time.sleep(3)
        response = get(madlan, headers={'User-Agent': userAgents[(t+1)%4]})

    if response.status_code == 403:
        time.sleep(3)
        response = get(madlan, headers={'User-Agent': userAgents[(t+3)%4]})

    content = response.content.split('"id":')
    content2 = response.content.split('"lng":')
    content3 = response.content.split('"lat":')
    for i in range(1, len(content)):
        school = {}
        semelMosad = content[i].split(',')[0]
        semelMosad = semelMosad[1:-1]
        lng = content2[i].split(',')[0]
        lng = lng[1:-1]
        lat = content3[i].split(',')[0]
        lat = lat[1:-1]
        school["SemelMosad"] = semelMosad.decode('utf-8')
        school["lng"] = lng.decode('utf-8')
        school["lat"] = lat.decode('utf-8')
        school["City"] = cities[t].decode('utf-8')
        schoolLocation.append(school)

    print t

ordered_list=["City","SemelMosad","lng","lat"] #list object calls by index but dict object calls items randomly
wb2=Workbook("schools locations.xlsx")
ws=wb2.add_worksheet("New Sheet") #or leave it blank, default name is "Sheet 1"

first_row=0
for header in ordered_list:
    col=ordered_list.index(header) # we are keeping order.
    ws.write(first_row,col,header) # we have written first row which is the header of worksheet also.

row=1
for school in schoolLocation:
    for _key,_value in school.items():
        if _key in ordered_list:
            col=ordered_list.index(_key)
        ws.write(row,col,_value)
    row+=1 #enter the next row
wb2.close()


exit(0)