### IMPORT EXCEPTION MODULES
import csv
import os
import sys
sys.path.append('../')  

import numpy
import pandas

### IMPORT CUSTOM MODULES
import Settings as cfg
import Utilities as util

#Read Break Dates Table
#with open(workingFolder + '/' + organization + '/' + project + '/ ' + cfg.pauses_dates_file_name, 'r') as f:
#    pauses_dates_list = [list(map(str,rec)) for rec in csv.reader(f, delimiter=cfg.CSV_separator)]

### THIS MODULE HAS BEEN USED FOR CHOISES DURING THE DEVELOPMENT. NOT USED FOR THE PAPER ###
def getOrganizationStats(organization, project, pauses_duration_list):
    stats = [organization+'/'+project]

    devs_with_pauses = 0
    dev_pauses_avg_acc = 0
    dev_ppy_acc = 0
    dev_avg_pause_len_acc = 0
    dev_var_acc = 0
    for line in pauses_duration_list:
        dev = line[0]
        dev_life = int(line[-2])
        dev_life_years = dev_life/365
        pauses = list(map(int, line[1:-2]))
        dev_pauses = len(line)-3
        if(dev_pauses > 0):
            devs_with_pauses += 1
            dev_pauses_avg_acc += (sum(pauses) / dev_pauses)
            dev_ppy_acc += (dev_pauses/dev_life_years)
            dev_avg_pause_len_acc += numpy.average(pauses)
            dev_var_acc += numpy.var(pauses)
        else:
            print("No pauses")

    avg_num_pauses = dev_pauses_avg_acc/devs_with_pauses
    avg_ppy = dev_ppy_acc/devs_with_pauses
    avg_pause_len = dev_avg_pause_len_acc/devs_with_pauses
    avg_var = dev_var_acc/devs_with_pauses
    stats += [avg_num_pauses,avg_ppy,avg_pause_len,avg_var]
    return stats

def getDeveloperStats(developer, organization, project, pauses_duration_list):
    stats = [developer, organization + '/' + project]

    pauses = 0
    life_days = 0
    pauses_per_year = 0
    avg_pause_len = 0
    pause_len_var = 0
    min_pause_len = 0
    max_pause_len = 999999999
    Q1, Q3 = 0, 0
    IQR = 0
    for line in pauses_duration_list:
        dev = line[0]
        if(dev==developer):
            pauses = len(line) - 3
            pauses_list = list(map(int, line[1:-2]))
            if(pauses > 0):
                life_days = int(line[-2])
                dev_life_years = life_days / 365
                pauses_per_year = pauses/dev_life_years
                avg_pause_len = numpy.mean(pauses_list)
                pause_len_var = numpy.var(pauses_list)
                min_pause_len = min(pauses_list)
                max_pause_len = max(pauses_list)
                Q1, Q3 = numpy.quantile(pauses_list, [.25,.75])
                IQR = Q3-Q1
            else:
                print("No pauses")
                life_days = int(line[-2])
                dev_life_years = life_days / 365
    stats += [pauses, life_days, pauses_per_year, avg_pause_len, pause_len_var, min_pause_len, max_pause_len, Q1, Q3, IQR]
    return stats

### MAIN FUNCTION
def main(repos_list):
    util.unmask_TF_routine()

    workingFolder = cfg.main_folder
    projects_stats = pandas.DataFrame(columns=['repo','avg_num_pauses','avg_pauses_per_year','avg_pause_len','avg_pause_len_var'])
    TF_devs_stats = pandas.DataFrame(columns=['dev','repo','num_pauses','dev_life_days','pauses_per_year','avg_pause_len','pause_len_var','min_pause_len','max_pause_len','Q1','Q3','IQR'])
    for url in repos_list:
        gitRepoName = url.replace('https://github.com/', '')
        organization, project = gitRepoName.split('/')

        # with open(workingFolder + '/' + organization + '/' + project + '/' + cfg.pauses_list_file_name, 'r') as f:
        with open(workingFolder + '/' + organization + '/' + cfg.pauses_list_file_name, 'r') as f:
            pauses_duration_list = [list(map(str, rec)) for rec in csv.reader(f, delimiter=cfg.CSV_separator)]

        main_project_stats = getOrganizationStats(organization, project, pauses_duration_list)
        util.add(projects_stats, main_project_stats)

        TF_devs_df = pandas.read_csv(workingFolder + '/' + organization + '/' + project + '/' + cfg.TF_developers_file, sep=cfg.CSV_separator)

        for dev in TF_devs_df.login.tolist():
            dev_stats = getDeveloperStats(dev, organization, project, pauses_duration_list)
            util.add(TF_devs_stats, dev_stats)

    projects_stats.to_csv(workingFolder + '/projects_pauses_stats.csv',
                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
    TF_devs_stats.to_csv(workingFolder + '/TF_devs_pauses_stats.csv',
                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    ### ARGUMENTS MANAGEMENT
    repos_list=util.getReposList()
    main(repos_list)

### THIS MODULE HAS BEEN USED FOR CHOISES DURING THE DEVELOPMENT. NOT USED FOR THE PAPER ###
