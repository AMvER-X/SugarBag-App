########################################################################################################################
#           INITIAL START AND DATA OPEN
########################################################################################################################

import pandas as pd
import datetime as dt
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

########################################################################################################################
#           MAIN 
########################################################################################################################

"""
Graph 
"""
def main():
    data_SB =merger()

    #x = data_SB.loc[:,('dc500-540f',"day_name" )] #not formatted correctly
    x = data_SB['fpc-da3a']["Date"]
    y = data_SB['fpc-da3a']["nonNegDigActivity"]
    #print(x)
    #print(y)
    plotting(x,y)

"""
*compare mean time of day 
*compare day of week
*compare specific day mean

"""   
########################################################################################################################
#           OPEN AND REMOVE UNNECESSARY DATA
########################################################################################################################
""" please update these as reqired
"""

def open_and_clean_Weather(): #not opertaional
    df =sugar_bag_data["weather_station"]
    df.drop(columns = ["airTemperatureDiff","atmosphericPressureDiff","gustSpeedDiff","relativeHumidityDiff","windSpeedDiff","windDirectionDiff"],inplace= True)
    return df

def open_and_clean_WIFI(): #not operational
    df =sugar_bag_data["wifi_counter"]
    df.drop(columns = ["newDiff","currentDiff","total"],inplace= True)
    return df

def open_and_clean_OBJ():
    df =sugar_bag_data["object_detection"]
    #df.drop(columns = [""],inplace= True)
    return df

def open_and_clean_IRBD():
    df =sugar_bag_data["infrared_bi_directional"]
    df.drop(columns = ["battery","count1","count2","activity"],inplace= True)
    return df

def open_and_clean_IRC():
    df =sugar_bag_data["infrared_counters"]
    df.drop(columns = ["battery","peopleCount"],inplace= True)
    return df

def open_and_clean_VC(): #not operational
    df =sugar_bag_data["'vibration_counters'"]
    df.drop(columns = [""],inplace= True)
    return df

########################################################################################################################
#           Transfer data into one dictionry
########################################################################################################################

""" Merge the data into usable dictionary
Status : WORKING With limited data on dictionary
"""
def merger():
    '''
    weather = open_and_clean_Weather()
    format_DT(weather)
    weather_Clean = daily_totals(weather)
    print(weather_Clean)
    

    WIFI = open_and_clean_WIFI()
    format_DT(WIFI)
    WIFI_Clean = daily_totals(WIFI)
    

    OBJ not currently formatted correctly
    OBJ = open_and_clean_OBJ()
    format_DT(OBJ)
    OBJ_Clean = daily_totals(OBJ)
    print(OBJ_Clean)
    '''
    IRBD = open_and_clean_IRBD()
    format_DT(IRBD)
    IRBD_Clean = daily_totals(IRBD)
    print(IRBD_Clean)

    IRC = open_and_clean_IRC()
    format_DT(IRC)
    IRC_Clean = daily_totals(IRC)
    
    """add names once formatted"""
    device_list = IRBD_Clean|IRC_Clean
    return device_list

########################################################################################################################
#           Data cleaning
########################################################################################################################

'''seperate the different devices into different columns.

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


'''ensures datetime is a value and readable

STATUS: WORKING
'''
def format_DT(df):
     
    df['datetime'] = pd.to_datetime(df['datetime'])
    #df['Date']= pd.to_datetime(df['datetime']).dt.date
    #print(df["Date"].head())

    return df

def get_date(df):

    df['Date']= pd.to_datetime(df['datetime']).dt.date
    #print(df["Date"].head())


"""Merges the columns based on the date, and sums each column for every day. 
works with dictionary

STATUS: WORKING
"""
def daily_totals(df):
    devices_inDict =seperate_devices(df)
    dict_key = list(devices_inDict.keys())
    daily = {}

    for device_name in dict_key:  
        total_PDay = devices_inDict[device_name].set_index('datetime').groupby(pd.Grouper(freq="D")).sum() #groups by the calander date'
        total_PDay['Date'] = total_PDay.index
        total_PDay["day_name"] = total_PDay["Date"].dt.day_name()
        daily[device_name]= total_PDay 

    
        #print(daily[device_name])
    
    return daily

"""merges cells based on the date by the frequency given in 'letter'
uses the grouper function's frequency 

STATUS: ASSUMED WORKING
"""
def totals(df,letter):
    devices_inDict =seperate_devices(df)
    dict_key = list(devices_inDict.keys())
    new = {}

    for i in dict_key:  
        total_PDay = devices_inDict[i].set_index('datetime').groupby(pd.Grouper(freq=letter)).sum() #groups by the calander date'
        total_PDay['Date'] = total_PDay.index
        total_PDay["day_name"] = total_PDay["Date"].dt.day_name()
        new[i]= total_PDay 
        #print(new[i])
    print(new)
    return new

"""get a subplot based off the chosen day of the week

STATUS: INCOMPLETE
"""
def specific_day(df, day):
    df.drop(df[~(df['day_name'] == day)].index)
    print("new day column")
    print(df.head())
    return df

"""
Determine which Trails are being used and have the highest frequency using the Infared sensors

"""

###############################
#       Plotting data
###############################


'''basic plotting function'''
def plotting(x, y, xlab ='x - axis', ylab ='y - axis', title='Graph Title'):
    
    plt.plot(x,y)       #plot the x and y values given
    plt.xlabel(xlab)    #lable the x vaule, a given value or default 'x - axis'
    plt.ylabel(ylab)    #lable the y vaule, a given value or default 'y - axis'
    plt.title(title)    #lable the graph, a given value or default 'Graph Title'
    plt.show()          #prints the graph in a window
    return 


main()