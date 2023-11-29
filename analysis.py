from argparse import ArgumentParser
from dateutil import parser as par
import datetime as dt
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

import dateparser
import ipdb

class MotivData:
    """
    Here is what is included.
        1. The files we sent them, which represent one day of data for solar and load.  The times in these files are in local times.  
            The dates are irrelevant, only the times are relevant.  So for an entry like 2023-01-01 01:36:00,2000000  if the API is 
            queried at 0136 PST we should get back a load value of 2000000 
        2. A directory of API queries.  In the second directory is a bunch of files.  Each one is a json object, and includes the UTC 
            time that the api call was made as well as the api_response.  I called it every minute for a few hours. 
        3. A copy of the script I used.  It cannot run standalone, and is included only for reference. But that’s how the files were generated. 

    The mission here is to replot the synthetic data we sent them, and then to look at the responses and make sure we know how to pull out the load 
    and solar from this set of files, which SHOULD correspond to the original files we sent them.
    """

    def __init__(self, data_path):
        self.data_path = data_path

    def get_file_paths(self):
        rootdir = os.getcwd()
        destdir = os.path.join(rootdir, self.data_path)
        for file in os.listdir(destdir):
            if file == 'api_responses' and os.path.isdir(os.path.join(destdir, file)):
                api_responses = os.path.join(destdir, file) 
            if file == 'data_we_gave_to_motiv' and os.path.isdir(os.path.join(destdir, file)):
                data_we_gave_to_motiv = os.path.join(destdir, file)

        paths = (api_responses, data_we_gave_to_motiv)
        
        if len(paths) < 2:
            raise Exception("One of the data paths is missing.")
        
        self.api_responses_path = paths[0]
        self.data_we_gave_to_motiv_path = paths[1]

    def process_single_api_response(self, contents):
        row = {}
        local_query_time = contents['timestamp']
        api_response = contents['api_response']
        row['api_return_time'] = api_response['Timestamp']

        for variable in self.api_response_df.columns[4:]:
            temp = api_response.get(variable)
            match variable:
                case 'ChargeDischargeCounter':
                    row[variable] = [str(tuple(temp.values()))]
                case '1MinPVAverager':
                    row[variable] = [temp.get('Averager')]
                case 'BatteryMeter':
                    row[variable] = [temp.get("ACPowerWattsSigned")]
                case 'PrimaryGridMeter':
                    row[variable] = ["ACPowerWattsSigned"]
                case 'ArbiterPower':
                    row[variable] = [temp.get('SystemDirectorPowerRequest')]
                case 'PVChargeLimiter':
                    row[variable] = ["PVChargeLimitWatts"]
                case 'PVMeter':
                    row[variable] = [temp.get('ACPowerWattsSigned')]
                case 'Distributer1':
                    row[variable] = [temp.get('AvailableCapacityWattHours')]
                case 'GEM100':
                    row[variable] = [temp.get('StateOfCharge')]
                case 'MaxAvgGrid':
                    row[variable] = [temp.get('MaxAverage')]
                case '1MinBatteryAverager':
                    row[variable] = [temp.get('Averager')]
                case 'DemandManagement1':
                    row[variable] = [temp.get('ClippingLevel')]
                case '15MinGridAverager':
                    row[variable] = [temp.get('Averager')]
                case '1MinGridLessBatteryAverager':
                    row[variable] = [str(tuple(temp.values()))]

        time_temp = dt.datetime.fromisoformat(row['api_return_time'])
        time_temp = time_temp - dt.timedelta(minutes=time_temp.minute % 1,
                             seconds=time_temp.second,
                             microseconds=time_temp.microsecond)
        time_temp = time_temp.strftime('%Y-%m-%dT%H:%M:%S.%fZ').split("T")[1]
        
        row['matched_timestamp'] = time_temp

        row['load'] = "WORK IN PROGRESS"
        row['solar'] = api_response['PVMeter']['ACPowerWattsSigned']     

        self.api_response_df = pd.concat([
            self.api_response_df, pd.DataFrame.from_dict(row)], 
            ignore_index=True)


    def collect_api_responses(self):
        """
        Think about the best way to store these responses. 
        """
        # Create a df instance variable to keep track of API response data that we need.
        self.api_response_df = pd.DataFrame(columns=[
            'api_return_time', 'matched_timestamp', 'load', 'solar', 'ChargeDischargeCounter', '1MinPVAverager', 'BatteryMeter', 'PrimaryGridMeter', 
            'ArbiterPower', 'PVChargeLimiter', 'PVMeter', 'Distributer1', 'GEM100', 'MaxAvgGrid', 
            '1MinBatteryAverager', 'DemandManagement1', '15MinGridAverager', '1MinGridLessBatteryAverager'
        ])

        for filename in os.listdir(self.api_responses_path):
            print(filename)
            filepath = os.path.join(self.api_responses_path, filename)
            file = open(filepath, '+r')
            contents = json.loads(file.read())
            self.process_single_api_response(contents)
        
        self.api_response_df['matched_timestamp_dt'] = self.api_response_df['matched_timestamp'].apply(lambda ts: par.parse(ts))
        self.api_response_df = self.api_response_df.set_index('matched_timestamp_dt')
        # self.api_response_df = self.api_response_df.drop(['matched_timestamp'], axis=1)
        self.api_response_df = self.api_response_df.sort_index()

    def convert_pst_string_to_utc_string(self, string):
        string = dateparser.parse(string)
        string = string.replace(tzinfo=dt.timezone(-dt.timedelta(hours=8)))
        string = string.astimezone(dt.timezone.utc)
        string = string.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        return string

    def collect_data_we_sent_to_motiv(self):
        for filename in os.listdir(self.data_we_gave_to_motiv_path):
            filepath = os.path.join(self.data_we_gave_to_motiv_path, filename)
            if 'load' in filepath:
                load = pd.read_csv(filepath, names=['timestamp', 'load'])
            elif 'pv' in filepath:
                pv = pd.read_csv(filepath, names=['timestamp', 'pv'])
        merged = load.merge(pv)

        # Convert PST timestamp strings to UTC ISO-8601 format timestamp strings
        merged.timestamp = merged.timestamp.apply(self.convert_pst_string_to_utc_string)

        # Keep only the time since the date is irrelevant
        # TODO: Should we remove the date since the date (YYYY-MM-DD) is just the current date?
        # TODO: This process is kind of slow
        merged.timestamp = merged.timestamp.apply(lambda utc_string: utc_string.split("T")[1])
        merged['timestamp_dt'] = merged.timestamp.apply(lambda ts: par.parse(ts))
        merged = merged.set_index('timestamp_dt').sort_index()
        merged = merged.drop(['timestamp'], axis=1)
        self.synthetic_load_pv = merged


    def preprocess_data(self):
        """
        Preprocess the data
        """

        # Get the file paths for the relevant data directories and set them as instance variables.
        self.get_file_paths()
        
        # Combine the load and pv data we sent to motive and save as a df as an instance variable.
        self.collect_data_we_sent_to_motiv()

        self.collect_api_responses()

        return

    def visualize_data(self):
        """
        Run visualizations.
        """



            
        
if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('data_path', default=os.getcwd(),
                        help='Relative filepath to a folder containing subdirectories called api_responses and data_we_gave_to_motiv')
    args = parser.parse_args()

    data_path = args.data_path

    motiv_data = MotivData(data_path=data_path)
    motiv_data.preprocess_data()

    motiv_data.api_response_df.to_csv('mined_motiv_response.csv')

    # TODO: join the synthetic data df's and the api processed data

    merged = pd.merge(motiv_data.synthetic_load_pv, motiv_data.api_response_df, how='inner', left_index=True, right_index=True)
    merged.to_csv("matched_system_response.csv")

    merged = merged[~merged.index.duplicated(keep='first')]

    # # Check missing datetime values
    # ipdb.set_trace()
    # test = merged.reindex(pd.date_range(min(merged.index), max(merged.index)), fill_value="NaN")
    # plt.plot(test.index.to_series())
    # plt.show()
    

