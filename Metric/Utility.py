import datetime
from datetime import datetime, timedelta
import copy

#CONSTANT
MONTH_DAY_START = 1
MONTH_DAY_END_30 = 30
MONTH_DAY_END_31 = 31
MONTH_DAY_END_28 = 28
MONTH_DAY_END_29 = 29
MONTH_END_WITH_30 = [11, 4, 6, 9]
FEBRUARY = 2
TOKEN_FILE_NAME = "tokens" 

#DATE FUNCTION
def creation_start_date_month(month, year):
    """
    The function generates the date of the first day of the month having month and year
    Args:
        month(int): The month of the date of which we want the first day of the month
        year(int): The year of the date of which we want the first day of the month
    """
    date_start = datetime.datetime(year, month, MONTH_DAY_START)
    return date_start.strftime("%Y-%m-%d")

def creation_end_date_month(month, year):
    """
    The function generates the date of the last day of the month having month and year
    Args:
        month(int): The month of the date of which we want the last day of the month
        year(int): The year of the date of which we want the last day of the month
    """
    if month in MONTH_END_WITH_30:
        date_end = datetime.datetime(year, month, MONTH_DAY_END_30)
    elif month == FEBRUARY:
        if year % 4 == 0:
            date_end = datetime.datetime(year, month, MONTH_DAY_END_29)
        else:
            date_end = datetime.datetime(year, month, MONTH_DAY_END_28)
    else:
        date_end = datetime.datetime(year, month, MONTH_DAY_END_31)
    
    return date_end

def creation_end_date(date: datetime):
    date_end_month = datetime(month=date.month, year= date.year, day= date.day).date()
    if date.month in MONTH_END_WITH_30:
        date_end_month = date_end_month.replace(day=30)
    elif date.month == FEBRUARY:
        if date.year%4 == 0:
            date_end_month =date_end_month.replace(day= 29)
        else:
            date_end_month = date_end_month.replace(day= 28)
    else:
        date_end_month = date_end_month.replace(day=31)
    
    return date_end_month

def getTokensList():
    """Return the tokens list"""
    with open(TOKEN_FILE_NAME) as rf:
        tokensList = rf.readlines()
    tokensList = [token.strip() for token in tokensList] # Remove whitespace characters like `\n` at the end of each line
    return tokensList

def getToken(index):
    """Return the token the chosen index. Index ranges (1-N)"""
    tokensList = getTokensList()
    token = tokensList[index - 1]
    return token


def convert_string_to_date(date_string, date_format = "%Y-%m-%d"):
    """
    Takes as input a date in string format and converts it to date type in the format specified in input
    Args:
        date_string(str): the string we want to convert to date
        date_format(str): the format in which we want to save the converted date
    Return:
        date(date): the converted date

    """
    date = datetime.strptime(date_string, date_format).date()
    return date

def next_day(date):
    """
    Takes a date as input and returns the next day's date
    Args:
        date(str or date): the date of which we want the next day
    Return:
        next_date(date): the date of the next day
    """
    if type(date) == str:
        date = convert_string_to_date(date, "%Y-%m-%d")
    
    next_date = date + timedelta(days=1)

    return next_date

def day_before(date):
    """
    takes a date as input and returns the date of the previous day
    Args:
        date(str or date): the date of which we want the previus day
    Return:
        date_before(date): the date of the previus day
    """
    if type(date) == str:
        date = convert_string_to_date(date, "%Y-%m-%d")
    
    date_before = date - timedelta(days=1)

    return date_before

class Time_lapse:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

    



def get_list_couple_start_date_end_date(st_date1, end_date1, st_date2, end_date2):
    """
    takes 2 time intervals as input and returns a list of time intervals
    Args:
        st_date1(str or date): the starting date of the first interval, must be in the format yyyy-mm-dd
        end_date1(str or date): the end date of the first interval must be in the format yyyy-mm-dd
        st_date2(str or date): the starting date of the second interval, must be in the format yyyy-mm-dd
        end_date(str or date): the end date of the second interval must be in the format yyyy-mm-dd
    Return:
        couple_list:
    """
    couple_list = []
    if type(st_date1) == str:
        st_date1 = convert_string_to_date(st_date1, "%Y-%m-%d")

    if type(end_date1) == str:
        st_date1 = convert_string_to_date(end_date1, "%Y-%m-%d")

    if type(st_date2) == str:
        st_date2 = convert_string_to_date(st_date2, "%Y-%m-%d")

    if type(end_date2) == str:
        end_date2 = convert_string_to_date(end_date2, "%Y-%m-%d")


    

    if st_date1 != st_date2:
        if st_date2 <= day_before(st_date1):
            couple_list.append(Time_lapse(str(st_date2), str(day_before(st_date1))))
        
    if end_date1 != end_date2:
        if end_date2 >= next_day(end_date1):
            couple_list.append(Time_lapse(str(next_day(end_date1)), str(end_date2)))

    return couple_list

def copy_list(list):
    """
    Takes a list as input and returns a copy of it
    """
    return copy.deepcopy(list)

         
