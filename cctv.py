import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
import webbrowser
import threading
import random
import string

# ============================================================
#  Resource Path for PyInstaller one-file EXE
# ============================================================

def resource_path(relative_path):
    """
    This returns the absolute path to bundled files when packaged
    using PyInstaller --onefile.
    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# ============================================================
#  Bundled FFmpeg paths
# ============================================================

FFMPEG = resource_path("ffmpeg/ffmpeg.exe")
FFPROBE = resource_path("ffmpeg/ffprobe.exe")
FFPLAY = resource_path("ffmpeg/ffplay.exe")


# ============================================================
#  FFmpeg Check
# ============================================================

def check_ffmpeg():
    if not os.path.exists(FFMPEG):
        messagebox.showerror("FFmpeg Missing",
                             "FFmpeg is missing inside the EXE bundle.\n"
                             "Please re-download the application.")
        sys.exit(1)
    return FFMPEG


# ============================================================
#  Random Mount Name
# ============================================================

def random_mount_name():
    """Generate a random unique stream mount name."""
    r = ''.join(random.choices(string.ascii_lowercase + string.digits, k=7))
    return f"stream_{r}.webm"


# ============================================================
#  Detect RTSP Camera Path Automatically
# ============================================================

def detect_rtsp_url(ffmpeg_path, user, password, ip):
    common_paths = [
        "/Streaming/Channels/101",
        "/Streaming/Channels/102",
        "/live/main",
        "/live/sub",
        "/h264Preview_01_main",
        "/h264Preview_01_sub",
        "/cam/realmonitor?channel=1&subtype=0",
        "/cam/realmonitor?channel=1&subtype=1",
        "/axis-media/media.amp",
        "/live.sdp",
        "/stream1",
        "/videoMain",
        "/videoSub"
    ]

    for path in common_paths:
        rtsp_url = f"rtsp://{user}:{password}@{ip}:554{path}"
        print("Testing:", rtsp_url)

        cmd = [
            ffmpeg_path,
            "-rtsp_transport", "tcp",
            "-i", rtsp_url,
            "-t", "3",
            "-f", "null", "-"
        ]

        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=5)

            out = result.stdout + result.stderr

            if b"Stream" in out or b"Video" in out:
                print("RTSP FOUND:", rtsp_url)
                return rtsp_url

        except Exception:
            pass

    messagebox.showerror("RTSP Error",
                         "Camera RTSP path could not be detected.\n"
                         "Check your IP, username, or password.")
    return None


# ============================================================
#  Start Streaming to Icecast
# ============================================================

def run_ffmpeg(ffmpeg_path, rtsp_url, mount_name):

    icecast_url = f"icecast://source:hackme@portal.thabir.ai:80/{mount_name}"
    viewer_url = f"http://portal.thabir.ai/{mount_name}"

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

    subprocess.Popen(cmd)
    webbrowser.open(viewer_url)

    url_var.set(viewer_url)
    messagebox.showinfo("Success", f"Stream started!\n\n{viewer_url}")


# ============================================================
#  Start Button Handler
# ============================================================

def start_stream():
    ip = ip_entry.get().strip()
    user = username_entry.get().strip()
    password = password_entry.get().strip()

    if not ip or not user or not password:
        messagebox.showwarning("Missing Fields", "Please enter all fields.")
        return

    ffmpeg_path = check_ffmpeg()
    mount_name = random_mount_name()

    def worker():
        rtsp_url = detect_rtsp_url(ffmpeg_path, user, password, ip)
        if rtsp_url:
            run_ffmpeg(ffmpeg_path, rtsp_url, mount_name)

    threading.Thread(target=worker, daemon=True).start()


# ============================================================
#  GUI Setup
# ============================================================

root = tk.Tk()
root.title("CCTV Streamer")
root.geometry("420x420")
root.configure(bg="#0f0f0f")

font_title = ("Arial", 14, "bold")
font_label = ("Arial", 10)

tk.Label(root, text="CCTV Live Streamer", fg="#e8e0f5",
         bg="#0f0f0f", font=font_title).pack(pady=15)

tk.Label(root, text="Camera IP:", fg="white",
         bg="#0f0f0f", font=font_label).pack()
ip_entry = tk.Entry(root, width=40)
ip_entry.pack()

tk.Label(root, text="Username:", fg="white",
         bg="#0f0f0f", font=font_label).pack()
username_entry = tk.Entry(root, width=40)
username_entry.pack()

tk.Label(root, text="Password:", fg="white",
         bg="#0f0f0f", font=font_label).pack()
password_entry = tk.Entry(root, width=40, show="*")
password_entry.pack()

tk.Button(root, text="Start Stream",
          command=start_stream,
          bg="#e3d2ff", fg="black",
          width=20, height=2).pack(pady=20)

url_var = tk.StringVar()
tk.Entry(root, textvariable=url_var,
         width=45, state="readonly",
         justify="center").pack()

root.mainloop()
