import json
import time
import requests
import capmonster_python
from twocaptcha import TwoCaptcha
from fake_useragent import UserAgent

class CaptchaSolver:
    def __init__(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        self.service = self.config['captcha_info']['service']
        if self.service == 'capmonster':
            self.api_key = self.config['capmonster']['api_key']
            self.client = capmonster_python.HCaptchaTask(self.api_key)
        elif self.service == '2cap':
            self.api_key = self.config['2cap']['api_key']
            self.client = TwoCaptcha(self.api_key)
        else:
            raise ValueError(f"Unsupported service: {self.service}")
        self.user_agent = UserAgent().random
    
    def solve_captcha(self, site, sitekey, rqdata=None):
        if self.service == 'capmonster':
            return self.solve_capmonster_captcha(site, sitekey, rqdata)
        elif self.service == '2cap':
            return self.solve_2cap_captcha(site, sitekey)

    def solve_capmonster_captcha(self, site, sitekey, rqdata=None):
        try:
            self.client.set_fallback_to_actual_user_agent(True)
            self.client.set_user_agent(self.user_agent)
            task_id = self.client.create_task(site, sitekey, is_invisible=True, custom_data=rqdata)
            while True:
                try:
                    result = self.client.join_task_result(task_id)
                    if result:
                        return result.get("gRecaptchaResponse")
                    else:
                        print("Captcha not solved yet, retrying...")
                        time.sleep(5)
                except Exception as e:
                    if "[ERROR_CAPTCHA_UNSOLVABLE]" in str(e):
                        print("[!] Captcha Not Supported or Unsolvable")
                        return None
                    else:
                        print("Error during captcha solving:", e)
                        time.sleep(5)
                        continue
        except Exception as e:
            print(f"Failed to create or solve captcha: {e}")
            return None

    def solve_2cap_captcha(self, site, sitekey):
        try:
            result = self.client.hcaptcha(
                sitekey=sitekey,
                url=site
            )
            return result.get('code')
        except Exception as e:
            print(f"Failed to solve captcha with 2Captcha: {e}")
            return None

    def get_balance(self):
        if self.service == 'capmonster':
            return self.get_capmonster_balance()
        elif self.service == '2cap':
            return self.get_2cap_balance()

    def get_capmonster_balance(self):
        try:
            balance = self.client.get_balance()
            print(f"[!] CapMonster Balance: ${balance}\n\n")
            return balance
        except Exception as e:
            print("Failed to fetch CapMonster balance:", e)
            return None

    def get_2cap_balance(self):
        try:
            response = requests.get(f"https://2captcha.com/res.php?key={self.api_key}&action=getbalance&json=1")
            response_data = response.json()
            if response_data.get('status') == 1:
                balance = response_data['request']
                print(f"[!] 2Captcha Balance: ${balance}\n\n")
                return balance
            else:
                print(f"Failed to retrieve 2Captcha balance: {response_data}")
                return None
        except Exception as e:
            print(f"Failed to fetch 2Captcha balance: {e}")
            return None
