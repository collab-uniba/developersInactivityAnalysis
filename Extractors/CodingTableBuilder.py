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

def mergeCodingActivities(organization):
    organization_folder = os.path.join(cfg.main_folder, organization)

    for folder in os.listdir(organization_folder):
        if os.path.isdir(organization_folder + '/' + folder):
            buildCodingActivitiesLists(os.path.join(organization_folder, folder))

    # General one
    buildCodingActivitiesLists(organization_folder)

def buildCodingActivitiesLists(destination_folder):
    commits_filename = cfg.commit_list_file_name
    prs_filename = 'prs_list.csv'
    missing_commits_filename = 'missing_commits_list.csv'

    out_coding_list_filename = 'coding_activities_list.csv'

    coding_activities_data = pandas.DataFrame(columns=['id', 'date', 'author'])

    if commits_filename in os.listdir(destination_folder):
        commits_data = pandas.read_csv(os.path.join(destination_folder, commits_filename), sep=cfg.CSV_separator)
        columns_to_merge = pandas.DataFrame({'id': commits_data['sha'],
                                             'date': commits_data['date'],
                                             'author': commits_data['author_id']})
        coding_activities_data = pandas.concat([coding_activities_data,
                                                columns_to_merge[~columns_to_merge.id.isin(coding_activities_data.id)]],
                                               ignore_index=True)
    if prs_filename in os.listdir(destination_folder):
        prs_data = pandas.read_csv(os.path.join(destination_folder, prs_filename), sep=cfg.CSV_separator)
        coding_activities_data = pandas.concat([coding_activities_data,
                                                prs_data[~prs_data.id.isin(coding_activities_data.id)]],
                                               ignore_index=True)
    if missing_commits_filename in os.listdir(destination_folder):
        missing_commits_data = pandas.read_csv(os.path.join(destination_folder, missing_commits_filename),
                                               sep=cfg.CSV_separator)
        columns_to_merge = pandas.DataFrame({'id': missing_commits_data['sha'],
                                             'date': missing_commits_data['date'],
                                             'author': missing_commits_data['author_id']})
        coding_activities_data = pandas.concat([coding_activities_data,
                                                columns_to_merge[~columns_to_merge.id.isin(coding_activities_data.id)]],
                                               ignore_index=True)

    if not coding_activities_data.empty:
        coding_activities_data.to_csv(os.path.join(destination_folder, out_coding_list_filename),
                                      sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None,
                                      line_terminator='\n')

def buildHistoryTables(organization):
    organization_folder = os.path.join(cfg.main_folder, organization)

    for folder in os.listdir(organization_folder):
        if os.path.isdir(organization_folder + '/' + folder):
            buildTable(os.path.join(organization_folder, folder))

    # General one
    buildTable(organization_folder)

def buildTable(destination_folder):
    coding_activities_filename = 'coding_activities_list.csv'

    out_coding_history_filename = 'coding_history_table.csv'

    if coding_activities_filename in os.listdir(destination_folder):
        coding_data = pandas.read_csv(os.path.join(destination_folder, coding_activities_filename), sep=cfg.CSV_separator)

        logging.info('Coding Activities found: Creating History Table for {}'.format(destination_folder))
        # Write the Coding history in form of a table of days x developers. Each cell contains the number of Coding Activities
        # GET MIN and MAX DATETIME
        max_date = max(coding_data['date'])
        min_date = min(coding_data['date'])

        column_names = ['user_id']
        for single_date in util.daterange(min_date, max_date):
            column_names.append(single_date.strftime("%Y-%m-%d"))

        # ITERATE UNIQUE USERS (U)
        devs_list = coding_data.author.unique()
        u_data = []
        for u in devs_list:
            user_id = u
            cur_user_data = [user_id]
            date_count = pandas.to_datetime(coding_data[['date']][coding_data['author'] == u].pop('date'),
                                            format="%Y-%m-%d").dt.date.value_counts()
            # ITERATE FROM DAY1 --> DAYN (D)
            for d in column_names[1:]:
                # IF U COMMITTED DURING D THEN U[D]=1 ELSE U(D)=0
                try:
                    cur_user_data.append(date_count[pandas.to_datetime(d).date()])
                except Exception:  # add "as name_given_to_exception" before ":" to get info
                    cur_user_data.append(0)
            # print("finished user", u)
            u_data.append(cur_user_data)

        coding_history_table = pandas.DataFrame(u_data, columns=column_names)
        coding_history_table.to_csv(os.path.join(destination_folder, out_coding_history_filename),
                             sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None,
                             line_terminator='\n')

