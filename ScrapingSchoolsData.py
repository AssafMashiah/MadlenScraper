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

schools = []
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
    records = schoolsTable.find_all('tr')
    teachersBurnout = []
    studentsGotKicked = []
    if len(records[0].find_all('td')) > 5:
        for elem in records:
            bla = elem.find_all('td')
            teachersBurnout.append(elem.find_all('td')[6].text.strip())
            studentsGotKicked.append(elem.find_all('td')[5].text.strip())

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
        schoolInfo = {}
        schoolInfoInList = []

        notIncludeInInfo = [u"טלפון",u"מנהל",u"תלמידים בכיתה",u"מספר כיתות"]

        for i in range(0, len(schoolInfoBox)):
            info = schoolInfoBox[i].text.splitlines()
            if notIncludeInInfo[0] in schoolInfoBox[i].text or notIncludeInInfo[1] in schoolInfoBox[i].text or notIncludeInInfo[2] in schoolInfoBox[i].text or notIncludeInInfo[3] in schoolInfoBox[i].text:
                continue
            schoolInfoInList.append(info[len(info) - 2].strip())

        headers = html_soup.find_all('h2')
        if u"מדד מדלן" in headers[0].text:
            currentMadlanIndex = headers[0].text.splitlines()[2].strip()
        else:
            currentMadlanIndex = ""

        madlanData = html_soup.find_all('table', class_="meitzav-table")
        if not madlanData:
            if len(schoolInfoInList) == 9:
                schoolInfo["City"] = cities[t].decode('utf-8')
                schoolInfo["SemelMosad"] = schoolIndex
                schoolInfo["SchoolName"] = schoolNames[m]
                schoolInfo["SchoolAddress"] = schoolInfoInList[0]
                schoolInfo["SchoolStudentNumber"] = schoolInfoInList[1]
                schoolInfo["SchoolEducationMinistry"] = schoolInfoInList[2]
                schoolInfo["SchoolYear"] = schoolInfoInList[3]
                schoolInfo["SchoolLongDay"] = schoolInfoInList[4]
                schoolInfo["SchoolOfekHadash"] = schoolInfoInList[5]
                schoolInfo["SchoolStatus"] = schoolInfoInList[6]
                schoolInfo["SchoolLanguage"] = schoolInfoInList[7]
                schoolInfo["SchoolSector"] = schoolInfoInList[8]
            else:
                schoolInfo["City"] = cities[t].decode('utf-8')
                schoolInfo["SemelMosad"] = schoolIndex
                schoolInfo["SchoolName"] = schoolNames[m]
                schoolInfo["SchoolAddress"] = schoolInfoInList[0]
                schoolInfo["SchoolEducationMinistry"] = schoolInfoInList[1]
                schoolInfo["SchoolYear"] = schoolInfoInList[2]
                schoolInfo["SchoolLongDay"] = schoolInfoInList[3]
                schoolInfo["SchoolOfekHadash"] = schoolInfoInList[4]
                schoolInfo["SchoolStatus"] = schoolInfoInList[5]
                schoolInfo["SchoolLanguage"] = schoolInfoInList[6]
                schoolInfo["SchoolSector"] = schoolInfoInList[7]
            schools.append(schoolInfo)
            continue
        temp = madlanData[0].find_all('td')
        madlanIndexPerYearInfo = []

        for i in range(0, len(temp), 2):
            madlanIndexYearInfo = {}
            madlanIndexYearInfo["Year"] = temp[i].text
            madlanIndexYearInfo["madlanIndex"] = temp[i + 1].text.strip()
            madlanIndexPerYearInfo.append(madlanIndexYearInfo)

        precentages=html_soup.find_all('div', class_="school-claim")
        goodAtSchoolRecords = []
        for elem in precentages:
            if u"טוב לי בבית הספר" in elem.text:
                goodAtSchoolRecords.append(elem.text)

        goodAtSchool = []
        for elem in goodAtSchoolRecords:
            record = {}
            temp = [s.strip() for s in elem.splitlines()]
            temp = filter(None, temp)
            record["Precent"] = temp[0]
            record["Grades"] = temp[3]
            goodAtSchool.append(record)

        zonePromotionBox = html_soup.find_all('div', class_="zonePromotionBox-data")
        if zonePromotionBox:
            if u"מדד חברתי" not in zonePromotionBox[3].text:
                neighborhoodIndex = ""
            else:
                neighborhoodIndex = [s.strip() for s in zonePromotionBox[3].text.splitlines()][4].split()[0]
        else:
            neighborhoodIndex = ""

        schoolInfo["City"] = cities[t].decode('utf-8')
        schoolInfo["SemelMosad"] = schoolIndex
        schoolInfo["SchoolName"] = schoolNames[m]
        schoolInfo["SchoolAddress"] = schoolInfoInList[0]
        schoolInfo["SchoolStudentNumber"] = schoolInfoInList[1]
        schoolInfo["SchoolEducationMinistry"] = schoolInfoInList[2]
        schoolInfo["SchoolYear"] = schoolInfoInList[3]
        schoolInfo["SchoolLongDay"] = schoolInfoInList[4]
        schoolInfo["SchoolOfekHadash"] = schoolInfoInList[5]
        schoolInfo["SchoolStatus"] = schoolInfoInList[6]
        schoolInfo["SchoolLanguage"] = schoolInfoInList[7]
        schoolInfo["SchoolSector"] = schoolInfoInList[8]
        if teachersBurnout:
            schoolInfo["TeachersBurnout"] = teachersBurnout[m]
            schoolInfo["StudentsGotKicked"] = studentsGotKicked[m]
        schoolInfo["CurrentMadlanIndex"] = currentMadlanIndex
        schoolInfo["NeighborhoodIndex"] = neighborhoodIndex
        if not goodAtSchool:
            schools.append(schoolInfo)
            continue
        schoolInfo["GoodAtSchool"] = goodAtSchool
        schools.append(schoolInfo)
    print t

ordered_list=["City","SemelMosad","SchoolName","SchoolAddress","SchoolStudentNumber","SchoolEducationMinistry","SchoolYear","SchoolLongDay","SchoolOfekHadash","SchoolStatus","SchoolLanguage", "SchoolSector", "TeachersBurnout","StudentsGotKicked","CurrentMadlanIndex","NeighborhoodIndex", "GoodAtSchool"] #list object calls by index but dict object calls items randomly
wb2=Workbook("schools.xlsx")
ws=wb2.add_worksheet("New Sheet")

first_row=0
for header in ordered_list:
    col=ordered_list.index(header)
    ws.write(first_row,col,header)

row=1
for school in schools:
    for _key,_value in school.items():
        col=ordered_list.index(_key)
        if _key == "GoodAtSchool" and len(_value) > 0:
            str = _value[0]["Grades"] + ":" + _value[0]["Precent"]
            ws.write(row, col, str)
            for i in range(1, len(_value)):
                ws.write(0, col + i, _key)
                str = _value[i]["Grades"] + ":" + _value[i]["Precent"]
                ws.write(row, col + i, str)
            continue
        ws.write(row,col,_value)
    row+=1
wb2.close()

exit(0)