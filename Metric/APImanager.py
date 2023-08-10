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
        print("I ask the Git hub api for the creation date of the repository")
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
        print("I request the main programming language of the repository from the Git hub api")

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
    
    def __get_repository_contributors(self):
        """
        Query the git hub API to get the number of contributors to the repository
        """
        base_url = "https://api.github.com"
        headers = {
            "Authorization": f"token {self.__token}"
        }

        # Ottieni l'URL API del repository specificato
        repo_url = f"{base_url}/repos/{self.__owner}/{self.__repository}"

        try:
            # Effettua una richiesta GET all'API di GitHub per ottenere il repository
            response = requests.get(repo_url, headers=headers)
            response.raise_for_status()  # Verifica eventuali errori nella risposta

            # Estrai l'URL per ottenere i contributori dalla risposta JSON
            repo_data = response.json()
            contributors_url = repo_data["contributors_url"]

            # Inizializza una lista per contenere tutti i dati dei contributori
            all_contributors_data = []

            # Continua a ottenere i dati dei contributori finché ci sono pagine disponibili
            while contributors_url:
                # Effettua una nuova richiesta per ottenere i dati dei contributori per la pagina corrente
                contributors_response = requests.get(contributors_url, headers=headers)
                contributors_response.raise_for_status()

                # Estrai i dati dei contributori dalla risposta JSON per la pagina corrente
                contributors_data = contributors_response.json()
                all_contributors_data.extend(contributors_data)

                # Verifica se ci sono altre pagine
                if "next" in contributors_response.links:
                    contributors_url = contributors_response.links["next"]["url"]
                else:
                    # Se non ci sono altre pagine, interrompi il ciclo
                    contributors_url = None

            # Calcola il numero totale di contributori
            contributors_count = len(all_contributors_data)

            return contributors_count

        except requests.exceptions.RequestException as e:
            print(f"Errore nella richiesta: {e}")
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
                print("Errore di autenticazione. Controlla il token di accesso personale.")
                return []
            elif response.status_code == 403:
                print("Limite di utilizzo raggiunto. Aspetta qualche minuto prima di riprovare.")
                return []
            else:
                print(f"Failed to fetch stargazers for {self.__owner}/{self.__repository}. Error code: {response.status_code}")
                return []

        return stargazers_with_dates