### GitHub Settings
items_per_page = 100  # The number of results in each page of the GitHub results. Max: 100
tokens_file = "../Resources/tokens.txt"  # The relative path of the file containing the list of the github tokens

### Extraction Settings
data_collection_date = "2020-01-15"  # The max date to consider for the commits and activities extraction
repos_file = "../Resources/repositories.txt"  # The relative path of the file containing the list of the repos <organization/repo>
main_folder = "../Organizations"  # The main folder where results will be archived
logs_folder = "../logs"  # The folder where the logs will be archived

TF_report_folder = "TF_Results"  # The folder where the TF/core developers are archived
TF_developers_file = "TF_devs.csv" # The file where the TF/core developers are listed as <name;login>
## WARNING: The correct path to save the <TF_developers_file> is <TF_report_folder>/<organization/mainRepo>/<TF_developers_file>

commit_list_file_name = "commit_list.csv"  # The file where the repo commits will be archived
commit_history_table_file_name = "commit_history_table.csv"  # The file where the 'devs by dates' table for each repo will be archived
pauses_list_file_name = "pauses_duration_list.csv"  # The file where the lists of devs' pauses durations will be archived
pauses_dates_file_name = "pauses_dates_list.csv"  # The file where the lists of devs' pauses boundary dates will be archived
issue_comments_list_file_name = "issues_comments_repo.csv"  # The file where the repo issue comments will be archived
pulls_comments_list_file_name = "pulls_comments_repo.csv"  # The file where the repo pulls comments will be archived
issue_events_list_file_name = "issues_events_repo.csv"  # The file where the repo issue events will be archived
issue_pr_list_file_name = "issues_prs_repo.csv"  # The file where the repo issue/PRs creations will be archived

#core_commit_coverage = 0.8 #Percentage of commits to cover for the core identification

### Files Settings
CSV_separator = ";"  # Character for cell separation in the used files
CSV_missing = "NA"  # Character for the missing values in the used files

### Breaks Identification
actions_folder_name = 'Actions_Tables'  # The folder where the other repo activities will be archived
breaks_folder_name = 'Dev_Breaks'  # The folder where the breaks list for each developer will be archived
sliding_window_size = 90  # The size in days of the sliding window
shift = 7  # The number of days to shift the sliding window of

### Breaks Labeling
labeled_breaks_folder_name = breaks_folder_name + '/Labeled_Breaks'  # The folder where the labeled breaks list for each developer will be archived
gone_threshold = 365  # Threshold to label a break as 'GONE'

### Statistics
chains_folder_name = 'Chains'  # The folder where the %age of the transitions for each organization will be archived

### CONSTANTS
A = 'ACTIVE'  # Label of the Active status: Developers contribute commits
NC = 'NON_CODING'  # Label of the Non-coding status: Developers do not contribute commits, but show other activity signals
I = 'INACTIVE'  # Label of the Inactive status: Developers do not show any activity signal
G = 'GONE'  # Label of the Gone status: Developers have been Inactive for longer than <gone_threshold>

#key_folders = ['Activities_Plots', 'Dead&Resurrected_Users', 'Hibernated&Unfrozen_Users', 'Sleeping&Awaken_Users', 'DevStats_Plots', 'Longer_Breaks']
