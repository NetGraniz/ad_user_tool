# AD User Tool Troubleshooting

## Diagnostic approach

Identify the failing stage first: application startup, form validation, LDAP connection or modification, PS1 writing, Word rendering, or execution of the generated script. Do not click `To create` again until you have checked the object state in Active Directory.

The current EXE uses `--noconsole`, so tracebacks are hidden. For diagnosis, run `python ad_user_tool.py` from PowerShell or build the temporary console version described in [Development](DEVELOPMENT.md).

## Application does not start

| Symptom | Likely cause | Check and action |
| --- | --- | --- |
| `python` is not found | Python is missing or absent from PATH | Run `py --version` and use `py -3.12` |
| `ModuleNotFoundError` | `.venv` is inactive or dependencies are missing | Activate the environment and run `python -m pip install -r requirements.txt` |
| Tkinter error | Incomplete Python installation | Run `python -m tkinter`; install the standard Windows Python distribution with Tcl/Tk if necessary |
| EXE closes immediately | `--noconsole` hides an exception | Run from source or use the diagnostic console build |
| Antivirus blocks the EXE | Heuristic detection of an unsigned one-file application | Review the security-product log, hash, and provenance; do not disable protection globally |

Check the environment:

```powershell
python -c "import sys, tkinter, ldap3, iuliia, docxtpl; print(sys.executable)"
python -m pip check
```

## Button appears unresponsive or the window freezes

LDAP operations run in Tkinter's main thread. During DNS, TCP 636, or NTLM delays, the window cannot repaint until the call returns. Do not click the button again.

Test DNS and the port separately:

```powershell
Resolve-DnsName dc01.example.local
Test-NetConnection dc01.example.local -Port 636
```

If the port is unreachable, inspect routing, host and network firewalls, LDAPS availability on the controller, and the configured server name.

## LDAPS connection errors

### `LDAPSocketOpenError` or socket failure

Typical causes are an incorrect server name, unreachable TCP 636, missing LDAPS, DNS failure, or TLS interruption. `Test-NetConnection` proves only that a port is reachable, not that LDAP bind succeeds.

Use an approved TLS diagnostic tool or OpenSSL when available:

```powershell
openssl s_client -connect dc01.example.local:636 -servername dc01.example.local -showcerts
```

Compare certificate validity, trust chain, and SAN entries with the FQDN used by the application.

### An untrusted certificate is accepted

This matches the current implementation. `Server(..., use_ssl=True)` is created without `Tls(validate=ssl.CERT_REQUIRED)`, so ldap3 does not validate the certificate. Add mandatory validation before production use; [Configuration](CONFIGURATION.md) contains an example.

### `invalidCredentials`

Check `AD_USER` format, password, service-account lockout and expiry, allowed authentication methods, and clock synchronization. NTLM normally expects `DOMAIN\\username`, where `DOMAIN` is the NetBIOS name.

Never print `AD_PASSWORD` or attach it to a ticket or issue.

## User is not created

| LDAP description | Typical cause | What to inspect |
| --- | --- | --- |
| `noSuchObject` | Invalid `usersOU` or group DN | Existence and order of every OU and DC component |
| `entryAlreadyExists` | The CN already exists in the OU | Locate the existing object; do not repeat automatically |
| `insufficientAccessRights` | Missing delegation | Object creation, attribute writes, password reset, UAC, and group membership |
| `objectClassViolation` | Unsupported attribute or schema | Kerio attributes and every field allowed for class `user` |
| `constraintViolation` | Type, length, or policy violation | `countryCode`, UPN, password, value lengths, and schema constraints |
| `invalidDNSyntax` | Invalid DN | Commas, reserved-character escaping, spaces, and component order |
| `unwillingToPerform` | Controller rejected the operation | LDAPS for password changes, password policy, object state, and detailed server message |

`conn.add()` and `conn.modify()` may return `False` without raising. The current code checks neither the return value nor `conn.result`, so the UI can display `Done` after a directory refusal.

For temporary development diagnostics, inspect the result without printing any password:

```python
ok = conn.add(user_dn, "user", attributes)
print(ok, conn.result)
```

Replace `print` with structured handling and safe logging before production use.

## User exists but the password was not set

Active Directory password changes require a protected connection and compliance with domain policy. Check LDAPS, delegated Reset password rights, minimum length, complexity, history, and banned values.

The current generator always produces 9 characters. A policy requiring 12 or 14 rejects the operation. After correcting the issue, do not rerun the entire application. Set the password on the existing test object through a controlled procedure, or remove only the test object after analysis.

## User is disabled or has incorrect flags

```powershell
Get-ADUser -Identity '<login>' -Properties Enabled,PasswordNeverExpires,LockedOut |
    Select-Object SamAccountName,Enabled,PasswordNeverExpires,LockedOut
```

