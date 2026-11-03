import tkinter as tk
from tkinter import messagebox
import iuliia
from ldap3 import Server, Connection, NTLM, MODIFY_REPLACE, MODIFY_ADD
from docxtpl import DocxTemplate
import random
import string
import os

# -------------------- Password generation --------------------
def generate_password():
    upper = random.choice(string.ascii_uppercase)
    lower = random.choice(string.ascii_lowercase)
    digits = ''.join(random.choices(string.digits, k=6))
    special = random.choice(['#', '!', '@'])
    return upper + lower + digits + special

# -------------------- Russians Ctrl+C/X/V --------------------
def bind_russian_clipboard(widget):
    # Key codes that correspond to Ctrl+C/X/V on the Russian keyboard layout.
    rus_ctrl_map = {
        75: 'copy',
        88: 'cut',
        86: 'paste'
    }

    def handler(event):
        if (event.state & 0x4) != 0:  # Ctrl pressed
            action = rus_ctrl_map.get(event.keycode)
            if action == 'copy':
                widget.event_generate("<<Copy>>")
                return "break"
            elif action == 'cut':
                widget.event_generate("<<Cut>>")
                return "break"
            elif action == 'paste':
                widget.event_generate("<<Paste>>")
                return "break"

    widget.bind("<KeyPress>", handler)

# -------------------- Creating a user --------------------
def create_user():
    name = entry_name.get().strip().title()
    sname = entry_sname.get().strip().title()
    title = entry_title.get().strip().title()
    departament = entry_department.get().strip().title()
    telephoneNumber = entry_phone.get().strip()
    mobile = entry_mobile.get().strip()
    physicalDeliveryOfficeName = entry_room.get().strip()
    numWS = entry_ws.get().strip()
    description = entry_desc.get().strip()

    if not name or not sname or not title or not departament or not physicalDeliveryOfficeName:
        messagebox.showerror("Error", "Fill in all required fields (*)")
        return

    fname = f"{sname} {name}"
    source_name = f"{name} {sname}"
    translited_name = source_name[0].lower() + source_name.split()[1].lower()
    tname2 = ''.join(filter(str.isalnum, iuliia.translate(translited_name, schema=iuliia.GOST_779_ALT)))

    userpswd = generate_password()

    telephoneNumber = telephoneNumber if telephoneNumber else " "
    mobile = mobile if mobile else " "
    description = description if description else " "
    numWS = numWS if numWS else " "

    try:
        AD_SERVER = 'IP of AD server'
        AD_USER = 'Your domain\\A user with creation rights'
        AD_PASSWORD = 'Replace Password'
        usersOU = 'OU=Replace,OU=Replace,DC=Replace,DC=Replace'

        server = Server(AD_SERVER, use_ssl=True, port=636)
        conn = Connection(server, AD_USER, AD_PASSWORD, authentication=NTLM, auto_bind=True)
        user_dn = f'cn={fname},{usersOU}'

        conn.add(user_dn, 'user', {
            'sAMAccountName': tname2,
            'userPrincipalName': tname2 + '@Your domain',
            'mail': tname2 + '@Your domain',
            'givenName': name,
            'sn': sname,
            'displayName': fname,
            'department': departament,
            'title': title,
            'telephoneNumber': telephoneNumber,
            'mobile': mobile,
            'physicalDeliveryOfficeName': physicalDeliveryOfficeName + ' - ' + numWS,
            'description': description,
            'company': 'Replace"',
            'st': 'Replace',
            'streetAddress': 'Replace',
            'c': 'Replace',
            'countryCode': 'Replace',
            'l': 'Replace',
            'postalCode': 'Replace',
            'kerio-Mail-AccountEnabled': '1', # If you use kerio mail
            'kerio-Mail-Active': 'Your domain'
        })

        conn.extend.microsoft.unlock_account(user_dn)
        conn.extend.microsoft.modify_password(user_dn, new_password=userpswd, old_password=None)
        conn.modify(user_dn, {"userAccountControl": [(MODIFY_REPLACE, [66048])]})

        groups = [
            "CN=Example,OU=Groups,OU=Replace,DC=Replace,DC=Replace",
            "CN=AllUsers,OU=Replace,DC=Replace,DC=Replace",
            
        ]
        for group_dn in groups:
            conn.modify(group_dn, {'member': (MODIFY_ADD, [user_dn])})

    except Exception as e:
        messagebox.showerror("AD Error", str(e))
        return

    # -------------------- PowerShell script --------------------
    ps_path = os.path.join(os.getcwd(), f"{tname2}.ps1")
    try:
        with open(ps_path, "w", encoding="utf-8") as my_file:
            my_file.write(f'''$samAccountName = "{tname2}"
$fullPath = "\\\\the address of the server where the user folders are located\\Users\\{tname2}"
$driveLetter = "Z:"
$User = Get-ADUser -Identity $samAccountName
if($User -ne $Null) {{
    Set-ADUser $User -HomeDrive $driveLetter -HomeDirectory $fullPath -ea Stop
    $homeShare = New-Item -path $fullPath -ItemType Directory -force -ea Stop
    $acl = Get-Acl $homeShare
    $FileSystemRights = [System.Security.AccessControl.FileSystemRights]"Modify"
    $AccessControlType = [System.Security.AccessControl.AccessControlType]::Allow
    $InheritanceFlags = [System.Security.AccessControl.InheritanceFlags]"ContainerInherit, ObjectInherit"
    $PropagationFlags = [System.Security.AccessControl.PropagationFlags]"NoPropagateInherit"
    $AccessRule = New-Object System.Security.AccessControl.FileSystemAccessRule ($User.SID, $FileSystemRights, $InheritanceFlags, $PropagationFlags, $AccessControlType)
    $acl.AddAccessRule($AccessRule)
    Set-Acl -Path $homeShare -AclObject $acl -ea Stop
    Write-Host ("HomeDirectory created at {0}" -f $fullPath)
}}''')
    except Exception as e:
        messagebox.showwarning("PS Error", f"PowerShell the script has not been created: {e}")

    # -------------------- Word --------------------
    try:
        doc = DocxTemplate("welcome2.docx")
        context = {'name': fname, 'login': tname2, 'email': tname2 + '@your domain', 'password': userpswd}
        doc.render(context)
        doc.save(f"{fname}.docx")
    except Exception as e:
        messagebox.showwarning("Word Error", f"The document has not been created: {e}")

    messagebox.showinfo("Done", f"The user has been created!\nLogin: {tname2}\nPass: {userpswd}")

