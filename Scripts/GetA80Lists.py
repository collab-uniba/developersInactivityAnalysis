import os
import pandas
import Utilities as util

### MAIN FUNCTION
def main(repos_list):

    for gitRepoName in repos_list:
        organization, repo = gitRepoName.split('/')
        sourceFolder = '../A80_Results/' + repo

        data = pandas.read_csv(os.path.join(sourceFolder, 'unmasking_results.csv'), sep = ';')

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

        A80devs.to_csv(os.path.join(sourceFolder, 'A80_devs.csv'),
                       sep=';', na_rep='N/A', index=False, quoting=None, line_terminator='\n')

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    ### ARGUMENTS MANAGEMENT
    repos_list=util.getReposList()
    main(repos_list)