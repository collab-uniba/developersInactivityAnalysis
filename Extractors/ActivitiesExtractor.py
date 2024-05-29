### IMPORT EXCEPTION MODULES
import logging
import os
import sys
sys.path.append('../')
from datetime import datetime

import pandas
### IMPORT SYSTEM MODULES
from github import Github, GithubException
from requests.exceptions import Timeout

### IMPORT CUSTOM MODULES
import Settings as cfg
import Utilities as util

### DEFINE CONSTANTS
COMPLETE = "COMPLETE"

def getActivityExtractionStatus(folder, statusFile):
    status = "NOT-STARTED"
    if(statusFile in os.listdir(folder)):
        with open(os.path.join(folder, statusFile)) as f:
            content = f.readline().strip()
        status, _ = content.split(';')
    return status

def get_issues_comments_repo(gith, token, outputFolder, repo):  # developers is a previously used param representing the list of core developers
    outputFileName = cfg.issue_comments_list_file_name
    tmpSavefile = '_issues_comments_save_file.log'
    tmpCompletedIssues = "_issues_comments_completed_issues.tmp"
    tmpStatusFile = "_issues_comments_extraction_status.tmp"

    status = getActivityExtractionStatus(outputFolder, tmpStatusFile)
    if(status != COMPLETE):
        exception_thrown = True
        while (exception_thrown):
            exception_thrown = False

            if outputFileName in os.listdir(outputFolder):
                issues_comments_data = pandas.read_csv(os.path.join(outputFolder,outputFileName), sep=cfg.CSV_separator)
            else:
                issues_comments_data = pandas.DataFrame(columns=['id', 'date', 'creator_login'])

            if tmpSavefile in os.listdir(outputFolder):
                last_issues_page, last_issue, last_comments_page = util.getLastActivitiesPageRead(os.path.join(outputFolder, tmpSavefile))
            else:
                last_issues_page = 0
                last_issue = ''
                last_comments_page = 0

            if tmpCompletedIssues in os.listdir(outputFolder):
                completed_issues = pandas.read_csv(os.path.join(outputFolder, tmpCompletedIssues), sep=cfg.CSV_separator)
            else:
                completed_issues = pandas.DataFrame(columns=['id'])

            logging.info("Starting Issue Comments Extraction")

            ### Get Comments on Issue
            try:
                issues_page = last_issues_page
                issue_id = ''
                page = 0

                issues = repo.get_issues(state='all', sort='created_at')
                num_issues = issues.totalCount
                final_issues_page = int(num_issues / cfg.items_per_page)

                for issues_page in range(last_issues_page, final_issues_page + 1):
                    gith, token = util.waitRateLimit(gith, token)
                    current_issues_page = issues.get_page(issues_page)
                    for issue in current_issues_page:
                        gith, token = util.waitRateLimit(gith, token)
                        issue_id = issue.id
                        if (issue_id not in completed_issues.id.tolist()):
                            if (issue_id != last_issue):
                                last_page = 0
                            else:
                                last_page = last_comments_page
                            gith, token = util.waitRateLimit(gith, token)
                            issues_comments = issue.get_comments()
                            num_items = issues_comments.totalCount
                            final_page = int(num_items / cfg.items_per_page)

                            for page in range(last_page, final_page + 1):
                                gith, token = util.waitRateLimit(gith, token)
                                issues_comments_page = issues_comments.get_page(page)
                                for comment in issues_comments_page:
                                    gith, token = util.waitRateLimit(gith, token)
                                    comment_id = comment.id
                                    if (comment_id not in issues_comments_data.id.tolist()):
                                        if (comment.user):
                                            #util.waitRateLimit(gith)
                                            user_login = comment.user.login
                                            #if (user_login in developers):
                                            #    util.waitRateLimit(gith)
                                            #    util.add(issues_comments_data, [comment_id, comment.created_at, user_login])
                                            # Uncomment the lines above and remove the 2 lines below
                                            #util.waitRateLimit(gith)
                                            util.add(issues_comments_data, [comment_id, comment.created_at, user_login])
                            util.add(completed_issues, issue_id)
                if (len(issues_comments_data) > 0):
                    issues_comments_data.to_csv(os.path.join(outputFolder,outputFileName),
                                                sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                    completed_issues.to_csv(os.path.join(outputFolder, tmpCompletedIssues),
                                                sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                with open(os.path.join(outputFolder, tmpStatusFile), "w") as statusSaver:
                    statusSaver.write('COMPLETE;{}'.format(datetime.today().strftime("%Y-%m-%d")))
                logging.info('Issues Comments Extraction Complete')
            except GithubException as ghe:
                logging.warning('Exception Occurred While Getting ISSUES COMMENTS: Github {}'.format(ghe))
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_issues_page:{},last_issue:{},last_comment_page:{}'.format(issues_page, issue_id, page))
                if str(ghe).startswith('500'):  # former == '500 None':
                    logging.warning('PROBLEMS ON ISSUE: {} Excluded From Comments Extraction'.format(issue_id))
                    util.add(completed_issues, issue_id)
                if (len(issues_comments_data) > 0):
                    issues_comments_data.to_csv(os.path.join(outputFolder,outputFileName),
                                                sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                    completed_issues.to_csv(os.path.join(outputFolder, tmpCompletedIssues),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                exception_thrown = True
                pass
            except Timeout:
                logging.warning('Exception Occurred While Getting ISSUES COMMENTS: Timeout')
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_issues_page:{},last_issue:{},last_comment_page:{}'.format(issues_page, issue_id, page))
                if (len(issues_comments_data) > 0):
                    issues_comments_data.to_csv(os.path.join(outputFolder,outputFileName),
                                                sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                    completed_issues.to_csv(os.path.join(outputFolder, tmpCompletedIssues),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                exception_thrown = True
                pass
            except:
                logging.warning('Execution Interrupted While Getting ISSUES COMMENTS')
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_issues_page:{},last_issue:{},last_comment_page:{}'.format(issues_page, issue_id, page))
                if (len(issues_comments_data) > 0):
                    issues_comments_data.to_csv(os.path.join(outputFolder,outputFileName),
                                                sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                    completed_issues.to_csv(os.path.join(outputFolder, tmpCompletedIssues),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                raise
    return gith, token

def get_pulls_comments_repo(gith, token, outputFolder, repo):  # developers is a previously used param representing the list of core developers
    outputFileName = cfg.pulls_comments_list_file_name
    tmpSavefile = '_pulls_comments_save_file.log'
    tmpCompletedPulls = "_pulls_comments_completed_pulls.tmp"
    tmpStatusFile = "_pulls_comments_extraction_status.tmp"

    status = getActivityExtractionStatus(outputFolder, tmpStatusFile)
    if (status != COMPLETE):
        exception_thrown = True
        while (exception_thrown):
            exception_thrown = False

            if outputFileName in os.listdir(outputFolder):
                pulls_comments_data = pandas.read_csv(os.path.join(outputFolder,outputFileName), sep=cfg.CSV_separator)
            else:
                pulls_comments_data = pandas.DataFrame(columns=['id', 'date', 'creator_login'])

            if tmpSavefile in os.listdir(outputFolder):
                last_pulls_page, last_pull, last_comments_page = util.getLastActivitiesPageRead(os.path.join(outputFolder, tmpSavefile))
            else:
                last_pulls_page = 0
                last_pull = ''
                last_comments_page = 0

            if tmpCompletedPulls in os.listdir(outputFolder):
                completed_pulls = pandas.read_csv(os.path.join(outputFolder, tmpCompletedPulls), sep=cfg.CSV_separator)
            else:
                completed_pulls = pandas.DataFrame(columns=['id'])

            ### Get Comments on Pull
            try:
                pulls_page = last_pulls_page
                pull_id = ''
                page = 0

                pulls = repo.get_pulls(state='all', sort='created_at')
                num_pulls = pulls.totalCount
                final_pulls_page = int(num_pulls / cfg.items_per_page)

                for pulls_page in range(last_pulls_page, final_pulls_page + 1):
                    gith, token = util.waitRateLimit(gith, token)
                    current_pulls_page = pulls.get_page(pulls_page)
                    for pull in current_pulls_page:
                        gith, token = util.waitRateLimit(gith, token)
                        pull_id = pull.id
                        if (pull_id not in completed_pulls.id.tolist()):
                            if (pull_id != last_pull):
                                last_page = 0
                            else:
                                last_page = last_comments_page
                            gith, token = util.waitRateLimit(gith, token)
                            pulls_comments = pull.get_comments()
                            num_items = pulls_comments.totalCount
                            final_page = int(num_items / cfg.items_per_page)

                            for page in range(last_page, final_page + 1):
                                gith, token = util.waitRateLimit(gith, token)
                                pulls_comments_page = pulls_comments.get_page(page)
                                for comment in pulls_comments_page:
                                    gith, token = util.waitRateLimit(gith, token)
                                    comment_id = comment.id
                                    if (comment_id not in pulls_comments_data.id.tolist()):
                                        if (comment.user):
                                            #util.waitRateLimit(gith)
                                            user_login = comment.user.login
                                            #if (user_login in developers):
                                            #    util.waitRateLimit(gith)
                                            #    util.add(pulls_comments_data, [comment_id, comment.created_at, user_login])
                                            # Uncomment the lines above and remove the 2 lines below
                                            #util.waitRateLimit(gith)
                                            util.add(pulls_comments_data, [comment_id, comment.created_at, user_login])
                            util.add(completed_pulls, pull_id)
                if (len(pulls_comments_data) > 0):
                    pulls_comments_data.to_csv(os.path.join(outputFolder,outputFileName),
                                               sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                    completed_pulls.to_csv(os.path.join(outputFolder, tmpCompletedPulls),
                                           sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                with open(os.path.join(outputFolder, tmpStatusFile), "w") as statusSaver:
                    statusSaver.write('COMPLETE;{}'.format(datetime.today().strftime("%Y-%m-%d")))
                logging.info('Pulls Comments Extraction Complete')
            except GithubException as ghe:
                logging.warning('Exception Occurred While Getting PULLS COMMENTS: Github {}'.format(ghe))
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_pulls_page:{},last_pull:{},last_comment_page:{}'.format(pulls_page, pull_id, page))
                if str(ghe).startswith('500'):  # former == '500 None':
                    logging.warning('PROBLEMS ON PULL: {} Excluded From Comments Extraction'.format(pull_id))
                    util.add(completed_pulls, pull_id)
                if (len(pulls_comments_data) > 0):
                    pulls_comments_data.to_csv(os.path.join(outputFolder,outputFileName),
                                               sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                    completed_pulls.to_csv(os.path.join(outputFolder, tmpCompletedPulls),
                                           sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                exception_thrown = True
                pass
            except Timeout:
                logging.warning('Exception Occurred While Getting PULLS COMMENTS: Timeout')
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_pulls_page:{},last_pull:{},last_comment_page:{}'.format(pulls_page, pull_id, page))
                if (len(pulls_comments_data) > 0):
                    pulls_comments_data.to_csv(os.path.join(outputFolder,outputFileName),
                                               sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                    completed_pulls.to_csv(os.path.join(outputFolder, tmpCompletedPulls),
                                           sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                exception_thrown = True
                pass
            except:
                logging.warning('Execution Interrupted While Getting PULLS COMMENTS')
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_pulls_page:{},last_pull:{},last_comment_page:{}'.format(pulls_page, pull_id, page))
                if (len(pulls_comments_data) > 0):
                    pulls_comments_data.to_csv(os.path.join(outputFolder,outputFileName),
                                               sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                    completed_pulls.to_csv(os.path.join(outputFolder, tmpCompletedPulls),
                                           sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                raise
    return gith, token


def get_issue_events_repo(gith, token, outputFolder, repo):  # developers is a previously used param representing the list of core developers
    outputFileName = cfg.issue_events_list_file_name
    tmpSavefile = '_issue_events_save_file.log'
    tmpCompletedIssues = "_issue_events_completed_issues.tmp"
    tmpStatusFile = "_issues_events_extraction_status.tmp"

    status = getActivityExtractionStatus(outputFolder, tmpStatusFile)
    if (status != COMPLETE):

        exception_thrown = True
        while (exception_thrown):
            exception_thrown = False

            if outputFileName in os.listdir(outputFolder):
                issues_events_data = pandas.read_csv(os.path.join(outputFolder,outputFileName), sep=cfg.CSV_separator)
            else:
                issues_events_data = pandas.DataFrame(columns=['id', 'date', 'event', 'creator_login'])

            if 'issues_events_extraction.log' in os.listdir(outputFolder):
                last_issues_page, last_issue, last_events_page = util.getLastActivitiesPageRead(os.path.join(outputFolder, tmpSavefile))
            else:
                last_issues_page = 0
                last_issue = ''
                last_events_page = 0

            if tmpCompletedIssues in os.listdir(outputFolder):
                completed_issues = pandas.read_csv(os.path.join(outputFolder, tmpCompletedIssues), sep=cfg.CSV_separator)
            else:
                completed_issues = pandas.DataFrame(columns=['id'])

            ### Get Other Issues Events
            try:
                issues_page = last_issues_page
                issue_id = ''
                page = 0

                issues = repo.get_issues(state='all', sort='created_at')
                num_issues = issues.totalCount
                final_issues_page = int(num_issues / cfg.items_per_page)

                for issues_page in range(last_issues_page, final_issues_page + 1):
                    gith, token = util.waitRateLimit(gith, token)
                    current_issues_page = issues.get_page(issues_page)
                    for issue in current_issues_page:
                        gith, token = util.waitRateLimit(gith, token)
                        issue_id = issue.id
                        if (issue_id not in completed_issues.id.tolist()):
                            if (issue_id != last_issue):
                                last_page = 0
                            else:
                                last_page = last_events_page
                            gith, token = util.waitRateLimit(gith, token)
                            issue_events = issue.get_events()
                            num_items = issue_events.totalCount
                            final_page = int(num_items / cfg.items_per_page)

                            for page in range(last_page, final_page + 1):
                                gith, token = util.waitRateLimit(gith, token)
                                issues_events_page = issue_events.get_page(page)
                                for event in issues_events_page:
                                    gith, token = util.waitRateLimit(gith, token)
                                    event_id = event.id
                                    if (event_id not in issues_events_data.id.tolist()):
                                        event_label = event.event
                                        if event_label != 'mentioned':
                                            if event_label in ['assigned', 'unassigned']:
                                                if event.assigner:
                                                    actor_login = event.assigner.login
                                                    util.add(issues_events_data, [event_id, event.created_at, event_label, actor_login])
                                            else:
                                                if event.actor:
                                                    actor_login = event.actor.login
                                                    util.add(issues_events_data, [event_id, event.created_at, event_label, actor_login])
                            util.add(completed_issues, issue_id)
                if (len(issues_events_data) > 0):
                    issues_events_data.to_csv(os.path.join(outputFolder,outputFileName),
                                                   sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                    completed_issues.to_csv(os.path.join(outputFolder, tmpCompletedIssues),
                                                   sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                with open(os.path.join(outputFolder, tmpStatusFile), "w") as statusSaver:
                    statusSaver.write('COMPLETE;{}'.format(datetime.today().strftime("%Y-%m-%d")))
                logging.info('Issues Events Extraction Complete')

            #        except github.UnknownObjectException:
            #            logging.warning('Exception Occurred While Getting ISSUES EVENTS: UnknownObject (Skipped)')
            #            with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
            #                statusSaver.write('last_issues_page:{},last_issue:{},last_comment_page:{}'.format(issues_page, issue_id, page))
            #            if (len(issues_events_data) > 0):
            #                issues_events_data.to_csv(os.path.join(outputFolder,outputFileName, sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
            #                completed_issues.to_csv(os.path.join(outputFolder, tmpCompletedIssues), sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
            #            exception_thrown=True
            #            pass
            except GithubException as ghe:
                logging.warning('Exception Occurred While Getting ISSUES EVENTS: Github {}'.format(ghe))
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_issues_page:{},last_issue:{},last_comment_page:{}'.format(issues_page, issue_id, page))
                if str(ghe).startswith('500'):  # former == '500 None':
                    logging.warning('PROBLEMS ON ISSUE: {} Excluded From Events Extraction'.format(issue_id))
                    util.add(completed_issues, issue_id)
                if (len(issues_events_data) > 0):
                    issues_events_data.to_csv(os.path.join(outputFolder,outputFileName),
                                              sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                    completed_issues.to_csv(os.path.join(outputFolder, tmpCompletedIssues),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                exception_thrown = True
                pass
            except Timeout:
                logging.warning('Exception Occurred While Getting ISSUES EVENTS: Timeout')
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_issues_page:{},last_issue:{},last_comment_page:{}'.format(issues_page, issue_id, page))
                if (len(issues_events_data) > 0):
                    issues_events_data.to_csv(os.path.join(outputFolder,outputFileName),
                                              sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                    completed_issues.to_csv(os.path.join(outputFolder, tmpCompletedIssues),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                exception_thrown = True
                pass
            except:
                logging.warning('Execution Interrupted While Getting ISSUES EVENTS')
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_issues_page:{},last_issue:{},last_comment_page:{}'.format(issues_page, issue_id, page))
                if (len(issues_events_data) > 0):
                    issues_events_data.to_csv(os.path.join(outputFolder,outputFileName),
                                              sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                    completed_issues.to_csv(os.path.join(outputFolder, tmpCompletedIssues),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                raise
    return gith, token


def get_issues_prs_repo(gith, token, outputFolder, repo):   # developers is a previously used param representing the list of core developers
    outputFileName = cfg.issue_pr_list_file_name
    tmpSavefile = '_issues_prs_save_file.log'
    #tmpCompletedIssues = "_issues_prs_completed_issues.tmp"
    tmpStatusFile = "_issues_prs_extraction_status.tmp"

    status = getActivityExtractionStatus(outputFolder, tmpStatusFile)
    if (status != COMPLETE):
        exception_thrown = True
        while (exception_thrown):
            exception_thrown = False

            ### Get Issue / Pull Requests
            created_issues_prs = repo.get_issues(state='all', sort='created_at')

            last_page_read = 0
            if outputFileName in os.listdir(outputFolder):
                issues_prs_data = pandas.read_csv(os.path.join(outputFolder, outputFileName), sep=cfg.CSV_separator)
                last_page_read = util.getLastPageRead(os.path.join(outputFolder, tmpSavefile))
            else:
                issues_prs_data = pandas.DataFrame(columns=['id', 'date', 'creator_login'])
            try:
                num_items = created_issues_prs.totalCount
                last_page = int(num_items / cfg.items_per_page)

                for page in range(last_page_read, last_page + 1):
                    created_issues_prs_page = created_issues_prs.get_page(page)
                    for issue in created_issues_prs_page:
                        issue_id = issue.id
                        if (issue_id not in issues_prs_data.id.tolist()):
                            if (issue.user):
                                gith, token = util.waitRateLimit(gith, token)
                                util.add(issues_prs_data, [issue_id, issue.created_at, issue.user.login])
                    with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                        statusSaver.write('last_page_read:{}'.format(page))
                if (len(issues_prs_data) > 0):
                    issues_prs_data.to_csv(os.path.join(outputFolder, outputFileName),
                                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                with open(os.path.join(outputFolder, tmpStatusFile), "w") as statusSaver:
                    statusSaver.write('COMPLETE;{}'.format(datetime.today().strftime("%Y-%m-%d")))
                logging.info('Issues/Pulls Extraction Complete')
            except GithubException as ghe:
                logging.warning('Exception Occurred While Getting ISSUES/PULLS: Github {}'.format(ghe))
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_page_read:{}'.format(page))
                issues_prs_data.to_csv(os.path.join(outputFolder,outputFileName),
                                       sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                exception_thrown = True
                pass
            except Timeout:
                logging.warning('Exception Occurred While Getting ISSUES/PULLS: Timeout')
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_page_read:{}'.format(page))
                if (len(issues_prs_data) > 0):
                    issues_prs_data.to_csv(os.path.join(outputFolder,outputFileName),
                                           sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                exception_thrown = True
                pass
            except:
                print('Execution Interrupted While Getting ISSUES/PULLS')
                with open(os.path.join(outputFolder, tmpSavefile), "w") as statusSaver:
                    statusSaver.write('last_page_read:{}'.format(page))
                if (len(issues_prs_data) > 0):
                    issues_prs_data.to_csv(os.path.join(outputFolder,outputFileName),
                                           sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, lineterminator='\n')
                raise
    return gith, token

def get_repo_activities(gith, token, outputFolder, repo):  # developers is a previously used param representing the list of core developers
    logging.info('Starting Issue/PullRequests Extraction')
    get_issues_prs_repo(gith, token, outputFolder, repo)  # developers is a previously used param representing the list of core developers

    logging.info('Starting Issues Comments Extraction')
    get_issues_comments_repo(gith,token, outputFolder, repo)  # developers is a previously used param representing the list of core developers

    logging.info('Starting Pull Comments Extraction')
    get_pulls_comments_repo(gith, token, outputFolder, repo)  # developers is a previously used param representing the list of core developers

    logging.info('Starting Issue Events Extraction')
    get_issue_events_repo(gith, token, outputFolder, repo)  # developers is a previously used param representing the list of core developers

### MAIN FUNCTION
def main(gitRepoName, token):
    ### SET THE PROJECT
    organization, project = gitRepoName.split('/')

    g = Github(token)
    try:
        g.get_rate_limit()
    except Exception as e:
        print('Exception {}'.format(e))
        logging.error(e)
        return
    g.per_page = cfg.items_per_page

    print("Running the Activity Extraction. \n Connection Done. \n Logging in {}".format(logfile))
    logging.info("Activity Extraction Started for {}.".format(organization))

    workingFolder = cfg.main_folder
    tfFolder = cfg.TF_report_folder

    devs_df = pandas.read_csv(os.path.join(tfFolder, project, cfg.TF_developers_file), sep=cfg.CSV_separator) # workingFolder, gitRepoName
    devs = devs_df.login.tolist()

    g, token = util.waitRateLimit(g, token)
    org = g.get_organization(organization)
    org_repos = org.get_repos(type='all')

    try: ### Only for Log (Block)
        num_repos = org_repos.totalCount
    except:
        num_repos = 'Unknown'

    repo_num = 0  ### Only for Log
    for repo in org_repos:
        g, token = util.waitRateLimit(g, token)
        project = repo.name
        repo_num += 1  ### Only for Log

        repo_name = organization+'/'+project

        logging.info('Project {} Started Activities Extraction. {} of {}'.format(repo_name, repo_num, num_repos))

        outputFolder = os.path.join(workingFolder, repo_name, 'Other_Activities')
        os.makedirs(outputFolder, exist_ok=True)

        get_repo_activities(g, token, outputFolder, repo)  # developers is a previously used param representing the list of core developers
        logging.info('Activities Extraction COMPLETE for {} of {} Side Projects'.format(repo_num, num_repos))
    logging.info('Activities Extraction SUCCESSFULLY COMPLETED')

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)
    
    os.makedirs(cfg.logs_folder, exist_ok=True)
    timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d_%H:%M')
    logfile = cfg.logs_folder+f"/Activities_Extraction_{timestamp}.log"
    logging.basicConfig(filename=logfile, level=logging.INFO)

    repoUrls = util.getReposList()
    for repoUrl in repoUrls:
        gitRepoName = repoUrl.replace('https://github.com/', '').strip()
        token = util.getRandomToken()
        logging.info("Starting Activity Extraction for {}".format(gitRepoName))
        main(gitRepoName, token)
    print("Done.")