# -------------------- GUI --------------------
root = tk.Tk()
root.title("Adding a user to AD")

window_width = 400
window_height = 300
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
x_cordinate = int((screen_width/2) - (window_width/2))
y_cordinate = int((screen_height/2) - (window_height/2))
root.geometry(f"{window_width}x{window_height}+{x_cordinate}+{y_cordinate}")

labels = [
    ("Surname*", 0), ("Name*", 1), ("Employee's position*", 2),
    ("Department / Division*", 3), ("Phone number (short)", 4),
    ("Phone number", 5), ("Room*", 6), ("№ workplace", 7),
    ("Description", 8)
]

entry_sname = tk.Entry(root)
entry_name = tk.Entry(root)
entry_title = tk.Entry(root)
entry_department = tk.Entry(root)
entry_phone = tk.Entry(root)
entry_mobile = tk.Entry(root)
entry_room = tk.Entry(root)
entry_ws = tk.Entry(root)
entry_desc = tk.Entry(root)

entries = [entry_sname, entry_name, entry_title, entry_department,
           entry_phone, entry_mobile, entry_room, entry_ws, entry_desc]

for i, (text, row) in enumerate(labels):
    tk.Label(root, text=text).grid(row=row, column=0, sticky='e', padx=5, pady=2)
    entries[i].grid(row=row, column=1, padx=5, pady=2)
    bind_russian_clipboard(entries[i])  # Add clipboard shortcuts for the Russian layout.

tk.Button(root, text="To create", command=create_user).grid(row=9, column=0, columnspan=2, pady=10)

root.mainloop()
