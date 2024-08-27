"""
"""


# PACKAGE IMPORTS
import openai
import os
import pandas as pd
import re
from datetime import datetime
import time

# LOCAL FILE IMPORTS


# AI CONSTANTS
from dotenv import load_dotenv
load_dotenv()

# MISC CONSTANTS
INT_TO_DAY_OF_MONTH = {"1": ["1st", "First"], "2": ["2nd", "Second"], "3": ["3rd", "Third"], "4": ["4th", "Fourth"], "5": ["5th", "Fifth"], "": ""}
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
HOUR_TYPES = ["Weekly", "Every Other Week", "Day of Month", "Week of Month", "Call for Information"]
UNCLEANED_HOURS_COLUMN = "Hours Uncleaned"
INVALID_CHARACTERS = ""




# HELPERS
def call_oai(prompt: str) -> str:
    """
    """
    openai.api_type = "azure"
    openai.api_base = os.getenv("OAI_BASE")
    openai.api_version = "2023-09-15-preview"
    openai.api_key = os.getenv("OAI_KEY")
    response = openai.Completion.create(
        engine=os.getenv("OAI_ENGINE"),
        prompt=f"{prompt}",
        temperature=0.2,
        max_tokens=256,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        best_of=1,
        stop=["%%"]
    )
    time.sleep(0.05)
    return response["choices"][0]["text"]


def postprocess_string(case: str) -> str:
    """
    """
    case = case.split(",")
    if case[7] != "" and "".join(case[0:7]) == "" and "".join(case[8:]) == "":
        case[10] = "Call for Information"
    if case[7] == "For information":
        case[7] = "Call for Information"
    return ",".join(case)


def preprocess_string(case: str) -> str:
    """
    """
    return case.strip().replace("/", ", ")


def format_input_string(case: str) -> dict:
    """
    """
    case.replace("/", ", ")
    split_value = case.split(";")
    response = map(lambda x: postprocess_string(call_oai(preprocess_string(x))), split_value)
    new_value = ";".join(response)
    response = {
        "base": case,
        "formatted": new_value,
        "isValid": True
    }
    return response


# TESTS
def test_valid_day_of_week(response: dict) -> None:
    """
    """
    if response["isValid"] == False:
        return
    list_of_entries = response["formatted"].split(";")
    is_valid = True
    for value in list_of_entries:
        value = value.split(",")
        try:
            response["isValid"] = value[0] in DAYS_OF_WEEK or (value[0] == "" and value[10] == "Call for Information") and response["isValid"]
        except:
            response["isValid"] = False
    return


def test_valid_entry_format(response: dict) -> None:
    """
    """
    if response["isValid"] == False:
        return
    count_semicolons = response["formatted"].count(";")
    count_commas = response["formatted"].count(",")
    is_valid = 13 + count_semicolons * 13 == count_commas
    is_valid = (count_semicolons < 1 and count_commas == 13) or (count_semicolons >= 1 and count_commas > 13) and is_valid
    response["isValid"] = response["isValid"] and is_valid
    return


def test_valid_open_closed_hours(response: dict) -> None:
    """
    """
    if response["isValid"] == False:
        return
    time_regex = re.compile("^([01]?[0-9]|2[0-3]):[0-5][0-9]$")
    list_of_entries = response["formatted"].split(";")
    is_valid = True
    for value in list_of_entries:
        value = value.split(",")
        if value[10] == "Call for Information":
            continue
        try:
            is_open_hour_valid = re.search(time_regex, value[1])
            is_closed_hour_valid = re.search(time_regex, value[2])
            is_valid = (is_open_hour_valid != None or value[1] == "") and (is_closed_hour_valid != None or value[2] == "") and is_valid
        except:
            is_valid = False
        response["isValid"] = response["isValid"] and is_valid
    return
            

