import pandas as pd
from datetime import datetime, timedelta
import csv
import Utility
import os
import SystemPath


class CSVmanager:
    def __init__(self, owner: str, repository: str, token: str):
        """
        The constructor of the CSVmanager class, which manages the reading and writing of the files for the calculation of the metrics
        Args:
        owner(str): the owner of the repository we are analyzing
        repository(str): the name of the repository we are analyzing
        token(str): the authentication token from github
        """
        self.__repository = repository
        self.__owner = owner
        self.__token = token
    
    def read_commit_list(self):
        path_file = SystemPath.get_path_to_commit_list(self.__owner, self.__repository)
        commit_list = []
        with open(path_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                sha = row['sha']
                date = Utility.convert_string_to_date(row['date'][:10])
                commit_list.append({
                    'sha': sha,
                    'author': row['author_id'],
                    'date': date
                })
        
        
        return commit_list
    
