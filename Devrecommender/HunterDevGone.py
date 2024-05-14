import os
import csv
from datetime import datetime
from datetime import timedelta

def read_G_full_list():
    path = 'developersInactivityAnalysis/Organizations/A80API/G_full_list.csv'
    list = []

    if os.path.exists(path):
        with open(path, mode='r', newline='') as file:
            reader = csv.DictReader(file, delimiter=';')  
            for row_readed in reader:
                if row_readed['repo'] == 'github/linguist':
                    row = {
                        'dev': row_readed['dev'],
                        'label': row_readed['label'],
                        'after': row_readed['after'] 
                    }
                    list.append(row)

    return list

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

def diff_date(start_date, end_date):
    diff_months = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
    return diff_months

def calculate_consecutive_breaks(pauses_list):
    i = len(pauses_list) - 1

    x, y = pauses_list[i].split('/')
    start_date_corrente = convert_string_to_date(x)
    end_date_corrente = convert_string_to_date(y)
    i -= 1  

    while i >= 0:
        x, y = pauses_list[i].split('/')
        start_date = convert_string_to_date(x)
        end_date = convert_string_to_date(y)
        if start_date_corrente == end_date or start_date_corrente == next_day(end_date):
            start_date_corrente = start_date
            i -= 1
        else:
            break  

    return start_date_corrente, end_date_corrente

def read_pauses_dates_list():
    path = 'developersInactivityAnalysis/Organizations/github/linguist/pauses_dates_list.csv'
    lista_pause_dev = []

    if os.path.exists(path):
        with open(path, newline='', encoding='utf-8') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=';')  
            for row in csvreader:
                    name = row[0]
                    pauses = row[1:]  # prendo le pause
                    if len(pauses) > 0:
                        start_date, end_date = calculate_consecutive_breaks(pauses)
                        durata_ultima_pausa = diff_date(start_date, end_date)
                        lista_pause_dev.append({'dev': name, 'durata_ultima_pausa': durata_ultima_pausa})

    return lista_pause_dev

def devs_gone():
    lista_pause_dev = read_pauses_dates_list()
    lista_devs = read_G_full_list()
    devs_gone = set()  

    for elem in lista_devs:
        if elem['label'] == 'GONE' or elem['after'] == 'GONE':
            devs_gone.add(elem['dev'])
    

    for pause in lista_pause_dev:
        if pause['durata_ultima_pausa'] >= 10:
            devs_gone.add(pause['dev']) 

    return devs_gone


if __name__ == "__main__":
    set = devs_gone()
    path_csv = 'developersInactivityAnalysis/Organizations/github/hunter_dev_gone.csv'
    with open(path_csv, mode='w', newline='') as file_csv:
        writer = csv.writer(file_csv)

        for name in set:
            writer.writerow([name])
    
    print(f"Names were written to the CSV file 'hunter_dev_gone.csv' ")