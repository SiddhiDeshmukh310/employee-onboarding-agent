import schedule
import time
import subprocess
import sys


def check_inbox():
    print("Checking inbox...")
    subprocess.run([sys.executable, "process_inbox.py"])


schedule.every(1).minutes.do(check_inbox)

print("Email listener started...")

while True:
    schedule.run_pending()
    time.sleep(5)