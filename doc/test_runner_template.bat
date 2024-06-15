call ..\venv\Scripts\activate.bat
call pytest test_example.py -s --self-contained-html --css=..\report_template.css --html=..\test_reports\Test_Report.html
