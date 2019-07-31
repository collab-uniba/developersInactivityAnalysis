import pandas, csv
import config_Organization as cfg
import utilities_Organization as util

def getNumCoreDevelopers(inactivity_intervals_data, threshold):
    
    # FILTER DEVELOPERS
    SLIDE_WIN_SIZE = threshold
    
    num_active_users=0
    for row in inactivity_intervals_data:
        num_breaks=len(row)-3
        if (('[bot]' not in row[0]) & (num_breaks>=SLIDE_WIN_SIZE)):
            num_active_users += 1
    return num_active_users


p_names = cfg.p_names
organizations = cfg.organizations

main_path = cfg.super_path

p_names = ['jabref','ionic','flutter','atom','linguist','elixir','framework','rails']
organizations = ['JabRef','ionic-team','flutter','atom','github','elixir-lang','laravel','rails']

START_FROM = 1 #1 is Jabref, 10 is rails

table=pandas.DataFrame(columns=['Project','total_devs','10','20','30','40','50','60','70','80'])
for i in range(START_FROM, len(p_names)+1):### Starts from 1 because of the token
    chosen_project = i-1 # FROM 0 TO n-1
    
    chosen_organization = organizations[chosen_project]
    main_project_name =  p_names[chosen_project]
    
    path = main_path+'/'+chosen_organization+'/'+main_project_name
    
    with open(path+'/inactivity_interval_list.csv', 'r') as f:  #opens PW file
        inactivity_intervals_data = [list(map(str,rec)) for rec in csv.reader(f, delimiter=',')]
        
    all_devs=len(inactivity_intervals_data)
    
    row = [main_project_name, all_devs]
    for threshold in range(10, 90, 10):
        num=getNumCoreDevelopers(inactivity_intervals_data, threshold)
        row.append(num)
        
    util.add(table, row)
    
table.to_csv(main_path+'/breaks_number_filter_stats.csv', sep=';', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
