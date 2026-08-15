from datetime import datetime, timedelta
from os import path
from typing import Optional

from pandas import concat, DataFrame, read_csv, to_datetime

from definitions import chunk_size, DATA_PROCESSED_PATH


def read_csv_in_chunks(data_path: str, index_col: str = None) -> Optional[DataFrame]:
    chunks = []
    for chunk in read_csv(data_path, index_col=index_col, chunksize=chunk_size):
        chunk.index = to_datetime(chunk.index, unit='s')
        if len(chunk.index) > 0:
            chunks.append(chunk)

    return concat(chunks) if len(chunks) > 0 else None


def current_hour() -> datetime:
    return datetime.now().replace(minute=0, second=0, microsecond=0)


if __name__ == '__main__':
    dataframe = read_csv_in_chunks(path.join(DATA_PROCESSED_PATH, 'tetovo', '3001', 'summary.csv'),
                                   index_col='time')
    timestamps = dataframe.index.tolist()
    dataframe = dataframe.loc[
        dataframe.between_time((current_hour() - timedelta(weeks=52)).time(), current_hour().time())]
    print(dataframe)
