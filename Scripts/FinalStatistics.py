### IMPORT SYSTEM MODULES
import os, pandas, numpy, csv
import matplotlib.pyplot as plt
import seaborn as sns

### IMPORT CUSTOM MODULES
import Settings as cfg
import Utilities as util

def getLife(dev, organization):
    dev_life = 0
    # Read Breaks Table
    with open(cfg.main_folder + '/' + organization + '/' + cfg.pauses_list_file_name) as inactivities_file:
        devs_inactivities = [list(map(str, rec)) for rec in csv.reader(inactivities_file, delimiter=';')]

    for d in devs_inactivities:
        sd = d[0]
        if sd == dev:
            dev_life = int(d[-2])
            break
    return dev_life

def countOrganizationsAffected(repos_list, output_file_name):
    affected_summary = pandas.DataFrame(columns=['Project', 'Contributors', 'Sampled_Contributors', 'Non-Coding', 'Inactive', 'Gone'])

    for gitRepoName in repos_list:
        organization, main_project = gitRepoName.split('/')
        workingFolder = cfg.main_folder + '/' + organization

        # Breaks occurrences
        repo_affected = countAffected(gitRepoName, workingFolder)
        util.add(affected_summary, repo_affected)

    affected_summary.to_csv(cfg.main_folder + '/' + output_file_name + '.csv',
                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

def countOrganizationsTransitions(repos_list, output_file_name):
    transitions_summary = pandas.DataFrame(columns=['Project', '#breaks', 'A_to_NC', 'NC_to_A', 'A_to_I', 'I_to_A', 'NC_to_I', 'I_to_NC', 'I_to_G', 'G_to_A', 'G_to_NC'])

    for gitRepoName in repos_list:
        organization, main_project = gitRepoName.split('/')
        workingFolder = cfg.main_folder + '/' + organization

        # Transition occurrences
        repo_transitions = countTransitions(gitRepoName, workingFolder)
        util.add(transitions_summary, repo_transitions)

    transitions_summary.to_csv(cfg.main_folder + '/' + output_file_name + '.csv',
                               sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
    return transitions_summary

def countAffected(repo, workingFolder):
    ''' Developers who have been inactive per organization '''
    affected = [repo]

    main_repo_folder = cfg.main_folder + '/' + repo
    commit_history_table = pandas.read_csv(main_repo_folder + '/' + cfg.commit_history_table_file_name, sep=cfg.CSV_separator)
    affected.append(len(commit_history_table))

    TF_devs = pandas.read_csv(main_repo_folder + '/' + cfg.commit_history_table_file_name, sep=cfg.CSV_separator)
    affected.append(len(TF_devs))

    dev_breaks_folder = workingFolder + '/' + cfg.labeled_breaks_folder_name
    non_coding = inactive = gone = 0
    for file in dev_breaks_folder:
        if os.path.isfile(dev_breaks_folder + '/' + file):
            dev_breaks = pandas.read_csv(dev_breaks_folder + '/' + file, sep = cfg.CSV_separator)
            if cfg.NC in dev_breaks.label.tolist():
                non_coding += 1
            if cfg.I in dev_breaks.label.tolist():
                inactive += 1
            if cfg.G in dev_breaks.label.tolist():
                gone += 1

    affected += [non_coding, inactive, gone]

    return affected

def countTransitions(repo, workingFolder):
    ''' Needed to calculate the percentages for the markov chains '''
    transitions = [repo]

    org = repo.split('/')[0]
    dev_breaks_folder = workingFolder + '/' + cfg.labeled_breaks_folder_name
    breaks = 0
    AtoNC = NCtoA = AtoI = ItoA = NCtoI = ItoNC = ItoG = GtoA = GtoNC = 0
    for file in os.listdir(dev_breaks_folder):
        if os.path.isfile(dev_breaks_folder + '/' + file):
            dev_breaks = pandas.read_csv(dev_breaks_folder + '/' + file, sep=cfg.CSV_separator)
            breaks += len(dev_breaks)
            AtoNC += len(dev_breaks[(dev_breaks.previously == cfg.A) & (dev_breaks.label == cfg.NC)])
            NCtoA += len(dev_breaks[(dev_breaks.previously == cfg.NC) & (dev_breaks.label == cfg.A)])
            AtoI += len(dev_breaks[(dev_breaks.previously == cfg.A) & (dev_breaks.label == cfg.I)])
            ItoA += len(dev_breaks[(dev_breaks.previously == cfg.I) & (dev_breaks.label == cfg.A)])
            NCtoI += len(dev_breaks[(dev_breaks.previously == cfg.NC) & (dev_breaks.label == cfg.I)])
            ItoNC += len(dev_breaks[(dev_breaks.previously == cfg.I) & (dev_breaks.label == cfg.NC)])
            ItoG += len(dev_breaks[(dev_breaks.previously == cfg.I) & (dev_breaks.label == cfg.G)])
            GtoA += len(dev_breaks[(dev_breaks.previously == cfg.G) & (dev_breaks.label == cfg.A)])
            GtoNC += len(dev_breaks[(dev_breaks.previously == cfg.G) & (dev_breaks.label == cfg.NC)])

    transitions += [breaks, AtoNC, NCtoA, AtoI, ItoA, NCtoI, ItoNC, ItoG, GtoA, GtoNC]
    return transitions

def organizationsTransitionsPercentages(transitions_summary_file_name, output_file_name):
    ''' Writes the chain table for each organization and returns the chains in a list needed to draw the markov chains '''
    labels = ['Project', 'A_to_A', 'A_to_NC', 'A_to_I',
              'NC_to_A', 'NC_to_NC', 'NC_to_I',
              'I_to_A', 'I_to_NC', 'I_to_I', 'I_to_G',
              'G_to_A', 'G_to_NC', 'G_to_G']
    chains_list = pandas.DataFrame(columns=labels)

    transitions_summary = pandas.read_csv(cfg.main_folder + '/' + transitions_summary_file_name + '.csv', sep=cfg.CSV_separator)

    for index, proj in transitions_summary.iterrows():
        in_G = proj['I_to_G']
        out_G = (proj['G_to_A'] + proj['G_to_NC'])

        if (in_G > 0):
            GtoA = proj['G_to_A'] / in_G * 100
            GtoNC = proj['G_to_NC'] / in_G * 100
            GtoG = (1 - out_G / in_G) * 100
        else:
            GtoA = 0
            GtoNC = 0
            GtoG = 0

        in_I = (proj['A_to_I'] + proj['NC_to_I'])
        out_I = (proj['I_to_A'] + proj['I_to_NC'] + proj['I_to_G'])

        if (in_I > 0):
            ItoA = proj['I_to_A'] / in_I * 100
            ItoNC = proj['I_to_NC'] / in_I * 100
            ItoI = (1 - out_I / in_I) * 100
            ItoG = proj['I_to_G'] / in_I * 100
        else:
            ItoA = 0
            ItoNC = 0
            ItoI = 0
            ItoG = 0

        in_NC = (proj['A_to_NC'] + proj['I_to_NC'] + proj['G_to_NC'])
        out_NC = (proj['NC_to_A'] + proj['NC_to_I'])

        if (in_NC > 0):
            NCtoA = proj['NC_to_A'] / in_NC * 100
            NCtoNC = (1 - out_NC / in_NC) * 100
            NCtoI = proj['NC_to_I'] / in_NC * 100
        else:
            NCtoA = 0
            NCtoNC = 0
            NCtoI = 0

        in_A = proj['#breaks']
        out_A = proj['A_to_NC'] + proj['A_to_I']

        AtoA = (1 - out_A / in_A) * 100
        AtoNC = proj['A_to_NC'] / in_A * 100
        AtoI = proj['A_to_I'] / in_A * 100

        matrix = pandas.DataFrame(columns=['to', 'Active', 'Non_coding', 'Inactive', 'Gone'])
        row = ['Active', AtoA, AtoNC, AtoI, '-']
        util.add(matrix, row)
        row = ['Non_coding', NCtoA, NCtoNC, NCtoI, '-']
        util.add(matrix, row)
        row = ['Inactive', ItoA, ItoNC, ItoI, ItoG]
        util.add(matrix, row)
        row = ['Gone', GtoA, GtoNC, '-', GtoG]
        util.add(matrix, row)

        destinationFolder = cfg.main_folder + '/' + cfg.chains_folder_name
        os.makedirs(destinationFolder, exist_ok=True)

        util.add(chains_list, [proj['Project'], AtoA, AtoNC, AtoI,
                             NCtoA, NCtoNC, NCtoI,
                             ItoA, ItoNC, ItoI, ItoG,
                             GtoA, GtoNC, GtoG])

        organization = proj['Project'].split('/')[0]
        matrix.to_csv(destinationFolder + '/' + organization + '_markov.csv',
                      sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
    TFs_row = TFsTransitionsPercentages(transitions_summary)
    util.add(chains_list, TFs_row)
    last_row = ['AVG']
    last_row += chains_list.mean().tolist()
    print(chains_list, len(last_row), len(chains_list.columns), last_row)
    util.add(chains_list, last_row)
    chains_list.to_csv(cfg.main_folder + '/' + output_file_name + '.csv',
                       sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

def breaksDistributionStats(repos_list, output_file_name):
    breaks_stats = pandas.DataFrame(columns=['Project', 'mean', 'st_dev', 'var', 'median', 'breaks_devlife_corr'])
    projects_counts = []
    for repo in repos_list:
        organization, project = repo.split('/')

        breaks_folder = cfg.main_folder + '/' + organization + '/' + cfg.labeled_breaks_folder_name
        breaks_lifetime = pandas.DataFrame(columns=['BpY', 'life'])
        for file in os.listdir(breaks_folder):
            if(os.path.isfile(breaks_folder + '/' + file)):
                dev = file.split('_')[0]

                dev_life = getLife(dev, organization)
                if(dev_life<=1):
                    print('INVALID DEVELOPER LIFE')
                    continue

                breaks_list = pandas.read_csv(breaks_folder + '/' + file, sep=cfg.CSV_separator)
                breaks_list = breaks_list[(breaks_list.label != 'ACTIVE') & (breaks_list.label != 'NOW')]
                num_breaks = len(breaks_list)
                years = dev_life / 365
                BpY = num_breaks / years
                util.add(breaks_lifetime, [BpY, dev_life])

        util.add(breaks_stats, [repo,
                           numpy.mean(breaks_lifetime.BpY.tolist()),
                           numpy.std(breaks_lifetime.BpY.tolist()),
                           numpy.var(breaks_lifetime.BpY.tolist()),
                           numpy.median(breaks_lifetime.BpY.tolist()),
                           numpy.corrcoef(breaks_lifetime['BpY'], breaks_lifetime['life'])[1][0]])
        projects_counts.append(breaks_lifetime.BpY)

    breaks_stats.to_csv(cfg.main_folder + '/' + output_file_name + '.csv',
                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

    ###
    # labels = [repo.split('/')[0] for repo in repos_list]
    # plt.clf()
    # projects_counts.reverse()
    # plt.boxplot(projects_counts)
    # labels.reverse()
    # plt.xticks(numpy.arange(1, len(repos_list) + 1), labels, rotation=20)
    # plt.grid(False)
    # plt.ylabel("Pauses per Year")
    # plt.savefig(cfg.main_folder + '/' + output_file_name, dpi=600)
    # plt.clf()

def breaksDurationsPlot(repos_list, output_file_name):
    data = pandas.DataFrame(columns=['project', 'status', 'average_duration'])
    for repo in repos_list:
        organization, project = repo.split('/')

        breaks_folder = cfg.main_folder + '/' + organization + '/' + cfg.labeled_breaks_folder_name
        NC_list = []
        I_list = []
        for file in os.listdir(breaks_folder):
            if (os.path.isfile(breaks_folder + '/' + file)):
                dev_breaks = pandas.read_csv(breaks_folder + '/' + file, sep=cfg.CSV_separator)

                NC_list.append(dev_breaks[dev_breaks.label=='NON_CODING'].len.mean())
                I_list.append(dev_breaks[dev_breaks.label == 'INACTIVE'].len.mean())

        for dev_avg in NC_list:
            util.add(data, [organization, 'non-coding', dev_avg])
        for dev_avg in I_list:
            util.add(data, [organization, 'inactive', dev_avg])

    print('S: ' + str(min(NC_list)) + ' - ' + str(max(NC_list)) + ' Avg: ' + str(numpy.mean(NC_list)))
    print('H: ' + str(min(I_list)) + ' - ' + str(max(I_list)) + ' Avg: ' + str(numpy.mean(I_list)))

    pal = [sns.color_palette('Set1')[5], sns.color_palette('Set1')[8], sns.color_palette('Set1')[0]]
    sns_plot = sns.boxplot(x='project', y='average_duration', hue="status", hue_order=['non-coding', 'inactive'], data=data, palette=pal)
    sns_plot.set_yscale('log')
    sns_plot.set_xticklabels(sns_plot.get_xticklabels(), rotation=20)
    sns_plot.get_figure().savefig(cfg.main_folder + '/' + output_file_name, dpi=600)
    sns_plot.get_figure().clf()

def breaksOccurrencesPlot(repos_list, output_file_name):
    dataframes = []
    for repo in repos_list:
        organization, project = repo.split('/')

        labels = ['dev', 'organization', 'NCs', 'Is', 'Gs']
        inactivities_df = pandas.DataFrame(columns=labels)

        breaks_folder = cfg.main_folder + '/' + organization + '/' + cfg.labeled_breaks_folder_name
        for file in os.listdir(breaks_folder):
            if (os.path.isfile(breaks_folder + '/' + file)):
                dev = file.split('_')[0]

                dev_life = getLife(dev, organization)
                if (dev_life <= 1):
                    print('INVALID DEVELOPER LIFE')
                    continue

                dev_years = dev_life / 365

                breaks_list = pandas.read_csv(breaks_folder + '/' + file, sep=cfg.CSV_separator)

                NCs = len(breaks_list[breaks_list.label == 'NON_CODING'])
                try:
                    NCs_perYear = NCs / dev_years
                except:
                    NCs_perYear = 0

                Is = len(breaks_list[breaks_list.label == 'INACTIVE'])
                try:
                    Is_perYear = Is / dev_years
                except:
                    Is_perYear = 0

                Gs = len(breaks_list[breaks_list.label == 'GONE'])
                try:
                    Gs_perYear = Gs / dev_years
                except:
                    Gs_perYear = 0

                util.add(inactivities_df, [dev, organization, NCs_perYear, Is_perYear, Gs_perYear])
        dataframes.append(inactivities_df)
    aggregated_data = pandas.concat(dataframes, ignore_index=True)

    data = pandas.DataFrame(columns=['organization', 'status', 'occurrences'])
    for index, dev_row in aggregated_data.iterrows():
        if (dev_row.NCs > 0):
            util.add(data, [dev_row.organization, 'non-coding', dev_row.NCs])
        if (dev_row.Is > 0):
            util.add(data, [dev_row.organization, 'inactive', dev_row.Is])
        if (dev_row.Gs > 0):
            util.add(data, [dev_row.organization, 'gone', dev_row.Gs])

    pal = [sns.color_palette('Set1')[5], sns.color_palette('Set1')[8], sns.color_palette('Set1')[0]]
    sns_plot = sns.boxplot(x='organization', y='occurrences', hue="status", hue_order=['non-coding', 'inactive', 'gone'],
                           data=data, palette=pal)
    # sns_plot.set_yscale('log')
    #sns_plot.set(ylim=(0, 13))
    sns_plot.set_xticklabels(sns_plot.get_xticklabels(), rotation=20)
    sns_plot.get_figure().savefig(cfg.main_folder + '/' + output_file_name, dpi=600)
    sns_plot.get_figure().clf()

def TFsTransitionsPercentages(transitions_summary):
    ''' Calculates the Chain for all the TF '''
    total = transitions_summary.sum()

    in_G = total['I_to_G']
    out_G = (total['G_to_A'] + total['G_to_NC'])

    if (in_G > 0):
        GtoA = total['G_to_A'] / in_G * 100
        GtoNC = total['G_to_NC'] / in_G * 100
        GtoG = (1 - out_G / in_G) * 100
    else:
        GtoA = 0
        GtoNC = 0
        GtoG = 0

    in_I = (total['A_to_I'] + total['NC_to_I'])
    out_I = (total['I_to_A'] + total['I_to_NC'] + total['I_to_G'])

    if (in_I > 0):
        ItoA = total['I_to_A'] / in_I * 100
        ItoNC = total['I_to_NC'] / in_I * 100
        ItoI = (1 - out_I / in_I) * 100
        ItoG = total['I_to_G'] / in_I * 100
    else:
        ItoA = 0
        ItoNC = 0
        ItoI = 0
        ItoG = 0

    in_NC = (total['A_to_NC'] + total['I_to_NC'] + total['G_to_NC'])
    out_NC = (total['NC_to_A'] + total['NC_to_I'])

    if (in_NC > 0):
        NCtoA = total['NC_to_A'] / in_NC * 100
        NCtoNC = (1 - out_NC / in_NC) * 100
        NCtoI = total['NC_to_I'] / in_NC * 100
    else:
        NCtoA = 0
        NCtoNC = 0
        NCtoI = 0

    in_A = total['#breaks']
    out_A = total['A_to_NC'] + total['A_to_I']

    AtoA = (1 - out_A / in_A) * 100
    AtoNC = total['A_to_NC'] / in_A * 100
    AtoI = total['A_to_I'] / in_A * 100

    row = ['TFs', AtoA, AtoNC, AtoI, NCtoA, NCtoNC, NCtoI, ItoA, ItoNC, ItoI, ItoG, GtoA, GtoNC, GtoG]
    return row

def TFsBreaksOccurrencesPlot(repos_list, output_file_name):
    dataframes = []
    for repo in repos_list:
        organization, project = repo.split('/')

        labels = ['dev', 'organization', 'NCs', 'Is', 'Gs']
        inactivities_df = pandas.DataFrame(columns=labels)

        breaks_folder = cfg.main_folder + '/' + organization + '/' + cfg.labeled_breaks_folder_name
        for file in os.listdir(breaks_folder):
            if (os.path.isfile(breaks_folder + '/' + file)):
                dev = file.split('_')[0]

                dev_life = getLife(dev, organization)
                if (dev_life == 0):
                    print('INVALID DEVELOPER LIFE')

                dev_years = dev_life / 365

                breaks_list = pandas.read_csv(breaks_folder + '/' + file, sep=cfg.CSV_separator)

                NCs = len(breaks_list[breaks_list.label == 'NON_CODING'])
                try:
                    NCs_perYear = NCs / dev_years
                except:
                    NCs_perYear = 0

                Is = len(breaks_list[breaks_list.label == 'INACTIVE'])
                try:
                    Is_perYear = Is / dev_years
                except:
                    Is_perYear = 0

                Gs = len(breaks_list[breaks_list.label == 'GONE'])
                try:
                    Gs_perYear = Gs / dev_years
                except:
                    Gs_perYear = 0

                util.add(inactivities_df, [dev, organization, NCs_perYear, Is_perYear, Gs_perYear])
        dataframes.append(inactivities_df)
    aggregated_data = pandas.concat(dataframes, ignore_index=True)

    data = pandas.DataFrame(columns=['organization', 'status', 'occurrences'])
    for index, dev_row in aggregated_data.iterrows():
        if (dev_row.NCs > 0):
            util.add(data, ['TF Developers', 'non-coding', dev_row.NCs])
        if (dev_row.Is > 0):
            util.add(data, ['TF Developers', 'inactive', dev_row.Is])
        if (dev_row.Gs > 0):
            util.add(data, ['TF Developers', 'gone', dev_row.Gs])

    #data = pandas.DataFrame({'organization':['a','a','a','a','a','a','b','b','b','b','c','c','c','c','c'],
    #                         'status':['x','y','y','x','y','y','y','x','y','y','x','y','y','y','x'],
    #                         'occurrences':[5,4,3,5,2,5,6,5,3,5,3,5,6,3,5]})
    pal = [sns.color_palette('Set1')[5], sns.color_palette('Set1')[8], sns.color_palette('Set1')[0]]
    sns_plot = sns.boxplot(x='organization', y='occurrences', hue="status",
                           hue_order=['non-coding', 'inactive', 'gone'],
                           data=data, palette=pal)
    # sns_plot.set_yscale('log')
    # sns_plot.set(ylim=(0, 12))
    sns_plot.set_xticklabels(sns_plot.get_xticklabels())
    sns_plot.get_figure().savefig(cfg.main_folder + '/' + output_file_name, dpi=600)
    sns_plot.get_figure().clf()

def TFsBreaksDurationsPlot(repos_list, output_file_name):
    data = pandas.DataFrame(columns=['project', 'status', 'average_duration'])
    for repo in repos_list:
        organization, project = repo.split('/')

        breaks_folder = cfg.main_folder + '/' + organization + '/' + cfg.labeled_breaks_folder_name
        NC_list = []
        I_list = []
        for file in os.listdir(breaks_folder):
            if (os.path.isfile(breaks_folder + '/' + file)):
                dev_breaks = pandas.read_csv(breaks_folder + '/' + file, sep=cfg.CSV_separator)

                NC_list.append(dev_breaks[dev_breaks.label=='NON_CODING'].len.mean())
                I_list.append(dev_breaks[dev_breaks.label == 'INACTIVE'].len.mean())

        for dev_avg in NC_list:
            util.add(data, ['TF Developers', 'non-coding', dev_avg])
        for dev_avg in I_list:
            util.add(data, ['TF Developers', 'inactive', dev_avg])

    pal = [sns.color_palette('Set1')[5], sns.color_palette('Set1')[8], sns.color_palette('Set1')[0]]
    sns_plot = sns.boxplot(x='project', y='average_duration', hue="status", hue_order=['non-coding', 'inactive'], data=data, palette=pal)
    sns_plot.set_yscale('log')
    sns_plot.set_xticklabels(sns_plot.get_xticklabels())
    sns_plot.get_figure().savefig(cfg.main_folder + '/' + output_file_name, dpi=600)
    sns_plot.get_figure().clf()

# MAIN FUNCTION
def main(repos_list):
    transitions_summary_file_name = 'transitionsSummary'

    countOrganizationsAffected(repos_list, 'affectedSummary')
    countOrganizationsTransitions(repos_list, transitions_summary_file_name)
    organizationsTransitionsPercentages(transitions_summary_file_name, 'organizations_chains_list')
    breaksDistributionStats(repos_list, 'BreaksDistributions')
    breaksOccurrencesPlot(repos_list, 'BreaksOccurrences')
    breaksDurationsPlot(repos_list, 'DurationsDistributions')

    TFsBreaksOccurrencesPlot(repos_list, 'TFsBreaksOccurrences')
    TFsBreaksDurationsPlot(repos_list, 'TFsDurationsDistributions')

#util.makeMeanDiffTests(organizations, main_path)

    print("That's it, man!")

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    ### ARGUMENTS MANAGEMENT
    repos_list = util.getReposList()
    main(repos_list)
