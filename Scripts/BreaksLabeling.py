### IMPORT EXCEPTION MODULES
from requests.exceptions import Timeout
from github import GithubException

### IMPORT SYSTEM MODULES
from github import Github
import os, logging, pandas
from datetime import datetime
import datetime as dt

### IMPORT CUSTOM MODULES
import Settings as cfg
import Utilities as util

### DEFINE CONSTANTS
COMPLETE = "COMPLETE"

def get_issues_prs(organizationFolder, developer_login):
    issues_prs_data = pandas.DataFrame(columns=['id', 'date', 'creator_login'])

    for dir in os.listdir(organizationFolder):
        path = organizationFolder + '/' + dir
        if os.path.isdir(path):
            try:
                issues_prs = pandas.read_csv(path + '/Other_Activities/' + cfg.issue_pr_list_file_name, sep=cfg.CSV_separator)
                issues_prs = issues_prs[issues_prs.creator_login == developer_login]
                issues_prs_data = pandas.concat([issues_prs_data, issues_prs], ignore_index=True)
            except:
                logging.info('Unable to get Issues/PRs from {}'.format(path))
                pass
    return issues_prs_data

def get_issues_comments_dev(organizationFolder, developer_login):
    issues_comments_data = pandas.DataFrame(columns=['id', 'date', 'creator_login'])

    for dir in os.listdir(organizationFolder):
        path = organizationFolder + '/' + dir
        if os.path.isdir(path):
            try:
                issues_comments = pandas.read_csv(path + '/Other_Activities/' + cfg.issue_comments_list_file_name, sep=cfg.CSV_separator)
                issues_comments = issues_comments[issues_comments.creator_login == developer_login]
                issues_comments_data = pandas.concat([issues_comments_data, issues_comments], ignore_index=True)
            except:
                logging.info('Unable to get Issue comments from {}'.format(path))
                pass
    return issues_comments_data

def get_pulls_comments_dev(organizationFolder, developer_login):
    pulls_comments_data = pandas.DataFrame(columns=['id', 'date', 'creator_login'])

    for dir in os.listdir(organizationFolder):
        path = organizationFolder + '/' + dir
        if os.path.isdir(path):
            try:
                pulls_comments = pandas.read_csv(path + '/Other_Activities/' + cfg.pulls_comments_list_file_name, sep=cfg.CSV_separator)
                pulls_comments = pulls_comments[pulls_comments.creator_login == developer_login]
                pulls_comments_data = pandas.concat([pulls_comments_data, pulls_comments], ignore_index=True)
            except:
                logging.info('Unable to get Pulls comments from {}'.format(path))
                pass
    return pulls_comments_data

def get_issue_events_dev(organizationFolder, developer_login):
    issue_events_data = pandas.DataFrame(columns=['id', 'date', 'creator_login'])

    for dir in os.listdir(organizationFolder):
        path = organizationFolder + '/' + dir
        if os.path.isdir(path):
            try:
                issue_events = pandas.read_csv(path + '/Other_Activities/' + cfg.issue_events_list_file_name, sep=cfg.CSV_separator)
                issue_events = issue_events[issue_events.creator_login == developer_login]
                issue_events_data = pandas.concat([issue_events_data, issue_events], ignore_index=True)
            except:
                logging.info('Unable to get Issue Events from {}'.format(path))
                pass
    return issue_events_data

def get_action_timeline(action_name, action_table, column_names):
    cur_action_data = [action_name]
    date_action_count = pandas.to_datetime(action_table[['date']].pop('date'), format="%Y-%m-%d").dt.date.value_counts()
    # ITERATE FROM DAY1 --> DAYN (D)
    for d in column_names[1:]:
        # IF U COMMITTED DURING D THEN U[D]=1 ELSE U(D)=0
        try:
            cur_action_data.append(date_action_count[pandas.to_datetime(d).date()])
        except Exception: # add "as name_given_to_exception" before ":" to get info
            cur_action_data.append(0)
    return cur_action_data

