import requests
import json
import os
import time
from PIL import Image
import io
from datetime import datetime

HIST_FILE = 'hist.json'
IMG_DIR = 'img'
CHECK_TIME = 10

BOT_TOKEN = ''
GROUP_ID = ''
PRIORITY_ID = ''
PERSONAL_ID = ''
MY_NAME = ''

API_URL = ""

os.makedirs(IMG_DIR, exist_ok=True)

def load_hist():
    try:
        with open(HIST_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_hist(hist):
    with open(HIST_FILE, 'w') as f:
        json.dump(hist, f, ensure_ascii=False, indent=2)

def dl_img(url, msg_id):
    try:
        r = requests.get(url)
        img = Image.open(io.BytesIO(r.content))
        path = f"{IMG_DIR}/{msg_id}.png"
        img.save(path, "PNG")
        return path
    except:
        return None

def tg_msg(chat_id, text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
    return requests.post(url, json=payload).json()

def tg_photo(chat_id, img_path, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(img_path, 'rb') as photo:
        files = {'photo': photo}
        data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'HTML'}
        return requests.post(url, files=files, data=data).json()

def fwd_msg(chat_id, from_id, msg_id):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/forwardMessage"
    payload = {'chat_id': chat_id, 'from_chat_id': from_id, 'message_id': msg_id}
    return requests.post(url, json=payload).json()

def send_tg(msg):
    try:
        s_id = msg.get('senderId', '')
        name = msg.get('senderName', 'Неизвестный')
        text = msg.get('textMessage', '') or msg.get('caption', '')
        
        if msg.get('type') == 'outgoing':
            name = MY_NAME
        
        if s_id != PRIORITY_ID:
            text = f"<strong>📘 Сообщение от {name}:</strong>\n\n{text}"

        sent_msg = None

        if msg.get('typeMessage') == 'imageMessage':
            path = dl_img(msg.get('downloadUrl'), msg['idMessage'])
            if path and os.path.exists(path):
                res = tg_photo(PERSONAL_ID, path, text)
                if res.get('ok'):
                    sent_msg = res['result']
        elif msg.get('typeMessage') in ['textMessage', 'extendedTextMessage'] and text:
            res = tg_msg(PERSONAL_ID, text)
            if res.get('ok'):
                sent_msg = res['result']

        if sent_msg:
            fwd_res = fwd_msg(GROUP_ID, PERSONAL_ID, sent_msg['message_id'])
            if fwd_res.get('ok'):
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Сообщение {msg['idMessage']} переслано в группу")
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка пересылки: {fwd_res}")
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка отправки: {e}")

def check_msgs():
    hist = load_hist()
    existing = {msg['idMessage'] for msg in hist}
    
    try:
        payload = {"chatId": "YOUR_CHAT_ID"}
        headers = {'Content-Type': 'application/json'}
        
        r = requests.post(API_URL, json=payload, headers=headers)
        
        if r.status_code == 200:
            msgs = sorted(r.json(), key=lambda x: x.get('timestamp', 0))
            filtered_msgs = [
                m for m in msgs 
                if m.get('typeMessage') in ['imageMessage', 'textMessage', 'extendedTextMessage']
            ]
            new = [m for m in filtered_msgs if m['idMessage'] not in existing]
            
            for msg in new:
                send_tg(msg)
                msg['processed_at'] = time.time()
            
            if new:
                save_hist(hist + new)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Обработано {len(new)} новых сообщений")
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка API: {r.status_code}")
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Ошибка: {e}")

def main():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Бот запущен...")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Проверка сообщений каждые {CHECK_TIME} секунд")
    while True:
        try:
            check_msgs()
        except Exception as e:
            print(f"Ошибка в цикле: {e}")
        time.sleep(CHECK_TIME)

if __name__ == "__main__":
    main()