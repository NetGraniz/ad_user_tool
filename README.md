# Installation Guide

## Prerequisites

Before starting, install:

* Git
* Python 3.12 or newer
* Microsoft Word (required for document generation)

---

## Clone the repository

```powershell
git clone https://github.com/NetGraniz/ad_user_tool.git
cd REPOSITORY
```

---

## Create a virtual environment

```powershell
python -m venv .venv
```

---

## Activate the virtual environment

### PowerShell

```powershell
.\.venv\Scripts\Activate.ps1
```

### Command Prompt

```cmd
.venv\Scripts\activate.bat
```

---

## Install project dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## Project configuration

Before running the application, update the configuration values according to your environment:

* Active Directory domain
* LDAP server
* Organizational Units (OU)
* Security Groups
* Mail server settings
* Network paths
* Word document template

The repository contains only example values. Replace them with your own environment configuration.

---

## Run the application

```powershell
python ad_user_tool.py
```

---

# Build Executable

## Recommended

Use the provided build script:

```powershell
.\build.ps1
```

The executable will be created in:

```text
dist\
└── ad_user_tool.exe
```

---

## Manual Build

If you prefer to build manually, activate the virtual environment first:

```powershell
.\.venv\Scripts\Activate.ps1
```

Then run PyInstaller:

```powershell
pyinstaller --clean --onefile --noconsole --name ad_user_tool --add-data ".venv\Lib\site-packages\iuliia\schemas;iuliia\schemas" ad_user_tool.py
```

The executable will be created in:

```text
dist\
└── ad_user_tool.exe
```


# Updating dependencies

If new Python packages are installed:

```powershell
python -m pip freeze > requirements.txt
```

Commit the updated dependency list:

```powershell
git add requirements.txt
git commit -m "Update Python dependencies"
git push
```

---

# Verification Checklist

Verify the following functionality after any code changes:

* ☐ Clipboard operations (Copy / Cut / Paste)
* ☐ Active Directory user creation
* ☐ Organization attributes
* ☐ Password generation
* ☐ Security group assignment
* ☐ Mail account configuration
* ☐ User folder creation
* ☐ Login script generation
* ☐ Microsoft Word document generation
* ☐ Executable build using `build.ps1`
