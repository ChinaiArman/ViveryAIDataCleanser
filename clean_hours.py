"""
"""


# PACKAGE IMPORTS
import openai
import argparse
import pandas as pd
import re
from datetime import datetime

# LOCAL FILE IMPORTS


# AI CONSTANTS
from keys import SOUTH_CENTRAL_API_KEY as OAI_API

# MISC CONSTANTS
INT_TO_DAY_OF_MONTH = {"1": ["1st", "First"], "2": ["2nd"], "3": ["3rd"], "4": ["4th"], "5": ["5th"], "": ""}
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
HOUR_TYPES = ["Weekly", "Every Other Week", "Day of Month", "Week of Month"]




# HELPERS
def create_id_hours_dict(df: pd.DataFrame) -> dict:
    """
    Create a dictionary mapping `Program External IDs` to `Hours Uncleaned` from a DataFrame.

    Args:
        - `df` (pd.DataFrame): A Pandas DataFrame containing data.

    Preconditions:
        - The DataFrame `df` must have columns `Program External ID` and `Hours Uncleaned`.
        - `Program External ID` column should contain unique identifiers.
        - `Hours Uncleaned` column should contain the hours data.

    Returns:
        - dict: A dictionary mapping `Program External IDs` (str) to `Hours Uncleaned` (str).

    Raises:
        - None

    Example:
        >>> import pandas as pd
        >>> data = {
        ...     'Program External ID': ['ID1', 'ID2', 'ID3'],
        ...     'Hours Uncleaned': ['x', 'y', 'z']
        ... }
        >>> df = pd.DataFrame(data)
        >>> result = create_id_hours_dict(df)
        >>> print(result)
        {'ID1': 'x', 'ID2': 'y', 'ID3': 'z'}
    """
    id_hours_dict = {}

    for _, row in df.iterrows():
        id_hours_dict[row["Program External ID"]] = str(row["Hours Uncleaned"]).strip()

    return id_hours_dict


def call_oai(prompt: str) -> str:
    """
    Calls the `Vivery Clean Hours Training Model` to format uncleaned hours into "bulk-upload-ready" hour entries. 

    Args:
        - `prompt` (str): An hour entry to be cleaned using the `Vivery Clean Hours Training Model`.

    Preconditions:
        - The OpenAI API key and other configuration details should be correctly set up in a separate `keys.py` file and imported with the constants at the top of the file.
            
            >>> API_KEY = {
                "key": "...",
                "base": "...",
                "engine": "..."
            }

        - The `prompt` should be a string.
        - The `Vivery Clean Hours Training Model` and `Microsoft Azure OAI` services must be online and operational to be called upon.

    Returns:
        - str: The hours, cleaned and formatted for the bulk upload file template. 

    Raises:
        - None

    Example:
        >>> response = call_oai("Every Monday, from 3pm-5pm")
        >>> print(response)
        'Monday,15:00,17:00,,,,,,,,Weekly,,,'
    """
    openai.api_type = "azure"
    openai.api_base = OAI_API["base"]
    openai.api_version = "2022-12-01"
    openai.api_key = OAI_API["key"]
    response = openai.Completion.create(
        engine=OAI_API["engine"],
        prompt=f"{prompt}",
        temperature=0.4,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        best_of=1,
        stop=["%%"]
    )
    return response["choices"][0]["text"]


def format_hours_iteratively(id_hours_dict: dict) -> dict:
    """
    Creates a dictionary of `Program External IDs` and their formatted-hour counterparts. 

    Args:
        - `id_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the original unformatted hour values as values.

    Preconditions:
        - The `id_hours_dict` should be a dictionary with `Program External IDs` as keys and string representations of unformatted hours as values.
        - All `call_oai` preconditions must be satisfied.

    Returns:
        - dict: A dictionary containing `Program External IDs` as keys and formatted hour values as values.

    Raises:
        - None

    Example:
        >>> id_hours = {
        ...     "ID1": "Every Monday, from 3pm-5pm",
        ...     "ID2": "3rd Tuesday and Wednesday, from 9am-10am"
        ... }
        >>> formatted_hours = format_hours_iteratively(id_hours)
        >>> print(formatted_hours)
        {
            "ID1": "Monday,15:00,17:00,,,,,,,,Weekly,,,", 
            "ID2": "Tuesday,9:00,10:00,,,,,,,3,Day of Month,,,;Wednesday,9:00,10:00,,,,,,,2,Day of Month,,,"
        }
    """
    cleaned_hours_dict = {}

    for key, value in id_hours_dict.items():
        new_value = call_oai(value)
        new_value = new_value
        cleaned_hours_dict[key] = new_value
    
    return cleaned_hours_dict


