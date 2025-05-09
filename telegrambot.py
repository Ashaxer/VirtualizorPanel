import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.utils.callback_data import CallbackData
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import cmds
import uuid
from notification_handler import CheckOn, CheckOff
import dotenv
import socks

def Startup_Notifications():
    users = cmds.LoadData()
    for userid, user in users.items():
        for panelid, panel in user.panels.items():
            for vpsid, vps in panel.vpss.items():
                if vps.Notification.notify:
                    try:
                        CheckOn(vps.userid,vps.address,vps.api_key,vps.api_pass,vps.panelid,vps.vpsid,vps.nickname,vps.hostname,list(vps.ips.items())[0][1],vps.Notification.warn,vps.Notification.sleep,vps.Notification.warnsleep)
                    except:
                        pass

API_TOKEN = dotenv.get_key("config.env", "TELEGRAM_BOT_TOKEN")
TELEGRAM_PROXY = dotenv.get_key("config.env", "TELEGRAM_PROXY")
ITEM_PER_PAGE=10
# States
class Form(StatesGroup):
    getPanelName = State()
    getPanelAddress = State()
    getApiKey = State()
    getApiPass = State()


# Callback templates
cb_1 = CallbackData("post", "act")
cb_2 = CallbackData("post", "act", "d_1")
cb_3 = CallbackData("post", "act", "d_1", "d_2")
cb_4 = CallbackData("post", "act", "d_1", "d_2", "d_3")
cb_5 = CallbackData("post", "act", "d_1", "d_2", "d_3", "d_4")
cb_7 = CallbackData("post", "act", "d_1", "d_2", "d_3", "d_4", "d_5", "d_6")

# Keyboards and Buttons
btn_MainMenu = InlineKeyboardButton("🏘 Main Menu", callback_data=cb_1.new(act="MainMenu"))
btn_CancelState = InlineKeyboardButton("✖️ Cancel", callback_data=cb_1.new(act="CancelState"))

form_data = {}

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN, proxy=TELEGRAM_PROXY)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
# dp.middleware.setup(LoggingMiddleware()) #Uncomment this if you want specific bot interaction log in terminal


@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user = cmds.LoadUserData(message.from_user.id)
    if not user:
        user = cmds.User(message.from_user.first_name, message.from_user.id)

    btn_AddPanel = InlineKeyboardButton("➕ Add Panel",
                                        callback_data=cb_2.new(act="addNewPanelForm", d_1=str(uuid.uuid4())))
    btn_ListPanel = InlineKeyboardButton("🟰 Panels list", callback_data=cb_2.new(act="listPanel",d_1=0))
    kb = InlineKeyboardMarkup().add(btn_AddPanel, btn_ListPanel)
    len(user.panels)
    await message.reply(
        f"""Welcome {message.from_user.first_name} to Virtualizor Bot
You have currently {len(user.panels)} Active Panels🎛 in this Bot
Use buttons to integrate with the Bot🤖"""
        , reply_markup=kb)

@dp.callback_query_handler(cb_1.filter(act="MainMenu"))
async def send_welcome(callback_query: types.CallbackQuery, callback_data):
    user = cmds.LoadUserData(callback_query.from_user.id)
    if not user:
        user = cmds.User(callback_query.from_user.first_name, callback_query.from_user.id)

    btn_AddPanel = InlineKeyboardButton("➕ Add Panel",
                                        callback_data=cb_2.new(act="addNewPanelForm", d_1=str(uuid.uuid4())))
    btn_ListPanel = InlineKeyboardButton("🟰 Panels list", callback_data=cb_2.new(act="listPanel", d_1=0))
    kb = InlineKeyboardMarkup().add(btn_AddPanel, btn_ListPanel)
    len(user.panels)
    await callback_query.message.edit_text(
        f"""Welcome {callback_query.from_user.first_name} to Virtualizor Bot
You have currently {len(user.panels)} Active Panels🎛 in this Bot
Use buttons to integrate with the Bot🤖"""
        , reply_markup=kb)

