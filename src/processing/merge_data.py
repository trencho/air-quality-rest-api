import numpy as np
import pandas as pd
from scipy import stats
from sklearn.impute import SimpleImputer

import src.processing.calculate_aqi as ca
from definitions import stations, pollutants


def drop_numerical_outliers(df, z_thresh=3):
    # Constrains will contain `True` or `False` depending on if it is a value below the threshold.
    constrains = df.select_dtypes(include=[np.number]).apply(lambda x: np.abs(stats.zscore(x)) < z_thresh,
                                                             result_type='reduce').all(axis=1)
    # Drop (inplace) values set to be rejected
    df.drop(df.index[~constrains], inplace=True)


timestamp_2018 = 1514764800

for station_name in stations:
    weather_data = pd.read_csv('D:/Downloads/NAPMMU/Datasets/Weather/weather_report_' + station_name + '.csv')
    pollution_data = pd.read_csv('D:/Downloads/NAPMMU/Datasets/Pollution/pollution_report_' + station_name + '.csv')
    combined_report_csv = 'D:/Downloads/NAPMMU/Datasets/combined_report_' + station_name + '.csv'

    dataframe = pd.merge(weather_data.drop_duplicates(), pollution_data.drop_duplicates(), on='time')

    #    nunique = dataframe.apply(pd.Series.nunique)
    #    cols_to_drop = nunique[nunique == 1].index
    #    dataframe.drop(cols_to_drop, axis=1, inplace=True)

    #    dataframe.loc[:, dataframe.std() > 0]

    df_columns = dataframe.columns.copy()

    #    df_nan = dataframe[dataframe.isna().any(axis=1)]
    #    for index, row in df_nan.iterrows():
    #        equal_sin_time_rows = dataframe[np.sin(dataframe['time']) == np.sin(row['time'])]
    #        for column in df_columns:
    #            if pd.isna(dataframe.iloc[index][column]):
    #                for index_rows, equal_sin_time_row in equal_sin_time_rows.iterrows():
    #                    if not pd.isna(equal_sin_time_row[column]):
    #                        dataframe.at[index, column] = equal_sin_time_row[column]
    #                        break

    df_columns = df_columns.drop('icon', errors='ignore')
    df_columns = df_columns.drop('precipType', errors='ignore')
    df_columns = df_columns.drop('summary', errors='ignore')
    df_columns = df_columns.drop('AQI', errors='ignore')
    #    df_columns = df_columns.drop('Type', errors='ignore')

    imp = SimpleImputer(missing_values=np.nan, strategy='most_frequent')
    for column in df_columns:
        dataframe[column] = pd.to_numeric(dataframe[column], errors='coerce')
        if not dataframe[column].isna().all():
            dataframe[column] = imp.fit_transform(dataframe[column].values.reshape(-1, 1))
            dataframe[column].interpolate(method='nearest', fill_value='extrapolate', inplace=True)
        else:
            dataframe.drop(columns=column)

    pollutants_wo_AQI = pollutants.copy()
    pollutants_wo_AQI.remove('AQI')
    for column in pollutants_wo_AQI:
        if column not in dataframe.columns:
            pollutants_wo_AQI.remove(column)

    test_dataset = dataframe[dataframe['time'] >= timestamp_2018]
    y_test = test_dataset[pollutants_wo_AQI]
    drop_columns_std = y_test[pollutants_wo_AQI].std()[y_test[pollutants_wo_AQI].std() == 0].index.values

    dataframe[pollutants_wo_AQI].replace(0, pd.np.nan).bfill(inplace=True)
    dataframe[pollutants_wo_AQI].replace(0, pd.np.nan).ffill(inplace=True)
    dataframe.drop(drop_columns_std, axis=1, inplace=True)

    dataframe['AQI'] = dataframe.apply(
        lambda row: ca.calculate_aqi(ca.calculate_co_aqi(row['CO']) if 'CO' in dataframe.columns else 0,
                                     ca.calculate_no2_aqi(row['NO2']) if 'NO2' in dataframe.columns else 0,
                                     ca.calculate_o3_aqi(row['O3']) if 'O3' in dataframe.columns else 0,
                                     ca.calculate_pm25_aqi(row['PM25']) if 'PM25' in dataframe.columns else 0,
                                     ca.calculate_pm10_aqi(row['PM10']) if 'PM10' in dataframe.columns else 0,
                                     ca.calculate_so2_aqi(row['SO2']) if 'SO2' in dataframe.columns else 0) if row[
                                                                                                                   'AQI'] is not None else
        row['AQI'], axis=1)

    #    dataframe = dataframe[(np.abs(stats.zscore(dataframe[df_columns])) < 3).all(axis=1)]
    drop_numerical_outliers(dataframe)

    #    dataframe.drop(columns=[dataframe.count().idxmin()], inplace=True, errors='ignore')
    for i, v in dataframe.isna().all().iteritems():
        if dataframe.isna().all()[i]:
            dataframe.drop(columns=[i], inplace=True, errors='ignore')
            df_columns = df_columns.drop(i, errors='ignore')

    #    dataframe.rename(columns={'Data' : 'data'}, inplace=True)
    #    dataframe.rename(columns={'Type' : 'type'}, inplace=True)

    #    cols = list(dataframe)
    #    # move the column to head of list using index, pop and insert
    #    cols.insert(0, cols.pop(cols.index('type')))
    #    # use ix to reorder
    #    dataframe = dataframe.ix[:, cols]

    dataframe.to_csv(combined_report_csv, index=False)

# import pandas as pd
#
# for station_name in stations:
#     weather_data = pd.read_csv('D:/Downloads/NAPMMU/Datasets/Weather/weather_report_' + station_name + '.csv')
#     pollution_data = pd.read_csv('D:/Downloads/NAPMMU/Datasets/Pollution/pollution_report_' + station_name + '.csv')
#     dataframe = pd.merge(weather_data.drop_duplicates(), pollution_data.drop_duplicates(), on='time')
#     for value_type in pollutants:
#         if value_type not in dataframe.columns:
#             continue
#         dataframe = dataframe.dropna(subset=[value_type])
#     print(station_name)
#     print(dataframe.count())
#     print(dataframe.isna().sum())
#     print('Number of rows: ' + str(len(dataframe.index)))
#     print('\n')
