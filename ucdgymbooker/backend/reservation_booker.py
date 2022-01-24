import os
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

from bs4 import BeautifulSoup

from ucdgymbooker import db
from ucdgymbooker.helpers import timezone_converter
from ucdgymbooker.models import Timeslot, Reservation, User

from ucdgymbooker.helpers import timezone_converter

import time

base_url = 'https://hub.ucd.ie/usis/W_HU_MENU.P_PUBLISH?p_tag=GYMBOOK'

#gets the reservations that fall within the time interval, update their status as well
#prepend admin reservations
def get_relevant_reservations():
    now = timezone_converter.get_current_utc_timestamp()
    lower_bound = timezone_converter.add_time(now, 3, 0)
    upper_bound = timezone_converter.add_time(now, 3, 20)

    #TODO is this also subordered by reservation priority?
    reservations = db.session.query(Reservation, Timeslot, User).join(Timeslot).join(User).filter(Timeslot.time <= upper_bound,  Timeslot.time >= lower_bound, Reservation.status=='Booked').order_by(User.admin.desc(), Reservation.reservation_time)




    #TODO check whether this does sth or not
    for reservation, timeslot, user in reservations:
        reservation.status = 'Processing'
    db.session.commit()

    return reservations

#returns poolside and/or performance gym urls in dict
#TODO trycatch
def get_confirm_urls(hourstring):
    return {}

#try to confim one specific reservation, returns True if success
def confirm_reservation(id, url):
    #TODO cookies, provide cursor as well
    return True

#TODO probably not used
#update status of all reservations in the DB, is separate from confirm_reservations for efficiency reasons
def update_status():
    print('lala')


reservations = get_relevant_reservations()

if reservations.count() > 0:
    # get the time when all reservations need to be done, normally all reservations within a 20 minute interval should have the same time
    # so getting the time from the first timeslot object in the first reservation should be ok
    goal_time = reservations[0][1].time
    current_time = timezone_converter.get_current_utc_timestamp()

    #polling wait
    while current_time < goal_time:
        time.sleep(0.1)
        current_time = timezone_converter.get_current_utc_timestamp()

    hourstring = timezone_converter.get_time_string(goal_time)
    urls = get_confirm_urls()

    poolside_available = True
    performance_available = True

    previous_successful = False

    #TODO primary secondary als current priority is 2

    #go over all reservations, try to book them as long as previous booking for the same gym was successful, skip over the confirmation otherwise (status is set as 'Failed' then also)
    #if priority is 2 it also checks whether or not the primary reservation (previous element in list) succeeded or not
    for reservation, timeslot, user in reservations:
        if reservation.priority == 2 and previous_successful:
            reservation.status = 'Primary booked successfully'
            previous_successful = False
            continue

        success = False

        if  poolside_available and timeslot.gym == 'Poolside':
            success = confirm_reservation(user.username, urls['Poolside'])
            poolside_available = success

        if performance_available and timeslot.gym == 'Performance' :
            success = confirm_reservation(user.username, urls['Performance'])
            poolside_available = success

        if success:
            reservation.status = 'Success'
        else:
            reservation.status = 'Failed'

        previous_successful = success





    db.session.commit()






'''
First thing it does is changing status in db
That way when new script starts while current script is running, nothing is screwed up

Run script every 15 min, it is responsible for time interval between now and now plus 20 minutes



'''

