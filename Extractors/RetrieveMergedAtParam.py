# FIXME This file needs to be removed after the first commit in the new branch because it is integrated in PullRequestsExtractor

### IMPORT EXCEPTION MODULES
from requests.exceptions import Timeout
from github import GithubException
from github.GithubException import IncompletableObject

### IMPORT SYSTEM MODULES
from github import Github
import os, sys, logging, pandas
from datetime import datetime

### IMPORT CUSTOM MODULES
sys.path.insert(1, '../')
import Settings as cfg
import Utilities as util

def get_missing_param(gith, organization):  # developers is a previously used param representing the list of core developers
    logging.info('Starting Param Extraction')
    workingFolder = os.path.join(cfg.main_folder, organization)

    folder_count = 0
    for folder in os.listdir(workingFolder):
        current_folder = os.path.join(workingFolder, folder)
        if os.path.isdir(current_folder):
            PR_file = os.path.join(current_folder, 'Other_Activities', 'prs_repo.csv')
            tmp_PR_file = os.path.join(current_folder, 'Other_Activities', '_tmp_prs_repo.csv')
            if os.path.lexists(PR_file):
                exception_thrown = True
                while (exception_thrown):
                    exception_thrown = False
                    repo = folder
                    prs_data = pandas.read_csv(PR_file, sep=cfg.CSV_separator)

                    if tmp_PR_file in os.listdir(os.path.join(current_folder, 'Other_Activities')):
                        new_prs_data = pandas.read_csv(tmp_PR_file, sep=cfg.CSV_separator)
                    else:
                        new_prs_data = pandas.DataFrame(
                            columns=['id', 'issue_id', 'date', 'creator_login',
                                     'status', 'closed_at', 'merged', 'merged_at', 'number'])

                    for index, pr in prs_data.iterrows():
                        pr_number = pr['number']
                        logging.info("Getting Param for PR n. {}".format(pr_number))
                        if 'merged_at' in pr.keys():
                            new_prs_data = prs_data
                            break
                        elif pr['number'] not in new_prs_data['number'].tolist():
                            try:
                                util.waitRateLimit(gith)
                                gh_pr = gith.get_repo(organization + '/' + repo).get_pull(pr_number)
                                util.add(new_prs_data, [pr['id'], pr['issue_id'], pr['date'], pr['creator_login'], pr['status'], pr['closed_at'], pr['merged'], gh_pr.merged_at, pr['number']])
                            except GithubException as ghe:
                                logging.warning('Exception Occurred While Getting PULLS: Github {}'.format(ghe))
                                if (len(new_prs_data) > 0):
                                    new_prs_data.to_csv(tmp_PR_file,
                                                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False,
                                                        quoting=None, line_terminator='\n')
                                exception_thrown = True
                                pass
                            except Timeout:
                                logging.warning('Exception Occurred While Getting PULLS: Timeout')
                                if (len(new_prs_data) > 0):
                                    new_prs_data.to_csv(tmp_PR_file,
                                                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False,
                                                        quoting=None, line_terminator='\n')
                                exception_thrown = True
                                pass
                            except:
                                print('Execution Interrupted While Getting PULLS')
                                if (len(new_prs_data) > 0):
                                    new_prs_data.to_csv(tmp_PR_file,
                                                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False,
                                                        quoting=None, line_terminator='\n')
                                raise
                    new_prs_data.to_csv(PR_file, sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
        folder_count += 1
        logging.info('Missing Param Extraction COMPLETE for {} of {} Folders'.format(folder_count, len(os.listdir(workingFolder))))

### MAIN FUNCTION
def main(gitRepoName, token):
    organization, project = gitRepoName.split('/')

    os.makedirs(cfg.logs_folder, exist_ok=True)
    logfile = cfg.logs_folder + "/Retrieve_Merged_at_" + organization + ".log"
    logging.basicConfig(filename=logfile, level=logging.INFO)

    g = Github(token)
    try:
        g.get_rate_limit()
    except Exception as e:
        print('Exception {}'.format(e))
        logging.error(e)
        return
    g.per_page = cfg.items_per_page

    print("Running the Param Extraction. \n Connection Done. \n Logging in {}".format(logfile))
    logging.info("Param Extraction Started for {}.".format(organization))

    get_missing_param(g, organization)

    logging.info('Missing Param Extraction SUCCESSFULLY COMPLETED')

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