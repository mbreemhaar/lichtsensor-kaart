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
IMG_DIR = 'photo'
LOCATION_DATA_FILENAME = 'birdhouse.txt'
MAP_FILENAME = 'index.html'

ALLOW_MISSING_DATA = True


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

def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.values():
        sp.set_visible(False)


def plot_observations(sensor_id):
    datestring = datetime.now().strftime('%Y%m%d')

    obs = load_observations(sensor_id)
    obs.to_csv(os.path.join(DATA_OUTPUT_DIR, f'{datestring}_{sensor_id}' + '.csv'))

    for t_idx, t in enumerate(TIMEFRAME):
        obs = obs[datetime.now() - timedelta(hours=t):datetime.now()]

        if obs.empty and not ALLOW_MISSING_DATA:
            return False

        fig, host = plt.subplots()
        fig.subplots_adjust(right=0.75)

        par1 = host.twinx()
        par2 = host.twinx()

        par2.spines["right"].set_position(("axes", 1.2))
        make_patch_spines_invisible(par2)
        par2.spines["right"].set_visible(True)

        p1, = host.plot(obs.index, obs.light_value, 'b-', label="Lichtwaarde (Lux)")
        p2, = par1.plot(obs.index, obs.is_open, 'r-', label="Open/Dicht")
        p3, = par2.plot(obs.index, obs.temp, 'g-', label="Temperatuur")

        hours_fmt = mdates.DateFormatter('%H:%M')
        host.xaxis.set_major_formatter(hours_fmt)
        par1.xaxis.set_major_formatter(hours_fmt)
        par2.xaxis.set_major_formatter(hours_fmt)

        par1.set_yticks(ticks=[0, 1])
        par1.set_yticklabels(['Dicht', 'Open'])

        host.set_xlabel("Tijd")
        host.set_ylabel("Lichtwaarde (Lux)")
        par1.set_ylabel("Open/Dicht")
        par2.set_ylabel("Temperatuur")

        host.yaxis.label.set_color(p1.get_color())
        par1.yaxis.label.set_color(p2.get_color())
        par2.yaxis.label.set_color(p3.get_color())

        fig.autofmt_xdate()

        host.set_title(f'Sensor {sensor_id}, afgelopen {t} uur')

        plt.savefig(os.path.join(PLOTS_DIR, f'{datestring}_{sensor_id}_{t}.jpg'))
        plt.close()

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

    datestring = datetime.now().strftime('%Y%m%d')

    for sensor_id in location_data.index:

        if not plot_observations(sensor_id):
            continue

        plot_file = PLOTS_DIR + '/' + f'{datestring}_{sensor_id}_{TIMEFRAME[0]}.jpg'
        popup_html = f'<img src="{plot_file}">'

        for t in TIMEFRAME[1:]:
            plot_file = PLOTS_DIR + '/' f'{datestring}_{sensor_id}_{t}.jpg'
            popup_html += f'<br><a href="{plot_file}">Laatste {t} uur</a>'

        popup_html += f'<br><a href="{DATA_OUTPUT_DIR}/{datestring}_{sensor_id}.csv">Download data</a>'

        img_filename = location_data.loc[sensor_id].photo

        if type(img_filename) == str:
            popup_html += f'<br><a href="{IMG_DIR}/{img_filename}">Locatie</a>'

        latitude = location_data.loc[sensor_id].breedte
        longitude = location_data.loc[sensor_id].lengte
        color = location_data.loc[sensor_id].kleur

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

        marker = folium.Marker((latitude, longitude), popup=popup_html, icon=folium.Icon(color=color))
        marker.add_to(m)

    m.fit_bounds([sw, ne])

    m.save(MAP_FILENAME)
