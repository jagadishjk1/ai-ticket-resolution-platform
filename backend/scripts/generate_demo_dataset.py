"""
Generate the demo knowledge base: backend/data/demo_tickets.xlsx

Creates a small, realistic, synthetic set of *resolved* IT support tickets.
Every issue type has its own correct resolution and is written in three
different ways (the way real users describe the same problem differently),
so similarity search has something meaningful to match against.

Usage (from the backend folder):
    python scripts/generate_demo_dataset.py
"""
import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

SEED = 42
OUTPUT = Path(__file__).resolve().parent.parent / "data" / "demo_tickets.xlsx"

# (category, priority, [three user descriptions], resolution)
ISSUES = [
    # ---------------- Hardware Request ----------------
    ("Hardware Request", "Medium", [
        "Laptop battery drains within an hour even when fully charged.",
        "My laptop battery is not holding charge anymore.",
        "Battery health shows 40% and laptop shuts down when unplugged.",
    ], "Ran battery diagnostics, confirmed degraded cell health, replaced the laptop battery under warranty and calibrated the new battery."),
    ("Hardware Request", "Low", [
        "Need a second monitor for my workstation.",
        "Requesting an additional external display for dual-screen setup.",
        "Can I get an extra monitor to work with two screens?",
    ], "Verified manager approval, issued a 24-inch monitor from inventory, connected it via HDMI and configured extended display settings."),
    ("Hardware Request", "Medium", [
        "Keyboard keys are sticking and some keys do not type.",
        "Several keys on my keyboard stopped working.",
        "Laptop keyboard is unresponsive for the letters A, S and D.",
    ], "Tested keyboard with on-screen diagnostics, confirmed hardware fault, replaced the keyboard and verified all keys register correctly."),
    ("Hardware Request", "Low", [
        "Mouse cursor jumps randomly across the screen.",
        "Wireless mouse is lagging and disconnecting.",
        "My mouse is not tracking smoothly.",
    ], "Replaced mouse batteries, re-paired the USB receiver on a different port, and issued a new mouse when the issue persisted."),
    ("Hardware Request", "High", [
        "Laptop overheating and fan is very loud.",
        "System becomes very hot and slows down after some time.",
        "Laptop fan running at full speed constantly and the bottom is hot.",
    ], "Cleaned dust from vents and fan, updated BIOS and chipset drivers, set the power plan to balanced and confirmed temperatures returned to normal."),
    ("Hardware Request", "Medium", [
        "Webcam not detected in Teams or Zoom.",
        "Laptop camera shows a black screen during video calls.",
        "Built-in camera is not working for meetings.",
    ], "Enabled camera access in Windows privacy settings, reinstalled the webcam driver from Device Manager and verified the camera in the meeting app."),
    ("Hardware Request", "Medium", [
        "Docking station not charging laptop or showing displays.",
        "Monitors connected to the dock stay blank.",
        "USB-C dock stopped working with my laptop.",
    ], "Updated docking station firmware and Thunderbolt driver, reseated the USB-C cable and confirmed charging and both displays work."),
    ("Hardware Request", "Low", [
        "Headset microphone not picking up my voice.",
        "Others cannot hear me through my headset on calls.",
        "USB headset mic is muted or not working.",
    ], "Set the headset as the default input device, enabled microphone access for apps and adjusted input level; issued a replacement headset after testing."),
    ("Hardware Request", "High", [
        "Laptop screen cracked after a fall.",
        "Display has lines and a broken corner.",
        "My laptop screen is physically damaged.",
    ], "Backed up user data, issued a loaner laptop and sent the device to the vendor for screen replacement under the accidental damage policy."),

    # ---------------- System Crash ----------------
    ("System Crash", "Critical", [
        "Blue screen error MEMORY_MANAGEMENT appears randomly.",
        "Computer crashes with BSOD several times a day.",
        "Getting a blue screen and automatic restart while working.",
    ], "Ran Windows Memory Diagnostic, found a faulty RAM module, replaced it and updated all drivers; no further blue screens observed."),
    ("System Crash", "High", [
        "Laptop freezes completely and only a hard reset helps.",
        "System hangs and mouse stops moving.",
        "Computer becomes unresponsive and I have to hold the power button.",
    ], "Checked Event Viewer, updated graphics and storage drivers, ran sfc /scannow and DISM to repair system files; issue resolved."),
    ("System Crash", "High", [
        "Computer restarts unexpectedly during software installation.",
        "PC shuts down while installing updates.",
        "Unexpected shutdown when I install a new program.",
    ], "Removed conflicting software, ran hardware diagnostics, checked the power supply and completed installation in clean boot mode."),
    ("System Crash", "Critical", [
        "Laptop stuck on the boot screen with the spinning circle.",
        "Windows will not start after an update.",
        "System stuck in an automatic repair loop.",
    ], "Booted into Windows Recovery, uninstalled the latest quality update, ran startup repair and restored normal boot."),
    ("System Crash", "Medium", [
        "Windows Explorer keeps crashing and restarting.",
        "Taskbar and desktop disappear and come back.",
        "File Explorer not responding when opening folders.",
    ], "Cleared File Explorer history, disabled faulty shell extensions, repaired system files with sfc /scannow and restarted Explorer."),
    ("System Crash", "Medium", [
        "Computer very slow and disk usage always at 100%.",
        "Laptop takes 10 minutes to start and apps lag.",
        "System performance extremely slow since last week.",
    ], "Disabled unnecessary startup programs, ran disk cleanup, checked SSD health and paused a stuck Windows Search indexing job."),
    ("System Crash", "High", [
        "Black screen after login, only cursor visible.",
        "Desktop does not load after entering password.",
        "Screen goes black after signing in.",
    ], "Restarted explorer.exe from Task Manager, rolled back the display driver and removed a corrupt user profile cache."),
    ("System Crash", "Medium", [
        "Laptop does not wake up from sleep.",
        "Screen stays off after opening the laptop lid.",
        "System hangs when resuming from sleep mode.",
    ], "Updated BIOS and Intel graphics driver, disabled fast startup and adjusted power management settings for the display adapter."),
    ("System Crash", "Critical", [
        "Hard drive making clicking noise and files are corrupted.",
        "Disk errors reported and computer crashes when opening files.",
        "SMART warning says the disk is failing.",
    ], "Backed up data immediately, replaced the failing drive with a new SSD and restored the user's files from backup."),

    # ---------------- Email Issues ----------------
    ("Email Issues", "Medium", [
        "Outlook emails not syncing on my phone.",
        "Emails not syncing across laptop and mobile.",
        "New mail shows on web but not in the Outlook app.",
    ], "Removed and re-added the mail account on the device, reset sync settings and re-authenticated with MFA; sync restored."),
    ("Email Issues", "High", [
        "Cannot send emails, they stay in the Outbox.",
        "Outgoing mail stuck and never delivered.",
        "Emails remain in Outbox with send error.",
    ], "Cleared the stuck item from Outbox, removed an oversized attachment, verified SMTP settings and resent the messages."),
    ("Email Issues", "Medium", [
        "Important emails going to the junk folder.",
        "Client emails are being marked as spam.",
        "Messages from a partner domain end up in junk.",
    ], "Added the sender domain to the safe senders list and adjusted the spam filter policy in the mail admin center."),
    ("Email Issues", "High", [
        "Mailbox full, cannot receive new emails.",
        "Getting mailbox size limit warning.",
        "Emails bounce back saying my mailbox is full.",
    ], "Enabled online archive, moved old items to archive and cleared Deleted Items; mailbox usage reduced below quota."),
    ("Email Issues", "Medium", [
        "Outlook keeps asking for password repeatedly.",
        "Credential prompt pops up in Outlook every few minutes.",
        "Outlook will not accept my password and keeps prompting.",
    ], "Cleared cached credentials in Windows Credential Manager, enabled modern authentication and re-signed in to Outlook."),
    ("Email Issues", "Low", [
        "Email signature not showing on replies.",
        "Need to set up company email signature.",
        "My Outlook signature disappeared.",
    ], "Created the standard company signature in Outlook settings and set it as default for new messages and replies."),
    ("Email Issues", "Medium", [
        "Shared mailbox not visible in Outlook.",
        "Cannot access the team shared inbox.",
        "Need access to the support shared mailbox.",
    ], "Granted Full Access and Send As permissions on the shared mailbox and waited for automapping to add it to Outlook."),
    ("Email Issues", "Medium", [
        "Outlook crashes when opening.",
        "Outlook not responding at startup.",
        "Outlook closes immediately after launching.",
    ], "Started Outlook in safe mode, disabled a faulty add-in, repaired the Office installation and rebuilt the Outlook profile."),
    ("Email Issues", "Low", [
        "Calendar invites not showing in Outlook.",
        "Meeting requests missing from my calendar.",
        "Calendar is not updating with new meetings.",
    ], "Cleared offline items for the calendar folder, re-synced the mailbox and verified calendar permissions with the delegate."),

    # ---------------- VPN Access ----------------
    ("VPN Access", "High", [
        "Unable to connect to VPN from home network.",
        "VPN connection fails when working remotely.",
        "Cannot connect to the company VPN from home.",
    ], "Reinstalled the VPN client, updated the certificate, verified the user is in the VPN access group and tested the connection."),
    ("VPN Access", "Medium", [
        "VPN keeps disconnecting every few minutes.",
        "VPN drops frequently during calls.",
        "Unstable VPN connection that reconnects repeatedly.",
    ], "Switched VPN protocol to TCP, disabled Wi-Fi power saving, updated the network adapter driver and recommended a wired connection."),
    ("VPN Access", "High", [
        "VPN authentication failed error.",
        "VPN rejects my credentials.",
        "Login to VPN says invalid username or password.",
    ], "Reset the user's VPN credentials, re-registered MFA and confirmed the account was not locked in Active Directory."),
    ("VPN Access", "Medium", [
        "Connected to VPN but cannot access internal sites.",
        "VPN connected but shared drives not reachable.",
        "Internal applications not opening over VPN.",
    ], "Flushed DNS cache, corrected DNS suffix settings on the VPN adapter and verified split tunnel routes for internal subnets."),
    ("VPN Access", "Low", [
        "Need VPN access for a new employee.",
        "Request to enable remote access for new joiner.",
        "Please provide VPN setup for new team member.",
    ], "Added the user to the VPN access group after approval, installed the VPN client and shared the setup guide."),
    ("VPN Access", "Medium", [
        "Internet very slow when VPN is connected.",
        "Browsing becomes slow after connecting to VPN.",
        "VPN makes all applications slow.",
    ], "Enabled split tunnelling for internet traffic, connected to the nearest VPN gateway and verified bandwidth improved."),
    ("VPN Access", "High", [
        "VPN client shows certificate expired error.",
        "VPN certificate error prevents connection.",
        "Security certificate warning when starting VPN.",
    ], "Renewed the device certificate through the management portal, synced the device and reconnected the VPN successfully."),
    ("VPN Access", "Medium", [
        "VPN app not opening after Windows update.",
        "VPN client crashes on launch.",
        "VPN software stopped working after update.",
    ], "Uninstalled and reinstalled the latest VPN client version compatible with the new Windows build and restarted the VPN service."),
    ("VPN Access", "Low", [
        "MFA prompt not received when connecting to VPN.",
        "Not getting the authenticator notification for VPN login.",
        "VPN waits for MFA approval that never arrives.",
    ], "Re-registered the authenticator app, enabled notifications on the phone and verified time sync on the mobile device."),

    # ---------------- Password Reset ----------------
    ("Password Reset", "High", [
        "Forgot my Windows login password.",
        "Cannot remember my password to log in.",
        "Need to reset my domain account password.",
    ], "Verified user identity, reset the password in Active Directory, set change-at-next-logon and guided the user through self-service setup."),
    ("Password Reset", "High", [
        "Account locked out after too many attempts.",
        "My account is locked and I cannot sign in.",
        "Getting account locked message on login.",
    ], "Unlocked the account in Active Directory, identified an old saved password on the phone causing lockouts and removed it."),
    ("Password Reset", "Medium", [
        "Password expired and cannot log in remotely.",
        "Password expired while working from home.",
        "Prompted that password has expired but change fails.",
    ], "Reset the password via the self-service portal, connected to VPN and locked/unlocked the laptop to sync the new password."),
    ("Password Reset", "Medium", [
        "Lost phone, cannot complete MFA to sign in.",
        "Need to reset multi-factor authentication on new phone.",
        "MFA device changed and I cannot log in.",
    ], "Verified identity, cleared old MFA methods, issued a temporary access pass and helped register the authenticator on the new phone."),
    ("Password Reset", "Low", [
        "Need to set up self-service password reset.",
        "How do I register for password reset portal?",
        "Want to enable SSPR for my account.",
    ], "Guided the user to register security info (phone and authenticator) in the self-service password reset portal."),
    ("Password Reset", "Medium", [
        "SAP password reset required.",
        "Locked out of the ERP application.",
        "Cannot log in to SAP, password not accepted.",
    ], "Reset the SAP user password via SU01, unlocked the user and shared a one-time password through a secure channel."),
    ("Password Reset", "Medium", [
        "Teams login fails with an error.",
        "Cannot sign in to Microsoft Teams.",
        "Teams keeps showing sign-in error.",
    ], "Cleared the Teams cache folder, removed stale credentials from Credential Manager and signed in again with the corporate account."),
    ("Password Reset", "Low", [
        "BitLocker recovery key requested on startup.",
        "Laptop asks for BitLocker key after BIOS update.",
        "Locked out by BitLocker recovery screen.",
    ], "Verified identity, retrieved the BitLocker recovery key from Active Directory/Intune and suspended BitLocker before the next BIOS update."),
    ("Password Reset", "Medium", [
        "Wi-Fi asks for password after password change.",
        "Cannot connect to office Wi-Fi after resetting password.",
        "Corporate wireless login fails since password update.",
    ], "Removed the saved corporate Wi-Fi profile, reconnected using the new credentials and confirmed certificate-based authentication."),

    # ---------------- Application Bug ----------------
    ("Application Bug", "High", [
        "Excel crashes when opening large files.",
        "Excel stops responding with big spreadsheets.",
        "Excel freezes on opening a workbook.",
    ], "Disabled COM add-ins, turned off hardware graphics acceleration, repaired Office and installed the 64-bit version of Excel."),
    ("Application Bug", "Medium", [
        "Teams not showing new messages.",
        "Teams chat not updating in real time.",
        "Messages in Teams appear late.",
    ], "Cleared the Teams cache, updated Teams to the latest version and verified network access to Microsoft 365 endpoints."),
    ("Application Bug", "Medium", [
        "Browser shows certificate error on internal portal.",
        "Your connection is not private error on company site.",
        "Chrome blocks access to intranet with SSL warning.",
    ], "Installed the internal root CA certificate via group policy, cleared the SSL state and verified the portal certificate chain."),
    ("Application Bug", "High", [
        "Application error 0x80070005 access denied while installing.",
        "Installer fails with access denied error.",
        "Cannot install software, permission error.",
    ], "Installed the application through the company software center with elevated rights and added it to the approved software list."),
    ("Application Bug", "Medium", [
        "Adobe Reader cannot open PDF files.",
        "PDF files open blank in Adobe.",
        "Error when opening PDF documents.",
    ], "Repaired the Adobe Reader installation, disabled protected mode for the affected files and set Reader as the default PDF app."),
    ("Application Bug", "Low", [
        "Word document formatting changes when opened.",
        "Fonts look different in Word documents.",
        "Word layout messed up on my system.",
    ], "Installed the missing company fonts, reset the Normal.dotm template and disabled compatibility mode."),
    ("Application Bug", "High", [
        "OneDrive not syncing files.",
        "OneDrive shows sync pending forever.",
        "Files not uploading to OneDrive.",
    ], "Reset the OneDrive client, renamed files with invalid characters, freed disk space and confirmed sync completed."),
    ("Application Bug", "Medium", [
        "CRM application very slow to load pages.",
        "Salesforce pages take too long to open.",
        "Customer portal app is lagging.",
    ], "Cleared browser cache and cookies, disabled heavy extensions and moved the user to the supported browser version."),
    ("Application Bug", "Medium", [
        "Zoom audio not working in meetings.",
        "Cannot hear others on Zoom calls.",
        "No sound in video conference app.",
    ], "Selected the correct speaker device in Zoom audio settings, updated the audio driver and disabled exclusive mode."),

    # ---------------- Network Connectivity ----------------
    ("Network Connectivity", "High", [
        "Wi-Fi connected but no internet access.",
        "Shows connected to Wi-Fi but websites do not load.",
        "No internet even though Wi-Fi is on.",
    ], "Released and renewed the IP address, flushed DNS, reset the TCP/IP stack with netsh and reconnected to the network."),
    ("Network Connectivity", "Medium", [
        "Wi-Fi keeps dropping in the office.",
        "Wireless connection disconnects frequently.",
        "Laptop loses Wi-Fi connection every few minutes.",
    ], "Updated the wireless adapter driver, disabled power saving on the adapter and moved the user to the 5 GHz SSID."),
    ("Network Connectivity", "High", [
        "Ethernet cable plugged in but network not detected.",
        "LAN port not working at my desk.",
        "Wired network shows cable unplugged.",
    ], "Tested with a known good cable, patched the wall port on the switch and enabled the port in the correct VLAN."),
    ("Network Connectivity", "High", [
        "Cannot access shared network drive.",
        "Mapped drive shows disconnected.",
        "Network folder not accessible.",
    ], "Re-mapped the network drive with the correct path, verified folder permissions and cleared cached credentials."),
    ("Network Connectivity", "Medium", [
        "Internet very slow at my desk.",
        "Network speed is very low today.",
        "Downloads extremely slow on office network.",
    ], "Ran a speed test, found a duplex mismatch on the switch port, corrected it and confirmed normal speeds."),
    ("Network Connectivity", "Low", [
        "Guest Wi-Fi access needed for visitor.",
        "Need Wi-Fi password for a client meeting.",
        "Request guest network access for vendor.",
    ], "Generated a time-limited guest Wi-Fi voucher in the wireless controller and shared it with the host."),
    ("Network Connectivity", "Medium", [
        "Website blocked by firewall needed for work.",
        "Access denied to a business website.",
        "Proxy blocking a site I need for my project.",
    ], "Reviewed the business justification, added the URL to the web filter allow list and confirmed access."),
    ("Network Connectivity", "High", [
        "IP address conflict detected on my computer.",
        "Windows says another device has the same IP.",
        "Duplicate IP address error on network.",
    ], "Removed the static IP configuration, switched the adapter to DHCP and reserved the address in the DHCP server."),
    ("Network Connectivity", "Medium", [
        "DNS server not responding error.",
        "Websites fail with DNS lookup error.",
        "Cannot resolve website names.",
    ], "Set the adapter to obtain DNS automatically, flushed the DNS cache and verified the internal DNS servers were reachable."),

    # ---------------- Printer Issues ----------------
    ("Printer Issues", "Medium", [
        "Printer shows offline on my computer.",
        "Cannot print, printer status is offline.",
        "Network printer appears offline.",
    ], "Restarted the print spooler, removed and re-added the printer using its IP address and printed a test page."),
    ("Printer Issues", "Medium", [
        "Print jobs stuck in the queue.",
        "Documents not printing and queue is full.",
        "Print queue will not clear.",
    ], "Stopped the print spooler, cleared the spool folder, restarted the service and resent the print job."),
    ("Printer Issues", "Low", [
        "Printer paper jam error even with no paper stuck.",
        "Printer keeps reporting a paper jam.",
        "Paper jam message will not go away.",
    ], "Opened all trays and the rear door, removed a small torn piece of paper, cleaned the rollers and reset the printer."),
    ("Printer Issues", "Low", [
        "Prints are faded and streaky.",
        "Printer output has lines and is very light.",
        "Poor print quality on office printer.",
    ], "Replaced the low toner cartridge, ran the printer cleaning cycle and printed a quality test page."),
    ("Printer Issues", "Medium", [
        "Need to add the office printer to my laptop.",
        "How to install the floor printer?",
        "Printer not listed on my new laptop.",
    ], "Installed the printer from the print server with the correct driver and set it as the default printer."),
    ("Printer Issues", "Medium", [
        "Scanner not sending scans to email.",
        "Scan to email fails on the multifunction printer.",
        "Scanned documents are not received in my inbox.",
    ], "Updated the printer SMTP relay settings, verified the sender address and tested scan-to-email successfully."),
    ("Printer Issues", "Low", [
        "Printer driver unavailable error.",
        "Windows shows driver is unavailable for printer.",
        "Cannot print due to driver problem.",
    ], "Removed the old driver package, installed the latest universal print driver and re-added the printer."),
    ("Printer Issues", "Low", [
        "Printing double-sided does not work.",
        "Duplex option is missing in print settings.",
        "Cannot print on both sides of the page.",
    ], "Enabled the duplex unit in printer device settings and set two-sided printing as the default preference."),
    ("Printer Issues", "Medium", [
        "Secure print release card not working.",
        "Badge does not release my print jobs.",
        "Follow-me printing not picking up my documents.",
    ], "Re-registered the user's badge in the print management system and confirmed jobs were submitted to the secure queue."),
]


def build_rows():
    rng = random.Random(SEED)
    start = datetime(2025, 1, 6)
    rows = []
    counter = 1
    for category, priority, descriptions, resolution in ISSUES:
        for description in descriptions:
            created = start + timedelta(days=rng.randint(0, 300), hours=rng.randint(8, 18))
            resolved = created + timedelta(hours=rng.randint(1, 72))
            rows.append({
                "Ticket ID": f"TKT{counter:04d}",
                "Category": category,
                "Description": description,
                "Resolution": resolution,
                "Priority": priority,
                "Status": rng.choice(["Resolved", "Closed"]),
                "Created Date": created.strftime("%Y-%m-%d %H:%M"),
                "Resolved Date": resolved.strftime("%Y-%m-%d %H:%M"),
            })
            counter += 1
    rng.shuffle(rows)
    return rows


def main():
    df = pd.DataFrame(build_rows())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_excel(OUTPUT, index=False)
    print(f"Wrote {len(df)} tickets to {OUTPUT}")
    print(df["Category"].value_counts().to_string())


if __name__ == "__main__":
    main()
