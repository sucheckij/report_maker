import pytest
from polarion_report_maker import PolarionReportMaker, Exceptions, Mode

INI_FILE = r'put path to ini file here'

###########################
##### PYTEST FIXTURES #####
###########################

@pytest.fixture(scope="session")
def polarion():
    report_maker = PolarionReportMaker(ini_path=INI_FILE,
                                       local_handler=True,
                                       mode=Mode.API.value,
                                       test_run_id=False,
                                       exceptions=Exceptions.WARNING.value)
    yield report_maker
    report_maker.create_test_run()
@pytest.fixture(scope="function",
                autouse=True)

def test_check(request, polarion: PolarionReportMaker):
    polarion.get_pytest_request(request)
    yield
    polarion.check_test_result(request)


###############################
##### TEST SESSION MODULE #####
###############################
def test_example(polarion):
    polarion.init_test_case(ID="")
    polarion.test_case_scenario()

















