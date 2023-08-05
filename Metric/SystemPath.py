import os

FILE_COMMIT_LIST = 'Organizations/{}/{}/commit_list.csv'
FOLDER_NAME = 'developersInactivityAnalysis'

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