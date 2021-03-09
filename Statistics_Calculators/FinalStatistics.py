### IMPORT SYSTEM MODULES
import csv
import numpy
import os
import pandas
import scipy
import sys

import matplotlib.pyplot as plt
import rpy2.robjects as robjects
import seaborn as sns
import statsmodels.api as sm
from rpy2.robjects.packages import importr

import Settings as cfg
import Utilities as util
import effectsize


def getLife(dev, organization):
    dev_life = 0
    # Read Breaks Table
    with open(os.path.join(cfg.main_folder, organization, cfg.pauses_list_file_name)) as inactivities_file:
        devs_inactivities = [list(map(str, rec)) for rec in csv.reader(inactivities_file, delimiter=';')]

    for d in devs_inactivities:
        sd = d[0]
        if sd == dev:
            dev_life = int(d[-2])
            break
    return dev_life

def countOrganizationsAffected(repos_list, output_file_name, mode):
    affected_summary = pandas.DataFrame(columns=['Project', 'Contributors', 'Sampled_Contributors', 'Non-Coding', 'Inactive', 'Gone', 'Still_Gone'])

    non_coding_affected = pandas.DataFrame(columns = ['repo','login'])
    inactive_affected = pandas.DataFrame(columns = ['repo','login'])
    gone_affected = pandas.DataFrame(columns = ['repo','login'])
    still_gone_affected = pandas.DataFrame(columns = ['repo','login'])

    for gitRepoName in repos_list:
        organization, main_project = gitRepoName.split('/')
        workingFolder = os.path.join(cfg.main_folder, organization)

        # Breaks occurrences
        repo_affected, repo_non_coding_affected, repo_inactive_affected, repo_gone_affected, repo_still_gone = countAffected(gitRepoName, workingFolder, mode)
        util.add(affected_summary, repo_affected)

        non_coding_affected = pandas.concat([non_coding_affected, repo_non_coding_affected], ignore_index=True)
        inactive_affected = pandas.concat([inactive_affected, repo_inactive_affected], ignore_index=True)
        gone_affected = pandas.concat([gone_affected, repo_gone_affected], ignore_index=True)
        still_gone_affected = pandas.concat([still_gone_affected, repo_still_gone], ignore_index=True)

    affected_summary.to_csv(os.path.join(cfg.main_folder, mode.upper(), output_file_name + '.csv'),
                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
    non_coding_affected.to_csv(os.path.join(cfg.main_folder, mode.upper(), 'non_coding_affected.csv'),
                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None,
                            line_terminator='\n')
    inactive_affected.to_csv(os.path.join(cfg.main_folder, mode.upper(), 'inactive_affected.csv'),
                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None,
                            line_terminator='\n')
    gone_affected.to_csv(os.path.join(cfg.main_folder, mode.upper(), 'gone_affected.csv'),
                            sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None,
                            line_terminator='\n')
    still_gone_affected.to_csv(os.path.join(cfg.main_folder, mode.upper(), 'still_gone_affected.csv'),
                         sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None,
                         line_terminator='\n')

def countOrganizationsTransitions(repos_list, output_file_name, mode):
    transitions_summary = pandas.DataFrame(columns=['Project', '#breaks', 'A_to_NC', 'NC_to_A', 'A_to_I', 'I_to_A', 'NC_to_I', 'I_to_NC', 'I_to_G', 'G_to_A', 'G_to_NC'])

    for gitRepoName in repos_list:
        organization, main_project = gitRepoName.split('/')
        workingFolder = os.path.join(cfg.main_folder, organization)

        # Transition occurrences
        repo_transitions = countTransitions(gitRepoName, workingFolder, mode)
        util.add(transitions_summary, repo_transitions)

    aggregated_row = ['Total']
    aggregated_row += transitions_summary.sum().tolist()[1:]
    util.add(transitions_summary, aggregated_row)

    transitions_summary.to_csv(os.path.join(cfg.main_folder, mode.upper(), output_file_name + '.csv'),
                               sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
    return transitions_summary

def countAffected(repo, workingFolder, mode):
    ''' Developers who have been inactive per organization '''
    org, repoName = repo.split('/')

    affected = [repo]

    main_repo_folder = os.path.join(cfg.main_folder, repo)
    commit_history_table = pandas.read_csv(main_repo_folder + '/' + cfg.commit_history_table_file_name, sep=cfg.CSV_separator)
    affected.append(len(commit_history_table))

    if mode.lower() == 'tf':
        core_devs = pandas.read_csv(os.path.join(cfg.TF_report_folder, repoName, cfg.TF_developers_file), sep=cfg.CSV_separator)
    elif mode.lower() == 'a80':
        core_devs = pandas.read_csv(os.path.join(cfg.A80_report_folder, repoName, cfg.A80_developers_file), sep=cfg.CSV_separator)
    elif mode.lower() == 'a80mod':
        core_devs = pandas.read_csv(os.path.join(cfg.A80mod_report_folder, repoName, cfg.A80mod_developers_file), sep=cfg.CSV_separator)
    else:  # elif mode.lower() == 'api':
        core_devs = pandas.read_csv(os.path.join(cfg.A80api_report_folder, repoName, cfg.A80api_developers_file), sep=cfg.CSV_separator)

    affected.append(len(core_devs))

    dev_breaks_folder = os.path.join(workingFolder, cfg.labeled_breaks_folder_name, mode.upper())
    non_coding = inactive = gone = still_gone = 0
    non_coding_affected = pandas.DataFrame(columns = ['repo','login'])
    inactive_affected = pandas.DataFrame(columns = ['repo','login'])
    gone_affected = pandas.DataFrame(columns = ['repo','login'])
    still_gone_affected = pandas.DataFrame(columns = ['repo','login'])
    for file in os.listdir(dev_breaks_folder):
        if os.path.isfile(dev_breaks_folder + '/' + file):
            dev = file.split('_')[0]
            dev_breaks = pandas.read_csv(dev_breaks_folder + '/' + file, sep = cfg.CSV_separator)
            if cfg.NC in dev_breaks.label.tolist() or cfg.NC + '(NOW)' in dev_breaks.label.tolist():
                non_coding += 1  # Can be removed, the count is the len(non_coding_affected)
                util.add(non_coding_affected, [repo, dev])
            if cfg.I in dev_breaks.label.tolist() or cfg.I + '(NOW)' in dev_breaks.label.tolist():
                inactive += 1  # Can be removed, the count is the len(inactive_affected)
                util.add(inactive_affected, [repo, dev])
            if cfg.G in dev_breaks.label.tolist() or cfg.G + '(NOW)' in dev_breaks.label.tolist():
                gone += 1  # Can be removed, the count is the len(gone_affected)
                util.add(gone_affected, [repo, dev])
            if cfg.G + '(NOW)' in dev_breaks.label.tolist():
                still_gone += 1  # Can be removed, the count is the len(gone_affected)
                util.add(still_gone_affected, [repo, dev])

    affected += [non_coding, inactive, gone, still_gone]

    return affected, non_coding_affected, inactive_affected, gone_affected, still_gone_affected

def countTransitions(repo, workingFolder, mode):
    ''' Needed to calculate the percentages for the markov chains '''
    transitions = [repo]

    org = repo.split('/')[0]
    dev_breaks_folder = os.path.join(workingFolder, cfg.labeled_breaks_folder_name, mode.upper())
    breaks = 0
    AtoNC = NCtoA = AtoI = ItoA = NCtoI = ItoNC = ItoG = GtoA = GtoNC = 0
    for file in os.listdir(dev_breaks_folder):
        if os.path.isfile(dev_breaks_folder + '/' + file):
            dev_breaks = pandas.read_csv(dev_breaks_folder + '/' + file, sep=cfg.CSV_separator)
            breaks += len(dev_breaks)
            AtoNC += len(dev_breaks[(dev_breaks.previously == cfg.A) & (dev_breaks.label == cfg.NC)])
            AtoNC += len(dev_breaks[(dev_breaks.previously == cfg.A) & (dev_breaks.label == cfg.NC + '(NOW)')])

            NCtoA += len(dev_breaks[(dev_breaks.previously == cfg.NC) & (dev_breaks.label == cfg.A)])

            AtoI += len(dev_breaks[(dev_breaks.previously == cfg.A) & (dev_breaks.label == cfg.I)])
            AtoI += len(dev_breaks[(dev_breaks.previously == cfg.A) & (dev_breaks.label == cfg.I + '(NOW)')])

            ItoA += len(dev_breaks[(dev_breaks.previously == cfg.I) & (dev_breaks.label == cfg.A)])

            NCtoI += len(dev_breaks[(dev_breaks.previously == cfg.NC) & (dev_breaks.label == cfg.I)])
            NCtoI += len(dev_breaks[(dev_breaks.previously == cfg.NC) & (dev_breaks.label == cfg.I + '(NOW)')])

            ItoNC += len(dev_breaks[(dev_breaks.previously == cfg.I) & (dev_breaks.label == cfg.NC)])
            ItoNC += len(dev_breaks[(dev_breaks.previously == cfg.I) & (dev_breaks.label == cfg.NC + '(NOW)')])

            GtoA += len(dev_breaks[(dev_breaks.previously == cfg.G) & (dev_breaks.label == cfg.A)])

            GtoNC += len(dev_breaks[(dev_breaks.previously == cfg.G) & (dev_breaks.label == cfg.NC)])
            GtoNC += len(dev_breaks[(dev_breaks.previously == cfg.G) & (dev_breaks.label == cfg.NC + '(NOW)')])

            ### ACTIVE -> GONE => ACTIVE -> INACTIVE -> GONE
            AtoI += len(dev_breaks[(dev_breaks.previously == cfg.A) & (dev_breaks.label == cfg.G)])
            AtoI += len(dev_breaks[(dev_breaks.previously == cfg.A) & (dev_breaks.label == cfg.G + '(NOW)')])
            ItoG += len(dev_breaks[(dev_breaks.previously == cfg.A) & (dev_breaks.label == cfg.G)])
            ItoG += len(dev_breaks[(dev_breaks.previously == cfg.A) & (dev_breaks.label == cfg.G + '(NOW)')])

            ### NON_CODING -> GONE => NON_CODING -> INACTIVE -> GONE
            NCtoI += len(dev_breaks[(dev_breaks.previously == cfg.NC) & (dev_breaks.label == cfg.G)])
            NCtoI += len(dev_breaks[(dev_breaks.previously == cfg.NC) & (dev_breaks.label == cfg.G + '(NOW)')])
            ItoG += len(dev_breaks[(dev_breaks.previously == cfg.NC) & (dev_breaks.label == cfg.G)])
            ItoG += len(dev_breaks[(dev_breaks.previously == cfg.NC) & (dev_breaks.label == cfg.G + '(NOW)')])

    transitions += [breaks, AtoNC, NCtoA, AtoI, ItoA, NCtoI, ItoNC, ItoG, GtoA, GtoNC]
    return transitions

def organizationsTransitionsPercentages(transitions_summary_file_name, output_file_name, mode):
    ''' Writes the chain table for each organization and returns the chains in a list needed to draw the markov chains '''
    labels = ['Project', 'A_to_A', 'A_to_NC', 'A_to_I',
              'NC_to_A', 'NC_to_NC', 'NC_to_I',
              'I_to_A', 'I_to_NC', 'I_to_I', 'I_to_G',
              'G_to_A', 'G_to_NC', 'G_to_G']
    chains_list = pandas.DataFrame(columns=labels)

    transitions_summary = pandas.read_csv(os.path.join(cfg.main_folder, mode.upper(), transitions_summary_file_name + '.csv'), sep=cfg.CSV_separator)

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

        destinationFolder = os.path.join(cfg.main_folder, cfg.chains_folder_name, mode.upper())
        os.makedirs(destinationFolder, exist_ok=True)

        util.add(chains_list, [proj['Project'], AtoA, AtoNC, AtoI,
                             NCtoA, NCtoNC, NCtoI,
                             ItoA, ItoNC, ItoI, ItoG,
                             GtoA, GtoNC, GtoG])

        organization = proj['Project'].split('/')[0]
        matrix.to_csv(os.path.join(destinationFolder, organization + '_markov.csv'),
                      sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')
    #Total_row = TotalTransitionsPercentages(transitions_summary)
    #util.add(chains_list, Total_row)
    last_row = ['AVG']
    last_row += chains_list[chains_list['Project'] != 'Total'].mean().tolist()
    print(chains_list, len(last_row), len(chains_list.columns), last_row)
    util.add(chains_list, last_row)
    chains_list.to_csv(os.path.join(cfg.main_folder, mode.upper(), output_file_name + '.csv'),
                       sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

def breaksDistributionStats(repos_list, output_file_name, mode):
    breaks_stats = pandas.DataFrame(columns=['Project', 'mean', 'st_dev', 'var', 'median', 'breaks_devlife_corr'])
    projects_counts = []
    for repo in repos_list:
        organization, project = repo.split('/')

        breaks_folder = os.path.join(cfg.main_folder, organization, cfg.labeled_breaks_folder_name, mode.upper())
        breaks_lifetime = pandas.DataFrame(columns=['BpY', 'life'])
        for file in os.listdir(breaks_folder):
            if(os.path.isfile(os.path.join(breaks_folder, file))):
                dev = file.split('_')[0]

                dev_life = getLife(dev, organization)
                if(dev_life<=1):
                    print('INVALID DEVELOPER LIFE:', dev)
                    continue

                breaks_list = pandas.read_csv(os.path.join(breaks_folder, file), sep=cfg.CSV_separator)
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

    breaks_stats.to_csv(os.path.join(cfg.main_folder, mode.upper(), output_file_name + '.csv'),
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

def try_or(fn, default):
    try:
        return fn()
    except OSError as err:
        print("OS error: {0}".format(err))
    except ValueError as err:
        print("Value error: {0}".format(err))
    except:
        return default

def breaksDurationsDescriptive(repos_list, output_file_name, mode):
    data = pandas.DataFrame(columns=['organization',
                                     'NC_min', 'NC_max', 'NC_avg', 'NC_StDev', 'NC_var', 'NC_Q1', 'NC_median', 'NC_Q3',
                                     'I_min', 'I_max', 'I_avg', 'I_StDev', 'I_var', 'I_Q1', 'I_median', 'I_Q3',
                                     'G_min', 'G_max', 'G_avg', 'G_StDev', 'G_var', 'G_Q1', 'G_median', 'G_Q3'])

    NC_all = []
    I_all = []
    G_all = []
    for repo in repos_list:
        organization, project = repo.split('/')

        breaks_folder = os.path.join(cfg.main_folder, organization, cfg.labeled_breaks_folder_name, mode.upper())
        NC_len_list = []
        I_len_list = []
        G_len_list = []
        for file in os.listdir(breaks_folder):
            if (os.path.isfile(os.path.join(breaks_folder, file))):
                dev_breaks = pandas.read_csv(os.path.join(breaks_folder, file), sep=cfg.CSV_separator)

                # Does not consider the (NOW)s because we don't know how long il will actually last
                NC_len_list += dev_breaks[dev_breaks.label == 'NON_CODING']['len'].tolist()
                I_len_list += dev_breaks[dev_breaks.label == 'INACTIVE']['len'].tolist()
                G_len_list += dev_breaks[dev_breaks.label == 'GONE']['len'].tolist()

        util.add(data, [organization,
                        min(NC_len_list) if len(NC_len_list) > 0 else 'NA',
                        max(NC_len_list) if len(NC_len_list) > 0 else 'NA',
                        numpy.mean(NC_len_list) if len(NC_len_list) > 0 else 'NA',
                        numpy.std(NC_len_list) if len(NC_len_list) > 0 else 'NA',
                        numpy.var(NC_len_list) if len(NC_len_list) > 0 else 'NA',
                        numpy.percentile(NC_len_list, 25) if len(NC_len_list) > 0 else 'NA',
                        numpy.median(NC_len_list) if len(NC_len_list) > 0 else 'NA',
                        numpy.percentile(NC_len_list, 75) if len(NC_len_list) > 0 else 'NA',
                        min(I_len_list) if len(I_len_list) > 0 else 'NA',
                        max(I_len_list) if len(I_len_list) > 0 else 'NA',
                        numpy.mean(I_len_list) if len(I_len_list) > 0 else 'NA',
                        numpy.std(I_len_list) if len(I_len_list) > 0 else 'NA',
                        numpy.var(I_len_list) if len(I_len_list) > 0 else 'NA',
                        numpy.percentile(I_len_list, 25) if len(I_len_list) > 0 else 'NA',
                        numpy.median(I_len_list) if len(I_len_list) > 0 else 'NA',
                        numpy.percentile(I_len_list, 75) if len(I_len_list) > 0 else 'NA',
                        min(G_len_list) if len(G_len_list) > 0 else 'NA',
                        max(G_len_list) if len(G_len_list) > 0 else 'NA',
                        numpy.mean(G_len_list) if len(G_len_list) > 0 else 'NA',
                        numpy.std(G_len_list) if len(G_len_list) > 0 else 'NA',
                        numpy.var(G_len_list) if len(G_len_list) > 0 else 'NA',
                        numpy.percentile(G_len_list, 25) if len(G_len_list) > 0 else 'NA',
                        numpy.median(G_len_list) if len(G_len_list) > 0 else 'NA',
                        numpy.percentile(G_len_list, 75) if len(G_len_list) > 0 else 'NA'])

        NC_all += NC_len_list
        I_all += I_len_list
        G_all += G_len_list

    util.add(data, ['Total',
                    min(NC_all) if len(NC_all) > 0 else 'NA',
                    max(NC_all) if len(NC_all) > 0 else 'NA',
                    numpy.mean(NC_all) if len(NC_all) > 0 else 'NA',
                    numpy.std(NC_all) if len(NC_all) > 0 else 'NA',
                    numpy.var(NC_all) if len(NC_all) > 0 else 'NA',
                    numpy.percentile(NC_all, 25) if len(NC_all) > 0 else 'NA',
                    numpy.median(NC_all) if len(NC_all) > 0 else 'NA',
                    numpy.percentile(NC_all, 75) if len(NC_all) > 0 else 'NA',
                    min(I_all) if len(I_all) > 0 else 'NA',
                    max(I_all) if len(I_all) > 0 else 'NA',
                    numpy.mean(I_all) if len(I_all) > 0 else 'NA',
                    numpy.std(I_all) if len(I_all) > 0 else 'NA',
                    numpy.var(I_all) if len(I_all) > 0 else 'NA',
                    numpy.percentile(I_all, 25) if len(I_all) > 0 else 'NA',
                    numpy.median(I_all) if len(I_all) > 0 else 'NA',
                    numpy.percentile(I_all, 75) if len(I_all) > 0 else 'NA',
                    min(G_all) if len(G_all) > 0 else 'NA',
                    max(G_all) if len(G_all) > 0 else 'NA',
                    numpy.mean(G_all) if len(G_all) > 0 else 'NA',
                    numpy.std(G_all) if len(G_all) > 0 else 'NA',
                    numpy.var(G_all) if len(G_all) > 0 else 'NA',
                    numpy.percentile(G_all, 25) if len(G_all) > 0 else 'NA',
                    numpy.median(G_all) if len(G_all) > 0 else 'NA',
                    numpy.percentile(G_all, 75) if len(G_all) > 0 else 'NA'])

    data.to_csv(os.path.join(cfg.main_folder, mode.upper(), output_file_name + '.csv'),
                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

def breaksOccurrencesDescriptive(repos_list, output_file_name, mode):
    data = pandas.DataFrame(columns=['organization',
                                     'NC_min', 'NC_max', 'NC_avg', 'NC_StDev', 'NC_var', 'NC_Q1', 'NC_median', 'NC_Q3',
                                     'I_min', 'I_max', 'I_avg', 'I_StDev', 'I_var', 'I_Q1', 'I_median', 'I_Q3',
                                     'G_min', 'G_max', 'G_avg', 'G_StDev', 'G_var', 'G_Q1', 'G_median', 'G_Q3'])

    NC_all = []
    I_all = []
    G_all = []
    for repo in repos_list:
        organization, project = repo.split('/')

        breaks_folder = os.path.join(cfg.main_folder, organization, cfg.labeled_breaks_folder_name, mode.upper())
        NC = []
        I = []
        G = []
        for file in os.listdir(breaks_folder):
            if (os.path.isfile(os.path.join(breaks_folder, file))):
                dev_breaks = pandas.read_csv(os.path.join(breaks_folder, file), sep=cfg.CSV_separator)

                # Does not consider the (NOW)s because we don't know how long il will actually last
                NC.append(len(dev_breaks[dev_breaks.label == 'NON_CODING']['len'].tolist()))
                I.append(len(dev_breaks[dev_breaks.label == 'INACTIVE']['len'].tolist()))
                G.append(len(dev_breaks[dev_breaks.label == 'GONE']['len'].tolist()))

        util.add(data, [organization,
                        min(NC) if len(NC) > 0 else 'NA',
                        max(NC) if len(NC) > 0 else 'NA',
                        numpy.mean(NC) if len(NC) > 0 else 'NA',
                        numpy.std(NC) if len(NC) > 0 else 'NA',
                        numpy.var(NC) if len(NC) > 0 else 'NA',
                        numpy.percentile(NC, 25) if len(NC) > 0 else 'NA',
                        numpy.median(NC) if len(NC) > 0 else 'NA',
                        numpy.percentile(NC, 75) if len(NC) > 0 else 'NA',
                        min(I) if len(I) > 0 else 'NA',
                        max(I) if len(I) > 0 else 'NA',
                        numpy.mean(I) if len(I) > 0 else 'NA',
                        numpy.std(I) if len(I) > 0 else 'NA',
                        numpy.var(I) if len(I) > 0 else 'NA',
                        numpy.percentile(I, 25) if len(I) > 0 else 'NA',
                        numpy.median(I) if len(I) > 0 else 'NA',
                        numpy.percentile(I, 75) if len(I) > 0 else 'NA',
                        min(G) if len(G) > 0 else 'NA',
                        max(G) if len(G) > 0 else 'NA',
                        numpy.mean(G) if len(G) > 0 else 'NA',
                        numpy.std(G) if len(G) > 0 else 'NA',
                        numpy.var(G) if len(G) > 0 else 'NA',
                        numpy.percentile(G, 25) if len(G) > 0 else 'NA',
                        numpy.median(G) if len(G) > 0 else 'NA',
                        numpy.percentile(G, 75) if len(G) > 0 else 'NA'])

        NC_all += NC
        I_all += I
        G_all += G

    util.add(data, ['Total',
                    min(NC_all) if len(NC_all) > 0 else 'NA',
                    max(NC_all) if len(NC_all) > 0 else 'NA',
                    numpy.mean(NC_all) if len(NC_all) > 0 else 'NA',
                    numpy.std(NC_all) if len(NC_all) > 0 else 'NA',
                    numpy.var(NC_all) if len(NC_all) > 0 else 'NA',
                    numpy.percentile(NC_all, 25) if len(NC_all) > 0 else 'NA',
                    numpy.median(NC_all) if len(NC_all) > 0 else 'NA',
                    numpy.percentile(NC_all, 75) if len(NC_all) > 0 else 'NA',
                    min(I_all) if len(I_all) > 0 else 'NA',
                    max(I_all) if len(I_all) > 0 else 'NA',
                    numpy.mean(I_all) if len(I_all) > 0 else 'NA',
                    numpy.std(I_all) if len(I_all) > 0 else 'NA',
                    numpy.var(I_all) if len(I_all) > 0 else 'NA',
                    numpy.percentile(I_all, 25) if len(I_all) > 0 else 'NA',
                    numpy.median(I_all) if len(I_all) > 0 else 'NA',
                    numpy.percentile(I_all, 75) if len(I_all) > 0 else 'NA',
                    min(G_all) if len(G_all) > 0 else 'NA',
                    max(G_all) if len(G_all) > 0 else 'NA',
                    numpy.mean(G_all) if len(G_all) > 0 else 'NA',
                    numpy.std(G_all) if len(G_all) > 0 else 'NA',
                    numpy.var(G_all) if len(G_all) > 0 else 'NA',
                    numpy.percentile(G_all, 25) if len(G_all) > 0 else 'NA',
                    numpy.median(G_all) if len(G_all) > 0 else 'NA',
                    numpy.percentile(G_all, 75) if len(G_all) > 0 else 'NA'])

    data.to_csv(os.path.join(cfg.main_folder, mode.upper(), output_file_name + '.csv'),
                        sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

def breaksDurationsPlot(repos_list, output_file_name, mode):
    data = pandas.DataFrame(columns=['organization', 'status', 'median_duration'])

### 1st ROUND OF REVIEWS: Sort the X axis by mean/median number of breaks/NC breaks ###

    # repos_list = sort_by_num_of_NC_breaks(repos_list, 'median')
    # repos_list = sort_by_num_of_breaks(repos_list, 'mean')
    repos_list = sort_by_num_of_NC_breaks_both(repos_list, 'median')

### END SORTING ###

    for repo in repos_list:
        organization, project = repo.split('/')

        breaks_folder = os.path.join(cfg.main_folder, organization, cfg.labeled_breaks_folder_name, mode.upper())
        NC_list = []
        I_list = []
        for file in os.listdir(breaks_folder):
            if (os.path.isfile(os.path.join(breaks_folder, file))):
                dev_breaks = pandas.read_csv(os.path.join(breaks_folder, file), sep=cfg.CSV_separator)

                # Does not consider the (NOW)s because we don't know how long il will actually last
                NC_list.append(dev_breaks[dev_breaks.label == 'NON_CODING'].len.mean())
                I_list.append(dev_breaks[dev_breaks.label == 'INACTIVE'].len.mean())

        for dev_avg in NC_list:
            util.add(data, [organization, 'non-coding', dev_avg])
        for dev_avg in I_list:
            util.add(data, [organization, 'inactive', dev_avg])

    data.to_csv(os.path.join(cfg.main_folder, mode.upper(), '_tmp_breaks_durations_data.csv'),
                   sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

    # print('S: ' + str(min(NC_list)) + ' - ' + str(max(NC_list)) + ' Avg: ' + str(numpy.mean(NC_list)))
    # print('H: ' + str(min(I_list)) + ' - ' + str(max(I_list)) + ' Avg: ' + str(numpy.mean(I_list)))

    plt.figure(figsize=(10, 8))
    pal = [sns.color_palette('Set1')[5], sns.color_palette('Set1')[8], sns.color_palette('Set1')[0]]
    sns_plot = sns.boxplot(x='organization', y='median_duration', hue="status", hue_order=['non-coding', 'inactive'],
                           data=data, palette=pal, linewidth=1, fliersize=1) # showmeans=True, meanprops={"marker":"o","markerfacecolor":"white", "markeredgecolor":"black","markersize":"5"}
    sns_plot.set_yscale('log')
    sns_plot.set_xticklabels(sns_plot.get_xticklabels(), rotation=20, horizontalalignment='right')
    sns_plot.get_figure().savefig(os.path.join(cfg.main_folder, mode.upper(), output_file_name), dpi=600)
    sns_plot.get_figure().clf()

    plt.figure(figsize=(12, 9))
    pal = [sns.color_palette('Set1')[5], sns.color_palette('Set1')[8], sns.color_palette('Set1')[0]]
    sns_plot = sns.boxplot(x='median_duration', y='organization', hue="status", hue_order=['non-coding', 'inactive'],
                           data=data, palette=pal, linewidth=1, fliersize=1)
    sns_plot.set_xscale('log')
    sns_plot.get_figure().savefig(os.path.join(cfg.main_folder, mode.upper(), output_file_name+'_H'), dpi=600)
    sns_plot.get_figure().clf()

def breaksDurationsPlotBoth(repos_list, output_file_name, mode):
    # same as breaksDurationsPlot but only takes devs who have been both non-coding and inactive

    data = pandas.DataFrame(columns=['organization', 'status', 'median_duration'])

### 1st ROUND OF REVIEWS: Sort the X axis by mean/median number of breaks/NC breaks ###

    #repos_list = sort_by_num_of_NC_breaks(repos_list, 'median')
    #repos_list = sort_by_num_of_breaks(repos_list, 'mean')
    repos_list = sort_by_num_of_NC_breaks_both(repos_list, 'median')

### END SORTING ###

    for repo in repos_list:
        organization, project = repo.split('/')

        breaks_folder = os.path.join(cfg.main_folder, organization, cfg.labeled_breaks_folder_name, mode.upper())
        NC_list = []
        I_list = []
        for file in os.listdir(breaks_folder):
            if (os.path.isfile(os.path.join(breaks_folder, file))):
                dev_breaks = pandas.read_csv(os.path.join(breaks_folder, file), sep=cfg.CSV_separator)

                current_dev_NC = dev_breaks[dev_breaks.label == 'NON_CODING']
                current_dev_I = dev_breaks[dev_breaks.label == 'INACTIVE']
                # Does not consider the (NOW)s because we don't know how long il will actually last

                if(not current_dev_NC.empty and not current_dev_I.empty):
                    NC_list.append(current_dev_NC.len.mean())
                    I_list.append(current_dev_I.len.mean())

        for dev_avg in NC_list:
            util.add(data, [organization, 'non-coding', dev_avg])
        for dev_avg in I_list:
            util.add(data, [organization, 'inactive', dev_avg])

    data.to_csv(os.path.join(cfg.main_folder, mode.upper(), '_tmp_breaks_durations_data.csv'),
                   sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

    print('S: ' + str(min(NC_list)) + ' - ' + str(max(NC_list)) + ' Avg: ' + str(numpy.mean(NC_list)))
    print('H: ' + str(min(I_list)) + ' - ' + str(max(I_list)) + ' Avg: ' + str(numpy.mean(I_list)))

    plt.figure(figsize=(10, 8))
    pal = [sns.color_palette('Set1')[5], sns.color_palette('Set1')[8], sns.color_palette('Set1')[0]]
    sns_plot = sns.boxplot(x='organization', y='median_duration', hue="status", hue_order=['non-coding', 'inactive'], data=data, palette=pal, linewidth=1, fliersize=1)
    sns_plot.set_yscale('log')
    sns_plot.set_xticklabels(sns_plot.get_xticklabels(), rotation=20, horizontalalignment='right')
    sns_plot.get_figure().savefig(os.path.join(cfg.main_folder, mode.upper(), output_file_name), dpi=600)
    sns_plot.get_figure().clf()

    plt.figure(figsize=(12, 9))
    pal = [sns.color_palette('Set1')[5], sns.color_palette('Set1')[8], sns.color_palette('Set1')[0]]
    sns_plot = sns.boxplot(x='median_duration', y='organization', hue="status", hue_order=['non-coding', 'inactive'],
                           data=data, palette=pal, linewidth=1, fliersize=1)
    sns_plot.set_xscale('log')
    sns_plot.get_figure().savefig(os.path.join(cfg.main_folder, mode.upper(), output_file_name+'_H'), dpi=600)
    sns_plot.get_figure().clf()

def breaksOccurrencesPlotNotNormalized(repos_list, output_file_name, mode):
    dataframes = []
    for repo in repos_list:
        organization, project = repo.split('/')

        labels = ['dev', 'organization', 'NCs', 'Is', 'Gs']
        inactivities_df = pandas.DataFrame(columns=labels)

        breaks_folder = os.path.join(cfg.main_folder, organization, cfg.labeled_breaks_folder_name, mode.upper())
        for file in os.listdir(breaks_folder):
            if (os.path.isfile(os.path.join(breaks_folder, file))):
                dev = file.split('_')[0]

                breaks_list = pandas.read_csv(os.path.join(breaks_folder, file), sep=cfg.CSV_separator)

                NCs = len(breaks_list[breaks_list.label == 'NON_CODING'])

                Is = len(breaks_list[breaks_list.label == 'INACTIVE'])

                Gs = len(breaks_list[breaks_list.label == 'GONE'])

                util.add(inactivities_df, [dev, organization, NCs, Is, Gs])
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

    data.to_csv(os.path.join(cfg.main_folder, mode.upper(), '_tmp_breaks_occurrences_not_normalized_data.csv'),
                   sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

    plt.figure(figsize=(10, 8))
    pal = [sns.color_palette('Set1')[5], sns.color_palette('Set1')[8], sns.color_palette('Set1')[0]]
    sns_plot = sns.boxplot(x='organization', y='occurrences', hue="status", hue_order=['non-coding', 'inactive', 'gone'],
                           data=data, palette=pal, linewidth=1, fliersize=1)
    # sns_plot.set_yscale('log')
    # sns_plot.set(ylim=(0, 20))
    sns_plot.set_xticklabels(sns_plot.get_xticklabels(), rotation=20, horizontalalignment='right')
    sns_plot.get_figure().savefig(os.path.join(cfg.main_folder, mode.upper(), output_file_name), dpi=600)
    sns_plot.get_figure().clf()

    plt.figure(figsize=(12, 9))
    pal = [sns.color_palette('Set1')[5], sns.color_palette('Set1')[8], sns.color_palette('Set1')[0]]
    sns_plot = sns.boxplot(x='occurrences', y='organization', hue="status",
                           hue_order=['non-coding', 'inactive', 'gone'],
                           data=data, palette=pal, linewidth=1, fliersize=1, orient="h")
    # sns_plot.set_yscale('log')
    # sns_plot.set(ylim=(0, 20))
    # sns_plot.set_xticklabels(sns_plot.get_xticklabels(), rotation=20, horizontalalignment='right')
    sns_plot.get_figure().savefig(os.path.join(cfg.main_folder, mode.upper(), output_file_name+'_H'), dpi=600)
    sns_plot.get_figure().clf()

def breaksOccurrencesPlot(repos_list, output_file_name, mode):
    dataframes = []
    for repo in repos_list:
        organization, project = repo.split('/')

        labels = ['dev', 'organization', 'NCs', 'Is', 'Gs']
        inactivities_df = pandas.DataFrame(columns=labels)

        breaks_folder = os.path.join(cfg.main_folder, organization, cfg.labeled_breaks_folder_name, mode.upper())
        for file in os.listdir(breaks_folder):
            if (os.path.isfile(os.path.join(breaks_folder, file))):
                dev = file.split('_')[0]

                dev_life = getLife(dev, organization)
                if (dev_life <= 1):
                    print('INVALID DEVELOPER LIFE:', dev)
                    continue

                dev_years = dev_life / 365

                breaks_list = pandas.read_csv(os.path.join(breaks_folder, file), sep=cfg.CSV_separator)

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

    data.to_csv(os.path.join(cfg.main_folder, mode.upper(), '_tmp_breaks_occurrences_data.csv'),
                   sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

    plt.figure(figsize=(10, 8))
    pal = [sns.color_palette('Set1')[5], sns.color_palette('Set1')[8], sns.color_palette('Set1')[0]]
    sns_plot = sns.boxplot(x='organization', y='occurrences', hue="status", hue_order=['non-coding', 'inactive', 'gone'],
                           data=data, palette=pal, linewidth=1, fliersize=1)
    # sns_plot.set_yscale('log')
    # sns_plot.set(ylim=(0, 50))
    sns_plot.set_xticklabels(sns_plot.get_xticklabels(), rotation=20, horizontalalignment='right')
    sns_plot.get_figure().savefig(os.path.join(cfg.main_folder, mode.upper(), output_file_name), dpi=600)
    sns_plot.get_figure().clf()


def meanDifferenceTest(repos_list, output_file_name, mode):
    data = pandas.DataFrame(columns=['project', 'non_coding', 'inactive', 'both', 'w', 'p', 'Cliff d', 'effect size',
                                     'GRB'])
    pvals = list()
    rcompanion = importr('rcompanion')
    for repo in repos_list:
        organization, project = repo.split('/')

        breaks_folder = os.path.join(cfg.main_folder, organization, cfg.labeled_breaks_folder_name, mode.upper())
        NC_avgs = pandas.DataFrame(columns=['dev', 'avg_duration'])
        I_avgs = pandas.DataFrame(columns=['dev', 'avg_duration'])
        for file in os.listdir(breaks_folder):
            if (os.path.isfile(os.path.join(breaks_folder, file))):
                dev = file.split('_')[0]
                dev_breaks = pandas.read_csv(os.path.join(breaks_folder, file), sep=cfg.CSV_separator)

                NC_dev_avg = dev_breaks[dev_breaks.label == 'NON_CODING']['len'].mean()
                if NC_dev_avg > 0:
                    util.add(NC_avgs, [dev, NC_dev_avg])

                I_dev_avg = dev_breaks[dev_breaks.label == 'INACTIVE']['len'].mean()
                if I_dev_avg > 0:
                    util.add(I_avgs, [dev, I_dev_avg])

        NC_devs = len(NC_avgs)
        I_devs = len(I_avgs)

        common = list(set(NC_avgs['dev'].tolist()).intersection(set(I_avgs['dev'].tolist())))
        common_devs = len(common)

        common_df = pandas.merge(NC_avgs, I_avgs, how='inner', on=['dev'])
        NC_common_list = common_df['avg_duration_x'].tolist()
        I_common_list = common_df['avg_duration_y'].tolist()

        ### MAKE TEST
        try:
            w_val, w_p = scipy.stats.wilcoxon(NC_common_list, I_common_list, correction = True)
            d, size = effectsize.cliffsDelta(NC_common_list, I_common_list)
            Y = robjects.FloatVector(NC_common_list + I_common_list)
            nc_factor = ['Non coding'] * len(NC_common_list)
            i_factor = ['Inactive'] * len(I_common_list)
            Group = robjects.FactorVector(nc_factor + i_factor)
            # https://rdrr.io/cran/rcompanion/man/wilcoxonRG.html
            grb = rcompanion.wilcoxonRG(x=Y, g=Group)
            grb = str(grb).strip().split('\n')[1]
        except:
            print('{} W not available. NC: {}, I: {}, Common: {}'.format(project, NC_devs, I_devs, common_devs))
            w_val = d = size = None
            w_p = 1
        pvals.append(w_p)

        ### ADD RESULTING ROW TO data
        util.add(data, [project, NC_devs, I_devs, common_devs, w_val, w_p, d, size, grb])

    reject, adjp, _, _ = sm.stats.multipletests(pvals, alpha=0.05, method='holm', is_sorted=False, returnsorted=False)
    data = data.assign(adjusted_p = adjp)
    data = data.assign(sig=reject)

    data.to_csv(os.path.join(cfg.main_folder, mode.upper(), output_file_name+'.csv'),
                sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

def TotalTransitionsPercentages(transitions_summary):
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

    row = ['Total', AtoA, AtoNC, AtoI, NCtoA, NCtoNC, NCtoI, ItoA, ItoNC, ItoI, ItoG, GtoA, GtoNC, GtoG]
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
                if (dev_life <= 1):
                    print('INVALID DEVELOPER LIFE:', dev)
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
                           data=data, palette=pal, linewidth=1, fliersize=1)
    # sns_plot.set_yscale('log')
    # sns_plot.set(ylim=(0, 10))
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
    sns_plot = sns.boxplot(x='project', y='average_duration', hue="status", hue_order=['non-coding', 'inactive'], data=data, palette=pal, linewidth=1, fliersize=1)
    sns_plot.set_yscale('log')
    sns_plot.set_xticklabels(sns_plot.get_xticklabels())
    sns_plot.get_figure().savefig(cfg.main_folder + '/' + output_file_name, dpi=600)
    sns_plot.get_figure().clf()

def writeDevslist(mode, repos_list):
    allDevs = pandas.DataFrame(columns = ['login', 'project'])
    output_folder = '.'

    for repo in repos_list:
        organization, repoName = repo.split('/')

        if mode.lower() == 'tf':
            repo_devs = pandas.read_csv(os.path.join(cfg.TF_report_folder, repoName, cfg.TF_developers_file), sep=cfg.CSV_separator)
            output_folder = cfg.TF_report_folder
        elif mode.lower() == 'a80':
            repo_devs = pandas.read_csv(os.path.join(cfg.A80_report_folder, repoName, cfg.A80_developers_file), sep=cfg.CSV_separator)
            output_folder = cfg.A80_report_folder
        elif mode.lower() == 'a80mod':
            repo_devs = pandas.read_csv(os.path.join(cfg.A80mod_report_folder, repoName, cfg.A80mod_developers_file), sep=cfg.CSV_separator)
            output_folder = cfg.A80mod_report_folder
        else:  # elif mode.lower() == 'a80api':
            repo_devs = pandas.read_csv(os.path.join(cfg.A80api_report_folder, repoName, cfg.A80api_developers_file), sep=cfg.CSV_separator)
            output_folder = cfg.A80api_report_folder

        for i, d in repo_devs.iterrows():
            util.add(allDevs, [d['login'], repo])

    allDevs.to_csv(os.path.join(output_folder, 'devs_full_list.csv'),
                   sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

def main(repos_list, mode):
    ''' MAIN FUNCTION '''
    transitions_summary_file_name = 'transitionsSummary'

    writeDevslist(mode, repos_list)

    outputFolder = os.path.join(cfg.main_folder, mode.upper())
    os.makedirs(outputFolder, exist_ok=True)

#    countOrganizationsAffected(repos_list, 'affectedSummary', mode)
#    countOrganizationsTransitions(repos_list, transitions_summary_file_name, mode)
#    organizationsTransitionsPercentages(transitions_summary_file_name, 'organizations_chains_list', mode)

#    breaksDistributionStats(repos_list, 'BreaksDistributions', mode)
    test_breaks_duration_normality(repos_list, 'BreaksDurationNormalityTest', mode)
#    breaksOccurrencesPlot(reversed(repos_list), 'BreaksOccurrences', mode)
#    breaksOccurrencesPlotNotNormalized(reversed(repos_list), 'BreaksOccurrencesNotNormalized', mode)
#    breaksDurationsPlot(reversed(repos_list), 'DurationsDistributions', mode)
#    breaksDurationsPlotBoth(reversed(repos_list), 'DurationsDistributionsBoth', mode)
#    breaksDurationsDescriptive(reversed(repos_list), 'DurationsDescriptiveStats', mode)
#    breaksOccurrencesDescriptive(reversed(repos_list), 'OccurrencesDescriptiveStats', mode)

#    meanDifferenceTest(repos_list, 'WilcoxonPairedMeanTest', mode)

    #TFsBreaksOccurrencesPlot(repos_list, 'TFsBreaksOccurrences')
    #TFsBreaksDurationsPlot(repos_list, 'TFsDurationsDistributions')

    #util.makeMeanDiffTests(organizations, main_path)

    print("That's it, man!")

### 1st ROUND OF REVIEWS ###
#Figure Sorting

def sort_by_num_of_breaks(repos_list, metric):
### Sort the list by Mean Number of Breaks
    repos_dict = {}
    for repo in repos_list:
        organization, project = repo.split('/')
        breaks_folder = os.path.join(cfg.main_folder, organization, cfg.labeled_breaks_folder_name, mode.upper())
        breaks_list = []
        for file in os.listdir(breaks_folder):
            if (os.path.isfile(os.path.join(breaks_folder, file))):
                dev_breaks = pandas.read_csv(os.path.join(breaks_folder, file), sep=cfg.CSV_separator)

                #Does not consider the (NOW)s because we don't know how long il will actually last
                breaks_list.append(dev_breaks[dev_breaks.label == 'ACTIVE'].len.mean())
        if metric == 'median':
            repos_dict[repo] = numpy.nanmedian(breaks_list)
        else:
            repos_dict[repo] = numpy.nanmean(breaks_list)

    return {k: v for k, v in sorted(repos_dict.items(), key=lambda item: item[1])}.keys()

def sort_by_num_of_NC_breaks(repos_list, metric):
### Sort the list by Mean Number of Breaks
    repos_dict = {}
    for repo in repos_list:
        organization, project = repo.split('/')
        breaks_folder = os.path.join(cfg.main_folder, organization, cfg.labeled_breaks_folder_name, mode.upper())
        NC_list = []
        for file in os.listdir(breaks_folder):
            if (os.path.isfile(os.path.join(breaks_folder, file))):
                dev_breaks = pandas.read_csv(os.path.join(breaks_folder, file), sep=cfg.CSV_separator)

                #Does not consider the (NOW)s because we don't know how long il will actually last
                NC_list.append(dev_breaks[dev_breaks.label == 'NON_CODING'].len.mean())
        if metric == 'median':
            repos_dict[repo] = numpy.nanmedian(NC_list)
        else:
            repos_dict[repo] = numpy.nanmean(NC_list)
    return {k: v for k, v in sorted(repos_dict.items(), key=lambda item: item[1])}.keys()

def sort_by_num_of_NC_breaks_both(repos_list, mode):
### Sort the list by Median Number of Breaks
    repos_dict = {}
    for repo in repos_list:
        organization, project = repo.split('/')
        breaks_folder = os.path.join(cfg.main_folder, organization, cfg.labeled_breaks_folder_name, mode.upper())
        NC_list = []
        I_list = []
        for file in os.listdir(breaks_folder):
            if (os.path.isfile(os.path.join(breaks_folder, file))):
                dev_breaks = pandas.read_csv(os.path.join(breaks_folder, file), sep=cfg.CSV_separator)

                current_dev_NC = dev_breaks[dev_breaks.label == 'NON_CODING']
                current_dev_I = dev_breaks[dev_breaks.label == 'INACTIVE']
                # Does not consider the (NOW)s because we don't know how long il will actually last
                if (not current_dev_NC.empty and not current_dev_I.empty):
                    NC_list.append(current_dev_NC.len.mean())
                    I_list.append(current_dev_I.len.mean())

                #Does not consider the (NOW)s because we don't know how long il will actually last
                NC_list.append(dev_breaks[dev_breaks.label == 'NON_CODING'].len.mean())
        repos_dict[repo] = numpy.nanmedian(NC_list)
    return {k: v for k, v in sorted(repos_dict.items(), key=lambda item: item[1])}.keys()

def sort_by_number_of_contributors(repos_list, mode):
### Sort the list by Median Number of Breaks
    repos_dict = {}
    for repo in repos_list:
        organization, project = repo.split('/')
        breaks_folder = os.path.join(cfg.main_folder, organization, cfg.labeled_breaks_folder_name, mode.upper())
        num_NC_list = []
        for file in os.listdir(breaks_folder):
            if (os.path.isfile(os.path.join(breaks_folder, file))):
                dev_breaks = pandas.read_csv(os.path.join(breaks_folder, file), sep=cfg.CSV_separator)

                #Does not consider the (NOW)s because we don't know how long il will actually last
                num_NC_list.append(len(dev_breaks[dev_breaks.label == 'NON_CODING']))
        repos_dict[repo] = numpy.median(num_NC_list)
    return {k: v for k, v in sorted(repos_dict.items(), key=lambda item: item[1])}.keys()

def test_breaks_duration_normality(repos_list, output_file_name, mode):
## Test if the breaks duration is normally distributed
    data_table = pandas.DataFrame(columns=['repo', '#breaks', '#NC', '#I',
                                           'sw_tot', 'p_sw_tot', 'sw_NC', 'p_sw_NC', 'sw_I', 'p_sw_I',
                                           'dag_tot', 'p_dag_tot', 'dag_NC', 'p_dag_NC', 'dag_I', 'p_dag_I',
                                           'chi_tot', 'p_chi_tot', 'chi_NC', 'p_chi_NC', 'chi_I', 'p_chi_I',
                                           'ks_tot', 'p_ks_tot', 'ks_NC', 'p_ks_NC', 'ks_I', 'p_ks_I',
                                           'lil_tot', 'p_lil_tot', 'lil_NC', 'p_lil_NC', 'lil_I', 'p_lil_I'])
    all_NC_list = []
    all_I_list = []
    all_durations_list = []

    for repo in repos_list:
        organization, project = repo.split('/')
        breaks_folder = os.path.join(cfg.main_folder, organization, cfg.labeled_breaks_folder_name, mode.upper())
        NC_list = []
        I_list = []
        G_list = []
        breaks_durations_list = []

        for file in os.listdir(breaks_folder):
            if (os.path.isfile(os.path.join(breaks_folder, file))):
                dev_breaks = pandas.read_csv(os.path.join(breaks_folder, file), sep=cfg.CSV_separator)

                #Does not consider the (NOW)s because we don't know how long il will actually last
                NC_list += dev_breaks[dev_breaks.label == 'NON_CODING'].len.tolist()
                I_list += dev_breaks[dev_breaks.label == 'INACTIVE'].len.tolist()
                G_list += dev_breaks[dev_breaks.label == 'GONE'].len.tolist()
        breaks_durations_list += NC_list + I_list + G_list

        all_NC_list += NC_list
        all_I_list += I_list
        all_durations_list += breaks_durations_list

        # Shapiro-Wilk Test
        from scipy.stats import shapiro
        try:
            sw_tot, p_sw_tot = shapiro(breaks_durations_list)
        except:
            sw_tot, p_sw_tot = 'NA', 'NA'
        try:
            sw_NC, p_sw_NC = shapiro(NC_list)
        except:
            sw_NC, p_sw_NC = 'NA', 'NA'
        try:
            sw_I, p_sw_I = shapiro(I_list)
        except:
            sw_I, p_sw_I = 'NA', 'NA'

        # D’Agostino’s K^2 Test
        from scipy.stats import normaltest
        try:
            dag_tot, p_dag_tot = normaltest(breaks_durations_list)
        except:
            dag_tot, p_dag_tot = 'NA', 'NA'
        try:
            dag_NC, p_dag_NC = normaltest(NC_list)
        except:
            dag_NC, p_dag_NC = 'NA', 'NA'
        try:
            dag_I, p_dag_I = normaltest(I_list)
        except:
            dag_I, p_dag_I = 'NA', 'NA'

        # Chi-Square Normality Test
        from scipy.stats import chisquare
        try:
            chi_tot, p_chi_tot = chisquare(breaks_durations_list)
        except:
            chi_tot, p_chi_tot = 'NA', 'NA'
        try:
            chi_NC, p_chi_NC = chisquare(NC_list)
        except:
            chi_NC, p_chi_NC = 'NA', 'NA'
        try:
            chi_I, p_chi_I = chisquare(I_list)
        except:
            chi_I, p_chi_I = 'NA', 'NA'

        # Kolmogorov-Smirnov Test
        from scipy.stats import kstest
        try:
            ks_tot, p_ks_tot = kstest(breaks_durations_list, 'norm')
        except:
            ks_tot, p_ks_tot = 'NA', 'NA'
        try:
            ks_NC, p_ks_NC = kstest(NC_list, 'norm')
        except:
            ks_NC, p_ks_NC = 'NA', 'NA'
        try:
            ks_I, p_ks_I = kstest(I_list, 'norm')
        except:
            ks_I, p_ks_I = 'NA', 'NA'

        # Lilliefors Test
        from statsmodels.stats.diagnostic import lilliefors
        try:
            lil_tot, p_lil_tot = lilliefors(breaks_durations_list)
        except:
            lil_tot, p_lil_tot = 'NA', 'NA'
        try:
            lil_NC, p_lil_NC = lilliefors(NC_list)
        except:
            lil_NC, p_lil_NC = 'NA', 'NA'
        try:
            lil_I, p_lil_I = lilliefors(I_list)
        except:
            lil_I, p_lil_I = 'NA', 'NA'

        # Anderson-Darling Test (Returns a list of critical-values instead of a single p-value)
        # from scipy.stats import anderson
        # ad_tot, p_ad_tot = anderson(num_breaks_list)
        # ad_NC, p_ad_NC = anderson(num_NC_list)
        # ad_I, p_ad_I = anderson(num_I_list)

        util.add(data_table, [repo, len(breaks_durations_list), len(NC_list), len(I_list),
                              sw_tot, p_sw_tot, sw_NC, p_sw_NC, sw_I, p_sw_I,
                              dag_tot, p_dag_tot, dag_NC, p_dag_NC, dag_I, p_dag_I,
                              chi_tot, p_chi_tot, chi_NC, p_chi_NC, chi_I, p_chi_I,
                              ks_tot, p_ks_tot, ks_NC, p_ks_NC, ks_I, p_ks_I,
                              lil_tot, p_lil_tot, lil_NC, p_lil_NC, lil_I, p_lil_I])

    ### Run Test on ALL the BREAKS
    # Shapiro-Wilk Test
    from scipy.stats import shapiro
    try:
        sw_all, p_sw_all = shapiro(all_durations_list)
    except:
        sw_all, p_sw_all = 'NA', 'NA'
    try:
        sw_all_NC, p_sw_all_NC = shapiro(all_NC_list)
    except:
        sw_all_NC, p_sw_all_NC = 'NA', 'NA'
    try:
        sw_all_I, p_sw_all_I = shapiro(all_I_list)
    except:
        sw_all_I, p_sw_all_I = 'NA', 'NA'

    # D’Agostino’s K^2 Test
    from scipy.stats import normaltest
    try:
        dag_all, p_dag_all = normaltest(all_durations_list)
    except:
        dag_all, p_dag_all = 'NA', 'NA'
    try:
        dag_all_NC, p_dag_all_NC = normaltest(all_NC_list)
    except:
        dag_all_NC, p_dag_all_NC = 'NA', 'NA'
    try:
        dag_all_I, p_dag_all_I = normaltest(all_I_list)
    except:
        dag_all_I, p_dag_all_I = 'NA', 'NA'

    # Chi-Square Normality Test
    from scipy.stats import chisquare
    try:
        chi_all, p_chi_all = chisquare(all_durations_list)
    except:
        chi_all, p_chi_all = 'NA', 'NA'
    try:
        chi_all_NC, p_chi_all_NC = chisquare(all_NC_list)
    except:
        chi_all_NC, p_chi_all_NC = 'NA', 'NA'
    try:
        chi_all_I, p_chi_all_I = chisquare(all_I_list)
    except:
        chi_all_I, p_chi_all_I = 'NA', 'NA'

    # Kolmogorov-Smirnov Test
    from scipy.stats import kstest
    try:
        ks_all, p_ks_all = kstest(all_durations_list, 'norm')
    except:
        ks_all, p_ks_all = 'NA', 'NA'
    try:
        ks_all_NC, p_ks_all_NC = kstest(all_NC_list, 'norm')
    except:
        ks_all_NC, p_ks_all_NC = 'NA', 'NA'
    try:
        ks_all_I, p_ks_all_I = kstest(all_I_list, 'norm')
    except:
        ks_all_I, p_ks_all_I = 'NA', 'NA'

    # Lilliefors Test
    from statsmodels.stats.diagnostic import lilliefors
    try:
        lil_all, p_lil_all = lilliefors(all_durations_list)
    except:
        lil_all, p_lil_all = 'NA', 'NA'
    try:
        lil_all_NC, p_lil_all_NC = lilliefors(all_NC_list)
    except:
        lil_all_NC, p_lil_all_NC = 'NA', 'NA'
    try:
        lil_all_I, p_lil_all_I = lilliefors(all_I_list)
    except:
        lil_all_I, p_lil_all_I = 'NA', 'NA'

    util.add(data_table, ['Total', len(all_durations_list), len(all_NC_list), len(all_I_list),
                          sw_all, p_sw_all, sw_all_NC, p_sw_all_NC, sw_all_I, p_sw_all_I,
                          dag_all, p_dag_all, dag_all_NC, p_dag_all_NC, dag_all_I, p_dag_all_I,
                          chi_all, p_chi_all, chi_all_NC, p_chi_all_NC, chi_all_I, p_chi_all_I,
                          ks_all, p_ks_all, ks_all_NC, p_ks_all_NC, ks_all_I, p_ks_all_I,
                          lil_all, p_lil_all, lil_all_NC, p_lil_all_NC, lil_all_I, p_lil_all_I])

    data_table.to_csv(os.path.join(cfg.main_folder, mode.upper(), output_file_name+'.csv'),
               sep=cfg.CSV_separator, na_rep=cfg.CSV_missing, index=False, quoting=None, line_terminator='\n')

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    ### ARGUMENTS MANAGEMENT
    # python script.py gitCloneURL
    # A80api
    print('Arguments: {} --> {}'.format(len(sys.argv), str(sys.argv)))
    mode = sys.argv[1]
    if mode.lower() not in cfg.supported_modes:
        print('ERROR: Not valid mode! ({})'.format(cfg.supported_modes))
        sys.exit(0)
    print('Selected Mode: ', mode.upper())

    repos_list=util.getReposList()
    main(repos_list, mode)