def get_activities(organizationFolder, developer_login):
    issues_prs = get_issues_prs(organizationFolder, developer_login)
    issues_comments = get_issues_comments_dev(organizationFolder, developer_login)
    pulls_comments = get_pulls_comments_dev(organizationFolder, developer_login)
    issue_events = get_issue_events_dev(organizationFolder, developer_login)

    commit_history = pandas.read_csv(organizationFolder + '/' + cfg.commit_history_table_file_name, sep=cfg.CSV_separator)

    column_names = ['action'] + commit_history.columns[1:].tolist()

    ### Add Action Timeline to the Table
    actions_data = []
    if len(issues_prs) > 0:
        actions_data.append(get_action_timeline("issues/pull_requests", issues_prs, column_names))
    if len(issues_comments) > 0:
        actions_data.append(get_action_timeline("issues_comments", issues_comments, column_names))
    if len(pulls_comments) > 0:
        actions_data.append(get_action_timeline("pull_requests_comments", pulls_comments, column_names))
    if len(issue_events) > 0:
        actions_data.append(get_action_timeline("issues_events", issue_events, column_names))

    actions_table = pandas.DataFrame(actions_data, columns=column_names)
    actions_table = actions_table.set_index('action')

    dest = organizationFolder + '/' + cfg.actions_folder_name
    os.makedirs(dest, exist_ok=True)
    actions_table.to_csv(organizationFolder + '/'+ cfg.actions_folder_name + '/' + developer_login + '_actions_table.csv',
                         sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
    return actions_table

def splitBreak(break_limits, action_days, th):
    status = 'ACTIVE'  # NCUT: Non coding under threshold.
    previously = status
    period_start = ''

    break_range = break_limits.split('/')
    action_days.insert(0, break_range[0])
    action_days.append(break_range[1])

    period_detail = pandas.DataFrame(columns=['len', 'dates', 'th', 'label', 'previously'])
    for i in range(0, len(action_days) - 1):
        if status == 'ACTIVE':
            previously = status
            size = util.daysBetween(action_days[i], action_days[i + 1])
            if size > th:
                if size > cfg.gone_threshold:
                    status = 'GONE'
                else:
                    status = 'INACTIVE'
                dates = action_days[i] + '/' + action_days[i + 1]
                util.add(period_detail, [size, dates, th, status, previously])
            else:
                status = 'NCUT'
                period_start = action_days[i]
        elif (status == 'INACTIVE') | (status == 'GONE'):
            previously = status
            size = util.daysBetween(action_days[i], action_days[i + 1])
            if size > th:
                status = 'NON_CODING'
                dates = action_days[i] + '/' + action_days[i + 1]
                util.add(period_detail, [size, dates, th, status, previously])
            else:
                status = 'NCUT'
                period_start = action_days[i]
        elif status == 'NON_CODING':
            previously = status
            size = util.daysBetween(action_days[i], action_days[i + 1])
            if size > 2 * th:
                NC_to_G_threshold = th + cfg.gone_threshold
                if size > NC_to_G_threshold:
                    status = 'GONE'
                else:
                    status = 'INACTIVE'
                start = (datetime.strptime(action_days[i], "%Y-%m-%d") + dt.timedelta(days=th)).strftime("%Y-%m-%d")
                dates = start + '/' + action_days[i + 1]
                util.add(period_detail, [size, dates, th, status, previously])
            else:
                break_start = period_detail.at[0, 'dates'].split('/')[0]
                new_end = action_days[i + 1]
                period_detail.at[0, 'len'] = util.daysBetween(break_start, new_end)  # New size
                period_detail.at[0, 'dates'] = break_start + '/' + new_end  # New dates
                # Same th
                # Same status
                # Same previously
        else:  # (status=='NCUT')
            size = util.daysBetween(period_start, action_days[i + 1])
            if size > th:
                status = 'NON_CODING'
                dates = period_start + '/' + action_days[i + 1]
                util.add(period_detail, [size, dates, th, status, previously])
    # A Final status 'INACTIVE', 'GONE' or 'NCUT' means an UNFREEZING ('NCUT' is not written into the detail list)

    last_end = period_detail.at[0, 'dates'].split('/')[1]
    if status == 'NCUT':
        if last_end == cfg.data_collection_date:
            start = period_detail.at[0, 'dates'].split('/')[1]
            size = util.daysBetween(start, last_end)
            util.add(period_detail, [size, start+'/'+last_end, th, 'NOW', 'NON_CODING'])
        else:
            status = previously
            break_start = period_detail.at[0, 'dates'].split('/')[0]
            new_end = action_days[i + 1]
            period_detail.at[0, 'len'] = util.daysBetween(break_start, new_end)  # New size
            period_detail.at[0, 'dates'] = break_start + '/' + new_end  # New dates
            # Same th
            # Same status
            # Same previously
    if last_end == cfg.data_collection_date:
        period_detail.at[0, 'label'] = 'NOW'
    else:
        util.add(period_detail, [0, last_end, 0, 'ACTIVE', status])
    return period_detail

### MAIN FUNCTION
def main(repos_list):
    for gitRepoName in repos_list:
        organization, main_project = gitRepoName.split('/')
        workingFolder = cfg.main_folder + '/' + organization
        actionsFolder = workingFolder + '/' + cfg.actions_folder_name
        breaksFolder = workingFolder + '/' + cfg.breaks_folder_name
        labeledBreaksFolder = workingFolder + '/' + cfg.labeled_breaks_folder_name
        os.makedirs(labeledBreaksFolder, exist_ok=True)

        for file in os.listdir(breaksFolder):
            if os.path.isfile(breaksFolder + '/' + file):
                dev = file.split('_')[0]

                breaks_df = pandas.read_csv(breaksFolder + '/' + file, sep=cfg.CSV_separator)

                devActionsFile = '{}_actions_table.csv'.format(dev)
                if devActionsFile in actionsFolder:
                    user_actions = pandas.read_csv(actionsFolder+'/'+devActionsFile, sep=cfg.CSV_separator)
                else:
                    user_actions = get_activities(workingFolder, dev)

                labeled_breaks = pandas.DataFrame(columns=['len', 'dates', 'th', 'label', 'previously'])
                for i, b in breaks_df.iterrows():
                    # CHECK ACTIVITIES
                    break_duration = b['len']
                    break_dates = b['dates']
                    threshold = b['th']
                    break_range = break_dates.split('/')
                    inner_start = (datetime.strptime(break_range[0], "%Y-%m-%d") + dt.timedelta(days=1)).strftime("%Y-%m-%d")
                    inner_end = (datetime.strptime(break_range[1], "%Y-%m-%d") - dt.timedelta(days=1)).strftime("%Y-%m-%d")

                    brake_actions = user_actions.loc[:, inner_start:inner_end]  # Gets only the chosen period

                    brake_actions = brake_actions.loc[~(brake_actions == 0).all(axis=1)]  # Removes the actions not performed

                    is_activity_day = (brake_actions != 0).any()  # List Of Columns With at least a Non-Zero Value
                    action_days = is_activity_day.index[is_activity_day].tolist()  # List Of Columns NAMES Having Column Names at least a Non-Zero Value

                    if len(brake_actions) > 0:  # There are other activities: the Break is Non-coding
                        break_detail = splitBreak(break_dates, action_days, threshold)
                        labeled_breaks = pandas.concat([labeled_breaks, break_detail], ignore_index=True)
                    else:  # No other activities: the Break is Inactive or Gone
                        if break_duration > cfg.gone_threshold:
                            status = 'GONE'
                            previously = 'ACTIVE'
                            util.add(labeled_breaks, [break_duration, break_dates, threshold, status, previously])
                        else:
                            status = 'INACTIVE'
                            previously = 'ACTIVE'
                            util.add(labeled_breaks, [break_duration, break_dates, threshold, status, previously])

                        break_end = break_dates.split('/')[1]
                        if break_end == cfg.data_collection_date:
                            labeled_breaks.at[0, 'label'] = 'NOW'
                        else:
                            util.add(labeled_breaks, [0, break_end, 0, 'ACTIVE', status])

                labeled_breaks.to_csv(labeledBreaksFolder + '/' + dev + '_labeled_breaks.csv',
                                      sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
        print('{} Breaks Labeling Complete!'.format(gitRepoName))
if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    ### ARGUMENTS MANAGEMENT
    repos_list = util.getReposList()
    main(repos_list)