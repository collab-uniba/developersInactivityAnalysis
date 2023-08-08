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
    path_folder = get_path_to_folder()
    path = path_folder + '/' + FILE_TF_DEVS.format(owner, repository)
    return path

def get_metric_folder(owner: str, reposiotry: str):
    path_folder = get_path_to_folder()
    path = path_folder + METRIC_FOLDER.format(owner, reposiotry)
    return path

def get_path_file_LOC_TF(owner: str, repository:str):
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + LOC_TF
    return path

def get_path_file_LOC_TF_gone(owner: str, repository:str):
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + LOC_TF_GONE
    return path

def get_path_file_LOC_core(owner: str, repository:str):
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + LOC_CORE
    return path

def get_path_file_LOC_core_gone(owner: str, repository:str):
    path_folder_metric = get_metric_folder(owner, repository)
    path = path_folder_metric + '/' + LOC_CORE_GONE
    return path

def get_path_pauses_list(owner: str, repositpry: str):
    path_folder = get_path_to_folder()
    path = path_folder + '/' + FILE_PAUSES.format(owner, repositpry)
    return path

def get_path_G_full_list():
    path_folder = get_path_to_folder()
    path = path_folder + '/' + FILE_G_FULL_LIST
    return path

def get_path_core_devs(repository):
    path_folder = get_path_to_folder()
    path = path_folder + '/' + FILE_CORE_DEVS.format(repository)