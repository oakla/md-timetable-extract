import pandas as pd
import octk
import re

found_subjects = set()
found_presenters = set()
found_locations = set()

location_indicators_map = {
    "Path Museum": ['Path Museum', 'Pathology Museum', 'PathMuseum'],
    "Dissecting location": ['Dissecting location'],
    "QE2MDLIB": ['Med Lib e-learning', 'MDLib eLearning', 'QE2MDLIB'],
    "Ross": ['Ross LT', "Ross"],
    "FJC": ['FJC LT', 'FJC', 'FJC Lecture Theatre', 'FJ Clark', 'FJ Clark LT'],
    "McCusker": ['McCusker LT'],
}

all_location_indicators = [item for sublist in location_indicators_map.values() for item in sublist]

subject_indicators_map = {
    'Research Skills': ['Research Skills'],
    'Pharmacology': ['Pharmacology', 'Pharm'],
    'Physiology': ['Physiology', 'Physiol'],
    'Aboriginal Health': ['Aboriginal Health', 'Aboriginal Healt'],
    'Population Health': ['Population Health', 'Pop Health', 'Popn Health'],
}

all_subject_indicators = [item for sublist in subject_indicators_map.values() for item in sublist]

presenter_indicators_map = {
    'Angus Cook': ["Angus Cook", '(AC)'],
    'Barbara Nattabi': ["Barbara Nattabi", '(BN)'],
    'David Preen': ["David Preen", '(DP)'],
    'Fiona Pixely': ["Fiona Pixely", '(FP)'],
    'Helen Wilcox': ["Helen Wilcox", '(HW)'],
    'Jo Chua': ["Jo Chua", '(JC)'],
    'Julie Saunders': ["Julie Saunders", '(JS)'],
    'Liz Quail': ["Liz Quail", '(LQ)'],
    'Marcus Dabner': ["Marcus Dabner", '(MD)'],
    'Nicole Swarbrick': ["Nicole Swarbrick", '(NS)'],
    'Patricia Martinez': ["Patricia Martinez", '(PM)'],
    'Paul McGurgan': ["Paul McGurgan", '(PM)'],
    "Peter Tan": ["Peter Tan", "(PT)"],
    'Rob White': ["Rob White", '(RW)'],
    'Shao Tneh': ["Shao Tneh", '(ST)'],
    'Thomas Wilson': ["(TW)", "Thomas Wilson", 'Tom Wilson'],
    'Tina Carter': ["Tina Carter", '(TC)'],
    'Zaza Lyons': ["Zaza Lyons", '(ZL)'],
}

type_to_location_map: dict[str,list] = {
    "Lab": ["Physiology Lab"],
    "Workshop": ["Med Lib e-learning"],
    "SGL": ["Pathology Museum"],
    "Clinical Skills": ["N Block"],
    "Lecture": ["FJC LT", "Ross LT", "McCusker LT", "FJ Clark"],
}

type_indicators = {
    "SGL": ["SGL", "Small Group Learning"],
    "Lab": ["Lab Group", "ANHB G05", "PHSL G11"],
    "Assessment": ["Assessment"],
    "TBL": ["TBL"],
    'Workshop': ['Workshop'],
}

def find_indicator(indicator_map, content):
    """
    @param indicator_map: dict[str, list[str]] - key is the value to be returned, value is a list of indicators
    @param content: str - the content to search for indicators in
    @return: str - the key of the first indicator found in the content
    """
    for key, indicators in indicator_map.items():
        for indicator in indicators:
            if indicator.lower() in content.strip().lower():
                return indicator
    return None

def standardise_from_indicator(indicator_map, symbol):
    """
    @param indicator_map: dict[str, list[str]] - key is the value to be returned, value is a list of indicators
    @param content: str - the content to search for indicators in
    @return: str - the key of the first indicator found in the content
    """
    for key, indicators in indicator_map.items():
        for indicator in indicators:
            if indicator.lower() in symbol.strip().lower():
                return key
    return symbol


def remove_duplicates(df):
    return df.drop_duplicates()

def is_invalid_location(location: str) -> bool:
    invalid_locations = [
        r"\d+ hours",
    ]
    for invalid_location in invalid_locations:
        if re.search(invalid_location, location):
            return True
    return False

def extract_location(event_description: str) -> str:
    """
    Extracts the location from the event description.
    First assumes location is contained in "[Location Name]" format.
    If no match is found, look for one of the location indicators.
    """
    if not event_description:
        return ""
    
    rtn_location = ""    # First try to find location in square brackets
    matches = [x.strip() for x in re.findall(r'\[([^\]]+)\]', event_description)]
    if matches:
        for match in matches:
            if not is_invalid_location(match):
                rtn_location = match.strip()
                standardised_location = standardise_from_indicator(location_indicators_map, rtn_location)
                rtn_location = standardised_location if standardised_location else rtn_location
                break

    # If no match, try to find location using indicators
    if not rtn_location:
        for location, indicators in location_indicators_map.items():
            for indicator in indicators:
                if indicator.lower() in event_description.strip().lower():
                    rtn_location = location
                    break
    return rtn_location


