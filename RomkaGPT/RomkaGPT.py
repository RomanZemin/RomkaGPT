# -*- coding: cp1251 -*-

from multiprocessing import context
import os
import openai
import telebot
import threading
import requests
import base64
import json
import shutil
import time
from telebot import types
from datetime import datetime
import subprocess
import pyautogui
import pyuac


#Constants
CHECK_UPDATE_TIME = 600 #10 �����

openai.api_key = os.getenv("OPENAI_API_KEY")
bot = telebot.TeleBot(os.getenv("TELEBOT_API_KEY"))
user_contexts = {}

@bot.message_handler(func=lambda _: True)

def handle_message(message):
    global user_contexts

    user_id = message.from_user.id
    if user_id not in user_contexts:
        user_contexts[user_id] = ""

    context = user_contexts[user_id]

    print(message.from_user.username+': '+message.text)

    if not os.path.exists(f"Database/{message.from_user.username}"): 
        os.makedirs(f"Database/{message.from_user.username}")
    date = datetime.now().strftime("%d-%m-%Y")
    filename = f"Database/{message.from_user.username}/{date}.txt"
    with open(filename, "a") as file:
        try:
            file.write('\n' + message.from_user.username+': '+message.text + '\n')
            pass
        except :
            file.write('\n' + message.from_user.username+': '+ "Some Emotions!" + '\n')
            pass


    markup=types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1=types.KeyboardButton("��������")
    markup.add(item1)

    if ((message.text=="��������" or message.text=="����������" or message.text=="����������" or message.text=="��������") and context != ""):
        info = get_response(f"�������� �������:{context}")
    else:
        info = get_response(message.text)
        user_contexts[user_id] = info

    print('Bot_Answer: ' + info)
    with open(filename, "a") as file:
        file.write('Bot_Answer: ' + info)

    send_msg(message.from_user.id, info)

def check_for_updates():
    while True:
        event = threading.Event()
        event.wait(CHECK_UPDATE_TIME)
        print("Looking for updates...")
        current_version = get_current_version()
        print("Your Version: " + current_version)
        new_version = get_new_version()
        if current_version != new_version:
            print(f'Congratulations! Now available new version: {new_version}!')
            download_update()
            restart_application()
        else:
            continue

def get_current_version():
    with open('cur_version.txt', 'r') as f:
        return f.read()
    
def get_new_version():
    current_version = get_current_version()

    response = requests.get('https://api.github.com/repos/RomanZemin/RomkaGPT/contents/RomkaGPT/cur_version.txt')
    if response.status_code == requests.codes.ok:
        jsonResponse = response.json()  # the response is a JSON
        #the JSON is encoded in base 64, hence decode it
        content = base64.b64decode(jsonResponse['content'])
        #convert the byte stream to string
        jsonString = content.decode('utf-8')
        finalJson = json.loads(jsonString)  
        version = str(content).replace("b\'","").replace("\\n\'","").replace('\'',"")
    else:
        version = current_version
        print('Can\'t get new version')
    print(f'Latest version: {version}')
    return version

def download_update():
    print("Updating...")
    version = get_new_version()
    url = 'https://github.com/RomanZemin/RomkaGPT/raw/master/RomkaGPT/dist/RomkaGPT.exe'
    r = requests.get(url, stream=True)
    if r.status_code == 200:
        print("Downloading...")
        with open(f'RomkaGPT_{version}.exe', 'wb') as f: #��������� exe ���� ��� ������, ��������� �������� ����� "wb"
            r.raw.decode_content = True
            try:
                shutil.copyfileobj(r.raw, f) #��������� ���������� ������ � ����
            except PermissionError:
                print("Error with downloading!")
    else:
        print("Error with downloading!")

def restart_application():
    print("Restarting...")
    version = get_new_version()
    current_version = get_current_version()
    with open('cur_version.txt', 'r+') as f:
        f.write(version)
    os.system(f'start RomkaGPT_{version}.exe')
    subprocess.run(f'taskkill /f /im RomkaGPT_{current_version}.exe')
    print('open')

def send_msg(id, info):
    if len(info) > 4096:
       for x in range(0, len(info), 4096):
           bot.send_message(chat_id=id, text=info[x:x+4096])
    else:
        bot.send_message(chat_id=id, text=info)

def get_response(prompt_text)-> str:
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"{prompt_text}",
        temperature=0.9,
        max_tokens=500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0.6,
        #stop=["You:"]
    )   
    return response['choices'][0]['text'].lstrip('\n')

if __name__ == '__main__':

    timer2 = threading.Timer(1.0, check_for_updates)
    timer2.start()
    timer2 = threading.Timer(1.0, bot.infinity_polling)
    timer2.start()
