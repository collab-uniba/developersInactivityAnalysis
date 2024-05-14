import os

FILE_COMMIT_LIST = 'Organizations/{}/{}/commit_list.csv'
FILE_PRS_LIST = 'Organizations/{}/{}/prs_list.csv'
FILE_ISSUE_LIST = 'Organizations/{}/{}/issue_list.csv'
FOLDER_NAME = 'developersInactivityAnalysis'
FILE_TF_DEVS = 'Organizations/{}/{}/TF_devs.csv'
METRIC_FOLDER = 'Organizations/{}/{}/Metric'
LOC_TF = "LOC_TF.csv"
LOC_TF_GONE = "LOC_TF_gone.csv"
LOC_CORE = "LOC_core.csv"
LOC_CORE_GONE = "LOC_core_gone.csv"
PRS_TF = "PRS_TF.csv"
PRS_TF_GONE = "PRS_TF_gone.csv"
PRS_CORE = "PRS_core.csv"
PRS_CORE_GONE = "PRS_core_gone.csv"
ISU_TF = "ISSUE_TF.csv"
ISU_TF_GONE = "ISSUE_TF_gone.csv"
ISU_CORE = "ISSUE_core.csv"
ISU_CORE_GONE = "ISSUE_core_gone.csv"
FILE_PAUSES = 'Organizations/{}/{}/pauses_dates_list.csv'
FILE_G_FULL_LIST = 'Organizations/A80API/G_full_list.csv'
FILE_CORE_DEVS = 'A80_Results/{}/A80_devs.csv'
BASIS_FILE_LOC = 'basis_LOC.csv'

FILE_REPOSITORIES_LOC_TF ='repositories_LOC_TF.csv'
FILE_REPOSITORIES_LOC_TF_GONE = 'repositories_LOC_TF_gone.csv'
FILE_REPOSITORIES_LOC_CORE = 'repositories_LOC_core.csv'
FILE_REPOSITORIES_LOC_CORE_GONE = 'repositories_LOC_core_gone.csv'

FILE_REPOSITORIES_PRS_TF = 'repositories_PRS_TF.csv'
FILE_REPOSITORIES_PRS_TF_GONE = 'repositories_PRS_TF_gone.csv'
FILE_REPOSITORIES_PRS_CORE = 'repositories_PRS_core.csv'
FILE_REPOSITORIES_PRS_CORE_GONE = 'repositories_PRS_core_gone.csv'

FILE_REPOSITORIES_ISSUE_TF = 'repositories_ISSUE_TF.csv'
FILE_REPOSITORIES_ISSUE_TF_GONE = 'repositories_ISSUE_TF_gone.csv'
FILE_REPOSITORIES_ISSUE_CORE = 'repositories_ISSUE_core.csv'
FILE_REPOSITORIES_ISSUE_CORE_GONE = 'repositories_ISSUE_core_gone.csv'

REPOSITORIES_METRIC_FOLDER = 'Metric'
REPOSITORIES_LIST = 'Resources/repositories.txt'

def get_path_to_folder():
    """
    Returns the path to the project folder
    Output:
        path(str): the path to the project folder
    """
    path_to_folder = os.getcwd()
    list_folder = path_to_folder.split('/')
    path = '/'
    for elem in list_folder:
        if elem != FOLDER_NAME:
            if path == '/':
                path = path + elem
            else:
                path = path + '/'+ elem
        else:
            path = path + '/' + elem
            break
    return path

def get_path_repositories_list():
    """
    The function returns the path of the repositories.txt file which contains the list of repositories
    """
    main_folder = get_path_to_folder()
    path = main_folder + '/' + REPOSITORIES_LIST
    return path

def get_repositories_metric_folder():
    """
    The function returns the path of the folder where the metrics files of all the repositories are present
    """
    path_to_main_folder = get_path_to_folder()
    path_folder = path_to_main_folder + '/' + REPOSITORIES_METRIC_FOLDER
    return path_folder

def get_path_repositories_LOC_TF():
    """
    The function returns the path of the file containing the LOC_TF metric data of all repositories
    """
    path_metric_folder = get_repositories_metric_folder()
    file_path = path_metric_folder + '/' + FILE_REPOSITORIES_LOC_TF
    return file_path

def get_path_repositories_LOC_TF_gone():
    """
    The function returns the path of the file containing the LOC_TF_gone metric data of all repositories
    """
    path_metric_folder = get_repositories_metric_folder()
    file_path = path_metric_folder + '/' +FILE_REPOSITORIES_LOC_TF_GONE
    return file_path

def get_path_repositories_LOC_core():
    """
    The function returns the path of the file containing the LOC_core metric data of all repositories
    """
    path_metric_folder = get_repositories_metric_folder()
    file_path = path_metric_folder + '/' +FILE_REPOSITORIES_LOC_CORE
    return file_path

def get_path_repositories_LOC_core_gone():
    """
    The function returns the path of the file containing the LOC_core_gone metric data of all repositories
    """
    path_metric_folder = get_repositories_metric_folder()
    file_path = path_metric_folder + '/' +FILE_REPOSITORIES_LOC_CORE_GONE
    return file_path

