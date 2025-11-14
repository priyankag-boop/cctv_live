import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
import webbrowser
import threading


# ================= RESOURCE PATH (IMPORTANT) =================

def resource_path(relative_path):
    """
    Get the correct path for files packaged inside PyInstaller EXE.
    """
    if hasattr(sys, '_MEIPASS'):   # Running from EXE
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


# Paths inside bundled EXE
FFMPEG_DIR = resource_path("ffmpeg")
FFMPEG = os.path.join(FFMPEG_DIR, "ffmpeg.exe")
FFPROBE = os.path.join(FFMPEG_DIR, "ffprobe.exe")
FFPLAY = os.path.join(FFMPEG_DIR, "ffplay.exe")

# ================= CHECK FFMPEG =================

def check_ffmpeg():
    if not os.path.exists(FFMPEG):
        messagebox.showerror("Error", f"Bundled FFmpeg not found at:\n{FFMPEG}")
        sys.exit(1)

    print(f"Using bundled FFmpeg at: {FFMPEG}")
    return FFMPEG


# ================= RTSP DETECTION =================

def detect_rtsp_url(ffmpeg_path, user, password, ip):
    common_paths = [
        "/Streaming/Channels/101",
        "/Streaming/Channels/102",
        "/cam/realmonitor?channel=1&subtype=0",
        "/cam/realmonitor?channel=1&subtype=1",
        "/live/main",
        "/live/sub",
        "/axis-media/media.amp",
        "/h264Preview_01_main",
        "/h264Preview_01_sub",
        "/stream1",
        "/live.sdp",
        "/media/video1",
        "/videoMain",
        "/videoSub",
        "/rtsp_tunnel",
        "/defaultPrimary",
        "/MediaInput/h264",
        "/profile1/media.smp",
        "/channel1",
        "/live/ch00_0",
    ]

    for path in common_paths:
        rtsp_url = f"rtsp://{user}:{password}@{ip}:554{path}"
        print(f"Testing {rtsp_url} ...")

        cmd = [ffmpeg_path, "-rtsp_transport", "tcp", "-i", rtsp_url, "-t", "3", "-f", "null", "-"]

        # Wine support (Linux only)
        if sys.platform.startswith("linux"):
            cmd.insert(0, "wine")

        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=6)
            output = result.stderr + result.stdout  # Wine sometimes flips streams

            if b"Stream #0" in output or b"Video" in output:
                print(f"Valid RTSP URL detected: {rtsp_url}")
                return rtsp_url

        except subprocess.TimeoutExpired:
            print("Timeout:", path)
        except Exception as e:
            print("Error:", e)

    messagebox.showerror("RTSP Error", "No valid RTSP URL found.\nCheck IP or credentials.")
    return None


# ================= START STREAM =================

def run_ffmpeg(ffmpeg_path, rtsp_url, mount):
    icecast_url = f"icecast://source:hackme@portal.thabir.ai:80/{mount}"
    viewer_url = f"http://portal.thabir.ai/{mount}"

    cmd = [
        ffmpeg_path,
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

    if sys.platform.startswith("linux"):
        cmd.insert(0, "wine")

    print("Starting FFmpeg:", " ".join(cmd))

    try:
        subprocess.Popen(cmd)
        webbrowser.open(viewer_url)
        messagebox.showinfo("Success", f"Your stream is live!\n\n{viewer_url}")
        url_var.set(viewer_url)

    except Exception as e:
        messagebox.showerror("FFmpeg Error", str(e))


# ================= GUI =================

def start_stream():
    ip = ip_entry.get().strip()
    user = username_entry.get().strip()
    passwd = password_entry.get().strip()
    mount = mount_entry.get().strip()

    if not all([ip, user, passwd, mount]):
        messagebox.showwarning("Missing Info", "Please fill all fields.")
        return

    ffmpeg_path = check_ffmpeg()

    def task():
        rtsp_url = detect_rtsp_url(ffmpeg_path, user, passwd, ip)
        if rtsp_url:
            run_ffmpeg(ffmpeg_path, rtsp_url, mount)

    threading.Thread(target=task, daemon=True).start()


def copy_url():
    url = url_var.get()
    if not url:
        messagebox.showwarning("No URL", "No stream yet.")
        return
    root.clipboard_clear()
    root.clipboard_append(url)
    root.update()
    messagebox.showinfo("Copied", "URL copied!")


# ================= GUI SETUP =================

root = tk.Tk()
root.title("CCTV Streamer")
root.geometry("420x400")
root.configure(bg="#0f0f0f")

font_title = ("Arial", 14, "bold")
font_label = ("Arial", 10)

tk.Label(root, text="CCTV Live Streamer", fg="#e8e0f5", bg="#0f0f0f", font=font_title).pack(pady=10)

tk.Label(root, text="Camera IP:", fg="white", bg="#0f0f0f", font=font_label).pack(pady=4)
ip_entry = tk.Entry(root, width=40)
ip_entry.pack()

tk.Label(root, text="Username:", fg="white", bg="#0f0f0f", font=font_label).pack(pady=4)
username_entry = tk.Entry(root, width=40)
username_entry.pack()

tk.Label(root, text="Password:", fg="white", bg="#0f0f0f", font=font_label).pack(pady=4)
password_entry = tk.Entry(root, width=40, show="*")
password_entry.pack()

tk.Label(root, text="Mount Name:", fg="white", bg="#0f0f0f", font=font_label).pack(pady=4)
mount_entry = tk.Entry(root, width=40)
mount_entry.pack()

tk.Button(root, text="Start Stream", command=start_stream, bg="#e3d2ff", fg="grey", width=20, height=2).pack(pady=15)

url_var = tk.StringVar()
tk.Entry(root, textvariable=url_var, width=45, state="readonly", justify="center").pack(pady=5)
tk.Button(root, text="Copy URL", command=copy_url, bg="#e3d2ff", fg="grey").pack(pady=5)

root.mainloop()
