# cctv.py
import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
import webbrowser
import threading
import uuid
import traceback
import datetime

# ----------------- Logging -----------------
def log(msg):
    try:
        tmp = os.environ.get("TEMP") or "/tmp"
        logdir = os.path.join(tmp, "CCTVStreamer")
        os.makedirs(logdir, exist_ok=True)
        logfile = os.path.join(logdir, "cctv.log")
        with open(logfile, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat()} {msg}\n")
    except Exception:
        pass

def log_exc(e):
    try:
        tmp = os.environ.get("TEMP") or "/tmp"
        logdir = os.path.join(tmp, "CCTVStreamer")
        os.makedirs(logdir, exist_ok=True)
        errfile = os.path.join(logdir, "cctv_error.txt")
        with open(errfile, "a", encoding="utf-8") as f:
            f.write(f"{datetime.datetime.now().isoformat()}\n")
            traceback.print_exc(file=f)
            f.write("\n\n")
    except Exception:
        pass

# ----------------- Helpers -----------------
def resource_path(relative_path):
    """Return path whether running as script or PyInstaller exe."""
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)

def get_ffmpeg_path():
    return resource_path(os.path.join("ffmpeg", "ffmpeg.exe"))

def get_ffprobe_path():
    return resource_path(os.path.join("ffmpeg", "ffprobe.exe"))

def generate_mount_name():
    return f"mount_{uuid.uuid4().hex[:8]}.webm"

# ----------------- FFmpeg sanity -----------------
def check_ffmpeg_runnable():
    ff = get_ffmpeg_path()
    if not os.path.exists(ff):
        messagebox.showerror("Missing FFmpeg", f"Bundled ffmpeg.exe not found at:\n{ff}")
        return False
    try:
        # try run version
        r = subprocess.run([ff, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8)
        out = (r.stdout or b"") + (r.stderr or b"")
        log("ffmpeg -version output: " + out[:200].decode(errors="ignore"))
        return True
    except Exception as e:
        log("ffmpeg runnable check failed: " + str(e))
        log_exc(e)
        messagebox.showerror("FFmpeg Error", f"Failed to run bundled ffmpeg.exe:\n{e}")
        return False

# ----------------- RTSP detection -----------------
def detect_rtsp_url(user, password, ip):
    ff = get_ffmpeg_path()
    paths = [
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

    for path in paths:
        try:
            rtsp = f"rtsp://{user}:{password}@{ip}:554{path}"
            log(f"Testing RTSP {rtsp}")
            cmd = [ff, "-rtsp_transport", "tcp", "-i", rtsp, "-t", "4", "-f", "null", "-"]
            # run and capture both stdout & stderr
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=12)
            out = (proc.stderr or b"") + (proc.stdout or b"")
            outl = out.decode(errors="ignore")
            log("ffmpeg probe output (first 300 chars): " + outl[:300])
            # indicators that input opened
            if "Input #0" in outl or "Stream #" in outl or "Video:" in outl or "Duration" in outl:
                return rtsp
        except subprocess.TimeoutExpired:
            log(f"Timeout testing {path}")
        except Exception as e:
            log("Error testing path: " + str(e))
            log_exc(e)

    return None

# ----------------- Run stream -----------------
def run_ffmpeg_stream(rtsp_url, mount_name):
    try:
        ff = get_ffmpeg_path()
        icecast_url = f"icecast://source:hackme@portal.thabir.ai:80/{mount_name}"
        viewer_url = f"http://portal.thabir.ai/{mount_name}"

        cmd = [
            ff,
            "-rtsp_transport", "tcp",
            "-thread_queue_size", "512",
            "-i", rtsp_url,
            "-c:v", "libvpx",
            "-deadline", "realtime",
            "-cpu-used", "5",
            "-g", "1",
            "-b:v", "1000k",
            "-ar", "44100",
            "-ac", "1",
            "-c:a", "libvorbis",
            "-b:a", "128k",
            "-content_type", "video/webm",
            "-f", "webm",
            icecast_url
        ]

        log("Starting ffmpeg stream with cmd: " + " ".join(cmd[:6]) + " ...")
        subprocess.Popen(cmd)
        webbrowser.open(viewer_url)
        url_var.set(viewer_url)
        messagebox.showinfo("Stream Started", f"Stream started!\n\n{viewer_url}")
    except Exception as e:
        log("Failed to start ffmpeg: " + str(e))
        log_exc(e)
        messagebox.showerror("Start Error", f"Failed to start stream:\n{e}")

# ----------------- GUI handlers -----------------
def start_stream_clicked():
    try:
        ip = ip_entry.get().strip()
        user = username_entry.get().strip()
        password = password_entry.get().strip()
        if not ip or not user or not password:
            messagebox.showwarning("Missing", "Please fill IP, username and password.")
            return

        if not check_ffmpeg_runnable():
            return

        def worker():
            try:
                rtsp = detect_rtsp_url(user, password, ip)
                if not rtsp:
                    messagebox.showerror("RTSP Error", "No valid RTSP URL detected. Check IP and credentials (or test with a public RTSP).")
                    return
                mount = generate_mount_name()
                run_ffmpeg_stream(rtsp, mount)
            except Exception as e:
                log_exc(e)
                messagebox.showerror("Error", str(e))

        threading.Thread(target=worker, daemon=True).start()

    except Exception as e:
        log_exc(e)
        messagebox.showerror("Error", str(e))

# ----------------- UI -----------------
root = tk.Tk()
root.title("CCTV Streamer")
root.geometry("420x380")
root.configure(bg="#0f0f0f")

tk.Label(root, text="CCTV Live Streamer", fg="#e8e0f5", bg="#0f0f0f", font=("Arial", 14, "bold")).pack(pady=10)

tk.Label(root, text="Camera IP (or host):", fg="white", bg="#0f0f0f").pack(pady=2)
ip_entry = tk.Entry(root, width=40)
ip_entry.pack()

tk.Label(root, text="Username:", fg="white", bg="#0f0f0f").pack(pady=2)
username_entry = tk.Entry(root, width=40)
username_entry.pack()

tk.Label(root, text="Password:", fg="white", bg="#0f0f0f").pack(pady=2)
password_entry = tk.Entry(root, width=40, show="*")
password_entry.pack()

tk.Button(root, text="Start Stream", command=start_stream_clicked, bg="#e3d2ff", fg="grey", width=20, height=2).pack(pady=14)

url_var = tk.StringVar()
tk.Entry(root, textvariable=url_var, width=45, state="readonly", justify="center").pack(pady=6)

root.mainloop()
