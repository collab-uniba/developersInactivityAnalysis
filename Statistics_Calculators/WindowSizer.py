### IMPORT EXCEPTION MODULES
from requests.exceptions import Timeout
from github import GithubException

### IMPORT SYSTEM MODULES
from github import Github
import os, sys, logging, pandas, csv, numpy
from datetime import datetime
import datetime as dt

### IMPORT CUSTOM MODULES
sys.path.insert(1, '../')
import Settings as cfg
import Utilities as util

### THIS MODULE HAS BEEN USED FOR CHOISES DURING THE DEVELOPMENT. NOT USED FOR THE PAPER ###

def getDeveloperStats(developer, organization, project, pauses_df, win):
    shift_days = 7

    stats = [developer, organization + '/' + project]

    for index, row in pauses_df.iterrows():
        dev = row['pauses'][0]
        no_pauses = len(row['pauses']) - 3
        if (dev == developer):
            ### Get First Pause Start (FPS) and Last Pause End (LPE) Dates
            FPS = row['dates'][1].split('/')[0]
            FPS_dt = datetime.strptime(FPS, '%Y-%m-%d')
            LPE = row['dates'][-1].split('/')[1]
            LPE_dt = datetime.strptime(LPE, '%Y-%m-%d')

            win_shifts = 0
            larger_pauses = []
            no_not_valid_win = 0
            max_no_pauses = 0
            min_no_pauses = 999999999
            sum_no_pauses = 0 # Needed for avg_no_pauses

            breaks_df = pandas.DataFrame(columns = ['len', 'dates'])

            win_start = FPS_dt
            win_end = FPS_dt + dt.timedelta(days=win)

            while(win_end<LPE_dt):
                win_pauses_list = pandas.DataFrame(columns=['len', 'dates'])
                for interval in row['dates'][1:]:
                    int_start, int_end = interval.split('/')
                    int_start_dt = datetime.strptime(int_start, '%Y-%m-%d')
                    int_end_dt = datetime.strptime(int_end, '%Y-%m-%d')

                    pause_length = util.daysBetween(int_start, int_end)
                    if((pause_length>win) and (interval not in larger_pauses)):
                        larger_pauses.append(interval)

                    if((int_start_dt>=win_start) and (int_end_dt<=win_end)):
                        util.add(win_pauses_list, [pause_length, interval])
                win_pauses = len(win_pauses_list)
                sum_no_pauses += win_pauses
                if(win_pauses<4):
                    no_not_valid_win += 1
                if(win_pauses<min_no_pauses):
                    min_no_pauses = win_pauses
                if(win_pauses>max_no_pauses):
                    max_no_pauses = win_pauses

                if(win_pauses>=4):
                    win_th = util.getFarOutThreshold(win_pauses_list['len'])
                    for i, p in win_pauses_list.iterrows():
                        if((p['len'] > win_th) and (p['dates'] not in breaks_df.dates.tolist())):
                            util.add(breaks_df, row)

                win_start += dt.timedelta(days=shift_days)
                win_end = win_start + dt.timedelta(days=win)
                win_shifts += 1
            try:
                avg_no_pauses = sum_no_pauses / win_shifts
            except ZeroDivisionError:
                print('Zero Division: Window too narrow, it has to be larger than the developer life')
                avg_no_pauses = 0

            no_breaks = len(breaks_df)
            no_larger_pauses = len(larger_pauses)
            stats += [no_pauses, win, no_breaks, win_shifts, no_larger_pauses, avg_no_pauses, min_no_pauses, max_no_pauses, no_not_valid_win]
            print(stats)
            break
    return stats

### MAIN FUNCTION
def main(repos_list):

    workingFolder = cfg.main_folder
    TF_devs_stats = pandas.DataFrame(columns=['dev','repo','no_pauses','win_size','no_breaks','no_shifts','no_larger_pauses','avg_no_pauses','min_no_pauses','max_no_pauses','no_not_valid_win'])
    win_sizes_to_test = [30,90,120,180,365] # sizes are in days

    for gitRepoName in repos_list:
        organization, project = gitRepoName.split('/')

        with open(workingFolder + '/' + organization + '/' + cfg.pauses_list_file_name, 'r') as f:
            pauses_duration_list = [list(map(str, rec)) for rec in csv.reader(f, delimiter=cfg.CSV_separator)]

        with open(workingFolder + '/' + organization + '/' + cfg.pauses_dates_file_name, 'r') as f:
            pauses_dates_list = [list(map(str, rec)) for rec in csv.reader(f, delimiter=cfg.CSV_separator)]

        pauses_df = pandas.DataFrame({'pauses': pauses_duration_list, 'dates': pauses_dates_list})

        TF_devs_df = pandas.read_csv(workingFolder + '/' + organization + '/' + project + '/' + cfg.TF_developers_file, sep=cfg.CSV_separator)

        for dev in TF_devs_df.login.tolist():
            for win_size in win_sizes_to_test:
                dev_stats = getDeveloperStats(dev, organization, project, pauses_df, win_size)
                util.add(TF_devs_stats, dev_stats)

    TF_devs_stats.to_csv(workingFolder + '/TF_devs_windows_stats.csv',
                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
    print("Process Successful Finished")

    print("Computing Averages")
    averages = pandas.DataFrame(columns=['win_size','no_breaks','no_shifts','no_larger_pauses','avg_no_pauses','min_no_pauses','max_no_pauses','no_not_valid_win'])
    for win in win_sizes_to_test:
        data = TF_devs_stats.loc[TF_devs_stats['win_size'] == win]
        avgs = data[3:].mean()
        util.add(averages,avgs)
    averages.to_csv(workingFolder + '/TF_devs_windows_stats_AVG.csv',
                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
    print("Computation DONE!")

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    ### ARGUMENTS MANAGEMENT
    repos_list=util.getReposList()
    main(repos_list)

### THIS MODULE HAS BEEN USED FOR CHOISES DURING THE DEVELOPMENT. NOT USED FOR THE PAPER ###
