import pandas as pd


def duplicated_mask(df):
    return pd.Index(df.columns).duplicated()


def dedupe_columns(df):
    mask = duplicated_mask(df)
    dropped = list(df.columns[mask])
    return df.loc[:, ~mask], dropped
