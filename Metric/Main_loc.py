
import CSVmanager
import sys

if __name__ == "__main__":
    
    print('Arguments: {} --> {}'.format(len(sys.argv), str(sys.argv)))
    owner = sys.argv[1]
    repository = sys.argv[2]
    token = sys.argv[3]
    csv = CSVmanager.CSVmanager(owner, repository, token)
    csv.create_LOC_values()