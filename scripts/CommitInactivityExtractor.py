# -*- coding: utf-8 -*-
"""
Created on Thu Feb  7 15:22:01 2019

@author: Pepp_
"""
import mysql.connector
import utilities as util
import pandas
import os
import numpy
import csv
import logging
import config as cfg

config = cfg.config

p_names=cfg.p_names
p_urls=cfg.p_urls

cnx = mysql.connector.connect(**config)
cursor = cnx.cursor(buffered=True)

for i in range(0, len(p_names)):
    chosen_project = i # FROM 0 TO n-1

    project_name =  p_names[chosen_project]
    partial_project_url = p_urls[chosen_project]

    project_id = util.getProjectId(cursor, project_name, partial_project_url)
    
    logging.basicConfig(filename='CommitExtraction.log',level=logging.INFO)
    logging.info('Project: '+project_name+' PID: '+project_id+' Started')
    
    query = ("SELECT created_at AS date FROM projects "+
             "WHERE id="+project_id)
    cursor.execute(query)
    project_start=cursor.fetchone()[0].strftime('%Y-%m-%d %H:%M:%S')
    
    path = ("C:/Users/Pepp_/SpyderWorkspace/Commit_Analysis/"+project_name)
    os.makedirs(path, exist_ok=True)  

    query = ("SELECT id, author_id, created_at AS date FROM commits "+
             "WHERE project_id="+project_id+
             " AND created_at>='"+project_start+"'"+
             " AND author_id NOT IN (SELECT id from users where fake=1)")
    cursor.execute(query)
    commits_data=pandas.DataFrame(cursor.fetchall(), columns=cursor.column_names)

    # GET MIN and MAX COMMIT TIMESTAMP
    max_commit_date=(max(commits_data.date))
    min_commit_date=(min(commits_data.date))
    
    column_names=['user_id']
    for single_date in util.daterange(min_commit_date, max_commit_date): #daterange(min_commit_date, max_commit_date):
        column_names.append(single_date.strftime("%Y-%m-%d"))

    # ITERATE UNIQUE USERS (U)
    u_data=[]
    for u in commits_data.author_id.unique():
        cur_user_data=[u]
        date_commit_count = pandas.to_datetime(commits_data[['date']][commits_data['author_id']==u].pop('date'), format="%Y-%m-%d").dt.date.value_counts()
        # ITERATE FROM DAY1 --> DAYN (D)
        for d in column_names[1:]:
            # IF U COMMITTED DURING D THEN U[D]=1 ELSE U(D)=0
            try:
                cur_user_data.append(date_commit_count[pandas.to_datetime(d).date()])
            except Exception: # add "as name_given_to_exception" before ":" to get info 
                cur_user_data.append(0)
        print("finished user", u)
        u_data.append(cur_user_data)
    
    commit_table=pandas.DataFrame(u_data,columns=column_names)
    commit_table.to_csv(project_name+'/commit_table.csv', sep=',', na_rep='NA', header=True, index=False, mode='w', encoding='utf-8', quoting=None, quotechar='"', line_terminator='\n', decimal='.')
    print("CSV Written")

    #commit_table = pandas.read_csv('C:/Users/Pepp_/SpyderWorkspace/Commit_Analysis/'+PROJECT_NAME+'/commit_table.csv') 
    
    # Calcola days between commits, if commits are in adjacent days count 1
    inactivity_intervals_data=[]
    break_dates=[]
    for index, u in commit_table.iterrows():
        row = [u[0]] #User_id
        current_break_dates = [u[0]] #User_id
        commit_dates=[]
        for i in range(1,len(u)):
            if(u[i]>0):
                commit_dates.append(commit_table.columns[i])
        for i in range(0,len(commit_dates)-1):
            period=util.days_between(commit_dates[i], commit_dates[i+1])
            if(period>1):
                row.append(period)
                current_break_dates.append(commit_dates[i]+"/"+commit_dates[i+1])
        print('Last User Done: ', row[0])
        inactivity_intervals_data.append(row)
        break_dates.append(current_break_dates)
        user_lifespan = util.days_between(commit_dates[0], commit_dates[len(commit_dates)-1])+1
        commit_frequency = len(commit_dates)/user_lifespan
        row.append(user_lifespan)
        row.append(commit_frequency)

    # Python program to get average of a list 
    for row in inactivity_intervals_data:
        total_inactivity_days = sum(row[1:(len(row)-2)])
        if(total_inactivity_days==0):
            avg_inactivity_interval = 0
            stdev_inactivity_interval = 0
            max_inactivity_days = 0
            min_inactivity_days = 0
        else:
            avg_inactivity_interval = total_inactivity_days/len(row[1:(len(row)-2)])
            stdev_inactivity_interval = numpy.std(row[1:(len(row)-2)])
            max_inactivity_days = max(row[1:(len(row)-2)])
            min_inactivity_days = min(row[1:(len(row)-2)])
        row.append(max_inactivity_days)
        row.append(min_inactivity_days)
        row.append(avg_inactivity_interval)
        row.append(stdev_inactivity_interval)

    with open(project_name+'/inactivity_interval_list.csv', 'w', newline='') as outcsv:   
        #configure writer to write standard csv file
        writer = csv.writer(outcsv, quoting=csv.QUOTE_NONE, quotechar='"')
        for r in inactivity_intervals_data:
            #Write item to outcsv
            writer.writerow(r)
        
    with open(project_name+'/break_dates_list.csv', 'w', newline='') as outcsv:   
        #configure writer to write standard csv file
        writer = csv.writer(outcsv, quoting=csv.QUOTE_NONE, quotechar='"')
        for r in break_dates:
            #Write item to outcsv
            writer.writerow(r)
    logging.info('Project: '+project_name+' PID: '+project_id+' DONE')

cursor.close
