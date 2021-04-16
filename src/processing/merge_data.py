from os import path

from numpy import abs, nan, number
from pandas import merge as pandas_merge, read_csv, to_numeric
from scipy.stats import zscore
from sklearn.impute import KNNImputer

from definitions import DATA_EXTERNAL_PATH, pollutants
from preparation import save_dataframe
from .calculate_index import calculate_aqi, calculate_co_index, calculate_no2_index, calculate_o3_index, \
    calculate_pm2_5_index, calculate_pm10_index, calculate_so2_index


def drop_numerical_outliers(dataframe, z_thresh=3):
    # Constrains will contain 'True' or 'False' depending on if it is a value below the threshold.
    constrains = dataframe.select_dtypes(include=[number]).apply(lambda x: abs(zscore(x)) < z_thresh,
                                                                 result_type='reduce').all(axis=1)
    # Drop (inplace) values set to be rejected
    dataframe.drop(index=dataframe.index[~constrains], inplace=True)


def merge_air_quality_data(data_path, city_name, sensor_id):
    weather_data = read_csv(path.join(data_path, city_name, sensor_id, 'weather.csv'))
    pollution_data = read_csv(path.join(data_path, city_name, sensor_id, 'pollution.csv'))

    dataframe = pandas_merge(weather_data.drop_duplicates(), pollution_data.drop_duplicates(), on='time')

    df_columns = dataframe.columns.copy()
    df_columns = df_columns.drop(['aqi', 'icon', 'precipType', 'sensorId', 'summary'], errors='ignore')

    imp = KNNImputer()
    for column in df_columns:
        dataframe[column] = to_numeric(dataframe[column], errors='coerce')
        if not dataframe[column].isna().all():
            dataframe[column] = imp.fit_transform(dataframe[column].values.reshape(-1, 1))
            dataframe[column].interpolate(method='nearest', fill_value='extrapolate', inplace=True)
        else:
            dataframe.drop(columns=column)

    pollutants_wo_aqi = pollutants.copy()
    pollutants_wo_aqi.pop('aqi')
    columns = pollutants_wo_aqi.copy()
    for column in columns:
        if column not in dataframe.columns:
            pollutants_wo_aqi.pop(column)

    drop_columns_std = dataframe[pollutants_wo_aqi].std()[dataframe[pollutants_wo_aqi].std() == 0].index.values

    dataframe[pollutants_wo_aqi].replace(0, nan).bfill(inplace=True)
    dataframe[pollutants_wo_aqi].replace(0, nan).ffill(inplace=True)
    dataframe.drop(columns=drop_columns_std, inplace=True)

    dataframe['aqi'] = dataframe.apply(
        lambda row: calculate_aqi(calculate_co_index(row['co']) if 'co' in dataframe.columns else 0,
                                  calculate_no2_index(row['no2']) if 'no2' in dataframe.columns else 0,
                                  calculate_o3_index(row['o3']) if 'o3' in dataframe.columns else 0,
                                  calculate_pm2_5_index(row['pm2_5']) if 'pm2_5' in dataframe.columns else 0,
                                  calculate_pm10_index(row['pm10']) if 'pm10' in dataframe.columns else 0,
                                  calculate_so2_index(row['so2']) if 'so2' in dataframe.columns else 0)
        if row.get('aqi') is None else row['aqi'], axis=1)

    # drop_numerical_outliers(dataframe)

    dataframe = dataframe.dropna(axis='columns', how='all').dropna(axis='index', how='all')
    if not dataframe.empty:
        summary_data_path = path.join(DATA_EXTERNAL_PATH, city_name, sensor_id, 'summary.csv')
        save_dataframe(dataframe, 'summary', summary_data_path, sensor_id)
