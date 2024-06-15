call ..\venv\Scripts\activate.bat
call pytest test_example.py --self-contained-html --css=..\report_template.css --html=..\test_reports\Test_Report.html -m xfail
