import os
import pandas
import Utilities as util
import Settings as cfg
import Scripts.BreaksLabeling as BL
from datetime import datetime
import datetime as dt

def listBreaks(workingFolder, repo):
    organization, project = repo.split('/')
    breaksFolder = os.path.join(workingFolder, organization, cfg.breaks_folder_name)

    repo_Blist = pandas.DataFrame(columns=['dev', 'repo', 'dates', 'len', 'Tfov'])
    for fileName in os.listdir(breaksFolder):
        filePath = os.path.join(breaksFolder, fileName)
        if os.path.isfile(filePath):
            dev = fileName.split('_')[0]
            dev_breaks = pandas.read_csv(filePath, sep=cfg.CSV_separator)
            for i, b in dev_breaks.iterrows():
                util.add(repo_Blist, [dev, repo, b.dates, b.len, b.th])

    return repo_Blist

def listNonCoding(workingFolder, repo):
    organization, project = repo.split('/')
    breaksFolder = os.path.join(workingFolder, organization, cfg.labeled_breaks_folder_name)

    repo_NClist = pandas.DataFrame(columns=['dev', 'repo', 'dates', 'len', 'Tfov', 'label', 'previously'])
    for fileName in os.listdir(breaksFolder):
        filePath = os.path.join(breaksFolder, fileName)
        if os.path.isfile(filePath):
            dev = fileName.split('_')[0]
            dev_breaks = pandas.read_csv(filePath, sep=cfg.CSV_separator)
            for i, b in dev_breaks[dev_breaks.label == cfg.NC].iterrows():
                util.add(repo_NClist, [dev, repo, b.dates, b.len, b.th, b.label, b.previously])

    return repo_NClist

def listInactive(workingFolder, repo):
    organization, project = repo.split('/')
    breaksFolder = os.path.join(workingFolder, organization, cfg.labeled_breaks_folder_name)

    repo_Ilist = pandas.DataFrame(columns=['dev', 'repo', 'dates', 'len', 'Tfov', 'label', 'previously'])
    for fileName in os.listdir(breaksFolder):
        filePath = os.path.join(breaksFolder, fileName)
        if os.path.isfile(filePath):
            dev = fileName.split('_')[0]
            dev_breaks = pandas.read_csv(filePath, sep=cfg.CSV_separator)
            for i, b in dev_breaks[dev_breaks.label == cfg.I].iterrows():
                util.add(repo_Ilist, [dev, repo, b.dates, b.len, b.th, b.label, b.previously])

    return repo_Ilist

def listGone(workingFolder, repo):
    organization, project = repo.split('/')
    breaksFolder = os.path.join(workingFolder, organization, cfg.labeled_breaks_folder_name)

    repo_Glist = pandas.DataFrame(columns=['dev', 'repo', 'dates', 'len', 'Tfov', 'label', 'previously'])
    for fileName in os.listdir(breaksFolder):
        filePath = os.path.join(breaksFolder, fileName)
        if os.path.isfile(filePath):
            dev = fileName.split('_')[0]
            dev_breaks = pandas.read_csv(filePath, sep=cfg.CSV_separator)
            for i, b in dev_breaks[dev_breaks.label == cfg.G].iterrows():
                util.add(repo_Glist, [dev, repo, b.dates, b.len, b.th, b.label, b.previously])

    return repo_Glist

def analyzeLongBreak(repo, dev, targetBreakDates, targetBreakTfov):
    organization, project = repo.split('/')
    workingFolder = os.path.join(cfg.main_folder, organization)
    actionsFolder = os.path.join(workingFolder, cfg.actions_folder_name)

    devActionsFile = '{}_actions_table.csv'.format(dev)
    if devActionsFile in actionsFolder:
        user_actions = pandas.read_csv(actionsFolder + '/' + devActionsFile, sep=cfg.CSV_separator)
    else:
        user_actions = BL.get_activities(workingFolder, dev)

    # CHECK ACTIVITIES
    threshold = targetBreakTfov
    break_range = targetBreakDates.split('/')
    inner_start = (datetime.strptime(break_range[0], "%Y-%m-%d") + dt.timedelta(days=1)).strftime("%Y-%m-%d")
    inner_end = (datetime.strptime(break_range[1], "%Y-%m-%d") - dt.timedelta(days=1)).strftime("%Y-%m-%d")

    break_actions = user_actions.loc[:, inner_start:inner_end]  # Gets only the chosen period

    break_actions = break_actions.loc[~(break_actions == 0).all(axis=1)]  # Removes the actions not performed

    is_activity_day = (break_actions != 0).any()  # List Of Columns With at least a Non-Zero Value
    action_days = is_activity_day.index[is_activity_day].tolist()  # List Of Columns NAMES Having Column Names at least a Non-Zero Value

    if len(break_actions) > 0:  # There are other activities: the Break is Non-coding
        break_detail = BL.splitBreak(targetBreakDates, action_days, threshold)
        print('Break Detail: \n', break_detail)
        #actions_detail = break_actions[action_days[1:-1]]  # splitBreak() has added the commit days, thus I exclude them here
        #print('Break Actions: \n', actions_detail)
    else:
        print('NONE')

### MAIN FUNCTION
def main(repos_list):
    workingDir = os.path.join(cfg.main_folder)
    BreaksList = pandas.DataFrame(columns=['dev', 'repo', 'dates', 'len', 'Tfov'])
    NClist = pandas.DataFrame(columns=['dev', 'repo', 'dates', 'len', 'Tfov', 'label', 'previously'])
    Ilist = pandas.DataFrame(columns=['dev', 'repo', 'dates', 'len', 'Tfov', 'label', 'previously'])
    Glist = pandas.DataFrame(columns=['dev', 'repo', 'dates', 'len', 'Tfov', 'label', 'previously'])

    for repo in repos_list:
        repo_Blist = listBreaks(workingDir, repo)
        BreaksList = pandas.concat([BreaksList, repo_Blist], ignore_index=True)

        repo_NClist = listNonCoding(workingDir, repo)
        NClist = pandas.concat([NClist, repo_NClist], ignore_index=True)

        repo_Ilist = listInactive(workingDir, repo)
        Ilist = pandas.concat([Ilist, repo_Ilist], ignore_index=True)

        repo_Glist = listGone(workingDir, repo)
        Glist = pandas.concat([Glist, repo_Glist], ignore_index=True)

        print(repo, 'DONE!')

    outputFileName = os.path.join(workingDir, 'Breaks_full_list.csv')
    BreaksList.to_csv(outputFileName,
                  sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
    outputFileName = os.path.join(workingDir, 'NC_full_list.csv')
    NClist.to_csv(outputFileName,
                      sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
    outputFileName = os.path.join(workingDir, 'I_full_list.csv')
    Ilist.to_csv(outputFileName,
                      sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
    outputFileName = os.path.join(workingDir, 'G_full_list.csv')
    Glist.to_csv(outputFileName,
                      sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    ### ARGUMENTS MANAGEMENT
    repos_list = util.getReposList()
    analyzeLongBreak('atom/atom', 'jasonrudolph', '2015-02-20/2017-04-04', 46)
    #main(repos_list)