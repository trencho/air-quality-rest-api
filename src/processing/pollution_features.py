# -*- coding: utf-8 -*-
"""
Created on Sun Aug  4 19:17:14 2019

@author: atren
"""

import pandas as pd

station_names = ['Centar', 'GaziBaba', 'Karpos', 'Kavadarci', 'Kicevo', 'Kocani', 'Kumanovo', 'Lisice', 'Miladinovci',
                 'Tetovo']

for station_name in station_names:
    pollution_report = 'D:/Downloads/NAPMMU/Datasets/Pollution/pollution_report_' + station_name + '.csv'

    df = pd.read_csv(pollution_report)
    df.drop(columns=['Humidity', 'Percipitation', 'Temperature', 'WindSpeed'], inplace=True)

    dataframe_collection = {}
    dataframe = pd.DataFrame()

    for value in df['Type'].unique():
        df_type = df[df['Type'] == value]
        df_type.rename(columns={'Data': value}, inplace=True)
        df_type.drop(columns=['Type'], inplace=True)

        dataframe_collection[value] = df_type

    for key in dataframe_collection.keys():
        if dataframe.empty:
            dataframe = dataframe.append(dataframe_collection[key], ignore_index=True)
        else:
            dataframe = pd.merge(dataframe, dataframe_collection[key], how='left', on='time')

    cols = list(dataframe)
    # move the column to head of list using index, pop and insert
    cols.insert(0, cols.pop(cols.index('time')))
    # use ix to reorder
    dataframe = dataframe.ix[:, cols]

    dataframe.to_csv(pollution_report, index=False)
