from numpy import int64
from pandas import DataFrame, read_csv, to_datetime

data_frame = DataFrame()

for year in range(2015, 2019):
    df = read_csv('D:/Downloads/NAPMMU/Datasets/Pollution/measurements_' + str(year) + '.csv', sep=';')
    df.rename(columns={'DateTime': 'time'}, inplace=True)

    if year == 2018:
        formatTime = '%Y-%m-%d %H:%M:%S'
    else:
        formatTime = '%d/%m/%Y %H:%M'

    df['time'] = to_datetime(df['time'], format=formatTime).astype(int64) // 10 ** 9

    data_frame = data_frame.append(df, sort=True)

station_names = ['Centar', 'GaziBaba', 'Karpos', 'Kavadarci', 'Kicevo', 'Kocani', 'Kumanovo', 'Lisice', 'Miladinovci',
                 'Tetovo']
for station_name in station_names:
    df = data_frame[data_frame['StationName'] == station_name]
    df.drop(columns='StationName', inplace=True)
    df.to_csv('D:/Downloads/NAPMMU/Datasets/Pollution/pollution_report_' + station_name + '.csv', index=False)
