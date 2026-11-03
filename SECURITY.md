# AD User Tool Security

## Current status

The current implementation is a prototype. Do not connect it to a production domain until the required controls have been implemented and reviewed by the responsible security team. The application creates accounts, sets passwords, changes group membership, and produces credential files. A configuration error can therefore affect confidentiality, directory integrity, and employee access at the same time.

## Primary risks

| Priority | Risk | Current state | Required control |
| --- | --- | --- | --- |
| Critical | Service-account compromise | `AD_PASSWORD` is stored as a source-code string and is embedded in the EXE | Retrieve the secret from an approved vault, remove it from Git history, and rotate any exposed password |
| Critical | LDAP server impersonation | LDAPS is enabled, but certificate validation is not configured explicitly | Use `Tls(validate=ssl.CERT_REQUIRED)`, a trusted CA, and an FQDN |
| High | Weak initial passwords | The code uses `random`, a length of 9, and fixed character-class positions | Use `secrets`, an approved length, and domain-policy validation |
| High | False success reporting | Return values from `conn.add()`, `conn.modify()`, and `conn.result` are not checked | Stop after every failed LDAP operation and show safe diagnostics |
| High | Excessive privileges | The delegation model is not enforced by the application | Use a dedicated service account delegated only to the target OU, attributes, and groups |
| High | Non-expiring user passwords | `userAccountControl = 66048` includes `DONT_EXPIRE_PASSWORD` | Align the setting with policy; normally remove the flag and require a change at first sign-in |
| High | Employee password disclosure | The password is displayed and stored in an unencrypted DOCX | Separate delivery channels, restrict ACLs, define deletion deadlines, and omit the password when possible |
| Medium | Partially provisioned user | There is no transaction or rollback | Record each step, provide compensating actions, and document recovery |
| Medium | Login collision or malformed login | There is no AD lookup or compound-name handling | Check uniqueness and preview the login before writing |
| Medium | Invalid DN | The full name is inserted into the CN without LDAP escaping | Use a supported DN-escaping function and validate input |
| Medium | Uncontrolled artifacts | PS1 and DOCX files are written to the working directory | Use a protected output directory, apply ACLs, log only non-secret paths, and clean up files |
| Medium | Missing application audit | No structured audit log exists | Record request ID, operator, object, step status, and error codes without passwords |

## Service account

Do not use Domain Admin or an operator's personal administrative account. Create a dedicated service account and delegate only the actions required in the specific OU and groups.

The application needs permission to create a user object, write the selected attributes, reset the password, change account state, unlock the account, and update the `member` attribute of approved groups. Group permissions must be granted individually. Editing the local `groups` list must never be enough to gain the ability to add users to privileged groups.

Do not store the secret in a Python file, README, committable `.env`, command-line argument, unprotected registry value, or shared network directory. A string embedded in a PyInstaller executable can be extracted; packaging is not secret protection.

If a real password appears in repository history, deleting the current line is insufficient. Revoke the credential first, assess repository access, and then clean the history through an approved process.

## LDAPS protection

Encryption without server authentication does not prevent impersonation. The ldap3 documentation states that `use_ssl=True` without a configured `Tls` object does not validate the certificate. Production configuration must require a trusted certificate and verify the domain controller name.

Use an FQDN present in the certificate SAN. Pin or otherwise trust the corporate CA correctly. Do not use `CERT_NONE` as a permanent workaround. A validation error must block provisioning rather than downgrade the connection.

