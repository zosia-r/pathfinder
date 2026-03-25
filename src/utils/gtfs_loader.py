import pandas as pd
from datetime import datetime
from src.utils.time import time_to_seconds

class GTFSLoader:
    def __init__(self, data_path='./data/'):
        self.data_path = data_path
        self.calendar_dates = None
        self.calendar = None
        self.routes = None
        self.stop_times = None
        self.stops = None
        self.trips = None

    def load_all(self, target_date=None):
        """Loads all GTFS data and filters it based on the target date."""
        if target_date is None:
            target_date = datetime.now().strftime('%Y%m%d')
            
        self.calendar_dates = pd.read_csv(self.data_path + 'calendar_dates.txt', dtype={'date': str})
        self.calendar = pd.read_csv(self.data_path + 'calendar.txt', dtype={'start_date': str, 'end_date': str})
        self.routes = pd.read_csv(self.data_path + 'routes.txt', dtype={'route_id': str})
        self.stop_times = pd.read_csv(self.data_path + 'stop_times.txt', dtype={'stop_id': str})
        self.stops = pd.read_csv(self.data_path + 'stops.txt', dtype={'stop_id': str, 'parent_station': str})
        self.trips = pd.read_csv(self.data_path + 'trips.txt', dtype={'route_id': str})

        # get active services for given date
        active_services = self.get_active_services(target_date)

        # filter trips based on active services
        self.trips = self.trips[self.trips['service_id'].isin(active_services)]

        # fill missing parent_station with stop_id
        self.stops["parent_station"] = self.stops["parent_station"].fillna(self.stops["stop_id"])
        
        # filter and prepare stop_times
        self.stop_times = self.stop_times[self.stop_times['trip_id'].isin(self.trips['trip_id'])]
        self.stop_times['arr_sec'] = self.stop_times['arrival_time'].apply(time_to_seconds)
        self.stop_times['dep_sec'] = self.stop_times['departure_time'].apply(time_to_seconds)

        # sort stop times for easier processing
        self.stop_times = self.stop_times.sort_values(['trip_id', 'stop_sequence'])

    def get_active_services(self, date_str):
        """Returns a set of active service_ids for the given date."""
        date_obj = datetime.strptime(date_str, '%Y%m%d')
        day_name = date_obj.strftime('%A').lower()

        # check date range in calendar.txt
        mask = ((self.calendar['start_date'] <= date_str) &
               (self.calendar['end_date'] >= date_str) &
               (self.calendar[day_name] == 1))
        services = set(self.calendar.loc[mask, 'service_id'])
        
        # check exceptions in calendar_dates.txt
        exceptions = self.calendar_dates[self.calendar_dates['date'] == date_str]
        for _, row in exceptions.iterrows():
            if row['exception_type'] == 1:  # service added
                services.add(row['service_id'])
            elif row['exception_type'] == 2:  # service removed
                services.discard(row['service_id'])
        
        return services