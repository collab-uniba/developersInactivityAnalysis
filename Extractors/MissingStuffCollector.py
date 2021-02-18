### IMPORT EXCEPTION MODULES

### IMPORT SYSTEM MODULES
import os, pandas, csv, sys
from datetime import datetime
import datetime as dt

### IMPORT CUSTOM MODULES
import Settings as cfg
import Utilities as util

### MAIN FUNCTION
def main(repos_list):
    workingFolder = cfg.main_folder

    missing_prs_filename = 'prs_repo.csv'

    out_prs_filename = 'prs_list.csv'
    out_commits_filename = 'missing_commits_list.csv'

    for gitRepoName in repos_list:
        organization, project = gitRepoName.split('/')
        organization_folder = os.path.join(workingFolder, organization)

        organization_prs_as_issues = pandas.DataFrame(columns=['id', 'date', 'author'])
        organization_missing_commits = pandas.DataFrame(columns=['sha', 'author_id', 'date'])

        for folder in os.listdir(organization_folder):
            # Check for PRs
            if os.path.exists(organization_folder + '/' + folder + '/Other_Activities'):
                missing_prs_file_location = os.path.join(organization_folder, folder, 'Other_Activities')
                if missing_prs_filename in os.listdir(missing_prs_file_location):
                    missing_prs_data = pandas.read_csv(os.path.join(missing_prs_file_location, missing_prs_filename), sep=cfg.CSV_separator)
                    columns_to_merge = pandas.DataFrame({'id': missing_prs_data['issue_id'],
                                                         'date': missing_prs_data['date'],
                                                         'author': missing_prs_data['creator_login']})
                    organization_prs_as_issues = pandas.concat([organization_prs_as_issues, columns_to_merge], ignore_index=True)

            # Check for Missing Commits
            if os.path.exists(organization_folder + '/' + folder + '/MissingCommits'):
                missing_commits_file_location = os.path.join(organization_folder, folder, 'MissingCommits')
                for missing_commits_file in os.listdir(missing_commits_file_location):
                    if missing_commits_file.endswith('.csv'):
                        missing_commits_data = pandas.read_csv(os.path.join(missing_commits_file_location, missing_commits_file), sep=cfg.CSV_separator)
                        organization_missing_commits = pandas.concat([organization_missing_commits, missing_commits_data[~missing_commits_data.sha.isin(organization_missing_commits.sha)]], ignore_index=True)

        organization_prs_as_issues.to_csv(os.path.join(organization_folder, out_prs_filename),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
        organization_missing_commits.to_csv(os.path.join(organization_folder, out_commits_filename),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    repos_list=util.getReposList()
    main(repos_list)