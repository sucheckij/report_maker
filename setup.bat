call venv\Scripts\deactivate
rmdir /S /Q venv
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
