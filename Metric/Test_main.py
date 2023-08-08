import APImanager
import CSVmanager

if __name__ == "__main__":
    csv = CSVmanager.CSVmanager("atom", "atom", "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")
    prova = APImanager.APImanager("atom", "atom", "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", csv)

    commit_list = csv.read_commit_list()
    start = commit_list[0]
    end = commit_list[-1]
    print(prova.get_creation_date())
    print(start)
    print(end)
    