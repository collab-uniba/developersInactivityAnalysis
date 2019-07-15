import utilities_PyGithub as util
import pandas, csv
#from datetime import datetime, timedelta
import config_PyGithub as cfg

p_names=cfg.p_names
main_path = cfg.super_path

p_names=['jabref','ionic','atom','flutter','linguist','elixir','react','framework']#,'node','rails']

START_FROM = 1 #1 is Jabref, 10 is rails
projects_stats=pandas.DataFrame(columns=['Project','Contributors','Sampled_Contributors','Sleeping','Hibernated','Dead'])

for i in range(START_FROM, len(p_names)+1):### Starts from 1 because of the token
    chosen_project = i-1 # FROM 0 TO n-1
    
    project_name =  p_names[chosen_project]
    
    proj_path = main_path+'/'+project_name
    
    with open(proj_path+'/inactivity_interval_list.csv', 'r') as f:  #opens PW file
        inactivity_intervals_data = [list(map(str,rec)) for rec in csv.reader(f, delimiter=',')]

    active_users_df = pandas.read_csv(proj_path+'/active_users.csv')

    num_main_proj_users = len(inactivity_intervals_data)
    num_active_users = len(active_users_df)
    
    full_sleepings_list = util.getSleepingsList(proj_path)
    full_hibernated_list = util.getHibernationsList(proj_path) # Includes Deads because they have been Hibernated before
    full_dead_list = util.getDeadsList(proj_path)
    util.add(projects_stats, [project_name, num_main_proj_users, num_active_users, len(full_sleepings_list), len(full_hibernated_list), len(full_dead_list)])
    
# Write Final Tables
projects_stats.to_csv(main_path+'/projects_stats.csv', sep=';', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
util.tableCumulativeTransitions(p_names, main_path)
util.tableCumulativeTransitionsPercentages(main_path)
util.tableTransitionsPercentagesProjectList(main_path)
util.reportPlotAllProjectBreaksDistribution(p_names, main_path)
util.tableTransitionsPercentages(main_path)
util.printProjectsDurationsLogTransformed(p_names, main_path)
util.printProjectsDurationsLogScale(p_names, main_path)
util.plotAllProjectInactivities(p_names, main_path)