def filter_invalid_values(id_hours_dict: dict, cleaned_hours_dict: dict, is_valid_hours_dict: dict) -> dict:
    """
    Removes cleaned hour entries that failed one or more tests during the testing phase. This process flags them for human review, returning the hours to their original, unformatted state.

    Args:
        - `id_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the original unformatted hour values as values.
        - `cleaned_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the cleaned/formatted hour values as values.
        - `is_valid_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.

    Preconditions:
        - `id_hours_dict` should be a dictionary with the `Program External IDs` as keys and string representations of hours as values.
        - `cleaned_hours_dict` should be a dictionary with the `Program External IDs` as keys and cleaned/formatted hour values as values.
        - `is_valid_hours_dict` should be a dictionary with the `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.

    Returns:
        - dict: A dictionary containing the `Program External IDs` as keys and the hours in their final state (invalid hours returned to original state, valid hours in a formatted state).

    Raises:
        - None

    Example:
        >>> id_hours = {
        ...     "ID1": "Every Monday, from 3pm-5pm",
        ...     "ID2": "3rd Tuesday and Wednesday, from 9am-10am"
        ... }
        >>> cleaned_hours = {
        ...     "ID1": "Monday,15:00,17:00,,,,,,,,Weekly,,,",
        ...     "ID2": "Tuesday,9:00,10:00,,,,,,,3,Day of Month,,,;Wednesday,9:00,10:00,,,,,,,2,Day of Month,,,"
        ... }
        >>> is_valid = {
        ...     "ID1": True,
        ...     "ID2": False
        ... }
        >>> valid_hours = filter_invalid_values(id_hours, cleaned_hours, is_valid)
        >>> print(valid_hours)
        {
            "ID1": "Monday,15:00,17:00,,,,,,,,Weekly,,,",
            "ID2": "3rd Tuesday and Wednesday, from 9am-10am"
        }
    """
    valid_hours_dict = {}

    for key, _ in cleaned_hours_dict.items():
        if is_valid_hours_dict[key]:
            valid_hours_dict[key] = cleaned_hours_dict[key]
        else:
            valid_hours_dict[key] = id_hours_dict[key]
            
    return valid_hours_dict


