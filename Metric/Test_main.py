import APImanager
import CSVmanager

if __name__ == "__main__":
    csv = CSVmanager.CSVmanager("atom", "atom", "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")
    prova = APImanager.APImanager("atom", "atom", "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", csv)

    print(prova.get_creation_date())
    print(prova.get_main_language())
    