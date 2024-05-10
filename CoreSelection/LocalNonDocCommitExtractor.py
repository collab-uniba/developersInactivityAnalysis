import sys
import os
import pandas
import git
import classifier

def add(dataframe, row):
    """Adds a row to the tail of a dataframe"""
    dataframe.loc[-1] = row  # adding a row
    dataframe.index = dataframe.index + 1  # shifting index
    dataframe.sort_index(inplace=True)
    dataframe.iloc[::-1]

### MAIN FUNCTION
def main(gitRepoURL):
    # TODO: move this to the Settings.py file
    reposDirectory = '../Local_Repositories'
    os.makedirs(reposDirectory, exist_ok=True)

    # Clone Repo Locally
    try:
        git.Git(reposDirectory).clone(gitRepoURL)
        print('Clone Complete: ', gitRepoURL)
    except:
        print('Warning: clone Failed! Probably repo already exists: trying to pull.')
        try:
            git.Git(reposDirectory).pull()
            print('Pull Complete: ', gitRepoURL)
        except:
            print('Error: pull Failed! Exiting.')
            sys.exit(1)

    repoName = gitRepoURL.split('/')[-1].split('.')[0]
    if(repoName=='Babylon'):
        repoName='Babylon.js'
    repoDir = os.path.join(reposDirectory, repoName)

    # Init
    # TODO: ./A80_Results/ should be a parameter
    outputDirectory = '../A80_Results/' + repoName
    os.makedirs(outputDirectory, exist_ok=True)

    contributions_destination = os.path.join(outputDirectory, 'commits.csv')
    aggregated_contributions_destination = os.path.join(outputDirectory, 'Cstats.csv')
    contributions = pandas.DataFrame(columns = ['name', 'email', 'date', 'sha'])
    repo = git.Repo(repoDir)

    basic_classifier = classifier.BasicFileTypeClassifier()

    try:
        contributions = pandas.read_csv(contributions_destination, sep=';')
        print('Contributions file ALREADY EXISTS, SKIP calculation!')
    except:
        print('Contributions file not found, STARTING calculation!')
        # Get Commit List
        commits_list = list(repo.iter_commits())
        commits_count = len(commits_list)
        print('Commits: ', commits_count)

        # Select NON-DOC Commits
        Tstatus=5
        for i in range(0, commits_count - 1):
            author_name = commits_list[i].author.name
            author_email = commits_list[i].author.email
            commit_date = commits_list[i].committed_datetime
            commit_sha = commits_list[i].hexsha

            for file in commits_list[i].diff(commits_list[i + 1]):
                file_path = file.a_path
                # Check Type
                label = basic_classifier.labelFile(file_path)
                if label!=basic_classifier.DOC: # There is at least 1 non-DOC file changed
                    add(contributions, [author_name, author_email, commit_date, commit_sha])
                    break

            ### LOGGING
            perc = int(i/commits_count*100)
            if perc == Tstatus:
                print('Commit filtered {}%'.format(perc))
                Tstatus += 5

        contributions['email'] = contributions['email'].str.lower()
        contributions['name'] = contributions['name'].str.lower()
        contributions.to_csv(contributions_destination,
                             sep=';', na_rep='N/A', index=False, quoting=None, lineterminator='\n')
        print('Contributions Written: ', contributions_destination)
        pass

    grouped_contributions = contributions.groupby(['name', 'email']).count()
    grouped_contributions = grouped_contributions.drop(columns=['date'])
    grouped_contributions = grouped_contributions.rename(columns={'sha': 'commits'})
    grouped_contributions.to_csv(aggregated_contributions_destination,
                                 sep=';', na_rep='N/A', index=True, quoting=None, lineterminator='\n')
    print('Grouped Contributions Written: ', aggregated_contributions_destination)

    #shutil.rmtree(repoDir)
    #print('Local Repository REMOVED')

if __name__ == "__main__":
    THIS_FOLDER = os.path.dirname(os.path.abspath(__file__))
    os.chdir(THIS_FOLDER)

    ### ARGUMENTS MANAGEMENT

    print('Arguments: {} --> {}'.format(len(sys.argv), str(sys.argv)))
    try:
        # sys.argv[1] is the file containing the list of Git repositories
        # read the file and process each line
        with open(sys.argv[1], 'r') as file:
            for line in file:
                gitRepoURL = line.strip()
                main(gitRepoURL)
    except IndexError:
        print("Error: No parameters provided. Please provide a file with one Git repository URL per line.")
        sys.exit(1)
