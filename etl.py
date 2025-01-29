import camelot
import pandas as pd


def table_to_df(df: pd.DataFrame) -> tuple[str, pd.DataFrame]:

    base_df = df.copy()


    # Get column names
    columns = base_df.iloc[1]
    # rename duplicate columns
    columns = [f'{col} ({i})' if columns.duplicated().iloc[i] else col for i, col in enumerate(columns)]
    
    base_df.columns = columns
    
    # get rows where time contains 'online'
    online_rows = base_df[base_df['Time'].str.contains('online', case=False)]
    # find first row with number in the time column
    for i, row in base_df.iterrows():
        if row[0].isdigit():
            break
    time_start_row = i

    # make new table starting from time_start_row
    df = base_df.iloc[time_start_row:]
    df.reset_index(drop=True, inplace=True)

    # where time appears twice, make the second time half past
    half_past_rows = []
    max_index = len(df) - 1
    for i, row in df.iterrows():
        if i+1 == max_index:
            break
        if df.loc[i, 'Time'] == df.loc[i+1, 'Time']:
            half_past_rows.append(i+1)

    new_half_past_rows = []
    for i, row in df.iterrows():
        if i in half_past_rows:
            df.loc[i, 'Time'] = df.loc[i, 'Time'] + ':30'
        elif i+1 in half_past_rows:
            df.loc[i, 'Time'] = df.loc[i, 'Time'] + ':00'
        else:
            new_half_past_rows.append(df.iloc[i].to_dict())
            df.loc[i, 'Time'] = df.loc[i, 'Time'] + ':00'

    for d in new_half_past_rows:
        d['Time'] = d['Time'] + ':30'

    new_rows_df = pd.DataFrame(new_half_past_rows)

    in_person_row = pd.concat([df, new_rows_df], ignore_index=True)
    full_df = pd.concat([in_person_row, online_rows], ignore_index=True)
    
    return full_df
