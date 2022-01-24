#TODO transition from regex to bs4 where possible?
import os
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup

from ucdgymbooker import db
from ucdgymbooker.helpers import timezone_converter
from ucdgymbooker.models import Timeslot

import time

months = {
        'jan': 1,
        'feb': 2,
        'mar': 3,
        'apr':4,
         'may':5,
         'jun':6,
         'jul':7,
         'aug':8,
         'sep':9,
         'oct':10,
         'nov':11,
         'dec':12
}


base_url = 'https://hub.ucd.ie/usis/W_HU_MENU.P_PUBLISH?p_tag=GYMBOOK'

xpath = '//*[@id="pagebar"]/form/select'
xpath3 = '//*[@id="pagebar"]/form/select/option[1]'

#https://towardsdatascience.com/using-python-and-selenium-to-automate-filling-forms-and-mouse-clicks-f87c74ed5c0f
options = webdriver.ChromeOptions()
service = Service(os.path.join(os.getcwd(), os.path.join('webdriver','chromedriver')))
#TODO uncomment
#options.add_argument("headless")

driver = webdriver.Chrome(service=service, options=options)

#tz_ie = pytz.timezone('Europe/Dublin')
#tz_utc = pytz.timezone('Etc/UTC')






#extract dates and gyms from source html [table containing gym, hour and minute] and a string containing the day, month and year
def extract_timeslots(table, datestring):
    timeslots = []
    #cleaned_table = table.replace("\n", "")
    #cleaned_table_row = cleaned_table.split("<tr")
    rows = table.findChildren(['tr'])


    #<tr id=".*" class=".*"><td>([0-9]*):([0-9]*)<\/td><td>[A-Z,a-z, ]*<\/td><td>[a-z,0-9, ]*<\/td><td>([A-Z,a-z, ]*)<\/td>

    datelist = datestring.split(" ")
    day = int(datelist[1])
    #take first 3 letters, turn into lowercase and then lookup in "months" dict
    month = int(months[datelist[2].strip()[:3].lower()])
    year = int(datelist[3])
    for row in rows:
        try:
            #row_data = re.findall(r'id=".*" class=".*"><td>([0-9]*):([0-9]*)<\/td><td>[A-Z,a-z, ]*<\/td><td>[a-z,0-9, ]*<\/td><td>([A-Z,a-z, ]*)<\/td>', elem)[0]
            cells = row.findChildren('td')
            time_string = cells[0].string
            print(time_string)
            hour = int(time_string[0:2])
            minute = int(time_string[3:5])
            timestamp_ie = timezone_converter.create_ie_timestamp(year, month, day, hour, minute)
            timestamp_utc = timezone_converter.ie_to_utc(timestamp_ie)
            #timestamp_ie = datetime(year, month, day, hour, minute, 0, 0, tz_utc)
            #timestamp_utc = timestamp_ie.astimezone(tz_ie)
            gym = cells[3].string
            dict = {"gym": gym, "date":timestamp_utc}
            timeslots.append(dict)


        except Exception as e:
            print(e)


    return timeslots

#update one db entry
def update_db_if_not_exists(timeslots):
    for timeslot in timeslots:
        gym = timeslot["gym"]
        timestamp = timeslot["date"]
        print(gym)
        print(timestamp)
        if not Timeslot.query.filter_by(gym=gym, time=timestamp).first():
            new_timeslot = Timeslot(gym=gym, time=timestamp)
            db.session.add(new_timeslot)
            db.session.commit()




driver.get(base_url)

page_html = driver.find_element(By.XPATH, xpath).get_attribute('outerHTML')
#print(dates_html)

#TODO change to bs4 because apparently the already selected element does not appear due to differing syntax
#dates = re.findall(r'<option value="[0-9,A-Z,-]*">(.*)<\/option>', page_html)
#print(dates)

#TODO uncomment this

html = driver.page_source

soup = BeautifulSoup(html, features="html.parser")

#dates = re.findall(r'<option value="[0-9,A-Z,-]*">(.*)<\/option>', page_html)
#print(dates)
dates_selector = soup.find("select",{"name":"p_code1"})
print(dates_selector)
dates_html = dates_selector.findChildren("option")
dates = []
for elem in dates_html:
    dates.append(elem.string)
print(dates_html)
print(dates)
current_table = soup.find("table",{"class":"plaintable"})
current_table = current_table.find("table",{"class":"datadisplaytable"})
#timeslots = extract_timeslots(current_table, dates[0])
#update_db_if_not_exists(timeslots)


#TODO change back to 1
#TODO check whether the scraped page and data match up
for i in range(0, len(dates)):
    print(i)
    print(dates[i])
    #//*[@id="pagebar"]/form/select
    xpath_selector = '//*[@id="pagebar"]/form/select'
    #start index of xpath selector is 1 instead of 0
    xpath_selection = '//*[@id="pagebar"]/form/select/option[' + str(i+1) + "]"
    #driver.find_element(By.XPATH, xpath_selector).click()
    driver.find_element(By.XPATH, xpath_selection).click()
    #TODO comment out?
    time.sleep(1)
    html = driver.page_source
    soup = BeautifulSoup(html, features="html.parser")
    current_table = soup.find("table",{"class":"plaintable"})
    current_table = current_table.find("table",{"class":"datadisplaytable"})
    #current_table = driver.find_element(By.XPATH, '//*[@id="SW300-1"]/table').get_attribute('outerHTML')

    timeslots = extract_timeslots(current_table, dates[i])
    update_db_if_not_exists(timeslots)




'''


print(pytz.all_timezones)

timezone = pytz.timezone('Europe/Dublin')

# GB-Eire  GMT0
tiz = pytz.timezone('GB-Eire')
tz2 = pytz.timezone('Europe/Brussels')
timezoneutc = pytz.timezone('Etc/UTC')

ie_tz = tz.gettz('Europe/Dublin')

#dublin to utc
#.astimezone(timezone)
timestamp = datetime(2022, 6, 12, 6, 0, 0, 0, ie_tz)
#timestamp2 = timestamp.replace(tzinfo=pytz.utc)
timestamp2 = timestamp.astimezone(timezoneutc)
print(timestamp)
print(timestamp2)

#utc to dublin
timestamp3 = datetime(2022, 6, 12, 6, 0, 0, 0, timezoneutc)
#timestamp2 = timestamp.replace(tzinfo=pytz.utc)
timestamp4 = timestamp3.astimezone(ie_tz)
print(timestamp3)
print(timestamp4)


#get html content of current page
driver.find_element(By.XPATH, "//body").get_attribute('outerHTML')


#get all selectable urls
driver.find_element(By.XPATH, xpath).click()


#soup = BeautifulSoup(content, 'html.parser')
#table = soup.find("table", {"class":"datadisplaytable"})

'''