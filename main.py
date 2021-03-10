import os
import re
from glob import iglob
import pandas as pd
from matplotlib import pyplot as plt
from datetime import datetime, timedelta
import folium
import matplotlib.dates as mdates

TIMEFRAME = [12, 1]

PLOTS_DIR = 'plots'
DATA_DIR = 'data'
DATA_OUTPUT_DIR = 'data_out'
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
    df.sort_index(inplace=True)

    return df


def plot_observations(sensor_id):
    obs = load_observations(sensor_id)
    obs.to_csv(os.path.join(DATA_OUTPUT_DIR, f'{sensor_id}' + '.csv'))

    for t_idx, t in enumerate(TIMEFRAME):

        fig, ax = plt.subplots()
        obs = obs[datetime.now() - timedelta(hours=t):datetime.now()]

        if obs.empty:
            return False

        hours_fmt = mdates.DateFormatter('%H:%M')

        ax.plot(obs.index, obs.light_value, c=LIGHT_VALUE_COLOR)
        ax.xaxis.set_major_formatter(hours_fmt)
        ax.set_ylabel('Lichtwaarde (Lux)')
        ax.yaxis.label.set_color(LIGHT_VALUE_COLOR)
        ax.set_title(f'Lichtwaardes sensor {sensor_id} afgelopen {t} uur')

        ax2 = ax.twinx()
        ax2.scatter(obs.index, obs.is_open, s=3,  c=IS_OPEN_COLOR)
        ax2.set_ylabel('Open/Dicht')
        ax2.set_yticks(ticks=[0, 1])
        ax2.set_yticklabels(['Dicht', 'Open'])
        ax2.yaxis.label.set_color(IS_OPEN_COLOR)
        ax2.xaxis.set_major_formatter(hours_fmt)

        fig.autofmt_xdate()
        plt.savefig(os.path.join(PLOTS_DIR, str(sensor_id) + f'_{t}' + '.jpg'))

    return True


if __name__ == "__main__":
    TIMEFRAME.sort(reverse=True)

    os.makedirs(PLOTS_DIR, exist_ok=True)
    os.makedirs(DATA_OUTPUT_DIR, exist_ok=True)

    location_data_path = os.path.join(DATA_DIR, LOCATION_DATA_FILENAME)
    location_data = pd.read_csv(location_data_path, index_col='sensor')

    m = folium.Map()

    sw = [None, None]
    ne = [None, None]

    for sensor_id in location_data.index:

        if not plot_observations(sensor_id):
            continue

        popup_html = ''
        for t in TIMEFRAME:
            plot_file = PLOTS_DIR + '/' + str(sensor_id) + f'_{t}' + '.jpg'
            popup_html += f'<img src="{plot_file}"><br>'

        popup_html += f'<a href="{DATA_OUTPUT_DIR}/{sensor_id}.csv">Download</a>'
        latitude = location_data.loc[sensor_id].breedte
        longitude = location_data.loc[sensor_id].lengte

        if sw[0] is None:
            sw = [latitude, longitude]
            ne = [latitude, longitude]
        else:
            if latitude < sw[0]:
                sw[0] = latitude
            if latitude > ne[0]:
                ne[0] = latitude
            if longitude < sw[1]:
                sw[1] = longitude
            if longitude > ne[1]:
                ne[1] = longitude

        marker = folium.Marker((latitude, longitude), popup=popup_html)
        marker.add_to(m)

    m.fit_bounds([sw, ne])

    m.save(MAP_FILENAME)
