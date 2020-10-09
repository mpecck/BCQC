import pandas as pd


def read_csv(worksheet):
    df = pd.read_csv(worksheet).ffill()
    # print(df)
    return df


def create_df(data):
    df = pd.DataFrame(data)
    # print(df)
    return df


def append_to_df(df, data):
    new_df = pd.DataFrame(data)
    df = df.append(new_df)
    # print(df)
    return df


def write_csv(filename, df):
    df.to_csv(filename, index=False)
