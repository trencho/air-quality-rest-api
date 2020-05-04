import numpy as np
import pandas as pd
from scipy import stats
from sklearn.impute import SimpleImputer

from definitions import pollutants, DATA_EXTERNAL_PATH
from preparation.handle_data import save_dataframe
from processing import calculate_aqi, calculate_co_aqi, calculate_no2_aqi, calculate_o3_aqi, calculate_pm25_aqi, \
    calculate_pm10_aqi, calculate_so2_aqi


def drop_numerical_outliers(df, z_thresh=3):
    # Constrains will contain `True` or `False` depending on if it is a value below the threshold.
    constrains = df.select_dtypes(include=[np.number]).apply(lambda x: np.abs(stats.zscore(x)) < z_thresh,
                                                             result_type='reduce').all(axis=1)
    # Drop (inplace) values set to be rejected
    df.drop(df.index[~constrains], inplace=True)


def merge(city_name, sensor_id):
    weather_data = pd.read_csv(DATA_EXTERNAL_PATH + '/' + city_name + '/' + sensor_id + '/weather_report.csv')
    pollution_data = pd.read_csv(DATA_EXTERNAL_PATH + '/' + city_name + '/' + sensor_id + '/pollution_report.csv')

    dataframe = pd.merge(weather_data.drop_duplicates(), pollution_data.drop_duplicates(), on='time')

    # nunique = dataframe.apply(pd.Series.nunique)
    # cols_to_drop = nunique[nunique == 1].index
    # dataframe.drop(cols_to_drop, axis=1, inplace=True)

    # dataframe.loc[:, dataframe.std() > 0]

    df_columns = dataframe.columns.copy()

    # df_nan = dataframe[dataframe.isna().any(axis=1)]
    # for index, row in df_nan.iterrows():
    #     equal_sin_time_rows = dataframe[np.sin(dataframe['time']) == np.sin(row['time'])]
    #     for column in df_columns:
    #         if pd.isna(dataframe.iloc[index][column]):
    #             for index_rows, equal_sin_time_row in equal_sin_time_rows.iterrows():
    #                 if not pd.isna(equal_sin_time_row[column]):
    #                     dataframe.at[index, column] = equal_sin_time_row[column]
    #                     break

    df_columns = df_columns.drop('icon', errors='ignore')
    df_columns = df_columns.drop('precipType', errors='ignore')
    df_columns = df_columns.drop('summary', errors='ignore')
    df_columns = df_columns.drop('aqi', errors='ignore')
    # df_columns = df_columns.drop('Type', errors='ignore')

    imp = SimpleImputer(missing_values=np.nan, strategy='most_frequent')
    for column in df_columns:
        dataframe[column] = pd.to_numeric(dataframe[column], errors='coerce')
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

    dataframe[pollutants_wo_aqi].replace(0, np.nan).bfill(inplace=True)
    dataframe[pollutants_wo_aqi].replace(0, np.nan).ffill(inplace=True)
    dataframe.drop(drop_columns_std, axis=1, inplace=True)

    dataframe['aqi'] = dataframe.apply(
        lambda row: calculate_aqi(calculate_co_aqi(row['co']) if 'co' in dataframe.columns else 0,
                                  calculate_no2_aqi(row['no2']) if 'no2' in dataframe.columns else 0,
                                  calculate_o3_aqi(row['o3']) if 'o3' in dataframe.columns else 0,
                                  calculate_pm25_aqi(row['pm25']) if 'pm25' in dataframe.columns else 0,
                                  calculate_pm10_aqi(row['pm10']) if 'pm10' in dataframe.columns else 0,
                                  calculate_so2_aqi(row['so2']) if 'so2' in dataframe.columns else 0)
        if dataframe.get('aqi') is None else row['aqi'], axis=1)

    # dataframe = dataframe[(np.abs(stats.zscore(dataframe[df_columns])) < 3).all(axis=1)]
    # drop_numerical_outliers(dataframe)

    # dataframe.drop(columns=[dataframe.count().idxmin()], inplace=True, errors='ignore')
    for i, v in dataframe.isna().all().iteritems():
        if dataframe.isna().all()[i]:
            dataframe.drop(columns=[i], inplace=True, errors='ignore')
            df_columns = df_columns.drop(i, errors='ignore')

    # dataframe.rename(columns={'Data' : 'data'}, inplace=True)
    # dataframe.rename(columns={'Type' : 'type'}, inplace=True)

    # cols = list(dataframe)
    # # move the column to head of list using index, pop and insert
    # cols.insert(0, cols.pop(cols.index('type')))
    # # use loc to reorder
    # dataframe = dataframe.loc[:, cols]

    summary_data_path = (
            DATA_EXTERNAL_PATH + '/' + city_name + '/' + sensor_id + '/summary_report.csv')
    save_dataframe(dataframe, 'summary', summary_data_path)
