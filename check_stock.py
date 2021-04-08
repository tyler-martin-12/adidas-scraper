import httplib2
import os
import oauth2client
from oauth2client import client, tools, file
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from googleapiclient.discovery import build
import mimetypes
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
import requests
from datetime import datetime
import argparse
import json
import time

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

SCOPES = 'https://www.googleapis.com/auth/gmail.send'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Gmail API Python Send Email'


def get_credentials():
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir, 'gmail-python-email-send.json')
    store = oauth2client.file.Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials


def send_message(sender, to, subject, msgHtml, msgPlain, attachmentFile=None):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = build('gmail', 'v1', http=http)
    message = html_message(sender, to, subject, msgHtml, msgPlain)
    result = send_message_internal(service, 'me', message)
    return result


def send_message_internal(service, user_id, message):
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        print('Message Id: %s' % message['id'])
        return message
    except apiclient.errors.HttpError as error:
        print('An error occurred: %s' % error)
        return 'Error'
    return 'OK'


def html_message(sender, to, subject, msgHtml, msgPlain):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = to
    msg.attach(MIMEText(msgHtml, 'html'))
    return {'raw': base64.urlsafe_b64encode(msg.as_string().encode()).decode()}


def initialize_inventory(color_list):
    if os.path.exists('inventory.json'):
        inventory = read_inventory()
        for color in color_list:
            if color not in inventory:
                inventory[color] = []
    else:
        inventory = {color: [] for color in color_list}
    dump_inventory(inventory)


def dump_inventory(inventory):
    inventory = {key: list(set(item)) for key, item in inventory.items()}
    with open('inventory.json', 'w') as f:
        json.dump(inventory, f, indent=4)


def read_inventory():
    with open('inventory.json', 'r') as f:
        inventory = json.load(f)
    inventory = {key: set(item) for key, item in inventory.items()}
    return inventory


def get_new_items(color_list):
    items = {}
    for color in color_list:
        items[color] = get_sizes(color)
    return items


def update_inventory(inventory, new_items):
    email_list = []
    for color, items in new_items.items():
        ids_to_send = [i for i in items if i not in inventory[color]]
        for item_id in ids_to_send:
            email_list.append((color, item_id))
        inventory[color] = items
    return inventory, email_list


def make_email(email_list):
    to = 'tyler.a.martin12@gmail.com'
    sender = 'tyler.a.martin12@gmail.com'
    subject = 'Adidas'
    msgHtml = 'Adidas summary: <br/> <br/>'
    for color, item in email_list:
        msgHtml += f'Size {item} of color {color} <br/> <br/>'
    msgPlain = ''
    send_message(sender, to, subject, msgHtml, msgPlain)
    return msgHtml


def get_unix_time():
    now = datetime.now()
    unix = int(time.mktime(now.timetuple()))
    return unix


def unix_time_to_str(unix):
    ts = datetime.fromtimestamp(unix)
    fmt = '%Y%m%d %H:%M'
    ts_str = ts.strftime(fmt)
    return ts_str


def get_soup(url):
    chrome_path = '/Users/tyler/Documents/from_air/Programming/chromedriver'
    chrome_options = Options()
    # chrome_options.add_argument('--headless')
    driver = webdriver.Chrome(chrome_path, options=chrome_options)
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    driver.quit()
    return soup


def get_sizes(color):
    color2ext = {'white': 'FW4455', 'black': 'FW4459', 'yellow': 'FY4485', 'navy': 'FY4486'}

    ext = color2ext[color]
    base = 'https://www.adidas.co.uk/the-velosamba-cycling-shoes'
    url = f'{base}/{ext}.html'

    soup = get_soup(url)
    sizes = soup.find_all(class_='size___TqqSo')
    sizes_text = [s.text for s in sizes]
    return sizes_text


def main():
    color_list = ['white', 'black', 'yellow', 'navy']
    initialize_inventory(color_list)
    inventory = read_inventory()
    new_items = get_new_items(color_list)
    inventory, email_list = update_inventory(inventory, new_items)
    if len(email_list) > 0:
        msg = make_email(email_list)
    dump_inventory(inventory)
    now = get_unix_time()
    now_str = unix_time_to_str(now)
    print(f'{now_str}: {len(email_list)} items added')


if __name__ == '__main__':
    main()
