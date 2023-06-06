# TODO This module Extracts the PRs using repo.get_pulls()
# Opening a PR is considered a coding activity
# so this script will be integrated with the CommitExtractor changing the name to "CodingExtractor"

### IMPORT EXCEPTION MODULES
from requests.exceptions import Timeout
from github import GithubException

### IMPORT SYSTEM MODULES
from github import Github
import os, sys, logging, pandas
from datetime import datetime

### IMPORT CUSTOM MODULES
sys.path.insert(1, '../')
import Settings as cfg
import Utilities as util

### DEFINE CONSTANTS
COMPLETE = "COMPLETE"

def getActivityExtractionStatus(folder, statusFile):
    status = "NOT-STARTED"
    if(statusFile in os.listdir(folder)):
        with open(os.path.join(folder, statusFile)) as f:
            content = f.readline().strip()
        status,ref_date = content.split(';')
    return status

def get_prs_repo(gith, outputFolder, repo):   # developers is a previously used param representing the list of core developers
    outputFileName = "prs_repo.csv"
    tmpSavefile = '_prs_save_file.log'
    tmpStatusFile = "_prs_extraction_status.tmp"

    status = getActivityExtractionStatus(outputFolder, tmpStatusFile)
    if (status != COMPLETE):
        exception_thrown = True
        while (exception_thrown):
            exception_thrown = False

            ### Get Issue / Pull Requests
            created_prs = repo.get_pulls(state='all', sort='created_at')

            last_page_read = 0
            if outputFileName in os.listdir(outputFolder):
                prs_data = pandas.read_csv(os.path.join(outputFolder, outputFileName), sep=cfg.CSV_separator)
                last_page_read = util.getLastPageRead(os.path.join(outputFolder, tmpSavefile))
            else:
                prs_data = pandas.DataFrame(columns=['id', 'issue_id', 'date', 'creator_login', 'status', 'closed_at', 'merged', 'merged_at', 'number'])
            try:
                num_items = created_prs.totalCount
                last_page = int(num_items / cfg.items_per_page)

                for page in range(last_page_read, last_page + 1):
                    created_issues_prs_page = created_prs.get_page(page)
                    for issue in created_issues_prs_page:
                        issue_id = issue.id
                        if (issue_id not in prs_data.id.tolist()):
                            if (issue.user):
                                util.waitRateLimit(gith)
                                util.add(prs_data, [issue_id, issue.as_issue().id, issue.created_at, issue.user.login, issue.state, issue.closed_at, issue.merged, issue.merged_at, issue.number])
                    with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                        statusSaver.write('last_page_read:{}'.format(page))
                if (len(prs_data) > 0):
                    prs_data.to_csv(os.path.join(outputFolder, outputFileName),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
                with open(os.path.join(outputFolder, tmpStatusFile), "w") as statusSaver:
                    statusSaver.write('COMPLETE;{}'.format(datetime.today().strftime("%Y-%m-%d")))
                logging.info('Pulls Extraction Complete')
            except GithubException as ghe:
                logging.warning('Exception Occurred While Getting PULLS: Github {}'.format(ghe))
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_page_read:{}'.format(page))
                prs_data.to_csv(os.path.join(outputFolder,outputFileName),
                                       sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
                exception_thrown = True
                pass
            except Timeout:
                logging.warning('Exception Occurred While Getting PULLS: Timeout')
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_page_read:{}'.format(page))
                if (len(prs_data) > 0):
                    prs_data.to_csv(os.path.join(outputFolder,outputFileName),
                                           sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
                exception_thrown = True
                pass
            except:
                print('Execution Interrupted While Getting PULLS')
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_page_read:{}'.format(page))
                if (len(prs_data) > 0):
                    prs_data.to_csv(os.path.join(outputFolder,outputFileName),
                                           sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
                raise

def get_repo_activities(gith, outputFolder, repo):  # developers is a previously used param representing the list of core developers
    logging.info('Starting Issue/PullRequests Extraction')
    get_prs_repo(gith, outputFolder, repo)  # developers is a previously used param representing the list of core developers

### MAIN FUNCTION
def main(gitRepoName, token):
    ### SET THE PROJECT
    organization, project = gitRepoName.split('/')

    os.makedirs(cfg.logs_folder, exist_ok=True)
    logfile = cfg.logs_folder+"/Activities_Extraction_"+organization+".log"
    logging.basicConfig(filename=logfile, level=logging.INFO)

    g = Github(token)
    try:
        g.get_rate_limit()
    except Exception as e:
        print('Exception {}'.format(e))
        logging.error(e)
        return
    g.per_page = cfg.items_per_page

    print("Running the Activity Extraction. \n Connection Done. \n Logging in {}".format(logfile))
    logging.info("Activity Extraction Started for {}.".format(organization))

    workingFolder = cfg.main_folder

    util.waitRateLimit(g)
    org = g.get_organization(organization)
    org_repos = org.get_repos(type='all')

    try: ### Only for Log (Block)
        num_repos = org_repos.totalCount
    except:
        num_repos = 'Unknown'

    repo_num = 0  ### Only for Log
    for repo in org_repos:
        util.waitRateLimit(g)
        project = repo.name
        repo_num += 1  ### Only for Log

        repo_name = organization+'/'+project

        logging.info('Project {} Started Activities Extraction. {} of {}'.format(repo_name, repo_num, num_repos))

        outputFolder = os.path.join(workingFolder, repo_name, 'Other_Activities')
        os.makedirs(outputFolder, exist_ok=True)

        get_repo_activities(g, outputFolder, repo)  # developers is a previously used param representing the list of core developers
        logging.info('Commit Extraction COMPLETE for {} of {} Side Projects'.format(repo_num, num_repos))
    logging.info('Commit Extraction SUCCESSFULLY COMPLETED')

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    ### ARGUMENTS MANAGEMENT
    # python script.py repoName(format: organization/project) tokenNumber
    print('Arguments: {} --> {}'.format(len(sys.argv), str(sys.argv)))
    gitRepoName = sys.argv[1]
    try:
        token = util.getToken(int(sys.argv[2]))
    except:
        token = sys.argv[2]
        pass
    main(gitRepoName, token)