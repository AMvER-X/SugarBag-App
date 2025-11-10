import pandas as pd
from datetime import datetime as dt
import matplotlib.pyplot as plt

file_paths_sugar_bag = {
    'weather_station': './SugarBag/SugarBagRd_Atmos_Aggregated.csv',
    'wifi_counter': './SugarBag/SugarBagRd_NCount_Aggregated.csv',
    'object_detection': './SugarBag/Alpha_X_Aggregated.csv',
    'infrared_bi_directional': './SugarBag/SugarBagRd_Farmo_Aggregated.csv',
    'infrared_counters': './SugarBag/SugarBagRd_DingTek_Aggregated.csv',
    'vibration_counters': './SugarBag/SugarBagRd_R718mbb_Aggregated.csv'

}

def load_dataset(file_path):
    return pd.read_csv(file_path)

sugar_bag_data = { sensor: load_dataset(path) for sensor, path in file_paths_sugar_bag.items()}

local_time = pd.to_datetime("2024-01-21 10:00:00")

trail_info = pd.DataFrame({"Name":["Aero","Bees Knees","Black Schute","Boner log line","Bottom Powerline Access Trail","Fantales","Golden Rough","Honeycomb","Milky Way","Party mix","Playground","Playground climb trail","Rocky Road","Sour Power","Sweet Sugar","Syrup","The Drop In Clinic","Willy Wonka"],
                               "Difficulty":["Double Black","Blue","Black","Black","Green","Green","Black","Blue","Green","Green","Double Black","Blue","Black","Green","Blue","Blue","Double Black","Blue"],
                               "TrailType":["Freeride","Freeride","Shortcut","Shortcut","Access Trail","Freeride","Freeride","Freeride","Access Trail","Freeride","Freeride/Multiline","Access Trail","Freeride","Access Trail","Freeride","Freeride","Freeride","Freeride"],
                               "Device":["NA","dc500-385c","dc500-4402","NA","NA","NA","fpc-4f48","NA","fpc-4f48","dc500-540f","fpc-da3a","NA","NA","fpc-da3a","NA","fpc-7559","NA","NA"],
                               "Counter":["NA","nonNegPeopleCount","nonNegPeopleCount","NA","NA","NA","nonNegDifCount2","NA","nonNegDifCount1","nonNegPeopleCount","nonNegDifCount2","NA","NA","nonNegDifCount1","NA","nonNegDifCount1","NA","NA"],
                               "Last_Maintenance":["2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00","2023-05-06 00:00:00"],
                               "Riders_since_Maintenace":["","","","","","","","","","","","","","","","","",""]})

#### CLEAN DATA ####
def open_and_clean_Weather():
    df =sugar_bag_data['weather_station']
    # Format time
    df['datetime'] = pd.to_datetime(df['datetime'])

    if df.isnull().values.any():
        df.ffill( inplace = True)

    # Drop unneeded columns
    if 'airTemeratureDiff' in df:
        df.drop(columns = ['airTemeratureDiff'], inplace = True)
    if 'atmosphericPressureDiff' in df:
        df.drop(columns = ['atmosphericPressureDiff'], inplace = True)
    if 'gustSpeedDiff' in df:
        df.drop(columns = ['gustSpeedDiff'], inplace = True)
    if 'relativeHumidityDiff' in df:
        df.drop(columns = ['relativeHumidityDiff'], inplace = True)
    if 'windSpeedDiff' in df:
        df.drop(columns = ['windSpeedDiff'], inplace = True)
    if 'windDirectionDiff' in df:
        df.drop(columns = ['windDirectionDiff'], inplace = True)
    if 'windDirection' in df:
        df.drop(columns = ['windDirection'], inplace = True)
    
    #Remove duplicate entries
    df = df.drop_duplicates()


    return df