def test_close_hour_greater_than_open_hour(response: dict) -> None:
    """
    """
    if response["isValid"] == False:
        return
    list_of_entries = response["formatted"].split(";")
    is_valid = True
    for value in list_of_entries:
        value = value.split(",")
        try:
            is_valid = datetime.strptime(value[2], "%H:%M") > datetime.strptime(value[1], "%H:%M") and is_valid
        except ValueError:
            is_valid = value[10] == "Call for Information" and is_valid
        except:
            is_valid = False
    response["isValid"] = response["isValid"] and is_valid
    return 


def test_day_of_month_formatting(response: dict) -> None:
    """
    """
    if response["isValid"] == False:
        return
    list_of_entries = response["formatted"].split(";")
    is_valid = True
    for value in list_of_entries:
        value = value.split(",")
        try:
            if value[10] == "Day of Month":
                is_valid = value[9].isdigit() and value[8] == "" and is_valid
                is_valid = (any(day_of_month_value.lower() in response["original"].lower() for day_of_month_value in INT_TO_DAY_OF_MONTH[value[9]]) or value[9] == "") and is_valid
        except:
            is_valid = False
    response["isValid"] = response["isValid"] and is_valid
    return 


def test_week_of_month_formatting(response: dict) -> None:
    """
    """
    if response["isValid"] == False:
        return
    list_of_entries = response["formatted"].split(";")
    is_valid = True
    for value in list_of_entries:
        value = value.split(",")
        try:
            if value[10] == "Week of Month":
                is_valid = value[8].isdigit() and value[9] == "" and is_valid
                is_valid = (any(day_of_week_value.lower() in response["original"].lower() for day_of_week_value in INT_TO_DAY_OF_MONTH[value[8]]) or value[8] == "") and is_valid
        except:
            is_valid = False
    response["isValid"] = response["isValid"] and is_valid
    return


def test_weekly_formatting(response: dict) -> None:
    """
    """
    if response["isValid"] == False:
        return
    list_of_entries = response["formatted"].split(";")
    is_valid = True
    for value in list_of_entries:
        value = value.split(",")
        try:
            if value[10] == "Weekly" or value[10] == "Every Other Week":
                is_valid = value[8] == "" and value[9] == "" and is_valid
        except:
            is_valid = False
    response["isValid"] = response["isValid"] and is_valid
    return


def test_call_for_information_formatting(response: dict) -> None:
    """
    """
    if response["isValid"] == False:
        return
    list_of_entries = response["formatted"].split(";")
    is_valid = True
    for value in list_of_entries:
        value = value.split(",")
        try:
            if value[10] == "Call for Information":
                is_valid = len("".join(value[0:7])) == 0 and len("".join(value[8:10])) == 0 and len("".join(value[11:])) == 0 and is_valid
        except:
            is_valid = False
    response["isValid"] = response["isValid"] and is_valid
    return


def test_all_null_values_empty_string(response: dict) -> None:
    """
    """
    if response["isValid"] == False:
        return
    list_of_entries = response["formatted"].split(";")
    is_valid = True
    for value in list_of_entries:
        value = value.split(",")
        try:
            is_valid = value[3] == "" and value[4] == "" and value[5] == "" and value[6] == "" and value[11] == "" and value[12] == "" and value[13] == "" and is_valid
        except:
            is_valid = False
    response["isValid"] = response["isValid"] and is_valid
    return


def test_valid_hour_types(response: dict) -> None:
    """
    """
    if response["isValid"] == False:
        return
    list_of_entries = response["formatted"].split(";")
    is_valid = True
    for value in list_of_entries:
        value = value.split(",")
        try:
            is_valid = value[10] in HOUR_TYPES and is_valid
        except:
            is_valid = False
    response["isValid"] = response["isValid"] and is_valid
    return




# MAIN
def normalize_input_string(case: str) -> str:
    """
    """
    response = format_input_string(case)
    validation_tests = [
        test_day_of_month_formatting,
        test_week_of_month_formatting,
        test_weekly_formatting,
        test_valid_hour_types,
        test_valid_day_of_week,
        test_valid_open_closed_hours,
        test_close_hour_greater_than_open_hour,
        test_all_null_values_empty_string,
        test_valid_entry_format,
        test_call_for_information_formatting,
    ]
    [test(response) for test in validation_tests]
    return response
