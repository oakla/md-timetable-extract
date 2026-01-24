from typing import Union
import pandas as pd
import octk
import re

found_subjects = set()
found_presenters = set()
found_locations = set()


MANDATORY_SESSION_TYPES = [
    "Assessment",
    "Lab",
    "Workshop",
    "TBL",
    "SGL",
    "Clinical Skills"
]

MANDATORY_INDICATORS = [
    "RECORDED ATTENDANCE",
    "Mandatory Attendance",
]

DROP_ROW_INDICATORS = [
    "NON-TEACHING WEEK",
    "Public Holiday",
    "PUBLIC-HOLIDAY"
]

SESSION_TYPES_WITHOUT_SUBJECTS = [
    "Assessment",
]

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
    'Aboriginal Health': ['Aboriginal Health', 'Aboriginal Healt'],
    'Assignment': ['Assignment'],
    'Anatomy': ['Anatomy', 'ANAT'],
    'Biochemistry': ['Biochemistry', 'Biochem'],
    'Behavioural Science': ['Behavioural Science', 'Behav Sci'],
    'Chemical Pathology': ['Chemical Pathology', 'Chem Path'],
    'Clinical Skills': ['Clinical Skills'],
    'Clinical': ['Clinical'],
    'Genetics': ['Genetics'],
    'Immunology': ['Immunology'],
    'Pharmacology': ['Pharmacology', 'Pharm'],
    'Physiology': ['Physiology', 'Physiol'],
    'Population Health': ['Population Health', 'Pop Health', 'Popn Health'],
    'Research Skills': ['Research Skills'],
    'Self directed revision': ['Self directed revision', 'Self-directed revision'],
}

all_subject_indicators = [item for sublist in subject_indicators_map.values() for item in sublist]

# TODO: this doesn't seem to do anything ...make it work
presenter_indicators_map = {
    'Angus Cook': ["Angus Cook", 'AC'],
    'Barbara Nattabi': ["Barbara Nattabi", 'BN'],
    'David Preen': ["David Preen", 'DP'],
    'Fiona Pixely': ["Fiona Pixely", 'FP'],
    'Helen Wilcox': ["Helen Wilcox", 'HW'],
    'Jo Chua': ["Jo Chua", 'JC'],
    'Julie Saunders': ["Julie Saunders", 'JS'],
    'Liz Quail': ["Liz Quail", 'LQ'],
    'Marcus Dabner': ["Marcus Dabner", 'MD'],
    'Nicole Swarbrick': ["Nicole Swarbrick", 'NS'],
    'Patricia Martinez': ["Patricia Martinez", 'PM'],
    'Paul McGurgan': ["Paul McGurgan", 'PM'],
    "Peter Tan": ["Peter Tan", "PT"],
    'Rob White': ["Rob White", 'RW'],
    'Shao Tneh': ["Shao Tneh", 'ST'],
    'Thomas Wilson': ["TW", "Thomas Wilson", 'Tom Wilson'],
    'Tina Carter': ["Tina Carter", 'TC'],
    'Zaza Lyons': ["Zaza Lyons", 'ZL'],
}

type_to_location_map: dict[str,list] = {
    "Lab": [
        "Physiology Lab", "AHBL G05", "ANHB G05", "PHSL G11"],
    "Workshop": ["Med Lib e-learning"],
    "SGL": ["Pathology Museum"],
    "Clinical Skills": ["N Block"],
    "Lecture": [
        *location_indicators_map["FJC"],
        *location_indicators_map["Ross"],
        *location_indicators_map["McCusker"],
    ]
}

# words that, if found in the description, indicate the type of session
#TODO: indicator values should be regexes, e.g. r"(?i)Lab .+ Group \d+"
type_indicators = {
    "Clinical Skills": ["Clinical Skills", "Clin Skills"],
    "SGL": ["SGL", "Small Group Learning"],
    "Lab": ["Lab Group", "ANHB G05", "PHSL G11"],
    "Assessment": ["Assessment", "^OSCE", '^Exam ', "IN SEMESTER TEST"],
    "TBL": ["TBL"],
    'Workshop': ['Workshop'],
    "Deadline": ["Assignment due"],
}

def find_indicator(indicator_map, content):
    """
    @param indicator_map: dict[str, list[str]] - key is the value to be returned, value is a list of regex indicator patterns
    @param content: str - the content to search for indicators
    @return: str - the key of the first indicator found in the content
    """
    for key, indicators in indicator_map.items():
        for indicator in indicators:
            if re.search(indicator, content.strip(), re.IGNORECASE):
                return key
    return None

