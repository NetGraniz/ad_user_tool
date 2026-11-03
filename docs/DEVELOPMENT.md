# AD User Tool Development and Build Guide

## Development environment

The complete application targets Windows because it uses Tkinter, NTLM authentication to Active Directory, PowerShell, and Windows EXE packaging. Pure helper functions can be developed on another operating system, but end-to-end verification requires Windows connected to an isolated test domain.

The repository currently has no automated tests, linter, formatter, CI configuration, or Python package metadata. The main file is executed directly.

## Create the environment

From the cloned repository root, run:

```powershell
py -3.12 -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Confirm the active interpreter:

```powershell
python -c "import sys; print(sys.executable); print(sys.version)"
```

The path should point to `.venv\Scripts\python.exe`.

## Dependencies

`requirements.txt` pins both runtime libraries and build tools. It resembles a `pip freeze` snapshot, so direct dependencies are not separated from transitive dependencies.

| Category | Packages |
| --- | --- |
| LDAP | `ldap3`, `pyasn1` |
| Word templates | `docxtpl`, `python-docx`, `docxcompose`, `Jinja2`, `MarkupSafe`, `lxml`, `babel`, `six`, `typing_extensions` |
| Transliteration | `iuliia` |
| Build | `pyinstaller`, `pyinstaller-hooks-contrib`, `altgraph`, `setuptools`, `packaging`, `pefile`, `pywin32-ctypes` |

Tkinter is part of the standard Windows Python installation and is not listed in `requirements.txt`.

Do not replace the dependency file with an unchecked `pip freeze > requirements.txt`. That command records every package in the active environment, including accidental installations. A future cleanup should separate minimal runtime dependencies from development tools.

`setuptools` is pinned to 80.8.0 because the pinned `altgraph 0.17.4` imports `pkg_resources`. Setuptools 80.9 promotes that use to a visible warning, and version 82 removes the module. Upgrade altgraph and PyInstaller together before removing this compatibility pin.

## Run from source

Configure a test server, OU, and groups before connecting to a directory. Then run:

```powershell
python .\ad_user_tool.py
```

Console execution is preferable during development because tracebacks and library messages remain visible. A `--noconsole` build hides them.

The current file cannot be imported safely for unit testing because it creates the GUI at module level and enters `mainloop()`. Before adding tests, place startup behind a guard:

```python
def main():
    # Create root and widgets.
    root.mainloop()


if __name__ == "__main__":
    main()
```

## Current build script

`build.ps1` deletes old `build` and `dist` directories, activates `.venv`, resolves the `iuliia\schemas` directory, and invokes PyInstaller.

```powershell
.\build.ps1
```

The equivalent PyInstaller command is:

```powershell
pyinstaller `
    --clean `
    --onefile `
    --noconsole `
    --name "ad_user_tool" `
    --add-data "$iuliia;iuliia/schemas" `
    ad_user_tool.py
```

| Option | Effect |
| --- | --- |
| `--clean` | Clears PyInstaller cache and temporary files |
| `--onefile` | Bundles the application and dependencies into one EXE |
| `--noconsole` | Prevents a console window from opening with the GUI |
| `--name` | Sets the output name to `ad_user_tool.exe` |
| `--add-data` | Includes the iuliia schemas required for transliteration |

The executable is written to `dist\ad_user_tool.exe`. `build`, `dist`, and `*.spec` are ignored by Git.

## External Word template

The build command does not include:

```text
--add-data "welcome2.docx;."
```

`welcome2.docx` is therefore not bundled. The Python code also does not resolve the PyInstaller extraction directory; it opens a relative path from the current working directory.

Without source changes, distribute the EXE and template together and configure the shortcut's working directory. To bundle the template, add it through `--add-data` and implement resource lookup for both normal execution and `sys._MEIPASS`. See the PyInstaller guide on [Adding Data Files](https://pyinstaller.org/en/stable/spec-files.html#adding-data-files).

## Diagnostic build

If the application closes without an explanation, build a temporary console version:

```powershell
pyinstaller `
    --clean `
    --onefile `
    --name "ad_user_tool_debug" `
    --add-data "$iuliia;iuliia/schemas" `
    ad_user_tool.py
```

