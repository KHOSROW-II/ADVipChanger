import os
import sys
import subprocess
import re
import random
import time
import requests
import platform
from threading import Event

class Colors:
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

def progress(msg): print(f"{Colors.CYAN}┌──[{Colors.BOLD}*{Colors.RESET}{Colors.CYAN}] {msg}{Colors.RESET}")
def status(msg, err=False): 
    if err:
        print(f"{Colors.RED}└──[{Colors.BOLD}*{Colors.RESET}{Colors.RED}] {msg}{Colors.RESET}")
    else:
        print(f"{Colors.GREEN}└──[{Colors.BOLD}*{Colors.RESET}{Colors.GREEN}] {msg}{Colors.RESET}")
def info(msg): print(f"{Colors.BLUE}├──[{Colors.BOLD}*{Colors.RESET}{Colors.BLUE}] {msg}{Colors.RESET}")
def warning(msg): print(f"{Colors.YELLOW}├──[{Colors.BOLD}*{Colors.RESET}{Colors.YELLOW}] {msg}{Colors.RESET}")
def clear(): os.system('cls' if os.name == 'nt' else 'clear')

PROXY_SOURCES = [
    {
        "name": "Proxy-List-Free",
        "url": "https://raw.githubusercontent.com/komutan234/Proxy-List-Free/main/proxies/http.txt",
        "type": "http"
    },
    {
        "name": "ProxyGather",
        "url": "https://raw.githubusercontent.com/Skillter/ProxyGather/master/proxies/working-proxies-http.txt",
        "type": "http"
    },
    {
        "name": "Free-Proxy-List",
        "url": "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "type": "http"
    },
    {
        "name": "Awesome-Free-Proxy",
        "url": "https://raw.githubusercontent.com/Thordata/awesome-free-proxy-list/main/proxies/http.txt",
        "type": "http"
    },
    {
        "name": "Proxy-List",
        "url": "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTP_RAW.txt",
        "type": "http"
    }
]

