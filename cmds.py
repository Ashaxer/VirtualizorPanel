import requests
import pickle
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class User:
    def __init__(self, name, userid):
        self.name = name
        self.userid = userid
        self.panels = {}

    def verify_api(self, address, api_key, api_pass):
        params = {"act": "vs",
                  "api": "json",
                  "apikey": api_key,
                  "apipass": api_pass}
        url = f"https://{address}/index.php"
        result = requests.post(url, params=params, verify=False)
        try:
            if int(result.json()["uid"]) > 0: return int(result.json()["uid"])
        except:
            pass
        return False

    def AddPanel(self, address, api_key, api_pass, nickname):
        uid = self.verify_api(address, api_key, api_pass)
        if uid and self.panels.get(uid) is None:
            self.panels[str(uid)] = VirtualizorPanel(self.userid, address, api_key, api_pass, nickname)
            return True
        elif uid:
            return "AlreadyExists"
        else:
            return False

    def RemPanel(self, address, api_key):
        dummy = self.panels.copy()
        for uid, panel in dummy.items():
            try:
                if panel.address == address and panel.api_key == api_key:
                    self.panels.pop(uid)
            except:
                pass
    def SendWelcomeMsg(self):
        pass
        # send msg to bot

    def NotiLog(self):
        output = []
        log = []
        for panelid, panel in self.panels.items():
            log.append(panel.NotiLogPanel())
        for panels in log:
            for vps in panels:
                output.append(vps)
        return output

class VirtualizorPanel:
    def __init__(self, userid, address, api_key, api_pass, nickname):
        self.userid = userid
        self.address = address
        self.api_key = api_key
        self.api_pass = api_pass
        self.nickname = nickname
        self.vpss = {}

    def GetInfo(self):
        params = {"act": "vs",
                  "api": "json",
                  "apikey": self.api_key,
                  "apipass": self.api_pass}
        url = f"https://{self.address}/index.php"
        result = requests.post(url, params=params, verify=False)
        try:
            Json = result.json()
            self.panelid = Json['uid']
            msg = f"""🎛 PanelName: {self.nickname}
🆔 {self.panelid}
🌐 Address: {self.address}
📋 UserName: {Json['username']}
📋 FirstName: {Json['preferences']['fname']}
📋 LastName: {Json['preferences']['lname']}
🖥 VPS Count: {Json['counts']['vps']}"""
            return msg
        except:
            return "Error getting panel info..."

    def VPSListJson(self):
        params = {"act": "listvs",
                  "api": "json",
                  "apikey": self.api_key,
                  "apipass": self.api_pass}
        url = f"https://{self.address}/index.php"
        result = requests.post(url, params=params, verify=False)
        try:
            Json = result.json()["vs"]
            return Json
        except:
            return False

    def VPSList(self):
        params = {"act": "listvs",
                  "api": "json",
                  "apikey": self.api_key,
                  "apipass": self.api_pass}
        url = f"https://{self.address}/index.php"
        result = requests.post(url, params=params, verify=False)
        try:
            Json = result.json()["vs"]
            for vpsid, vps in Json.items():
                if vpsid not in self.vpss:
                    self.vpss[vpsid] = VPS(self.address, self.api_key, self.api_pass, self.panelid,self.nickname,
                    vps['vpsid'], vps['vps_name'], vps['uuid'], vps['uid'], vps['plid'], vps['hostname'], vps['osid'],
                    vps['os_name'], vps['space'], vps['ram'], vps['cpu'], vps['cores'], vps['bandwidth'], vps['vnc'],
                    vps['vncport'], vps['vnc_passwd'], vps['suspended'], vps['suspend_reason'], vps['nw_suspended'],
                    vps['used_bandwidth'], vps['email'], vps['os_distro'], vps['status'], vps['ips'])
                else:
                    self.vpss[vpsid] = VPS.UpdateVPSInfo(self.vpss[vpsid] ,self.address, self.api_key, self.api_pass, self.panelid,self.nickname,
                    vps['vpsid'], vps['vps_name'], vps['uuid'], vps['uid'], vps['plid'], vps['hostname'], vps['osid'],
                    vps['os_name'], vps['space'], vps['ram'], vps['cpu'], vps['cores'], vps['bandwidth'], vps['vnc'],
                    vps['vncport'], vps['vnc_passwd'], vps['suspended'], vps['suspend_reason'], vps['nw_suspended'],
                    vps['used_bandwidth'], vps['email'], vps['os_distro'], vps['status'], vps['ips'])
                return self.vpss
        except Exception as e:
            print(e)
            return False

    def NotiLogPanel(self):
        log = []
        for vpsid, vps in self.vpss.items():
            notilog = vps.NotiLogVPS()
            notilog['api_key'] = self.api_key
            notilog['api_pass'] = self.api_pass
            notilog['address'] = self.address
            notilog['nickname'] = self.nickname
            log.append(notilog)
        return log