def standardise_from_indicator(indicator_map, symbol):
    """
    look for the symbol in the indicator_map and return the key if found
    @param indicator_map: dict[str, list[str]] - key is the value to be
    returned, value is a list of indicators
    @param symbol: str - the symbol to search for
    """
    for key, indicators in indicator_map.items():
        for indicator in indicators:
            if indicator.lower() in symbol.strip().lower():
                return key
    return None


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
    
    # First try to find one of the standard location indicators
    for location, indicators in location_indicators_map.items():
        for indicator in indicators:
            if indicator.lower() in event_description.strip().lower():
                return location

    matches = [x.strip() for x in re.findall(r'\[([^\]]+)\]', event_description)]
    return "" if not matches else matches[0]
    # if matches:
    #     for match in matches:
    #         if not is_invalid_location(match):
    #             rtn_location = match.strip()
    #             standardised_location = standardise_from_indicator(location_indicators_map, rtn_location)
    #             rtn_location = standardised_location if standardised_location else rtn_location
    #             break

    #     return rtn_location

def add_missing_location(df):
    # if 'location' column is empty, try to extract location from 'description' column
    for index, row in df.iterrows():
        if pd.isna(row['location']) or row['location'].strip() == "":
            location = extract_location(row['description'])
            df.at[index, 'location'] = location
        found_locations.add(location)
    return df


def set_subject(df): 
    # for missing 'subject' values, search in 'description' column
    for index, row in df.iterrows():
        if df.at[index, 'session_type'].lower() in [x.lower() for x in SESSION_TYPES_WITHOUT_SUBJECTS]:
            df.at[index, 'subject'] = ""
            continue
        subject_0 = ""
        if not pd.isna(row['subject']):
            subject_0 = row['subject'].strip()
        if subject_0:
            ## If subject is already set, standardise it
            subject_1 = standardise_from_indicator(subject_indicators_map, subject_0)
        else:
            ## If subject is not set, try to find an indicator in the description
            subject_1 = find_indicator(subject_indicators_map, row['description'])
        if not subject_1:
            ## If no indicator found, use the first word of the description as the subject
            subject_1 = row['description'].split()[0] if row['description'] else ""
        new_subject = subject_1 if subject_1 else subject_0
        found_subjects.add(new_subject)
        df.at[index, 'subject'] = new_subject
        found_subjects.add(new_subject)
    return df


def set_session_type(df):
    # for missing 'session_type' values, search in 'description' column
    for index, row in df.iterrows():
        session_type = find_indicator(type_indicators, row['description'])
        if session_type:
            df.at[index, 'session_type'] = session_type
            continue
        # infer from location
        elif not pd.isna(row['location']):
            suggested_session_type = standardise_from_indicator(type_to_location_map, row['location'])
            session_type = suggested_session_type if suggested_session_type else ""
            if session_type:
                df.at[index, 'session_type'] = session_type
    return df

def extract_group_numbers(description):
    match = re.search(r'(?i)\bGroups?\s*(\d+(\s*-\s*\d+)?)\b', description)
    if not match:
        return ""
    # Remove spaces and return the group numbers as a string
    groups_substring = re.sub(" ", "", match.group(1).strip())
    return "'" + groups_substring if groups_substring else ""

def add_groups_column(df):
    # Add a 'groups' column based on the 'description' column. Blank if session_type is lecture, otherwise uses number range found after word 'Group' or 'Groups'.
    df['groups'] = df.apply(lambda row: extract_group_numbers(row['description']) if row['session_type'].lower() != 'lecture' else "", axis=1)
    return df

def add_groups_list_column(df):
    # Add a 'groups_list' column based on the 'groups' column, splitting by '-'
    def split_groups(groups_str):
        if not groups_str:
            return []
        if '-' in groups_str:
            start, end = groups_str.lstrip("'").split('-')
            return [str(i) for i in range(int(start), int(end) + 1)]
        else:
            return [groups_str.lstrip("'")]
    
    df['groups_list'] = df['groups'].apply(split_groups)
    return df

def set_row_topic(row):
    # assume topic is after "<subject> - " and before the next '(' or '['
    match = re.search(r'(.*?)(?:\(|\[|$)', row['description'])
    if match:
        # Remove the subject part from the topic
        topic = match.group(1).strip()
        # Remove any leading subject name if it matches the subject column
        if row['subject'] and topic.lower().startswith(row['subject'].lower()):
            topic = topic[len(row['subject']):].strip()
        # remove any leading hyphen, colon or dash
        topic = re.sub(r'^[\-\:\s]+', '', topic)
        return topic

    return match.group(1).strip() if match else ""