def writePauses(organization):
    organization_folder = os.path.join(cfg.main_folder, organization)

    for folder in os.listdir(organization_folder):
        if os.path.isdir(organization_folder + '/' + folder):
            computePauses(os.path.join(organization_folder, folder))

    # General one
    computePauses(organization_folder)

def computePauses(destination_folder):
    """Computes the Pauses and writes
    1. the Intervals file containing for each developer the list of its pauses' length
    2. the Breaks Dates file containing for each developer the list of date intervals"""

    coding_history_filename = 'coding_history_table.csv'
    out_coding_pauses_filename = 'coding_pauses.csv'
    out_coding_pauses_dates_filename = 'coding_pauses_dates.csv'

    if coding_history_filename in os.listdir(destination_folder):
        coding_table = pandas.read_csv(os.path.join(destination_folder, coding_history_filename), sep=cfg.CSV_separator)

        # Calcola days between coding activities, if activities are in adjacent days count 1
        pauses_duration_list = []
        pauses_dates_list = []
        for index, u in coding_table.iterrows():
            row = [u[0]]  # User_id
            current_pause_dates = [u[0]]  # User_id
            coding_dates = []
            for i in range(1, len(u)):
                if (u[i] > 0):
                    coding_dates.append(coding_table.columns[i])
            for i in range(0, len(coding_dates) - 1):
                period = util.daysBetween(coding_dates[i], coding_dates[i + 1])
                if (period > 1):
                    row.append(period)
                    current_pause_dates.append(coding_dates[i] + '/' + coding_dates[i + 1])
            # ADD LAST PAUSE
            last_coding_day = coding_dates[-1]
            collection_day=cfg.data_collection_date
            period = util.daysBetween(last_coding_day, collection_day)
            if (period > 1):
                row.append(period)
                current_pause_dates.append(last_coding_day + '/' + collection_day)

            # Wrap up the list
            pauses_duration_list.append(row)
            pauses_dates_list.append(current_pause_dates)
            user_lifespan = util.daysBetween(coding_dates[0], coding_dates[len(coding_dates) - 1]) + 1
            commit_frequency = len(coding_dates) / user_lifespan
            row.append(user_lifespan)
            row.append(commit_frequency)

        with open(os.path.join(destination_folder, out_coding_pauses_filename), 'w', newline='') as outcsv:
            writer = csv.writer(outcsv, quoting=csv.QUOTE_NONE, delimiter=cfg.CSV_separator, quotechar='"', escapechar='\\')
            for r in pauses_duration_list:
                writer.writerow(r)

        with open(os.path.join(destination_folder, out_coding_pauses_dates_filename), 'w', newline='') as outcsv:
            writer = csv.writer(outcsv, quoting=csv.QUOTE_NONE, delimiter=cfg.CSV_separator, quotechar='"', escapechar='\\')
            for r in pauses_dates_list:
                writer.writerow(r)

### MAIN FUNCTION
def main(repos_list):

    for gitRepoName in repos_list:
        organization, project = gitRepoName.split('/')

        logfile = cfg.logs_folder + "/Coding_Table_Pause_Builder.log"
        logging.basicConfig(filename=logfile, level=logging.INFO)

        mergeCodingActivities(organization)
        logging.info('Coding Activities Merged for {}'.format(organization))

        buildHistoryTables(organization)
        logging.info('History Table Written for {}'.format(organization))

        writePauses(organization)
        logging.info('Pauses Data Written (list and dates) for {}'.format(organization))

    logging.info('History Tables and Pauses computing SUCCESSFULLY COMPLETED for {}'.format(organization))

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    repos_list = util.getReposList()
    main(repos_list)