def convert_id_hours_dict_to_df(cleaned_hours_dict: dict, is_valid_hours_dict: dict, df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert the cleaned hours dictionary into a DataFrame, filling in formatted hour entries when valid and preserving original data for invalid entries 

    Args:
        - `cleaned_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the cleaned/formatted hour values as values.
        - `is_valid_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.
        - `df` (pd.DataFrame): The original DataFrame containing program data.

    Preconditions:
        - 'cleaned_hours_dict' should be a dictionary with `Program External IDs` as keys and cleaned/formatted hour values as values.
        - 'is_valid_hours_dict' should be a dictionary with `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.
        - 'df' should be a pandas DataFrame containing program data with a "Program External ID" column.

    Returns:
        - pd.DataFrame: A new DataFrame with cleaned/formatted hour values for valid entries and original data for invalid entries. This DataFrame's format matches that of the `Bulk Upload` file

    Raises:
        - None

    Example:
        >>> program_data = pd.DataFrame({
        ...     "Program External ID": ["ID1", "ID2"],
        ...     # Other program data columns...
        ... })
        >>> cleaned_hours = {
        ...     "ID1": "Monday,15:00,17:00,,,,,,,,Weekly,,,",
        ...     "ID2": "3rd Tuesday and Wednesday, from 9am-10am"
        ... }
        >>> is_valid = {
        ...     "ID1": True,
        ...     "ID2": False
        ... }
        >>> cleaned_hours_df = convert_id_hours_dict_to_df(cleaned_hours, is_valid, program_data)
        >>> print(cleaned_hours_df)
            "Program External ID"   # Unrelated Columns   # Formatted Hours Related Columns (CSV)
        0              "ID1"          ...     ...           "Monday","15:00","17:00",,,,,,,,"Weekly",,,,      
        1              "ID2"          ...     ...           ,,,,,,,,,,,,,"3rd Tuesday and Wednesday, from 9am-10am",  
    """
    # Create new DF
    cleaned_hours_df = pd.DataFrame(columns=df.columns)

    # Iterate over Program IDs
    for id in df["Program External ID"].to_list():
        new_entries = []
        row = df.loc[df['Program External ID'] == id].values.tolist()[0]

        # Create new row if valid cleaning
        if is_valid_hours_dict[id]:
            row = row[0:len(df.columns) - 15]
            list_of_entries = cleaned_hours_dict[id].split(";")
            for entry in list_of_entries:
                entry = entry.split(',')
                entry = row + entry + [""]
                new_entries.append(entry)

        # Add row to new DF
        if is_valid_hours_dict[id]:
            for entry in new_entries:
                try:
                    cleaned_hours_df.loc[len(cleaned_hours_df)] = entry
                except ValueError:
                    cleaned_hours_df.loc[len(cleaned_hours_df)] = row + [""] * 15
        else:
            cleaned_hours_df.loc[len(cleaned_hours_df)] = row
    
    # Return DF
    return cleaned_hours_df




# TESTS
def test_valid_day_of_week(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    Test the validity of the day of the week entries in the cleaned hours dictionary.

    Args:
        - `_` (dict): [UNUSED] `id_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the original unformatted hour values as values.
        - `cleaned_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the cleaned/formatted hour values as values.
        - `is_valid_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.

    Preconditions:
        - `cleaned_hours_dict` should be a dictionary with the `Program External IDs` as keys and cleaned/formatted hour values as values.
        - `is_valid_hours_dict` should be a dictionary with the `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.

    Returns:
        - dict: An updated `is_valid_dict` with the validity of day of the week entries for each program.

    Raises:
        - None

    Example:
        >>> cleaned_hours = {
        ...     "ID1": "Monday,15:00,17:00,,,,,,,,Weekly,,,",
        ...     "ID2": "Mursday,12:00,13:00,,,,,,3,,Week of Month,,,",
        ...     "ID3": "Tuesday,9:00,10:00,,,,,,,3,Day of Month,,,;Wednesday,9:00,10:00,,,,,,,2,Day of Month,,,"
        ... }
        >>> is_valid = {
        ...     "ID1": True,
        ...     "ID2": True,
        ...     "ID3": False
        ... }
        >>> updated_validity = test_valid_day_of_week(cleaned_hours, is_valid)
        >>> print(updated_validity)
        {
            "ID1": True,
            "ID2": False,
            "ID3": False
        }
    """
    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            is_valid = value[0] in DAYS_OF_WEEK and is_valid

        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict


def test_valid_entry_format(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    Test the validity of entry format in the cleaned hours dictionary.

    Args:
        - `_` (dict): [UNUSED] `id_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the original unformatted hour values as values.
        - `cleaned_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the cleaned/formatted hour values as values.
        - `is_valid_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.

    Preconditions:
        - `cleaned_hours_dict` should be a dictionary with the `Program External IDs` as keys and cleaned/formatted hour values as values.
        - `is_valid_hours_dict` should be a dictionary with the `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.

    Returns:
        - dict: An updated `is_valid_dict` with the validity of entry format for each program.

    Raises:
        - None

    Example:
        >>> cleaned_hours = {
        ...     "ID1": "Monday,15:00,17:00,,,,,,,,Weekly,,,",
        ...     "ID2": "Monday,12:00,13:00,3,Week of Month;",
        ...     "ID3": "Tuesday,9:00,10:00,,,,,,,3,Day of Month,,,;Wednesday,9:00,10:00,,,,,,,2,Day of Month,,,"
        ... }
        >>> is_valid = {
        ...     "ID1": True,
        ...     "ID2": True,
        ...     "ID3": False
        ... }
        >>> updated_validity = test_valid_entry_format(cleaned_hours, is_valid)
        >>> print(updated_validity)
        {
            "ID1": True,
            "ID2": False,
            "ID3": False
        }
    """
    for key, value in cleaned_hours_dict.items():
        count_semicolons = value.count(";")
        count_commas = value.count(",")
        is_valid = 13 + count_semicolons * 13 == count_commas
        is_valid = (count_semicolons < 1 and count_commas == 13) or (count_semicolons >= 1 and count_commas > 13) and is_valid
        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict


def test_valid_open_closed_hours(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    Test the validity of open and closed hours format in the cleaned hours dictionary.

    Args:
        - `_` (dict): [UNUSED] `id_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the original unformatted hour values as values.
        - `cleaned_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the cleaned/formatted hour values as values.
        - `is_valid_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.

    Preconditions:
        - `cleaned_hours_dict` should be a dictionary with the `Program External IDs` as keys and cleaned/formatted hour values as values.
        - `is_valid_hours_dict` should be a dictionary with the `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.

    Returns:
        - dict: An updated `is_valid_dict` with the validity of open and closed hours format for each program.

    Raises:
        - None

    Example:
        >>> cleaned_hours = {
        ...     "ID1": "Monday,15:00,17:00,,,,,,,,Weekly,,,",
        ...     "ID2": "Monday,12pm,1pm,,,,,,3,,Week of Month,,,",
        ...     "ID3": "Tuesday,9:00,10:00,,,,,,,3,Day of Month,,,;Wednesday,9:00,10:00,,,,,,,2,Day of Month,,,"
        ... }
        >>> is_valid = {
        ...     "ID1": True,
        ...     "ID2": True,
        ...     "ID3": False
        ... }
        >>> updated_validity = test_valid_open_closed_hours(cleaned_hours, is_valid)
        >>> print(updated_validity)
        {
            "ID1": True,
            "ID2": False,
            "ID3": False
        }
    """
    time_regex = re.compile("^([01]?[0-9]|2[0-3]):[0-5][0-9]$")

    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            is_valid = value[1] != "" and value[2] != "" and is_valid
            is_open_hour_valid = re.search(time_regex, value[1])
            is_closed_hour_valid = re.search(time_regex, value[2])
            is_valid = is_open_hour_valid != None and is_closed_hour_valid != None and is_valid

        is_valid_dict[key] = is_valid_dict[key] and is_valid
    
    return is_valid_dict
            

def test_close_hour_greater_than_open_hour(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    Test if the closing hour is greater than the opening hour for each program in the cleaned hours dictionary.

    Args:
        - `_` (dict): [UNUSED] `id_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the original unformatted hour values as values.
        - `cleaned_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the cleaned/formatted hour values as values.
        - `is_valid_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.

    Preconditions:
        - `cleaned_hours_dict` should be a dictionary with the `Program External IDs` as keys and cleaned/formatted hour values as values.
        - `is_valid_hours_dict` should be a dictionary with the `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.

    Returns:
        - dict: An updated `is_valid_dict` with the validity of closing hours being greater than opening hours for each program.

    Raises:
        - None

    Example:
        >>> cleaned_hours = {
        ...     "ID1": "Monday,15:00,17:00,,,,,,,,Weekly,,,",
        ...     "ID2": "Monday,14:00,13:00,,,,,,3,,Week of Month,,,",
        ...     "ID3": "Tuesday,9:00,10:00,,,,,,,3,Day of Month,,,;Wednesday,9:00,10:00,,,,,,,2,Day of Month,,,"
        ... }
        >>> is_valid = {
        ...     "ID1": True,
        ...     "ID2": True,
        ...     "ID3": False
        ... }
        >>> updated_validity = test_close_hour_greater_than_open_hour(cleaned_hours, is_valid)
        >>> print(updated_validity)
        {
            "ID1": True,
            "ID2": False,
            "ID3": False
        }
    """
    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            try:
                is_valid = datetime.strptime(value[2], "%H:%M") > datetime.strptime(value[1], "%H:%M") and is_valid
            except:
                is_valid = False

        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict


def test_day_of_month_formatting(id_hours_dict: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    Test the formatting and validity of `Day of Month` entries in cleaned hours for each program.

    Args:
        - `id_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the original unformatted hour values as values.
        - `cleaned_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the cleaned/formatted hour values as values.
        - `is_valid_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.

    Preconditions:
        - `cleaned_hours_dict` should be a dictionary with the `Program External IDs` as keys and cleaned/formatted hour values as values.
        - `is_valid_hours_dict` should be a dictionary with the `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.

    Returns:
        - dict: An updated `is_valid_dict` with the validity of `Day of Month` entries in cleaned hours for each program.

    Raises:
        - None

    Example:
        >>> cleaned_hours = {
        ...     "ID1": "Monday,15:00,17:00,,,,,,,,Weekly,,,",
        ...     "ID2": "Thursday,14:00,13:00,,,,,,,7,Day of Month,,,",
        ...     "ID3": "Friday,15:00,17:00,,,,,,,,Year of Week,,,"
        ... }
        >>> is_valid = {
        ...     "ID1": True,
        ...     "ID2": True,
        ...     "ID3": False
        ... }
        >>> updated_validity = test_day_of_month_formatting(cleaned_hours, is_valid)
        >>> print(updated_validity)
        {
            "ID1": True,
            "ID2": False,
            "ID3": False
        }
    """
    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            if value[10] == "Day of Month":
                is_valid = value[9].isdigit() and value[8] == "" and is_valid
            try:
                is_valid = (any(day_of_month_value in id_hours_dict[key] for day_of_month_value in INT_TO_DAY_OF_MONTH[value[9]]) or value[9] == "") and is_valid
            except:
                is_valid = False

        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict


def test_week_of_month_formatting(id_hours_dict: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    Test the formatting and validity of 'Day of Month' entries in cleaned hours for each program.

    Args:
        - `_` (dict): [UNUSED] `id_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the original unformatted hour values as values.
        - `cleaned_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and the cleaned/formatted hour values as values.
        - `is_valid_hours_dict` (dict): A dictionary containing the `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.

    Preconditions:
        - `cleaned_hours_dict` should be a dictionary with the `Program External IDs` as keys and cleaned/formatted hour values as values.
        - `is_valid_hours_dict` should be a dictionary with the `Program External IDs` as keys and Boolean values indicating whether the hour value is valid.

    Returns:
        - dict: An updated `is_valid_dict` with the validity of `Day of Month` entries in cleaned hours for each program.

    Raises:
        - None

    Example:
        >>> cleaned_hours = {
        ...     "ID1": "Monday,15:00,17:00,,,,,,,,Weekly,,,",
        ...     "ID2": "Thursday,14:00,13:00,,,,,,,7,Week of Month,,,",
        ...     "ID3": "Friday,15:00,17:00,,,,,,,,Year of Week,,,"
        ... }
        >>> is_valid = {
        ...     "ID1": True,
        ...     "ID2": True,
        ...     "ID3": False
        ... }
        >>> updated_validity = test_week_of_month_formatting(cleaned_hours, is_valid)
        >>> print(updated_validity)
        {
            "ID1": True,
            "ID2": False,
            "ID3": False
        }
    """
    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            if value[10] == "Week of Month":
                is_valid = value[8].isdigit() and value[9] == "" and is_valid
            try:
                is_valid = (any(day_of_week_value in id_hours_dict[key] for day_of_week_value in INT_TO_DAY_OF_MONTH[value[8]]) or value[8] == "") and is_valid
            except:
                is_valid = False

        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict


def test_weekly_formatting(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    """
    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            if value[10] == "Weekly" or value[10] == "Every Other Week":
                is_valid = value[8] == "" and value[9] == "" and is_valid

        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict


def test_all_null_values_empty_string(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    """
    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            is_valid = value[3] == "" and value[4] == "" and value[5] == "" and value[6] == "" and value[11] == "" and value[12] == "" and value[13] == "" and is_valid

        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict


def test_valid_hour_types(_: dict, cleaned_hours_dict: dict, is_valid_dict: dict) -> dict:
    """
    """
    for key, value in cleaned_hours_dict.items():
        is_valid = True
        list_of_entries = value.split(";")

        for value in list_of_entries:
            value = value.split(",")
            is_valid = value[10] in HOUR_TYPES and is_valid

        is_valid_dict[key] = is_valid_dict[key] and is_valid

    return is_valid_dict




# MAIN
if __name__ == "__main__":
    # Define console parser
    parser = argparse.ArgumentParser(description="Clean a bulk upload files hours")
    # Add file argument
    parser.add_argument("file", action="store", help="A bulk upload file")
    # Console arguments
    args = parser.parse_args()

    # Create DataFrame
    df = pd.read_csv(args.file)
    # Create id_hours Dictionary
    id_hours_dict = create_id_hours_dict(df)
    # Create is_valid_hours Dictionary
    is_valid_hours_dict = {key: True for key, _ in id_hours_dict.items()}

    # Parse Hours through OAI
    cleaned_hours_dict = format_hours_iteratively(id_hours_dict)

    # PRINT ALL OAI RETURNED VALUES (OPTIONAL REMOVE):
    for key, value in cleaned_hours_dict.items():
        print(cleaned_hours_dict[key].split(";"))

    # Test OAI Hours 
    validation_tests = [
        test_day_of_month_formatting,
        test_week_of_month_formatting,
        test_weekly_formatting,
        test_valid_hour_types,
        test_valid_day_of_week,
        test_valid_open_closed_hours,
        test_close_hour_greater_than_open_hour,
        test_all_null_values_empty_string,
        test_valid_entry_format
    ]
    [test(id_hours_dict, cleaned_hours_dict, is_valid_hours_dict) for test in validation_tests]
    print(is_valid_hours_dict)

    # Check Values Still Valid
    valid_id_hours_dict = filter_invalid_values(id_hours_dict, cleaned_hours_dict, is_valid_hours_dict)

    # Convert Back to DF
    cleaned_hours_df = convert_id_hours_dict_to_df(cleaned_hours_dict, is_valid_hours_dict, df)
    cleaned_hours_df.to_csv(args.file.replace(".csv", "") + "_HOURS_CLEANED.csv")
