import sys
sys.path.append(r'../')

import pytest
from polarion_report_maker import PolarionReportMaker, Exceptions, Mode

ini_file = r'D:\study_project\polarion_report_maker\polarion_config.ini'

###########################
##### PYTEST FIXTURES #####
###########################

@pytest.fixture(scope="session")
def polarion():
    report_maker = PolarionReportMaker(ini_path=ini_file,
                                       local_handler=True,
                                       mode=Mode.API.value,
                                       test_run_id='testy_xpass_with_skip',
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

@pytest.mark.parametrize('parameter', [1,2,3])
def test_with_parametrization(polarion,parameter):
    polarion.init_test_case(ID="PRMT-647")
    polarion.test_case_scenario()
    if parameter == 1:
        assert True
    elif parameter == 2:
        assert False
    elif parameter == 3:
        pytest.skip()
    else:
        assert False

def test_passed(polarion):
    polarion.init_test_case(ID="PRMT-654")
    polarion.test_case_scenario()
    assert False

def test_failed(polarion):
    polarion.init_test_case(ID="PRMT-654")
    polarion.test_case_scenario()
    assert False


@pytest.mark.xfail
def test_xpassed(polarion):
    polarion.init_test_case(ID="PRMT-655")
    polarion.test_case_scenario()
    assert True


@pytest.mark.xfail
def test_xfailed(polarion):
    polarion.init_test_case(ID="PRMT-655")
    polarion.test_case_scenario()
    assert False

# def test_xpassed(polarion):
#     polarion.init_test_case(ID="PRMT-655")
#     polarion.test_case_scenario()
#     assert False

# def test_failed_2(polarion):
#     polarion.init_test_case(ID="PRMT-654")
#     polarion.test_case_scenario()
#     assert False

def test_skipped(polarion):
    polarion.init_test_case(ID="PRMT-657")
    pytest.skip()
    polarion.test_case_scenario()
    assert True
#
# def test_with_full_scenario(polarion):
#     polarion.init_test_case(ID="PRMT-647")
#     polarion.test_case_scenario()
#     assert False
# #
# def test_with_steps(polarion):
#     polarion.init_test_case(ID="PRMT-647")
#     polarion.test_case_title()
#     polarion.test_step(step=1)
#     #test execution
#     polarion.test_step_descritpion(step=1)
#     # test execution
#     polarion.test_expected_result(step=1)
#     # test result checking
#     polarion.test_case_polarion_link()
#
#     polarion.test_step(step=2)
#     # test execution
#     polarion.test_step_descritpion(step=2)
#     # test execution
#     polarion.test_expected_result(step=2)
#     # test result checking
#     polarion.test_case_polarion_link()
#     assert False
#
# def test_not_included_in_polarion_with_full_scenario(polarion):
#     polarion.init_test_case(ID="PRMT-1000")
#     polarion.test_case_scenario()
#     assert False
#
# def test_not_included_in_polarion_with_steps(polarion):
#     polarion.init_test_case(ID="PRMT-500")
#     polarion.test_step(step=1)
#     #test execution
#     polarion.test_step_descritpion(step=1)
#     # test execution
#     polarion.test_expected_result(step=1)
#     # test result checking
#     polarion.test_case_polarion_link()
#     assert True
#
# def test_report_maker_not_used(polarion):
#     assert True














