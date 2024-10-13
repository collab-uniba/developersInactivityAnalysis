"""
This script collects and aggregates missing pull requests (PRs) and commits data from multiple repositories within an organization.
It processes each repository to extract relevant data, saves the data at both the repository and organization levels, and outputs the results to CSV files.
The script is designed to help analyze developer inactivity by identifying missing PRs and commits across the organization.
"""

### IMPORT SYSTEM MODULES
import os
from datetime import datetime
import logging
import sys
sys.path.append('../')

import pandas

### IMPORT CUSTOM MODULES
import Settings as cfg
import Utilities as util


### MAIN FUNCTION
def main(repos_list):
    workingFolder = cfg.main_folder

    missing_prs_filename = 'prs_repo.csv'

    out_prs_filename = 'prs_list.csv'
    out_commits_filename = 'missing_commits_list.csv'

    # Aggregates the extracted 'prs_repo.csv' data per repo into a larger DataFrame 
    # at the entire organization level
    logging.info("Aggregating missing PRs and commits data at the organization level")
    for gitRepoName in repos_list:
        slug = gitRepoName.replace('https://github.com/', '')
        organization, _ = slug.split('/')
        organization_folder = os.path.join(workingFolder, organization)

        organization_prs_as_issues = pandas.DataFrame(columns=['id', 'date', 'author'])
        organization_missing_commits = pandas.DataFrame(columns=['sha', 'author_id', 'date'])

        for folder in os.listdir(organization_folder):
            logging.info(f"Processing {folder} in {organization}")
            # Check if the 'Other_Activities' directory exists within the organization folder
            if os.path.exists(organization_folder + '/' + folder + '/Other_Activities'):
                missing_prs_file_location = os.path.join(organization_folder, folder, 'Other_Activities')
                
                # Check if the 'prs_repo.csv' file exists in the 'Other_Activities' directory
                if missing_prs_filename in os.listdir(missing_prs_file_location):
                    logging.info(f"Found prs_repo.csv file in {organization}/{folder}")
                    # Read the data from the CSV file into a DataFrame
                    missing_prs_data = pandas.read_csv(os.path.join(missing_prs_file_location, missing_prs_filename), sep=cfg.CSV_separator)
                    
                    # Create a new DataFrame with selected columns: 'issue_id', 'date', and 'creator_login'
                    columns_to_merge = pandas.DataFrame({
                        'id': missing_prs_data['issue_id'],
                        'date': missing_prs_data['date'],
                        'author': missing_prs_data['creator_login']
                    })
                    
                    # Save the local DataFrame to a CSV file in the current folder
                    columns_to_merge.to_csv(
                        os.path.join(organization_folder, folder, out_prs_filename),
                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n'
                    )
                    
                    # Concatenate the local DataFrame with the organization-wide DataFrame
                    organization_prs_as_issues = pandas.concat([organization_prs_as_issues, columns_to_merge], ignore_index=True)

            # Check if the 'MissingCommits' directory exists within the current folder
            if os.path.exists(organization_folder + '/' + folder + '/MissingCommits'):
                missing_commits_file_location = os.path.join(organization_folder, folder, 'MissingCommits')
                
                # Initialize local DataFrame to store missing commits data for the current folder
                local_missing_commits = pandas.DataFrame(columns=['sha', 'author_id', 'date'])
                
                # Iterate through all files in the 'MissingCommits' directory
                for missing_commits_file in os.listdir(missing_commits_file_location):
                    # Process only CSV files
                    if missing_commits_file.endswith('.csv'):
                        logging.info(f"Found missing commits file in {organization}/{folder}")
                        # Read the missing commits data from the CSV file into a DataFrame
                        missing_commits_data = pandas.read_csv(os.path.join(missing_commits_file_location, missing_commits_file), sep=cfg.CSV_separator)
                        
                        # Concatenate the new data with the local DataFrame, ensuring no duplicate 'sha' values are added
                        local_missing_commits = pandas.concat([local_missing_commits, missing_commits_data[~missing_commits_data.sha.isin(local_missing_commits.sha)]], ignore_index=True)
                
                # Save the local missing commits data to a CSV file in the current folder
                local_missing_commits.to_csv(os.path.join(organization_folder, folder, out_commits_filename),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                
                # Concatenate the local missing commits data with the organization-wide DataFrame, ensuring no duplicate 'sha' values are added
                organization_missing_commits = pandas.concat([organization_missing_commits, local_missing_commits[
                    ~local_missing_commits.sha.isin(organization_missing_commits.sha)]], ignore_index=True)

        # Save the DataFrame containing PRs data to a CSV file in the organization folder
        logging.info(f"Saving PRs data to {organization_folder}")
        organization_prs_as_issues.to_csv(os.path.join(organization_folder, out_prs_filename),
                                          sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')

        # Save the DataFrame containing missing commits data to a CSV file in the organization folder
        logging.info(f"Saving missing commits data to {organization_folder}")
        organization_missing_commits.to_csv(os.path.join(organization_folder, out_commits_filename),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    os.makedirs(cfg.logs_folder, exist_ok=True)
    timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d_%H%M')
    logfile = cfg.logs_folder+f"/Missing_Stuff_Collector{timestamp}.log"
    logging.basicConfig(filename=logfile, level=logging.INFO)

    repos_list=util.getReposList()
    main(repos_list)
    print("Done.")