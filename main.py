import os
import tls_client 
import random 
import base64, json
import re
import fake_useragent, string
import time
from solver import CaptchaSolver
import threading 
import json 

with open("config.json", "r") as f:
    config = json.load(f)
    user_token = config["user_token"]

api = "https://canary.discord.com/api/v8"
delay = 0
bot_ids = open("bot_ids.txt", "r").read().splitlines()
guild_ids = open("server_ids.txt", "r").read().splitlines()
solver = CaptchaSolver('config.json')

def create_session():
  session = tls_client.Session(
      client_identifier="chrome112",
      random_tls_extension_order=True

  )
  return session

def get_build_number():
  client = create_session()
  headers = {
      "Accept": "*/*",
      "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
      "Cache-Control": "no-cache",
      "Pragma": "no-cache",
      "Referer": "https://discord.com/login",
      "Sec-Ch-Ua": '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
      "Sec-Ch-Ua-Mobile": "?0",
      "Sec-Ch-Ua-Platform": '"macOS"',
      "Sec-Fetch-Dest": "script",
      "Sec-Fetch-Mode": "no-cors",
      "Sec-Fetch-Site": "same-origin",
      "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
  }
  request = client.get("https://discord.com/login", headers=headers)
  pattern = r'<script\s+src="([^"]+\.js)"\s+defer>\s*</script>'
  matches = re.findall(pattern, request.text)
  for file in matches:
    build_url = f"https://discord.com{file}"
    response = client.get(build_url, headers=headers)
    if "buildNumber" not in response.text:
        continue
    else:
        build_number = response.text.split('build_number:"')[1].split('"')[0]
        return build_number

def xsuper(ua):
  sec_ch_ua = '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"'
  user_agent = ua
  accept_language = "en-US,en;q=0.9"
  client_identifier = 'chrome_120'
  browser_version = '120.0.0.0'
  build_number = get_build_number()
  data = {
      "os": "Windows",
      "browser": "Chrome",
      "device": "",
      "system_locale": "en-US",
      "browser_user_agent": user_agent,
      "browser_version": browser_version,
      "os_version": "10",
      "referrer": "",
      "referring_domain": "",
      "referrer_current": "",
      "referring_domain_current": "",
      "release_channel": "stable",
      "client_build_number": build_number,
      "client_event_source": None,
      "design_id": 0
  }
  return base64.b64encode(json.dumps(data, separators=(',', ':')).encode()).decode()

def get_headers(token):
  user_agent = fake_useragent.UserAgent().random
  headers = {
      'authority': 'discord.com',
      'accept': '*/*',
      'accept-language': 'it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7',
      'authorization': token,
      'content-type': 'application/json',
      'origin': 'https://discord.com',
      'referer': 'https://discord.com/channels/@me',
      'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
      'sec-ch-ua-mobile': '?0',
      'sec-ch-ua-platform': '"Windows"',
      'sec-fetch-dest': 'empty',
      'sec-fetch-mode': 'cors',
      'sec-fetch-site': 'same-origin',
      'user-agent': user_agent,
      'x-context-properties': xsuper(user_agent),
      'x-debug-options': 'bugReporterEnabled',
      'x-discord-locale': 'en-GB',
  }
  return headers

def get_cookies():
  client = create_session()
  cookies = {}
  response = client.get('https://discord.com')
  for cookie in response.cookies:
      if cookie.name.startswith('__') and cookie.name.endswith('uid'):
          cookies[cookie.name] = cookie.value
  return cookies

def gen_sid():
  return ''.join(random.choice(string.ascii_lowercase) + random.choice(string.digits) for _ in range(16))

def check_member(guild, bot):
  headers = get_headers(user_token)
  cookies = get_cookies()
  client = create_session()
  sid = gen_sid()
  request = client.get(api+"/guilds/"+guild+"/members/"+bot, headers=headers, cookies=cookies)
  if request.status_code == 200:
    return True
  return False

def hcap_solve(rqdata):
    site = "https://discord.com"
    sitekey = "a9b5fb07-92ff-493f-86fe-352a2803b3df"
    print("[!] Solving Captcha...")
    start_time = time.time()
    resp = solver.solve_captcha(site, sitekey, rqdata)
    elapsed_time = time.time() - start_time
    if resp:
       print(f"[!] Captcha Solved")
    else:
        print(f"[!] Captcha Not Solved | Time: {elapsed_time:.2f} seconds.")
    return resp
    
def add_bot(bot_id, server_id):
    if check_member(server_id, bot_id):
        print(f"[!] {bot_id} already in {server_id}.")
        return
    print(f"[!] Adding {bot_id} to {server_id}.")
    client = create_session()
    headers = get_headers(user_token)
    cookies = get_cookies()
    payload = {"authorize": True, "permissions": 0, "guild_id": server_id, "guild": server_id}
    request = client.post(f"https://canary.discord.com/api/v10/oauth2/authorize?client_id={bot_id}&permissions=0&scope=bot", headers=headers, json=payload, cookies=cookies)
    if "captcha_rqtoken" in request.json():
        rtkn = request.json()["captcha_rqtoken"]
        rqdata = request.json()["captcha_rqdata"] if "captcha_rqdata" in request.json() else None
        captcha_key = hcap_solve(rqdata) if rqdata else None
        payload2 = {"captcha_service": "hcaptcha", "captcha_key": captcha_key, "captcha_rqtoken": rtkn, "authorize": True, "permissions": 0, "guild_id": server_id, "guild": server_id, "season_id": gen_sid()}
        request2 = client.post(f"https://canary.discord.com/api/v10/oauth2/authorize?client_id={bot_id}&permissions=0&scope=bot", headers=headers, json=payload2, cookies=cookies)
    else:
        request2 = request
    if request2.status_code == 429:
        rate_limit = request2.json()
        sleep_time = rate_limit["retry_after"]
        print(f"[!] Rate Limited | Retry After: {sleep_time}")
        time.sleep(sleep_time)
        add_bot(bot_id, server_id)
        return
    if request2.status_code == 200:
        print(f"[!] Added Bot {bot_id} To {server_id}")
    elif "captcha" in request2.text:
        print(f"[!] Failed to add bot {bot_id} to {server_id}, due to captcha failure")
    else:
        print(f"[!] Failed to add bot {bot_id} to {server_id}, {request2.text}")

def main():
    for server_id in guild_ids:
        for bot_id in bot_ids:
            print("adding")
            add_bot(bot_id, server_id)
            time.sleep(delay)
        time.sleep(delay+5)

def run_in_threads():
    thread_count = 0
    for server_id in guild_ids:
        for bot_id in bot_ids:
            threading.Thread(target=add_bot, args=(bot_id, server_id),).start()
            thread_count+1
            if str(thread_count) == "5" or str(thread_count).endswith("5"):
                time.sleep(1)
        
if __name__ == "__main__":
    solver.get_balance()
    run_in_threads()
