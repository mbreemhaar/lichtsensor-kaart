import os
import re
from glob import iglob
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from datetime import datetime
import folium

PLOTS_DIR = 'plots'
DATA_DIR = 'data'
LOCATION_DATA_FILENAME = 'birdhouse.txt'
MAP_FILENAME = 'index.html'


def load_observations(id):
    """
    Loads all observations of a given sensor.

    :param id: int with sensor id
    :return: pandas dataframe with all observations
    """
    files = iglob(os.path.join(DATA_DIR, '**', f'*{id}.csv'), recursive=True)

    today = datetime.now()
    year = today.year
    month = today.month
    day = today.day

    files = [f for f in files if re.search(fr'{year}-0?{month}-0?{day}', f)]

    names = ['time', 'sensor_id', 'light_value', 'is_open', 'temp']

    df = pd.DataFrame(columns=names)
    for f in files:
        print(f'Loading file {f}')
        file_data = pd.read_csv(f, delimiter=';', header=0, names=names, parse_dates=['time'])

        # Replace Pandas inferred date (today) by date from filename
        date_match = re.search(r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})', f)
        year = int(date_match.group('year'))
        month = int(date_match.group('month'))
        day = int(date_match.group('day'))
        file_data['time'] = [timestamp.replace(year=year, month=month, day=day) for timestamp in file_data['time']]
        df = df.append(file_data, ignore_index=True)

    df.set_index('time', drop=True, inplace=True)

    return df


def plot_observations(sensor_id):
    obs = load_observations(sensor_id)
    
    time = obs.index
    time_labels = np.array([datetime.strftime(t, '%H:%M') for t in time])
    idx = np.round(np.linspace(0, len(time) - 1, 5)).astype(int)
    time_labels = time_labels[idx]

    light_value = obs['light_value']

    plt.plot_date(range(len(time)), light_value, '-')
    plt.xticks(idx, time_labels)
    plt.savefig(os.path.join(PLOTS_DIR, str(sensor_id) + '.jpg'))


if __name__ == "__main__":
    os.makedirs(PLOTS_DIR, exist_ok=True)

    location_data_path = os.path.join(DATA_DIR, LOCATION_DATA_FILENAME)
    location_data = pd.read_csv(location_data_path, index_col='sensor')

    m = folium.Map()

    for sensor_id in location_data.index:
        plot_observations(sensor_id)

        plot_file = PLOTS_DIR + '/' + str(sensor_id) + '.jpg'

        latitude = location_data.loc[sensor_id].breedte
        longitude = location_data.loc[sensor_id].lengte
        marker = folium.Marker((latitude, longitude), popup=f'<img src="{plot_file}">')
        marker.add_to(m)

    m.save(MAP_FILENAME)