def add_missing_location(df):
    # if 'location' column is empty, try to extract location from 'description' column
    for index, row in df.iterrows():
        if pd.isna(row['location']) or row['location'].strip() == "":
            location = extract_location(row['description'])
            df.at[index, 'location'] = location
        found_locations.add(location)
    return df


def add_missing_subject(df): 
    # for missing 'subject' values, search in 'description' column
    for index, row in df.iterrows():
        subject_0 = ""
        if not pd.isna(row['subject']):
            subject_0 = row['subject'].strip()
        if subject_0:
            subject_1 = standardise_from_indicator(subject_indicators_map, subject_0)
        else:
            subject_1 = standardise_from_indicator(subject_indicators_map, row['description'])
        new_subject = subject_1 if subject_1 else subject_0
        found_subjects.add(new_subject)
        df.at[index, 'subject'] = new_subject
        found_subjects.add(new_subject)
    return df


def add_missing_type(df):
    # for missing 'session_type' values, search in 'description' column
    for index, row in df.iterrows():
        # infer from description
        if not row['session_type']:
            session_type = find_indicator(type_indicators, row['description'])
            if session_type:
                df.at[index, 'session_type'] = session_type
                continue
            # infer from location
            elif not pd.isna(row['location']):
                session_type = standardise_from_indicator(type_to_location_map, row['location'])
                if session_type:
                    df.at[index, 'session_type'] = session_type
    return df

def extract_group_numbers(description):
    match = re.search(r'(?i)\bGroups?\s*(\d+(-\d+)?)\b', description)
    return "'" + match.group(1).strip() if match else ""

def add_groups_column(df):
    # Add a 'groups' column based on the 'description' column. Blank if session_type is lecture, otherwise uses number range found after word 'Group' or 'Groups'.
    df['groups'] = df.apply(lambda row: extract_group_numbers(row['description']) if row['session_type'].lower() != 'lecture' else "", axis=1)
    return df

def extract_topic(description):
    # assume topic is after "<subject> - " and before the next '(' or '['
    match = re.search(r'\s*?[-:]\s*(.*?)(\(|\[|$)', description)

    return match.group(1).strip() if match else ""

def add_topics(df):
    # assume topic is after "<subject> - " and before the next '(' or '['
    df['topic'] = df['description'].apply(extract_topic)
    return df

def trim_topic(df):
    """ Remove anything from topic after and including terms that appear in location, or subject indicators """
    for index, row in df.iterrows():
        topic = row['topic']
        # Check against location indicators
        for loc in all_location_indicators:
            if loc in topic:
                topic = topic.split(loc)[0].strip()
                break
        # Check against subject indicators
        for subj in all_subject_indicators:
            if subj in topic:
                topic = topic.split(subj)[0].strip()
                break
        df.at[index, 'topic'] = topic
    return df

def is_no_presenter(event_description: str) -> bool:

    return "(Path Museum)" in event_description or \
            "(Pathology Museum)" in event_description or \
            "[ANHB G05]" in event_description or \
            "Groups 1-10" in event_description or \
            "Groups 11-20" in event_description

def extract_presenter(event_description: str) -> str:
    """
    Extracts the presenter from the event description.'
    First assumes presenter is contained in "(Presenter Name)" format.
    If no match is found, try "[Presenter Name]" format.
    Returns an empty string if no presenter is found.
    """
    if is_no_presenter(event_description):
        return "Various"
    match = re.search(r'\(([^)]+)\)', event_description)
    if match:
        return match.group(1).strip()
    match = re.search(r'\[([^\]]+)\]', event_description)
    if match:
        return match.group(1).strip()
    return ""

def standardize_presenter_names(current_presenter):
    """
    Standardizes the presenter names to its full form.
    """
    found_presenters.add(current_presenter.strip())
    fullname = standardise_from_indicator(presenter_indicators_map, current_presenter)
    return fullname.strip() if fullname else current_presenter.strip()


def add_presenter_column(df):
    df['presenter'] = df['description'].apply(extract_presenter)\
        .apply(standardize_presenter_names)
    return df



def post_process_events(df):
    df = remove_duplicates(df)
    df = add_missing_location(df)
    df = add_missing_subject(df)
    df = add_missing_type(df)
    df = add_presenter_column(df)
    df = add_groups_column(df)
    df = add_topics(df)
    df = trim_topic(df)
    return df




