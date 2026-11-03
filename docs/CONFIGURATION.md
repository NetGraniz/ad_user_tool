# AD User Tool Configuration

## Configuration model

The current version has no separate configuration file. Domain settings, groups, organization details, mail domains, and the file-server path are defined directly inside `create_user()` in `ad_user_tool.py`. Replace every demonstration marker before the first run and validate the result in an isolated test OU.

Never commit a production service-account password. A production design should retrieve it from Windows Credential Manager or an approved corporate secret store. Move non-secret settings to a separate local configuration file excluded from Git.

## Source-code settings

| Value | Purpose | Example format |
| --- | --- | --- |
| `AD_SERVER` | Domain controller used for LDAPS | `dc01.example.local` |
| `AD_USER` | Account used for LDAP operations | `EXAMPLE\\svc_ad_provision` |
| `AD_PASSWORD` | Service-account password | Retrieve from a protected external source |
| `usersOU` | Distinguished Name of the target OU | `OU=Employees,OU=Users,DC=example,DC=local` |
| `@Your domain` in `userPrincipalName` | UPN suffix | `@example.local` or an approved alternate UPN |
| `@Your domain` in `mail` | Primary email domain | `@example.com` |
| `company` | Organization name stored on the user | `Example LLC` |
| `st` | State or region | Value defined by the corporate directory standard |
| `streetAddress` | Organization address | Postal-address string |
| `c` | Country code accepted by the AD schema | Usually a two-letter value such as `US` |
| `countryCode` | Numeric country code used by the AD schema | Organization-approved numeric value |
| `l` | City | `London` |
| `postalCode` | Postal code | Postal-code string |
| `kerio-Mail-AccountEnabled` | Enables a Kerio mail account | `1`, only when the schema contains this attribute |
| `kerio-Mail-Active` | Kerio domain or service value | Value expected by the Kerio integration |
| `groups` | Full DNs of groups assigned to the employee | `CN=AllUsers,OU=Groups,DC=example,DC=local` |
| `$fullPath` in the generated PS1 | Home-directory root | `\\files01.example.local\Users\<login>` |
| `$driveLetter` | Home-drive letter | `Z:` |
| `@your domain` in the Word context | Email domain used in the document | `@example.com` |
| `welcome2.docx` | Relative template path | File in the current working directory |

Search for unresolved demonstration markers from the repository root:

```powershell
Select-String -Path .\ad_user_tool.py -Pattern 'Replace|Your domain|your domain|IP of AD server|the address of the server'
```

This command should return no results only in a locally configured working copy. Never publish a file after inserting real credentials.

## Active Directory connection

### Server name and port

The code constructs the server object as follows:

```python
server = Server(AD_SERVER, use_ssl=True, port=636)
```

Use a DNS name included in the certificate SAN, such as `dc01.example.local`. An IP address often does not match the certificate identity and prevents correct authentication. The firewall must permit outbound TCP 636 to the selected controller.

The current implementation does not pass a `Tls` object. According to ldap3 documentation, the server certificate is not validated in this configuration. Add mandatory trust-chain validation before production use:

```python
import ssl
from ldap3 import Server, Tls

tls = Tls(
    validate=ssl.CERT_REQUIRED,
    ca_certs_file=r"C:\ProgramData\ADUserTool\domain-ca.pem",
)
server = Server(AD_SERVER, port=636, use_ssl=True, tls=tls)
```

Obtain the CA file through a trusted channel and make it read-only for ordinary users. If the organization relies on the system trust store, verify the correct integration on the target Python and ldap3 versions.

### Service account

With `authentication=NTLM`, `AD_USER` is normally written as `NETBIOS_DOMAIN\\username`. Delegate only the required operations: create users in the target OU, write the listed attributes, reset passwords, change `userAccountControl`, unlock accounts, and add members to the approved groups.

Do not use Domain Admin. A dedicated service account simplifies revocation, auditing, and impact containment.

A minimal step away from a hard-coded password is:

```python
AD_PASSWORD = os.environ["AD_USER_TOOL_PASSWORD"]
```

An environment variable still exposes the secret in process state. It is better than a source-code string, but it is not a substitute for a corporate secret store. Treat the example as a refactoring direction, not a complete credential design.

## Target OU and Distinguished Name

`usersOU` must contain the full DN of the employee container, ordered from the innermost OU toward the domain root:

```python
usersOU = "OU=Employees,OU=Users,DC=example,DC=local"
```

The application builds the user DN as `CN=<Surname First name>,<usersOU>`. It does not currently escape reserved DN characters. Test apostrophes, commas, backslashes, and leading or trailing spaces separately; add ldap3-supported escaping before production use.

## UPN, login, and email

The application generates `sAMAccountName` automatically. It combines the first-name initial with the surname, transliterates the value through `GOST_779_ALT`, and retains only alphanumeric characters. The algorithm assumes single-token names and does not check whether the login already exists.

`userPrincipalName`, the LDAP `mail` attribute, and the email address in the Word document are set in three places. If the sign-in domain and email domain differ, configure each suffix deliberately:

```python
'userPrincipalName': tname2 + '@example.local',
'mail': tname2 + '@example.com',

context = {
    'name': fname,
    'login': tname2,
    'email': tname2 + '@example.com',
    'password': userpswd,
}
```

