import pandas as pd
from datetime import datetime as dt
from clean_sb_data import device_dict, clean_data, trail_info, local_time


##### Time Manipulation ###

"""Change the date or time
a string value that is formatted like the date, time, or both 
0000-00-00 00:00:00
STATUS: WORKING 
"""
def set_datetime(time):
    global local_time

    if is_valid_datetime(time) == True:
        time = pd.to_datetime(time)
        time = remove_minsec(time)
        local_time = time
    elif is_valid_date(time) == True:
        time = pd.to_datetime(time)
        date_part = time.date()
        time_part = local_time.time()
        local_time =dt.combine(date_part, time_part)
    elif is_valid_time(time) == True:
        time = pd.to_datetime(time)
        time = remove_minsec(time) #remove min and sec as the dataframes only occour in hours
        date_part = local_time.date()
        time_part = time.time()
        local_time =dt.combine(date_part, time_part)
        
    else:
        print("""there is an error with your date imput. 
no changes made""")
        

"""Validates the given date, time, or both
STATUS: WORKING""" 
def is_valid_datetime(date_time, format="%Y-%m-%d %H:%M:%S"):
    #date_timestr =date_time.strftime('%Y-%m-%d %H:%M:%S')
    try:
        # Try to parse the datetime string with the given format
        dt.strptime(date_time, format)
        return True
    except ValueError:
        return False
        
def is_valid_date(date, format="%Y-%m-%d"):
    #datestr =date.strftime('%H:%M:%S')
    try:
        # Try to parse the datetime string with the given format
        dt.strptime(date, format)
        return True
    except ValueError:
        return False
    
def is_valid_time(time, format="%H:%M:%S"):
    #timestr =time.strftime('%H:%M:%S') #converts the timestamp into a string 
    try:
        # Try to parse the datetime string with the given format
        dt.strptime(time, format)
        return True
    except ValueError:
        return False


"""function to remove min and second from the time stamp
STATUS : WORKING
"""
def remove_minsec(time):
    no_minsec = time.replace(minute=0, second=0)

    return no_minsec



#### Maintenance update ###
"""update the maintenance date to the current date when work is done
for test cases, random dates will be added so"""
def update_maintenance(trail, time = local_time): #time is default set to the local time, may be changed for simulation
    global trail_info
    newtime = pd.to_datetime(time)

    #update the maintenance time
    trail_info.loc[trail_info["Name"] == trail, "Last_Maintenance"] = newtime
    

"""Get how many riders have used the trail since the last maintenance work """
def get_trailuse(trail, time = local_time):
    
    currentTime = pd.to_datetime(time)

    #get the time when the trail was last worked on
    last_maintenance = trail_info.loc[trail_info["Name"] == trail, "Last_Maintenance"].values[0]
    last_maintenance =pd.to_datetime(last_maintenance)

    #open the df of the device that is at located at the trailhead
    data = device_dict()
    trail_dev = trail_info.loc[trail_info["Name"] == trail, "Device"].values[0]
    data = data[trail_dev]

    #sets the column based on the device 
    if  "dc500" in trail_dev:
        column = "peopleCount"
    if "fpc" in trail_dev:
        if trail == "Golden Rough" or "Playground":
            column = "count2"
        else:
            column = "count1"
        
    # works for vibration sensors, gets the 
    before = data.loc[data["datetime"]==last_maintenance,column].values[0]
    after = data.loc[data["datetime"]==currentTime,column].values[0]
    use =  after - before 
    #print("before =" , before, "after=",after  )
    return use

    #people count@ local time - peoplecount@last maintenance = wear


##### PARK population per hour ####

'''Gives the total number of users who are connected to the wifi sensor
Used as the number of riders in the park per hour'''
def total_riders(): 
    global local_time
    data = clean_data()
    wificounter = data["wifi_counter"] # the df with the number of devices connected

    if local_time < pd.to_datetime("2024-03-01 00:00:00"): #this negates a time error found before this date
        edited_time = local_time + pd.DateOffset(hours= 14)
    else:
        edited_time = local_time
        
    #get the current users. "current" or "total" to be used, total sometimes reather high and unsure if this is correct
    current_users = wificounter.loc[wificounter["datetime"] ==edited_time, "current"].values[0] 
    print("there are approx.", current_users, "people in the park")
    return current_users

#### TRAIL population

"""gets how many riders have been on the trail in the last hour
STATUS WORKING - not every trail has the an iot device 
"""
def get_trail_numbers(trail_name): 

    time = local_time
    trail_device = trail_info.loc[trail_info["Name"]== trail_name,"Device"].values[0]
    trail_count = trail_info.loc[trail_info["Name"]== trail_name,"Counter"].values[0]
    data = device_dict()
    iotdevice = data[trail_device]

    no_riders = iotdevice.loc[iotdevice["datetime"] ==time, trail_count].values[0]
    print("there are approx.", no_riders, "people on:", trail_name)
    return no_riders

