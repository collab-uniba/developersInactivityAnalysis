import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import CSVmanager
import Utilities as util

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)
    
    repoUrls = util.getReposList()
    for repoUrl in repoUrls:
        gitRepoName = repoUrl.replace('https://github.com/', '').strip()
        # split the repo name to get the owner and the repository name
        owner, repository = gitRepoName.split('/')
        token = util.getRandomToken()
        csv = CSVmanager.CSVmanager(owner, repository, token)
        csv.create_issues_file()
    print("Done")
    