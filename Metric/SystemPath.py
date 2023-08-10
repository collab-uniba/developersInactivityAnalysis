import os

FILE_COMMIT_LIST = 'Organizations/{}/{}/commit_list.csv'
FOLDER_NAME = 'developersInactivityAnalysis'
FILE_TF_DEVS = 'Organizations/{}/{}/TF_devs.csv'
METRIC_FOLDER = 'Organizations/{}/{}/Metric'
LOC_TF = "LOC_TF.csv"
LOC_TF_GONE = "LOC_TF_gone.csv"
LOC_CORE = "LOC_core.csv"
LOC_CORE_GONE = "LOC_core_gone.csv"
FILE_PAUSES = 'Organizations/{}/{}/pauses_dates_list.csv'
FILE_G_FULL_LIST = 'Organizations/A80API/G_full_list.csv'
FILE_CORE_DEVS = 'A80_Results/{}/A80_devs.csv'

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
    path = path_folder + METRIC_FOLDER.format(owner, reposiotry)
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