import pandas as pd
from datetime import datetime, timedelta
import csv
import Utility
import os
import SystemPath
import APImanager

# G_FULL_LIST KEYWORDS
ACTIVE = 'ACTIVE'
GONE = 'GONE'
NON_CODING = 'NON_CODING'


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
        self.__apimanager = APImanager.APImanager(owner, repository, token, self)
        self.__create_metric_folder()
    #===================================================================================================================FUNCTIONS TO READ FILES==================================================================================================================
    def read_commit_list(self):
        """
        The function takes care of reading the file in which all the commits made during the analysis period are present, 
        returns a list where each element of the list is a commit with the relative information
        Output:
        commit_list(list): The list contains all the information about the commits of the analysis period
        """
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
    
    def __create_metric_folder(self):
        """
        The function creates the folder in which to save the files for the metrics, in case it doesn't exist
        """
        metric_folder = SystemPath.get_metric_folder(self.__owner, self.__repository)
        exist = os.path.exists(metric_folder)
        if not exist:
            try:
                os.makedirs(metric_folder)
            except OSError as error:
                print(f"{error}")
    
    def create_LOC_values(self):
        """
        The function takes care of calculating all the information for the LOC metric and creates a file for each meaning of dev_breaks_count
        """
        commit_list = self.read_commit_list()
        start_date = commit_list[0]['date']
        end_date = commit_list[-1]['date']
        LOC_list = self.create_LOC_list(start_date, end_date)
        self.__calculate_LOC_and_size(commit_list, LOC_list)
        self.__calculate_project_stars(LOC_list)

        self.__create_and_save_LOC_TF(start_date, end_date, Utility.copy_list(LOC_list))
        self.__create_and_save_LOC_TF_gone(start_date, end_date, Utility.copy_list(LOC_list))

        self.__create_and_save_LOC_core(start_date, end_date, Utility.copy_list(LOC_list))
        self.create_and_save_LOC_core_gone(start_date, end_date, Utility.copy_list(LOC_list))
        

    def create_LOC_list(self, start_date: datetime.date, end_date: datetime.date):
        """
        The function creates the base list of metric values for LOC
        Args:
            start_date(datetime.date): The starting day for generating the LOC_list
            end_date(datetime.date): The date on which generation of the LOC_list should end
        Output:
            LOC_list(list): The base list for LOC metrics
        """
        st_date = datetime(year= start_date.year, month= start_date.month, day= start_date.day).date()
        ed_date = datetime(year= end_date.year, month= end_date.month, day= end_date.day).date()
        LOC_list = []
        print("Creation of the list containing the analysis data")
        creation_date = self.__apimanager.get_creation_date()
        main_language = self.__apimanager.get_main_language()
        number_contributors = self.__apimanager.get_contributors()
        while st_date <= ed_date:
            project_age = st_date - creation_date
            loc_stats = {
                'date': st_date,
                'LOC' : 0,
                'dev_breaks_count': 0,
                'project_age' : project_age.days,
                'project_contributors': number_contributors,
                'project_name': self.__repository,
                'project_language': main_language,
                'project_size': 0,
                'project_stars':0
            }
            LOC_list.append(loc_stats)

            st_date = Utility.next_day(st_date)
        
        return LOC_list
    
    def __calculate_LOC_and_size(self, commit_list, LOC_list):
        """
        The function calculates the LOC and repository size values for each item in the list
        Args:
            commit_list(list): The list containing information about all commits made in the analysis period
            LOC_list(list):In the list we will insert the values calculated from the commit_list
        """
        i = 0
        number_elem = len(LOC_list)
        T_status = 5
        print("Calculate the size of the repository and the LOC value for each day")
        while i < len(LOC_list):
            for elem in commit_list:
                if elem['date'] == LOC_list[i]['date']:
                    lines_added, lines_removed, repository_size = self.__apimanager.get_commit_infomations_sha(elem['sha'])
                    commit_list.remove(elem)
                    LOC_list['LOC'] += lines_added + lines_removed
                    LOC_list['project_size'] = repository_size
            i +=1
            perc = int(i/number_elem * 100)
            if perc == T_status:
                T_status += 5
                print('Days calculated {}%'.format(perc))

    def __calculate_project_stars(self, LOC_list):
        """
        The function calculates the number of stars assigned to the project each day of the analysis period
        Args:
            LOC_list(list): the calculated values for the project_stars metric will be inserted in the list
        """
        print("Repository project starts calculation for each day")
        stargazers_data = self.__apimanager.get_all_stargazers()
        i = 0
        j = 0
        counter = 0
        number_elem = len(LOC_list)
        T_status = 5
        stargazers_data = self.__apimanager.get_all_stargazers()
        while i < len(LOC_list):
            username, starred_at = stargazers_data[j]
            if starred_at < LOC_list[i]['date']:
                flag = True
                while flag and j < len(stargazers_data):
                    username, starred_at = stargazers_data[j]
                    if starred_at < LOC_list[i]['date']:
                        j += 1
                        counter += 1
                    else:
                        flag = False
            elif starred_at == LOC_list[i]['date']:
                counter += 1
                LOC_list[i]['project_stars'] = counter
                j +=1
            elif starred_at > LOC_list[i]['date']:
                LOC_list[i]['project_stars'] = counter
                i += 1
            perc = int(i/number_elem * 100)
            if perc == T_status:
                T_status += 5
                print('Days calculated {}%'.format(perc))

    def __create_dev_breaks_count_TF(self, date_start: datetime, date_end: datetime):
        """
        The function calculates the dev_breaks_count values for each day of the analysis period considering them as the number of developer TFs that are inactive or gone.
        Args:
            date_start(datetime): analysis period start date
            date_end(datetime): analysis period end date
        Outoput:
            dev_breaks_count(list): the list contains the values of the dev_breaks_count metric for each day of the analysis period
        """
        print("Calculate the number of TF developers that are inactive or gone for each day")
        tf_devs = self.__get_list_tf()
        st_date = datetime(year= date_start.year, month= date_start.month, day= date_start.day).date()
        ed_date = datetime(year= date_end.year, month= date_end.month, day= date_end.day).date()
        pauses_tf = []
        total_days = (ed_date - st_date).days
        T_status = total_days - 30
        dev_breaks_count = []
        for login in tf_devs:
            pauses_tf.append(self.__get_list_pauses(login))
        
            
        while st_date <= ed_date:
            count = 0
            for list_pause in pauses_tf:
                count += self.__counts_number_of_developers_paused_on_a_date(st_date, list_pause)
            row = {
                'date': st_date,
                'number_devs':count
            }
            dev_breaks_count.append(row)
            calculated_days = (ed_date - st_date).days
            if calculated_days == T_status:
                days = total_days - T_status
                print(f"Days calculated {days} out of {total_days}")
                if T_status <= 30:
                    T_status = 0
                else:
                    T_status -= 30
            st_date = Utility.next_day(st_date)
        
        return dev_breaks_count
    
    def __counts_number_of_developers_paused_on_a_date(self, date: datetime, pauses_list):
        """
        The function calculates the number of developers on break on a given day
        Args:
            date(datetime): the date for which we want to know the number of devs on pause
            pauses_list(list): the list we need to analyze to figure out the number of developers on hiatus on a given date
        """
        for elem in pauses_list:
            start_date_p = elem['date_start']
            end_date_p = elem['date_end']
            if start_date_p <= date <= end_date_p:
                return 1
        
        return 0
    
    def __get_list_tf(self):
        """
        The function reads the TF_devs file and returns the TF developer login list
        Output:
            list_TF_devs(list): the list contains the logins of the TF developers of the repository
        """
        file_path = SystemPath.get_path_to_TF_devs(self.__owner, self.__repository)
        list_TF_devs = []

        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=';')
                for row in csvreader:
                    if len(row) == 2:
                        name, login = row
                        list_TF_devs.append(login.strip())

            return list_TF_devs[1:]

        except FileNotFoundError:
            print(f"File '{file_path}' not found.")
            return None
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
        

    def __get_list_pauses(self, name_dev: str):
        """
        The function reads the pauses_list.csv file and returns a developer's pauses list
        Args:
            name_dev(str): the login of the developer whose pause list we want
        """
        list_pauses = []
        file_path = SystemPath.get_path_pauses_list(self.__owner, self.__repository)
        try:
            with open(file_path, newline='', encoding='utf-8') as csvfile:
                csvreader = csv.reader(csvfile, delimiter=';')
                for row in csvreader:
                    name = row[0]
                    pauses = row[1:]
                    if name == name_dev:
                        return self.__transform_list_pauses(pauses)
            
            return list_pauses
        except FileNotFoundError:
            print(f"File '{file_path}' not found.")
            return None
        except Exception as e:
            print(f"Error reading file: {e}")
            return None
        
    def __transform_list_pauses(self, pauses):
        """
        The function takes a developer's pause list generated by __get_list_pauses and creates a new list, each element of the list represents a pause and separates the start date and the end date
        Args:
            pauses(list): the list of pauses generated by __get_list_pauses that we need to transform
        """
        list_pauses = []
        for elem in pauses:
            date_start, date_end = elem.split("/")
            pause = {
                'date_start': Utility.convert_string_to_date(date_start),
                'date_end': Utility.convert_string_to_date(date_end)
            }
            list_pauses.append(pause)
        
        return list_pauses
        
    def __create_and_save_LOC_TF(self, start_date: datetime, end_date: datetime, LOC_list):
        """
        The function calculates dev_breaks_count as the number of developer TFs paused or gone and then generates the file with all the LOC metrics
        Args:
            start_date(datetime): analysis period start date
            end_date(datetime): analysis period end date
            LOC_list(list): the list that will contain all the values of the metrics for LOC for each day of the analysis period
        """
        i = 0
        list_dev_breaks_count = self.__create_dev_breaks_count_TF(start_date, end_date)
        while i in range(0, len(list_dev_breaks_count)):
            LOC_list[i]['dev_breaks_count'] = list_dev_breaks_count[i]['number_devs']
            i += 1
        print("End of calculation for inactive or gone TF developers, data saving...")
        self.__save_data_for_loc(LOC_list, SystemPath.get_path_file_LOC_TF(self.__owner, self.__repository))
        
    def __save_data_for_loc(self, LOC_list, file_path: str):
        """
        The function takes care of saving files for the LOC metric
        Args:
            LOC_list(list): the list of values to save
            file_path(str): the path to save the file
        """
        exist = os.path.isfile(file_path)
        fieldnames = ['date', 'LOC', 'dev_breaks_count', 'project_age', 
                     'project_contributors' ,'project_name', 'project_language', 
                      'project_size', 'project_stars']
        with open(file_path, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(LOC_list)

    def create_dev_breaks_count_TF_gone(self, start_date: datetime, end_date: datetime):
        """
        The function calculates the dev_breaks_count values for each day of the analysis period considering them as the number of developer TFs that are gone.
        Args:
            date_start(datetime): analysis period start date
            date_end(datetime): analysis period end date
        Outoput:
            dev_breaks_count(list): the list contains the values of the dev_breaks_count metric for each day of the analysis period
        """
        print("Calculate the number of TF developers that are gone for each day")
        g_list = self.read_G_full_list_for_TF()
        st_date = datetime(year= start_date.year, month= start_date.month, day= start_date.day).date()
        ed_date = datetime(year= end_date.year, month= end_date.month, day= end_date.day).date()
        all_days = []
        while st_date <= ed_date:
            row = {
                'date': st_date,
                'devs_count': 0
            }
            all_days.append(row)
            st_date = Utility.next_day(st_date)
        
        for dev in g_list:
            i = 0
            while i in range(0, len(g_list)):
                if dev['previously'] == GONE:
                    if all_days[i]['date'] <= dev['start_date']:
                        all_days[i]['devs_count'] += 1
                
                if dev['label'] == GONE:
                    if dev['start_date'] <= all_days[i]['date'] <= dev['end_date']:
                        all_days[i]['devs_count'] += 1
                
                if dev['after'] == GONE:
                    if all_days[i]['date'] > dev['end_date']:
                        all_days[i]['devs_count'] += 1
                i += 1
        return all_days



    def read_G_full_list_for_TF(self):
        """
        The function reads the G_full_list.csv file obtaining the information on the TF developers contained in the file
        Output:
            list_tf_dates(list): the list contains the information on the TF developers extrapolated from the G_full_list.csv file
        """
        tf_devs = self.__get_list_tf()
        path_file = SystemPath.get_path_G_full_list()
        list_tf_dates = []
        login_tf_list = []
        repo_name = self.__owner + '/' + self.__repository
        for elem in tf_devs:
            name, login = elem
            login_tf_list.append(login)

        try:
            with open(path_file, "r", encoding= 'utf-8') as file:
                csvreader = csv.reader(file, delimiter=';')
                for dev, repo, dates, len, Tfov, previously, label, after in csvreader:
                    if repo == repo_name:
                        if dev in login_tf_list:
                            date_interval = dates.split('/')
                            start_date = Utility.convert_string_to_date(date_interval[0])
                            end_date = Utility.convert_string_to_date(date_interval[-1])
                            elem = {
                                'dev' : dev,
                                'start_date': start_date,
                                'end_date': end_date,
                                'previously': previously,
                                'label': label,
                                'after': after
                            }
                            list_tf_dates.append(elem)
            
            return list_tf_dates
        except FileNotFoundError:
            print(f"File '{path_file}' non trovato.")
        except Exception as e:
            print(f"Errore durante la lettura del file: {e}")
            return None

    def __create_and_save_LOC_TF_gone(self, start_date, end_date, LOC_list):
        """
        The function calculates dev_breaks_count as the number of developer TFs gone and then generates the file with all the LOC metrics
        Args:
            start_date(datetime): analysis period start date
            end_date(datetime): analysis period end date
            LOC_list(list): the list that will contain all the values of the metrics for LOC for each day of the analysis period
        """
        i = 0
        list_dev_breaks_count = self.create_dev_breaks_count_TF_gone(start_date, end_date)
        i = 0
        while i in range(0, len(list_dev_breaks_count)):
            LOC_list[i]['dev_breaks_count'] = list_dev_breaks_count[i]['devs_count']
            i += 1
        print("End of calculation for gone TF developers, data saving...")
        self.__save_data_for_loc(LOC_list, SystemPath.get_path_file_LOC_TF_gone(self.__owner, self.__repository))

    def get_list_core_devs(self):
        """
        The function reads the A80_devs.csv file and returns the core developers login list
        Output:
            list_core_devs(list): the list contains the logins of the core developers of the repository
        """
        file_path = SystemPath.get_path_core_devs(self.__repository)
        list_core_devs = []

        try:
            with open(file_path, "r", encoding= 'utf-8') as file:
                csvreader = csv.reader(file, delimiter=';')
                for row in csvreader:
                    login, commits, percentage = row
                    list_core_devs.append(login.strip())
            return list_core_devs
        except FileNotFoundError:
            print(f"File '{file_path}' non trovato.")
            return None
        except Exception as e:
            print(f"Errore durante la lettura del file: {e}")
            return None
    
    def create_dev_breaks_count_core(self, date_start: datetime, date_end: datetime):
        """
        The function calculates dev_breaks_count as the number of gone developers gone or inactive and then generates the file with all the LOC metrics
        Args:
            start_date(datetime): analysis period start date
            end_date(datetime): analysis period end date
            LOC_list(list): the list that will contain all the values of the metrics for LOC for each day of the analysis period
        """
        core_devs = self.get_list_core_devs()
        print("Calculate the number of core developers that are gone or inactive for each day")
        st_date = datetime(year= date_start.year, month= date_start.month, day= date_start.day).date()
        ed_date = datetime(year= date_end.year, month= date_end.month, day= date_end.day).date()
        total_days = (ed_date - st_date).days
        T_status = total_days - 30
        pauses_core = []
        dev_breaks_count = []
        for login in core_devs:
            pauses_core.append(self.__get_list_pauses(login))
        
        while st_date <= ed_date:
            count = 0
            for list_pause in pauses_core:
                count += self.__counts_number_of_developers_paused_on_a_date(st_date, list_pause)
            row = {
                'date': st_date,
                'number_devs': count
            }
            dev_breaks_count.append(row)
            calculated_days = (ed_date - st_date).days
            if calculated_days == T_status:
                days = total_days - T_status
                print(f"Days calculated {days} out of {total_days}")
                if T_status <= 30:
                    T_status = 0
                else:
                    T_status -= 30
            st_date = Utility.next_day(st_date)
        
        return dev_breaks_count
    

    def __create_and_save_LOC_core(self, start_date, end_date, LOC_list):
        """
        The function calculates dev_breaks_count as the number of core developers gone or inactive and then generates the file with all the LOC metrics
        Args:
            start_date(datetime): analysis period start date
            end_date(datetime): analysis period end date
            LOC_list(list): the list that will contain all the values of the metrics for LOC for each day of the analysis period
        """
        list_dev_breaks_count = self.create_dev_breaks_count_core(start_date, end_date)
        i = 0
        while i in range(0, len(list_dev_breaks_count)-1):
            LOC_list[i]['dev_breaks_count'] = list_dev_breaks_count[i]['number_devs']
            i += 1
        print("End of calculation for inactive or gone core developers, data saving...")
        self.__save_data_for_loc(LOC_list, SystemPath.get_path_file_LOC_core(self.__owner, self.__repository))

    def create_and_save_LOC_core_gone(self, start_date, end_date, LOC_list):
        """
        The function calculates dev_breaks_count as the number of core developers gone and then generates the file with all the LOC metrics
        Args:
            start_date(datetime): analysis period start date
            end_date(datetime): analysis period end date
            LOC_list(list): the list that will contain all the values of the metrics for LOC for each day of the analysis period
        """
        list_dev_breaks_count = self.create_dev_breaks_count_core_gone(start_date, end_date)
        i = 0
        while i in range(0, len(list_dev_breaks_count)-1):
            LOC_list[i]['dev_breaks_count'] = list_dev_breaks_count[i]['number_devs']
            i += 1
        print("End of calculation for gone core developers, data saving...")
        self.__save_data_for_loc(LOC_list, SystemPath.get_path_file_LOC_core_gone(self.__owner, self.__repository))

    def create_dev_breaks_count_core_gone(self, start_date: datetime, end_date: datetime):
        """
        The function calculates dev_breaks_count as the number of gone developers gone and then generates the file with all the LOC metrics
        Args:
            start_date(datetime): analysis period start date
            end_date(datetime): analysis period end date
            LOC_list(list): the list that will contain all the values of the metrics for LOC for each day of the analysis period
        """
        print("Calculate the number of core developers that are gone for each day")
        g_list = self.read_G_full_list_for_core()
        st_date = datetime(year= start_date.year, month= start_date.month, day= start_date.day).date()
        ed_date = datetime(year= end_date.year, month= end_date.month, day= end_date.day).date()
        all_days = []
        while st_date <= ed_date:
            row = {
                'date': st_date,
                'devs_count': 0
            }
            all_days.append(row)
            st_date = Utility.next_day(st_date)
        
        for dev in g_list:
            i = 0
            while i in range(0, len(all_days)):
                if dev['previously'] == GONE:
                    if all_days[i]['date'] <= dev['start_date']:
                        all_days[i]['devs_count'] += 1
                
                if dev['label'] == GONE:
                    if dev['start_date'] <= all_days[i]['date'] <= dev['end_date']:
                        all_days[i]['devs_count'] += 1
                
                if dev['after'] == GONE:
                    if all_days[i]['date'] > dev['end_date']:
                        all_days[i]['devs_count'] += 1
                i += 1
        return all_days
    
    def read_G_full_list_for_core(self):
        """
        The function reads the G_full_list.csv file obtaining the information on the core developers contained in the file
        Output:
            list_tf_dates(list): the list contains the information on the core developers extrapolated from the G_full_list.csv file
        """
        core_devs = self.get_list_core_devs()
        path_file = SystemPath.get_path_G_full_list()
        list_core_dates = []
        repo_name = self.__owner + '/' + self.__repository
        try:
            with open(path_file, "r", encoding= 'utf-8') as file:
                csvreader = csv.reader(file, delimiter=';')
                for dev, repo, dates, len, Tfov, previously, label, after in csvreader:
                    if repo == repo_name:
                        print("alemeno una volta trovo il repo")
                        if dev in core_devs:
                            print("esiete un dev")
                            date_interval = dates.split('/')
                            start_date = Utility.convert_string_to_date(date_interval[0])
                            end_date = Utility.convert_string_to_date(date_interval[-1])
                            elem = {
                                'dev' : dev,
                                'start_date': start_date,
                                'end_date': end_date,
                                'previously': previously,
                                'label': label,
                                'after': after
                            }
                            list_core_dates.append(elem)
            
            return list_core_dates
        except FileNotFoundError:
            print(f"File '{path_file}' non trovato.")
        except Exception as e:
            print(f"Errore durante la lettura del file: {e}")
            return None
    
