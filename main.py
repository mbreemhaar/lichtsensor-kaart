import os
import re
from glob import iglob
import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from datetime import datetime


def load_observations(id):
    """
    Loads all observations of a given sensor.

    :param id: int with sensor id
    :return: pandas dataframe with all observations
    """
    files = iglob(os.path.join('data', '**', f'*{id}.csv'), recursive=True)
    names = ['time', 'sensor_id', 'light_value', 'is_open', 'temp']

    df = pd.DataFrame(columns=names)
    for f in files:
        file_data = pd.read_csv(f, delimiter=';', header=0, names=names, parse_dates=['time'])

        # Replace Pandas inferred date (today) by date from filename
        date_match = re.search(r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})', f)
        year = int(date_match.group('year'))
        month = int(date_match.group('month'))
        day = int(date_match.group('day'))
        file_data['time'] = [timestamp.replace(year=year, month=month, day=day) for timestamp in file_data['time']]

        df = df.append(file_data, ignore_index=True)

    return df


def plot_observations(obs):
    time = obs.time
    time_labels = np.array([datetime.strftime(t, '%H:%M') for t in time])
    idx = np.round(np.linspace(0, len(time) - 1, 5)).astype(int)
    time_labels = time_labels[idx]

    light_value = obs['light_value']

    plt.plot_date(range(len(time)), light_value, '-')
    plt.xticks(idx, time_labels)
    plt.show()


if __name__ == "__main__":
    location_data_path = os.path.join('data', 'birdhouse.txt')
    location_data = pd.read_csv(location_data_path)

    for sensor_id in location_data.sensor:
        observations = load_observations(sensor_id)
        print(observations)
