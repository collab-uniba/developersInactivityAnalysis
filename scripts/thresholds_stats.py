import utilities as util
import pandas, csv
import config as cfg

config = cfg.config

p_names=cfg.p_names
p_urls=cfg.p_urls
thresholds=[10,20,30,40,50,60,70,80]
super_path = cfg.super_path

ths_table=pandas.DataFrame(columns=['Project', 'Developers']+[str(th) for th in thresholds])
for i in range(0, len(p_names)):
    chosen_project = i
    project_name =  p_names[chosen_project]
    partial_project_url = p_urls[chosen_project]
    
    if(project_name=='framework'):
        p_row=['laravel']
    else:
        p_row=[project_name]
        
    #Read Breaks Table
    with open(super_path+'/'+project_name+'/inactivity_interval_list.csv', 'r') as f:  #opens PW file
        reader = csv.reader(f)
        inactivity_intervals_data = [list(map(float,rec)) for rec in csv.reader(f, delimiter=',')]
    
    #Read Break Dates Table
    with open(super_path+'/'+project_name+'/break_dates_list.csv', 'r') as f:
        reader = csv.reader(f)
        break_dates_data = [list(map(str,rec)) for rec in csv.reader(f, delimiter=',')]
    
            
    breaks_df = pandas.DataFrame({'durations' : inactivity_intervals_data, 'datelimits' : break_dates_data})
        
    num_all_users = len(inactivity_intervals_data)
    p_row.append(num_all_users)
    
    for t in thresholds:
        SLIDE_WIN_SIZE = t
        
        # FILTER DEVELOPERS
        active_users_df = pandas.DataFrame(columns=['durations','datelimits'])
        
        for index, row in breaks_df.iterrows():
            num_breaks=len(row['durations'])-7
            if ((num_breaks>=SLIDE_WIN_SIZE)):
                util.add(active_users_df, row)
        
        num_active_users = len(active_users_df)
        p_row.append(num_active_users)
    
    util.add(ths_table, p_row)        
ths_table.to_csv(super_path+'/thresholds_cuts.csv', sep=';', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')