def get_path_repositories_PRS_TF():
    """
    The function returns the path of the file containing the PRS_TF metric data of all repositories
    """
    path_metric_folder = get_repositories_metric_folder()
    file_path = path_metric_folder + '/' +FILE_REPOSITORIES_PRS_TF
    return file_path

def get_path_repositories_PRS_TF_gone():
    """
    The function returns the path of the file containing the PRS_TF_gone metric data of all repositories
    """
    path_metric_folder = get_repositories_metric_folder()
    file_path = path_metric_folder + '/' +FILE_REPOSITORIES_PRS_TF_GONE
    return file_path

def get_path_repositories_PRS_core():
    """
    The function returns the path of the file containing the PRS_core metric data of all repositories
    """
    path_metric_folder = get_repositories_metric_folder()
    file_path = path_metric_folder + '/' +FILE_REPOSITORIES_PRS_CORE
    return file_path

def get_path_repositories_PRS_core_gone():
    """
    The function returns the path of the file containing the PRS_core_gone metric data of all repositories
    """
    path_metric_folder = get_repositories_metric_folder()
    file_path = path_metric_folder + '/' + FILE_REPOSITORIES_PRS_CORE_GONE
    return file_path

def get_path_repositories_ISSUE_TF():
    """
    The function returns the path of the file containing the ISSUE_TF metric data of all repositories
    """
    path_metric_folder = get_repositories_metric_folder()
    file_path = path_metric_folder + '/' + FILE_REPOSITORIES_ISSUE_TF
    return file_path

def get_path_repositories_ISSUE_TF_gone():
    """
    The function returns the path of the file containing the ISSUE_TF_gone metric data of all repositories
    """
    path_metric_folder = get_repositories_metric_folder()
    file_path = path_metric_folder + '/' + FILE_REPOSITORIES_ISSUE_TF_GONE
    return file_path

def get_path_repositories_ISSUE_core():
    """
    The function returns the path of the file containing the ISSUE_core metric data of all repositories
    """
    path_metric_folder = get_repositories_metric_folder()
    file_path = path_metric_folder + '/' + FILE_REPOSITORIES_ISSUE_CORE
    return file_path

def get_path_repositories_ISSUE_core_gone():
    """
    The function returns the path of the file containing the ISSUE_core_gone metric data of all repositories
    """
    path_metric_folder = get_repositories_metric_folder()
    file_path = path_metric_folder + '/' + FILE_REPOSITORIES_ISSUE_CORE_GONE
    return file_path

def get_path_to_commit_list(owner: str, repository: str):
    """
    Returns the path to the owner/repository commit_list file
    Args:
        owner(str): the name of the owner of the repository whose commit_list file we want to have
        repository(str): the name of the repository whose commit_list file we want to have
    Output:
        path(str): the path to the owner/repository commit_list file
    """
    path_folder = get_path_to_folder()
    path = path_folder + '/' + FILE_COMMIT_LIST.format(owner, repository)
    return path

def get_path_prs_list(owner: str, repository: str):
    """
    Returns the path to the owner/repository prs_list file
    Args:
        owner(str): the name of the owner of the repository whose prs_list file we want to have
        repository(str): the name of the repository whose prs_list file we want to have
    Output:
        path(str): the path to the owner/repository prs_list file
    """
    path_folder = get_path_to_folder()
    path = path_folder + '/' + FILE_PRS_LIST.format(owner, repository)
    return path

def get_path_issue_list(owner: str, repository: str):
    """
    Returns the path to the owner/repository issue_list file
    Args:
        owner(str): the name of the owner of the repository whose issue_list file we want to have
        repository(str): the name of the repository whose issue_list file we want to have
    Output:
        path(str): the path to the owner/repository issue_list file
    """
    path_folder = get_path_to_folder()
    path = path_folder + '/' + FILE_ISSUE_LIST.format(owner, repository)
    return path

def get_path_to_TF_devs(owner: str, repository: str):
    """
    Returns the path file where the TF developers list is saved
    Args:
        owner(str): the name of the repository's owner
        repository(str): the name of the repository
    Output:
        path(str): the path to the file concerned
    """
    path_folder = get_path_to_folder()
    path = path_folder + '/' + FILE_TF_DEVS.format(owner, repository)
    return path

def get_metric_folder(owner: str, reposiotry: str):
    """
    Returns the path to the Metric folder of a repository
    Args:
        owner(str): the name of the repository's owner
        repository(str): the name of the repository
    Output:
        path(str): the path to the folder concerned
    """
    path_folder = get_path_to_folder()
    path = path_folder + '/' + METRIC_FOLDER.format(owner, reposiotry)
    return path

def get_path_file_LOC_TF(owner: str, repository:str):
    """
    Returns the path to the LOC metric file, which treats the deb_break_count as the number of TF developers gone or inactive
    Args:
        owner(str): the name of the repository's owner
        repository(str): the name of the repository
    Output:
        path(str): the path to the file concerned
    """
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + LOC_TF
    return path