The code should write `userAccountControl = 66048`, which combines a normal account with a non-expiring password. If the modification failed, the object may remain disabled after the initial add.

## Group membership is incomplete

```powershell
Get-ADPrincipalGroupMembership '<login>' |
    Sort-Object Name |
    Select-Object Name,GroupScope,GroupCategory
```

Compare the result with every DN in `groups`. The service account needs permission on the group object's `member` attribute, not merely on the user OU. Do not correct one invalid group DN by recreating the user.

The application does not identify which group modification returned `False`. During development, inspect `conn.result` inside the loop and include the safe group DN in the error.

## Kerio Connect errors

Remove `kerio-Mail-AccountEnabled` and `kerio-Mail-Active` when the domain schema does not contain them. In an extended schema, verify exact spelling, syntax, and allowed values against a supported reference account.

The presence of attributes does not prove that Kerio created a mailbox. Synchronization and activation are outside this application and must be checked separately in the mail system's administration console.

## `PS Error`

This warning refers to writing `<login>.ps1`, not to executing PowerShell. Causes include a non-writable working directory, invalid filename, another process locking the file, endpoint protection blocking script creation, or exhausted disk quota.

Check the working directory and write access:

```powershell
Get-Location
$test = Join-Path (Get-Location) 'write-test.tmp'
New-Item -Path $test -ItemType File -ErrorAction Stop
Remove-Item $test
```

A successful AD change is not undone by `PS Error`. Inspect Active Directory before retrying anything.

## Generated PS1 fails

| Message | Cause | Action |
| --- | --- | --- |
| `Get-ADUser is not recognized` | ActiveDirectory module is missing | Install or enable RSAT AD DS and import the module |
| User not found | Wrong login or AD creation did not complete | Run `Get-ADUser -Identity` manually |
| `Access is denied` from `Set-ADUser` | Missing HomeDrive or HomeDirectory write permission | Delegate the minimum required rights |
| `Access is denied` from `New-Item` | Missing file-share permission | Check share and NTFS rights on the root |
| `The network path was not found` | UNC, DNS, or SMB failure | Verify the file-server name and TCP 445 |
| `Set-Acl` failure | Invalid ACL, ownership, or insufficient rights | Compare with a reference directory and inspect the execution identity |
| Directory already exists | A retry or an earlier object created it | Do not delete automatically; inspect owner and ACL |

Check the file share:

```powershell
Test-NetConnection files01.example.local -Port 445
Test-Path '\\files01.example.local\Users'
```

The script uses `NoPropagateInherit`. If organizational policy expects different inheritance, the result can diverge from the reference even without an exception.

## `Word Error`

### `welcome2.docx` is missing

```powershell
Get-Location
Test-Path .\welcome2.docx
```

When using a shortcut, configure its `Start in` directory. The current `build.ps1` does not bundle the template.

### Template is corrupt or not a DOCX

Open a copy in Word or a compatible editor and save it as a standard `.docx`. Legacy `.doc`, protected documents, and files with a misleading extension are unsupported.

### Variables remain in the rendered document

Verify the exact names `{{ name }}`, `{{ login }}`, `{{ email }}`, and `{{ password }}`. A variable must not be split across Word runs with different formatting. Compare it with the keys in the Python `context` dictionary.

### Document cannot be saved

Possible causes include missing write permission, an open `<Surname First name>.docx`, invalid filename characters, or endpoint-protection restrictions. Close the document, switch to a test directory, and repeat only the render after checking AD state.

## PyInstaller build errors

### `.venv` is missing

`build.ps1` explicitly calls `.\.venv\Scripts\Activate.ps1`. Create an environment with that name or change the script deliberately.

### PowerShell execution policy error

Allow scripts only for the current process:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\build.ps1
```

Do not change the entire machine policy without approval.

### Transliteration fails after packaging

Inspect `$iuliia` and confirm that the schema directory exists:

```powershell
.\.venv\Scripts\Activate.ps1
python -c "import pathlib, iuliia; print(pathlib.Path(iuliia.__file__).parent / 'schemas')"
```

`--add-data` must receive an existing directory. Build a diagnostic console version and inspect the traceback.

### EXE works only on the development machine

Check Windows architecture, downloaded-file blocking, antivirus, external `welcome2.docx`, working directory, network access, DNS, LDAPS certificate trust, and service-account permissions. A one-file build normally does not require Python on the target machine, but its network and template dependencies remain.

## Collecting diagnostic data

An internal ticket should include time, source version or EXE hash, failed stage, exact error text without passwords, controller FQDN, target OU, employee login, object existence after failure, and safe network-check results.

Do not attach the service-account password, employee password, completed credential DOCX, private keys, a complete environment dump, or unfiltered packet capture.

## Related documentation

See [Configuration](CONFIGURATION.md), [Usage](USAGE.md), [Development](DEVELOPMENT.md), and [Security](../SECURITY.md).
