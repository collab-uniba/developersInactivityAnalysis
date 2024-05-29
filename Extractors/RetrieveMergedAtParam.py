# FIXME This file needs to be removed after the first commit in the new branch because it is integrated in PullRequestsExtractor

### IMPORT EXCEPTION MODULES
import logging
import os
import sys
sys.path.append('../')
from datetime import datetime

import pandas
### IMPORT SYSTEM MODULES
from github import Github, GithubException
from requests.exceptions import Timeout

### IMPORT CUSTOM MODULES
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

                    for _, pr in prs_data.iterrows():
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
                                                        quoting=None, lineterminator='\n')
                                exception_thrown = True
                                pass
                            except Timeout:
                                logging.warning('Exception Occurred While Getting PULLS: Timeout')
                                if (len(new_prs_data) > 0):
                                    new_prs_data.to_csv(tmp_PR_file,
                                                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False,
                                                        quoting=None, lineterminator='\n')
                                exception_thrown = True
                                pass
                            except:
                                print('Execution Interrupted While Getting PULLS')
                                if (len(new_prs_data) > 0):
                                    new_prs_data.to_csv(tmp_PR_file,
                                                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False,
                                                        quoting=None, lineterminator='\n')
                                raise
                    new_prs_data.to_csv(PR_file, sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
        folder_count += 1
        logging.info('Missing Param Extraction COMPLETE for {} of {} Folders'.format(folder_count, len(os.listdir(workingFolder))))

### MAIN FUNCTION
def main(gitRepoName, token):
    organization, _ = gitRepoName.split('/')

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
    
    os.makedirs(cfg.logs_folder, exist_ok=True)
    timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d_%H:%M')
    logfile = cfg.logs_folder+f"/Retrive_Merged_Param_Extraction_{timestamp}.log"
    logging.basicConfig(filename=logfile, level=logging.INFO)

    repoUrls = util.getReposList()
    for repoUrl in repoUrls:
        gitRepoName = repoUrl.replace('https://github.com/', '').strip()
        token = util.getRandomToken()
        logging.info("Starting Retrive merged at param extraction for {}".format(gitRepoName))
        main(gitRepoName, token)
    print("Done")