#import pytz
from datetime import datetime
from dateutil import tz

#all timezone stuff is put in the same file as creating bugs on accident is super easy

tz_ie = tz.gettz('Europe/Dublin')
tz_utc = tz.gettz('Etc/UTC')

def get_current_utc_timestamp():
    return datetime.now().astimezone(tz_utc)

def create_ie_timestamp(year, month, day, hour, minute):
    return datetime(year, month, day, hour, minute, 0, 0, tz_ie)

def create_utc_timestamp(year, month, day, hour, minute):
    return datetime(year, month, day, hour, minute, 0, 0, tz_utc)

def utc_to_ie(time):
    return time.astimezone(tz_ie)

def ie_to_utc(time):
    return time.astimezone(tz_utc)

#quick sanity check function
def checker_timezones():
    timestamp = create_ie_timestamp(2022, 1, 12, 6, 0)
    # timestamp2 = timestamp.replace(tzinfo=pytz.utc)
    timestamp2 = ie_to_utc(timestamp)
    print("both should be the same, Irish winter time is the same as UTC")
    print(timestamp)
    print(timestamp2)

    # utc to dublin
    timestamp3 = create_utc_timestamp(2022, 1, 12, 6, 0)
    # timestamp2 = timestamp.replace(tzinfo=pytz.utc)
    timestamp4 = utc_to_ie(timestamp3)
    print("both should be the same, Irish winter time is the same as UTC")
    print(timestamp3)
    print(timestamp4)


    timestamp = create_ie_timestamp(2022, 6, 12, 6, 0)
    # timestamp2 = timestamp.replace(tzinfo=pytz.utc)
    timestamp2 = ie_to_utc(timestamp)
    print("top is Irish in summer time, should be one hour more")
    print(timestamp)
    print(timestamp2)

    # utc to dublin
    timestamp3 = create_utc_timestamp(2022, 6, 12, 6, 0)
    # timestamp2 = timestamp.replace(tzinfo=pytz.utc)
    timestamp4 = utc_to_ie(timestamp3)
    print("bottom is Irish in summer time, should be one hour more")
    print(timestamp3)
    print(timestamp4)

    print("should be current time with UTC specification")
    print(get_current_utc_timestamp())


#checker_timezones()
#test


'''
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

'''