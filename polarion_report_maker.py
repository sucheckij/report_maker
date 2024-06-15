import os
import httpx
import configparser
import glob
import pandas as pd

from enum import IntEnum
from bs4 import BeautifulSoup
from typing import Callable, Literal, Union
from datetime import datetime, timezone
from pytest import FixtureRequest
from pytest_metadata.plugin import metadata_key

class Mode(IntEnum):
    API = 0
    FILE = 1

class Exceptions(IntEnum):
    WARNING = 0
    ERROR = 1

def convert_html_to_str(html_str: str) -> str:
    if not isinstance(html_str,str):
        raise ValueError("ERROR: Html str can input only 'str' type")
    soup = BeautifulSoup(html_str,'html.parser')
    return soup.get_text()

class PolarionReportMaker():

    def __init__(self, ini_path: str,
                 local_handler: bool = True,
                 mode: int = None,
                 exceptions: int = None,
                 test_run_id: Union[str, Literal[False]] = ''):

        # Project ini file settings
        self.__ini_path = ini_path
        self.__final_test_cases_file_name = 'project_test_cases.xlsx'

        # Extracted main project settings
        self.__polarion_server = ''
        self.__token_path = ''
        self.__test_document_path = ''
        self.__project_id = ''
        self.__token_path = ''
        self.__token = ''
        self.__test_run_polarion_template = ''
        self.__current_request_test_function = None

        # Mode and exception handling (default: API with only warnings)
        self.__mode = Mode.API.value
        self.__exceptions = Exceptions.WARNING.value

        # Handlers flags (handling default turned on)
        self.__global_handler = True
        self.__local_handler = True
        self.__test_run_handler = True

        # Set initial states of appliance
        self.set_local_handler(local_handler)
        self.__extract_project_ini_file(self.__ini_path)

        if mode is not None:
            self.__set_mode(mode=mode)

        if exceptions is not None:
            self.set_exceptions(exceptions=exceptions)

        self.__token = self.__get_polarion_token_from_file(self.__token_path)

        # Settings of current intialized work item (test case)
        self.workitem_id = ''
        self.workitem_title = 'no title'
        self.number_of_test_steps = 0
        self.steps = []
        self.step_descriptions = []
        self.expected_results = []
        self.__df = None

        # Settings of test run
        self.polarion_test_cases_from_test_session = {}
        self.all_test_cases_from_test_session = {}
        self.test_run_id = test_run_id
        self.__test_run_handling_init()
        self.workitem_id_initialized_via_api = False

        if self.__mode == Mode.FILE.value and self.__handler:
            self.__convert_xlsx_docs_files_to_final_xlsx()
            self.__df = pd.read_excel(self.__test_document_path + self.__final_test_cases_file_name)

