import os
import re
from glob import iglob
import pandas as pd
from matplotlib import pyplot as plt
from datetime import datetime, timedelta
import folium
import matplotlib.dates as mdates

PLOTS_DIR = 'plots'
DATA_DIR = 'data'
LOCATION_DATA_FILENAME = 'birdhouse.txt'
MAP_FILENAME = 'index.html'

LIGHT_VALUE_COLOR = 'blue'
IS_OPEN_COLOR = 'red'


def load_observations(id):
    """
    Loads all observations of a given sensor.

    :param id: int with sensor id
    :return: pandas dataframe with all observations
    """
    files = iglob(os.path.join(DATA_DIR, '**', f'*{id}.csv'), recursive=True)

    today = datetime.now()
    yesterday = today - timedelta(days=1)

    files = [f for f in files if re.search(fr'{today.year}-0?{today.month}-0?{today.day}', f) or re.search(fr'{yesterday.year}-0?{yesterday.month}-0?{yesterday.day}', f)]

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
    fig, ax = plt.subplots()

    obs = load_observations(sensor_id)

    hours = mdates.HourLocator()
    hours_fmt = mdates.DateFormatter('%H:%M')

    ax.plot(obs.index, obs.light_value, c=LIGHT_VALUE_COLOR)
    ax.xaxis.set_major_locator(hours)
    ax.xaxis.set_major_formatter(hours_fmt)
    ax.set_ylabel('Lichtwaarde (Lux)')
    ax.yaxis.label.set_color(LIGHT_VALUE_COLOR)
    ax.set_title(f'Lichtwaardes sensor {sensor_id}')

    ax2 = ax.twinx()
    ax2.step(obs.index, obs.is_open, c=IS_OPEN_COLOR)
    ax2.set_ylabel('Open/Dicht')
    ax2.set_yticks(ticks=[0, 1])
    ax2.set_yticklabels(['Dicht', 'Open'])
    ax2.yaxis.label.set_color(IS_OPEN_COLOR)
    ax2.xaxis.set_major_locator(hours)
    ax2.xaxis.set_major_formatter(hours_fmt)

    fig.autofmt_xdate()
    plt.savefig(os.path.join(PLOTS_DIR, str(sensor_id) + '.jpg'))
    plt.show()


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