def open_and_clean_WIFI(): 
    # open data
    df =sugar_bag_data['wifi_counter']
    # Formatting time
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Check if data frame has null values
    if df.isnull().values.any():
        df.ffill( inplace = True)

    # Drop uneeded columns
    if 'currentDiff' in df:
        df.drop(columns = ['currentDiff'], inplace = True)
    if 'newDiff' in df:
        df.drop(columns = ['newDiff'], inplace = True)
    if 'totalDiff' in df:
        df.drop(columns = ['totalDiff'], inplace = True)

    # Remove duplicate entries
    df = df.drop_duplicates()

    # Remove invalid entries
    for index, row in df.iterrows():
        if row['new'] < 0:
            df.loc[index, 'new'] = 0
        if row['current'] < 0:
            df.loc[index, 'current'] = 0
        if row['total'] < 0:
            df.loc[index, 'total'] = 0

    return df

def open_and_clean_OBJ(): 
    # open data
    df =sugar_bag_data['object_detection']
    # Formatting time
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Check if data frame has null values
    if df.isnull().values.any():
        df.ffill( inplace = True)

    # Drop uneeded columns
    if 'F1 - peopleLeft/Up' in df:
        df.drop(columns = ['F1 - peopleLeft/Up'], inplace = True)
    if 'F2 - peopleRight/Down' in df:
        df.drop(columns = ['F2 - peopleRight/Down'], inplace = True)
    if 'F9 - trucksLeft/Up' in df:
        df.drop(columns = ['F9 - trucksLeft/Up'], inplace = True)
    if 'F10 - trucksRight/Down' in df:
        df.drop(columns = ['F10 - trucksRight/Down'], inplace = True)
  

    # Remove duplicate entries
    df = df.drop_duplicates()

    # Remove invalid entries
    for index, row in df.iterrows():
        if row["F3 - bikesLeft/Up"] < 0:
            df.loc[index, 'F3 - bikesLeft/Up'] = 0
        if row['F4 - bikesRight/Down'] < 0:
            df.loc[index, 'F4 - bikesRight/Down'] = 0
        if row["F5 - carsLeft/Up"] < 0:
            df.loc[index, 'F5 - carsLeft/Up'] = 0
        if row['F6 - carsRight/Down'] < 0:
            df.loc[index, 'F6 - carsRight/Down'] = 0
        if row["F7 - busesLeft/Up"] < 0:
            df.loc[index, 'F7 - busesLeft/Up'] = 0
        if row['F8 - busesRight/Down'] < 0:
            df.loc[index, 'F8 - busesRight/Down'] = 0
        


    return df

def open_and_clean_IRBD():
    df =sugar_bag_data["infrared_bi_directional"]
    # Formatting time
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Check if data frame has null values
    if df.isnull().values.any():
        df.ffill( inplace = True)
    
    # Drop uneeded columns
    if 'battery' in df:
        df.drop(columns = ['battery'], inplace = True)
    #if 'count1' in df:
    #    df.drop(columns = ['count1'], inplace = True)
    #if 'count2' in df:
    #   df.drop(columns = ['count2'], inplace = True)
    if 'activity' in df:
        df.drop(columns = ['activity'], inplace = True)

    # Remove duplicate entries
    df = df.drop_duplicates()

    # Remove invalid entries and cap entries at 200
    for index, row in df.iterrows():
        if row['nonNegDifCount1'] < 0:
            df.loc[index, 'nonNegDifCount1'] = 0
        elif row['nonNegDifCount1'] > 200:
            df.loc[index, 'nonNegDifCount1'] = 200
        if row['nonNegDifCount2'] < 0:
            df.loc[index, 'nonNegDifCount2'] = 0
        elif row['nonNegDifCount2'] > 200:
            df.loc[index, 'nonNegDifCount2'] = 200
        if row['nonNegDigActivity'] < 0:
            df.loc[index, 'nonNegDigActivity'] = 0
        elif row['nonNegDigActivity'] > 200:
            df.loc[index, 'nonNegDigActivity'] = 200
        

    return df

def open_and_clean_IRC():
    df =sugar_bag_data["infrared_counters"]
    # Formatting time
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Check if data frame has null values
    if df.isnull().values.any():
        df.ffill( inplace = True)

    # Drop uneeded columns
    if 'battery' in df:
        df.drop(columns = ['battery'], inplace = True)
  
    # Remove duplicate entries
    df = df.drop_duplicates()

    # Remove invalid entries
    for index, row in df.iterrows():
        if row['peopleCount'] < 0:
            df.loc[index, 'peopleCount'] = 0
        if row["nonNegPeopleCount"] < 0:
            df.loc[index, 'nonNegPeopleCount'] = 0

    return df