##################################
##### INITIALIZATION METHODS #####
##################################
    def __extract_project_ini_file(self, ini_path: str):

        # extract main project settings from 'polarion_config.ini'
        config = configparser.ConfigParser()
        try:
            config.read(ini_path)

            self.__polarion_server = str(config.get('polarion','POLARION_SERVER'))
            self.__token_path = str(config.get('polarion', 'TOKEN_PATH'))
            self.__test_document_path = str(config.get('polarion', 'TEST_DOCUMENT_PATH'))
            self.__project_id = str(config.get('polarion', 'PROJECT_ID'))
            self.__mode = int(config.getint('polarion', 'MODE'))
            self.__global_handler = True if config.get('polarion', 'GLOBAL_HANDLER') in ['True', 'On'] else False
            self.__exceptions = int(config.getint('polarion', 'EXCEPTIONS'))
            self.__test_run_handler = True if config.get('polarion', 'TEST_RUN_GLOBAL_HANDLER') in ['True', 'On'] else False
            self.__test_run_polarion_template = str(config.get('polarion', 'TEST_RUN_TEMPLATE'))

        except:
            raise Exception("PolarionReportMakerException: File configuration problem during PolarionReportMaker initialization")

        # checking if endpoint and test documents path have "/" or "\" at the end of line
        if '/' in self.__polarion_server and not self.__polarion_server[-1] == '/':
            self.__polarion_server = f'{self.__polarion_server}/'
        elif '\\' in self.__polarion_server and not self.__polarion_server[-1] == '\\':
            self.__polarion_server = f'{self.__polarion_server}\\'

        if '/' in self.__test_document_path and not self.__test_document_path[-1] == '/':
            self.__test_document_path = f'{self.__test_document_path}/'
        elif '\\' in self.__test_document_path and not self.__test_document_path[-1] == '\\':
            self.__test_document_path = f'{self.__test_document_path}\\'

    def set_test_run_template(self, template_name: str):
        if not isinstance(template_name,str):
            raise Exception('PolarionTestRunException: Wrong data type of typed template name.')
        self.__test_run_polarion_template = template_name

    def __set_mode(self, mode: int):
        if not isinstance(mode,int):
            raise Exception('PolarionReportMakerException: Wrong data type of typed mode.')
        # Set correct mode 0 - api, 1 - file. If wrong mode setting handle exception.
        try:
            self.__mode = Mode(mode)
        except:
            raise ValueError('PolarionReportMakerException: Given mode not exist. Choose correct one: [0] api or [1] file')

    def set_exceptions(self, exceptions: int):
        if not isinstance(exceptions,int):
            raise Exception('PolarionReportMakerException: Wrong data type of typed exceptions.')
        # Set correct mode 0 - api, 1 - file. If wrong mode setting handle exception.
        try:
            self.__exceptions = Exceptions(exceptions)
        except:
            raise ValueError('PolarionReportMakerException: Given exceptions not exist. Choose correct one: [0] warnings or [1] errors')

    def __get_polarion_token_from_file(self, file_path: str) -> str:
        # That function returns autorization bearer token from .ini file
        with open(file_path, 'r') as file:
            if os.path.getsize(file_path) == 0:
                raise Exception( 'PolarionReportMakerException: Token file is empty')
            lines_number = sum(1 for line in file)
            if lines_number == 1:
                file.seek(0)
                token = file.read()
            else:
                raise Exception('PolarionReportMakerException: Wrong format data in token file')
        return token

    def __test_run_handling_init(self)-> None:
        if isinstance(self.test_run_id, str):
            if self.test_run_id == '' or self.__mode != Mode.API.value:
                self.__test_run_handler = False

        elif (isinstance(self.test_run_id, bool) and not self.test_run_id) or self.__mode != Mode.API.value:
                self.__test_run_handler = False

        else:
            raise Exception("PolarionTestRunException: Wrong value of test_run_id")

        if self.__test_run_handler:
            if self.__is_test_run_name_doubled():
                raise Exception("PolarionTestRunException: Test run ID already exist. Please type different name of test run.")

