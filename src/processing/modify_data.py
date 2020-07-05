def previous_value_overwrite(dataframe):
    dataframe = dataframe.shift(periods=-1, axis=0)
    dataframe.reset_index(drop=True, inplace=True)
    dataframe.drop(len(dataframe) - 1, inplace=True)

    return dataframe
