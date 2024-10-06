import threading
import json
import requests
import time
import urllib3
import socks
import dotenv
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Global dictionary to track threads by their arguments
threads = {}
lock = threading.Lock()  # Ensure thread-safe operations on the dictionary

API_TOKEN = dotenv.get_key("config.env", "TELEGRAM_BOT_TOKEN")
TELEGRAM_PROXY = dotenv.get_key("config.env", "TELEGRAM_PROXY")


def Notify(msg, chat_id):
    proxies = {"http":TELEGRAM_PROXY,
               "https":TELEGRAM_PROXY}
    url = f"https://api.telegram.org/bot{API_TOKEN}/sendMessage"
    params = {"chat_id": chat_id,
              "text": msg}
    requests.get(url, params=params, proxies=proxies)


def CheckStatus(userid, address, api_key, api_pass, panelid, vpsid, nickname, hostname, vpsip, warn, tsleep, warnsleep, stop_event):
    while not stop_event.is_set():
        print(f"[{nickname}] Checking...")
        params = {
            "act": "vps_stats",
            "svs": vpsid,
            "api": "json",
            "apikey": api_key,
            "apipass": api_pass
        }
        url = f"https://{address}/index.php"

        try:
            response = requests.get(url, params=params, verify=False)
            response = response.json()
            print(f'[{nickname}] FREE GB: {response["info"]["bandwidth"]["free_gb"]}')
            if response["info"]["bandwidth"]["free_gb"] < warn:
                msg = f'''🔴 Traffic is reaching Quota
🎛 Panel: {nickname}
🖥 VPS Name: {hostname}
🌐 IP: {vpsip}
📈 Usage: {response["info"]["bandwidth"]["used_gb"]}/{response["info"]["bandwidth"]["limit_gb"]}
📊 Remaining: {response["info"]["bandwidth"]["free_gb"]}'''
                print(f'[{nickname}] Sending message to telegram...')
                Notify(msg, userid)
                for _ in range(warnsleep//5):
                    if stop_event.is_set():
                        print(f'[{nickname}] Terminating thread...')
                        return
                    time.sleep(5)
            else:
                for _ in range(tsleep//5):
                    if stop_event.is_set():
                        print(f'[{nickname}] Terminating thread...')
                        return
                    time.sleep(5)
        except Exception as e:
            print("Exception happened:", e)
            for _ in range(tsleep//5):
                if stop_event.is_set():
                    print(f'[{nickname}] Terminating thread...')
                    return
                time.sleep(5)

def CheckOn(userid, address, api_key, api_pass, panelid, vpsid, nickname, hostname, vpsip, warn, tsleep, warnsleep):
    global threads
    thread_key = (userid, address, api_key, api_pass, panelid, vpsid, nickname, warn, tsleep, warnsleep)

    with lock:
        if thread_key in threads:
            print(f"Thread with args {userid}, {address}, {api_key}, {api_pass}, {panelid}, {vpsid}, {nickname}, {warn}, {tsleep}, {warnsleep} is already running")
            return

        # Create a new stop event
        stop_event = threading.Event()
        thread = threading.Thread(target=CheckStatus, args=(userid, address, api_key, api_pass, panelid, vpsid, nickname, hostname, vpsip, warn, tsleep, warnsleep, stop_event))
        threads[thread_key] = (thread, stop_event)
        thread.start()
        print(f"Started thread with args: {userid}, {address}, {api_key}, {api_pass}, {panelid}, {vpsid}, {nickname}, {warn}, {tsleep}, {warnsleep}")


def CheckOff(userid, address, api_key, api_pass, panelid, vpsid, nickname):
    global threads
    keys_to_stop = []
    thread_key = (userid, address, api_key, api_pass, panelid, vpsid, nickname)

    with lock:
        for thread_key in threads.keys():
            if (thread_key[0], thread_key[1], thread_key[2], thread_key[3], thread_key[4], thread_key[5], thread_key[6]) == (userid, address, api_key, api_pass, panelid, vpsid, nickname):
                keys_to_stop.append(thread_key)
        if len(keys_to_stop) == 0:
            print(f"No thread running with args: {userid}, {address}, {api_key}, {api_pass}, {panelid}, {vpsid}, {nickname}")
        else:
            for key in keys_to_stop:
                thread, stop_event = threads[key]
                stop_event.set()
                del threads[thread_key]
                print(f"Stopped thread with args: {key[0]}, {key[1]}, {key[2]}, {key[3]}, {key[4]}, {key[5]}, {key[5]}, {key[7]}, {key[8]}, {key[9]}")
