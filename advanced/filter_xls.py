from lcs import lcs

import numpy as np
import pandas as pd
import re


class TestData:
    def __init__(self, xlsx_file: str):
        self.data: pd.DataFrame = pd.read_excel(xlsx_file, index_col=None, header=0)
        self._preprocess_data()
        self.num_tests = self.data.shape[0]
        self.num_columns = self.data.shape[1]
        self.column_names = self.data.columns
        self.groups = self.data.groupby(self.key).groups

    def _preprocess_data(self):
        pass

    def get_rows_by_req_nr(self, value):
        condition = self.data[self.key] == value
        return self.data.loc[condition]

    def print_rows_by_req_nr(self, value):
        pd.set_option('display.width', None)  # Display large column text as well
        print(self.get_rows_by_req_nr(value)[self.print_col_names])

    def print_stats(self):
        print(f"{type(self).__name__}: Tests = {self.num_tests}, Columns = {self.num_columns}")
        print(f"Column names: {self.column_names}")
        print(f"Groups: {self.groups}")
        print("\n")
        # print(data[req_nr])
        # print(self.data.iloc[0])
        # print(data.groupby(req_nr).get_group('FC10001N'))


class TrovaTestData(TestData):
    def __init__(self):
        xlsx_file = "Trova_test_result_18-11-2022.xlsx"
        self.key = 'Requisition Nr'
        self.unique = 'Test'
        self.print_col_names = [self.key, self.unique, 'Visit']
        super().__init__(xlsx_file)

    def _preprocess_data(self):
        super()._preprocess_data()
        condition = (self.data['Test result'] != 'N R') & \
                    (self.data['Test result'] != 'N D') & \
                    (self.data['Test result'] != 'Pending') & \
                    (self.data['Test result'] != 'Sample not yet received') & \
                    (self.data['Continent'] != 'Asia') & \
                    (self.data['Continent'] != 'North America')
        self.data = self.data[condition]


class RealTestData(TestData):
    def __init__(self):
        xlsx_file = "REAL_Tests_EU.xlsx"
        self.key = 'BARCNBR'
        self.unique = 'VISITPANEL_TEST'
        self.print_col_names = [self.key, self.unique, 'VISIT']
        super().__init__(xlsx_file)

    def _preprocess_data(self):
        super()._preprocess_data()

        def clean_barc_nr(barc_nr):
            if re.search('-.*', barc_nr):
                pos = re.search('-.*', barc_nr).start()
                return barc_nr[:pos]

            else:
                return barc_nr

        self.data[self.key] = self.data[self.key].apply(clean_barc_nr)

        condition = (self.data['VISITPANEL'] != 'VISIT')
        self.data = self.data[condition]


def compare(ref_data: TrovaTestData, imported_data: RealTestData):
    ref_set = set(ref_data.groups.keys())
    imported_set = set(imported_data.groups.keys())
    in_ref_but_not_imported = ref_set.difference(imported_set)
    in_imported_but_not_ref = imported_set.difference(ref_set)

    print(f"\n\nRequisition nr in reference but not in imported = {len(in_ref_but_not_imported)}", in_ref_but_not_imported)
    for test in in_ref_but_not_imported:
        ref_data.print_rows_by_req_nr(test)

    # Now check all matches
    for req_nr in ref_set.intersection(imported_set):
        ref_tests = ref_data.get_rows_by_req_nr(req_nr)
        imported_tests = imported_data.get_rows_by_req_nr(req_nr)

        # Match column `Test` in reference data with column `VISITPANEL_TEST` in imported data
        if True:  # len(ref_tests) != len(imported_tests):
            unique_column_ref_tests = ref_tests[ref_data.unique]
            unique_column_imported_tests = imported_tests[imported_data.unique]

            # print(f"\n\nTests in reference = {len(ref_tests)}")
            # ref_data.print_rows_by_req_nr(req_nr)
            # print(f"\n\nTests in imported = {len(imported_tests)}")
            # imported_data.print_rows_by_req_nr(req_nr)

            not_found_tests = []
            for key1, value1 in unique_column_ref_tests.items():
                match_lengths = [lcs(value1, value).pop() for value in unique_column_imported_tests.values]
                match_lengths = np.sort(match_lengths)
                if len(match_lengths[-1]) < 8:
                    not_found_tests.append(key1)

            if not_found_tests:
                print(f"\n\nRequisition nr found but some tests missing")
                print(f"{ref_data.data.loc[not_found_tests][ref_data.print_col_names]}")

    print(f"\n\nRequisition nr in imported but not in reference {len(in_imported_but_not_ref)}", in_imported_but_not_ref)
    for test in in_imported_but_not_ref:
        imported_data.print_rows_by_req_nr(test)


if __name__ == "__main__":
    trova_test_data = TrovaTestData()
    real_test_data = RealTestData()
    trova_test_data.print_stats()
    real_test_data.print_stats()
    compare(trova_test_data, real_test_data)