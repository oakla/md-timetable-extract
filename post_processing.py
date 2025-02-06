import pandas as pd
import octk


location_indicators = {
    "Pathology Museum": ['Path Museum', 'Pathology Museum', 'PathMuseum'],
    "Dissecting location": ['Dissecting location'],
    "Med Lib e-learning": ['Med Lib e-learning', 'MDLib eLearning'],
}

subject_indicators = {
    'Research Skills': ['Research Skills'],
    'Pharmacology': ['Pharmacology', 'Pharm'],
    'Physiology': ['Physiology', 'Physiol'],
    'Aboriginal Health': ['Aboriginal Health'],
}

type_indicators = {
    "SGL": ["SGL", "Small Group Learning"],
    "Lab": ["Lab Group"],
    "Assessment": ["Assessment"],
    "TBL": ["TBL"],
    'Workshop': ['Workshop'],
}

presenter_indicators = {
    "Peter Tan": ["Peter Tan", "(PT)"],
    'Thomas Wilson': ["(TW)", "Thomas Wilson", 'Tom Wilson'],
    'David Preen': ["David Preen", '(DP)'],
    'Shao Tneh': ["Shao Tneh", '(ST)'],
    'Hannah Phylaxis': ["Hannah Phylaxis", '(LQ)'],
    'Liz Quail': ["Liz Quail", '(LQ)'],
    'Rob White': ["Rob White", '(RW)'],
    'Paul McGurgan': ["Paul McGurgan", '(PM)'],
    'Julie Saunders': ["Julie Saunders", '(JS)'],
    'Barbara Nattabi': ["Barbara Nattabi", '(BN)'],
    'Angus Cook': ["Angus Cook", '(AC)'],
    'Zaza Lyons': ["Zaza Lyons", '(ZL)'],
    'Tina Carter': ["Tina Carter", '(TC)'],
    'Jo Chua': ["Jo Chua", '(JC)'],
}

location_to_type_map = {
    "Physiology Lab": "Lab",
    "Med Lib e-learning": "Workshop",
    "Pathology Museum": "SGL",
}

def translate_from_indicator(indicator_map, content):
    for key, indicators in indicator_map.items():
        for indicator in indicators:
            if indicator.lower() in content.strip().lower():
                return key
    return None


def remove_duplicates(df):
    return df.drop_duplicates()

def add_missing_location(df):
    # for missing 'location' values, search in 'event' column
    for index, row in df.iterrows():
        if pd.isna(row['location']):
            location = translate_from_indicator(location_indicators, row['event'])
            if location:
                print(row['event'], location)
                df.at[index, 'location'] = location
    return df


def add_missing_subject(df): 
    # for missing 'subject' values, search in 'event' column
    for index, row in df.iterrows():
        if pd.isna(row['subject']):
            subject = translate_from_indicator(subject_indicators, row['event'])
            if subject:
                df.at[index, 'subject'] = subject
    return df


def add_missing_type(df):
    # for missing 'session_type' values, search in 'event' column
    for index, row in df.iterrows():
        if pd.isna(row['session_type']):
            session_type = translate_from_indicator(type_indicators, row['event'])
            if session_type:
                df.at[index, 'session_type'] = session_type
                continue
            elif not pd.isna(row['location']):
                location:str = row['location'].strip()
                for location_key, type_value in location_to_type_map.items():
                    if location.lower() == location_key.lower():
                        df.at[index, 'session_type'] = type_value
                        print("type set for: ", location, type_value)
    return df


def add_missing_presenter(df):
    # for missing 'presenter' values, search in 'event' column
    for index, row in df.iterrows():
        if pd.isna(row['presenter']) or row['presenter'] == "":
            presenter = translate_from_indicator(presenter_indicators, row['event'])
            if presenter:
                df.at[index, 'presenter'] = presenter
    return df


def post_process_events(df):
    df = remove_duplicates(df)
    df = add_missing_location(df)
    df = add_missing_subject(df)
    df = add_missing_type(df)
    df['presenter'] = ""
    df = add_missing_presenter(df)
    return df




