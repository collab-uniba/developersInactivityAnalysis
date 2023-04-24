# Creation of the list of core developers

Core developers are defined as those authoring 80% of a project's code base

## Step 1

Clones a git repo locally and extract commits statistics.

Run `LocalNonDocCommitExtractor.py <repo-url>`
- Input: repo url
- Output: A80*_results/repo/commits.csv, A80*_results/repo/Cstats.csv

## Step 2

Extract commit author information (id;name;email;login;commits).

Run `LoginIdentifier.py <org/repo> <token / token index>`
- Requires: A80*_results/repo/Cstats.csv 
- Input: organization/repository, valid GitHub API token or index in the token file
- Output: A80*_results/repo/login_map.csv

## Step 3

Find aliases among committers.

Run `UnmaskAliases.py <org/repo>`
- Requires: A80*_results/repo/login_map.csv
- Input organization/repository
- Output: A80*_results/repo/unmasking_results.csv

## Step 4

Obtain the list of core developers.

Run `GetA80Lists.py`
- Requires: A80*_results/repo/unmasking_results.csv
- Output: A80*_devs.csv