"""
This script processes coding activities data from multiple repositories within an organization.
It performs the following tasks:
1. Merges coding activities (commits, pull requests, and missing commits) into a single list for each repository and the organization as a whole.
2. Builds history tables that represent coding activities in a tabular format, with days as columns and developers as rows.
3. Computes pauses in coding activities, identifying periods of inactivity for each developer and writing this data to CSV files.

The script is designed to help analyze developer activity and inactivity across an organization by consolidating and processing data from various sources.
"""
import csv
import logging
import os
import sys

sys.path.append('../')
from datetime import datetime

import pandas

### IMPORT CUSTOM MODULES
import Settings as cfg
import Utilities as util

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def mergeCodingActivities(organization):
    logging.info(f"Starting mergeCodingActivities for organization: {organization}")
    organization_folder = os.path.join(cfg.main_folder, organization)
    ensure_directory_exists(organization_folder)

    for folder in os.listdir(organization_folder):
        if folder == '.github':
            continue
        folder_path = os.path.join(organization_folder, folder)
        if os.path.isdir(folder_path):
            logging.debug(f"Processing folder: {folder}")
            buildCodingActivitiesLists(folder_path)

    # General one
    buildCodingActivitiesLists(organization_folder)
    logging.info(f"Completed mergeCodingActivities for organization: {organization}")

def buildCodingActivitiesLists(destination_folder):
    logging.info(f"Starting buildCodingActivitiesLists for folder: {destination_folder}")
    commits_filename = cfg.commit_list_file_name
    prs_filename = 'prs_list.csv'
    missing_commits_filename = 'missing_commits_list.csv'

    out_coding_list_filename = 'coding_activities_list.csv'

    coding_activities_data = pandas.DataFrame(columns=['id', 'date', 'author'])

    try:
        if commits_filename in os.listdir(destination_folder):
            logging.debug(f"Reading commits data from {commits_filename}")
            commits_data = pandas.read_csv(os.path.join(destination_folder, commits_filename), sep=cfg.CSV_separator)
            columns_to_merge = pandas.DataFrame({'id': commits_data['sha'],
                                                 'date': commits_data['date'],
                                                 'author': commits_data['author_id']})
            coding_activities_data = pandas.concat([coding_activities_data,
                                                    columns_to_merge[~columns_to_merge.id.isin(coding_activities_data.id)]],
                                                   ignore_index=True)
        if prs_filename in os.listdir(destination_folder):
            logging.debug(f"Reading PRs data from {prs_filename}")
            prs_data = pandas.read_csv(os.path.join(destination_folder, prs_filename), sep=cfg.CSV_separator)
            coding_activities_data = pandas.concat([coding_activities_data,
                                                    prs_data[~prs_data.id.isin(coding_activities_data.id)]],
                                                   ignore_index=True)
        if missing_commits_filename in os.listdir(destination_folder):
            logging.debug(f"Reading missing commits data from {missing_commits_filename}")
            missing_commits_data = pandas.read_csv(os.path.join(destination_folder, missing_commits_filename),
                                                   sep=cfg.CSV_separator)
            columns_to_merge = pandas.DataFrame({'id': missing_commits_data['sha'],
                                                 'date': missing_commits_data['date'],
                                                 'author': missing_commits_data['author_id']})
            coding_activities_data = pandas.concat([coding_activities_data,
                                                    columns_to_merge[~columns_to_merge.id.isin(coding_activities_data.id)]],
                                                   ignore_index=True)

        if not coding_activities_data.empty:
            logging.debug(f"Writing coding activities data to {out_coding_list_filename}")
            coding_activities_data.to_csv(os.path.join(destination_folder, out_coding_list_filename),
                                          sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None,
                                          lineterminator='\n')
    except Exception as e:
        logging.exception(f"Error processing {destination_folder}: {e}")
    logging.info(f"Completed buildCodingActivitiesLists for folder: {destination_folder}")

def buildHistoryTables(organization):
    logging.info(f"Starting buildHistoryTables for organization: {organization}")
    organization_folder = os.path.join(cfg.main_folder, organization)
    ensure_directory_exists(organization_folder)

    for folder in os.listdir(organization_folder):
        if folder == '.github':
            continue
        folder_path = os.path.join(organization_folder, folder)
        if os.path.isdir(folder_path):
            logging.debug(f"Processing folder: {folder}")
            buildTable(folder_path)

    # General one
    buildTable(organization_folder)
    logging.info(f"Completed buildHistoryTables for organization: {organization}")

