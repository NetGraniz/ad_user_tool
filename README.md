# AD User Tool

A Python application that automates the creation of Active Directory user accounts and generates onboarding documents through a simple graphical interface.

The application reduces the time required to provision new employees by automating repetitive administrative tasks while maintaining a consistent user creation process.

## Features

* Graphical interface built with Tkinter.
* Automatic Active Directory user creation using LDAP over SSL.
* Username generation with transliteration (GOST 7.79).
* Secure password generation.
* Automatic assignment of user attributes.
* Automatic addition to predefined security groups.
* Optional Kerio Mail attribute configuration.
* Generation of a PowerShell script for creating a home directory and assigning NTFS permissions.
* Automatic generation of a personalized Microsoft Word welcome document from a template.
* Clipboard support for both English and Russian keyboard layouts (Ctrl+C / Ctrl+X / Ctrl+V).

## Technologies

* Python
* Tkinter
* ldap3
* DocxTemplate
* python-docx
* iuliia
* PyInstaller

## Workflow

1. Enter employee information.
2. Generate a username and secure password.
3. Create the Active Directory account.
4. Configure user attributes.
5. Add the user to security groups.
6. Generate a PowerShell script for the user's home directory.
7. Generate a personalized welcome document.
8. Display the created credentials.

## Repository Contents

* `ad_user_tool.py` — main application.
* `welcome2.docx` — Word template used for document generation.
* `requirements.txt` — Python dependencies.
* `build.ps1` — automated build script.
* `README.md` — installation and usage instructions.

## Disclaimer

This project is intended for demonstration and educational purposes. All domains, LDAP paths, organizational units, server names, groups, credentials, and company information included in the repository have been replaced with fictional examples.


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
