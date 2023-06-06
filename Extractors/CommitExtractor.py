### IMPORT EXCEPTION MODULES
from requests.exceptions import Timeout
from github import GithubException
from github.GithubException import IncompletableObject

### IMPORT SYSTEM MODULES
from github import Github
import os, sys, logging, pandas, csv
from datetime import datetime

### IMPORT CUSTOM MODULES
sys.path.insert(1, '../')
import Settings as cfg
import Utilities as util

### DEFINE CONSTANTS
COMPLETE = "COMPLETE"

#import github

def getCommitExtractionStatus(folder, statusFile):
    status = "NOT-STARTED"
    if(statusFile in os.listdir(folder)):
        with open(os.path.join(folder, statusFile)) as f:
            content = f.readline().strip()
        status,ref_date = content.split(';')
    return status

def runCommitExtractionRoutine(g, organizationFolder, organization, project):
    workingFolder = (os.path.join(organizationFolder, project))
    os.makedirs(workingFolder, exist_ok=True)

    logging.info('Commit Extraction for {}'.format(project))

    util.waitRateLimit(g)
    repoName = organization + '/' + project
    repo = g.get_repo(repoName)

    project_start_dt = repo.created_at # To make it a string: stringData=datetimeData.strftime('%Y-%m-%d %H:%M:%S')

    collection_day = datetime.strptime(cfg.data_collection_date, '%Y-%m-%d')

    fileStatus = getCommitExtractionStatus(workingFolder, "_extractionStatus.tmp")
    if (fileStatus != COMPLETE):
        util.waitRateLimit(g)
        updateCommitListFile(g, repoName, project_start_dt, collection_day, workingFolder)
    try:
        commits_data = pandas.read_csv(os.path.join(workingFolder, cfg.commit_list_file_name), sep=cfg.CSV_separator)

        if (cfg.commit_history_table_file_name in os.listdir(workingFolder)):
            commit_table = pandas.read_csv(os.path.join(workingFolder, cfg.commit_history_table_file_name), sep=cfg.CSV_separator)
        else:
            logging.info("Start Writing Commit History Table for {}".format(project))
            commit_table = writeCommitHistoryTable(workingFolder, commits_data)

        logging.info('Starting Inactivity Computation for {}'.format(project))
        writePauses(workingFolder, commit_table)
    except:
        logging.info("No Commits for {}".format(project))

