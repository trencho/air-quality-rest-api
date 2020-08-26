def previous_value_overwrite(dataframe):
    dataframe = dataframe.shift(periods=-1, axis=0)
    dataframe.drop(dataframe.iloc[-1].index, inplace=True)

    return dataframe
