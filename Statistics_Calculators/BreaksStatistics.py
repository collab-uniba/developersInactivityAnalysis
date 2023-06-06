import os, pandas
import matplotlib.pyplot as plt

### IMPORT CUSTOM MODULES
import sys
sys.path.insert(1, '../')
import Settings as cfg
import Utilities as util

### THIS MODULE HAS BEEN USED FOR CHOISES DURING THE DEVELOPMENT. NOT USED FOR THE PAPER ###

### MAIN FUNCTION
def main(repos_list):
    all_th = []
    all_breaks = []
    for gitRepoName in repos_list:
        organization, main_project = gitRepoName.split('/')
        workingFolder = cfg.main_folder + '/' + organization
        breaksFolder = workingFolder + '/Dev_Breaks'

        for file in os.listdir(breaksFolder):
            if(os.path.isfile(breaksFolder+'/'+file)):
                dev = file.split('_')[0]

                breaks_df = pandas.read_csv(breaksFolder + '/' + file, sep=cfg.CSV_separator)
                all_th += breaks_df.th.tolist()
                all_breaks += breaks_df.len.tolist()
                try:
                    min_th = round(min(breaks_df.th),3)
                    max_th = round(max(breaks_df.th),3)
                    mean_th = round(breaks_df.th.mean(),3)
                    dev_th = round(breaks_df.th.std(),3)
                    print(dev, min_th, max_th, mean_th, dev_th)
                    #breaks_df.th.plot.hist()
                    #plt.show()
                except Exception as e:
                    print(dev, 'Exception: {}'.format(e))
    print(len(all_th))

    plt.plot(sorted(all_th))
    plt.xlim(0, 500)
    plt.ylim(0, 20)
    plt.show()

    plt.plot(sorted(all_breaks))
    plt.xlim(0, 500)
    plt.ylim(0, 20)
    plt.show()

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    ### ARGUMENTS MANAGEMENT
    repos_list = util.getReposList()
    main(repos_list)

### THIS MODULE HAS BEEN USED FOR CHOISES DURING THE DEVELOPMENT. NOT USED FOR THE PAPER ###