def updateCommitListFile(g, repoName, start_date, end_date, workingFolder):
    """Writes the list of the commits fro the given repository"""

    outputFileName = cfg.commit_list_file_name
    tmpSavefile = "_saveFile.tmp"
    tmpExcludedCommits = "_excludedNoneType.tmp"
    tmpStatusFile = "_extractionStatus.tmp"
    logging.info("Initializing Extraction")

    status = getCommitExtractionStatus(workingFolder, tmpStatusFile)
    if(status != COMPLETE):
        with open(os.path.join(workingFolder, tmpStatusFile), "w") as statusSaver:
            statusSaver.write('INCOMPLETE;{}'.format(datetime.today().strftime('%Y-%m-%d %H:%M:%S')))

        exception_thrown = True
        while (exception_thrown):
            exception_thrown = False

            util.waitRateLimit(g)
            repo = g.get_repo(repoName)

            commits = repo.get_commits(since=start_date, until=end_date)  # Fake users to be filtered out (author_id NOT IN (SELECT id from users where fake=1))

            count_exception = True
            while (count_exception):
                count_exception = False
                try:
                    num_items = commits.totalCount
                except GithubException as ghe:
                    if str(ghe).startswith('500'):  # former == '500 None':
                        logging.warning('Failed to get commits from this project (500 None: Ignoring Repo): {}'.format(repoName))
                        return
                    elif str(ghe).startswith('409'):
                        logging.warning('Failed to get commits from this project (409 Empty: Ignoring Repo):'.format(repoName))
                        return
                    else:
                        logging.warning('Failed to get commits from this project (GITHUB Unknown: Retrying):'.format(repoName))
                        count_exception = True
                    pass
                except Timeout:
                    logging.warning('Failed to get commits from this project (TIMEOUT: Retrying):'.format(repoName))
                    count_exception = True
                    pass
                except:
                    logging.warning('Failed to get commits from this project (Probably Empty): '.format(repoName))
                    return

            last_page = int(num_items / cfg.items_per_page)
            last_page_read = 0

            if (outputFileName in os.listdir(workingFolder)):
                commits_data = pandas.read_csv(os.path.join(workingFolder, outputFileName), sep=cfg.CSV_separator)
                if (tmpSavefile in os.listdir(workingFolder)):
                    last_page_read = util.getLastPageRead(os.path.join(workingFolder, tmpSavefile))
                logging.info("Resuming Extraction")
            else:
                commits_data = pandas.DataFrame(columns=['sha', 'author_id', 'date'])
                logging.info("Starting New Extraction")

            if tmpExcludedCommits in os.listdir(workingFolder):
                excluded_commits = pandas.read_csv(os.path.join(workingFolder, tmpExcludedCommits), sep=cfg.CSV_separator)
            else:
                excluded_commits = pandas.DataFrame(columns=['sha'])

                try:
                    for page in range(last_page_read, last_page + 1):
                        commits_page = commits.get_page(page)
                        for commit in commits_page:
                            util.waitRateLimit(g)
                            sha = commit.sha
                            if ((sha not in commits_data.sha.tolist()) and (sha not in excluded_commits.sha.tolist())):
                                if (
                                commit.author):  ### If author is NoneType, that means the author is no longer active in GitHub
                                    util.waitRateLimit(g)
                                    author_id = commit.author.login  ### HERE IS THE DIFFERENCE
                                    date = commit.commit.author.date
                                    util.add(commits_data, [sha, author_id, date])
                    if (len(commits_data) > 0):
                        commits_data.to_csv(os.path.join(workingFolder, outputFileName),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
                except IncompletableObject:
                    logging.warning('Github Exception 400: Returned object contains no URL. SHA: {}'.format(sha))
                    util.add(excluded_commits, [sha])
                    if (len(commits_data) > 0):
                        commits_data.to_csv(os.path.join(workingFolder, outputFileName),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
                    excluded_commits.to_csv(os.path.join(workingFolder, tmpExcludedCommits),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
                    with open(os.path.join(workingFolder, tmpSavefile), "w") as statusSaver:
                        statusSaver.write('last_page:{}'.format(page))
                    exception_thrown = True
                    pass
                except GithubException as ghe:
                    logging.warning('Exception Occurred While Getting COMMITS: Github {}'.format(ghe))
                    if (len(commits_data) > 0):
                        commits_data.to_csv(os.path.join(workingFolder, outputFileName),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
                    with open(os.path.join(workingFolder, tmpSavefile), "w") as statusSaver:
                        statusSaver.write('last_page:{}'.format(page))
                    exception_thrown = True
                    pass
                except Timeout:
                    logging.warning('Exception Occurred While Getting COMMITS: Timeout')
                    if (len(commits_data) > 0):
                        commits_data.to_csv(os.path.join(workingFolder, outputFileName),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
                    with open(os.path.join(workingFolder, tmpSavefile), "w") as statusSaver:
                        statusSaver.write('last_page:{}'.format(page))
                    exception_thrown = True
                    pass
                except AttributeError:
                    logging.warning('Exception Occurred While Getting COMMIT DATA: NoneType for Author. SHA: {}'.format(sha))
                    util.add(excluded_commits, [sha])
                    if (len(commits_data) > 0):
                        commits_data.to_csv(os.path.join(workingFolder, outputFileName),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
                    excluded_commits.to_csv(os.path.join(workingFolder, tmpExcludedCommits),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
                    with open(os.path.join(workingFolder, tmpSavefile), "w") as statusSaver:
                        statusSaver.write('last_page:{}'.format(page))
                    exception_thrown = True
                    pass
                except:
                    logging.warning('Execution Interrupted While Getting COMMITS')
                    if (len(commits_data) > 0):
                        commits_data.to_csv(os.path.join(workingFolder, outputFileName),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
                    with open(os.path.join(workingFolder, tmpSavefile), "w") as statusSaver:
                        statusSaver.write('last_page:{}'.format(page))
                    raise
        logging.info("Commit Extraction Complete")
        with open(os.path.join(workingFolder, tmpStatusFile), "w") as statusSaver:
            statusSaver.write('COMPLETE;{}'.format(cfg.data_collection_date))

def writeCommitHistoryTable(workingFolder, commits_data):
    """Writes the commit history in form of a table of days x developers. Each cell contains the number of commits"""
    # GET MIN and MAX COMMIT DATETIME
    max_commit_date = max(commits_data['date'])
    min_commit_date = min(commits_data['date'])

    column_names = ['user_id']
    for single_date in util.daterange(min_commit_date, max_commit_date):  # daterange(min_commit_date, max_commit_date):
        column_names.append(single_date.strftime("%Y-%m-%d"))

    # ITERATE UNIQUE USERS (U)
    devs_list = commits_data.author_id.unique()
    u_data = []
    for u in devs_list:
        user_id = u
        cur_user_data = [user_id]
        date_commit_count = pandas.to_datetime(commits_data[['date']][commits_data['author_id'] == u].pop('date'),
                                               format="%Y-%m-%d").dt.date.value_counts()
        # ITERATE FROM DAY1 --> DAYN (D)
        for d in column_names[1:]:
            # IF U COMMITTED DURING D THEN U[D]=1 ELSE U(D)=0
            try:
                cur_user_data.append(date_commit_count[pandas.to_datetime(d).date()])
            except Exception:  # add "as name_given_to_exception" before ":" to get info
                cur_user_data.append(0)
        # print("finished user", u)
        u_data.append(cur_user_data)

    commit_table = pandas.DataFrame(u_data, columns=column_names)
    commit_table.to_csv(os.path.join(workingFolder, cfg.commit_history_table_file_name),
                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
    logging.info("Commit History Table Written")
    return commit_table

def writePauses(workingFolder, commit_table):
    """Computes the Pauses and writes
    1. the Intervals file containing for each developer the list of its pauses' length
    2. the Breaks Dates file containing for each developer the list of date intervals"""
    # Calcola days between commits, if commits are in adjacent days count 1
    pauses_duration_list = []
    pauses_dates_list = []
    for index, u in commit_table.iterrows():
        row = [u[0]]  # User_id
        current_pause_dates = [u[0]]  # User_id
        commit_dates = []
        for i in range(1, len(u)):
            if (u[i] > 0):
                commit_dates.append(commit_table.columns[i])
        for i in range(0, len(commit_dates) - 1):
            period = util.daysBetween(commit_dates[i], commit_dates[i + 1])
            if (period > 1):
                row.append(period)
                current_pause_dates.append(commit_dates[i] + '/' + commit_dates[i + 1])
        # ADD LAST PAUSE
        last_commit_day = commit_dates[-1]
        collection_day=cfg.data_collection_date
        period = util.daysBetween(last_commit_day, collection_day)
        if (period > 1):
            row.append(period)
            current_pause_dates.append(last_commit_day + '/' + collection_day)

        # Wrap up the list
        pauses_duration_list.append(row)
        pauses_dates_list.append(current_pause_dates)
        user_lifespan = util.daysBetween(commit_dates[0], commit_dates[len(commit_dates) - 1]) + 1
        commit_frequency = len(commit_dates) / user_lifespan
        row.append(user_lifespan)
        row.append(commit_frequency)
    logging.info('Inactivity Computation Done')

    with open(os.path.join(workingFolder, cfg.pauses_list_file_name), 'w', newline='') as outcsv:
        # configure writer to write standard csv file
        writer = csv.writer(outcsv, quoting=csv.QUOTE_NONE, delimiter=cfg.CSV_separator, quotechar='"', escapechar='\\')
        for r in pauses_duration_list:
            # Write item to outcsv
            writer.writerow(r)

    with open(os.path.join(workingFolder, cfg.pauses_dates_file_name), 'w', newline='') as outcsv:
        # configure writer to write standard csv file
        writer = csv.writer(outcsv, quoting=csv.QUOTE_NONE, delimiter=cfg.CSV_separator, quotechar='"', escapechar='\\')
        for r in pauses_dates_list:
            # Write item to outcsv
            writer.writerow(r)

def mergeProjectsCommits(path, main_project_name):  # No filter on core_devs_df. All developers are taken
    proj_path = os.path.join(path, main_project_name)
    commits_data = pandas.read_csv(os.path.join(proj_path, cfg.commit_list_file_name), sep=cfg.CSV_separator)

    projects = os.listdir(path)
    for project in projects:
        if ((project != main_project_name) and (os.path.isdir(os.path.join(path, project)))):
            proj_path = os.path.join(path, project)
            if cfg.commit_list_file_name in os.listdir(proj_path):
                project_commits = pandas.read_csv(os.path.join(proj_path, cfg.commit_list_file_name), sep=cfg.CSV_separator)
                commits_data = pandas.concat([commits_data, project_commits], ignore_index=True)

    commits_data.to_csv(os.path.join(path, cfg.commit_list_file_name),
                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
    logging.info('All the Organization commits have been merged with '.format(main_project_name))

### MAIN FUNCTION
def main(gitRepoName, token):
    ### SET THE PROJECT
    splitRepoName = gitRepoName.split('/')
    organization = splitRepoName[0]
    project = splitRepoName[1]

    os.makedirs(cfg.logs_folder, exist_ok=True)
    logfile = cfg.logs_folder+"/Commit_Extraction_"+organization+".log"
    logging.basicConfig(filename=logfile, level=logging.INFO)

    g = Github(token)
    try:
        g.get_rate_limit()
    except Exception as e:
        print('Exception {}'.format(e))
        logging.error(e)
        return
    g.per_page = cfg.items_per_page

    print("Running the Commit Extraction. \n Connection Done. \n Logging in {}".format(logfile))
    logging.info("Commit Extraction Started for {}.".format(organization))

    organizationsFolder = cfg.main_folder
    os.makedirs(organizationsFolder, exist_ok=True)

    organizationFolder = os.path.join(organizationsFolder, organization)
    os.makedirs(organizationsFolder, exist_ok=True)

    runCommitExtractionRoutine(g, organizationFolder, organization, project)
    #core_devs_df = findCoreDevelopers(organizationFolder, project)
    #core_devs_list = core_devs_df.dev.tolist()
    #logging.info('Commit Extraction COMPLETE for the Main Project: {}! {} Core developers found.'.format(project, len(core_devs_list)))

    util.waitRateLimit(g)
    org = g.get_organization(organization)
    org_repos = org.get_repos(type='all')

    try: ### Only for Log (Block)
        num_repos = org_repos.totalCount - 1
    except:
        num_repos = 'Unknown'

    repo_num = 0 ### Only for Log
    for repo in org_repos:
        util.waitRateLimit(g)
        project_name = repo.name
        if project_name != project:
            repo_num += 1 ### Only for Log
            runCommitExtractionRoutine(g, organizationFolder, organization, project_name)
    logging.info('Commit Extraction COMPLETE for {} of {} Side Projects'.format(repo_num,num_repos))

    logging.info('Merging the Commits in the WHOLE {} Organization'.format(organization))
    mergeProjectsCommits(organizationFolder, project)  # No filter on core_devs_df. All developers are taken

    if cfg.commit_list_file_name in os.listdir(organizationFolder):
        commits_data = pandas.read_csv(os.path.join(organizationFolder, cfg.commit_list_file_name), sep=cfg.CSV_separator)
        writeCommitHistoryTable(organizationFolder, commits_data)

    if cfg.commit_history_table_file_name in os.listdir(organizationFolder):
        commit_table = pandas.read_csv(os.path.join(organizationFolder, cfg.commit_history_table_file_name), sep=cfg.CSV_separator)
        writePauses(organizationFolder, commit_table)

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