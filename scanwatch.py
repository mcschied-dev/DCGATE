#!/usr/bin/env python3
"""Monitor a folder and upload files to DRACOON
"""
# -*- encoding: utf-8 -*-
import asyncio
import os
import platform
import subprocess
import sys
import time
import filetype

from dracoon import DRACOON, OAuth2ConnectionType
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer

# DRACOON OAuth2 & credentials conf
baseURL = "" # please fill in your _DRACOON_ URL
client_id = ""  # please fill in your client id
client_secret = "" # please fill in your client secret
myusername = "" # please fill in your username - should be write only
mypassword = ""  # please fill in your user password
secret ='' # please fill in your keypair password

# DRACOON target dataroom
target = "/SCANSENC/"

# event pattern
patterns = ["*"]
ignore_patterns = ["*.lock", ".*", "*.git", "*.tmp"]
ignore_directories = True
case_sensitive = True

# observer conf
path = "./toupload"
go_recursively = True

def check_app(appname):
    """Check for native apps
    """
    app_available = True
    print(f"check for 3rd party app dependencies: {appname}")
    try:
        print(subprocess.check_output([appname, "-version","2>&1"]))
    except Exception as e:
        print(e, e.output)
        app_available = False
    if not app_available:
        sys.exit(1)

def get_system_info():
    """Show OS details
    """
    print("\n")
    print("="*40, "SCANWATCH2 System Information", "="*40)
    uname = platform.uname()
    print(f"System: {uname.system}")
    print(f"Node Name: {uname.node}")
    print(f"Release: {uname.release}")
    print(f"Version: {uname.version}")
    print(f"Machine: {uname.machine}")
    print(f"Processor: {uname.processor}")
    print(f"\nFile position: {__file__}\n")
    print(f"Watched folder: {path}\n")
    #check_app("ffmpeg")
    #check_app("convert")

async def upload_files(myfilename, username, password):
    """Upload files to DRACOON
    """
    dracoon = DRACOON(base_url=baseURL, client_id=client_id,
                      client_secret=client_secret)

    connection = await dracoon.connect(OAuth2ConnectionType.password_flow, username, password)
    try:
        connected = await dracoon.test_connection()
        plain_keypair = await dracoon.get_keypair(secret)
        await dracoon.upload(file_path=myfilename, target_path=target, display_progress=True)
        try:
            os.remove(myfilename)
            # print(myfilename)
            # print(os.path.isfile(myfilename))
        except OSError as e:
            print ("Error: %s - %s." % (e.filename, e.strerror))
        await dracoon.logout()
    except Exception as e:
        print("Something went wrong! Abort\n")
        print(e, e.output)
        sys.exit(1)


async def watcher():
    """ Event handler
    """
    my_event_handler = PatternMatchingEventHandler(
        patterns, ignore_patterns, ignore_directories, case_sensitive)

    def on_created(event):
        print(f"{event.src_path} has been created!")
        kind = filetype.guess(event.src_path)
        if kind is None:
            print('Cannot guess file type!')
            return
        print('File extension: %s' % kind.extension)
        print('File MIME type: %s' % kind.mime)

        print(f"Starting upload to {target}")
        asyncio.run(upload_files(event.src_path, myusername, mypassword))

    def on_deleted(event):
        print(f"{event.src_path} deleted!")
        # fill in your ideas

    def on_modified(event):
        print(f"{event.src_path} modified")
        # fill in your ideas

    def on_moved(event):
        print(f"moved {event.src_path} to {event.dest_path}")
        # fill in your ideas

    my_event_handler.on_created = on_created
    my_event_handler.on_modified = on_modified
    my_event_handler.on_moved = on_moved
    my_event_handler.on_deleted = on_deleted

    my_observer = Observer()
    my_observer.schedule(my_event_handler, path, recursive=go_recursively)
    my_observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        my_observer.stop()
        my_observer.join()

if __name__ == "__main__":
    get_system_info()
    asyncio.run(watcher())
