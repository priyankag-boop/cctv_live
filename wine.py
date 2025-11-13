import os
import sys
import subprocess
import tkinter as tk
from tkinter import messagebox
import webbrowser
import threading

# ========== Helper Functions ==========

def check_ffmpeg():
    """Ensure local ffmpeg.exe exists (no system fallback)."""
    if getattr(sys, 'frozen', False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    ffmpeg_path = os.path.join(base_dir, "ffmpeg", "ffmpeg.exe")

    if not os.path.exists(ffmpeg_path):
        messagebox.showerror("Error", f"Bundled FFmpeg not found!\nExpected at:\n{ffmpeg_path}")
        sys.exit(1)

    print(f"Using bundled FFmpeg: {ffmpeg_path}")
    return ffmpeg_path


def detect_rtsp_url(ffmpeg_path, user, password, ip):
    """Try top 20 common RTSP paths until one works."""
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

        # If on Linux, prepend "wine" for .exe
        if sys.platform.startswith("linux"):
            cmd.insert(0, "wine")

        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=6)
            if b"Stream #0" in result.stderr or b"Video" in result.stderr:
                print(f"Valid RTSP URL found: {rtsp_url}")
                return rtsp_url
        except subprocess.TimeoutExpired:
            print(f"Timeout on {path}")
        except Exception as e:
            print(f"Error testing {path}: {e}")

    messagebox.showerror("RTSP Error", "No valid RTSP URL found!\nPlease verify camera IP or credentials.")
    return None


import socket

def detect_icecast_port(host="portal.thabir.ai"):
    """Check if Icecast is reachable on port 80 or 8000 and return the working one."""
    for port in [80, 8000]:
        try:
            with socket.create_connection((host, port), timeout=3):
                print(f"Icecast detected on port {port}")
                return port
        except Exception:
            continue
    messagebox.showerror("Connection Error", f"Could not connect to Icecast on port 80 or 8000.\nCheck your network or server.")
    sys.exit(1)


def run_ffmpeg(ffmpeg_path, rtsp_url, stream_name):
    """Start streaming using local ffmpeg with auto-detected Icecast port."""
    host = "portal.thabir.ai"
    port = detect_icecast_port(host)

    icecast_url = f"icecast://source:hackme@{host}:{port}/{stream_name}"
    viewer_url = f"http://{host}:{port}/{stream_name}"

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

    print("Starting FFmpeg stream...\n", " ".join(cmd))
    try:
        subprocess.Popen(cmd)
        webbrowser.open(viewer_url)
        messagebox.showinfo("Stream Started", f"Your stream is live!\n\n{viewer_url}")
        url_var.set(viewer_url)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start FFmpeg:\n{e}")

# ========== GUI ==========

def start_stream():
    ip = ip_entry.get().strip()
    user = username_entry.get().strip()
    password = password_entry.get().strip()
    stream_name = mount_entry.get().strip()

    if not all([ip, user, password, stream_name]):
        messagebox.showwarning("Missing Info", "Please fill all fields.")
        return

    ffmpeg_path = check_ffmpeg()

    def task():
        rtsp_url = detect_rtsp_url(ffmpeg_path, user, password, ip)
        if rtsp_url:
            run_ffmpeg(ffmpeg_path, rtsp_url, stream_name)

    threading.Thread(target=task, daemon=True).start()


def copy_url():
    url = url_var.get()
    if not url:
        messagebox.showwarning("No URL", "No stream URL to copy yet.")
        return

    root.clipboard_clear()
    root.clipboard_append(url)
    root.update()
    messagebox.showinfo("Copied", "Stream URL copied to clipboard!")


# ========== GUI Setup ==========

root = tk.Tk()
root.title("CCTV Streamer")
root.geometry("420x400")
root.configure(bg="#0f0f0f")  # black background

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

tk.Label(root, text="Mount Name (e.g., stream1.webm):", fg="white", bg="#0f0f0f", font=font_label).pack(pady=4)
mount_entry = tk.Entry(root, width=40)
mount_entry.pack()

tk.Button(root, text="Start Stream", command=start_stream, bg="#e3d2ff", fg="grey", width=20, height=2).pack(pady=15)

url_var = tk.StringVar()
tk.Entry(root, textvariable=url_var, width=45, state="readonly", justify="center").pack(pady=5)
tk.Button(root, text="Copy URL", command=copy_url, bg="#e3d2ff", fg="grey").pack(pady=5)

root.mainloop()