The UPN suffix must be allowed in the Active Directory forest. The email domain must match Kerio Connect and corporate address-book rules.

## Form fields and AD attributes

| Form field | Processing | Active Directory attribute |
| --- | --- | --- |
| `Surname*` | `strip().title()` | `sn`; also used in `displayName` and the CN |
| `Name*` | `strip().title()` | `givenName`; also used in `displayName` and login generation |
| `Employee's position*` | `strip().title()` | `title` |
| `Department / Division*` | `strip().title()` | `department` |
| `Phone number (short)` | A single space when empty | `telephoneNumber` |
| `Phone number` | A single space when empty | `mobile` |
| `Room*` | Combined with the workstation number | `physicalDeliveryOfficeName` |
| `No. workplace` | Combined as `<room> - <workstation>` | `physicalDeliveryOfficeName` |
| `Description` | A single space when empty | `description` |

`.title()` may change all-uppercase abbreviations. Remove that transformation from fields where exact case matters.

For optional attributes, the current code inserts a single space. Omitting absent attributes from the dictionary would be more predictable. Until that change is made, confirm that the target AD schema accepts whitespace-only values.

## Organization and country attributes

The application writes `company`, `st`, `streetAddress`, `c`, `countryCode`, `l`, and `postalCode` for every employee. The AD schema determines each attribute's type and allowed format. The demonstration value `Replace` is not a valid numeric `countryCode`; replace it or remove the attribute until configuration is complete.

After creating a test user, compare the actual values in Attribute Editor with an approved corporate reference account.

## Kerio Connect

These attributes are required only in a domain whose schema has been extended for Kerio:

```python
'kerio-Mail-AccountEnabled': '1',
'kerio-Mail-Active': 'example.com',
```

If the schema does not contain them, user creation may fail. Remove both values in non-Kerio environments. In Kerio environments, compare names and values with an account created through a supported process and test in an isolated OU first.

## Security groups

Each item in `groups` must be the full DN of an existing group:

```python
groups = [
    "CN=VPN Users,OU=Groups,DC=example,DC=local",
    "CN=All Users,OU=Groups,DC=example,DC=local",
]
```

The service account needs permission to write the `member` attribute of every group. The application does not validate group type, scope, nesting, existing membership, or the result of each operation. A failure on one group does not automatically reverse membership added to earlier groups.

## Account flags

After creating the object, the application unlocks it, sets the password, and writes `userAccountControl = 66048`. This is `512` (`NORMAL_ACCOUNT`) plus `65536` (`DONT_EXPIRE_PASSWORD`). The result is an enabled ordinary domain account whose password does not expire.

Do not use this value if corporate policy requires an initial password change or prohibits non-expiring user passwords. Implement and test the policy change explicitly; changing the number without validating operation order is insufficient.

## Home directory

The Python source defines the UNC path template and drive letter:

```powershell
$fullPath = "\\files01.example.local\Users\<login>"
$driveLetter = "Z:"
```

The generated script calls `Get-ADUser`, writes `HomeDrive` and `HomeDirectory`, creates the directory, and adds inherited `Modify` permission for the user's SID. It does not disable parent inheritance or remove existing ACEs.

Before the first run, verify administrator access to the root share, UNC availability, inheritance policy, Access-Based Enumeration requirements, backups, and quotas. If the directory already exists, `New-Item -Force` reuses it and the script adds another ACE to the current ACL.

## Word template

The code opens `welcome2.docx` relative to the current working directory and supplies four values:

| Template variable | Value |
| --- | --- |
| `{{ name }}` | `<Surname> <First name>` |
| `{{ login }}` | Generated `sAMAccountName` |
| `{{ email }}` | Login plus configured email suffix |
| `{{ password }}` | Generated initial password |

Variables must remain valid Jinja2 expressions supported by DocxTemplate. Do not split one variable into multiple Word runs with different formatting, because the template engine may no longer recognize it correctly.

The output is saved as `<Surname First name>.docx` in the current working directory. An existing file with the same name may be overwritten without confirmation. The document contains a plaintext password and must be handled as confidential.

## Configuration preflight

| Control | Ready when |
| --- | --- |
| Test scope | A separate OU exists with no production users |
| Name resolution | The controller FQDN resolves through corporate DNS |
| LDAPS | TCP 636 is reachable and the client validates a trusted certificate |
| Delegation | The service account has no excessive privileges |
| OU | The DN is verified through ADUC, ADSI Edit, or PowerShell |
| Attributes | All values meet schema constraints |
| Kerio | Attributes exist or are removed from configuration |
| Groups | DNs exist and `member` writes are permitted |
| Logins | Collision and compound-name rules are defined |
| Password | Format and lifetime match domain policy |
| File server | The UNC path and ACL model pass testing on a test directory |
| Template | All four variables are replaced in a rendered copy |
| Secrets | No production password exists in Git or source code |

## Related documentation

See [Usage](USAGE.md) for daily operation, [Architecture](ARCHITECTURE.md) for internal sequencing, [Troubleshooting](TROUBLESHOOTING.md) for common failures, and [Security](../SECURITY.md) for production requirements.