def get_path_basis_LOC(owner, repository):
    """
    the function returns the path of the basis_LOC file
    """
    path_folder = get_metric_folder(owner, repository)
    path = path_folder + '/' + BASIS_FILE_LOC
    return path

def get_path_file_LOC_TF_gone(owner: str, repository:str):
    """
    Returns the path to the LOC metric file, which treats the deb_break_count as the number of TF developers gone
    Args:
        owner(str): the name of the repository's owner
        repository(str): the name of the repository
    Output:
        path(str): the path to the file concerned
    """
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + LOC_TF_GONE
    return path

def get_path_file_LOC_core(owner: str, repository:str):
    """
    Returns the path to the LOC metric file, which treats the deb_break_count as the number of core developers gone or inactive
    Args:
        owner(str): the name of the repository's owner
        repository(str): the name of the repository
    Output:
        path(str): the path to the file concerned
    """
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + LOC_CORE
    return path

def get_path_file_LOC_core_gone(owner: str, repository:str):
    """
    Returns the path to the LOC metric file, which treats the deb_break_count as the number of core developers gone
    Args:
        owner(str): the name of the repository's owner
        repository(str): the name of the repository
    Output:
        path(str): the path to the file concerned
    """
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + LOC_CORE_GONE
    return path

def get_path_file_PRS_TF(owner: str, repository: str):
    """
    Returns the path to the PRS metric file, which treats the deb_break_count as the number of TF developers gone or inactive
    Args:
        owner(str): the name of the repository's owner
        repository(str): the name of the repository
    Output:
        path(str): the path to the file concerned
    """
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + PRS_TF
    return path

def get_path_file_PRS_TF_gone(owner: str, repository: str):
    """
    Returns the path to the PRS metric file, which treats the deb_break_count as the number of TF developers gone
    Args:
        owner(str): the name of the repository's owner
        repository(str): the name of the repository
    Output:
        path(str): the path to the file concerned
    """
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + PRS_TF_GONE
    return path

def get_path_file_PRS_core(owner: str, repository: str):
    """
    Returns the path to the PRS metric file, which treats the deb_break_count as the number of core developers gone or inactive
    Args:
        owner(str): the name of the repository's owner
        repository(str): the name of the repository
    Output:
        path(str): the path to the file concerned
    """
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + PRS_CORE
    return path

def get_path_file_PRS_core_gone(owner: str, repository: str):
    """
    Returns the path to the LOC metric file, which treats the deb_break_count as the number of core developers gone
    Args:
        owner(str): the name of the repository's owner
        repository(str): the name of the repository
    Output:
        path(str): the path to the file concerned
    """
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + PRS_CORE_GONE
    return path

def get_path_file_ISU_TF(owner: str, repository: str):
    """
    Returns the path to the ISU metric file, which treats the deb_break_count as the number of TF developers gone or inactive
    Args:
        owner(str): the name of the repository's owner
        repository(str): the name of the repository
    Output:
        path(str): the path to the file concerned
    """
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + ISU_TF
    return path

def get_path_file_ISU_TF_gone(owner: str, repository: str):
    """
    Returns the path to the ISU metric file, which treats the deb_break_count as the number of TF developers gone
    Args:
        owner(str): the name of the repository's owner
        repository(str): the name of the repository
    Output:
        path(str): the path to the file concerned
    """
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + ISU_TF_GONE
    return path

def get_path_file_ISU_core(owner: str, repository: str):
    """
    Returns the path to the ISU metric file, which treats the deb_break_count as the number of core developers gone or inactive
    Args:
        owner(str): the name of the repository's owner
        repository(str): the name of the repository
    Output:
        path(str): the path to the file concerned
    """
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + ISU_CORE
    return path

def get_path_file_ISU_core_gone(owner: str, repository: str):
    """
    Returns the path to the ISU metric file, which treats the deb_break_count as the number of core developers gone
    Args:
        owner(str): the name of the repository's owner
        repository(str): the name of the repository
    Output:
        path(str): the path to the file concerned
    """
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + ISU_CORE_GONE
    return path


def get_path_pauses_list(owner: str, repositpry: str):
    """
    Returns the path of the repository's developer pause list file
    Args:
        owner(str): the name of the repository's owner
        repository(str): the name of the repository
    Output:
        path(str): the path to the file concerned
    """
    path_folder = get_path_to_folder()
    path = path_folder + '/' + FILE_PAUSES.format(owner, repositpry)
    return path

def get_path_G_full_list():
    """
    Returns the path to the G_full_list file
    Output:
        path(str): the path to the file concerned
    """
    path_folder = get_path_to_folder()
    path = path_folder + '/' + FILE_G_FULL_LIST
    return path

def get_path_core_devs(repository):
    """
    Returns the path file where the core developers list is saved
    Args:
        repository(str): the name of the repository
    Output:
        path(str): the path to the file concerned
    """
    path_folder = get_path_to_folder()
    path = path_folder + '/' + FILE_CORE_DEVS.format(repository)
    return path