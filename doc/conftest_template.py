import pytest

from polarion_report_maker import PolarionReportMaker

def pytest_configure(config):
    PolarionReportMaker.configure_report_table_content(pytest_config=config,
                                       Project_Name= "Project Name",
                                       Project_Number = "Project Number",
                                       SW_Version = "--",
                                       HW_Version = "--",
                                       Test_Version = "--",
                                       Author = "Author Name",
                                       Test_Scope = "Test Scope",
                                       Test_Type = "Automatic,Manual, Mixed",
                                       Risks= "--",
                                       Specification= "Test specification",
                                       Comments = "Comments and information"
                                       )

@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    PolarionReportMaker.make_report(item=item, outcome=outcome)
