
from aqt import mw, gui_hooks
from aqt.qt import QAction, QDialog, QVBoxLayout, QCheckBox, QPushButton
from aqt.utils import showInfo
import os
import json
from datetime import datetime, timedelta

ADDON_NAME = "new_card_counter"
ADDON_PATH = os.path.join(mw.pm.addonFolder(), ADDON_NAME)
mw.addonManager.setWebExports(__name__, r".+\.css")

CONFIG_PATH = os.path.join(ADDON_PATH, "config.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {"show_today": True, "show_week": True, "show_month": False}
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(config):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f)

def count_new_cards():
    today = datetime.today().date()
    start_week = today - timedelta(days=today.weekday())
    start_month = today.replace(day=1)

    today_count = 0
    week_count = 0
    month_count = 0

    card_ids = mw.col.db.all("SELECT id FROM cards")
    for cid_tuple in card_ids:
        cid = cid_tuple[0]
        card = mw.col.get_card(cid)
        created_ts = card.note().id / 1000
        created = datetime.fromtimestamp(created_ts).date()

        if created == today:
            today_count += 1
        if created >= start_week:
            week_count += 1
        if created >= start_month:
            month_count += 1

    return today_count, week_count, month_count

def inject_card_stats(deck_browser, content):
    config = load_config()
    today_count, week_count, month_count = count_new_cards()

    lines = []
    if config["show_today"]:
        lines.append(f"<div style='margin: 4px 0; font-size: 16px; color: #333;'>📅 Total new cards today: <b>{today_count}</b></div>")
    if config["show_week"]:
        lines.append(f"<div style='margin: 4px 0; font-size: 16px; color: #333;'>📈 Total new cards this week: <b>{week_count}</b></div>")
    if config["show_month"]:
        lines.append(f"<div style='margin: 4px 0; font-size: 16px; color: #333;'>📊 Total new cards this month: <b>{month_count}</b></div>")

#    lines = []
#    if config["show_today"]:
#        lines.append(f"<span style='class='counter-line''>Total new cards today: <b>{today_count}</b></span>")
#    if config["show_week"]:
#        lines.append(f"<span style='class='counter-line';'>Total new cards this week: <b>{week_count}</b></span>")
#    if config["show_month"]:
#        lines.append(f"<span style='class='counter-line';'>Total new cards this month: <b>{month_count}</b></span>")

    if lines:
        box = "".join(lines) #bỏ box = "<br>".join(lines)
        content.stats += f"""
        <br>
        <div class="new-card-counter"> 
            {box}
        </div>
        """

gui_hooks.deck_browser_will_render_content.append(inject_card_stats)

def on_config_dialog():
    config = load_config()

    dlg = QDialog(mw)
    dlg.setWindowTitle("New Card Counter")
    layout = QVBoxLayout()

    cb_today = QCheckBox("📅Total new cards today")
    cb_today.setChecked(config["show_today"])
    layout.addWidget(cb_today)

    cb_week = QCheckBox("📈Total new cards this week")
    cb_week.setChecked(config["show_week"])
    layout.addWidget(cb_week)

    cb_month = QCheckBox("📊Total new cards this month")
    cb_month.setChecked(config["show_month"])
    layout.addWidget(cb_month)

    save_btn = QPushButton("Save")
    def on_save():
        new_config = {
            "show_today": cb_today.isChecked(),
            "show_week": cb_week.isChecked(),
            "show_month": cb_month.isChecked(),
        }
        save_config(new_config)
        deck_browser = mw.deckBrowser
        deck_browser.refresh()
        showInfo("Settings saved and applied!")
        dlg.accept()
    save_btn.clicked.connect(on_save)
    layout.addWidget(save_btn)

    dlg.setLayout(layout)
    dlg.exec()

def on_main_window_ready():
    action = QAction("📊 New Card Counter", mw)
    action.triggered.connect(on_config_dialog)
    mw.form.menuTools.addAction(action)

gui_hooks.main_window_did_init.append(on_main_window_ready)
