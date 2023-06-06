# Truck-Factor

This is a tool for estimating the Truck Factor of GitHub projects, using information from commit history. Truck Factor (also known as Bus Factor or Lottery Number) is the minimal number of developers that have to be hit by a truck (or leave) before a project is incapacitated.

## Environment 

The scripts for extracting commit information from git repositories are implemented using Shell and AWK. So, the execution environment must support those script languages.  Optionally, the Ruby interpreter (To use the library you need to have a version equal to or greater than 2.7.5) is required if you decide to use the Linguist library to automatically discard files like documentation and third-party libraries. See the specific Linguist requirements in [linguist page](https://github.com/github/linguist).

```shell
gem install rugged github-linguist
```

Note:
- On Unix-like systems you might have to execute the command above as root using `sudo`.
- On MacOs you need to install ruby via [Homebrew](https://mac.install.guide/ruby/13.html) rather than using the version of ruby shipped with MacOS


## Usage

1. Execute the scripts to extract information from the git repository to be analyzed:
    1. Extract commit and file information. 
        - command: ```./commit_log_script.sh  <path/to/.../git/repo>```
        - Example: `./commit_log_script.sh ../Local_Repositories/developersInactivityAnalysis`
	
    2. Extract files to be discarded using the Linguist library (Optional)
        - command: ```./linguist_script.sh <path/to/.../git/repo>```
        - Example: `./linguist_script.sh ../Local_Repositories/developersInactivityAnalysis`

2. Execute the gittruckfactor tool.
    - command: ```java –jar gittruckfactor.jar <path/to/.../git/repo> <orgname/reponame>```
    - Example: `java –jar gittruckfactor.jar ../Local_Repositories/developersInactivityAnalysis collab-uniba/developersInactivityAnalysis`
3. Manually create a folder into followings path:  "../TF_Results/reponame", "../Organizations/TF_Results/org/repo" and "../Organization/orgname/reponame" with the following files from gittruckfactor tool output: 
    - TF_report.txt: copy all the output of gittruckfactor.jar
    - TF_devs.csv: for each developer enter <name;login>
    - TF_devs_names.csv: for each developer enter <Developer;Files;Percentage>

## Optional Settings

Repository specifc information can be provided using the files in the folder `repo_info`, which  can improve the TF calculation results. The additional information supported are:

* Filtered files (`filtered-files.txt`): set files that must be discard before start the TF calculation. 
  * Info pattern: `<git_repository_fullname>;<file_path>;<filter_info>`
* Aliases (`alias.txt`): set developers aliases.
  * Info pattern: `<git_repository_fullname>;<developer_alias1>;<developer_alias2>`
* Modules (`modules.txt`): map files to modules. 
  * Info pattern: `<git_repository_fullname>;<file_path>;<module_name>`
  * * Module calculation not implemented yet.

### Run-time settings

Algorithm's variables can be set by modifying the `config.properties `file.


## Reference

GitHub: https://github.com/aserg-ufmg/Truck-Factor

Citation: Guilherme Avelino, Leonardo Passos, Andre Hora, Marco Tulio Valente. [A Novel Approach for Estimating Truck Factors](https://arxiv.org/abs/1604.06766). In 24th International Conference on Program Comprehension (ICPC), pages 1-10, 2016.
