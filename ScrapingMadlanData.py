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

schoolMadlanData = []
for t in range(0, len(cities)):

    madlan = "https://www.madlan.co.il/education/" + cities[t]

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

    html_soup = BeautifulSoup(response.text, 'html.parser')
    tablesInPage = html_soup.find_all('tbody')
    if not tablesInPage:
        continue

    if len(tablesInPage) == 1:
        schoolsTable = tablesInPage[0]
    else:
        schoolsTable = tablesInPage[1]

    schoolsLinks = schoolsTable.find_all('a')

    schoolNames = []
    for i in range(0, len(schoolsLinks)):
        schoolNames.append(schoolsLinks[i].text)

    links = []
    for i in range(0, len(schoolsLinks)):
        link = "https://www.madlan.co.il" + schoolsLinks[i].get('href')
        links.append(link)

    for m in range(0, len(links)):
        schoolIndex = links[m].split("/")[5]
        response = get(links[m], headers={'User-Agent': userAgents[m % 4]})
        html_soup = BeautifulSoup(response.text, 'html.parser')
        schoolInfoBox = html_soup.find_all('div', class_='shcoolInfoBox')
        schoolMadlanInfo = {}
        schoolInfoInList = []
        madlanData = html_soup.find_all('table', class_="meitzav-table")
        if not madlanData:
            schoolMadlanInfo["City"] = cities[t].decode('utf-8')
            schoolMadlanInfo["SemelMosad"] = schoolIndex
            schoolMadlanData.append(schoolMadlanInfo)
            continue
        temp = madlanData[0].find_all('td')

        years = []
        madlanIndexes = []
        for i in range(0, len(temp), 2):
            years.append(temp[i].text)
            madlanIndexes.append(temp[i + 1].text.strip())

        testsResults = html_soup.find_all('div', class_="gradesPerYearCont")
        for n in range(0, len(testsResults)):
            yearData = testsResults[n].find_all('div', class_="perYearAndClassGrade")
            for j in range(0, len(yearData)):
                test = {}
                dataText = []
                dataText = [s.strip() for s in yearData[j].text.splitlines()]
                dataText = filter(None, dataText)
                test["Year"] = years[n]
                test["MadlanIndex"] = madlanIndexes[n]
                test["TestKind"] = dataText[0].split()[1].strip(":")
                testKind = dataText[0].split()[1]
                if u"בגרות" not in testKind:
                    test["Grade"] = dataText[0].split()[3].strip(":")
                    grade = dataText[0].split()[3]
                subjectsList = []
                for k in range(1, len(dataText)):
                    subjects = {}
                    subjects["Subject"] = dataText[k].split(":")[0]
                    subjects["Precent"] = dataText[k].split(":")[1]
                    subjectsList.append(subjects)
                test["Subjects"] = subjectsList
                test["City"]= cities[t].decode('utf-8')
                test["SemelMosad"] = schoolIndex
                schoolMadlanData.append(test)

    print t

subjects = ["City","SemelMosad","Year","MadlanIndex","TestKind","Grade"]

ordered_list=["City","SemelMosad","Year","MadlanIndex","TestKind","Grade"]
wb2=Workbook("madlan data.xlsx")
ws=wb2.add_worksheet("New Sheet")

first_row=0
for header in ordered_list:
    col=ordered_list.index(header)
    ws.write(first_row,col,header)

row=1
for school in schoolMadlanData:
    for _key,_value in school.items():
        if _key in ordered_list:
            col=ordered_list.index(_key)
        if _key == "Subjects":
            if len(_value) == 0:
                continue
            for i in range(0, len(_value)):
                if _value[i]["Subject"] not in subjects:
                    subjects.append(_value[i]["Subject"])
                col2 = subjects.index(_value[i]["Subject"])
                ws.write(0, col2, _value[i]["Subject"])
                ws.write(row, col2, _value[i]["Precent"])
            continue
        ws.write(row,col,_value)
    row+=1
wb2.close()


exit(0)