##################################################
##### FUNCTIONAL METHODS OF APLIANCE CONTROL #####
##################################################
    def clear_test_case_data(self):
        self.workitem_id = ''
        self.workitem_title = 'no title'
        self.number_of_test_steps = 0
        self.steps = []
        self.step_descriptions = []
        self.expected_results = []
        self.workitem_id_initialized_via_api = False
    def handle_exceptions(self, f: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                if self.__exceptions == Exceptions.WARNING.value:
                    print(f'\nWARNING: {e}')
                elif self.__exceptions == Exceptions.ERROR.value:
                    raise e
                else:
                    print(f'\nWARNING: {e}')
        return wrapper

    def get_pytest_request(self, func: FixtureRequest):
        self.__current_request_test_function = func.function

    @property
    def __handler(self):
        return self.__local_handler and self.__global_handler

    def set_local_handler(self, local_handler: bool):
        self.handle_exceptions(self.__set_local_handler)(local_handler)

    def __set_local_handler(self, local_handler: bool):
        if not isinstance(local_handler, bool):
            raise Exception("PolarionReportMakerException: Wrong type format of 'local handler'")
        self.__local_handler = local_handler

    @staticmethod
    def configure_report_table_content(pytest_config, **kwargs):
        pytest_config.stash[metadata_key].clear()
        for key,value in kwargs.items():
            pytest_config.stash[metadata_key][key.replace("_"," ")] = value
    @staticmethod
    def make_report(item, outcome, rename:bool = True):

        if not isinstance(rename,bool):
            raise TypeError("Wrong type of 'rename' flag. Please put True or False.")

        report = outcome.get_result()

        if rename:
            test_fn = item.obj
            docstring = getattr(test_fn, '__doc__')

            new_nodeid =''
            for sign in report.nodeid[::-1]:
                if sign != ':':
                    new_nodeid += sign
                else:
                    break
            new_nodeid=new_nodeid[::-1]
            # report.nodeid = report.nodeid.replace("::", "/")
            report.nodeid = new_nodeid.replace("_"," ")

            if docstring:
                report.nodeid = docstring.partition('\n')[0]

        setattr(item, 'rep_' + report.when, report)

################################
##### POLARION API METHODS #####
################################
    def get_request_via_api(self, endpoint: str):
        if not isinstance(endpoint,str):
            raise Exception('PolarionReportMakerException [{self.workitem_id}]: Wrong data type of typed mode. Endpoint in "str" format required.')
        headers = {
            'Authorization': f'Bearer {self.__token}'
        }

        try:
            response = httpx.get(url=endpoint, headers=headers, verify=False, timeout=20)
            if response.status_code == 200:
                return response.json()
            else:
                raise Exception(f'PolarionReportMakerException [{self.workitem_id}]: Error during http request with status code: {response.status_code}')
        except httpx.RequestError as e:
            self.__local_handler = False
            self.__test_run_handler = False
            print(f"ERROR: Web error: {e}")

    def post_request_via_api(self, endpoint: str, data: dict):
        if not isinstance(endpoint,str):
            raise Exception(f'PolarionReportMakerException : Wrong data type of typed mode. Endpoint in "str" format required.')
        headers = {
            'Authorization': f'Bearer {self.__token}'
        }

        try:
            response = httpx.post(url=endpoint, json=data, headers=headers, verify=False, timeout=20)
            if response.status_code == 201:
                return response.json()
            else:
                raise Exception(f'PolarionReportMakerException : Error during http request with status code: {response.status_code}')
        except httpx.RequestError as e:
            self.__local_handler = False
            self.__test_run_handler = False
            print(f"ERROR: Web error: {e}")

    def polarion_api_request_get_test_steps(self, ID:str, test_step: int=1) -> str:
        # return f'{self.__polarion_server}{self.project_id}/workitems/{ID}/teststeps?fields[teststeps]=@all'
        return f'{self.__polarion_server}{self.__project_id}/workitems/{ID}/teststeps?fields%5Bteststeps%5D=%40all&page%5Bnumber%5D={test_step}'

    def polarion_api_request_get_title(self, ID:str) -> str:
        return f'{self.__polarion_server}{self.__project_id}/workitems/{ID}'

    def polarion_api_request_get_test_runs(self)-> str:
        return f'{self.__polarion_server}{self.__project_id}/testruns'

    def polarion_api_request_get_test_runs_site(self, site_number: int)-> str:
        return f'{self.__polarion_server}{self.__project_id}/testruns?page%5Bnumber%5D={site_number}'

    def polarion_api_request_post_test_run(self)-> str:
        return f'{self.__polarion_server}{self.__project_id}/testruns'

    def polarion_api_request_post_test_result(self)-> str:
        return f'{self.__polarion_server}{self.__project_id}/testruns/{self.test_run_id}/testrecords'

##################################################
##### METHODS FOR REPORTING CONTROL VIA FILE #####
##################################################
    def __get_all_xlsx_files_names(self) -> list[str]:

        xlsx_files = glob.glob(os.path.join(self.__test_document_path, '*.xlsx'))
        xlsx_file_names = [os.path.basename(file_path) for file_path in xlsx_files]

        if len([file for file in xlsx_file_names if file != self.__final_test_cases_file_name]) == 0:
           raise Exception(f'PolarionReportMakerException : No exported files from Polarion. Empty test case database')

        return xlsx_file_names

    def __convert_xlsx_docs_files_to_final_xlsx(self):

        xlsx_test_polarion_files = self.__get_all_xlsx_files_names()

        if self.__final_test_cases_file_name in xlsx_test_polarion_files:
            os.remove(self.__test_document_path + self.__final_test_cases_file_name)
            xlsx_test_polarion_files = [file for file in xlsx_test_polarion_files if file != self.__final_test_cases_file_name]

        dfs = []

        for xlsx_file_name in xlsx_test_polarion_files:
            df_org = pd.read_excel(self.__test_document_path + xlsx_file_name)

            df = df_org.copy()

            for index, row in df_org.iterrows():
                if df_org.at[index, 'Type'] != 'Test Case':
                    df = df.drop(index)

            df = df.reset_index(drop=True)

            # Check if raw value can be found in column
            checking_value = self.workitem_id
            if_present = df['ID'].isin([checking_value]).any()
            # print(f"Value {checking_value} is in dataframe: {if_present}")

            # Return idx for choosen element
            checking_element = self.workitem_id
            idx = 0
            for index, value in df['ID'].items():
                if value == checking_element:
                    idx = index
                    break

            # Change NaN position to correct values of IDs
            current_ID = df.at[0, 'ID']

            for index, row in df.iterrows():
                if pd.isna(df.at[index, 'ID']):
                    df.at[index, 'ID'] = current_ID
                else:
                    current_ID = row.ID

            # Change NaN position to correct values of step numbers
            current_ID = df.at[0, 'ID']
            i = 1
            for index, row in df.iterrows():
                if df.at[index, 'ID'] != current_ID:
                    i = 1
                    current_ID = row.ID

                df.at[index, '#'] = i
                i += 1

            # Change NaN position to correct values of titles
            for index, row in df.iterrows():

                if pd.isna(df.at[index, 'Title']) and index != 0:
                    df.at[index, 'Title'] = df.at[index - 1, 'Title']

            df = df.drop(columns=['_polarion'])


            dfs.append(df)

        combined_df = pd.concat(dfs, ignore_index=True)

        # Save prepared dataframe to final working document
        combined_df.to_excel(self.__test_document_path + self.__final_test_cases_file_name, index=False)


##################################################
##### METHODS OF REPORT CREATION IN POLARION #####
##################################################
    def __is_test_run_name_doubled(self) -> bool:

        msg = self.get_request_via_api(endpoint= self.polarion_api_request_get_test_runs())
        no_sites_to_read = 1
        if msg['links']['first'] != msg['links']['last']:
            list_ = ''
            for i in msg['links']['last'][::-1]:
                if i != '=':
                    list_ += i
                else:
                    break
            no_sites_to_read = int(list_[::-1])


        test_run_name_list = []
        for i in range(0,no_sites_to_read):
            endpt = self.polarion_api_request_get_test_runs_site(site_number=i+1)
            msg = self.get_request_via_api(endpoint=endpt)
            for ele in msg['data']:
                test_run_name_list.append(ele['id'][len(self.__project_id)+1:])

        return True if self.test_run_id in test_run_name_list else False

    def check_test_result(self, request: FixtureRequest):

        if self.workitem_id_initialized_via_api:

            if hasattr(request.node.rep_call, 'wasxfail'):
                if not request.node.rep_call.passed:
                    if self.workitem_id not in self.polarion_test_cases_from_test_session:
                        self.polarion_test_cases_from_test_session[self.workitem_id] = [True]
                    else:
                        self.polarion_test_cases_from_test_session[self.workitem_id].append(True)

                elif request.node.rep_call.passed:
                    if self.workitem_id not in self.polarion_test_cases_from_test_session:
                        self.polarion_test_cases_from_test_session[self.workitem_id] = [False]
                    else:
                        self.polarion_test_cases_from_test_session[self.workitem_id].append(False)

            elif request.node.rep_call.failed:
                if self.workitem_id not in self.polarion_test_cases_from_test_session:
                    self.polarion_test_cases_from_test_session[self.workitem_id]=[False]
                else:
                    self.polarion_test_cases_from_test_session[self.workitem_id].append(False)

            elif request.node.rep_call.passed:
                if self.workitem_id not in self.polarion_test_cases_from_test_session:
                    self.polarion_test_cases_from_test_session[self.workitem_id] = [True]
                else:
                    self.polarion_test_cases_from_test_session[self.workitem_id].append(True)

            if request.node.rep_call.skipped:
                if self.workitem_id not in self.polarion_test_cases_from_test_session:
                    self.polarion_test_cases_from_test_session[self.workitem_id] = [None]
                else:
                    self.polarion_test_cases_from_test_session[self.workitem_id].append(None)

    def __get_final_test_results(self):
        for id, result in self.polarion_test_cases_from_test_session.items():
            set_result = set(result)
            if False in set_result or True in set_result:
                if all(set_result-{None}):
                    self.polarion_test_cases_from_test_session[id] = 'passed'
                else:
                    self.polarion_test_cases_from_test_session[id] = 'failed'
            else:
                if None in set_result:
                    self.polarion_test_cases_from_test_session[id] = 'skipped'

    def create_test_run(self):

        if all([self.__handler, self.__test_run_handler]):
            if len(self.polarion_test_cases_from_test_session) == 0:
                print("\nWARNING: PolarionTestRunInfo: Test run is not created due to no test cases linked with Polarion")

            if  len(self.polarion_test_cases_from_test_session) != 0:
                self.post_request_via_api(endpoint=self.polarion_api_request_post_test_run(),
                                          data=self.__test_run_json())

                self.__get_final_test_results()
                for id,result in self.polarion_test_cases_from_test_session.items():
                    self.post_request_via_api(endpoint=self.polarion_api_request_post_test_result(),
                                              data=self.__test_results_json(test_case_ID=id,
                                                                            test_status=result)
                                              )

                self.__print_excluded_test_cases_from_test_run()
    def __collect_all_test_cases_from_init_input(self, workitem: str):
        if workitem in  self.all_test_cases_from_test_session.keys():
            self.all_test_cases_from_test_session[workitem] += 1
        else:
            self.all_test_cases_from_test_session[workitem] = 0
    def __print_excluded_test_cases_from_test_run(self):
        print("")
        print(f"\nINFO: PolarionTestRunInfo: Test cases excluded from created test run '{self.test_run_id}' in Polarion ")

        print(r"\\")
        for test_case in (set(self.all_test_cases_from_test_session.keys())-set(list(self.polarion_test_cases_from_test_session.keys()))):
            print(f"  {test_case}")
        print(r"//")

        print("\n")


##############################################################
##### METHODS OF TEST CASE INITTIALIZATION FROM POLARION #####
##############################################################

    def init_test_case(self,ID: str, func: Callable = None):
        self.handle_exceptions(self.__init_test_case)(ID, func)

    def __init_test_case(self, ID: str, func: Callable = None):

        self.clear_test_case_data()
        self.workitem_id = ID
        self.__collect_all_test_cases_from_init_input(workitem=self.workitem_id)

        if self.__handler:
            if self.__mode == Mode.API.value:
                if not isinstance(ID,str):
                    raise TypeError(f"PolarionReportMakerException [{self.workitem_id}]: Wrong type of 'ID' value")

                msg = self.get_request_via_api(self.polarion_api_request_get_title(ID=ID))

                self.workitem_title = msg['data']['attributes']['title']

                if self.all_test_cases_from_test_session[self.workitem_id] > 0:
                    self.__current_request_test_function.__doc__ = f"[{self.workitem_id}] " + self.workitem_title +f' [{self.all_test_cases_from_test_session[self.workitem_id]+1}]'
                else:
                    self.__current_request_test_function.__doc__ = f"[{self.workitem_id}] " + self.workitem_title

                msg = self.get_request_via_api(self.polarion_api_request_get_test_steps(ID=ID))

                no_sites_to_read = 1
            # check condition if there is more than one site during calling test steps
                if msg['links']['first'] != msg['links']['last']:   # REGEX
                    list_ = ''
                    for i in msg['links']['last'][::-1]:
                        if i != '=':
                            list_ += i
                        else:
                            break
                    no_sites_to_read = int(list_[::-1])
                    # print(f'Number sites to read: {no_sites_to_read}')

            # parse from endpoind response all test_case data
                for ele in msg['data']:
                    self.number_of_test_steps += 1
                    self.steps.append(convert_html_to_str(ele['attributes']['values'][0]['value']))
                    self.step_descriptions.append(convert_html_to_str(ele['attributes']['values'][1]['value']))
                    self.expected_results.append(convert_html_to_str(ele['attributes']['values'][2]['value']))

                if no_sites_to_read > 1:
                    for i in range(2,no_sites_to_read+1):
                        msg = self.get_request_via_api(self.polarion_api_request_get_test_steps(ID=ID, test_step=i))
                        for ele in msg['data']:
                            self.number_of_test_steps += 1
                            self.steps.append(convert_html_to_str(ele['attributes']['values'][0]['value']))
                            self.step_descriptions.append(convert_html_to_str(ele['attributes']['values'][1]['value']))
                            self.expected_results.append(convert_html_to_str(ele['attributes']['values'][2]['value']))

                self.workitem_id_initialized_via_api = True

            elif self.__mode == Mode.FILE.value and self.__df['ID'].isin([self.workitem_id]).any():

                # sprawdz ilosc test stepów dla danego test case
                id_counts = self.__df['ID'].value_counts()[self.workitem_id]

                first_index = self.__df[self.__df['ID'] == self.workitem_id].index[0]

                self.workitem_title= self.__df.loc[first_index, 'Title']

                if self.all_test_cases_from_test_session[self.workitem_id] > 0:
                    self.__current_request_test_function.__doc__ = f"[{self.workitem_id}] " + self.workitem_title + f' [{self.all_test_cases_from_test_session[self.workitem_id]+1}]'
                else:
                    self.__current_request_test_function.__doc__ = f"[{self.workitem_id}] " + self.workitem_title

                for i in range(first_index,first_index+id_counts):

                    self.number_of_test_steps += 1
                    self.steps.append(str(self.__df.loc[i, 'Step']))
                    self.step_descriptions.append(str(self.__df.loc[i, 'Step Description']))
                    self.expected_results.append(str(self.__df.loc[i, 'Expected Result']))


############################################################
##### METHODS TO INCLUDING TEST CASES IN PYTEST REPORT #####
############################################################
    def test_case_title(self):
        if self.__handler:
                print(self.workitem_title)

    def test_step(self,step: int):
        self.handle_exceptions(self.__test_step)(step)

    def __test_step(self, step: int):
        if self.__handler:
            if not isinstance(step, int):
                raise TypeError(f"PolarionReportMakerException [{self.workitem_id}]: Wrong type of 'step' value")
            if step < 1 or step > len(self.steps):
                raise ValueError(f"PolarionReportMakerException [{self.workitem_id}]: Given 'step' in wrong value range")
            else:
                print(f'-----------------------------  STEP {step + 1}  -----------------------------------------\n')
                print(f'\n{self.steps[step]}\n')
                print(f'--------------------------------------------------------------------------------\n')

    def test_step_descritpion(self,step: int):
        self.handle_exceptions(self.__test_step_description)(step)

    def __test_step_description(self, step: int):
        if self.__handler:
            if not isinstance(step, int):
                raise TypeError(f"PolarionReportMakerException [{self.workitem_id}]: Wrong type of 'step' value")
            if step < 1 or step > len(self.steps):
                raise ValueError(f"PolarionReportMakerException [{self.workitem_id}]: Given 'step' in wrong value range")
            else:
                print(f'-----------------------------  STEP DESCRIPTION {step + 1}  ------------------------------\n')
                print(f'\n{self.step_descriptions[step]}\n')
                print(f'--------------------------------------------------------------------------------\n')

    def test_expected_result(self, step: int):
        self.handle_exceptions(self.__test_expected_result)(step)
    def __test_expected_result(self, step: int):
        if self.__handler:
            if not isinstance(step, int):
                raise TypeError(f"PolarionReportMakerException [{self.workitem_id}]: Wrong type of 'step' value")
            if step < 1 or step > len(self.steps):
                raise ValueError(f"PolarionReportMakerException [{self.workitem_id}]: Given 'step' in wrong value range")
            else:
                print(f'-----------------------------  EXPECTED RESULTS {step + 1}  --------------------------\n')
                print(f'[EXPECTED_RESULT]: \n{self.expected_results[step]}\n')
                print(f'--------------------------------------------------------------------------------\n')


    def test_step_scenario(self, step: int):
        self.handle_exceptions(self.__test_step_scenario)(step)
    def __test_step_scenario(self, step):
        if self.__handler:
            if not isinstance(step, int):
                raise TypeError(f"PolarionReportMakerException [{self.workitem_id}]: Wrong type of 'step' value")
            if step < 1 or step > len(self.steps):
                raise ValueError(f"PolarionReportMakerException [{self.workitem_id}]: Given 'step' in wrong value range")
            else:
                print(f' STEP {step}: \n{self.steps[step - 1]}')
                print(f' STEP_DESCRIPTION: \n{self.step_descriptions[step - 1]}')
                print(f' EXPECTED_RESULT: \n{self.expected_results[step - 1]}')

    def test_case_scenario(self):
        self.handle_exceptions(self.__test_case_scenario)()
    def __test_case_scenario(self):
        if self.__handler:
            if self.number_of_test_steps != 0:

                print(
                    f'\n-----------------------------  {self.workitem_id}  ---------------------------------------')
                print(f"{self.workitem_title}")
                print(f'--------------------------------------------------------------------------------')

                for step in range(len(self.steps)):
                    print(f'-----------------------------  STEP {step + 1}  -----------------------------------------\n')
                    print(f'[STEP]: \n{self.steps[step]}\n')
                    print(f'[STEP_DESCRIPTION] \n{self.step_descriptions[step]}\n')
                    print(f'[EXPECTED_RESULT]: \n{self.expected_results[step]}\n')
                print(f'--------------------------------------------------------------------------------\n')
                self.test_case_polarion_link()
            else:
                raise Exception(f"PolarionReportMakerException [{self.workitem_id}]: Cannot print test case scenario: no steps")

    def test_case_polarion_link(self):
        print(f'[POLARION LINK]')
        print(f'https://polarion.controls.corp.diehl.com/polarion/#/project/{self.__project_id}/workitem?id={self.workitem_id}')


###################################################
##### JSON BODY CREATORS FOR API POST METHODS #####
###################################################

    @staticmethod
    def __get_current_datetime_iso():
        current_datetime = datetime.now(timezone.utc)
        datetime_iso = current_datetime.strftime("%Y-%m-%dT%H:%M:%SZ")
        return datetime_iso

    def __test_run_json(self):

        data =  {
            "data": [
                {
                    "type": "testruns",
                    "attributes": {
                        "finishedOn": f"{self.__get_current_datetime_iso()}",
                        "groupId": "",
                        "homePageContent": {
                            "type": "text/html",
                            "value": self.test_run_id
                        },
                        "id": self.test_run_id,
                        "idPrefix": "",
                        "isTemplate": False,
                        "keepInHistory": False,
                        "query": "Query",
                        "selectTestCasesBy": "manualSelection",
                        "status": "open",
                        "title": self.test_run_id,
                        "type": "automated",
                        "useReportFromTemplate": True
                    },
                    "relationships": {
                        "template": {
                            "data": {
                                "id": f"{self.__project_id}/{self.__test_run_polarion_template}",
                                "type": "testruns"
                            }
                        }
                    }

                }
            ]
        }

        return data


    def __test_results_json(self, test_case_ID: str, test_status: str):

        data =  {
                "data": [
                    {
                        "type": "testrecords",
                        "attributes": {
                            "comment": {
                                "type": "text/html",
                                "value": "via automated test execution"
                            },
                            "duration": 5,
                            "executed": self.__get_current_datetime_iso(),
                            "result": test_status,
                            "testCaseRevision": ""
                        },
                        "relationships": {
                            "testCase": {
                                "data": {
                                    "id": f"{self.__project_id}/{test_case_ID}",
                                    "type": "workitems"
                                }
                            }
                        }
                    }
                ]
            }

        return data

