import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import CSVmanager
import SystemPath

import Utilities as util

if __name__ == "__main__":
    token = util.getRandomToken()

    LOC_list = CSVmanager.generate_repositories_LOC_TF(token)
    CSVmanager.save_data_for_loc(LOC_list, SystemPath.get_path_repositories_LOC_TF())
    LOC_list = CSVmanager.generate_repositories_LOC_TF_gone(token)
    CSVmanager.save_data_for_loc(LOC_list, SystemPath.get_path_repositories_LOC_TF_gone())
    LOC_list = CSVmanager.generate_repositories_LOC_core(token)
    CSVmanager.save_data_for_loc(LOC_list, SystemPath.get_path_repositories_LOC_core())
    LOC_list = CSVmanager.generate_repositories_LOC_core_gone(token)
    CSVmanager.save_data_for_loc(LOC_list, SystemPath.get_path_repositories_LOC_core_gone())

    PRS_list = CSVmanager.generate_repositories_PRS_TF(token)
    CSVmanager.save_data_for_prs(PRS_list, SystemPath.get_path_repositories_PRS_TF())
    PRS_list = CSVmanager.generate_repositories_PRS_TF_gone(token)
    CSVmanager.save_data_for_prs(PRS_list, SystemPath.get_path_repositories_PRS_TF_gone())
    PRS_list = CSVmanager.generate_repositories_PRS_core(token)
    CSVmanager.save_data_for_prs(PRS_list, SystemPath.get_path_repositories_PRS_core())
    PRS_list = CSVmanager.generate_repositories_PRS_core_gone(token)
    CSVmanager.save_data_for_prs(PRS_list, SystemPath.get_path_repositories_PRS_core_gone())

    ISSUE_list = CSVmanager.generate_repositories_ISSUE_TF(token)
    CSVmanager.save_data_for_isu(ISSUE_list, SystemPath.get_path_repositories_ISSUE_TF())
    ISSUE_list = CSVmanager.generate_repositories_ISSUE_TF_gone(token)
    CSVmanager.save_data_for_isu(ISSUE_list, SystemPath.get_path_repositories_ISSUE_TF_gone())
    ISSUE_list = CSVmanager.generate_repositories_ISSUE_core(token)
    CSVmanager.save_data_for_isu(ISSUE_list, SystemPath.get_path_repositories_ISSUE_core())
    ISSUE_list = CSVmanager.generate_repositories_ISSUE_core_gone(token)
    CSVmanager.save_data_for_isu(ISSUE_list, SystemPath.get_path_repositories_ISSUE_core_gone())