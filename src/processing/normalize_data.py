from numpy import int64
from pandas import DataFrame, merge as pandas_merge, to_datetime


def closest_hour(t):
    return t.replace(microsecond=0, second=0, minute=0,
                     hour=t.hour if t.minute <= 30 else 0 if t.hour == 23 else t.hour + 1)


def current_hour(t):
    return t.replace(microsecond=0, second=0, minute=0, hour=t.hour)


def flatten_json(nested_json: dict, exclude=None):
    """
    Flatten a list of nested dicts.
    """
    if exclude is None:
        exclude = ['']
    out = dict()

    def flatten(x: (list, dict, str), name: str = '', exclude=exclude):
        if type(x) is dict:
            for a in x:
                if a not in exclude:
                    flatten(x[a], f'{name}{a}_')
        elif type(x) is list:
            if len(x) == 1:
                flatten(x[0], f'{name}')
            else:
                i = 0
                for a in x:
                    flatten(a, f'{name}{i}_')
                    i += 1
        else:
            out[name[:-1]] = x

    flatten(nested_json)
    return out


def next_hour(t):
    return t.replace(microsecond=0, second=0, minute=0, hour=0 if t.hour == 23 else t.hour + 1,
                     day=t.day + 1 if t.hour == 23 else t.day)


def normalize_pollution_data(df):
    dataframe = DataFrame()
    dataframe_collection = {}

    for value in df['type'].unique():
        df_type = df[df['type'] == value].copy()
        df_type.rename(columns={'value': value}, inplace=True)
        df_type.drop(columns=['position', 'type'], inplace=True, errors='ignore')

        dataframe_collection[value] = df_type

    for key in dataframe_collection:
        if dataframe.empty:
            dataframe = dataframe.append(dataframe_collection[key], ignore_index=True)
        else:
            dataframe = pandas_merge(dataframe, dataframe_collection[key], how='left', on='time')

    cols = list(dataframe)
    # move the column to head of list using index, pop and insert
    cols.insert(0, cols.pop(cols.index('time')))
    # use loc to reorder
    dataframe = dataframe.loc[:, cols]

    dataframe['time'] = to_datetime(dataframe['time'], unit='s')
    dataframe['time'] = dataframe.apply(lambda row: current_hour(row['time']), axis=1)
    dataframe['time'] = dataframe['time'].values.astype(int64) // 10 ** 9

    return dataframe