class VPS:
    def __init__(self, address, api_key, api_pass, panelid, nickname, vpsid, vps_name, uuid, uid, plid, hostname, osid,
                 os_name, space, ram, cpu, cores, bandwidth,vnc, vncport, vnc_passwd, suspended, suspend_reason,
                 nw_suspended, used_bandwidth, email, os_distro, status, ips):
        self.address = address
        self.api_key = api_key
        self.api_pass = api_pass
        self.panelid = panelid
        self.nickname = nickname
        self.vpsid = vpsid
        self.vps_name = vps_name
        self.uuid = uuid
        self.uid = uid
        self.plid = plid
        self.hostname = hostname
        self.osid = osid
        self.os_name = os_name
        self.space = space
        self.ram = ram
        self.cpu = cpu
        self.cores = cores
        self.bandwidth = bandwidth
        self.vnc = vnc
        self.vncport = vncport
        self.vnc_passwd = vnc_passwd
        self.suspended = suspended
        self.suspend_reason = suspend_reason
        self.nw_suspended = nw_suspended
        self.used_bandwidth = used_bandwidth
        self.email = email
        self.os_distro = os_distro
        self.status = status
        self.ips = ips
        self.Notification = Notification(self.vpsid, self.panelid, 250, 300, 3600)

    def UpdateVPSInfo(self, address, api_key, api_pass, panelid, nickname, vpsid, vps_name, uuid, uid, plid, hostname, osid,
                 os_name, space, ram, cpu, cores, bandwidth ,vnc, vncport, vnc_passwd, suspended, suspend_reason,
                 nw_suspended, used_bandwidth, email, os_distro, status, ips):
        self.address = address
        self.api_key = api_key
        self.api_pass = api_pass
        self.panelid = panelid
        self.nickname = nickname
        self.vpsid = vpsid
        self.vps_name = vps_name
        self.uuid = uuid
        self.uid = uid
        self.plid = plid
        self.hostname = hostname
        self.osid = osid
        self.os_name = os_name
        self.space = space
        self.ram = ram
        self.cpu = cpu
        self.cores = cores
        self.bandwidth = bandwidth
        self.vnc = vnc
        self.vncport = vncport
        self.vnc_passwd = vnc_passwd
        self.suspended = suspended
        self.suspend_reason = suspend_reason
        self.nw_suspended = nw_suspended
        self.used_bandwidth = used_bandwidth
        self.email = email
        self.os_distro = os_distro
        self.status = status
        self.ips = ips
        return self

    def MainInfo(self):
        IPs = ""
        for _, IP in self.ips.items(): IPs += f'\n{IP}'
        return f"""VPS Hostname: {self.hostname}
VPS Name: {self.vps_name}
VPS ID: {self.vpsid}
==============
IPs: {IPs}
OS: {self.os_name}
CPU: {self.cores} * {float(self.cpu)/1000} GHz
RAM: {float(self.ram)/1024} GB
SPACE: {int(self.space)} GB
Bandwidth: {float(self.used_bandwidth)} / {float(self.bandwidth)} GB ({round(float(self.used_bandwidth)/float(self.bandwidth)*100,2)} %)
Remaining: {round(float(self.bandwidth)-float(self.used_bandwidth),2)} GB
==============
Panel Name: {self.nickname}
Panel ID: {self.panelid}
Panel Address: {self.address}
Panel Email: {self.email}"""

    def NotiLogVPS(self):
        return self.Notification.Info()

class Notification:
    def __init__(self, vpsid, panelid , warn, sleep, warnsleep):
        self.vpsid = vpsid
        self.panelid = panelid
        self.warn = warn
        self.sleep = sleep
        self.warnsleep = warnsleep
        self.notify = True

    def Info(self):
        return {
            "vpsid": self.vpsid,
            "panelid": self.panelid,
            "warn": self.warn,
            "sleep": self.sleep,
            "warnsleep": self.warnsleep,
            "Notify": self.notify
            }

    def ChangeWarn(self, warn):
        self.warn = int(warn)

    def ChangeSleep(self, sleep):
        self.sleep = int(sleep)

    def ChangeWarnSleep(self, warnsleep):
        self.warnsleep = int(warnsleep)

    def ChangeNotify(self, notify):
        self.notify = notify

    def ToggleNotify(self):
        if self.notify: self.notify = False
        else: self.notify = True


def SaveUserData(User):
    try:
        with open('database.pkl', 'rb') as dbf:
            users = pickle.load(dbf)
    except:
        users = {}
    users[User.userid] = User
    with open('database.pkl', 'wb') as dbf:
        pickle.dump(users, dbf)


def LoadUserData(User):
    try:
        with open('database.pkl', 'rb') as dbf:
            return pickle.load(dbf)[int(User)]
    except:
        return False

def LoadData():
    try:
        with open('database.pkl', 'rb') as dbf:
            return pickle.load(dbf)
    except:
        return False
