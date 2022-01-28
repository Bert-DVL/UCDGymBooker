import os
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from bs4 import BeautifulSoup

from ucdgymbooker import db
from ucdgymbooker.helpers import timezone_converter
from ucdgymbooker.models import Timeslot, Reservation, User



import time

base_url = 'https://hub.ucd.ie/usis/W_HU_MENU.P_PUBLISH?p_tag=GYMBOOK'

#https://towardsdatascience.com/using-python-and-selenium-to-automate-filling-forms-and-mouse-clicks-f87c74ed5c0f
options = webdriver.ChromeOptions()
service = Service(os.path.join(os.getcwd(), os.path.join('webdriver','chromedriver')))
#TODO uncomment
#options.add_argument("headless")

driver = webdriver.Chrome(service=service, options=options)

#gets the reservations that fall within the time interval, update their status as well
#prepend admin reservations
def get_relevant_reservations():
    now = timezone_converter.get_current_utc_timestamp()
    #TODO minuys to plus
    lower_bound = timezone_converter.add_time(now, -3, 0)
    upper_bound = timezone_converter.add_time(now, 3, 20)

    #TODO is this also subordered by reservation priority?
    #TODO issue with , Reservation.status=='Booked'
    reservations = db.session.query(Reservation, Timeslot, User).join(Timeslot).join(User).filter(Timeslot.time <= upper_bound,  Timeslot.time >= lower_bound).order_by(User.admin.desc(), Reservation.reservation_time)




    #TODO check whether this does sth or not
    for reservation, timeslot, user in reservations:
        reservation.status = 'Processing'
    db.session.commit()

    return reservations

#returns poolside and/or performance gym urls in dict
#TODO trycatch
def get_confirm_urls(hourstring):
    urls = {}
    driver.get(base_url)
    html = driver.page_source
    soup = BeautifulSoup(html, features="html.parser")
    table = soup.find("table", {"class": "plaintable"})
    table = table.find("table", {"class": "datadisplaytable"})

    rows = table.findChildren(['tr'])

    baseurl = "https://hub.ucd.ie/usis/"

    for row in rows:
        try:
            cells = row.findChildren('td')

            gym = cells[3].string[0:4].lower()

            print(gym)
            print(cells[5].findChildren('a')[0]['href'])
            half_url = cells[5].findChildren('a')[0]['href']

            fullurl = baseurl + half_url
            '''
            fullurl = fullurl.replace("&amp", "&")
            fullurl = fullurl.replace(";", "")
            '''

            urls[gym] = fullurl
            print('fullurl')
            print(fullurl)
            if cells[0].string == hourstring:
                urls[cells[3].string] = cells[5].string

        except Exception as e:
            print(e)


    #print(table)

    #print(urls)

    return urls

#try to confim one specific reservation, returns True if success
def confirm_reservation(id, url, first_iteration):
    driver.get(url)



    #TODO do cookies properly, except in trycatch is very inefficent
    if first_iteration:
        try:
            cookies1 = '//*[@id="onetrust-accept-btn-handler"]'
            cookies2 = '/html/body/div[3]/div[3]/div/div/div[2]/div/div/button'
            #TODO 1 second was kind of cutting it close
            element = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, cookies2)))
            #driver.find_element(By.XPATH, cookies1).click()
            element.click()
        except Exception as e:
            print(e)

    try:
        inputfield = '//*[@id="single-column-content"]/div/div/div/div[2]/div/form/input[4]'
        driver.find_element(By.XPATH, inputfield).send_keys(id)

        proceedbutton = '//*[@id="single-column-content"]/div/div/div/div[2]/div/form/input[5]'
        driver.find_element(By.XPATH, proceedbutton).click()

        confirmbutton = '// *[ @ id = "single-column-content"] / div / div / div / div[2] / div / a[1]'
        driver.find_element(By.XPATH, confirmbutton).click()

        if driver.title == 'Confirmation':
            return True
        else:
            return False

        #confirmtext = '//*[@id="single-column-content"]/div/div/div/h1'







    except Exception as e:
        print(e)


    return False

reservations = get_relevant_reservations()
print(reservations.count())

if reservations.count() > 0:
    # get the time when all reservations need to be done, normally all reservations within a 20 minute interval should have the same time
    # so getting the time from the first timeslot object in the first reservation should be ok

    #timestamp is already in utc but not localised yet, ie_to_utc fixes that
    goal_time = timezone_converter.subtract_time(timezone_converter.ie_to_utc(reservations[0][1].time), 3, 0)
    print(goal_time)
    current_time = timezone_converter.get_current_utc_timestamp()
    print(current_time)

    #TODO uncomment
    #polling wait

    while current_time < goal_time:
        time.sleep(0.1)
        current_time = timezone_converter.get_current_utc_timestamp()
        


    hourstring = timezone_converter.get_time_string(timezone_converter.utc_to_ie(reservations[0][1].time))
    urls = get_confirm_urls(hourstring)

    poolside_available = True
    performance_available = True

    previous_successful = False

    first_iteration = True

    #TODO primary secondary als current priority is 2

    #go over all reservations, try to book them as long as previous booking for the same gym was successful, skip over the confirmation otherwise (status is set as 'Failed' then also)
    #if priority is 2 it also checks whether or not the primary reservation (previous element in list) succeeded or not
    for reservation, timeslot, user in reservations:
        print('currently handling')
        print(user)
        print(timeslot)
        print(timeslot.gym)
        if reservation.priority == 2 and previous_successful:
            reservation.status = 'Primary booked successfully'
            previous_successful = False
            continue

        success_reservation = False

        if  poolside_available and timeslot.gym == 'Poolside Gym':
            success = confirm_reservation(user.username, urls['pool'], first_iteration)
            poolside_available = success
            success_reservation = success
        print('LALA')
        print(urls['perf'])
        print(performance_available)
        if performance_available and timeslot.gym == 'Performance Gym' :
            print('perf triggered')
            print(urls['perf'])
            success = confirm_reservation(user.username, urls['perf'], first_iteration)
            print(success)
            performance_available = success
            success_reservation = success
            print(performance_available)

        if success_reservation:
            reservation.status = 'Success'
        else:
            reservation.status = 'Failed'

        previous_successful = success_reservation
        first_iteration = False





    db.session.commit()



driver.quit()


'''
First thing it does is changing status in db
That way when new script starts while current script is running, nothing is screwed up

Run script every 15 min, it is responsible for time interval between now and now plus 20 minutes



'''

