import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
import webbrowser
import threading
import random
import string

# ===================== Resource Path ===================== #

def resource_path(relative_path):
    """Get correct path whether running normally or from PyInstaller EXE."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

FFMPEG_DIR = resource_path("ffmpeg")
FFMPEG = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
FFPROBE = os.path.join(FFMPEG_DIR, "ffprobe.exe")

# ===================== FFmpeg Check ===================== #

def check_ffmpeg():
    if not os.path.exists(FFMPEG):
        messagebox.showerror("Error", "FFmpeg not found inside bundled folder!")
        sys.exit(1)
    return FFMPEG

# ===================== Auto-Generate Mount Name ===================== #

def random_mount_name():
    r = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"stream_{r}.webm"

# ===================== RTSP Detection ===================== #

def detect_rtsp_url(ffmpeg_path, user, password, ip):
    common_paths = [
        "/Streaming/Channels/101",
        "/Streaming/Channels/102",
        "/h264Preview_01_main",
        "/h264Preview_01_sub",
        "/live/main",
        "/live/sub",
        "/cam/realmonitor?channel=1&subtype=0",
        "/cam/realmonitor?channel=1&subtype=1",
        "/axis-media/media.amp",
        "/live.sdp",
        "/stream1",
        "/videoMain",
        "/videoSub",
    ]

    for path in common_paths:
        rtsp_url = f"rtsp://{user}:{password}@{ip}:554{path}"
        print(f"Testing: {rtsp_url}")

        cmd = [ffmpeg_path, "-rtsp_transport", "tcp", "-i", rtsp_url, "-t", "3", "-f", "null", "-"]

        if sys.platform.startswith("linux"):
            cmd.insert(0, "wine")

        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
            out = result.stdout + result.stderr

            if b"Stream" in out or b"Video" in out:
                print("RTSP found:", rtsp_url)
                return rtsp_url

        except:
            pass

    messagebox.showerror("RTSP Error", "Could not detect RTSP path. Wrong IP or credentials.")
    return None

# ===================== Stream Start ===================== #

def run_ffmpeg(ffmpeg_path, rtsp_url, stream_name):

    icecast_url = f"icecast://source:hackme@portal.thabir.ai:80/{stream_name}"
    viewer_url = f"http://portal.thabir.ai/{stream_name}"

    cmd = [
        ffmpeg_path,
        "-rtsp_transport", "tcp",
        "-i", rtsp_url,
        "-c:v", "libvpx",
        "-b:v", "1000k",
        "-c:a", "libvorbis",
        "-b:a", "128k",
        "-f", "webm",
        icecast_url
    ]

    if sys.platform.startswith("linux"):
        cmd.insert(0, "wine")

    subprocess.Popen(cmd)
    webbrowser.open(viewer_url)
    url_var.set(viewer_url)
    messagebox.showinfo("Success", f"Stream started!\n\n{viewer_url}")

# ===================== GUI ===================== #

def start_stream():
    ip = ip_entry.get().strip()
    user = username_entry.get().strip()
    password = password_entry.get().strip()

    if not all([ip, user, password]):
        messagebox.showwarning("Missing Info", "Enter all fields!")
        return

    ffmpeg_path = check_ffmpeg()

    stream_name = random_mount_name()

    def task():
        rtsp_url = detect_rtsp_url(ffmpeg_path, user, password, ip)
        if rtsp_url:
            run_ffmpeg(ffmpeg_path, rtsp_url, stream_name)

    threading.Thread(target=task, daemon=True).start()

# ===================== GUI Setup ===================== #

root = tk.Tk()
root.title("CCTV Streamer")
root.geometry("420x400")
root.configure(bg="#0f0f0f")

font_title = ("Arial", 14, "bold")
font_label = ("Arial", 10)

tk.Label(root, text="CCTV Live Streamer", fg="#e8e0f5", bg="#0f0f0f", font=font_title).pack(pady=15)

tk.Label(root, text="Camera IP:", fg="white", bg="#0f0f0f", font=font_label).pack()
ip_entry = tk.Entry(root, width=40)
ip_entry.pack()

tk.Label(root, text="Username:", fg="white", bg="#0f0f0f", font=font_label).pack()
username_entry = tk.Entry(root, width=40)
username_entry.pack()

tk.Label(root, text="Password:", fg="white", bg="#0f0f0f", font=font_label).pack()
password_entry = tk.Entry(root, width=40, show="*")
password_entry.pack()

tk.Button(root, text="Start Stream", command=start_stream, bg="#e3d2ff", fg="grey", width=20, height=2).pack(pady=20)

url_var = tk.StringVar()
tk.Entry(root, textvariable=url_var, width=45, state="readonly", justify="center").pack()

root.mainloop()
