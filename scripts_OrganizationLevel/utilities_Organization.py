import config_Organization as cfg
super_path = cfg.super_path


def get_last_page_read_short(log_file):
    log_handler = open (log_file,'r')
    log_lines_list = log_handler.readlines()
    log_handler.close()
    if(len(log_lines_list)>0):
        last_line=log_lines_list[-1]
        lp=int(last_line.split(':')[-1])
    else:
        lp=0
    return lp

def existsFileStartingWith(directory, string): # checks if in the 'directory' exists a file staring with 'string'
    import os
    
    file_list = os.listdir(directory)
    for name in file_list:
        if name.startswith(string):
            return name
    return False

def getLife(dev, breaks_list): #gets the life in days of a developer in the project
    for b in breaks_list:
        d_id=b[0]
        if d_id==dev:
            return int(b[-2]), (len(b)-3)
    return -1, -1

def getLastCommitDay(commit_table, user_id): #gets the last day when a developer committed
    user_row=commit_table.loc[commit_table['user_id'] == user_id]
    is_commit_day = (user_row != 0).any() #List Of Columns With at least a Non-Zero Value
    commit_days = is_commit_day.index[is_commit_day].tolist() #List Of Columns NAMES Having Column Names at least a Non-Zero Value
                    
    date=commit_days[-1]
    return date

def days_between(d1, d2): # gets the number of days between two dates
    from datetime import datetime
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    d2 = datetime.strptime(d2, "%Y-%m-%d")
    return abs((d2 - d1).days)

# ITERATE FROM MIN_TIMESTAMP --> MAX_TIMESTAMP
        # OBTAIN A LIST OF STRINGS: [USER_ID, DAY1, DAY2, ..., DAYN]
def daterange(start_date, end_date):
    from datetime import datetime
    from datetime import timedelta #, date
    
    if type(start_date)==str:
        start_date=datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
    if type(end_date)==str:
        end_date=datetime.strptime(end_date, '%Y-%m-%d %H:%M:%S')

    for n in range(int ((end_date - start_date).days+2)):
        yield start_date + timedelta(n)
        
def add(dataframe, row): #adds a row to a dataframe
    dataframe.loc[-1] = row  # adding a row
    dataframe.index = dataframe.index + 1  # shifting index
    dataframe.sort_index(inplace=True)

def getBreaksNumberThreshold(inactivityData):
    import numpy
    avgList=[]
    for index, row in inactivityData.iterrows():
        avgList.append(len(row['durations'])-3)#remove ID and 6 statistics
    th = numpy.percentile(avgList,90)
    return th

