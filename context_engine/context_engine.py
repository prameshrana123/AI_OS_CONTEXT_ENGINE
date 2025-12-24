import win32gui
import win32process
import psutil
import time
import json
from pynput import keyboard
from pynput import mouse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from google.genai import Client
import pyperclip

client=Client(api_key="AIzaSyAf7E98Div8-054dLhscENV70TlopMCtSo")

def get_active_window_info():
    hnwd = win32gui.GetForegroundWindow()
    title = win32gui.GetWindowText(hnwd)
    _, pid = win32process.GetWindowThreadProcessId(hnwd)
    process= psutil.Process(pid)

    try:
        name=process.name()
        exe=process.exe()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        name="N/A"
        exe="N/A"

    return {
        "timestamp": time.time(),
        "hnwd": hnwd,
        "title": title,
        "process_name": name,
        "executable": exe,
        "pid": pid
    }


def get_system_state():
    try:
        vm = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        try:
            battery = psutil.sensors_battery()
            battery_percent = battery.percent if battery else "N/A"
        except AttributeError:
            battery_percent = "N/A"
        return {
            "cpu_percent": cpu,
            "memory_total": vm.total,
            "memory_available": vm.available,
            "memory_used": vm.used,
            "memory_percent": vm.percent,
            "battery_percent": battery_percent
        }
    except Exception as e:
        return {"error": str(e)}        
    
def get_process_snapshot():
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'exe', 'cpu_percent', 'memory_info']):
        try:
            proc_info = proc.info
            processes.append({
                "pid": proc_info['pid'],
                "name": proc_info['name'],
                "executable": proc_info['exe'],
                "cpu_percent": proc_info['cpu_percent'],
                "memory_rss": proc_info['memory_info'].rss,
                "memory_vms": proc_info['memory_info'].vms
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

recent_fsm_events = []

class MyEventHandler(FileSystemEventHandler):
    def on_modified(self, event):
        recent_fsm_events.append({
            "event_type": "modified",
            "src_path": event.src_path,
            "timestamp": time.time()
        })

    def on_created(self, event):
        recent_fsm_events.append({
            "event_type": "created",
            "src_path": event.src_path,
            "timestamp": time.time()
        })

    def on_deleted(self, event):
        recent_fsm_events.append({
            "event_type": "deleted",
            "src_path": event.src_path,
            "timestamp": time.time()
        })
def start_fsm_observer(path='.'):
    event_handler = MyEventHandler()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.daemon = True
    observer.start()
    return observer

def get_recent_fsm_events():
    global recent_fsm_events
    events = recent_fsm_events.copy()
    recent_fsm_events = []
    return events

last_clipboard_content = ""
def get_clipboard_state():
    global last_clipboard_content
    try:
        current_content = pyperclip.paste()
        if current_content != last_clipboard_content:
            last_clipboard_content = current_content
            return {
                "changed": True,
                "content": current_content
            }
        else:
            return {
                "changed": False,
                "content": current_content
            }
    except Exception as e:
        return {"error": str(e)}
    
def get_network_state():
    try:
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }
    except Exception as e:
        return {"error": str(e)}
    

def collect_basic_context():
    aw = get_active_window_info()
    return {
        "process_name": aw["process_name"],
        "window_title": aw["title"],
        "hnwd": aw["hnwd"],
        "pid": aw["pid"]
    }


def collect_heavy_context():
    process_snapshot = get_process_snapshot()
    fsm_events = get_recent_fsm_events()
    clipboard_state = get_clipboard_state()
    network_state = get_network_state()

    return {
        "process_snapshot": process_snapshot,
        "fsm_events": fsm_events,
        "clipboard_state": clipboard_state,
        "network_state": network_state
    }
