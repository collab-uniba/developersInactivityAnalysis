import CSVmanager
import sys

if __name__ == "__main__":

    print('Arguments: {} --> {}'.format(len(sys.argv), str(sys.argv)))
    owner = sys.argv[1]
    repository = sys.argv[2]
    token = sys.argv[3]
    csv_manager = CSVmanager.CSVmanager(owner, repository, token)
    csv_manager.create_PRS_file()