Official reference: [ldap3 SSL and TLS](https://ldap3.readthedocs.io/en/latest/ssltls.html).

## Password generation and policy

Python's `random` module is intended for modelling and statistical work, not secrets. The Python documentation directs password and token generation to `secrets`.

A replacement generator must use a cryptographically secure source, sufficient length, an approved alphabet, and validation against domain requirements. Random character-class placement is preferable to a fixed pattern. Never log a password or include it in exception text.

If policy requires a password change at first sign-in, implement the appropriate attribute and test its interaction with Kerio, VPN, and other systems. UAC value `66048` combines `NORMAL_ACCOUNT` and `DONT_EXPIRE_PASSWORD`, as documented in [Microsoft userAccountControl guidance](https://learn.microsoft.com/en-us/troubleshoot/windows-server/active-directory/useraccountcontrol-manipulate-account-properties).

Official references: [Python `secrets`](https://docs.python.org/3/library/secrets.html) and the [warning for Python `random`](https://docs.python.org/3/library/random.html).

## Delivering employee credentials

The current application displays the password in a modal dialog and inserts it into a DOCX file. This creates secret copies in memory, on screen, on local storage, in backups, and potentially in synchronization history.

Define an approved delivery process. For example, send the login through a corporate channel and the one-time password through a separate verified channel. Create the document in a directory with restricted ACLs and delete it after receipt is confirmed. Recycle bins, synchronization services, and backups may retain deleted copies longer than expected.

Do not send the login and password together by ordinary email. Never attach a DOCX containing real credentials to a public GitHub issue.

## Validating LDAP results

Every modifying call must check its Boolean return value and `conn.result`. Do not begin the next step until the previous one is confirmed. Group errors may identify the safe DN of the affected group, but must never expose a password.

After creation, read the object back and compare critical attributes with the expected values. UI success should mean that creation, password assignment, UAC state, and group membership have been confirmed.

Automatic rollback must be conservative. Do not delete an object merely because its login matches. The application must prove that the current operation created the object and that another administrator has not modified it.

## Input and DN construction

The operator supplies the first and last name used in the CN and output filename. LDAP DNs have reserved characters and escaping rules. Use a supported ldap3 escaping function, enforce length limits, and handle commas, plus signs, quotation marks, backslashes, number signs, and leading or trailing spaces explicitly.

Sanitize the output DOCX filename separately under Windows filename rules. Login filtering is not sufficient because `fname`, which becomes the document name, does not pass through the same filter.

Title, department, and description are not executed as code, but they are written to the directory and displayed by other systems. Restrict their length and reject invalid control characters.

## PowerShell and home directories

The application writes but does not execute a PS1 file. That file is still an administrative script. Store it in a protected directory, review it before execution, and sign it with a corporate code-signing certificate when available.

The login is reduced to alphanumeric characters, which lowers PowerShell-injection risk through `$samAccountName`. The root path remains static source configuration and must also be reviewed. Do not insert operator-provided data into it without correct escaping.

The `Modify` ACL, inheritance flags, and `NoPropagateInherit` setting must match the file-server standard. Verify share permissions, ownership, inherited administrative ACEs, quotas, auditing, and backups as well.

## Word template and local files

Use a trusted `welcome2.docx` template with controlled provenance and a recorded hash. Restrict modification rights. A replaced template can alter employee instructions, add external links, or direct the operator to a fraudulent resource.

The current `.gitignore` does not automatically exclude generated `.ps1` and `.docx` files. Check `git status` before every commit. A safer design writes artifacts to a dedicated ignored `output/` directory.

## Logging and audit

A safe log should contain time, request ID, operator, target domain, user DN, calculated login, operation status, and error codes. It must not include the service-account password, employee password, complete Word context, private keys, or secret tokens.

Correlate the application log with Active Directory auditing and the request system. Every operation should have an identifiable business reason, initiator, and outcome.

Protect the log from ordinary-operator changes and define retention. Detailed LDAP messages can reveal directory structure, so access to them must also be restricted.

## Secure build and distribution

Build releases in a clean virtual environment from a verified commit. Review Python dependencies, record the EXE hash, and sign the executable when corporate PKI is available. Never distribute production configuration in a public build.

PyInstaller bundles code and data but does not encrypt them. Do not embed passwords, private keys, or other long-lived secrets. A template included through `--add-data` is extracted to a temporary directory when a one-file application starts.

## Production-readiness criteria

| Control | Acceptance criterion |
| --- | --- |
| Secrets | No production password exists in code, Git, or the EXE; the secret source is approved |
| Permissions | The service account has documented least-privilege delegation |
| TLS | The certificate and server name are validated with no insecure fallback |
| Passwords | `secrets` is used, length and policy are approved, and first-sign-in change is configured when required |
| LDAP | Every call is checked and the resulting object is read back |
| Logins | Preview, uniqueness checking, and collision handling exist |
| Input | DNs and filenames are escaped and validated correctly |
| Groups | The allowed set is policy-controlled; privileged groups require separate approval |
| Artifacts | DOCX and PS1 files are created in protected storage and removed according to policy |
| Audit | The operation is linked to a request and logged without secrets |
| Errors | Partial success is visible and a tested recovery plan exists |
| Tests | Scenarios pass in an isolated OU and on a clean Windows machine |
| Release | The EXE is reproducibly built, tested, hashed, and signed when required |

## Reporting a vulnerability

Do not publish a vulnerability report together with production DNs, passwords, server addresses, or employee files. Use a private owner channel or GitHub private vulnerability reporting when enabled. Include the affected commit, a reproducible scenario using fictional data, potential impact, and the proposed mitigation.