def writeUsersCSV_byItem(dataframe, path):
    import os
    os.makedirs(path, exist_ok=True) 
    for item in dataframe:
        username = item[0]
        item[1].to_csv(path+"/"+username+'.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
        print(username+" CSV Written")

def reportPlotAllProjectBreaksDistribution(o_names, p_names, path):
    import matplotlib.pyplot as plt
    import numpy, csv, pandas
    
    breaks_stats=pandas.DataFrame(columns=['project','mean','st_dev','var','median','breaks_devlife_corr'])
    projects_counts=[]
    for i in range(0, len(o_names)):
        chosen_project = i # FROM 0 TO n-1
        
        project_name =  o_names[chosen_project]
        main_project = p_names[chosen_project]
        breaks_lifetime = pandas.DataFrame(columns=['BpY','life'])

        #Read Breaks Table
        with open(path+'/'+project_name+'/'+main_project+'/inactivity_interval_list.csv', 'r') as f:  #opens PW file
            breaks_list = [list(map(str,rec)) for rec in csv.reader(f, delimiter=',')]
        
        counts_perYear=[]
        for row in breaks_list:
            num_breaks = len(row[1:])-2   
            if num_breaks>0:
                num_days = int(row[-2])
                years=num_days / 365
                BpY=num_breaks/years
                counts_perYear.append(BpY)
                add(breaks_lifetime, [BpY, num_days])
        projects_counts.append(counts_perYear)
        add(breaks_stats, [project_name,
                           numpy.mean(counts_perYear), 
                           numpy.std(counts_perYear), 
                           numpy.var(counts_perYear),
                           numpy.median(counts_perYear),
                           numpy.corrcoef(breaks_lifetime['BpY'], breaks_lifetime['life'])[1][0]])
    
    breaks_stats.to_csv(path+'/breaks_stats_all.csv', sep=';', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
    
    labels=[]
    for name in p_names:
        if name=='framework':
            labels.append('laravel')
        else:
            labels.append(name)
    
    plt.clf()
    projects_counts.reverse()
    plt.boxplot(projects_counts)
    labels.reverse()
    plt.xticks(numpy.arange(1,len(p_names)+1), labels, rotation=20)
    # Pad margins so that markers don't get clipped by the axes: plt.margins(0.2)
    # Tweak spacing to prevent clipping of tick-label: plt.subplots_adjust(bottom=0.15)
    plt.grid(False)
    plt.ylabel("Pauses per Year")
    plt.savefig(path+"/BreaksDistribution", dpi=600)
    plt.clf()

def getFarOutThreshold(values):
    import numpy
    q_3rd = numpy.percentile(values,75) 
    q_1st = numpy.percentile(values,25) 
    iqr = q_3rd-q_1st
    th = q_3rd + 3*iqr
    return th

def refineSleepingPeriod(break_duration, break_limits, action_days, th):
    from datetime import timedelta, datetime

    d_th=cfg.dead_threshold
    period_detail=[[break_duration, break_limits]]

    status='n' # n: Null - h: hibernation - sot: sleeping - ut: sleeping under threshold.
    period_start=''
    
    break_range=break_limits.split('/')
    action_days.insert(0, break_range[0])
    action_days.append(break_range[1])
    
#    if(break_limits=='2015-09-10/2015-12-12'):
#        print(break_limits+" THRESHOLD IS "+str(th))
#    if(break_limits=='2017-11-02/2018-01-28'):
#        print(break_limits+" THRESHOLD IS "+str(th))
    
    for i in range(0, len(action_days)-1):
        if(status=='n'):
            size = days_between(action_days[i], action_days[i+1])
            if(size>th):
                if(size>d_th):
                    status='d'
                else:
                    status='h'
                period_detail.append([status, size, action_days[i]+'/'+action_days[i+1]])
            else:
                status='sut'
                period_start = action_days[i]
        elif((status=='h') | (status=='d')):
            size = days_between(action_days[i], action_days[i+1])
            if(size>th):
                status='sot'
                period_detail.append([status, size, action_days[i]+'/'+action_days[i+1]])
            else:
                status='sut'
                period_start = action_days[i]
        elif(status=='sot'):
            size = days_between(action_days[i], action_days[i+1])
            if(size>2*th):
                if(size>d_th):
                    status='d'
                else:
                    status='h'
                start=(datetime.strptime(action_days[i], "%Y-%m-%d")+timedelta(days=th)).strftime("%Y-%m-%d")
                period_detail.append([status, size, start+'/'+action_days[i+1]])   
            else:
                status='sot'
                last_sot=period_detail.pop()
                sleeping_start=last_sot[-1].split('/')[0]
                sleeping_duration=days_between(sleeping_start, action_days[i+1])
                period_detail.append([status, sleeping_duration, sleeping_start+'/'+action_days[i+1]])    
        else: #(status=='sut')
            size = days_between(period_start, action_days[i+1])
            if(size>th):
                status='sot'
                period_detail.append([status, size, period_start+'/'+action_days[i+1]])
    # A Final status 'h', 'd' or 'sut' means an UNFREEZING ('sut' is not written into the detail list)
    return period_detail

def getHibernationsList(path): # How many developers Hibernated at least once
    import os#, csv
    
    hibernated_dir=path+'/Hibernated&Unfrozen_Users'
    hibernated_file_list = [name for name in os.listdir(hibernated_dir) if name.endswith('.csv')]
    dead_dir=path+'/Dead&Resurrected_Users'
    dead_file_list = [name for name in os.listdir(dead_dir) if ((name.endswith('.csv')) & (name not in hibernated_file_list))]
    
    id_list=[uid.split('.')[0] for uid in hibernated_file_list]
    id_list+=[uid.split('.')[0] for uid in dead_file_list]
    
    return id_list

def getDeadsList(path): # How many developers Hibernated at least once
    import os#, csv
    
    dead_dir=path+'/Dead&Resurrected_Users'
    dead_file_list = [name for name in os.listdir(dead_dir) if (name.endswith('.csv'))]

    id_list=[uid.split('.')[0] for uid in dead_file_list]
    
    return id_list

def getSleepingsList(path): # How many developers Slept at least once
    import os

    sleeping_dir=path+'/Sleeping&Awaken_Users'
    sleeping_file_list = [name for name in os.listdir(sleeping_dir) if (name.endswith('.csv'))]

    id_list=[uid.split('.')[0] for uid in sleeping_file_list]
    
    return id_list

def countDevTransitions(path, breaks_list):
    import os, csv, pandas
    
    sleeping_devs=getSleepingsList(path)
    hibernated_devs=getHibernationsList(path)
    
    analyzed_devs = list(set(sleeping_devs).union(hibernated_devs)) #for more than 2 lists is list(set().union(l1,l2,l3))
    
    labels = ['dev','breaks','A_to_S','S_to_A','A_to_H','H_to_A','S_to_H','H_to_S','H_to_D','D_to_A','D_to_S']
    transitions_df = pandas.DataFrame(columns=labels)
    
    sleeping_dir=path+'/Sleeping&Awaken_Users/Details'
    hibernated_dir=path+'/Hibernated&Unfrozen_Users'
    dead_dir=path+'/Dead&Resurrected_Users'
    
    for dev in analyzed_devs:
        
        plot_path = path+'/DevStats_Plots'
        os.makedirs(plot_path, exist_ok=True) 
        
        AtoS_count=0
        AtoH_count=0
        StoA_count=0
        StoH_count=0
        HtoA_count=0
        HtoS_count=0
        HtoD_count=0
        DtoA_count=0
        DtoS_count=0        
        
        name = dev+'.csv'
        #Check in Sleeping Directory
        Hfound=[]
        Dfound=[]
        if name in os.listdir(sleeping_dir):
            with open(sleeping_dir+'/'+name, 'r') as f:  #opens PW file
                breaks = [list(map(str,rec)) for rec in csv.reader(f, delimiter=',')]
                for b in breaks:
                    detail_size=len(b[1:])
                    if(detail_size>1):
                        prev_status='u'
                        for i in range(1, detail_size): 
                            status = b[i].replace('[','').split(',')[0].replace('\'','')
                            next_status = b[i+1].replace('[','').split(',')[0].replace('\'','')
                            if (status=='sot') & (next_status=='h'):
                                if(prev_status=='u'):
                                    AtoS_count += 1 
                                    StoH_count += 1
                                else:
                                    StoH_count += 1
                                Hfound.append(b[i+1].replace(']','').split(',')[2].replace('\'','').strip())#Adds Hibernation to a list to check after for hubernation counts
                            elif (status=='h') & (next_status=='sot'):
                                if(prev_status=='u'):
                                    AtoH_count += 1
                                    HtoS_count += 1
                                else:
                                    HtoS_count += 1
                                Hfound.append(b[i].replace(']','').split(',')[2].replace('\'',''))#Adds Hibernation to a list to check after for hubernation counts
                            elif (status=='sot') & (next_status=='d'):
                                if(prev_status=='u'):
                                    AtoS_count += 1 
                                    StoH_count += 1
                                    HtoD_count += 1
                                else:
                                    StoH_count += 1
                                    HtoD_count += 1
                                Dfound.append(b[i+1].replace(']','').split(',')[2].replace('\'',''))#Adds Dead to a list to check after for dead counts
                            elif (status=='d') & (next_status=='sot'):
                                if(prev_status=='u'):
                                    AtoH_count += 1
                                    HtoD_count += 1
                                    DtoS_count += 1
                                else:
                                    DtoS_count += 1
                                Dfound.append(b[i].replace(']','').split(',')[2].replace('\'',''))#Adds Dead to a list to check after for dead counts
                            prev_status = status
                            if b[i+1].replace('[','').split(',')[2].replace('\'','').split('/')[1]==cfg.collection_date:
                                print("Broken Here ".join(b))
                                break;
                    else:
                        status = b[1].replace('[','').split(',')[0].replace('\'','')
                        if((status=='sot') & (b[1].replace('[','').split(',')[2].replace('\'','').split('/')[1]!=cfg.collection_date)):
                            AtoS_count += 1 
                            StoA_count += 1
                        elif (b[1].replace('[','').split(',')[2].replace('\'','').split('/')[1]==cfg.collection_date):              
                            print("Single Last Status ".join(b))

        #Check in Hibernated Directory
        if name in os.listdir(hibernated_dir):
            with open(hibernated_dir+'/'+name, 'r') as f:  #opens PW file
                breaks = [list(map(str,rec)) for rec in csv.reader(f, delimiter=',')]
                for b in breaks[1:]:
                    if(b[1] not in Hfound):
                        end_date = b[1].split('/')[1]
                        if end_date!=cfg.collection_date:
                            AtoH_count += 1
                            HtoA_count += 1
                        else:
                            AtoH_count += 1
                            print("Ongoing Hibernation ".join(b))
                    else:
                        print("Hibernation Already Counted ".join(b))
        
        #Check in Dead Directory
        if name in os.listdir(dead_dir):
            with open(dead_dir+'/'+name, 'r') as f:  #opens PW file
                breaks = [list(map(str,rec)) for rec in csv.reader(f, delimiter=',')]
                for b in breaks[1:]:
                    if(b[1] not in Hfound):
                        end_date = b[1].split('/')[1]
                        if end_date!=cfg.collection_date:
                            AtoH_count += len(breaks)-1
                            HtoD_count += len(breaks)-1
                            DtoA_count += len(breaks)-1
                        else:
                            AtoH_count += len(breaks)-1
                            HtoD_count += len(breaks)-1
                            print("Ongoing Dead or Already Counted".join(b))
                    else:
                        print("Dead Already Counted ".join(b))
        life, num_breaks = getLife(dev, breaks_list)
        factor=life/365
        current_dev_stats=[dev, num_breaks/factor, AtoS_count/factor, StoA_count/factor, AtoH_count/factor, HtoA_count/factor, StoH_count/factor, HtoS_count/factor, HtoD_count/factor, DtoA_count/factor, DtoS_count/factor]
        
        add(transitions_df, current_dev_stats)              
    
    transitions_df.to_csv(path+'/transitions.csv', sep=';', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
    
    return transitions_df

def reportDevsBreaksLengthDistribution(path):
    import os, csv, pandas
    
    sleeping_devs=getSleepingsList(path)
    hibernated_devs=getHibernationsList(path)
    
    analyzed_devs = list(set(sleeping_devs).union(hibernated_devs)) #for more than 2 lists is list(set().union(l1,l2,l3))
    
    labels=['dev','sleepings','hibernatings','deads']
    durations_df = pandas.DataFrame(columns=labels)
    
    sleeping_dir=path+'/Sleeping&Awaken_Users'
    hibernated_dir=path+'/Hibernated&Unfrozen_Users'
    dead_dir=path+'/Dead&Resurrected_Users'
    
    for dev in analyzed_devs:
        plot_path = path+'/DevStats_Plots'
        os.makedirs(plot_path, exist_ok=True) 
        
        ##TRASFORMARE QUESTI IN ARRAY E APPENDERE LE DURATE
        sleepings_durations=[]
        hibernations_durations=[]
        dead_durations=[]
        
        name = dev+'.csv'
        #Check in Sleeping Directory
        if name in os.listdir(sleeping_dir):
            with open(sleeping_dir+'/'+name, 'r') as f:  #opens PW file
                breaks = [list(map(str,rec)) for rec in csv.reader(f, delimiter=',')]
                for b in breaks[1:]:
                    sleepings_durations.append(int(float(b[0]))) 

        #Check in Hibernation Directory
        if name in os.listdir(hibernated_dir):
            with open(hibernated_dir+'/'+name, 'r') as f:  #opens PW file
                breaks = [list(map(str,rec)) for rec in csv.reader(f, delimiter=',')]
                for b in breaks[1:]:
                    hibernations_durations.append(int(float(b[0]))) 
        
        #Check in Dead Directory
        if name in os.listdir(dead_dir):
            with open(dead_dir+'/'+name, 'r') as f:  #opens PW file
                breaks = [list(map(str,rec)) for rec in csv.reader(f, delimiter=',')]
                for b in breaks[1:]:
                    dead_durations.append(int(float(b[0]))) 
        
        current_dev_stats=[dev, sleepings_durations, hibernations_durations, dead_durations]
        
        add(durations_df, current_dev_stats)              
    
    durations_df.to_csv(path+'/statuses_durations.csv', sep=';', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
    
    return durations_df

def getSleepingsFromSleepingDetail(period_detail):
    import pandas
    others_deads_df = pandas.DataFrame(columns=['durations', 'datelimits'])
    for b in period_detail[1:]:
        if b[0]=='sot':
            add(others_deads_df, [float(b[1]), b[2]])
    return others_deads_df

def getHibernationsFromSleepingDetail(period_detail):
    import pandas
    others_hibernations_df = pandas.DataFrame(columns=['durations', 'datelimits'])
    for b in period_detail[1:]:
        if b[0]=='h':
            add(others_hibernations_df, [float(b[1]), b[2]])
    return others_hibernations_df

def getDeadsFromSleepingDetail(period_detail):
    import pandas
    others_deads_df = pandas.DataFrame(columns=['durations', 'datelimits'])
    for b in period_detail[1:]:
        if b[0]=='d':
            add(others_deads_df, [float(b[1]), b[2]])
    return others_deads_df

def makeMeanDiffTests(o_names, path):
    import numpy, pandas, scipy
    
    t_stats_df = pandas.DataFrame(columns=['organization','N_s','N_h','N_common', 't', 'p(t)','tp','p(tp)','u','p(u)','w','p(w)','h','p(h)'])
    
    for i in range(0, len(o_names)):
        chosen_project = i # FROM 0 TO n-1
            
        project_name =  o_names[chosen_project]
        sleep_means_df = pandas.DataFrame(columns=['id','mean'])
        hiber_means_df = pandas.DataFrame(columns=['id','mean'])
            
        current_project_df = pandas.read_csv(path+'/'+project_name+'/statuses_durations.csv', sep=';')
            
        for index, line in current_project_df.iterrows():
            ls = line['sleepings']    
            if ls!='[]':
                    ls=list(map(int,ls.replace('[','').replace(']','').split(',')))
                    sleeping_avg=numpy.mean(ls)
                    add(sleep_means_df, [line['dev'],sleeping_avg])
            lh = line['hibernatings']
            if lh!='[]':
                lh=list(map(int,lh.replace('[','').replace(']','').split(',')))
                hibernation_avg=numpy.mean(lh)
                add(hiber_means_df, [line['dev'],hibernation_avg])
                
        s_avg_list = sleep_means_df['mean'].tolist()
        h_avg_list = hiber_means_df['mean'].tolist()
        paired_df = pandas.merge(sleep_means_df, hiber_means_df, how='inner', on=['id'])
        s_paired_avg_list = paired_df['mean_x'].tolist()
        h_paired_avg_list = paired_df['mean_y'].tolist()
            
        t_val, t_p = scipy.stats.ttest_ind(s_avg_list, h_avg_list)
        t_paired_val, t_paired_p = scipy.stats.ttest_rel(s_paired_avg_list, h_paired_avg_list)
        u_val, u_p = scipy.stats.mannwhitneyu(s_avg_list, h_avg_list)
        w_val, w_p = scipy.stats.wilcoxon(s_paired_avg_list, h_paired_avg_list)
        h_val, h_p = scipy.stats.kruskal(s_avg_list, h_avg_list)
        #f_val, f_p = scipy.stats.friedmanchisquare(s_avg_list, h_avg_list)
        add(t_stats_df, [project_name, len(s_avg_list), len(h_avg_list), len(paired_df), t_val, t_p, t_paired_val, t_paired_p, u_val, u_p, w_val, w_p, k_val, k_p])
    
    t_stats_df.to_csv(path+'/t_stats.csv', sep=';', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')


def printProjectsDurationsLogScale(o_names, path):
        import numpy, pandas, scipy
        import seaborn as sns
        
        data = pandas.DataFrame(columns=['project', 'status', 'average_duration'])
        for i in range(0, len(o_names)):
            chosen_project = i # FROM 0 TO n-1
            
            project_name =  o_names[chosen_project]
            s_avg_list=[]
            h_avg_list=[]
            current_project_df = pandas.read_csv(path+'/'+project_name+'/statuses_durations.csv', sep=';')
            
            for l in current_project_df['sleepings'].tolist():
                if l!='[]':
                    l=list(map(int,l.replace('[','').replace(']','').split(',')))
                    sleeping_avg=numpy.mean(l)
                    s_avg_list.append(sleeping_avg)
                    add(sleep_means_df, [])
                    if(project_name=='framework'):
                        add(data, ['laravel', 'non-coding', sleeping_avg])
                    else:
                        add(data, [project_name, 'non-coding', sleeping_avg])
            for l in current_project_df['hibernatings'].tolist():
                if l!='[]':
                    l=list(map(int,l.replace('[','').replace(']','').split(',')))
                    hibernation_avg=numpy.mean(l)
                    h_avg_list.append(hibernation_avg)
                    if(project_name=='framework'):
                        add(data, ['laravel', 'inactive', hibernation_avg])
                    else:
                        add(data, [project_name, 'inactive', hibernation_avg])
            
        print('S: '+str(min(s_avg_list))+' - '+str(max(s_avg_list))+' Avg: '+str(numpy.mean(s_avg_list)))
        print('H: '+str(min(h_avg_list))+' - '+str(max(h_avg_list))+' Avg: '+str(numpy.mean(h_avg_list)))
        
        t_stats_df.to_csv(path+'/t_stats.csv', sep=';', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')

        pal=[sns.color_palette('Set1')[5],sns.color_palette('Set1')[8],sns.color_palette('Set1')[0]]
        sns_plot = sns.boxplot(x='project', y='average_duration', hue="status", hue_order=['non-coding','inactive'], data=data, palette=pal)
        sns_plot.set_yscale('log')
        sns_plot.set_xticklabels(sns_plot.get_xticklabels(),rotation=20)
        sns_plot.get_figure().savefig(path+"/durationsDistributions", dpi=600)

#main_path = cfg.super_path
#organizations = ['JabRef','ionic-team','flutter','atom','github','elixir-lang','laravel','rails']
#makeMeanDiffTests(organizations, main_path)


def printProjectsDurationsLogTransformed(o_names, path):
        import numpy, pandas
        import seaborn as sns
        
        data = pandas.DataFrame(columns=['project', 'status', 'average_duration'])
        for i in range(0, len(o_names)):
            chosen_project = i # FROM 0 TO n-1
            
            project_name =  o_names[chosen_project]
            
            current_project_df = pandas.read_csv(path+'/'+project_name+'/statuses_durations.csv', sep=';')
            for l in current_project_df['sleepings'].tolist():
                if l!='[]':
                    l=list(map(int,l.replace('[','').replace(']','').split(',')))
                    sleeping_avg=numpy.log1p(numpy.mean(l))
                    if(project_name=='framework'):
                        add(data, ['laravel', 'non-coding', sleeping_avg])
                    else:
                        add(data, [project_name, 'non-coding', sleeping_avg])
            for l in current_project_df['hibernatings'].tolist():
                if l!='[]':
                    l=list(map(int,l.replace('[','').replace(']','').split(',')))
                    hibernation_avg=numpy.log1p(numpy.mean(l))
                    if(project_name=='framework'):
                        add(data, ['laravel', 'inactive', hibernation_avg])
                    else:
                        add(data, [project_name, 'inactive', hibernation_avg])
        
        pal=[sns.color_palette('Set1')[5],sns.color_palette('Set1')[8],sns.color_palette('Set1')[0]]
        sns_plot = sns.boxplot(x='project', y='average_duration', hue="status", hue_order=['non-coding','inactive'], data=data, palette=pal) #fliersize=5 (Default)
        sns_plot.set_xticklabels(sns_plot.get_xticklabels(),rotation=20)
        sns_plot.get_figure().savefig(path+"/durationsDistributionsLOG", dpi=600)

def tableCumulativeTransitions(o_names, path):
    import pandas
    
    START_FROM = 0
    
    labels = ['Project','#breaks','A_to_S','S_to_A','A_to_H','H_to_A','S_to_H','H_to_S','H_to_D','D_to_A','D_to_S']
    
    cumulative_table=pandas.DataFrame(columns=labels)
    
    for i in range(START_FROM, len(o_names)):
        
        chosen_project = i # FROM 0 TO n-1  
        project_name =  o_names[chosen_project]
        
        current_table=pandas.read_csv(path+'/'+project_name+'/transitions.csv', sep=';')
        sums = current_table.sum(skipna = True)
        if project_name=='framework':
            line=['laravel']+sums.tolist()[1:]
        else:
            line=[project_name]+sums.tolist()[1:]
        add(cumulative_table, line)
    cumulative_table.to_csv(path+'/cumulative_transitions.csv', sep=';', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')

def tableTransitionsPercentagesProjectList(path):
    import pandas
    transitions_table=pandas.read_csv(path+'/cumulative_transitions.csv',sep=';')
    
    labels = ['Project', 'AtoA', 'AtoS', 'AtoH',
              'StoA', 'StoS', 'StoH', 
              'HtoA', 'HtoS', 'HtoH', 'HtoD', 
              'DtoA', 'DtoS', 'DtoD']
    projects_table=pandas.DataFrame(columns=labels)
    
    for index, proj in transitions_table.iterrows():
        in_D = proj['H_to_D']
        out_D = (proj['D_to_A']+proj['D_to_S'])
        
        if(in_D>0):
            DtoA = proj['D_to_A']/in_D*100
            DtoS = proj['D_to_S']/in_D*100
            DtoD = (1-out_D/in_D)*100
        else:
            DtoA = 0
            DtoS = 0
            DtoD = 0
        
        in_H = (proj['A_to_H']+proj['S_to_H'])
        out_H =(proj['H_to_A']+proj['H_to_S']+proj['H_to_D'])
        HtoA = proj['H_to_A']/in_H*100
        HtoS = proj['H_to_S']/in_H*100
        HtoH = (1-out_H/in_H)*100
        HtoD = proj['H_to_D']/in_H*100
        
        in_S = (proj['A_to_S']+proj['H_to_S']+proj['D_to_S'])
        out_S = (proj['S_to_A']+proj['S_to_H'])
        StoA = proj['S_to_A']/in_S*100
        StoS = (1-out_S/in_S)*100
        StoH = proj['S_to_H']/in_S*100
        
        in_A = proj['#breaks']
        out_A = proj['A_to_S']+proj['A_to_H']
        
        AtoA = (1-out_A/in_A)*100
        AtoS = proj['A_to_S']/in_A*100
        AtoH = proj['A_to_H']/in_A*100
    
        add(projects_table, [proj['Project'], AtoA, AtoS, AtoH,
                                             StoA, StoS, StoH, 
                                             HtoA, HtoS, HtoH, HtoD, 
                                             DtoA, DtoS, DtoD])
        
    projects_table.to_csv(path+'/transitions_percentages_projects.csv', sep=';', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')

def tableTransitionsPercentages(path):
    import pandas, os
    transitions_table=pandas.read_csv(path+'/cumulative_transitions.csv',sep=';')
    
    for index, proj in transitions_table.iterrows():
        in_D = proj['H_to_D']
        out_D = (proj['D_to_A']+proj['D_to_S'])
        
        if(in_D>0):
            DtoA = proj['D_to_A']/in_D*100
            DtoS = proj['D_to_S']/in_D*100
            DtoD = (1-out_D/in_D)*100
        else:
            DtoA = 0
            DtoS = 0
            DtoD = 0
        
        in_H = (proj['A_to_H']+proj['S_to_H'])
        out_H =(proj['H_to_A']+proj['H_to_S']+proj['H_to_D'])
        HtoA = proj['H_to_A']/in_H*100
        HtoS = proj['H_to_S']/in_H*100
        HtoH = (1-out_H/in_H)*100
        HtoD = proj['H_to_D']/in_H*100
        
        in_S = (proj['A_to_S']+proj['H_to_S']+proj['D_to_S'])
        out_S = (proj['S_to_A']+proj['S_to_H'])
        StoA = proj['S_to_A']/in_S*100
        StoS = (1-out_S/in_S)*100
        StoH = proj['S_to_H']/in_S*100
        
        in_A = proj['#breaks']
        out_A = proj['A_to_S']+proj['A_to_H']
        
        AtoA = (1-out_A/in_A)*100
        AtoS = proj['A_to_S']/in_A*100
        AtoH = proj['A_to_H']/in_A*100
        
        matrix = pandas.DataFrame(columns=['to', 'Active', 'Sleeping', 'Hibernating', 'Dead'])
        row=['Active', AtoA, AtoS, AtoH, '-']
        add(matrix, row)
        row=['Sleeping', StoA, StoS, StoH, '-']
        add(matrix, row)
        row=['Hibernating', HtoA, HtoS, HtoH, HtoD]
        add(matrix, row)
        row=['Dead', DtoA, DtoS, '-', DtoD]
        add(matrix, row)
        chains_path = path+'/Chains'
        os.makedirs(chains_path, exist_ok=True) 
        matrix.to_csv(chains_path+'/'+proj['Project']+'_markov.csv', sep=';', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')

def tableCumulativeTransitionsPercentages(path):
    import pandas
    transitions_table=pandas.read_csv(path+'/cumulative_transitions.csv',sep=';')
    sums = transitions_table.sum(skipna = True)
    
    in_D = sums['H_to_D']
    out_D = (sums['D_to_A']+sums['D_to_S'])
    
    if(in_D>0):
        DtoA = sums['D_to_A']/in_D*100
        DtoS = sums['D_to_S']/in_D*100
        DtoD = (1-out_D/in_D)*100
    else:
        DtoA = 0
        DtoS = 0
        DtoD = 0
    
    in_H = (sums['A_to_H']+sums['S_to_H'])
    out_H =(sums['H_to_A']+sums['H_to_S']+sums['H_to_D'])
    HtoA = sums['H_to_A']/in_H*100
    HtoS = sums['H_to_S']/in_H*100
    HtoH = (1-out_H/in_H)*100
    HtoD = sums['H_to_D']/in_H*100
    
    in_S = (sums['A_to_S']+sums['H_to_S']+sums['D_to_S'])
    out_S = (sums['S_to_A']+sums['S_to_H'])
    StoA = sums['S_to_A']/in_S*100
    StoS = (1-out_S/in_S)*100
    StoH = sums['S_to_H']/in_S*100
    
    in_A = sums['#breaks']
    out_A = sums['A_to_S']+sums['A_to_H']
    
    AtoA = (1-out_A/in_A)*100
    AtoS = sums['A_to_S']/in_A*100
    AtoH = sums['A_to_H']/in_A*100
    
    matrix = pandas.DataFrame(columns=['to', 'Active', 'Sleeping', 'Hibernating', 'Dead'])
    row=['Active', AtoA, AtoS, AtoH, '-']
    add(matrix, row)
    row=['Sleeping', StoA, StoS, StoH, '-']
    add(matrix, row)
    row=['Hibernating', HtoA, HtoS, HtoH, HtoD]
    add(matrix, row)
    row=['Dead', DtoA, DtoS, '-', DtoD]
    add(matrix, row)
    matrix.to_csv(path+'/cumulative_markov.csv', sep=';', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')

def getProjectInactivities(project): #returns the list of developers each with its number of sleepings, hibernations and deads
    import csv, pandas
    
    durations_df = pandas.read_csv(super_path+'/'+project+'/statuses_durations.csv', sep=';')
    #Read Breaks Table
    with open(super_path+'/'+project+'/inactivity_interval_list.csv', 'r') as f:  #opens PW file
        #reader = csv.reader(f)
        breaks_list = [list(map(str,rec)) for rec in csv.reader(f, delimiter=',')]
    
    labels=['dev','project','sleepings','hibernatings','deads']
    inactivities_df=pandas.DataFrame(columns=labels)

    for index, dev_row in durations_df.iterrows():
        dev_life, dummy=getLife(dev_row['dev'], breaks_list)
        dev_years=dev_life/365
        
        sleepings = dev_row['sleepings'][1:-1]
        if(sleepings!=''):
            sleepings_perYear=len(sleepings.split(','))/dev_years
        else:
            sleepings_perYear=0
            
        hibernations = dev_row['hibernatings'][1:-1]
        if(hibernations!=''):
            hibernations_perYear=len(hibernations.split(','))/dev_years
        else:
            hibernations_perYear=0
            
        deads = dev_row['deads'][1:-1]
        if(deads!=''):
            deads_perYear=len(deads.split(','))/dev_years
        else:
            deads_perYear=0
            
        if(project=='framework'):
            add(inactivities_df, [dev_row['dev'], 'laravel', sleepings_perYear, hibernations_perYear, deads_perYear])
        else:
            add(inactivities_df, [dev_row['dev'], project, sleepings_perYear, hibernations_perYear, deads_perYear])

    return inactivities_df

def plotAllProjectInactivities(o_names, path):
    import pandas
    import seaborn as sns
    
    dataframes=[]
    for i in range(0, len(o_names)):
        chosen_project = i # FROM 0 TO n-1
        
        project_name =  o_names[chosen_project]
        dataframes.append(getProjectInactivities(project_name))
    aggregated_data = pandas.concat(dataframes)
    
    data = pandas.DataFrame(columns=['project', 'status', 'occurrences'])
    for index, dev_row in aggregated_data.iterrows():
        if(dev_row['sleepings']>0):
            add(data, [dev_row['project'], 'non-coding', dev_row['sleepings']])
        if(dev_row['hibernatings']>0):
            add(data, [dev_row['project'], 'inactive', dev_row['hibernatings']])
        if(dev_row['deads']>0):
            add(data, [dev_row['project'], 'gone', dev_row['deads']])
        
    pal=[sns.color_palette('Set1')[5],sns.color_palette('Set1')[8],sns.color_palette('Set1')[0]]
    sns_plot = sns.boxplot(x='project', y='occurrences', hue="status", hue_order=['non-coding','inactive','gone'], data=data, palette=pal)
    #sns_plot.set_yscale('log')
    sns_plot.set(ylim=(0, 13))
    sns_plot.set_xticklabels(sns_plot.get_xticklabels(), rotation=20)
    sns_plot.get_figure().savefig(path+"/Inactivities_occurrences.png", dpi=600)
    
def boxplotTransitionsPerYearOverall(p_names):
    import pandas
    import seaborn as sns

    data = pandas.DataFrame(columns=['dev','transition','amount_per_year'])
    for i in range(0, len(p_names)):
        chosen_project = i # FROM 0 TO n-1
        
        project_name =  p_names[chosen_project]
        transitions = pandas.read_csv(super_path+'/'+project_name+'/transitions.csv', sep=';')
        
        for index, row in transitions.iterrows():
            dev=row[0]
            
            if(row['A_to_S']!=0):
                add(data, [dev, 'A_to_S', row['A_to_S']])
            if(row['A_to_H']!=0):
                add(data, [dev, 'A_to_H', row['A_to_H']])
            if(row['S_to_A']!=0):
                add(data, [dev, 'S_to_A', row['S_to_A']])
            if(row['S_to_H']!=0):
                add(data, [dev, 'S_to_H', row['S_to_H']])
            if(row['H_to_A']!=0):
                add(data, [dev, 'H_to_A', row['H_to_A']])
            if(row['H_to_S']!=0):
                add(data, [dev, 'H_to_S', row['H_to_S']])
            if(row['H_to_D']!=0):
                add(data, [dev, 'H_to_D', row['H_to_D']])
            if(row['D_to_A']!=0):
                add(data, [dev, 'D_to_A', row['D_to_A']])
            if(row['D_to_S']!=0):
                add(data, [dev, 'D_to_S', row['D_to_S']])
    
    pal=[sns.color_palette('Set1')[8]]
    sns_plot = sns.boxplot(x='transition', y='amount_per_year', data=data, palette=pal, order=['A_to_S','A_to_H','S_to_A','S_to_H','H_to_A','H_to_S','H_to_D','D_to_A','D_to_S'])
    sns_plot.set_xticklabels(sns_plot.get_xticklabels(), rotation=20)
    sns_plot.get_figure().savefig(super_path+"/transitions_per_year_overall.png", dpi=600)