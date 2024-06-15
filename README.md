#  dc-polarion_report_maker

#### Purpose for this Repository

"Polarion Report Maker is appliance prepared for integration automatic test execution with test management in Polarion. That library is implemented in Python language and used with Pytest framework allows creating test reports directly linked with test cases from Polarion and creating test runs automatically after test session executed. Minimal Python for using that tool is 3.9."


#### Advices how to clone
```
git clone https://github.com/sucheckij/report_maker.git

```

#### Advices how to build

Remember to set version number in `setup.cfg`.

**Option 1: Just build locally:**

(optional) Create virtual environment if not existing yet and activate it:
```
python -m venv venv
venv/Scripts/activate
```
Install the `build` package (needed to be able to build)
```
python -m pip install build
```
Finally, build:
```
python -m build
```
Release will be in `dist` subdirectory.

**Option 2: Generate release for devpi:**

(optional) Create virtual environment if not existing yet and activate it:
```
python -m venv venv
venv/Scripts/activate
```
Install the `pip-system-certs` and `devpi-client` packages (needed to be able to build):
```
python -m pip install pip-system-certs devpi-client
```
login to devpi:
```
python -m devpi use https://devpi.diehlako.local/[username]/dev
python -m devpi login [username]
```
Generate and upload release:
```
python -m devpi upload
```

#### Advices how to use / install the Releases

**Option 1: Install release from devpi:**  

**Automatic:**(via setup.bat)

Add venv\pip.ini file with this content:

```
[global]
index-url = https://devpi.diehlako.local/controls/prod/+simple/
[search]
index = https://devpi.diehlako.local/controls/prod
```

Create setup.ini in main project folder with below script:
```
call venv\Scripts\deactivate
rmdir /S /Q venv
python -m venv venv
call venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
  
**Manual:**
(via commands)

(optional) Create virtual environment if not existing yet and activate it:
```
python -m venv venv
venv/Scripts/activate
```
Install the `pip-system-certs` package:
```
python -m pip install pip-system-certs
```
Add `venv\pip.ini` file with this content:
```ini
[global]
index-url = https://devpi.diehlako.local/controls/prod/+simple/
[search]
index = https://devpi.diehlako.local/controls/prod
```
Finally install the library:
```
python -m pip install dc-polarion_report_maker 
```
Or add to `requirements.txt`:
```
dc-polarion_report_maker
```
and install:
```
python -m pip install -r requirements.txt
```

**Option 2: Install release from github:**

(optional) Create virtual environment if not existing yet and activate it:
```
python -m venv venv
venv/Scripts/activate
```
Finally install the library:
```
python -m pip install dc-polarion_report_maker@git+https://github.com/DiehlControlsSoftware/internal-pypkg-dc-polarion_report_maker
```
Install a specific release:
```
python -m pip install dc-polarion_report_maker@git+https://github.com/DiehlControlsSoftware/internal-pypkg-dc-polarion_report_maker@v1.1.0
```
(the part after the `@` can be a git tag, commit, branch, etc.)  
Or add to `requirements.txt`:
```
dc-polarion_report_maker@git+https://github.com/DiehlControlsSoftware/internal-pypkg-dc-polarion_report_maker@v1.1.0
```
and install:
```
python -m pip install -r requirements.txt
```

Some usage examples are provided further below in this document.
See also the manual: (do be done)


