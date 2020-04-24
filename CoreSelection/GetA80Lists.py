import os
import pandas
import Utilities as util
import Settings as cfg

def getA80(repos_list):
    for gitRepoName in repos_list:
        organization, repo = gitRepoName.split('/')
        sourceFile = os.path.join(cfg.A80_report_folder, repo, 'unmasking_results.csv')
        destFolder = os.path.join(cfg.A80_report_folder, repo)

        data = pandas.read_csv(sourceFile, sep = ';')

        tot_commits = data['commits'].sum()

        devs_with_login = data[data['login'].notnull()].drop(columns=['id', 'name', 'email'])
        devs_with_login = devs_with_login.groupby(['login'], as_index=False).sum().sort_values(by=['commits'], ascending=False)

        A80devs = pandas.DataFrame(columns = ['login', 'commits', 'percentage'])
        cum_perc = 0
        for i, dev in devs_with_login.iterrows():
            dev_perc = dev['commits'] / tot_commits * 100
            cum_perc += dev_perc

            util.add(A80devs, [dev['login'], dev['commits'], dev_perc])

            if cum_perc >= 80:
                break

        A80devs.to_csv(os.path.join(destFolder, cfg.A80_developers_file),
                       sep=';', na_rep='N/A', index=False, quoting=None, line_terminator='\n')

def getA80mod(repos_list):
    for gitRepoName in repos_list:
        organization, repo = gitRepoName.split('/')
        sourceFile = os.path.join(cfg.A80_report_folder, repo, 'unmasking_results.csv')
        destFolder = os.path.join(cfg.A80mod_report_folder, repo)
        os.makedirs(destFolder, exist_ok=True)

        data = pandas.read_csv(sourceFile, sep = ';')

        tot_commits = data['commits'].sum()

        devs_with_login = data[data['login'].notnull()].drop(columns=['id', 'name', 'email'])
        devs_with_login = devs_with_login.groupby(['login'], as_index=False).sum().sort_values(by=['commits'], ascending=False)

        A80modDevs = pandas.DataFrame(columns = ['login', 'commits', 'percentage'])

        cum_perc = 0
        for i, dev in devs_with_login.iterrows():
            dev_perc = dev['commits'] / tot_commits * 100
            cum_perc += dev_perc

            if dev_perc >= cfg.modTh:
                util.add(A80modDevs, [dev['login'], dev['commits'], dev_perc])

                if cum_perc >= 80 and dev_perc > cfg.modTh:
                    break
            else:
                break

        A80modDevs.to_csv(os.path.join(destFolder, cfg.A80mod_developers_file),
                       sep=';', na_rep='N/A', index=False, quoting=None, line_terminator='\n')

def getA80api(repos_list):
    for gitRepoName in repos_list:
        organization, repo = gitRepoName.split('/')
        sourceFile = os.path.join(cfg.main_folder, organization, repo, cfg.commit_list_file_name)
        destFolder = os.path.join(cfg.A80api_report_folder, repo)
        os.makedirs(destFolder, exist_ok=True)

        data = pandas.read_csv(sourceFile, sep = ';')
        data = data.drop(columns = ['date'])

        tot_commits = len(data)
        data = data.groupby(['author_id'], as_index=False).count().rename(columns = {'author_id':'login', 'sha':'commits'}).sort_values(by=['commits'], ascending=False)

        A80apiDevs = pandas.DataFrame(columns = ['login', 'commits', 'percentage'])

        cum_perc = 0
        for i, dev in data.iterrows():
            dev_perc = dev['commits'] / tot_commits * 100
            cum_perc += dev_perc

            util.add(A80apiDevs, [dev['login'], dev['commits'], dev_perc])

            if cum_perc >= 80:
                break

        A80apiDevs.to_csv(os.path.join(destFolder, cfg.A80api_developers_file),
                       sep=';', na_rep='N/A', index=False, quoting=None, line_terminator='\n')

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    ### ARGUMENTS MANAGEMENT
    repos_list=util.getReposList()
    getA80(repos_list)
    getA80mod(repos_list)
    getA80api(repos_list)