### IMPORT EXCEPTION MODULES

### IMPORT SYSTEM MODULES
import os, pandas, csv
from datetime import datetime
import datetime as dt

### IMPORT CUSTOM MODULES
import Settings as cfg
import Utilities as util
windows_log_df = pandas.DataFrame(columns=['DEV','Q1','Q3','IQR','Tfov','Values'])

def getFarOutThreshold(values, dev): ### If it is satisfying, move the function into UTILITIES
    import numpy
    th = 0
    q_3rd = numpy.percentile(values,75)
    q_1st = numpy.percentile(values,25)
    iqr = q_3rd-q_1st
    if iqr > 1:
        th = q_3rd + 3*iqr
    line = "{};{};{};{};{};{}\n".format(dev, q_1st, q_3rd, iqr, th, values.tolist())
    util.add(windows_log_df, line)
    return th

def addToBreaksList(pauses, currentBreaks, th):
    for i, p in pauses.iterrows():
        if (p['len'] > th) and (p['dates'] not in currentBreaks.dates.tolist()):
            util.add(currentBreaks, [p['len'], p['dates'], th])
    return currentBreaks

def cleanClearBreaks(clearBreaks, breaks):
    for i, b in breaks.iterrows():
        clearBreaks = clearBreaks[clearBreaks.dates != b['dates']] # If it was in the long_breaks list, remove ot from there
    return clearBreaks

def identifyBreaks(pauses_dates_list, developer, window, shift):
    ''' Removes the SURE BREAKS from the windows to calculate Tfov and Excludes IQRs<=1 '''
    breaks_df = pandas.DataFrame(columns=['len', 'dates', 'th'])
    for row in pauses_dates_list:
        dev = row[0]
        if (dev == developer):
            intervals_list = row[1:]
            if(len(intervals_list)>0):
                clear_breaks = pandas.DataFrame(columns=['len', 'dates'])

                ### Get First Pause Start (FPS) and Last Pause End (LPE) Dates
                FPS = row[1].split('/')[0]
                FPS_dt = datetime.strptime(FPS, '%Y-%m-%d')
                LPE = row[-1].split('/')[1]
                LPE_dt = datetime.strptime(LPE, '%Y-%m-%d')

                win_start = FPS_dt
                win_end = FPS_dt + dt.timedelta(days=window)

                last_th = 0
                while (win_end < LPE_dt):
                    win_pauses_list = pandas.DataFrame(columns=['len', 'dates'])
                    partially_included_pauses_list = pandas.DataFrame(columns=['len', 'dates'])
                    for interval in intervals_list:
                        int_start, int_end = interval.split('/')
                        int_start_dt = datetime.strptime(int_start, '%Y-%m-%d')
                        int_end_dt = datetime.strptime(int_end, '%Y-%m-%d')

                        pause_length = util.daysBetween(int_start, int_end)

                        ### Save the pause if within the window
                        if (int_start_dt >= win_start) and (int_end_dt <= win_end):
                            util.add(win_pauses_list, [pause_length, interval])

                        ### Save the pause if it starts inside or finishes inside
                        if ((int_start_dt <= win_end) and (int_end_dt > win_end)) or ((int_end_dt >= win_start) and (int_start_dt < win_start)):
                            util.add(partially_included_pauses_list, [pause_length, interval])

                    win_pauses = len(win_pauses_list)
                    pauses = pandas.concat([win_pauses_list, partially_included_pauses_list], ignore_index=True)
                    if win_pauses >= 4:
                        win_th = getFarOutThreshold(win_pauses_list['len'], dev) ### If it is satisfying, move the function into UTILITIES
                        if win_th > 0:
                            breaks_df = addToBreaksList(pauses, breaks_df, win_th)
                        else:
                            if last_th > 0:
                                breaks_df = addToBreaksList(pauses, breaks_df, last_th)
                    else:
                        if last_th > 0:
                            breaks_df = addToBreaksList(pauses, breaks_df, last_th)

                        line = '{};{};{};{};{};{}'.format(dev,'N/A','N/A','N/A',last_th,win_pauses_list.len.tolist()) ### REMOVE, Not contributing to the algoryhtm
                        util.add(windows_log_df, line) ### REMOVE, Not contributing to the algoryhtm

                        clear_breaks = cleanClearBreaks(clear_breaks, breaks_df)
                        for i, p in pauses.iterrows():
                            if (p['len'] >= window) and (p['dates'] not in clear_breaks.dates.tolist()) and (p['dates'] not in breaks_df.dates.tolist()):
                                util.add(clear_breaks, p)

                    win_start += dt.timedelta(days=shift)
                    win_end = win_start + dt.timedelta(days=window)

                if len(clear_breaks)>0:
                    mean_th = breaks_df.th.mean()
                    try:
                        avg_th = int(round(mean_th, 0))
                    except:
                        print("ERROR while calculating the AVG Tfov. Setting to 7")
                        avg_th = 7
                    for i, p in clear_breaks.iterrows():
                        print('adding remaining clear breaks from the list')
                        if(p['dates'] not in breaks_df.dates.tolist()):
                            util.add(breaks_df, [p['len'], p['dates'], avg_th])
                print(developer, ' Done')
            else:
                print(developer, ' Has NO Pauses')
    return breaks_df

### MAIN FUNCTION
def main(repos_list):
    workingFolder = cfg.main_folder

    for gitRepoName in repos_list:
        organization, project = gitRepoName.split('/')

        devs_df = pandas.read_csv(os.path.join(workingFolder,cfg.TF_report_folder,organization,project,cfg.TF_developers_file), sep=cfg.CSV_separator)

        win = cfg.sliding_window_size
        shift = cfg.shift

        for dev in devs_df.login.tolist():
            print(dev, ' Checking')
            with open(workingFolder + '/' + organization + '/' + cfg.pauses_dates_file_name, 'r') as f:
                pauses_dates_list = [list(map(str, rec)) for rec in csv.reader(f, delimiter=cfg.CSV_separator)]

            breaks_df = identifyBreaks(pauses_dates_list, dev, win, shift)

            output_folder = workingFolder + '/' + organization + '/' + cfg.breaks_folder_name#/IQRcut'
            os.makedirs(output_folder, exist_ok=True)

            breaks_df.to_csv(output_folder + '/' + dev + '_breaks.csv',
                             sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
            windows_log_df.to_csv(cfg.logs_folder + '/Windows_Tfov_logs.csv',
                             sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    ### ARGUMENTS MANAGEMENT
    repos_list=util.getReposList()
    main(repos_list)