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
        print("start calculation for " + str(owner)+ "/" + str(repository))
        self.__repository = repository
        self.__owner = owner
        self.__apimanager = APImanager.APImanager(owner, repository, token)
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
        with open(path_file, 'r', newline = '') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                sha = row['sha']
                date = Utility.convert_string_to_date(row['date'][:10])
                commit_list.append({
                    'sha': sha,
                    'author': row['author_id'],
                    'date': date
                })
        
        commit_list = sorted(commit_list, key=lambda x: x['date'])
        return commit_list
    
    def read_prs_list(self):
        """
        The function takes care of reading the file in which all the pull requests made during the analysis period are present, 
        returns a list where each element of the list is a pull request with the relative information
        Output:
            prs_list(list): The list contains all the information about the pull requests of the analysis period
        """
        path_file = SystemPath.get_path_prs_list(self.__owner, self.__repository)
        prs_list = []
        with open(path_file, 'r', newline = '') as csvfile:
            reader = csv.DictReader(csvfile, delimiter = ';')
            for row in reader:
                id_pr = row['id']
                date = Utility.convert_string_to_date(row['date'][:10])
                author = row['author']
                prs_list.append({
                    'id': id_pr,
                    'date': date,
                    'author': author
                })
        
        return prs_list
    
    def read_issues_list(self):
        """
        The function takes care of reading the file in which all the issues made during the analysis period are present, 
        returns a list where each element of the list is a issue with the relative information
        Output:
            issues_list(list): The list contains all the information about the issues of the analysis period
        """
        path = SystemPath.get_path_issue_list(self.__owner, self.__repository)
        exist = os.path.exists(path)
        if not exist:
            self.save_all_issues()

        issues_list = []
        with open(path, 'r', newline = '') as csvfile:
            reader = csv.DictReader(csvfile, delimiter = ',')
            for row in reader:
                id = row['id']
                date = Utility.convert_string_to_date(row['date'][:10])
                author = row['author']
                issues_list.append({
                    'id': id,
                    'date': date,
                    'author': author
                })
        
        return issues_list
    
    
    def read_LOC_file(self, path: str):
        """
        the function reads the file containing the LOC metric. 
        The file path is requested to specify which of the 4 files with the LOC metric we want to read 
        (TF, TF_gone, core, core_gone)
        Args:
            path(str): the path of the file containing the LOC metric we want to read
        Output:
            LOC_values(list): the list containing the data saved in the read file
        """
        LOC_values = []
        with open (path, 'r', newline = '') as csvfile:
            reader = csv.DictReader(csvfile, delimiter = ',')
            for row in reader:
                LOC_values.append({
                    'date': Utility.convert_string_to_date(row['date']),
                    'LOC': int(row['LOC']),
                    'dev_breaks_count': int(row['dev_breaks_count']),
                    'project_age': int(row['project_age']),
                    'project_contributors': int(row['project_contributors']),
                    'project_name': row['project_name'],
                    'project_language': row['project_language'],
                    'project_size': int(row['project_size']),
                    'project_stars': int(row['project_stars'])
                })
        
        return LOC_values
    
    def read_PRS_file(self, path: str):
        """
        the function reads the file containing the PRS metric. 
        The file path is requested to specify which of the 4 files with the LOC metric we want to read 
        (TF, TF_gone, core, core_gone)
        Args:
            path(str): the path of the file containing the PRS metric we want to read
        Output:
            PRS_values(list): the list containing the data saved in the read file
        """
        PRS_value = []
        with open(path, mode='r', newline='') as file:
            reader = csv.DictReader(file, delimiter=',')
            for row in reader:
                PRS_value.append({
                    'date': Utility.convert_string_to_date(row['date']),
                    'PRS': int(row['PRS']),
                    'dev_breaks_count': row['dev_breaks_count'],
                    'project_age': row['project_age'],
                    'project_contributors': int(row['project_contributors']),
                    'project_name': row['project_name'],
                    'project_language': row['project_language'],
                    'project_size': int(row['project_size']),
                    'project_stars': int(row['project_stars'])

                })
        return PRS_value
    
    def read_ISSUE_file(self, path: str):
        """
        the function reads the file containing the ISSUE metric. 
        The file path is requested to specify which of the 4 files with the LOC metric we want to read 
        (TF, TF_gone, core, core_gone)
        Args:
            path(str): the path of the file containing the LOC metric we want to read
        Output:
            ISSUE_values(list): the list containing the data saved in the read file
        """
        ISSUE_value = []
        with open(path, mode='r', newline='') as file:
            reader = csv.DictReader(file, delimiter=',')
            for row in reader:
                ISSUE_value.append({
                    'date': Utility.convert_string_to_date(row['date']),
                    'ISSUE': int(row['ISSUE']),
                    'dev_breaks_count': row['dev_breaks_count'],
                    'project_age': row['project_age'],
                    'project_contributors': int(row['project_contributors']),
                    'project_name': row['project_name'],
                    'project_language': row['project_language'],
                    'project_size': int(row['project_size']),
                    'project_stars': int(row['project_stars'])

                })
        return ISSUE_value
    
    def create_PRS_file(self):
        """
        The function reads the 4 LOC files, and then replaces the LOC parameter with the PRS parameter, creating the PRS files with the various meanings deo dev_breaks_count
        """
        LOC_values_TF = self.read_LOC_file(SystemPath.get_path_file_LOC_TF(self.__owner, self.__repository))
        LOC_values_TF_gone = self.read_LOC_file(SystemPath.get_path_file_LOC_TF_gone(self.__owner, self.__repository))
        LOC_values_core = self.read_LOC_file(SystemPath.get_path_file_LOC_core(self.__owner, self.__repository))
        LOC_values_core_gone = self.read_LOC_file(SystemPath.get_path_file_LOC_core_gone(self.__owner, self.__repository))
        start_date = LOC_values_TF[0]['date']
        end_date = LOC_values_TF[-1]['date']
        prs_list = self.__calculate_prs_for_days(start_date, end_date)
        i = 0
        while i < len(LOC_values_TF):
            del LOC_values_TF[i]['LOC']
            del LOC_values_TF_gone[i]['LOC']
            del LOC_values_core[i]['LOC']
            del LOC_values_core_gone[i]['LOC']
            LOC_values_TF[i]['PRS'] = prs_list[i]['prs_value']
            LOC_values_TF_gone[i]['PRS'] = prs_list[i]['prs_value']
            LOC_values_core[i]['PRS'] = prs_list[i]['prs_value']
            LOC_values_core_gone[i]['PRS'] = prs_list[i]['prs_value']
            i += 1

        self.__save_data_for_prs(LOC_values_TF, SystemPath.get_path_file_PRS_TF(self.__owner, self.__repository))
        self.__save_data_for_prs(LOC_values_TF_gone, SystemPath.get_path_file_PRS_TF_gone(self.__owner, self.__repository))
        self.__save_data_for_prs(LOC_values_core, SystemPath.get_path_file_PRS_core(self.__owner, self.__repository))
        self.__save_data_for_prs(LOC_values_core_gone, SystemPath.get_path_file_PRS_core_gone(self.__owner, self.__repository))

    def create_issues_file(self):
        """
        The function reads the 4 LOC files, and then replaces the LOC parameter with the ISSUE parameter, creating the PRS files with the various meanings deo dev_breaks_count
        """
        LOC_values_TF = self.read_LOC_file(SystemPath.get_path_file_LOC_TF(self.__owner, self.__repository))
        LOC_values_TF_gone = self.read_LOC_file(SystemPath.get_path_file_LOC_TF_gone(self.__owner, self.__repository))
        LOC_values_core = self.read_LOC_file(SystemPath.get_path_file_LOC_core(self.__owner, self.__repository))
        LOC_values_core_gone = self.read_LOC_file(SystemPath.get_path_file_LOC_core_gone(self.__owner, self.__repository))
        start_date = LOC_values_TF[0]['date']
        end_date = LOC_values_TF[-1]['date']
        issues_list = self.__calculate_issue_for_days(start_date, end_date)
        i = 0
        while i < len(LOC_values_TF):
            del LOC_values_TF[i]['LOC']
            del LOC_values_TF_gone[i]['LOC']
            del LOC_values_core[i]['LOC']
            del LOC_values_core_gone[i]['LOC']
            LOC_values_TF[i]['ISSUE'] = issues_list[i]['issue_value']
            LOC_values_TF_gone[i]['ISSUE'] = issues_list[i]['issue_value']
            LOC_values_core[i]['ISSUE'] = issues_list[i]['issue_value']
            LOC_values_core_gone[i]['ISSUE'] = issues_list[i]['issue_value']
            i += 1

        self.__save_data_for_isu(LOC_values_TF, SystemPath.get_path_file_ISU_TF(self.__owner, self.__repository))
        self.__save_data_for_isu(LOC_values_TF_gone, SystemPath.get_path_file_ISU_TF_gone(self.__owner, self.__repository))
        self.__save_data_for_isu(LOC_values_core, SystemPath.get_path_file_ISU_core(self.__owner, self.__repository))
        self.__save_data_for_isu(LOC_values_core_gone, SystemPath.get_path_file_ISU_core_gone(self.__owner, self.__repository))
        

    def __create_prs_list_for_all_days(self, start_date: datetime.date, end_date: datetime.date):
        """
        The function creates a list which will serve as a basis for counting pull request to day.
        Each element of the list will contain the data parameter and the prs_value parameter (initialized to 0)
        Args:
            start_date(datetime.date): the start date of the analysis period
            end_date(datetime.date): the end date of the analysis period
        Output:
            prs_for_days(list): list for counting pull requests per day
        """
        st_date = datetime(year= start_date.year, month= start_date.month, day= start_date.day).date()
        ed_date = datetime(year= end_date.year, month= end_date.month, day= end_date.day).date()
        prs_for_days = []
        while st_date <= ed_date:
            prs_day = {
                'date': st_date,
                'prs_value' :0
            }
            prs_for_days.append(prs_day)
            st_date = Utility.next_day(st_date)
        
        return prs_for_days
    
    def __create_issue_list_for_all_days(self, start_date: datetime.date, end_date: datetime.date):
        """
        The function creates a list which will serve as a basis for counting issues per day.
        Each element of the list will contain the data parameter and the issue_value parameter (initialized to 0)
        Args:
            start_date(datetime.date): the start date of the analysis period
            end_date(datetime.date): the end date of the analysis period
        Output:
            prs_for_days(list): list for counting issues per day
        """
        st_date = datetime(year= start_date.year, month= start_date.month, day= start_date.day).date()
        ed_date = datetime(year= end_date.year, month= end_date.month, day= end_date.day).date()
        issue_for_days = []
        while st_date <= ed_date:
            issue_day = {
                'date': st_date,
                'issue_value': 0
            }
            issue_for_days.append(issue_day)
            st_date = Utility.next_day(st_date)
        
        return issue_for_days
    
    def __calculate_prs_for_days(self, start_date, end_date):
        """
        the function generates a list with each element containing the date and the number of pull requests on that date
        Args:
            start_date(datetime.date): the start date of the analysis period
            end_date(datetime.date): the end date of the analysis period
        Output:
            prs_for_days(list): the list containing the pull requests count for each day
        """
        prs_list = self.read_prs_list()
        prs_for_days = self.__create_prs_list_for_all_days(start_date, end_date)
        i = 0
        for i in range(0, len(prs_for_days)):
            counter = 0
            for pr in prs_list:
                if prs_for_days[i]['date'] == pr['date']:
                    counter += 1
            
            prs_for_days[i]['prs_value'] = counter
        
        return prs_for_days
    
    def __calculate_issue_for_days(self, start_date, end_date):
        """
        the function generates a list with each element containing the date and the number of issues on that date
        Args:
            start_date(datetime.date): the start date of the analysis period
            end_date(datetime.date): the end date of the analysis period
        Output:
            issues_for_days(list): the list containing the issue count for each day
        """
        issues_list = self.read_issues_list()
        issues_for_days = self.__create_issue_list_for_all_days(start_date, end_date)
        i = 0
        for i in range(0, len(issues_for_days)):
            counter = 0
            for issue in issues_list:
                if issues_for_days[i]['date'] == issue['date']:
                    counter += 1
            
            issues_for_days[i]['issue_value'] = counter
        
        return issues_for_days

    
    def __create_metric_folder(self):
        """
        The function creates the folder in which to save the files for the metrics, in case it doesn't exist
        """
        metric_folder = SystemPath.get_metric_folder(self.__owner, self.__repository)
        exist = os.path.exists(metric_folder)
        if not exist:
            try:
                print("Repository metrics will be stored in " + str(metric_folder))
                os.makedirs(metric_folder)
            except OSError as error:
                print(f"{error}")
        else:
            print("Repository metrics folder " + str(self.__owner)+"/"+ str(self.__repository) + " already exists in " + str(metric_folder))
    
    def create_LOC_values(self):
        """
        The function takes care of calculating all the information for the LOC metric and creates a file for each meaning of dev_breaks_count
        """
        commit_list = self.read_commit_list()
        start_date = commit_list[0]['date']
        end_date = commit_list[-1]['date']
        LOC_list = self.create_LOC_list(start_date, end_date)
        self.__calculate_LOC_and_size(commit_list, LOC_list)
        
        i = 0
        while i < len(LOC_list):
            del LOC_list[i]['done']
            i += 1
        
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
        file_path = SystemPath.get_path_basis_LOC(self.__owner, self.__repository)
        exist = os.path.isfile(file_path)
        if not exist:
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
                    'project_stars':0,
                    'done': False
                }
                LOC_list.append(loc_stats)

                st_date = Utility.next_day(st_date)
            
            return LOC_list
        else:
            LOC_list = self.__read_basis_LOC()
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
            if not LOC_list[i]['done']:
                for elem in commit_list:
                    if elem['date'] == LOC_list[i]['date']:
                        lines_added, lines_removed, repository_size = self.__apimanager.get_commit_infomations_sha(elem['sha'])
                        commit_list.remove(elem)
                        LOC_list[i]['LOC'] += lines_added + lines_removed
                        LOC_list[i]['project_size'] = repository_size
                LOC_list[i]['done'] = True
                self.__update_basis_LOC(LOC_list)
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
            _, starred_at = stargazers_data[j]
            if starred_at < LOC_list[i]['date']:
                flag = True
                while flag and j < len(stargazers_data):
                    _, starred_at = stargazers_data[j]
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
        print("End of calculation for inactive or gone TF developers, saving data ...")
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

    def __save_data_for_prs(self, PRS_list, file_path: str):
        """
        the function takes care of saving the files with the PRS metric
        Args:
            PRS_list(list): the list of values to save
            file_path(str): the path to save the file
        """
        exist = os.path.isfile(file_path)
        fieldnames = ['date', 'PRS', 'dev_breaks_count', 'project_age', 
                     'project_contributors' ,'project_name', 'project_language', 
                      'project_size', 'project_stars']
        with open(file_path, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(PRS_list)

    def __save_data_for_isu(self, ISU_list, file_path: str):
        """
        the function takes care of saving the files with the ISU metric
        Args:
            ISU_list(list): the list of values to save
            file_path(str): the path to save the file
        """
        exist = os.path.isfile(file_path)
        fieldnames = ['date', 'ISSUE', 'dev_breaks_count', 'project_age', 
                     'project_contributors' ,'project_name', 'project_language', 
                      'project_size', 'project_stars']
        with open(file_path, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(ISU_list)

    def save_all_issues(self):
        """
        the function takes care of saving the data relating to the issues
        """
        issues_list = self.__apimanager.get_all_issues()
        path = SystemPath.get_path_issue_list(self.__owner, self.__repository)
        exist = exist = os.path.isfile(path)
        fieldnames = ["date", "author", "id"]
        with open(path, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(issues_list)


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
            login = elem
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
        print("End of calculation for gone TF developers, saving data ...")
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
        print("End of calculation for inactive or gone core developers, saving data...")
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
            LOC_list[i]['dev_breaks_count'] = list_dev_breaks_count[i]['devs_count']
            i += 1
        print("End of calculation for gone core developers, saving data...")
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
                        if dev in core_devs:
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
        

    def __read_basis_LOC(self):
        """
        The function takes care of reading the base of the LOC files, it is called if the generation of the LOC files is started and then interrupted
        """
        file_path = SystemPath.get_path_basis_LOC(self.__owner, self.__repository)
        LOC_list = []
        with open(file_path, mode='r', newline='') as file:
            reader = csv.DictReader(file, delimiter=',')
            for row in reader:
                LOC_list.append({
                    'date': Utility.convert_string_to_date(row['date']),
                    'LOC': int(row['LOC']),
                    'dev_breaks_count': int(row['dev_breaks_count']),
                    'project_age': int(row['project_age']),
                    'project_contributors': int(row['project_contributors']),
                    'project_name': row['project_name'],
                    'project_language': row['project_language'],
                    'project_size': int(row['project_size']),
                    'project_stars': row['project_stars'],
                    'done': row['done'] == 'True'
                })
        return LOC_list
    
    def __update_basis_LOC(self, LOC_list):
        """
        The function updates the base of the LOC files, it is called every time the LOC and project_size value is examined
        """
        file_path = SystemPath.get_path_basis_LOC(self.__owner, self.__repository)
        fieldnames = ['date', 'LOC', 'dev_breaks_count', 'project_age', 
                     'project_contributors' ,'project_name', 'project_language', 
                      'project_size', 'project_stars', 'done']
        with open(file_path, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(LOC_list)

def read_repositories_list():
    """
    The function reads the repositories.txt file present in the Rsources folder returning a list of repository names with owner and name of the repository
    Output:
        repositories_list(list): The list containing the names of the repositories, each element of the list is of the type {'owner': name_owner, 'repository': repo_name}
    """
    path_file = SystemPath.get_path_repositories_list()
    repositories_list = []
    with open(path_file, mode = 'r') as file:
        for line in file:
            row = line.replace('https://github.com/','').strip()
            row = row.split('/')
            repositories_list.append({
                'owner': row[0],
                'repository': row[1]
            })
    
    return repositories_list

def generate_repositories_LOC_TF(token):
    """
    The function takes all the LOC_TF.csv files of the repositories present in the repositories.txt file in Resources folder
    and creates a single list that contains all the data present in the files
    Output:
        repositories_LOC_TF(list): the list containing all the information present in the LOC_TF files of all the analysis repositories
    """
    repositories_list = read_repositories_list()
    repositories_LOC_TF = []
    for repository in repositories_list:
        csv_manager = CSVmanager(repository['owner'], repository['repository'], token)
        if len(repositories_LOC_TF) == 0:
            repositories_LOC_TF = csv_manager.read_LOC_file(SystemPath.get_path_file_LOC_TF(repository['owner'], repository['repository']))
        else:
            repositories_LOC_TF.extend(csv_manager.read_LOC_file(SystemPath.get_path_file_LOC_TF(repository['owner'], repository['repository'])))
    
    return repositories_LOC_TF

def generate_repositories_LOC_TF_gone(token):
    """
    The function takes all the LOC_TF_gone.csv files of the repositories present in the repositories.txt file in Resources folder
    and creates a single list that contains all the data present in the files
    Output:
        repositories_LOC_TF_gone(list): the list containing all the information present in the LOC_TF_gone files of all the analysis repositories
    """
    repositories_list = read_repositories_list()
    repositories_LOC_TF_gone = []
    for repository in repositories_list:
        csv_manager = CSVmanager(repository['owner'], repository['repository'], token)
        if len(repositories_LOC_TF_gone) == 0:
            repositories_LOC_TF_gone = csv_manager.read_LOC_file(SystemPath.get_path_file_LOC_TF_gone(repository['owner'], repository['repository']))
        else:
            repositories_LOC_TF_gone.extend(csv_manager.read_LOC_file(SystemPath.get_path_file_LOC_TF_gone(repository['owner'], repository['repository'])))
    
    return repositories_LOC_TF_gone

def generate_repositories_LOC_core(token):
    """
    The function takes all the LOC_core.csv files of the repositories present in the repositories.txt file in Resources folder
    and creates a single list that contains all the data present in the files
    Output:
        repositories_LOC_core(list): the list containing all the information present in the LOC_core files of all the analysis repositories
    """
    repositories_list = read_repositories_list()
    repositories_LOC_core = []
    for repository in repositories_list:
        csv_manager = CSVmanager(repository['owner'], repository['repository'], token)
        if len(repositories_LOC_core) == 0:
            repositories_LOC_core = csv_manager.read_LOC_file(SystemPath.get_path_file_LOC_core(repository['owner'], repository['repository']))
        else:
            repositories_LOC_core.extend(csv_manager.read_LOC_file(SystemPath.get_path_file_LOC_core(repository['owner'], repository['repository'])))
    
    return repositories_LOC_core

def generate_repositories_LOC_core_gone(token):
    """
    The function takes all the LOC_core_gone.csv files of the repositories present in the repositories.txt file in Resources folder
    and creates a single list that contains all the data present in the files
    Output:
        repositories_LOC_core_gone(list): the list containing all the information present in the LOC_core_gone files of all the analysis repositories
    """
    repositories_list = read_repositories_list()
    repositories_LOC_core_gone = []
    for repository in repositories_list:
        csv_manager = CSVmanager(repository['owner'], repository['repository'], token)
        if len(repositories_LOC_core_gone) == 0:
            repositories_LOC_core_gone = csv_manager.read_LOC_file(SystemPath.get_path_file_LOC_core_gone(repository['owner'], repository['repository']))
        else:
            repositories_LOC_core_gone.extend(csv_manager.read_LOC_file(SystemPath.get_path_file_LOC_core_gone(repository['owner'], repository['repository'])))
    
    return repositories_LOC_core_gone

def generate_repositories_PRS_TF(token):
    """
    The function takes all the PRS_TF.csv files of the repositories present in the repositories.txt file in Resources folder
    and creates a single list that contains all the data present in the files
    Output:
        repositories_PRS_TF(list): the list containing all the information present in the PRS_TF files of all the analysis repositories
    """
    repositories_list = read_repositories_list()
    repositories_PRS_TF = []
    for repository in repositories_list:
        csv_manager = CSVmanager(repository['owner'], repository['repository'], token)
        if len(repositories_PRS_TF) == 0:
            repositories_PRS_TF = csv_manager.read_PRS_file(SystemPath.get_path_file_PRS_TF(repository['owner'], repository['repository']))
        else:
            repositories_PRS_TF.extend(csv_manager.read_PRS_file(SystemPath.get_path_file_PRS_TF(repository['owner'], repository['repository'])))
    
    return repositories_PRS_TF

def generate_repositories_PRS_TF_gone(token):
    """
    The function takes all the PRS_TF_gone.csv files of the repositories present in the repositories.txt file in Resources folder
    and creates a single list that contains all the data present in the files
    Output:
        repositories_PRS_TF_gone(list): the list containing all the information present in the PRS_TF_gone files of all the analysis repositories
    """
    repositories_list = read_repositories_list()
    repositories_PRS_TF_gone = []
    for repository in repositories_list:
        csv_manager = CSVmanager(repository['owner'], repository['repository'], token)
        if len(repositories_PRS_TF_gone) == 0:
            repositories_PRS_TF_gone = csv_manager.read_PRS_file(SystemPath.get_path_file_PRS_TF_gone(repository['owner'], repository['repository']))
        else:
            repositories_PRS_TF_gone.extend(csv_manager.read_PRS_file(SystemPath.get_path_file_PRS_TF_gone(repository['owner'], repository['repository'])))
    
    return repositories_PRS_TF_gone

def generate_repositories_PRS_core(token):
    """
    The function takes all the PRS_core.csv files of the repositories present in the repositories.txt file in Resources folder
    and creates a single list that contains all the data present in the files
    Output:
        repositories_PRS_core(list): the list containing all the information present in the PRS_core files of all the analysis repositories
    """
    repositories_list = read_repositories_list()
    repositories_PRS_core = []
    for repository in repositories_list:
        csv_manager = CSVmanager(repository['owner'], repository['repository'], token)
        if len(repositories_PRS_core) == 0:
            repositories_PRS_core = csv_manager.read_PRS_file(SystemPath.get_path_file_PRS_core(repository['owner'], repository['repository']))
        else:
            repositories_PRS_core.extend(csv_manager.read_PRS_file(SystemPath.get_path_file_PRS_core(repository['owner'], repository['repository'])))
    
    return repositories_PRS_core

def generate_repositories_PRS_core_gone(token):
    """
    The function takes all the PRS_core_gone.csv files of the repositories present in the repositories.txt file in Resources folder
    and creates a single list that contains all the data present in the files
    Output:
        repositories_PRS_core_gone(list): the list containing all the information present in the PRS_core_gone files of all the analysis repositories
    """
    repositories_list = read_repositories_list()
    repositories_PRS_core_gone = []
    for repository in repositories_list:
        csv_manager = CSVmanager(repository['owner'], repository['repository'], token)
        if len(repositories_PRS_core_gone) == 0:
            repositories_PRS_core_gone = csv_manager.read_PRS_file(SystemPath.get_path_file_PRS_core_gone(repository['owner'], repository['repository']))
        else:
            repositories_PRS_core_gone.extend(csv_manager.read_PRS_file(SystemPath.get_path_file_PRS_core_gone(repository['owner'], repository['repository'])))
    
    return repositories_PRS_core_gone

def generate_repositories_ISSUE_TF(token):
    """
    The function takes all the ISSUE_TF.csv files of the repositories present in the repositories.txt file in Resources folder
    and creates a single list that contains all the data present in the files
    Output:
        repositories_ISSUE_TF(list): the list containing all the information present in the ISSUE_TF files of all the analysis repositories
    """
    repositories_list = read_repositories_list()
    repositories_ISSUE_TF = []
    for repository in repositories_list:
        csv_manager = CSVmanager(repository['owner'], repository['repository'], token)
        if len(repositories_ISSUE_TF) == 0:
            repositories_ISSUE_TF = csv_manager.read_ISSUE_file(SystemPath.get_path_file_ISU_TF(repository['owner'], repository['repository']))
        else:
            repositories_ISSUE_TF.extend(csv_manager.read_ISSUE_file(SystemPath.get_path_file_ISU_TF(repository['owner'], repository['repository'])))
    
    return repositories_ISSUE_TF

def generate_repositories_ISSUE_TF_gone(token):
    """
    The function takes all the ISSUE_TF_gone.csv files of the repositories present in the repositories.txt file in Resources folder
    and creates a single list that contains all the data present in the files
    Output:
        repositories_ISSUE_TF_gone(list): the list containing all the information present in the ISSUE_TF_gone files of all the analysis repositories
    """
    repositories_list = read_repositories_list()
    repositories_ISSUE_TF_gone = []
    for repository in repositories_list:
        csv_manager = CSVmanager(repository['owner'], repository['repository'], token)
        if len(repositories_ISSUE_TF_gone) == 0:
            repositories_ISSUE_TF_gone = csv_manager.read_ISSUE_file(SystemPath.get_path_file_ISU_TF_gone(repository['owner'], repository['repository']))
        else:
            repositories_ISSUE_TF_gone.extend(csv_manager.read_ISSUE_file(SystemPath.get_path_file_ISU_TF_gone(repository['owner'], repository['repository'])))
    
    return repositories_ISSUE_TF_gone

def generate_repositories_ISSUE_core(token):
    """
    The function takes all the ISSUE_core.csv files of the repositories present in the repositories.txt file in Resources folder
    and creates a single list that contains all the data present in the files
    Output:
        repositories_ISSUE_core(list): the list containing all the information present in the ISSUE_core_gone files of all the analysis repositories
    """
    repositories_list = read_repositories_list()
    repositories_ISSUE_core = []
    for repository in repositories_list:
        csv_manager = CSVmanager(repository['owner'], repository['repository'], token)
        if len(repositories_ISSUE_core) == 0:
            repositories_ISSUE_core = csv_manager.read_ISSUE_file(SystemPath.get_path_file_ISU_core(repository['owner'], repository['repository']))
        else:
            repositories_ISSUE_core.extend(csv_manager.read_ISSUE_file(SystemPath.get_path_file_ISU_core(repository['owner'], repository['repository'])))
    
    return repositories_ISSUE_core

def generate_repositories_ISSUE_core_gone(token):
    """
    The function takes all the ISSUE_core_gone.csv files of the repositories present in the repositories.txt file in Resources folder
    and creates a single list that contains all the data present in the files
    Output:
        repositories_ISSUE_core_gone(list): the list containing all the information present in the ISSUE_core_gone files of all the analysis repositories
    """
    repositories_list = read_repositories_list()
    repositories_ISSUE_core_gone = []
    for repository in repositories_list:
        csv_manager = CSVmanager(repository['owner'], repository['repository'], token)
        if len(repositories_ISSUE_core_gone) == 0:
            repositories_ISSUE_core_gone = csv_manager.read_ISSUE_file(SystemPath.get_path_file_ISU_core_gone(repository['owner'], repository['repository']))
        else:
            repositories_ISSUE_core_gone.extend(csv_manager.read_ISSUE_file(SystemPath.get_path_file_ISU_core_gone(repository['owner'], repository['repository'])))
    
    return repositories_ISSUE_core_gone

def save_data_for_loc(LOC_list, file_path: str):
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

def save_data_for_prs(PRS_list, file_path: str):
        """
        the function takes care of saving the files with the PRS metric
        Args:
            PRS_list(list): the list of values to save
            file_path(str): the path to save the file
        """
        fieldnames = ['date', 'PRS', 'dev_breaks_count', 'project_age', 
                     'project_contributors' ,'project_name', 'project_language', 
                      'project_size', 'project_stars']
        with open(file_path, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(PRS_list)

def save_data_for_isu(ISU_list, file_path: str):
        """
        the function takes care of saving the files with the ISU metric
        Args:
            ISU_list(list): the list of values to save
            file_path(str): the path to save the file
        """
        fieldnames = ['date', 'ISSUE', 'dev_breaks_count', 'project_age', 
                     'project_contributors' ,'project_name', 'project_language', 
                      'project_size', 'project_stars']
        with open(file_path, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(ISU_list)

def read_LOC_file(path: str):
        """
        the function reads the file containing the LOC metric. 
        The file path is requested to specify which of the 4 files with the LOC metric we want to read 
        (TF, TF_gone, core, core_gone)
        Args:
            path(str): the path of the file containing the LOC metric we want to read
        Output:
            LOC_values(list): the list containing the data saved in the read file
        """
        LOC_values = []
        with open (path, 'r', newline = '') as csvfile:
            reader = csv.DictReader(csvfile, delimiter = ',')
            for row in reader:
                LOC_values.append({
                    'date': Utility.convert_string_to_date(row['date']),
                    'LOC': int(row['LOC']),
                    'dev_breaks_count': int(row['dev_breaks_count']),
                    'project_age': int(row['project_age']),
                    'project_contributors': int(row['project_contributors']),
                    'project_name': row['project_name'],
                    'project_language': row['project_language'],
                    'project_size': int(row['project_size']),
                    'project_stars': int(row['project_stars'])
                })
        
        return LOC_values

def read_commit_list(owner, repository):
        """
        The function takes care of reading the file in which all the commits made during the analysis period are present, 
        returns a list where each element of the list is a commit with the relative information
        Output:
            commit_list(list): The list contains all the information about the commits of the analysis period
        """
        path_file = SystemPath.get_path_to_commit_list(owner, repository)
        commit_list = []
        with open(path_file, 'r', newline = '') as csvfile:
            reader = csv.DictReader(csvfile, delimiter=';')
            for row in reader:
                sha = row['sha']
                date = Utility.convert_string_to_date(row['date'][:10])
                commit_list.append({
                    'sha': sha,
                    'author': row['author_id'],
                    'date': date
                })
        
        commit_list = sorted(commit_list, key=lambda x: x['date'])
        return commit_list

def read_PRS_file(path: str):
        """
        the function reads the file containing the PRS metric. 
        The file path is requested to specify which of the 4 files with the LOC metric we want to read 
        (TF, TF_gone, core, core_gone)
        Args:
            path(str): the path of the file containing the PRS metric we want to read
        Output:
            PRS_values(list): the list containing the data saved in the read file
        """
        PRS_value = []
        with open(path, mode='r', newline='') as file:
            reader = csv.DictReader(file, delimiter=',')
            for row in reader:
                PRS_value.append({
                    'date': Utility.convert_string_to_date(row['date']),
                    'PRS': int(row['PRS']),
                    'dev_breaks_count': int(row['dev_breaks_count']),
                    'project_age': int(row['project_age']),
                    'project_contributors': int(row['project_contributors']),
                    'project_name': row['project_name'],
                    'project_language': row['project_language'],
                    'project_size': int(row['project_size']),
                    'project_stars': int(row['project_stars'])

                })
        return PRS_value

def read_ISSUE_file(path: str):
        """
        the function reads the file containing the ISSUE metric. 
        The file path is requested to specify which of the 4 files with the LOC metric we want to read 
        (TF, TF_gone, core, core_gone)
        Args:
            path(str): the path of the file containing the LOC metric we want to read
        Output:
            ISSUE_values(list): the list containing the data saved in the read file
        """
        ISSUE_value = []
        with open(path, mode='r', newline='') as file:
            reader = csv.DictReader(file, delimiter=',')
            for row in reader:
                ISSUE_value.append({
                    'date': Utility.convert_string_to_date(row['date']),
                    'ISSUE': int(row['ISSUE']),
                    'dev_breaks_count': int(row['dev_breaks_count']),
                    'project_age': int(row['project_age']),
                    'project_contributors': int(row['project_contributors']),
                    'project_name': row['project_name'],
                    'project_language': row['project_language'],
                    'project_size': int(row['project_size']),
                    'project_stars': int(row['project_stars'])

                })
        return ISSUE_value


    
    