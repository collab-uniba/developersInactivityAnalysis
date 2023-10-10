# How to use files in the Metric folder

### Setup
What you need before starting the productivity analysis for the files in the `Metric` folder is to have the following files from the `reference repository`:
- `commit_list.csv` path: developersInactivityAnalysis/Organizations/owner_name/repository_name/commit_list.csv
- `pauses_dates_list.csv` 
        path: developersInactivityAnalysis/Organizations/owner_name/repository_name/pauses_dates_list.csv
- `TF_devs.csv` path: developersInactivityAnalysis/Organizations/owner_name/repository_name/TF_devs.csv
- `prs_list.csv` path: developersInactivityAnalysis/Organizations/owner_name/repository_name/prs_list.csv
- `G_full_list.csv` path: developersInactivityAnalysis/Organizations/A80API/G_full_list.cvs
- `A80_devs.csv` path: developersInactivityAnalysis/A80_Results/repository_name/A80_devs.csv

### Generator script
if you don’t have these files. cvs then you will have to run the following files:
- run `CommitExtractor.py` to create `commit_list.csv`, 
        script path: developersInactivityAnalysis/Extractors/CommitExtractor.py

- run `c` to create `pauses_dates_list.csv`, script path:

- run `gittruckfacor.jar` to create `TF_devs.csv`, 
        scrip path: developersInactivityAnalysis/TruckFactor/gittruckfactor.jar

- run `get_pull_requests.py` to create `prs_list.csv`, 
        script path: developersInactivityAnalysis/Metric/get_pull_requests.py
- run `ExtremeCasesAnalysis.ipynb` to create `G_full_list.scv`, 
        script path: developersInactivityAnalysis/Statics_Calculators/ExtremeCasesAnalysis.ipynb

- run `GetA80Lists.py` to create `A80_devs.csv`, script path: developersInactivityAnalysis/CoreSelection/GetA80Lists.py

Once you have checked that all the `files have been created`, you can switch to start the files in the `Metric` folder

## Step 1

Create files for LOC metric

- Run: `Main_loc.py <owner_name> <repository_name> <token>`
- Requires: commit_list.csv, pauses_dates_list.csv, TF_devs.csv, G_full_list.csv
- Input: organization name, repository name, valid GitHub API token
- Output: in developersInactivityAnalysis/Organizations/owner_name/repository_name/Metric :
        `LOC_TF.csv`, `LOC_TF_gone.csv`, `LOC_core.csv`, `LOC_core_gone.csv`
- Example: `python3 Main_loc.py collab-uniba developersInactivityAnalysis myPersonalToken`

## Step 2

Create file for PRS metric

- Run: `Main_prs.py <owner_name> <repository_name> <token>`
- Requires: prs_list.scv, LOC_TF.csv, LOC_TF_gone.csv, LOC_core.csv, LOC_core_gone.csv
- Input: organization name, repository name, valid GitHub API token
- Output: in developersInactivityAnalysis/Organizations/owner_name/repository_name/Metric :
        `PRS_TF.csv`, `PRS_TF_gone.csv`, `PRS_core.csv`, `PRS_core_gone.csv`
- Example: `python3 Main_prs.py collab-uniba developersInactivityAnalysis myPersonalToken`

### Step 3

Create file for ISSUE metric

- Run: `Main_issue.py <owner_name> <repository_name> <token>`
- Requires: LOC_TF.csv, LOC_TF_gone.csv, LOC_core.csv, LOC_core_gone.csv
- Input: organization name, repository name, valid GitHub API token
- Output: in developersInactivityAnalysis/Organizations/owner_name/repository_name/Metric :
        `ISSUE_TF.csv`, `ISSUE_TF_gone.csv`, `ISSUE_core.csv`, `ISSUE_core_gone.csv`, `issues_list.csv`
- Example: `python3 Main_issue.py collab-uniba developersInactivityAnalysis myPersonalToken`

### Step 4

Generate for each metric a single file containing all the info of all the repositories

- Run: `CreateRepositoriesMetricfile.py`
- Requires: LOC_TF.csv, LOC_TF_gone.csv, LOC_core.csv, LOC_core_gone.csv,
            ISSUE_TF.csv, ISSUE_TF_gone.csv, ISSUE_core.csv, ISSUE_core_gone.csv
            PRS_TF.csv, PRS_TF_gone.csv, PRS_core.csv, PRS_core_gone.csv

- Output: in developersInactivityAnalysis/Metric :
        `repositories_ISSUE_TF.csv`, `repositories_ISSUE_TF_gone.csv`, `repositories_ISSUE_core.csv`, `repositories_ISSUE_core_gone.csv`, `repositories_PRS_TF.csv`, `repositories_PRS_TF_gone.csv`, `repositories_PRS_core.csv`, `repositories_PRS_core_gone.csv`, `repositories_LOC_TF.csv`, `repositories_LOC_TF_gone.csv`, `repositories_LOC_core.csv`, `repositories_LOC_core_gone.csv`

- Example: `python3 CreateRepositoriesMetricfile.py`