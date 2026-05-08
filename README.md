# 🌐 IP Changer - Smart Network Tool

A professional command-line tool for changing local and public IP addresses, proxy management, and program tunneling.

## ✨ Features

- 🔄 Change local IP (Static/DHCP)
- 🌍 Change public IP using proxies
- 🤖 Smart automatic proxy fetching from GitHub repositories
- 🚀 Tunnel any program through active proxy
- 📡 Show detailed network information
- 🎨 Beautiful colored terminal interface
- ⚡ Fast and lightweight

## 📋 Requirements

- Python 3.6+
- pip
- Administrator/Root privileges (for local IP change)

## 🔧 Installation

1. **Clone or download** the script to your system

2. **Install required packages:**

```bash
pip install requests
Run the script:
```

```bash
python IP_Changer.py
Or on Linux/Mac:
```

```bash
python3 IP_Changer.py
```

🚀 Usage
Start the program:
```bash
python IP_Changer.py
```

Main Menu Options:
Option	Description
1	Change LOCAL IP - Manual Configuration
2	Change LOCAL IP - Automatic (DHCP)
3	Change PUBLIC IP - Manual (Via Proxy Entry)
4	Change PUBLIC IP - Smart Automatic (GitHub Proxies)
5	Tunnel Program Through Active Proxy
6	Show Current Network Info
7	Test Your Current Public IP
0	Exit
------
### 📖 How It Works
Local IP Change
Manual: Set static IP, subnet mask, and gateway

DHCP: Automatically obtain IP from router

Public IP Change (Smart Mode)
Fetches proxies from 5 different GitHub sources

Tests each proxy for connectivity

Finds working proxies with lowest latency

Changes your public IP automatically

Program Tunneling
Routes any application through your active proxy

Works with browsers, curl, ping, and other tools

Sets HTTP_PROXY and HTTPS_PROXY environment variables

### 🖥️ Platform Support
OS	Supported	Admin Required (Local IP)
Windows	✅ Yes	Run as Administrator
Linux	✅ Yes	sudo
macOS	✅ Yes	sudo
⚠️ Important Notes
Admin/Root privileges are required for local IP changes

Public IP change works by routing traffic through proxies (not changing ISP IP)

Some proxies may be slow or unreliable

Proxy sources are fetched from public GitHub repositories

### 📝 Example Commands
Run on Windows as Admin:
powershell
# Right-click PowerShell -> Run as Administrator
python IP_Changer.py
Run on Linux/Mac:
```bash
sudo python3 IP_Changer.py
```

Tunnel Firefox through proxy:
text
Select option 5
Enter program: firefox
📦 Dependencies
```text
requests>=2.25.0
```

### 🔒 Legal Disclaimer
This tool is for educational purposes only. Use responsibly and comply with all applicable laws and terms of service.

## 👨‍💻 Author
**Developed by KHOSROW**

### 📄 License
- MIT License

Happy Networking! 🚀