def open_and_clean_VC(): 
    df =sugar_bag_data["'vibration_counters'"]

    # Formatting time
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Check if data frame has null values
    if df.isnull().values.any():
        df.ffill( inplace = True)

    # Drop uneeded columns
    if 'battery' in df:
        df.drop(columns = ['battery'], inplace = True)
    if 'batteryDiff' in df:
        df.drop(columns = ['batteryDiff'], inplace = True)
    if 'workCount' in df:
        df.drop(columns = ['workCount'], inplace = True)
        
    # Remove duplicate entries
    df = df.drop_duplicates()

    # Remove duplicate entries
    for index, row in df.iterrows():
        if row['workCountDiff'] < 0:
            df.loc[index, 'workCountDiff'] = 0

    return df

def open_and_clean_VC(): 
    df =sugar_bag_data["vibration_counters"]

    # Formatting time
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Check if data frame has null values
    if df.isnull().values.any():
        df.ffill( inplace = True)

    # Drop uneeded columns
    if 'battery' in df:
        df.drop(columns = ['battery'], inplace = True)
    if 'batteryDiff' in df:
        df.drop(columns = ['batteryDiff'], inplace = True)
    if 'workCount' in df:
        df.drop(columns = ['workCount'], inplace = True)
        
    # Remove duplicate entries
    df = df.drop_duplicates()

    # Remove duplicate entries
    for index, row in df.iterrows():
        if row['workCountDiff'] < 0:
            df.loc[index, 'workCountDiff'] = 0

    return df

#### DICTIONARY OF DATA
"""create a dictionary with all the devices as the keys"""
def device_dict():
    
    weather = open_and_clean_Weather()
    weather_Clean = seperate_devices(weather)
    
    WIFI = open_and_clean_WIFI()
    WIFI_Clean = seperate_devices(WIFI)
    
    OBJ = open_and_clean_OBJ()
    OBJ_Clean = seperate_devices(OBJ)
    
    IRBD = open_and_clean_IRBD()
    IRBD_Clean = seperate_devices(IRBD)

    IRC = open_and_clean_IRC()
    IRC_Clean = seperate_devices(IRC)
    
    """add names once formatted"""
    device_list = weather_Clean|WIFI_Clean|OBJ_Clean|IRBD_Clean|IRC_Clean
    
    return device_list

"""cleans the datatypes and puts them back in a dictionay"""
def clean_data():
    Weather = open_and_clean_Weather()

    WIFI = open_and_clean_WIFI()

    OBJ = open_and_clean_OBJ()

    IRBD = open_and_clean_IRBD()

    IRC = open_and_clean_IRC()

    VC = open_and_clean_VC()
    #Add the clean data back into a dictionary
    SB_Clean = {
    'weather_station': Weather,
    'wifi_counter':WIFI,
    'object_detection': OBJ,
    'infrared_bi_directional': IRBD,
    'infrared_counters': IRC,
    'vibration_counters': VC} 

    return SB_Clean


#### FORMAT DATA ####
"""find the distinct devices based on the dev_id

STATUS: WORKING
"""
def find_devices(df):
    dev_id_col = df["dev_id"]
    distinct_dev =[]

    for device in dev_id_col: 
        if device not in distinct_dev: 
            distinct_dev.append(device) 

    return distinct_dev

'''seperate the different devices into different dataframes.

STATUS: WORKING
'''
def seperate_devices(df):
    distinct =find_devices(df)
    split_list = {}

    for device in distinct:
        var_name = "%s" % device
        df_device = df.loc[df["dev_id"]==device].copy()
        df_device.drop(columns = ["dev_id"],inplace= True)
        split_list[var_name] = df_device
    
    #print("this is the fpc-6460 data ",split_list["fpc-6460"]) #check 
    return split_list

"""function to show from a selcected date for a given number of days, of a given datafrme

STATUS: WORKING
"""
def cut_view(df,start,span):
    start = pd.to_datetime(start)
    end = start + pd.DateOffset(days=span)
    #remove dates before
    filtered_df = df[df['datetime'] >= start]
    #remove dates after the given timeframe
    filtered_df = df[df['datetime'] <= end]

    return filtered_df

