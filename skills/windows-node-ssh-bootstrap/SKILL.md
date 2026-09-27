---
name: windows-node-ssh-bootstrap
description: Complete automation guide and scripts for configuring OpenSSH server, passwordless public key auth, Windows firewall, and headless remote GPU node access on Windows machines.
---

# Windows Node SSH Bootstrap & Remote Access Skill

This skill provides ready-to-run automation scripts and configurations for transforming any local or remote Windows PC (such as a dedicated GPU worker node) into an accessible, headless SSH workstation with passwordless public key authentication.

---

## 1. Automated SSH Setup Script (`setup_ssh_node.bat`)

Run this batch script as **Administrator** on the target Windows node:

```bat
@echo off
title Setup OpenSSH Server on Windows Node
echo ======================================================================
echo  Installing & Configuring OpenSSH Server for Headless Node Access
echo ======================================================================

:: 1. Install OpenSSH Server via Windows Capability
powershell -Command "Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0"

:: 2. Start OpenSSH Service & Enable Automatic Startup
powershell -Command "Start-Service sshd; Set-Service -Name sshd -StartupType 'Automatic'"

:: 3. Open Firewall Port 22
netsh advfirewall firewall add rule name="OpenSSH-Server-In-TCP-22" dir=in action=allow protocol=TCP localport=22

:: 4. Create .ssh directory for the user
if not exist "%USERPROFILE%\.ssh" mkdir "%USERPROFILE%\.ssh"
icacls "%USERPROFILE%\.ssh" /inheritance:r /grant:r "%USERNAME%:(OI)(CI)F" /grant:r "SYSTEM:(OI)(CI)F"

echo.
echo [✓] OpenSSH Server installed and running on port 22!
echo [✓] Node IP Address:
ipconfig | findstr /i "IPv4"
pause
```

---

## 2. Setting Up Passwordless Public Key Authentication

To allow the main workstation / IDE to connect instantly without password prompts:

### Step 1: Generate SSH Key on Client (if not already existing)
```powershell
ssh-keygen -t ed25519 -f "$env:USERPROFILE\.ssh\id_ed25519" -N ""
```

### Step 2: Push Public Key to Target Node
Run from client:
```powershell
$target_node = "ITX@192.168.1.152"
$pub_key = Get-Content "$env:USERPROFILE\.ssh\id_ed25519.pub"
ssh $target_node "powershell -Command `"New-Item -ItemType Directory -Force -Path `$env:USERPROFILE\.ssh; Add-Content -Path `$env:USERPROFILE\.ssh\authorized_keys -Value '$pub_key'`""
```

### Step 3: Configure Administrative Permissions (`administrators_authorized_keys`)
On Windows OpenSSH, administrative users check `C:\ProgramData\ssh\administrators_authorized_keys`:
```powershell
ssh $target_node "powershell -Command `"Copy-Item `$env:USERPROFILE\.ssh\authorized_keys C:\ProgramData\ssh\administrators_authorized_keys; icacls.exe C:\ProgramData\ssh\administrators_authorized_keys /inheritance:r /grant 'Administrators:F' /grant 'SYSTEM:F'`""
```

---

## 3. SSH Config Shortcut Setup (`~/.ssh/config`)

Add to client `%USERPROFILE%\.ssh\config`:
```ssh
Host itx
    HostName 192.168.1.152
    User ITX
    IdentityFile ~/.ssh/id_ed25519
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
```

Now connect, transfer files, or execute GPU scripts via:
```powershell
ssh itx "dir D:\AI_Workspace"
scp local_script.py itx:D:/AI_Workspace/
```

---

## 4. Headless GPU Node Auto-Start / Keep-Alive

To ensure the node stays awake and accessible without monitor attachment:
1. **Disable Sleep:**
   ```bat
   powercfg /change standby-timeout-ac 0
   powercfg /change hibernate-timeout-ac 0
   ```
2. **Auto-Start AI Daemons:**
   Add startup task in Task Scheduler to launch ComfyUI / Ollama / Python workers automatically upon system reboot.