Omitting `--noconsole` exposes tracebacks. Do not distribute the diagnostic EXE as a production release if its console can reveal internal paths or other operational details.

## Syntax and import checks

Compile the Python source without starting the GUI:

```powershell
python -m py_compile .\ad_user_tool.py
```

Check key imports:

```powershell
python -c "import ldap3, iuliia, docxtpl; print(ldap3.__version__, iuliia.__version__)"
```

Not every package exposes `__version__`. If the installed iuliia version does not, use:

```powershell
python -m pip show ldap3 iuliia docxtpl pyinstaller
```

## Manual test matrix

| Area | Scenario | Expected result |
| --- | --- | --- |
| GUI | Start source and EXE | A 400 by 300 window opens in the center |
| Validation | Leave each required field empty in turn | `Error` appears and LDAP is not called |
| Clipboard | Copy, Cut, and Paste under English and Russian layouts | Values are transferred exactly once |
| Names | Non-Latin text, hyphens, spaces, and compound surnames | The result is recorded and follows the approved rule |
| Collision | The generated login already exists | The error is recognized and the existing object is unchanged |
| Password | Domain policy is stricter than the generated format | The operator receives a clear failure and the account is not reported as ready |
| LDAPS | Trusted and untrusted certificates | The trusted certificate succeeds and the untrusted one fails after TLS hardening |
| OU | Valid and nonexistent DNs | Success or a clearly diagnosed `noSuchObject` |
| Permissions | The service account lacks one permission | Partial success is recognized and not hidden by `Done` |
| Groups | Valid and nonexistent group | The failure identifies the affected DN |
| Kerio | Schemas with and without Kerio attributes | Configuration selects only supported fields |
| PS1 | New and existing directory | ACL and HomeDirectory remain predictable |
| DOCX | Present, missing, and corrupted template | Success or a clear warning |
| Path | Working directory is not writable | The operator is told that the local artifact failed after any AD change |
| Build | Clean Windows machine without Python | The EXE starts, iuliia works, and the external template is found |

## Checking LDAP results during development

Inspect the Boolean return value and `conn.result` after every modifying call. A minimal wrapper is:

```python
def require_ldap_success(connection, ok: bool, operation: str) -> None:
    if not ok:
        result = connection.result or {}
        description = result.get("description", "unknown")
        message = result.get("message", "")
        raise RuntimeError(f"{operation}: {description}: {message}")
```

Use it as follows:

```python
ok = conn.add(user_dn, "user", attributes)
require_ldap_success(conn, ok, "Create AD user")
```

Microsoft extension calls must also be checked. Never write passwords or the complete Word context to logs.

## Suggested automated tests

| Test | Isolation strategy |
| --- | --- |
| Password format | Replace the random source and verify length and character classes |
| Login generation | Table-driven non-Latin names, hyphens, and compound values |
| Validation | Pure function returning field errors without Tkinter |
| LDAP attributes | Compare the generated dictionary with an expected fixture |
| LDAP failures | ldap3 mock strategy or a test AD with controlled responses |
| PowerShell template | Verify the path, login, and absence of unresolved markers |
| Word context | Render a temporary copy and inspect the document XML |
| EXE resources | Smoke test on a clean Windows VM |

## Versioning and release

Before release, define the application version in one place, update documentation when attributes or operation order change, build the EXE in a clean virtual environment, record its hash, and sign it with a corporate code-signing certificate when required.

Do not commit `dist`, `.venv`, a real employee template, generated `.ps1` or `.docx` files, private-key certificates, or secret files. Generated `<login>.ps1` and `<Surname First name>.docx` are not automatically ignored, so check `git status` before every commit.

## Related documentation

See [Architecture](ARCHITECTURE.md), [Configuration](CONFIGURATION.md), [Troubleshooting](TROUBLESHOOTING.md), and [Security](../SECURITY.md).