def buildTable(destination_folder):
    logging.info(f"Starting buildTable for folder: {destination_folder}")
    coding_activities_filename = 'coding_activities_list.csv'
    out_coding_history_filename = 'coding_history_table.csv'

    if coding_activities_filename in os.listdir(destination_folder):
        try:
            coding_data = pandas.read_csv(os.path.join(destination_folder, coding_activities_filename), sep=cfg.CSV_separator)

            logging.info(f'Coding Activities found: Creating History Table for {destination_folder}')
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
                                                format="%Y-%m-%d %H:%M:%S%z").dt.date.value_counts()
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
            logging.debug(f"Writing coding history table to {out_coding_history_filename}")
            coding_history_table.to_csv(os.path.join(destination_folder, out_coding_history_filename),
                                 sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None,
                                 lineterminator='\n')
        except Exception as e:
            logging.exception(f"Error building table for {destination_folder}: {e}")
    logging.info(f"Completed buildTable for folder: {destination_folder}")

def writePauses(organization):
    logging.info(f"Starting writePauses for organization: {organization}")
    organization_folder = os.path.join(cfg.main_folder, organization)
    ensure_directory_exists(organization_folder)

    for folder in os.listdir(organization_folder):
        if folder == '.github':
            continue
        folder_path = os.path.join(organization_folder, folder)
        if os.path.isdir(folder_path):
            logging.debug(f"Processing folder: {folder}")
            computePauses(folder_path)

    # General one
    computePauses(organization_folder)
    logging.info(f"Completed writePauses for organization: {organization}")

def computePauses(destination_folder):
    logging.info(f"Starting computePauses for folder: {destination_folder}")
    """Computes the Pauses and writes
    1. the Intervals file containing for each developer the list of its pauses' length
    2. the Breaks Dates file containing for each developer the list of date intervals"""

    coding_history_filename = 'coding_history_table.csv'
    out_coding_pauses_filename = 'coding_pauses.csv'
    out_coding_pauses_dates_filename = 'coding_pauses_dates.csv'

    if coding_history_filename in os.listdir(destination_folder):
        try:
            coding_table = pandas.read_csv(os.path.join(destination_folder, coding_history_filename), sep=cfg.CSV_separator)

            # Calcola days between coding activities, if activities are in adjacent days count 1
            pauses_duration_list = []
            pauses_dates_list = []
            for _, u in coding_table.iterrows():
                row = [u.iloc[0]]  # User_id
                current_pause_dates = [u.iloc[0]]   # User_id
                coding_dates = []
                for i in range(1, len(u)):
                    if (u.iloc[i] > 0):
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

            logging.debug(f"Writing coding pauses to {out_coding_pauses_filename}")
            with open(os.path.join(destination_folder, out_coding_pauses_filename), 'w', newline='') as outcsv:
                writer = csv.writer(outcsv, quoting=csv.QUOTE_NONE, delimiter=cfg.CSV_separator, quotechar='"', escapechar='\\')
                for r in pauses_duration_list:
                    writer.writerow(r)

            logging.debug(f"Writing coding pauses dates to {out_coding_pauses_dates_filename}")
            with open(os.path.join(destination_folder, out_coding_pauses_dates_filename), 'w', newline='') as outcsv:
                writer = csv.writer(outcsv, quoting=csv.QUOTE_NONE, delimiter=cfg.CSV_separator, quotechar='"', escapechar='\\')
                for r in pauses_dates_list:
                    writer.writerow(r)
        except Exception as e:
            logging.exception(f"Error computing pauses for {destination_folder}: {e}")
    logging.info(f"Completed computePauses for folder: {destination_folder}")

### MAIN FUNCTION
def main(repos_list):
    logging.info("Starting main function")
    for gitRepoName in repos_list:
        slug = gitRepoName.replace('https://github.com/', '')
        organization, _ = slug.split('/')

        mergeCodingActivities(organization)
        logging.info('Coding Activities Merged for {}'.format(organization))

        buildHistoryTables(organization)
        logging.info('History Table Written for {}'.format(organization))

        writePauses(organization)
        logging.info('Pauses Data Written (list and dates) for {}'.format(organization))

    logging.info('History Tables and Pauses computing SUCCESSFULLY COMPLETED for all organizations')

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    ensure_directory_exists(cfg.logs_folder)
    timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d_%H%M')
    logfile = cfg.logs_folder+f"/Coding_Table_Builder_{timestamp}.log"
    logging.basicConfig(filename=logfile, level=logging.DEBUG)
    
    repos_list = util.getReposList()
    main(repos_list)
    print("Done.")
    