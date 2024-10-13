import requests
import Utility
import os
import SystemPath
import time
import json

class APImanager:
    def __init__(self, owner: str, repository: str, token: str):
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
        self.__token = token
        self.__creation_date = self.__get_start_date_repository()
        self.__main_language = self.__get_main_programming_language()
        self.__contributors = self.__get_repository_contributors()

    def get_creation_date(self):
        """
        returns the creation date of the repository
        """
        return self.__creation_date
    
    def get_contributors(self):
        """
        returns the number of contributors to the repository
        """
        return self.__contributors

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
        print("Query the creation date of the repository")
        response = requests.get(base_url, headers)

        if response.status_code == 200:
            self.handle_rate_limit(response.headers)
            data = response.json()
            creation_date = Utility.convert_string_to_date(data["created_at"][:10])
            return creation_date
        elif response.status_code == 404:
            return f"Project '{self.__owner}' not found for user '{self.__repository}'."
        else:
            print(f"Error {response.status_code}")
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
        print("Query the main programming language of the repository")
        try:
            response = requests.get(url, headers=headers, timeout= (10, 30))

            if response.status_code == 200:
                self.handle_rate_limit(response.headers)
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
            repository_size(int): the size of the repository during the specified date
        """
        commit_url = f"https://api.github.com/repos/{self.__owner}/{self.__repository}/commits/{sha}"
        headers = {"Authorization": f"Bearer {self.__token}"}
        commit_response = requests.get(commit_url, headers=headers)
        if commit_response.status_code == 200: self.handle_rate_limit(commit_response.headers)
        commit_data = commit_response.json()
        stats = commit_data["stats"] if "stats" in commit_data else {"additions": 0, "deletions": 0}
        lines_added = stats["additions"]
        lines_removed = stats["deletions"]

        tree_url = f"https://api.github.com/repos/{self.__owner}/{self.__repository}/git/trees/{sha}"
        tree_response = requests.get(tree_url, headers= headers)
        repository_size = 0
        if tree_response.status_code == 200: 
            self.handle_rate_limit(tree_response.headers)
            tree_data = tree_response.json()

            for tree in tree_data.get("tree", []):
                repository_size += tree.get("size", 0)

        return lines_added, lines_removed, repository_size
    
    def __get_repository_contributors(self):
        """
        Query the git hub API to get the number of contributors to the repository
        """
        base_url = "https://api.github.com"
        headers = {
            "Authorization": f"token {self.__token}"
        }
        print("Query the number of contributors to the repository")
        #Get the API URL of the specified repository
        repo_url = f"{base_url}/repos/{self.__owner}/{self.__repository}"

        try:
            # Make a GET request to the GitHub API to get the repository
            response = requests.get(repo_url, headers=headers, timeout=(10, 30))
            response.raise_for_status()  # Check for errors in the response

            # Extract URL to get contributors from JSON response
            repo_data = response.json()
            contributors_url = repo_data["contributors_url"]

            #Initialize a list to hold all contributor data
            all_contributors_data = []

            # Keep getting contributor data as long as there are pages available
            while contributors_url:
                # Make a new request to get contributor data for the current page
                contributors_response = requests.get(contributors_url, headers=headers)
                contributors_response.raise_for_status()

                # Extract contributor data from the JSON response for the current page
                contributors_data = contributors_response.json()
                all_contributors_data.extend(contributors_data)

                # Check if there are other pages
                if "next" in contributors_response.links:
                    contributors_url = contributors_response.links["next"]["url"]
                else:
                    # If there are no other pages, break the loop
                    contributors_url = None
                self.handle_rate_limit(contributors_response.headers)

            # Calculate the total number of contributors
            contributors_count = len(all_contributors_data)

            return contributors_count

        except requests.exceptions.RequestException as e:
            print(f"Error in request: {e}")
            return None
    
    def get_all_stargazers(self):
        """
        The function calculates the number of stars for each day from the creation date of the repository
        Output:
            stargazers_with_dates(list): the list of days with the number of stars that the repository had on that day
        """
        url = "https://api.github.com/graphql"
        headers = {
            "Authorization": f"Bearer {self.__token}"
        }
        end_cursor = None
        stargazers_with_dates = []

        while True:
            after_param = f'after: "{end_cursor}"' if end_cursor else ''
            query = f"""
            query {{
            repository(owner: "{self.__owner}", name: "{self.__repository}") {{
                stargazers(first: 100, {after_param}) {{
                edges {{
                    starredAt
                    node {{
                    login
                    }}
                }}
                pageInfo {{
                    endCursor
                    hasNextPage
                }}
                }}
            }}
            }}
            """

            response = requests.post(url, headers=headers, json={"query": query})

            if response.status_code == 200:
                data = response.json()
                stargazers_data = data.get("data", {}).get("repository", {}).get("stargazers", {}).get("edges", [])
                page_info = data.get("data", {}).get("repository", {}).get("stargazers", {}).get("pageInfo", {})
                stargazers_with_dates += [(stargazer["node"]["login"], Utility.convert_string_to_date(stargazer["starredAt"][:10])) for stargazer in stargazers_data]

                if not page_info.get("hasNextPage"):
                    break

                end_cursor = page_info["endCursor"]

                # Gestisci il rate limit: attesa di 1 secondo tra le richieste
                time.sleep(1)
            elif response.status_code == 401:
                print("Authentication error. Check the validity of the personal access token.")
                return []
            elif response.status_code == 403:
                print("Personal access token limit reached. Wait before trying again.") ## FIXME
                return []
            else:
                print(f"Failed to fetch stargazers for {self.__owner}/{self.__repository}. Error code: {response.status_code}")
                return []

        return stargazers_with_dates
    

    def handle_rate_limit(self, response_headers):
        """
        The function checks the remaining rate limit of the token and in case the number of remaining requests is equal to 0, 
        the function suspends the program, until the rate limit is restored
        Args:
            response_headers: the header of the response of the gi hub api, which contains the information regarding the rate limit
        """
        if "X-RateLimit-Remaining" in response_headers:
            remaining_requests = int(response_headers["X-RateLimit-Remaining"])
            #reset_timestamp = int(response_headers["X-RateLimit-Reset"])

            while remaining_requests < 5:
                print("Rate limit exceeded. Swapping token...")
                self.__token = Utility.getRandomToken()
                # Attenzione: è necessario attendere fino al reset_timestamp prima di effettuare ulteriori richieste
                #current_timestamp = int(time.time())
                #sleep_duration = max(0, reset_timestamp - current_timestamp) + 5  # Aggiungi 5 secondi di margine
                #print(f"Rate limit exceeded. Sleeping for {sleep_duration} seconds...")
                #time.sleep(sleep_duration)
    
    def get_all_issues(self):
        """
        the function by querying the git hub api obtains all the issues made from the day the repository was created to today. 
        For each issue we get date, author and id.
        """
        base_url = f"https://api.github.com/repos/{self.__owner}/{self.__repository}/issues"
        headers = {
            "Authorization": f"token {self.__token}"
        }

        all_issues = []
        page = 1
        while True:
            params = {"page": page, "per_page": 100}  # Imposta il numero di issue per pagina
            response = requests.get(base_url, headers=headers, params=params)

            if response.status_code == 200:
                self.handle_rate_limit(response.headers)
                issues = json.loads(response.text)
                if not issues:  # Nessuna issue rimanente, esci dal ciclo
                    break
                all_issues.extend(issues)
                page += 1
            else:
                print(f"Error  {response.status_code}: Unable to get issues.")
                break
        issues_data = []
        for issue in all_issues:
            date = issue["created_at"]
            author = issue["user"]["login"]
            issue_number = issue["number"]
            issue_data = {
                "date": date,
                "author": author,
                "id": issue_number
            }
            issues_data.append(issue_data)

        return issues_data
