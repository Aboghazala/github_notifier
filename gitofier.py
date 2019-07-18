#!/usr/bin/env python
import os, sys
import pycurl
import queue
import time

import certifi
from io import BytesIO
import json
# import PySimpleGUIWx as sg
import PySimpleGUIQt as sg
import webbrowser

sg.ChangeLookAndFeel('Reds')
sg.SetOptions(font='any 12')
version = 1.0

path = os.path.abspath(sys.argv[0])
path = os.path.dirname(path)
os.chdir(path)

icon1 = os.path.join(path, 'icons', "cat1.png")
icon2 = os.path.join(path, 'icons', "cat2.png")

user = 'Aboghazala'

# load your authorization token from a file
with open('token.txt') as f:
    password = f.read().strip()

base_url = 'https://api.github.com'
notif_url = "/notifications"
test_url = '/users/Aboghazala/events'

notifications = ''
notif_num = 0

mainWindow_q = queue.Queue()


def get(url):
    custom_header = ["Time-Zone: Africa/Cairo"]  # "If-Modified-Since: Thu, 05 Jul 2012 15:31:30 GMT",
    if url.startswith(base_url):
        pass
    else:
        url = base_url + url

    buffer = BytesIO()
    headerBuffer = BytesIO()

    c = pycurl.Curl()
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.USERPWD, f"{user}:{password}")
    c.setopt(pycurl.USERAGENT, "curl")
    c.setopt(pycurl.HTTPHEADER, custom_header)
    c.setopt(pycurl.MAXREDIRS, 50)
    c.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_2TLS)
    c.setopt(pycurl.TCP_KEEPALIVE, 1)
    c.setopt(pycurl.WRITEHEADER, headerBuffer)

    c.setopt(c.CAINFO, certifi.where())
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    response = c.getinfo(pycurl.RESPONSE_CODE)
    c.close()

    header = headerBuffer.getvalue().decode('utf-8')
    body = buffer.getvalue()
    body = json.loads(body)

    buffer = ''
    num = len(body)

    for item in body:
        if type(item) == dict:
            out = f"{item.get('repository', {}).get('name')}\n{item.get('subject', {}).get('title')}\n{'-' * 50}\n\n"
            buffer += out
        else:
            buffer = header

    print(buffer)
    return buffer, num


def mark_all_as_read(url):
    custom_header = ["Time-Zone: Africa/Cairo"]
    if url.startswith(base_url):
        pass
    else:
        url = base_url + url

    buffer = BytesIO()
    headerBuffer = BytesIO()

    c = pycurl.Curl()
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.USERPWD, f"{user}:{password}")
    c.setopt(pycurl.USERAGENT, "curl")
    c.setopt(pycurl.HTTPHEADER, custom_header)
    c.setopt(pycurl.MAXREDIRS, 50)
    c.setopt(pycurl.HTTP_VERSION, pycurl.CURL_HTTP_VERSION_2TLS)
    c.setopt(pycurl.TCP_KEEPALIVE, 1)
    c.setopt(pycurl.WRITEHEADER, headerBuffer)

    c.setopt(pycurl.CUSTOMREQUEST, "PUT")

    c.setopt(c.CAINFO, certifi.where())
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    response = c.getinfo(pycurl.RESPONSE_CODE)
    c.close()

    header = headerBuffer.getvalue().decode('utf-8')
    body = buffer.getvalue().decode('utf-8')

    print('send PUT request, response:', response, '\n')
    print(header, '\n')
    print(body)


class SysTray:
    def __init__(self):
        self.tray = None
        self.exit_app = False
        self.icon = icon1
        self.setup()

    def setup(self):
        menu_def = ['BLANK', ['Show', 'Setting', '---', 'Exit']]
        self.tray = sg.SystemTray(menu=menu_def, filename=self.icon)
        self.exit_app = False

    def run(self):
        menu_item = self.tray.Read(timeout=10)
        if menu_item == 'Exit':
            self.tray.Hide()
            self.exit_app = True

        elif menu_item in ('Show', '__ACTIVATED__'):
            mainWindow_q.put('restart')

        elif menu_item == 'Setting':
            pass

    def animate(self):
        if notif_num > 0:
            icons = [icon1, icon2]
            self.icon = icons[0] if icons[0] != self.icon else icons[1]
            self.tray.Update(filename=self.icon, tooltip=f'{notif_num} notifications')
        else:
            if self.icon != icon1:
                self.tray.Update(filename=self.icon, tooltip=f'{notif_num} notifications')


class MainWindow:
    def __init__(self):
        self.isActive = True
        self.window = None
        self.setup()
        self.notif = ''

    def setup(self):
        window_layout = [[sg.Text(f'GitHub Notifications: {notif_num}', key='notifications_num'),
                          sg.Button('info', size=(5, 1))],
                         [sg.T('')],
                         [sg.Multiline(notifications, size=(500, 200), key='output')],
                         [sg.Text('')],
                         [sg.Ok(size=(10, 1)), sg.Button('To GitHub', size=(10, 1), key='open_url'),
                          sg.Button('Mark all as read', size=(20, 1), key='read_all'), ]]
        self.window = sg.Window(f'GitHub Notifier ver.{version}', window_layout, icon=icon1)
        self.window.Finalize()

    def restart(self):
        self.window.Close()
        self.setup()
        self.isActive = True
        self.run()

    def close(self):
        self.window.Close()
        self.isActive = False

    def run(self):
        if mainWindow_q.qsize():
            temp = mainWindow_q.get()
            if temp == 'exit':
                self.close()
            elif temp == 'restart':
                self.restart()  # restart window

        if self.isActive:

            event, values = self.window.Read(timeout=10)
            if event in (None, 'Ok'):
                self.close()

            elif event == 'info':
                sg.Popup('Github notifier \nby: Mahmoud Elshahat\nager', non_blocking=True)

            elif event == 'open_url':
                webbrowser.open('https://github.com/notifications')

            elif event == 'read_all':
                mark_all_as_read(notif_url)
                self.update_notifications()

    def update_notifications(self):
        if self.isActive and notifications != self.notif:
            self.window.Element('output').Update(notifications)
            self.window.Element('notifications_num').Update(f'Github notifications: {notif_num} unread')
            self.notif = notifications


def cleanup():
    """send messages to running threads to quit and close any open resources"""
    mainWindow_q.put('exit')


def main():
    global notifications, notif_num
    timer = 0
    timer2 = 0

    # make gui windows
    systray_menu = SysTray()
    mainWindow = MainWindow()

    # main loop
    while True:
        if time.time() - timer >= 60:
            notifications, notif_num = get(notif_url)
            mainWindow.update_notifications()
            timer = time.time()

        # animate systray icon if there is unread notiications received
        if time.time() - timer2 >= 1:
            systray_menu.animate()
            timer2 = time.time()

        if systray_menu.exit_app:
            cleanup()
            break

        systray_menu.run()
        mainWindow.run()


if __name__ == '__main__':
    main()
