# Will you come back to contribute? Investigating the inactivitiy of OSS developers in GitHub
[![DOI](https://zenodo.org/badge/183011533.svg)](https://zenodo.org/badge/latestdoi/183011533)


### CommitExtractor.py

#### Params

- `gitRepoName`: repository name in the form of organization/repository
- `tokenNo`: number of the token to use from the tokens file (`Resources/tokens.txt`) or the token itself

#### Requirements

- Set files and folders names in the `Settings.py` file

#### Execution

`python CommitExtractor.py collab-uniba/developersBreaksAnalysis [1...n]`

or

`python CommitExtractor.py collab-uniba/developersBreaksAnalysis myTokenString`

#### Output

- `logs/Commit_Extraction_organization.log`: log file
- `Organizations/<organization>/[<repo1>...<repoN>]/`: Results folders
- For each repo folder: 
  - `commit_list.csv`: List of the commits in the format: <SHA; author_id; date>
  - `commit_history_table.csv`: Matrix of autors and dates. The cells contain the number of the commits of a developer in one day
  - `pauses_duration_list.csv`: List of pauses durations in days for each developer in the format: <dev; listOfDurations>
  - `pauses_dates_list.csv`: List of pauses dates for each developer in the format: <dev; listOfPauseDates>
- The same files are given after merging the commits of every organization's repo in the `Organizations/<organization>/` folder.

---

### ActivitiesExtractor.py

#### Params

- `gitRepoName`: repository name in the form of organization/repository
- `tokenNo`: number of the token to use from the tokens file (`Resources/tokens.txt`) or the token itself

#### Requirements

- Set files and folders names in the `Settings.py` file

#### Execution

`python ActivitiesExtractor.py collab-uniba/developersBreaksAnalysis [1...n]`

or

`python ActivitiesExtractor.py collab-uniba/developersBreaksAnalysis myTokenString`

#### Output

- `logs/Commit_Extraction_organization.log`: log file
- `Organizations/<organization>/[<repo1>...<repoN>]/Other_Activities/`: Results folders
- For each repo folder:
  - `issues_comments_repo.csv`: List of the issue comments in the format: <id; date; creator_login>
  - `issues_events_repo.csv`: List of the issue events in the format: <id; date; creator_login>
  - `issues_prs_repo.csv`: List of the issue and pull request creations in the format: <id; date; creator_login>
  - `pulls_comments_repo.csv`: List of the pull request comments in the format: <id; date; creator_login>

---

### BreaksIdentification.py

#### Params

None

#### Requirements

- Set files and folders names in the `Settings.py` file
- Insert the list of the TF/core developers (<TF_developers_file>) in the right folder. Formatted as a list of <name;login>. The path to save the file is set in the `Settings.py` file.
- Set the `window` size and the `shift` size in the `Settings.py` file

#### Execution

`python BreaksIdentification.py`

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

None

#### Requirements

- Make sure to have already executed the `BreaksIdentification.py` script to get the `<devLogin>_breaks.csv` files (one for each developer).

#### Execution

`python BreaksLabeling.py`

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
