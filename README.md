# Will you come back to contribute? Investigating the inactivitiy of OSS developers in GitHub
[![DOI](https://zenodo.org/badge/183011533.svg)](https://zenodo.org/badge/latestdoi/183011533)

### Setup

Use the `main` branch, not `master`.

Add to the root a folder named `Resources/` with the following files: 
- `repositories.txt` containing the list of projects (one per line) to be analyzed, in the following format `org/repo_name` (e.g., `atom/atom); 
- `tokens.txt` (optional) containinig the list of GH tokens to be used;

### Sampling of developers

#### Core Developers Selection

Refer to this [README.md](CoreSelection/README.md) file.

#### Truck-Factor Developer Selection

Refer to this [README.md](TruckFactor/README.md) file.

---

### CommitExtractor.py


#### Params

Uses the tokens defined in `Resources/tokens.txt` and the list of repository urls in `Resources/repositories.txt`, as defined in the `Settings.py` file.

- None.

#### Requirements

- Set files and folders names in the `Settings.py` file

#### Execution

`python CommitExtractor.py`


#### Output

- `logs/Commit_Extraction_organization.log`: log file
- `Organizations/<organization>/[<repo1>...<repoN>]/`: Results folders
- For each repo folder: 
  - `commit_list.csv`: List of the commits in the format: <SHA; author_id; date>
  - `commit_history_table.csv`: Matrix of autors and dates. The cells contain the number of the commits of a developer in one day
  - `pauses_duration_list.csv`: List of pauses durations in days for each developer in the format: <dev; listOfDurations>
  - `pauses_dates_list.csv`: List of pauses dates for each developer in the format: <dev; listOfPauseDates>
- The same files are given after merging the commits of every organization's repo in the `Organizations/<organization>/` folder.

if you came here from point 2 of core selection you can now perform step 3 following [(CoreSelection | Step 3)](CoreSelection/README.md#L18)

---

### ActivitiesExtractor.py

#### Params

- None

#### Requirements

- Set of files and folders names in the `Settings.py` file

#### Execution

`python ActivitiesExtractor.py`


#### Output

- `logs/Commit_Extraction_organization.log`: log file
- `Organizations/<organization>/[<repo1>...<repoN>]/Other_Activities/`: Results folders
- For each repo folder:
  - `issues_comments_repo.csv`: List of the issue comments in the format: <id; date; creator_login>
  - `issues_events_repo.csv`: List of the issue events in the format: <id; date; creator_login>
  - `issues_prs_repo.csv`: List of the issue and pull request creations in the format: <id; date; creator_login>
  - `pulls_comments_repo.csv`: List of the pull request comments in the format: <id; date; creator_login>


### PullRequestExtractor.py

The script iterates over all repositories in a given organization to extract pull requests.

#### Params

- None

#### Requirements

- Set of files and folders names in the `Settings.py` file
- `Resources/tokens.txt`
- `Resources/repositories.txt`

#### Execution

`python PullRequestsExtractor.py`

#### Output

 * `logs/Pull_Request_Extraction_*.log`: log file
 * `Organizations/<organization>/[<repo1>...<repoN>]/Other_Activities/prs_repo.csv`: CSV files containing pull request data for each repository

### NonMergedCommitsExtractor.py

The script  automates the extraction of commits from non-merged pull requests in all the GitHub repositories of the organizations provided. 

#### Params

- None

#### Requirements

- Set of files and folders names in the `Settings.py` file
- `Resources/tokens.txt`
- `Resources/repositories.txt`

#### Execution

`python NonMergedCommitsExtractor.py`

#### Output

* `logs//Non_Merged_Commits_Extraction_*.log`: log file
* `Organizations/<organization>/[<repo1>...<repoN>]/MissingCommits/<PR_number>_commits.csv`: a CSV file containing commit data for each non-merged PRs for each repository of the organization.

### MissingStuffCollector.py

#### Params

- None

#### Requirements

- Set of files and folders names in the `Settings.py` file
- `Resources/repositories.txt`
- `Organizations/<organization>/[<repo1>...<repoN>]/Other_Activities/prs_repo.csv`: CSV files containing pull request data for each repository

#### Execution

`python MissingStuffCollector.py`

#### Output

* `Organizations/<organization>/[<repo1>...<repoN>]/Other_Activities/prs_list.csv`: CSV file containing data on PRs
* `Organizations/<organization>/[<repo1>...<repoN>]/MissingCommits/missing_commits_list.csv`: CSV file containing data on missing commits
* `Organizations/<organization>/prs_list.csv`: An aggregated CSV at the organization level containing data on all missing commits

### CodingTableBuilder.py

This script processes coding activities data from multiple repositories within an organization. It performs the following tasks:
1. Merges coding activities (commits, pull requests, and missing commits) into a single list for each repository and the organization as a whole.
2. Builds history tables that represent coding activities in a tabular format, with days as columns and developers as rows.
3. Computes pauses in coding activities, identifying periods of inactivity for each developer and writing this data to CSV files.

#### Params

- None

#### Requirements

- `Resources/repositories.txt`
- `Organizations/<organization>/<repo>/prs_list.csv`
- `Organizations/<organization>/<repo>/missing_commits_list.csv`

#### Execution

`python CodingTableBuilder.py`

#### Output

* `logs/Coding_Table_Builder_*.log`: timestamped log file
* `Organizations/<organization>/<repo>/coding_activities_list.csv`: Contains a consolidated list of coding activities (commits, pull requests, and missing commits) for the specified repository. Each entry includes the activity ID, date, and author.
* `Organizations/<organization>/<repo>/coding_history_table.csv`: Represents coding activities in a tabular format, with days as columns and developers as rows. Each cell contains the number of coding activities performed by a developer on a specific day.
* `Organizations/<organization>/<repo>/coding_pauses.csv`: Lists the lengths of pauses (periods of inactivity) for each developer. Each entry includes the developer's ID and the duration of each pause.
* `Organizations/<organization>/<repo>/coding_pauses_dates.csv`: Contains the date intervals for each pause for each developer. Each entry includes the developer's ID and the start and end dates of each pause.


---

### BreaksIdentification.py

#### Params

- `mode`: enter one of following modes ['tf', 'a80', 'a80mod', 'a80api']

#### Requirements

- Set files and folders names in the `Settings.py` file
- Insert the list of the TF/core developers (<TF_developers_file>) in the right folder. Formatted as a list of <name;login>. The path to save the file is set in the `Settings.py` file.
- Set the `window` size and the `shift` size in the `Settings.py` file

#### Execution

`python BreaksIdentification.py tf | a80 | a80mod | a80api`

#### Output

- `logs/Breaks_Identification.log`: log file
- `Organizations/<organization>/Dev_Breaks/`: Results folders
- For each developer in the TF file:
  - `<devLogin>_breaks.csv`: List of the breaks in the format: <len; dates; Tfov_used>

#### Algorithm

Let **D** be a developer to analyze and let **life(D)** be the number of days between its first and last commits.
For each sliding *window* **W** in **life(D)** which slides of *shift* days. The values of variables *window* (default 90 days) and *shift* (default 7 days) are set in the `Settings.py` file).

The goal is to select all the *breaks* (*pauses* that are larger than usual) associated with the *Tfov* (Far-out-value threshold) of the first window where they have been found:

1. PAUSES SELECTION **STEP**

- In the list `win_pauses`, put all the pauses within **W** (only these pauses define the rythm of **D** in **W**).
- In the list `partially_included`, put all the pauses partially within **W** (i.e., pauses that start in **W** and end in the next window).

2. *Tfov* DEFINITION **STEP**

- If `win_pauses` contains >=4 *pauses* then the **W** is valid, then use `win_pauses` to calculate *Tfov*. If *Tfov* is valid (i.e., *IQR*>1), then proceed to the breaks identification step (go to STEP 3).
- Else, when `win_pauses` < 4 (i.e., *Tfov* cannot be calculated) or if *Tfov* is invalid (i.e., *IQR*<=1) for **W**, then:
  - If a previous *Tfov* exists, then consider it as the current *Tfov* and proceed to the next step for breaks identification (go to STEP 3).
  - Otherwise, save into the list `clear_breaks` all the *pauses* from `partially_included` that are larger than the window size and have not been considered yet, ignore the other *pauses* in `win_pauses`; move forward **W** by *shift* days and RESTART (go back to STEP 1).

  (Note: The *pauses* that are larger than *shift* days will be considered in the next **W** and so on, whereas the smaller ones are not breaks and can be safely ignored).

3. BREAKS IDENTIFICATION **STEP**

- Select as *break* each couple *<p, t>* from the lists `win_pauses` and `partially_included` where *t* is *Tfov* and *p* is a *pause* > *Tfov*.
  - Move forward **W** by *shift* days and RESTART (go back to STEP 1).

4. FINAL **STEP** (When there are no more **W**)

- Compute *Avg_Tfov* as the average of all the valid *Tfovs* found.
- Save the *pauses* in the list `clear_breaks` as *breaks* (*<p, t>* where *t* is *Avg_Tfov*, and *p* is a *pause* > *Avg_Tfov* as for list definition).

---

### BreaksLabeling.py

#### Params

- `mode`: choose one of following modes ['tf', 'a80', 'a80mod', 'a80api']

#### Requirements

- Make sure to have already executed the `BreaksIdentification.py` script to get the `<devLogin>_breaks.csv` files (one for each developer).

#### Execution

`python BreaksLabeling.py tf | a80 | a80mod | a80api`

#### Output

- `logs/Breaks_Labeling.log`: events log file
- `Organizations/<organization>/Dev_Breaks/`: Results folders
- For each developer in the TF file:
  - `<devLogin>_labeled_breaks.csv`: List of the breaks in the format: <len; dates; Tfov_used; label; previously>

#### Algorithm

1. Get a *break* from the `Breaks` list.

2. If there is not any other activity performed by the developer during the break, then label it `INACTIVE` if < 365 days; `GONE` otherwise.

3. If there are other activities in the period:

- Define `sub_breaks_list` as the list of the intervals between such activities (*sub_break*).
- Identify each *sub_break* > *Tfov* from the `sub_breaks_list` and label it based on the defined state diagram (∆t_inactive = ∆t_non-coding = Tfov).

![state diagram](https://dl.dropboxusercontent.com/s/4jluvxonjv1mz9d/New_state_diagram.png?dl=1)
