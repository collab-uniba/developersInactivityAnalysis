import requests
import Utility
import CSVmanager
import os
import SystemPath
import time

class APImanager:
    def __init__(self, owner: str, repository: str, token: str, csv_menager: CSVmanager.CSVmanager):
        """
        the constructor of the APImanager class, which takes care of retrieving information about the repository by querying the git hub API
        Args:
        owner(str): the owner of the repository we are analyzing
        repository(str): the name of the repository we are analyzing
        token(str): the authentication token from github
        csv_menager(CSVmanager.CSVmanager): it is an object of the CSVmanager.CSVmanager class and is used to save the information obtained
        """
        self.__repository = repository
        self.__owner = owner
        self.__csv_maneger = csv_menager
        self.__token = token
        self.__creation_date = self.__get_start_date_repository()
        self.__main_language = self.__get_main_programming_language()

    def get_creation_date(self):
        """
        returns the creation date of the repository
        """
        return self.__creation_date
    
    def get_main_language(self):
        """
        returns the main language of the repository
        """
        return self.__main_language
    
    def __get_start_date_repository(self): 
        """
        query the git hub api to get the creation date of the repository
        """
        base_url = f"https://api.github.com/repos/{self.__owner}/{self.__repository}"
        headers = {"Authorization": f"Bearer {self.__token}"}
        response = requests.get(base_url, headers)

        if response.status_code == 200:
            data = response.json()
            creation_date = Utility.convert_string_to_date(data["created_at"][:10])
            return creation_date
        elif response.status_code == 404:
            print("errore 1")
            return f"Project '{self.__owner}' not found for user '{self.__repository}'."
        else:
            print("errore 2")
            return "An error occurred while fetching data."
    
    def __get_main_programming_language(self):
        """
        query the git hub api to get the main language used in the repository
        """
        url = f"https://api.github.com/repos/{self.__owner}/{self.__repository}/languages"

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {self.__token}"
        }

        try:
            response = requests.get(url, headers=headers)

            if response.status_code == 200:
                language_data = response.json()
                if language_data:
                    main_language = max(language_data, key=language_data.get)
                    return main_language
                else:
                    print("No language information found for the repository.")
            else:
                print("Failed to retrieve language data:", response.status_code)
        except requests.exceptions.RequestException as e:
            print("Error during API request:", e)

        return None
    
    def get_commit_infomations_sha(self, sha: str):
        """
        Returns information about a specific commit
        Args
        sha(str): sha identifier of the commit we want information about
        Output:
        lines_added(int): number of lines added with commit
        lines_removed(int): number of lines removed with commit
        """
        commit_url = f"https://api.github.com/repos/{self.__owner}/{self.__repository}/commits/{sha}"
        headers = {"Authorization": f"Bearer {self.__token}"}
        commit_response = requests.get(commit_url, headers=headers)
        commit_data = commit_response.json()
        stats = commit_data["stats"] if "stats" in commit_data else {"additions": 0, "deletions": 0}
        lines_added = stats["additions"]
        lines_removed = stats["deletions"]

        tree_url = f"https://api.github.com/repos/{self.__owner}/{self.__repository}/git/trees/{sha}"
        tree_response = requests.get(tree_url, headers= headers)
        tree_data = tree_response.json()
        repository_size = 0

        for tree in tree_data.get("tree", []):
            repository_size += tree.get("size", 0)

        return lines_added, lines_removed, repository_size