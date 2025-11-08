# Network Setup Guide for Sensee

## Issue: `sensee.local` only works on the host device

The `.local` domain (mDNS/Bonjour) requires specific software to work properly on different operating systems.

## Solutions

### Option 1: Install Bonjour on Windows (Recommended for .local support)

For `.local` domains to work on Windows, you need to install Apple's Bonjour service:

1. **Download Bonjour Print Services for Windows**:

   - Visit: https://support.apple.com/kb/DL999
   - Or search for "Bonjour Print Services for Windows"
   - Download and install the package

2. **Alternative - Install iTunes or Safari**:

   - iTunes or Safari for Windows both include Bonjour
   - Download from Apple's website

3. **Verify Installation**:
   ```powershell
   Get-Service -Name "*Bonjour*"
   ```
   You should see "Bonjour Service" listed and running.

### Option 2: Use Direct IP Address (Works Immediately)

Instead of using `sensee.local`, use the server's IP address directly:

1. **Find your server's IP address** (shown when the server starts):

   ```
   🌐 Server running at http://192.168.x.x:8000
   ```

2. **Connect from other devices** using:
   ```
   http://192.168.x.x:8000
   ```

### Option 3: Configure Your Flutter App to Support Both

Modify your Flutter app to:

1. Try connecting to `sensee.local` first
2. If that fails, use UDP discovery to find the server's IP
3. Fall back to manual IP entry

## Install Required Python Package

Make sure `zeroconf` is installed:

```bash
pip install zeroconf==0.136.2
```

Or install all requirements:

```bash
pip install -r requirements.txt
```

## Firewall Configuration

Ensure these ports are open in Windows Firewall:

- **TCP 8000**: HTTP API server
- **UDP 54321**: Discovery protocol
- **UDP 5353**: mDNS/Bonjour (for .local domain resolution)

To check firewall rules:

```powershell
Get-NetFirewallRule -DisplayName "*Python*" | Select-Object DisplayName, Enabled, Direction, Action
```

## Testing mDNS

### From Command Line (Windows with Bonjour):

```bash
ping sensee.local
```

### From Another Device:

```bash
# iOS/Mac
dns-sd -B _sensee._tcp local.

# Android (with Network Analyzer app)
# Scan for _sensee._tcp services

# Linux
avahi-browse -rt _sensee._tcp
```

## Common Issues

### 1. "sensee.local" doesn't resolve

- **Cause**: Bonjour not installed on Windows client
- **Solution**: Install Bonjour or use IP address

### 2. Server only accessible from localhost

- **Cause**: Server not binding to 0.0.0.0
- **Solution**: Verify server starts with `host="0.0.0.0"` (already configured)

### 3. Connection refused from other devices

- **Cause**: Windows Firewall blocking Python
- **Solution**: Allow Python through firewall:
  ```powershell
  New-NetFirewallRule -DisplayName "Python Server" -Direction Inbound -Program "C:\Path\To\python.exe" -Action Allow
  ```

### 4. mDNS service fails to register

- **Cause**: Port conflict or missing zeroconf package
- **Solution**:
  - Install zeroconf: `pip install zeroconf`
  - Check if port 5353 is available
  - Server still accessible via IP even if mDNS fails

## Network Architecture

```
┌─────────────────────┐
│   Your Laptop       │
│  (Windows/Mac)      │
│                     │
│  Python Server      │
│  → 0.0.0.0:8000     │
│  → UDP:54321        │
│  → mDNS:5353        │
└──────────┬──────────┘
           │
           │ Local Network (WiFi/Ethernet)
           │
           ├─────────────────────┐
           │                     │
    ┌──────┴──────┐      ┌──────┴──────┐
    │   Phone 1   │      │   Phone 2   │
    │  (Flutter)  │      │  (Flutter)  │
    │             │      │             │
    │ Discovers   │      │ Discovers   │
    │ via mDNS    │      │ via UDP     │
    └─────────────┘      └─────────────┘
```

## Quick Start (After Installing Dependencies)

1. **Start the server**:

   ```bash
   cd c:\Users\rafai\Desktop\Programs\sensee\raspi
   python -m server.main
   ```

2. **Note the IP address** shown in the console:

   ```
   🌐 Server running at http://192.168.1.100:8000
   ```

3. **Connect from other devices**:
   - With Bonjour: `http://sensee.local:8000`
   - Without Bonjour: `http://192.168.1.100:8000`

## Verifying Everything Works

1. Server should print:

   ```
   ✅ mDNS service registered as sensee.local at 192.168.x.x:8000
      Other devices can connect using: http://192.168.x.x:8000
   ```

2. From another device on the same network, open a browser:

   - Try: `http://sensee.local:8000`
   - If that fails, try the IP address shown above

3. You should see the video stream or be able to access the API.