@dp.callback_query_handler(cb_1.filter(act="CancelState"),state='*')
async def cancel_handler(callback_query: types.CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup().add(btn_MainMenu)
    current_state = await state.get_state()
    if current_state is None:
        return
    await state.finish()
    await callback_query.message.edit_text("Operation Canceled...", reply_markup=kb)


@dp.callback_query_handler(cb_2.filter(act="addNewPanelForm"))
async def process_new_panel(callback_query: types.CallbackQuery, callback_data, state=FSMContext):
    kb = InlineKeyboardMarkup().add(btn_CancelState)
    session_id = callback_data['d_1']
    form_data[session_id] = {}
    await Form.getPanelName.set()
    async with state.proxy() as data:
        data["session_id"] = session_id
    await callback_query.message.edit_text(f'Choose a name for this Panel:', reply_markup=kb)


@dp.message_handler(state=Form.getPanelName)
async def process_panel_address(message: types.Message, state=FSMContext):
    kb = InlineKeyboardMarkup().add(btn_CancelState)
    async with state.proxy() as data:
        session_id = data["session_id"]
    form_data[session_id]["nickname"] = message.text
    await Form.getPanelAddress.set()
    await message.reply("Enter your panel address (with port):\nExample: 172.16.75.41:4083", reply_markup=kb)


@dp.message_handler(state=Form.getPanelAddress)
async def process_api_key(message: types.Message, state=FSMContext):
    kb = InlineKeyboardMarkup().add(btn_CancelState)
    async with state.proxy() as data:
        session_id = data["session_id"]
    form_data[session_id]["panel_address"] = message.text
    await Form.getApiKey.set()
    await message.reply("Enter your api key:", reply_markup=kb)


@dp.message_handler(state=Form.getApiKey)
async def process_api_pass(message: types.Message, state=FSMContext):
    kb = InlineKeyboardMarkup().add(btn_CancelState)
    async with state.proxy() as data:
        session_id = data["session_id"]
    form_data[session_id]["api_key"] = message.text
    await Form.getApiPass.set()
    await message.reply("Enter your api pass:", reply_markup=kb)


@dp.message_handler(state=Form.getApiPass)
async def process_add_panel_confirm(message: types.Message, state=FSMContext):
    async with state.proxy() as data:
        session_id = data["session_id"]
    form_data[session_id]["api_pass"] = message.text
    btn_confirm = (InlineKeyboardButton("Confirm", callback_data=cb_2.new("addNewPanel", session_id)))
    kb = InlineKeyboardMarkup().row(btn_confirm).row(btn_CancelState)
    await state.finish()
    await message.reply(f"""Double check your info:

🎛 Panel Name:    {form_data[session_id]['nickname']}
🌐 Panel Address:    {form_data[session_id]['panel_address']}
🔑 API KEY:    {form_data[session_id]['api_key']}
🗝 API PASS:    {form_data[session_id]['api_pass']}""", reply_markup=kb)


@dp.callback_query_handler(cb_2.filter(act="addNewPanel"))
async def process_add_panel(callback_query: types.CallbackQuery, callback_data):
    kb = InlineKeyboardMarkup().add(btn_MainMenu)
    user = cmds.LoadUserData(callback_query.from_user.id)
    session_id = callback_data['d_1']
    result = user.AddPanel(form_data[session_id]["panel_address"],
                           form_data[session_id]["api_key"],
                           form_data[session_id]["api_pass"],
                           form_data[session_id]["nickname"])
    if result:
        await callback_query.message.edit_text(f'✅ Panel Added Successfully...', reply_markup=kb)
    else:
        await callback_query.message.edit_text(f'❌ Invalid data...', reply_markup=kb)


@dp.callback_query_handler(cb_2.filter(act="listPanel"))
async def generate_panel_list(callback_query: types.CallbackQuery, callback_data):
    try:
        user = cmds.LoadUserData(callback_query.from_user.id)
        page = int(callback_data['d_1'])
        panels_items = user.panels.items()
        if len(panels_items) >= ITEM_PER_PAGE:
            last_page = (len(panels_items)-1)//ITEM_PER_PAGE
            panels = list(panels_items)[page*ITEM_PER_PAGE:(page+1)*ITEM_PER_PAGE]
            btn_Previous = InlineKeyboardButton("◀", callback_data=cb_2.new(act="listPanel", d_1=0 if page == 0 else page - 1))
            btn_PageNumber = InlineKeyboardButton(f"Page {page+1}", callback_data=cb_2.new(act="listPanel", d_1=page))
            btn_Next = InlineKeyboardButton("▶", callback_data=cb_2.new(act="listPanel", d_1=last_page if page == last_page else page + 1))
        else:
            panels = list(panels_items)
        kb = InlineKeyboardMarkup()
        for uid, panel in panels:
            kb.row(InlineKeyboardButton(f"🎛 {panel.nickname}", callback_data=cb_4.new(act="getVPSList", d_1=uid, d_2=0, d_3=page)))
        if len(panels_items) >= ITEM_PER_PAGE: kb.row(btn_Previous, btn_PageNumber, btn_Next)
        kb.add(btn_MainMenu)
        await callback_query.message.edit_text("Choose a panel:", reply_markup=kb)
    except Exception as e:
        print(e)
        await callback_query.answer("Error occurred, Probably using an old message.")


@dp.callback_query_handler(cb_4.filter(act="getVPSList"))
async def generate_vps_list(callback_query: types.CallbackQuery, callback_data):
    # d_3 is panel list page
    try:
        kb = InlineKeyboardMarkup()
        btn_removePanel = InlineKeyboardButton("✖️ Remove Panel", callback_data=cb_4.new(act="removePanel", d_1=callback_data['d_1'],d_2=callback_data['d_2'], d_3=callback_data['d_3']))
        user = cmds.LoadUserData(callback_query.from_user.id)
        msg = user.panels[callback_data['d_1']].GetInfo()
        vpslists_items = user.panels[callback_data['d_1']].VPSList().items()
        page = int(callback_data['d_2'])
        btn_Back = InlineKeyboardButton("🔙 Back", callback_data=cb_2.new("listPanel", d_1=callback_data["d_3"]))
        if len(vpslists_items) >= ITEM_PER_PAGE:
            last_page = (len(vpslists_items)-1)//ITEM_PER_PAGE
            vpslist = list(vpslists_items)[page*ITEM_PER_PAGE:(page+1)*ITEM_PER_PAGE]
            btn_Previous = InlineKeyboardButton("◀", callback_data=cb_4.new(act="getVPSList", d_1=callback_data['d_1'], d_2=0 if page == 0 else page - 1, d_3=callback_data["d_3"]))
            btn_PageNumber = InlineKeyboardButton(f"Page {page+1}", callback_data=cb_4.new(act="getVPSList", d_1=callback_data['d_1'], d_2=page, d_3=callback_data["d_3"]))
            btn_Next = InlineKeyboardButton("▶", callback_data=cb_4.new(act="getVPSList", d_1=callback_data['d_1'], d_2=last_page if page == last_page else page + 1, d_3=callback_data["d_3"]))
        else:
            vpslist = list(vpslists_items)
        try:
            for vpsid, vps in vpslist:
                kb.row(InlineKeyboardButton(f"{'🗑' if vps.isObsolete else '🔴' if vps.suspended != '0' or vps.nw_suspended is not None else '🟢'} ({vpsid}) {vps.hostname} {next(iter(vps.ips.values()))}",
                                            callback_data=cb_5.new(act="getVPS",
                                                                   d_1=callback_data['d_1'], d_2=vpsid, d_3=page, d_4=callback_data["d_3"])))
        except:
            pass
        if len(vpslists_items) >= ITEM_PER_PAGE: kb.row(btn_Previous, btn_PageNumber, btn_Next)
        kb.add(btn_removePanel).row(btn_Back, btn_MainMenu)
        await callback_query.message.edit_text(msg, reply_markup=kb)
    except Exception as e:
        print(e)
        await callback_query.answer("Error occurred, Probably using an old message.")

@dp.callback_query_handler(cb_5.filter(act="getVPS"))
async def generate_vps_info(callback_query: types.CallbackQuery, callback_data):
    try:
        user = cmds.LoadUserData(callback_query.from_user.id)
        btn_Back = InlineKeyboardButton("🔙 Back", callback_data=cb_4.new(act="getVPSList", d_1=callback_data['d_1'], d_2=callback_data["d_3"], d_3=callback_data["d_4"]))
        vpslist = user.panels[callback_data['d_1']].VPSList()
        if vpslist[callback_data['d_2']].Notification.notify:
            noti_btn_txt = "🔔 Notification Settings"
        else:
            noti_btn_txt = "🔕 Notification Settings"

        btn_notify = InlineKeyboardButton(noti_btn_txt,
                                          callback_data=cb_7.new(act="notifSet", d_1=callback_data['d_1'],
                                                                 d_2=callback_data['d_2'], d_3=False, d_4=False, d_5=callback_data["d_3"], d_6=callback_data["d_4"]))

        kb = InlineKeyboardMarkup().add(btn_notify)
        if vpslist[callback_data['d_2']].isObsolete:
            btn_obs = InlineKeyboardButton("🗑 Remove this VPS", callback_data=cb_3.new(act="removeVPSConfirmed",d_1=callback_data['d_1'], d_2=callback_data['d_2']))
            kb.add(btn_obs)
        kb.row(btn_Back, btn_MainMenu)

        await callback_query.message.edit_text(vpslist[callback_data['d_2']].MainInfo(), reply_markup=kb)
    except Exception as e:
        print(e)
        await callback_query.answer("Error occurred, Probably using an old message.")



@dp.callback_query_handler(cb_3.filter(act="removeVPSConfirmed"))
async def toggle_notify(callback_query: types.CallbackQuery, callback_data):
    try:
        user = cmds.LoadUserData(callback_query.from_user.id)
        panel = user.panels[callback_data['d_1']]
        vpsid = callback_data['d_2']
        panel.RemVPS(vpsid)
        kb = InlineKeyboardMarkup().add(btn_MainMenu)
        await callback_query.message.edit_text(f"VPS ID \"{vpsid}\" removed from your panel.", reply_markup=kb)
    except Exception as e:
        print(e)
        await callback_query.answer("Error occurred, Probably using an old message.")

@dp.callback_query_handler(cb_4.filter(act="removePanel"))
async def toggle_notify(callback_query: types.CallbackQuery, callback_data):
    try:
        user = cmds.LoadUserData(callback_query.from_user.id)
        nickname = user.panels[callback_data['d_1']].nickname
        btn_Yes = InlineKeyboardButton("🗑 Yes", callback_data=cb_2.new(act="removePanelConfirmed", d_1=callback_data["d_1"]))
        btn_No = InlineKeyboardButton("No", callback_data=cb_4.new(act="getVPSList", d_1=callback_data["d_1"], d_2=callback_data["d_2"], d_3=callback_data["d_3"]))
        kb = InlineKeyboardMarkup().row(btn_Yes,btn_No)
        await callback_query.message.edit_text(f"Are you sure you want to remove \"{nickname}\" Panel from your panels list?", reply_markup=kb)
    except Exception as e:
        print(e)
        await callback_query.answer("Error occurred, Probably using an old message.")


@dp.callback_query_handler(cb_2.filter(act="removePanelConfirmed"))
async def toggle_notify(callback_query: types.CallbackQuery, callback_data):
    user = cmds.LoadUserData(callback_query.from_user.id)
    nickname = user.panels[callback_data['d_1']].nickname
    address = user.panels[callback_data['d_1']].address
    api_key = user.panels[callback_data['d_1']].api_key
    user.RemPanel(address,api_key)
    kb = InlineKeyboardMarkup().add(btn_MainMenu)
    await callback_query.message.edit_text(f"Panel \"{nickname}\" removed from your list.", reply_markup=kb)


@dp.callback_query_handler(cb_7.filter(act="notifSet"))
async def toggle_notify(callback_query: types.CallbackQuery, callback_data):
    try:
        user = cmds.LoadUserData(callback_query.from_user.id)
        kb = InlineKeyboardMarkup()
        userid = callback_query.from_user.id
        panel = callback_data['d_1']
        address = user.panels[panel].address
        api_key = user.panels[panel].api_key
        api_pass = user.panels[panel].api_pass
        panelid = user.panels[panel].panelid
        nickname = user.panels[panel].nickname
        vps = callback_data['d_2']
        method = callback_data['d_3']
        method_val = callback_data['d_4']

        warn = user.panels[panel].vpss[vps].Notification.warn
        sleep = user.panels[panel].vpss[vps].Notification.sleep
        warnsleep = user.panels[panel].vpss[vps].Notification.warnsleep
        notify = user.panels[panel].vpss[vps].Notification.notify
        if method:
            if method == "warnChng":
                user.panels[panel].vpss[vps].Notification.ChangeWarn(method_val)
                warn = user.panels[panel].vpss[vps].Notification.warn
            elif method == "sleepChng":
                user.panels[panel].vpss[vps].Notification.ChangeSleep(method_val)
                sleep = user.panels[panel].vpss[vps].Notification.sleep
            elif method == "warnsleepChng":
                user.panels[panel].vpss[vps].Notification.ChangeWarnSleep(method_val)
                warnsleep = user.panels[panel].vpss[vps].Notification.warnsleep
            elif method == "notifyChange":
                if method_val == "False": method_val = False
                elif method_val == "True": method_val = True
                user.panels[panel].vpss[vps].Notification.ChangeNotify(method_val)
                notify = user.panels[panel].vpss[vps].Notification.notify

        decore_warn = InlineKeyboardButton("⚠️ :", callback_data=".")
        decore_sleep = InlineKeyboardButton("💤 :", callback_data=".")
        decore_warnsleep = InlineKeyboardButton("📵 :", callback_data=".")
        decore_notify = InlineKeyboardButton("🔔 :", callback_data=".")

        btn_warn_1 = InlineKeyboardButton("50GB", callback_data=cb_7.new(act="notifSet", d_1=panel, d_2=vps, d_3="warnChng", d_4="50", d_5=callback_data["d_5"], d_6=callback_data["d_6"]))
        btn_warn_2 = InlineKeyboardButton("100GB", callback_data=cb_7.new(act="notifSet", d_1=panel, d_2=vps, d_3="warnChng", d_4="100", d_5=callback_data["d_5"], d_6=callback_data["d_6"]))
        btn_warn_3 = InlineKeyboardButton("250GB", callback_data=cb_7.new(act="notifSet", d_1=panel, d_2=vps, d_3="warnChng", d_4="250", d_5=callback_data["d_5"], d_6=callback_data["d_6"]))
        btn_warn_4 = InlineKeyboardButton("500GB", callback_data=cb_7.new(act="notifSet", d_1=panel, d_2=vps, d_3="warnChng", d_4="500", d_5=callback_data["d_5"], d_6=callback_data["d_6"]))
        if warn == 50: btn_warn_1.text = "🔘 " + btn_warn_1.text
        elif warn == 100: btn_warn_2.text = "🔘 " + btn_warn_2.text
        elif warn == 250: btn_warn_3.text = "🔘 " + btn_warn_3.text
        elif warn == 500: btn_warn_4.text = "🔘 " + btn_warn_4.text

        btn_sleep_1 = InlineKeyboardButton("5m", callback_data=cb_7.new(act="notifSet", d_1=panel, d_2=vps, d_3="sleepChng", d_4="300", d_5=callback_data["d_5"], d_6=callback_data["d_6"]))
        btn_sleep_2 = InlineKeyboardButton("15m", callback_data=cb_7.new(act="notifSet", d_1=panel, d_2=vps, d_3="sleepChng", d_4="900", d_5=callback_data["d_5"], d_6=callback_data["d_6"]))
        if sleep == 300: btn_sleep_1.text = "🔘 " + btn_sleep_1.text
        elif sleep == 900: btn_sleep_2.text = "🔘 " + btn_sleep_2.text

        btn_warnsleep_1 = InlineKeyboardButton("30m", callback_data=cb_7.new(act="notifSet", d_1=panel, d_2=vps, d_3="warnsleepChng", d_4="1800", d_5=callback_data["d_5"], d_6=callback_data["d_6"]))
        btn_warnsleep_2 = InlineKeyboardButton("1h", callback_data=cb_7.new(act="notifSet", d_1=panel, d_2=vps, d_3="warnsleepChng", d_4="3600", d_5=callback_data["d_5"], d_6=callback_data["d_6"]))
        btn_warnsleep_3 = InlineKeyboardButton("2h", callback_data=cb_7.new(act="notifSet", d_1=panel, d_2=vps, d_3="warnsleepChng", d_4="7200", d_5=callback_data["d_5"], d_6=callback_data["d_6"]))
        if warnsleep == 1800: btn_warnsleep_1.text = "🔘 " + btn_warnsleep_1.text
        elif warnsleep == 3600: btn_warnsleep_2.text = "🔘 " + btn_warnsleep_2.text
        elif warnsleep == 7200: btn_warnsleep_3.text = "🔘 " + btn_warnsleep_3.text

        btn_notify_no = InlineKeyboardButton("Off", callback_data=cb_7.new(act="notifSet", d_1=panel, d_2=vps, d_3="notifyChange", d_4=False, d_5=callback_data["d_5"], d_6=callback_data["d_6"]))
        btn_notify_yes = InlineKeyboardButton("On", callback_data=cb_7.new(act="notifSet", d_1=panel, d_2=vps, d_3="notifyChange", d_4=True, d_5=callback_data["d_5"], d_6=callback_data["d_6"]))
        if notify is False: btn_notify_no.text = "🔘 " + btn_notify_no.text
        elif notify is True: btn_notify_yes.text = "🔘 " + btn_notify_yes.text

        msg = """Here you can modify notification settings for your VPS 🖥:
    
    ⚠️ Warn: Target bandwidth to send a warning if quota goes less than this
    💤 Sleep: Interval between each check if a warning has been sent
    📵 Warn Sleep: Interval between each check if a warn is given"""

        kb.row(decore_warn,btn_warn_1,btn_warn_2,btn_warn_3,btn_warn_4)
        kb.row(decore_sleep,btn_sleep_1,btn_sleep_2)
        kb.row(decore_warnsleep,btn_warnsleep_1,btn_warnsleep_2,btn_warnsleep_3)
        kb.row(decore_notify,btn_notify_no,btn_notify_yes)

        btn_save = InlineKeyboardButton("💾 Save", callback_data=cb_5.new(act="notifSave", d_1=panel, d_2=vps, d_3=callback_data["d_5"], d_4=callback_data["d_6"]))
        kb.add(btn_save).add(btn_MainMenu)
        await callback_query.message.edit_text(msg, reply_markup=kb)
    except Exception as e:
        print(e)
        await callback_query.answer("Error occurred, Probably using an old message.")

@dp.callback_query_handler(cb_5.filter(act="notifSave"))
async def toggle_notify(callback_query: types.CallbackQuery, callback_data):
    try:
        user = cmds.LoadUserData(callback_query.from_user.id)
        kb = InlineKeyboardMarkup()
        btn_Back = InlineKeyboardButton("🔙 Back", callback_data=cb_4.new(act="getVPSList", d_1=callback_data['d_1'],
                                                                         d_2=callback_data["d_3"], d_3=callback_data["d_4"]))
        #Gather information
        userid = callback_query.from_user.id
        panel = callback_data['d_1']
        vps = callback_data['d_2']
        warn = user.panels[panel].vpss[vps].Notification.warn
        sleep = user.panels[panel].vpss[vps].Notification.sleep
        warnsleep = user.panels[panel].vpss[vps].Notification.warnsleep
        notify = user.panels[panel].vpss[vps].Notification.notify
        address = user.panels[panel].address
        api_key = user.panels[panel].api_key
        api_pass = user.panels[panel].api_pass
        panelid = user.panels[panel].panelid
        nickname = user.panels[panel].nickname
        hostname = user.panels[panel].vpss[vps].hostname
        vpsip = list(user.panels[panel].vpss[vps].ips.items())[0][1]

        #Stop the notification task
        CheckOff(userid, address, api_key, api_pass, panelid, vps, nickname)

        #Start the notification task if is enabled
        if notify: CheckOn(userid, address, api_key, api_pass, panelid, vps, nickname, hostname, vpsip, warn, sleep, warnsleep)

        vpslist = user.panels[callback_data['d_1']].VPSList()

        if vpslist[callback_data['d_2']].Notification.notify:
            btn_text = "🔔 Notification Settings"
        else:
            btn_text = "🔕 Notification Settings"

        btn_notify = InlineKeyboardButton(btn_text,
                                          callback_data=cb_7.new(act="notifSet", d_1=callback_data['d_1'],
                                                                 d_2=callback_data['d_2'], d_3=False, d_4=False, d_5=callback_data["d_3"], d_6=callback_data["d_4"]))

        kb = InlineKeyboardMarkup().add(btn_notify).row(btn_Back, btn_MainMenu)
        await callback_query.message.edit_text("✅ Notification Settings Saved!\n"
                                               "=============="
                                               f"{vpslist[callback_data['d_2']].MainInfo()}", reply_markup=kb)
    except Exception as e:
        print(e)
        await callback_query.answer("Error occurred, Probably using an old message.")

if __name__ == '__main__':
    try:
        Startup_Notifications()
    except:
        print("No database found, looks like a fresh start...")
    executor.start_polling(dp, skip_updates=True)