class NetworkManager:
    def __init__(self):
        self.system = platform.system()
        self.is_admin = self.check_admin()
        
    def check_admin(self):
        try:
            if self.system == "Windows":
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except:
            return False
    
    def get_adapters(self):
        adapters = []
        
        if self.system == "Windows":
            try:
                result = subprocess.run('ipconfig', shell=True, capture_output=True, text=True)
                lines = result.stdout.split('\n')
                
                current_adapter = None
                for i, line in enumerate(lines):
                    line = line.strip()
                    
                    if 'adapter' in line.lower() and line.endswith(':'):
                        current_adapter = line.replace(':', '').strip()
                    
                    # Look for IPv4 address
                    elif 'IPv4' in line or 'IPv4 Address' in line:
                        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                        if ip_match and current_adapter:
                            ip = ip_match.group(1)
                            if not ip.startswith('127.'):
                                adapters.append({
                                    "name": current_adapter,
                                    "ip": ip,
                                    "netmask": "255.255.255.0"
                                })
                                current_adapter = None
                    
                    elif 'IP Address' in line:
                        ip_match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                        if ip_match and current_adapter:
                            ip = ip_match.group(1)
                            if not ip.startswith('127.'):
                                adapters.append({
                                    "name": current_adapter,
                                    "ip": ip,
                                    "netmask": "255.255.255.0"
                                })
                                current_adapter = None
            except Exception as e:
                warning(f"Error getting adapters: {e}")
        
        else:  # Linux / Mac
            try:
                result = subprocess.run('ip -4 addr show', shell=True, capture_output=True, text=True)
                if result.returncode == 0 and result.stdout:
                    lines = result.stdout.split('\n')
                    current_iface = None
                    
                    for line in lines:
                        line = line.strip()
                        
                        if line.startswith(('eth', 'wlan', 'enp', 'ens', 'wlp', 'en0', 'en1')):
                            parts = line.split(':')
                            if len(parts) >= 2:
                                current_iface = parts[1].strip()
                        
                        elif 'inet ' in line and current_iface:
                            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/(\d+)', line)
                            if ip_match:
                                ip = ip_match.group(1)
                                if not ip.startswith('127.'):
                                    adapters.append({
                                        "name": current_iface,
                                        "ip": ip,
                                        "netmask": "255.255.255.0"
                                    })
                                    current_iface = None
                
                if not adapters:
                    result = subprocess.run('ifconfig', shell=True, capture_output=True, text=True)
                    lines = result.stdout.split('\n')
                    current_iface = None
                    
                    for line in lines:
                        line = line.strip()
                        
                        if line and not line.startswith((' ', '\t')) and 'flags' in line:
                            current_iface = line.split(':')[0]
                        
                        elif 'inet ' in line and current_iface and not '127.0.0.1' in line:
                            ip_match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
                            if ip_match:
                                ip = ip_match.group(1)
                                adapters.append({
                                    "name": current_iface,
                                    "ip": ip,
                                    "netmask": "255.255.255.0"
                                })
                                current_iface = None
            except Exception as e:
                warning(f"Error getting adapters: {e}")
        
        return adapters
    
    def set_static_ip(self, adapter_name, ip, mask="255.255.255.0", gateway=None):
        try:
            if not self.is_admin:
                warning("Administrator/root privileges required!")
                return False
            
            if self.system == "Windows":
                cmd = f'netsh interface ip set address "{adapter_name}" static {ip} {mask}'
                if gateway:
                    cmd += f' {gateway}'
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    return True
                else:
                    warning(f"Error: {result.stderr}")
                    return False
            else:
                cidr = self.mask_to_cidr(mask)
                subprocess.run(f'sudo ip addr flush dev {adapter_name}', shell=True, capture_output=True)
                cmd = f'sudo ip addr add {ip}/{cidr} dev {adapter_name}'
                result = subprocess.run(cmd, shell=True, capture_output=True)
                if result.returncode != 0:
                    warning(f"Failed to add IP: {result.stderr}")
                    return False
                if gateway:
                    subprocess.run(f'sudo ip route add default via {gateway}', shell=True, capture_output=True)
                return True
        except Exception as e:
            warning(f"Failed to set static IP: {e}")
            return False
    
    def set_dhcp(self, adapter_name):
        try:
            if not self.is_admin:
                warning("Administrator/root privileges required!")
                return False
            
            if self.system == "Windows":
                cmd = f'netsh interface ip set address "{adapter_name}" dhcp'
                subprocess.run(cmd, shell=True, check=True, capture_output=True)
                return True
            else:
                subprocess.run(f'sudo dhclient -r {adapter_name}', shell=True, capture_output=True)
                subprocess.run(f'sudo dhclient {adapter_name}', shell=True, capture_output=True)
                return True
        except Exception as e:
            warning(f"Failed to set DHCP: {e}")
            return False
    
    def mask_to_cidr(self, mask):
        """Convert netmask to CIDR notation"""
        try:
            return str(sum(bin(int(x)).count('1') for x in mask.split('.')))
        except:
            return "24"
    
    def restart_network(self):
        try:
            if not self.is_admin:
                warning("Administrator/root privileges required!")
                return False
            
            if self.system == "Windows":
                subprocess.run('ipconfig /release', shell=True, capture_output=True)
                time.sleep(2)
                subprocess.run('ipconfig /renew', shell=True, capture_output=True)
                return True
            else:
                subprocess.run('sudo systemctl restart NetworkManager', shell=True, capture_output=True)
                return True
        except Exception as e:
            warning(f"Failed to restart network: {e}")
            return False

