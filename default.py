import json
import os
import time
from os.path import join
from textwrap import dedent
from urllib.request import urlretrieve as download
import requests
import telepot
from clarifai.rest import ClarifaiApp
from simpleeval import simple_eval

# create directory structure
for x in ["SMALL", "MEDIUM", "BIG", "LARGE", "EXTRA LARGE"]:
    os.makedirs(x, exist_ok=True)
    
# Make sure to load environment variables in configuration.
CLARIFY_API_KEY = os.environ['CLARIFY_API_KEY']
BOT_TOKEN = os.environ['BOT_TOKEN']

app = ClarifaiApp(api_key=CLARIFY_API_KEY)
model = app.public_models.general_model

# sys.stdout = open('output.log', 'a')
# sys.stderr = open('error.log', 'a')

FILE_ID_URL = "https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
DOWNLOAD_FILE_URL = "https://api.telegram.org/file/bot{bot_token}/{file_path}"
small, medium, big, large = 9999, 99999, 999999, 9999999

bot = telepot.Bot(BOT_TOKEN)


# All the command and chat handlers
def start(chat_id):
    bot.sendMessage(chat_id, text="Hi! I am a Telegram Bot\n"
                                  "I am capable of doing some serious calculations!!")


def unknown(chat_id, custom_message="Sorry, I didn't understand that command."):
    bot.sendMessage(chat_id, text=custom_message)


def help(chat_id):
    bot.sendMessage(chat_id, text=dedent("""They call me a Telegram Bot. I can help you do stuff."""))


def settings(chat_id):
    bot.sendMessage(chat_id, text="I cannot be configured via any settings yet. Check back soon!")


def calc(chat_id, text):
    if text == "143":
        bot.sendMessage(chat_id, text="Vikram loves Priyanka!")
    else:
        bot.sendMessage(chat_id, text=str(simple_eval(text)))


def process(chat_id, file_list, folder_name, analyze):
    # Ignore if list is empty
    if not file_list:
        return
    files = []
    for file_id in file_list:
        try:
            resp = requests.get(FILE_ID_URL.format(bot_token=BOT_TOKEN, file_id=file_id))
            js = resp.json()
            file_path = js['result']['file_path']
            download_url = DOWNLOAD_FILE_URL.format(bot_token=BOT_TOKEN, file_path=file_path)
            extension = '.' + file_path.split('.')[-1]
            file_path = join(folder_name, file_id + extension)
            download(download_url, filename=file_path)
            files.append(file_path)
        except:
            print(folder_name, file_id, "Could not be downloaded")

    # At least analyze one
    if analyze:
        for file_loc in files:
            try:
                if analyze:
                    response = model.predict_by_filename(file_loc)
                    for c in response['outputs'][0]['data']['concepts'][:5]:
                        bot.sendMessage(chat_id, text=f"{c['name'].title()} : Confidence {(c['value'] * 100):.3f}%")
                return True
            except:
                print(folder_name, file_loc, "Could not be processed")
        return False
    else:
        return True


def handle(msg):
    """
    Function to handle incoming messages and determine what the user is asking for
    :param msg:
    :return:
    """
    flavor = telepot.flavor(msg)
    # normal message
    if flavor in ["chat", "normal"]:
        content_type, chat_type, chat_id = telepot.glance(msg)
        print("Normal Message:", content_type, chat_type, chat_id)
        if content_type.lower().strip() == 'text':
            command = msg["text"].lower()
            if command in ["/start", "start"]:
                start(chat_id)
            elif command in ["/help", 'help']:
                help(chat_id)
            elif command in ["/settings", "settings"]:
                settings(chat_id)
            elif command in ["author", "authors"]:
                bot.sendMessage(chat_id, text="Hi Everyone!\n\nMy name is Vikram  Bankar\n"
                                              "I created this bot as an experiment\n"
                                              "This is intended for testing and not a commercial application\n"
                                              "If you liked this message me @ https://t.me/viksto\n"
                                              "I will be very glad!")
            else:
                try:
                    calc(chat_id, command)
                except:
                    unknown(chat_id)
        elif content_type.lower().strip() == 'photo':
            try:
                small_pics, medium_pics, big_pics, large_pics, extra_large = [], [], [], [], []
                for item_ in msg['photo']:
                    item = item_['file_id']
                    dim = item_['width'] * item_['height']
                    if dim <= small:
                        small_pics.append(item)
                    elif dim <= medium:
                        medium_pics.append(item)
                    elif dim <= big:
                        big_pics.append(item)
                    elif dim <= large:
                        large_pics.append(item)
                    else:
                        extra_large.append(item)

                analyze = True
                x = [extra_large, large_pics, big_pics, medium_pics, small_pics]
                y = ['EXTRA LARGE', 'LARGE', 'BIG', 'MEDIUM', 'SMALL']
                for lists, folders in zip(x, y):
                    resp = process(chat_id, lists, folders, analyze)
                    if analyze and resp:
                        analyze = False
                bot.sendMessage(chat_id, text="Thanks for the picture!")
            except:
                unknown(chat_id, "Could not process that picture")
        return ("Message sent")
    else:
        raise telepot.exception.BadFlavor(msg)


# AWS LAMBDA HANDLER, NOT FOR LOCAL DEV
# def my_handler(event, context):
#     print("Received event: " + json.dumps(event, indent=2))
#     handle(event["message"])


# FOR LOCAL DEV
def my_handler(event):
    print("Received event: " + json.dumps(event, indent=2))
    handle(event)


bot.message_loop(my_handler)

print("Listening ...")

# Keep the program running.
while 1:
    time.sleep(10)
