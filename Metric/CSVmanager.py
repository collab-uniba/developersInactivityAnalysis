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
        data = pd.read_csv(path_file)
        collums = data.columns
        for index, row in data.iterrows():
            date = Utility.convert_string_to_date(row[collums[2]])
            author = row[collums[1]]
            sha = row[collums[0]]
            lines_added, lines_removed, repository_size = self.__apiManeger.get_commit_infomations_sha(sha)
            commit_stats = {
                'sha': sha,
                'author': author,
                'date': date,
                'lines_added': lines_added,
                'lines_removed': lines_removed,
                'repository_size': repository_size
            }
            commit_list.append(commit_stats)
        
        return commit_list
    
