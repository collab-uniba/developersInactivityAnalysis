import CSVmanager

if __name__ == "__main__":
    prova = CSVmanager.CSVmanager("atom", "atom", "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")
    commit_list = prova.read_commit_list()


    print(len(commit_list))