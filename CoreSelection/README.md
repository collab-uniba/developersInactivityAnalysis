# Creation of the list of core developers

Core developers are defined as those authoring 80% of a project's code base

## Step 1

Clones a git repo locally and extract commits statistics.

Run `LocalNonDocCommitExtractor.py <repo-url>`
- Input: list of GitHub repository urls
- Output: A80*_results/repo/commits.csv, A80*_results/repo/Cstats.csv
- Example: `python LocalNonDocCommitExtractor.py ../Resources/repositories.txt`

## Step 2
Refer to this [(README | CommitExtractor)](../README.md#L24) file and execute `CommitExtractor.py`.
At the end of the execution proceed with step 3 below

## Step 3

Extract commit author information (id;name;email;login;commits).

Run `LoginIdentifier.py `
- Requires: A80_results/<repo>/Cstats.csv, text file with the list of GitHub repositories to analyze
- Output: A80_results/<repo>/login_map.csv
- Example: `python LoginIdentifier.py`

## Step 4

Find aliases among committers.

Run `UnmaskAliases.py`
- Requires: A80_results/<repo>/login_map.csv,  text file with the list of GitHub repositories to analyze
- Output: A80_results/<repo>/unmasking_results.csv
- Example: `python UnmaskAliases.py`

## Step 5

Obtain the list of core developers.

Run `GetA80Lists.py`
- Requires: A80_results/<repo>/unmasking_results.csv
- Output: A80_devs.csv
- Example: `python GetA80Lists.py`