class ProxyManager:
    def __init__(self):
        self.proxies = []
        self.working_proxies = []
        self.current_proxy = None
        self.stop_testing = Event()
    
    def fetch_from_github(self):
        progress("Fetching proxies from GitHub repositories...")
        all_proxies = []
        
        for source in PROXY_SOURCES:
            try:
                info(f"Fetching from {source['name']}...")
                response = requests.get(source['url'], timeout=15, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    lines = response.text.strip().split('\n')
                    count = 0
                    for line in lines[:100]:
                        line = line.strip()
                        if line and ':' in line and not line.startswith('#'):
                            proxy = f"http://{line}"
                            all_proxies.append(proxy)
                            count += 1
                    status(f"Got {count} from {source['name']}")
                else:
                    warning(f"Failed to fetch from {source['name']}: HTTP {response.status_code}")
                    
            except requests.RequestException as e:
                warning(f"Connection error for {source['name']}: {e}")
            except Exception as e:
                warning(f"Error processing {source['name']}: {e}")
        
        self.proxies = list(set(all_proxies))
        status(f"Total unique proxies collected: {len(self.proxies)}")
        return self.proxies
    
    def test_proxy(self, proxy_url, timeout=10):
        try:
            proxy_dict = {"http": proxy_url, "https": proxy_url}
            start_time = time.time()
            
            response = requests.get(
                'https://api.ipify.org',
                proxies=proxy_dict,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            
            latency = time.time() - start_time
            
            if response.status_code == 200:
                ip = response.text.strip()
                return {
                    'proxy': proxy_url,
                    'ip': ip,
                    'latency': latency,
                    'working': True
                }
        except:
            pass
        
        return {'proxy': proxy_url, 'working': False}
    
    def find_working_proxies(self, max_proxies=10):
        if not self.proxies:
            self.fetch_from_github()
        
        if not self.proxies:
            warning("No proxies fetched! Using fallback proxies...")
            self.proxies = [
                "http://51.89.14.70:80",
                "http://198.23.239.134:65309",
                "http://45.87.80.59:80"
            ]
        
        test_count = min(len(self.proxies), 50)
        progress(f"Testing {test_count} proxies for working ones...")
        self.working_proxies = []
        
        test_list = self.proxies[:50]
        
        for i, proxy in enumerate(test_list):
            if self.stop_testing.is_set():
                break
                
            result = self.test_proxy(proxy)
            if result['working']:
                self.working_proxies.append(result)
                status(f"Working proxy found: {result['ip']} (latency: {result['latency']:.2f}s)")
            
            if (i + 1) % 10 == 0:
                progress(f"Tested {i+1}/{len(test_list)} proxies...")
        
        self.working_proxies.sort(key=lambda x: x['latency'])
        status(f"Found {len(self.working_proxies)} working proxies")
        return self.working_proxies[:max_proxies]
    
    def get_new_ip(self):
        progress("Searching for a working proxy to change IP...")
        
        working = self.find_working_proxies(max_proxies=5)
        
        if not working:
            warning("No working proxies found!")
            return None
        
        old_ip = self.get_current_public_ip()
        info(f"Current public IP: {old_ip}")
        
        for proxy_info in working:
            proxy_url = proxy_info['proxy']
            new_ip = proxy_info['ip']
            
            if new_ip != old_ip:
                self.current_proxy = {"http": proxy_url, "https": proxy_url}
                status(f"IP changed successfully!")
                info(f"New IP: {new_ip}")
                info(f"Latency: {proxy_info['latency']:.2f} seconds")
                info(f"Proxy: {proxy_url}")
                return new_ip
            else:
                status(f"Proxy gave same IP, trying next...")
        
        if working and working[0]['ip'] == old_ip:
            status("All working proxies give the same IP. Trying network restart...")
            network = NetworkManager()
            if network.restart_network():
                time.sleep(5)
                return self.get_current_public_ip()
        
        return None
    
    def get_current_public_ip(self):
        try:
            response = requests.get('https://api.ipify.org', timeout=10)
            return response.text
        except:
            try:
                response = requests.get('https://icanhazip.com', timeout=10)
                return response.text.strip()
            except:
                try:
                    response = requests.get('https://checkip.amazonaws.com', timeout=10)
                    return response.text.strip()
                except:
                    return None
    
    def get_ip_location(self, ip):
        try:
            response = requests.get(f'http://ip-api.com/json/{ip}', timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data['status'] == 'success':
                    return f"{data['city']}, {data['country']}"
        except:
            pass
        return "Unknown"

class TunnelManager:
    def __init__(self, proxy_manager):
        self.proxy_manager = proxy_manager
    
    def tunnel_program(self, program_path):
        if not self.proxy_manager.current_proxy:
            warning("No active proxy! Please change IP first (option 4)")
            return False
        
        if not os.path.exists(program_path):
            import shutil
            if shutil.which(program_path) is None:
                warning(f"Program not found: {program_path}")
                return False
        
        env = os.environ.copy()
        proxy_url = self.proxy_manager.current_proxy.get('http', '')
        env['HTTP_PROXY'] = proxy_url
        env['HTTPS_PROXY'] = proxy_url
        env['ALL_PROXY'] = proxy_url
        
        try:
            if platform.system() == "Windows":
                process = subprocess.Popen([program_path], env=env, shell=True)
            else:
                process = subprocess.Popen([program_path], env=env)
            
            status(f"Program launched through proxy!")
            info(f"PID: {process.pid}")
            info(f"Using proxy: {proxy_url}")
            return True
        except Exception as e:
            warning(f"Failed to launch program: {e}")
            return False

def display_banner():
    banner = f"""
{Colors.MAGENTA}{Colors.BOLD}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}                                                                                  {Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}     {Colors.CYAN}██╗██████╗    {Colors.RESET} {Colors.GREEN} █████████  ██╗  ██╗ █████╗ ███╗   ██╗ ██████╗ ███████╗{Colors.RESET}       {Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}     {Colors.CYAN}██║██╔══██╗   {Colors.RESET} {Colors.GREEN}███╔═══╗███ ██║  ██║██╔══██╗████╗  ██║██╔════╝ ██╔════╝{Colors.RESET}       {Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}     {Colors.CYAN}██║██████╔╝   {Colors.RESET} {Colors.GREEN}██╔╝   ╚═╝  ███████║███████║██╔██╗ ██║██║  ███╗█████╗{Colors.RESET}         {Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}     {Colors.CYAN}██║██╔═══╝    {Colors.RESET} {Colors.GREEN}███     ███ ██╔══██║██╔══██║██║╚██╗██║██║   ██║██╔══╝{Colors.RESET}         {Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}     {Colors.CYAN}██║██║        {Colors.RESET} {Colors.GREEN} █████████╝ ██║  ██║██║  ██║██║ ╚████║╚██████╔╝███████╗{Colors.RESET}       {Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}     {Colors.CYAN}╚═╝╚═╝        {Colors.RESET} {Colors.GREEN}  ╚══════╝  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝ (R){Colors.RESET}   {Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}                                                                                  {Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}          {Colors.YELLOW}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{Colors.RESET}            {Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}          {Colors.YELLOW}┃{Colors.RESET}               {Colors.WHITE}{Colors.BOLD}     IP CHANGER V2.3    {Colors.RESET}                   {Colors.YELLOW}┃{Colors.RESET}            {Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}          {Colors.YELLOW}┃{Colors.RESET}                 {Colors.DIM}Developed BY: KHOSROW                  {Colors.RESET}  {Colors.YELLOW}┃{Colors.RESET}            {Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}          {Colors.YELLOW}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{Colors.RESET}            {Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}                                                                                  {Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}
{Colors.MAGENTA}{Colors.BOLD}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{Colors.RESET}
"""
    print(banner)

def display_menu():
    menu = f"""
{Colors.YELLOW}{Colors.BOLD}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}                                                                              {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}                 {Colors.WHITE}{Colors.BOLD}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{Colors.RESET}                 {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}                 {Colors.WHITE}{Colors.BOLD}┃{Colors.RESET}                  {Colors.CYAN}MAIN MENU{Colors.RESET}               {Colors.WHITE}{Colors.BOLD}┃{Colors.RESET}                 {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}                 {Colors.WHITE}{Colors.BOLD}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{Colors.RESET}                 {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}                                                                              {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}     {Colors.GREEN}┌─┐{Colors.RESET}  {Colors.CYAN}1.{Colors.RESET} Change LOCAL IP - Manual Configuration                           {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}     {Colors.GREEN}├─┤{Colors.RESET}  {Colors.CYAN}2.{Colors.RESET} Change LOCAL IP - Automatic (DHCP)                               {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}     {Colors.GREEN}├─┤{Colors.RESET}  {Colors.CYAN}3.{Colors.RESET} Change PUBLIC IP - Manual (Via Proxy Entry)                      {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}     {Colors.GREEN}├─┤{Colors.RESET}  {Colors.CYAN}4.{Colors.RESET} Change PUBLIC IP - Smart Automatic (GitHub Proxies)              {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}     {Colors.GREEN}├─┤{Colors.RESET}  {Colors.CYAN}5.{Colors.RESET} Tunnel Program Through Active Proxy                              {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}     {Colors.GREEN}├─┤{Colors.RESET}  {Colors.CYAN}6.{Colors.RESET} Show Current Network Info                                        {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}     {Colors.GREEN}├─┤{Colors.RESET}  {Colors.CYAN}7.{Colors.RESET} Test Your Current Public IP                                      {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}     {Colors.GREEN}└─┘{Colors.RESET}  {Colors.RED}0.{Colors.RESET} Exit                                                             {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}                                                                              {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}
{Colors.YELLOW}{Colors.BOLD}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{Colors.RESET}
"""
    print(menu)

def show_network_info(network, proxy_manager):
    clear()
    display_banner()
    progress("Current Network Information")
    
    adapters = network.get_adapters()
    print(f"\n{Colors.YELLOW}{Colors.BOLD}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{Colors.RESET}")
    print(f"{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}  {Colors.WHITE}{Colors.BOLD}  NETWORK ADAPTERS{Colors.RESET}                                                    {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}")
    print(f"{Colors.YELLOW}{Colors.BOLD}┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫{Colors.RESET}")
    
    for adapter in adapters:
        print(f"{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}  {Colors.GREEN}►{Colors.RESET} {adapter['name']}")
        print(f"{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}      IP: {Colors.CYAN}{adapter['ip']}{Colors.RESET}")
        print(f"{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}      Netmask: {adapter['netmask']}")
        print(f"{Colors.YELLOW}{Colors.BOLD}┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫{Colors.RESET}")
    
    public_ip = proxy_manager.get_current_public_ip()
    if public_ip:
        location = proxy_manager.get_ip_location(public_ip)
        print(f"{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}  {Colors.WHITE}{Colors.BOLD}  PUBLIC INFORMATION{Colors.RESET}                                                     {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}")
        print(f"{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}      Public IP: {Colors.CYAN}{public_ip}{Colors.RESET}")
        print(f"{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}      Location: {location}")
        print(f"{Colors.YELLOW}{Colors.BOLD}┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫{Colors.RESET}")
    
    if proxy_manager.current_proxy:
        print(f"{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}  {Colors.WHITE}{Colors.BOLD}  ACTIVE PROXY{Colors.RESET}                                                          {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}")
        print(f"{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}      {proxy_manager.current_proxy.get('http', 'None')}")
    
    print(f"{Colors.YELLOW}{Colors.BOLD}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{Colors.RESET}")
    print()

def main():
    clear()
    display_banner()
    
    network = NetworkManager()
    proxy_manager = ProxyManager()
    tunnel_manager = TunnelManager(proxy_manager)
    
    # Check admin privileges
    if not network.is_admin:
        warning("Not running with administrator/root privileges!")
        warning("Some features (like changing local IP) will not work.")
        print()
    else:
        status("Running with administrator privileges")
    
    adapters = network.get_adapters()
    
    if not adapters:
        warning("No network adapters found!")
        input("Press Enter to exit...")
        return
    
    print(f"\n{Colors.YELLOW}{Colors.BOLD}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{Colors.RESET}")
    print(f"{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}  {Colors.WHITE}{Colors.BOLD}  AVAILABLE NETWORK ADAPTERS{Colors.RESET}                                          {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}")
    print(f"{Colors.YELLOW}{Colors.BOLD}┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫{Colors.RESET}")
    
    for idx, adapter in enumerate(adapters, 1):
        print(f"{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}    {Colors.CYAN}{idx}.{Colors.RESET} {adapter['name']} - {adapter['ip']}")
    
    print(f"{Colors.YELLOW}{Colors.BOLD}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{Colors.RESET}")
    
    print()
    while True:
        try:
            choice = int(input(f"{Colors.BOLD}└─[{Colors.CYAN}?{Colors.RESET}{Colors.BOLD}] Select adapter number: {Colors.RESET}"))
            if 1 <= choice <= len(adapters):
                selected_adapter = adapters[choice-1]
                status(f"Selected adapter: {selected_adapter['name']}")
                break
            else:
                warning("Invalid choice!")
        except ValueError:
            warning("Please enter a number!")
    
    # Main loop
    while True:
        display_menu()
        print()
        option = input(f"{Colors.BOLD}└─[{Colors.CYAN}*{Colors.RESET}{Colors.BOLD}] Enter your choice: {Colors.RESET}")
        
        if option == '1':
            clear()
            display_banner()
            progress("MANUAL LOCAL IP CHANGE")
            print()
            print(f"{Colors.YELLOW}{Colors.BOLD}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{Colors.RESET}")
            print(f"{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}  Enter new network configuration:                            {Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}")
            print(f"{Colors.YELLOW}{Colors.BOLD}┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫{Colors.RESET}")
            
            new_ip = input(f"{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}    IP Address: {Colors.CYAN}")
            print(f"{Colors.RESET}", end="")
            mask = input(f"{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}    Subnet Mask [255.255.255.0]: {Colors.CYAN}") or "255.255.255.0"
            print(f"{Colors.RESET}", end="")
            gateway = input(f"{Colors.YELLOW}{Colors.BOLD}┃{Colors.RESET}    Gateway [optional]: {Colors.CYAN}") or None
            print(f"{Colors.RESET}", end="")
            print(f"{Colors.YELLOW}{Colors.BOLD}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{Colors.RESET}")
            
            if network.set_static_ip(selected_adapter['name'], new_ip, mask, gateway):
                status(f"Local IP changed to {new_ip}")
                selected_adapter['ip'] = new_ip
            else:
                warning("Failed to change local IP!")
        
        elif option == '2':
            clear()
            display_banner()
            progress("AUTOMATIC LOCAL IP CHANGE (DHCP)")
            print()
            if network.set_dhcp(selected_adapter['name']):
                status("Local IP set to DHCP mode")
                time.sleep(2)
                adapters = network.get_adapters()
                for adapter in adapters:
                    if adapter['name'] == selected_adapter['name']:
                        selected_adapter['ip'] = adapter['ip']
                        break
                info(f"New IP: {selected_adapter['ip']}")
            else:
                warning("Failed to enable DHCP!")
        
        elif option == '3':
            clear()
            display_banner()
            progress("MANUAL PUBLIC IP CHANGE")
            print()
            info("Enter proxy details manually:")
            print()
            proxy_ip = input(f"{Colors.BOLD}├─[{Colors.CYAN}*{Colors.RESET}{Colors.BOLD}] Proxy IP: {Colors.CYAN}")
            print(f"{Colors.RESET}", end="")
            proxy_port = input(f"{Colors.BOLD}  └─[{Colors.CYAN}*{Colors.RESET}{Colors.BOLD}] Proxy Port: {Colors.CYAN}")
            print(f"{Colors.RESET}", end="")
            
            proxy_url = f"http://{proxy_ip}:{proxy_port}"
            proxy_manager.current_proxy = {"http": proxy_url, "https": proxy_url}
            
            print()
            progress("Testing proxy...")
            test_result = proxy_manager.test_proxy(proxy_url)
            if test_result['working']:
                status(f"Proxy is working! Your IP: {test_result['ip']}")
            else:
                warning("Proxy is not responding!")
        
        elif option == '4':
            clear()
            display_banner()
            progress("SMART AUTOMATIC PUBLIC IP CHANGE")
            print()
            status("This may take 10-30 seconds...")
            print()
            
            new_ip = proxy_manager.get_new_ip()
            if new_ip:
                status(f"Public IP successfully changed!")
                location = proxy_manager.get_ip_location(new_ip)
                info(f"New location: {location}")
            else:
                warning("Failed to change public IP!")
                info("Try again later or use manual proxy entry")
        
        elif option == '5':
            clear()
            display_banner()
            progress("PROGRAM TUNNELING")
            print()
            
            if not proxy_manager.current_proxy:
                warning("No active proxy detected!")
                answer = input(f"{Colors.BOLD}└─[{Colors.CYAN}?{Colors.RESET}{Colors.BOLD}] Get a proxy first? (y/n): {Colors.RESET}").lower()
                if answer == 'y':
                    new_ip = proxy_manager.get_new_ip()
                    if not new_ip:
                        continue
                else:
                    continue
            
            print(f"\n{Colors.DIM}Examples: firefox, chrome, /usr/bin/curl, C:\\Windows\\notepad.exe{Colors.RESET}")
            program = input(f"{Colors.BOLD}└─[{Colors.CYAN}*{Colors.RESET}{Colors.BOLD}] Program path/name: {Colors.CYAN}")
            print(f"{Colors.RESET}", end="")
            
            tunnel_manager.tunnel_program(program)
        
        elif option == '6':
            clear()
            show_network_info(network, proxy_manager)
        
        elif option == '7':
            clear()
            display_banner()
            progress("PUBLIC IP TEST")
            print()
            public_ip = proxy_manager.get_current_public_ip()
            if public_ip:
                location = proxy_manager.get_ip_location(public_ip)
                status(f"Your public IP: {Colors.CYAN}{public_ip}{Colors.RESET}")
                info(f"Location: {location}")
            else:
                warning("Could not detect public IP!")
        
        elif option == '0':
            clear()
            display_banner()
            progress("Shutting down...")
            print()
            status("Thank you for using IP Changer!")
            print(f"\n{Colors.MAGENTA}{Colors.BOLD}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{Colors.RESET}")
            print(f"{Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}                         {Colors.WHITE}Goodbye! Have a great day!{Colors.RESET}                               {Colors.MAGENTA}{Colors.BOLD}┃{Colors.RESET}")
            print(f"{Colors.MAGENTA}{Colors.BOLD}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{Colors.RESET}")
            print()
            break
        
        else:
            warning("Invalid option! Please choose 0-7")
        
        print()
        input(f"{Colors.YELLOW}{Colors.BOLD}└─[{Colors.CYAN}*{Colors.RESET}{Colors.YELLOW}{Colors.BOLD}] Press Enter to continue...{Colors.RESET}")
        clear()
        display_banner()
        status(f"Active adapter: {selected_adapter['name']} - {selected_adapter['ip']}")
        print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}\n┌────────────────────────────────────────────────────────────────────────────┐{Colors.RESET}")
        print(f"{Colors.YELLOW}{Colors.BOLD}│{Colors.RESET}                      {Colors.RED} Interrupted by user{Colors.RESET}                                  {Colors.YELLOW}{Colors.BOLD}│{Colors.RESET}")
        print(f"{Colors.YELLOW}{Colors.BOLD}└────────────────────────────────────────────────────────────────────────────┘{Colors.RESET}")
    except Exception as e:
        warning(f"Unexpected error: {e}")
        input("Press Enter to exit...")