def add_topics(df):
    # assume topic is after "<subject> - " and before the next '(' or '['
    df['topic'] = df.apply(set_row_topic, axis=1)
    return df

def trim_topic(df):
    """ Remove anything from topic after and including terms that appear in location, or a pair of brackets """
    for index, row in df.iterrows():
        topic = row['topic']
        # # Check against location indicators
        # for loc in all_location_indicators:
        #     if loc in topic:
        #         topic = topic.split(loc)[0].strip()
        #         break
        # Check for brackets
        match = re.search(r'(.*?)(?:\(|\[|$)', topic)
        if match:
            topic = match.group(1).strip()
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


def is_mandatory_session(row) -> bool:
    """
    Determines if a session is mandatory based on its type and description.
    """
    if row['session_type'] in MANDATORY_SESSION_TYPES:
        return True
    if any(indicator in row['description'] for indicator in MANDATORY_INDICATORS):
        return True
    return False


def add_is_mandatory_column(df):
    """
    Adds a column 'is_mandatory' to the dataframe.
    If the session_type is 'Assessment', it is mandatory.
    Otherwise, it is not mandatory.
    """
    df['is_mandatory'] = df.apply(lambda x: 1 if is_mandatory_session(x) else 0, axis=1)
    # df['is_mandatory'] = df.apply(is_mandatory_session, axis=1)
    return df


def drop_useless_rows(df):
    """
    Drops rows that are not useful for the timetable.
    These are rows that contain 'NON-TEACHING WEEK' or 'Public Holiday' in the description.
    """
    # TODO: log dropped rows
    df = df[~df['description'].str.contains('|'.join(DROP_ROW_INDICATORS), case=False, na=False)]
    return df


def add_event_length(row):
    """
    Adds an 'event_length' column to the row if 'start_time' and 'end_time' are present.
    """
    time_blank = False
    if pd.isna(row['start_time']) or pd.isna(row['end_time']):
        time_blank = True
    if not row['start_time'] or not row['end_time']:
        time_blank = True

    if time_blank:
        if row['location'].lower() == "online":
            return 1
        else:
            return None

    start_time = pd.to_datetime(row['start_time'], format='%H:%M', errors='coerce')
    end_time = pd.to_datetime(row['end_time'], format='%H:%M', errors='coerce')
    if pd.notna(start_time) and pd.notna(end_time):
        return (end_time - start_time).total_seconds() / 60 / 60  # return length in hours
    
    return None


def add_event_lengths(df):
    """
    Adds an 'event_length' column to the dataframe.
    The length is calculated as the difference between 'end_time' and 'start_time'.
    """
    df['event_length'] = df.apply(add_event_length, axis=1)
    return df


def drop_unwanted_groups(df, include_groups: Union[list[str], str] = "all"):
    """Drops rows from the DataFrame where the 'groups_list' column does not contain any of the specified groups
    AND if the 'groups' column is NOT empty.
    
    @param df: pandas DataFrame - the input DataFrame
    @param include_groups: list[str], "all", str 
        - list of group numbers to include (e.g. ['1', '2', '3'])
        - "all" to include all groups
        - str of comma-separated group numbers (e.g. '1,3,5') or range (e.g. '1-5') can be mixed (e.g. '1,3-5,7')
    @return: pandas DataFrame - the filtered DataFrame
    """
    GROUPS_COLUMN = 'groups_list'

    if not GROUPS_COLUMN in df.columns:
        return df
    if include_groups == "all":
        return df
    if isinstance(include_groups, str):
        include_groups = include_groups.split(',')
        # expand ranges like '1-5' into ['1', '2', '3', '4', '5']
        expanded_groups = []
        for grp in include_groups:
            if '-' in grp:
                start, end = grp.split('-')
                expanded_groups.extend([str(i) for i in range(int(start), int(end) + 1)])
            else:
                expanded_groups.append(grp.strip())
        include_groups = expanded_groups
    include_groups_set = set(include_groups)
    groups_lists = df[GROUPS_COLUMN].tolist()
    keep_mask = [
        not groups or any(group in include_groups_set for group in groups)
        for groups in groups_lists
    ]
    return df[keep_mask]


def post_process_events(df):
    df = drop_useless_rows(df)
    df = remove_duplicates(df)
    df = add_missing_location(df)
    df = set_session_type(df)
    df = set_subject(df)
    df = add_presenter_column(df)
    df = add_groups_column(df)
    df = add_groups_list_column(df)
    df = drop_unwanted_groups(df)
    df = add_topics(df)
    df = trim_topic(df)
    df = add_is_mandatory_column(df)
    df = add_event_lengths(df)
    return df




