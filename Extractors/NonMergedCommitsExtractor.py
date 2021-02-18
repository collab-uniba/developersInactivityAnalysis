# TODO This module Extracts the Commits from non-merged PRs using repo.get_pull(PRnum).get_commits()
# Even though not merged these commits represent coding activity
# so this script will be integrated with the CommitExtractor changing the name to "CodingExtractor"


### IMPORT EXCEPTION MODULES
from requests.exceptions import Timeout
from github import GithubException
from github.GithubException import IncompletableObject

### IMPORT SYSTEM MODULES
from github import Github
import os, sys, logging, pandas
from datetime import datetime

### IMPORT CUSTOM MODULES
import Settings as cfg
import Utilities as util

### DEFINE CONSTANTS
COMPLETE = "COMPLETE"

def getExtractionStatus(folder, statusFile):
    status = "NOT-STARTED"
    if(statusFile in os.listdir(folder)):
        with open(os.path.join(folder, statusFile)) as f:
            content = f.readline().strip()
        status,ref_date = content.split(';')
    return status

def extract_commits(gith, organization, repo_name, pr_number):
    outputFolder = os.path.join(cfg.main_folder, organization, repo_name, 'MissingCommits')
    os.makedirs(outputFolder, exist_ok=True)
    outputFileName = "{}_commits.csv".format(pr_number)
    tmpExcludedCommits = "_excludedNoneType.tmp"
    tmpSavefile = '_{}_commits_save_file.log'.format(pr_number)
    tmpStatusFile = "_{}_commits_extraction_status.tmp".format(pr_number)

    logging.info("Missing Commits Extraction for {} PR {}.".format(repo_name, pr_number))
    status = getExtractionStatus(outputFolder, tmpStatusFile)
    if (status != COMPLETE):
        with open(os.path.join(outputFolder, tmpStatusFile), "w") as statusSaver:
            statusSaver.write('INCOMPLETE;{}'.format(datetime.today().strftime('%Y-%m-%d %H:%M:%S')))

        exception_thrown = True
        while (exception_thrown):
            exception_thrown = False

            ### Get Commits
            util.waitRateLimit(gith)
            repo = gith.get_repo(organization + '/' + repo_name)
            commits = repo.get_pull(pr_number).get_commits()

            count_exception = True
            while (count_exception):
                count_exception = False
                try:
                    num_items = commits.totalCount
                except GithubException as ghe:
                    if str(ghe).startswith('500'):  # former == '500 None':
                        logging.warning(
                            'Failed to get commits from this PR (500 None: Ignoring PR): {}'.format(pr_number))
                        return
                    elif str(ghe).startswith('409'):
                        logging.warning(
                            'Failed to get commits from this PR (409 Empty: Ignoring PR):'.format(pr_number))
                        return
                    else:
                        logging.warning(
                            'Failed to get commits from this PR (GITHUB Unknown: Retrying):'.format(pr_number))
                        count_exception = True
                    pass
                except Timeout:
                    logging.warning('Failed to get commits from this PR (TIMEOUT: Retrying):'.format(pr_number))
                    count_exception = True
                    pass
                except:
                    logging.warning('Failed to get commits from this PR (Probably Empty): '.format(pr_number))
                    return
            last_page = int(num_items / cfg.items_per_page)
            last_page_read = 0

            if outputFileName in os.listdir(outputFolder):
                commits_data = pandas.read_csv(os.path.join(outputFolder, outputFileName), sep=cfg.CSV_separator)
                if (tmpSavefile in os.listdir(outputFolder)):
                    last_page_read = util.getLastPageRead(os.path.join(outputFolder, tmpSavefile))
                logging.info("Resuming Extraction")
            else:
                commits_data = pandas.DataFrame(columns=['sha', 'author_id', 'date'])
                logging.info("Starting New Extraction")

            if tmpExcludedCommits in os.listdir(outputFolder):
                excluded_commits = pandas.read_csv(os.path.join(outputFolder, tmpExcludedCommits), sep=cfg.CSV_separator)
            else:
                excluded_commits = pandas.DataFrame(columns=['sha', 'PR_number'])

            try:
                for page in range(last_page_read, last_page + 1):
                    pr_commits_page = commits.get_page(page)
                    for commit in pr_commits_page:
                        sha = commit.sha
                        if (sha not in commits_data.sha.tolist()) and (sha not in excluded_commits.sha.tolist()):
                            if (commit.author):
                                util.waitRateLimit(gith)
                                author_id = commit.author.login
                                date = commit.commit.author.date
                                util.add(commits_data, [sha, author_id, date])
                if (len(commits_data) > 0):
                    commits_data.to_csv(os.path.join(outputFolder, outputFileName),
                                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
            except IncompletableObject:
                logging.warning('Github Exception 400: Returned object contains no URL. SHA: {}'.format(sha))
                util.add(excluded_commits, [sha, pr_number])
                if (len(commits_data) > 0):
                    commits_data.to_csv(os.path.join(outputFolder, outputFileName),
                                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None,
                                        line_terminator='\n')
                excluded_commits.to_csv(os.path.join(outputFolder, tmpExcludedCommits),
                                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None,
                                        line_terminator='\n')
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_page:{}'.format(page))
                exception_thrown = True
                pass
            except GithubException as ghe:
                logging.warning('Exception Occurred While Getting Missing Commits: Github {}'.format(ghe))
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_page_read:{}'.format(page))
                commits_data.to_csv(os.path.join(outputFolder,outputFileName),
                                       sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
                exception_thrown = True
                pass
            except Timeout:
                logging.warning('Exception Occurred While Getting Missing Commits: Timeout')
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_page_read:{}'.format(page))
                if (len(commits_data) > 0):
                    commits_data.to_csv(os.path.join(outputFolder,outputFileName),
                                           sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
                exception_thrown = True
                pass
            except AttributeError:
                logging.warning('Exception Occurred While Getting Missing Commits Data: NoneType for Author. SHA: {}'.format(sha))
                util.add(excluded_commits, [sha, pr_number])
                if (len(commits_data) > 0):
                    commits_data.to_csv(os.path.join(outputFolder, outputFileName),
                                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None,
                                        line_terminator='\n')
                excluded_commits.to_csv(os.path.join(outputFolder, tmpExcludedCommits),
                                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None,
                                        line_terminator='\n')
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_page:{}'.format(page))
                exception_thrown = True
                pass

            except:
                print('Execution Interrupted While Getting Missing Commits')
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_page_read:{}'.format(page))
                if (len(commits_data) > 0):
                    commits_data.to_csv(os.path.join(outputFolder,outputFileName),
                                           sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
                raise
    logging.info("Commit Extraction Complete")
    with open(os.path.join(outputFolder, tmpStatusFile), "w") as statusSaver:
                statusSaver.write('COMPLETE;{}'.format(cfg.data_collection_date))


def get_missing_commits(gith, organization):  # developers is a previously used param representing the list of core developers
    logging.info('Starting Issue/PullRequests Extraction')
    workingFolder = os.path.join(cfg.main_folder, organization)
    tmp_folder_status_file = "_folder_status.tmp"

    folder_count = 0
    for folder in os.listdir(workingFolder):
        current_folder = os.path.join(workingFolder, folder)
        if os.path.isdir(current_folder):
            PR_file = os.path.join(current_folder, 'Other_Activities', 'prs_repo.csv')
            if os.path.lexists(PR_file):
                repo = folder
                if (not os.path.lexists(os.path.join(current_folder, 'Other_Activities', tmp_folder_status_file))) or (getExtractionStatus(os.path.join(current_folder, 'Other_Activities'), tmp_folder_status_file)!=COMPLETE): # TODO: Remove line, not fundamental
                    prs_data = pandas.read_csv(PR_file, sep=cfg.CSV_separator)
                    for index, pr in prs_data.iterrows():
                        if pr['status'] == 'open' and pr['date'] < cfg.data_collection_date:
                            pr_number = pr['number']
                            logging.info("Getting COMMITS for PR n. {} OPEN".format(pr_number))
                            extract_commits(gith, organization, repo, pr_number)
                            logging.info('Missing Commit Extraction COMPLETE for PR n. {}'.format(pr_number))
                        if pr['status'] == 'closed' and pr['merged'] == False and pr['date'] < cfg.data_collection_date:
                            pr_number = pr['number']
                            logging.info("Getting COMMITS for PR n. {} CLOSED NOT MERGED".format(pr_number))
                            extract_commits(gith, organization, repo, pr_number)
                            logging.info('Missing Commit Extraction COMPLETE for PR n. {}'.format(pr_number))
                        if pr['status'] == 'closed' and pr['merged'] == True and pr['date'] < cfg.data_collection_date and pr['closed_at'] >= cfg.data_collection_date:
                            pr_number = pr['number']
                            logging.info("Getting COMMITS for PR n. {} CLOSED AFTER EXTRACTION".format(pr_number))
                            extract_commits(gith, organization, repo, pr_number)
                            logging.info('Missing Commit Extraction COMPLETE for PR n. {}'.format(pr_number))
                        if pr['status'] == 'closed' and pr['merged'] == True and pr['date'] < cfg.data_collection_date and pr['closed_at'] < cfg.data_collection_date and pr['merged_at'] >= cfg.data_collection_date:
                            pr_number = pr['number']
                            logging.info("Getting COMMITS for PR n. {} MERGED AFTER EXTRACTION".format(pr_number))
                            extract_commits(gith, organization, repo, pr_number)
                            logging.info('Missing Commit Extraction COMPLETE for PR n. {}'.format(pr_number))
                    with open(os.path.join(current_folder, 'Other_Activities', tmp_folder_status_file), "w") as statusSaver:
                        statusSaver.write('COMPLETE;{}'.format(cfg.data_collection_date))
        folder_count += 1
        logging.info('Missing Commit Extraction COMPLETE for {} - {} of {} Folders'.format(current_folder, folder_count, len(os.listdir(workingFolder))))

### MAIN FUNCTION
def main(gitRepoName, token):
    organization, project = gitRepoName.split('/')

    os.makedirs(cfg.logs_folder, exist_ok=True)
    logfile = cfg.logs_folder + "/Missing_Commits_Extraction_" + organization + ".log"
    logging.basicConfig(filename=logfile, level=logging.INFO)

    g = Github(token)
    try:
        g.get_rate_limit()
    except Exception as e:
        print('Exception {}'.format(e))
        logging.error(e)
        return
    g.per_page = cfg.items_per_page

    print("Running the Missing Commits Extraction. \n Connection Done. \n Logging in {}".format(logfile))
    logging.info("Missing Commits Extraction Started for {}.".format(organization))

    get_missing_commits(g, organization)

    logging.info('Missing Commit Extraction SUCCESSFULLY COMPLETED')

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