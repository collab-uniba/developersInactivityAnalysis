import CSVmanager
import SystemPath

if __name__ == "__main__":
    LOC_list = CSVmanager.generate_repositories_LOC_TF()
    CSVmanager.save_data_for_loc(LOC_list, SystemPath.get_path_repositories_LOC_TF())
    LOC_list = CSVmanager.generate_repositories_LOC_TF_gone()
    CSVmanager.save_data_for_loc(LOC_list, SystemPath.get_path_repositories_LOC_TF_gone())
    LOC_list = CSVmanager.generate_repositories_LOC_core()
    CSVmanager.save_data_for_loc(LOC_list, SystemPath.get_path_repositories_LOC_core())
    LOC_list = CSVmanager.generate_repositories_LOC_core_gone()
    CSVmanager.save_data_for_loc(LOC_list, SystemPath.get_path_repositories_LOC_core_gone())

    PRS_list = CSVmanager.generate_repositories_PRS_TF()
    CSVmanager.save_data_for_prs(PRS_list, SystemPath.get_path_repositories_PRS_TF())
    PRS_list = CSVmanager.generate_repositories_PRS_TF_gone()
    CSVmanager.save_data_for_prs(PRS_list, SystemPath.get_path_repositories_PRS_TF_gone())
    PRS_list = CSVmanager.generate_repositories_PRS_core()
    CSVmanager.save_data_for_prs(PRS_list, SystemPath.get_path_repositories_PRS_core())
    PRS_list = CSVmanager.generate_repositories_PRS_core_gone()
    CSVmanager.save_data_for_prs(PRS_list, SystemPath.get_path_repositories_PRS_core_gone())

    ISSUE_list = CSVmanager.generate_repositories_ISSUE_TF()
    CSVmanager.save_data_for_isu(ISSUE_list, SystemPath.get_path_repositories_ISSUE_TF())
    ISSUE_list = CSVmanager.generate_repositories_ISSUE_TF_gone()
    CSVmanager.save_data_for_isu(ISSUE_list, SystemPath.get_path_repositories_ISSUE_TF_gone())
    ISSUE_list = CSVmanager.generate_repositories_ISSUE_core()
    CSVmanager.save_data_for_isu(ISSUE_list, SystemPath.get_path_repositories_ISSUE_core())
    ISSUE_list = CSVmanager.generate_repositories_ISSUE_core_gone()
    CSVmanager.save_data_for_isu(ISSUE_list, SystemPath.get_path_repositories_ISSUE_core_gone())