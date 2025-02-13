import pandas as pd
import octk


location_indicators = {
    "Pathology Museum": ['Path Museum', 'Pathology Museum', 'PathMuseum'],
    "Dissecting location": ['Dissecting location'],
    "Med Lib e-learning": ['Med Lib e-learning', 'MDLib eLearning', 'QE2MDLIB'],
    "Ross LT": ['Ross LT', "Ross"],
    "FJC LT": ['FJC LT', 'FJC'],
    "McCusker LT": ['McCusker LT'],
}

subject_indicators = {
    'Research Skills': ['Research Skills'],
    'Pharmacology': ['Pharmacology', 'Pharm'],
    'Physiology': ['Physiology', 'Physiol'],
    'Aboriginal Health': ['Aboriginal Health', 'Aboriginal Healt'],
    'Population Health': ['Population Health', 'Pop Health', 'Popn Health'],
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
    'Hannah Phylaxis': ["Hannah Phylaxis", '(HP)'],
    'Marcus Dabner': ["Marcus Dabner", '(MD)'],
    'Nicole Swarbrick': ["Nicole Swarbrick", '(NS)'],
    'Patricia Martinez': ["Patricia Martinez", '(PM)'],
}

type_to_location_map: dict[str,list] = {
    "Lab": ["Physiology Lab"],
    "Workshop": ["Med Lib e-learning"],
    "SGL": ["Pathology Museum"],
    "Lecture": ["FJC LT", "Ross LT", "McCusker LT"],
}

type_indicators = {
    "SGL": ["SGL", "Small Group Learning"],
    "Lab": ["Lab Group"],
    "Assessment": ["Assessment"],
    "TBL": ["TBL"],
    'Workshop': ['Workshop'],
}

def translate_from_indicator(indicator_map, content):
    """
    @param indicator_map: dict[str, list[str]] - key is the value to be returned, value is a list of indicators
    @param content: str - the content to search for indicators in
    @return: str - the key of the first indicator found in the content
    """
    for key, indicators in indicator_map.items():
        for indicator in indicators:
            if indicator.lower() in content.strip().lower():
                return key
    return None


def remove_duplicates(df):
    return df.drop_duplicates()

def add_missing_location(df):
    # for missing 'location' values, search in 'description' column
    for index, row in df.iterrows():
        if not row['location']:
            location = translate_from_indicator(location_indicators, row['description'])
            if location:
                print(row['description'], location)
                df.at[index, 'location'] = location
    return df


def add_missing_subject(df): 
    # for missing 'subject' values, search in 'description' column
    for index, row in df.iterrows():
        if pd.isna(row['subject']):
            subject = ""
        subject = row['subject'].strip()
        if subject:
            translate_from_indicator(subject_indicators, subject)
        if not subject:
            subject = translate_from_indicator(subject_indicators, row['description'])
            if subject:
                df.at[index, 'subject'] = subject
    return df


def add_missing_type(df):
    # for missing 'session_type' values, search in 'description' column
    for index, row in df.iterrows():
        # infer from description
        if not row['session_type']:
            session_type = translate_from_indicator(type_indicators, row['description'])
            if session_type:
                df.at[index, 'session_type'] = session_type
                continue
            # infer from location
            elif not pd.isna(row['location']):
                session_type = translate_from_indicator(type_to_location_map, row['location'])
                if session_type:
                    df.at[index, 'session_type'] = session_type
    return df


def add_missing_presenter(df):
    # for missing 'presenter' values, search in 'description' column
    for index, row in df.iterrows():
        if pd.isna(row['presenter']) or row['presenter'] == "":
            presenter = translate_from_indicator(presenter_indicators, row['description'])
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




