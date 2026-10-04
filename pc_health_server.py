import http.server
import json
import os
import platform
import socketserver
import sys
import time
from datetime import datetime

try:
    import psutil
except ImportError:
    print("Error: psutil is not installed.")
    print("Install it using: pip install psutil")
    sys.exit(1)


# ============================================================
# CONFIGURATION
# ============================================================

DEFAULT_PORT = 5050

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE_DIR, "pc_health_monitor.html")


# ============================================================
# GLOBAL STATE
# ============================================================

prev_time = time.time()
prev_disk_io = psutil.disk_io_counters()
prev_net_io = psutil.net_io_counters()


# Prime CPU measurements
psutil.cpu_percent(interval=None)
psutil.cpu_percent(interval=None, percpu=True)

# Prime process CPU measurements
for process in psutil.process_iter():
    try:
        process.cpu_percent(interval=None)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        continue


# ============================================================
# UTILITY FUNCTIONS
# ============================================================

def safe_round(value, digits=2):
    """Safely round a numeric value."""
    try:
        return round(value, digits)
    except (TypeError, ValueError):
        return 0


def bytes_to_gb(value):
    """Convert bytes to GB."""
    return safe_round(value / (1024 ** 3), 2)


def bytes_to_mb(value):
    """Convert bytes to MB."""
    return safe_round(value / (1024 ** 2), 1)


# ============================================================
# CPU INFORMATION
# ============================================================

def get_cpu_model():
    """Retrieve the actual processor name on Windows."""
    try:
        if platform.system() == "Windows":
            import winreg

            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
            )

            name, _ = winreg.QueryValueEx(
                key,
                "ProcessorNameString"
            )

            winreg.CloseKey(key)

            if name:
                return name.strip()

    except Exception:
        pass

    return platform.processor() or "Unknown Processor"


# ============================================================
# SYSTEM INFORMATION
# ============================================================

def get_system_specs():
    """Return static system information."""

    try:
        boot_timestamp = psutil.boot_time()
        boot_time = datetime.fromtimestamp(
            boot_timestamp
        ).strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        boot_time = "Unknown"

    try:
        mem = psutil.virtual_memory()

        total_ram = bytes_to_gb(mem.total)
    except Exception:
        total_ram = 0

    return {
        "hostname": platform.node(),

        "os_name": f"{platform.system()} {platform.release()}",

        "os_arch": platform.machine(),

        "os_version": platform.version(),

        "cpu_model": get_cpu_model(),

        "physical_cores": psutil.cpu_count(logical=False) or 0,

        "logical_cores": psutil.cpu_count(logical=True) or 0,

        "total_ram_gb": total_ram,

        "boot_time": boot_time
    }


# ============================================================
# REAL-TIME SYSTEM METRICS
# ============================================================

def get_realtime_metrics():
    global prev_time
    global prev_disk_io
    global prev_net_io

    current_time = time.time()

    dt = max(
        current_time - prev_time,
        0.001
    )

    # --------------------------------------------------------
    # CPU
    # --------------------------------------------------------

    cpu_total = psutil.cpu_percent(
        interval=None
    )

    cpu_cores = psutil.cpu_percent(
        interval=None,
        percpu=True
    )

    # --------------------------------------------------------
    # MEMORY
    # --------------------------------------------------------

    mem = psutil.virtual_memory()

    swap = psutil.swap_memory()

    # --------------------------------------------------------
    # DISKS
    # --------------------------------------------------------

    disks = []

    try:
        partitions = psutil.disk_partitions(
            all=False
        )
    except Exception:
        partitions = []

    for partition in partitions:

        try:
            usage = psutil.disk_usage(
                partition.mountpoint
            )

            disks.append({
                "device": partition.device,

                "mountpoint": partition.mountpoint,

                "fstype": partition.fstype,

                "total_gb": bytes_to_gb(
                    usage.total
                ),

                "used_gb": bytes_to_gb(
                    usage.used
                ),

                "free_gb": bytes_to_gb(
                    usage.free
                ),

                "percent": usage.percent
            })

        except (
            PermissionError,
            OSError
        ):
            continue

    # --------------------------------------------------------
    # DISK I/O
    # --------------------------------------------------------

    current_disk_io = psutil.disk_io_counters()

    if (
        current_disk_io
        and prev_disk_io
    ):
        read_bytes_sec = (
            current_disk_io.read_bytes
            - prev_disk_io.read_bytes
        ) / dt

        write_bytes_sec = (
            current_disk_io.write_bytes
            - prev_disk_io.write_bytes
        ) / dt

    else:
        read_bytes_sec = 0
        write_bytes_sec = 0

    read_bytes_sec = max(
        0,
        read_bytes_sec
    )

    write_bytes_sec = max(
        0,
        write_bytes_sec
    )

    # --------------------------------------------------------
    # NETWORK I/O
    # --------------------------------------------------------

    current_net_io = psutil.net_io_counters()

    if (
        current_net_io
        and prev_net_io
    ):
        net_sent_sec = (
            current_net_io.bytes_sent
            - prev_net_io.bytes_sent
        ) / dt

        net_recv_sec = (
            current_net_io.bytes_recv
            - prev_net_io.bytes_recv
        ) / dt

    else:
        net_sent_sec = 0
        net_recv_sec = 0

    net_sent_sec = max(
        0,
        net_sent_sec
    )

    net_recv_sec = max(
        0,
        net_recv_sec
    )

    # --------------------------------------------------------
    # UPDATE PREVIOUS VALUES
    # --------------------------------------------------------

    prev_time = current_time

    prev_disk_io = current_disk_io

    prev_net_io = current_net_io

    # --------------------------------------------------------
    # BATTERY
    # --------------------------------------------------------

    battery_info = None

    try:
        battery = psutil.sensors_battery()

        if battery:

            battery_info = {
                "percent": battery.percent,

                "power_plugged": battery.power_plugged,

                "secs_left": (
                    battery.secsleft
                    if battery.secsleft != psutil.POWER_TIME_UNKNOWN
                    else None
                )
            }

    except Exception:
        battery_info = None

    # --------------------------------------------------------
    # PROCESSES
    # --------------------------------------------------------

    processes = []

    for process in psutil.process_iter(
        [
            "pid",
            "name",
            "cpu_percent",
            "memory_info",
            "memory_percent",
            "username"
        ]
    ):

        try:
            info = process.info

            memory_info = info.get(
                "memory_info"
            )

            rss_mb = (
                bytes_to_mb(memory_info.rss)
                if memory_info
                else 0
            )

            processes.append({
                "pid": info.get("pid", 0),

                "name": (
                    info.get("name")
                    or "System"
                ),

                "cpu": safe_round(
                    info.get("cpu_percent") or 0,
                    1
                ),

                "mem_mb": rss_mb,

                "mem_percent": safe_round(
                    info.get("memory_percent") or 0,
                    1
                ),

                "user": (
                    info.get("username")
                    or ""
                )
            })

        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess
        ):
            continue

    # --------------------------------------------------------
    # SORT PROCESSES BY CPU USAGE
    # --------------------------------------------------------

    processes.sort(
        key=lambda process: process["cpu"],
        reverse=True
    )

    # --------------------------------------------------------
    # UPTIME
    # --------------------------------------------------------

    try:
        uptime_seconds = int(
            time.time()
            - psutil.boot_time()
        )
    except Exception:
        uptime_seconds = 0

    # --------------------------------------------------------
    # RETURN DATA
    # --------------------------------------------------------

    return {

        "timestamp": current_time,

        "uptime_seconds": uptime_seconds,

        "cpu_total": cpu_total,

        "cpu_cores": cpu_cores,

        "memory": {

            "total_gb": bytes_to_gb(
                mem.total
            ),

            "used_gb": bytes_to_gb(
                mem.used
            ),

            "available_gb": bytes_to_gb(
                mem.available
            ),

            "free_gb": bytes_to_gb(
                mem.free
            ),

            "percent": mem.percent
        },

        "swap": {

            "total_gb": bytes_to_gb(
                swap.total
            ),

            "used_gb": bytes_to_gb(
                swap.used
            ),

            "percent": swap.percent
        },

        "disks": disks,

        "disk_io": {

            "read_bytes_per_sec":
                read_bytes_sec,

            "write_bytes_per_sec":
                write_bytes_sec,

            "cumulative_read_bytes":
                (
                    current_disk_io.read_bytes
                    if current_disk_io
                    else 0
                ),

            "cumulative_write_bytes":
                (
                    current_disk_io.write_bytes
                    if current_disk_io
                    else 0
                ),

            "read_count":
                (
                    current_disk_io.read_count
                    if current_disk_io
                    else 0
                ),

            "write_count":
                (
                    current_disk_io.write_count
                    if current_disk_io
                    else 0
                )
        },

        "net_io": {

            "bytes_sent_per_sec":
                net_sent_sec,

            "bytes_recv_per_sec":
                net_recv_sec,

            "cumulative_sent_bytes":
                (
                    current_net_io.bytes_sent
                    if current_net_io
                    else 0
                ),

            "cumulative_recv_bytes":
                (
                    current_net_io.bytes_recv
                    if current_net_io
                    else 0
                )
        },

        "battery": battery_info,

        "processes_count":
            len(processes),

        "processes":
            processes
    }


# ============================================================
# HTTP REQUEST HANDLER
# ============================================================

class MonitorRequestHandler(
    http.server.SimpleHTTPRequestHandler
):

    # --------------------------------------------------------
    # JSON RESPONSE
    # --------------------------------------------------------

    def send_json(self, data, status=200):

        response = json.dumps(
            data
        ).encode("utf-8")

        self.send_response(status)

        self.send_header(
            "Content-Type",
            "application/json; charset=utf-8"
        )

        self.send_header(
            "Cache-Control",
            "no-cache, no-store, must-revalidate"
        )

        self.send_header(
            "Pragma",
            "no-cache"
        )

        self.send_header(
            "Content-Length",
            str(len(response))
        )

        self.end_headers()

        self.wfile.write(response)

    # --------------------------------------------------------
    # GET REQUESTS
    # --------------------------------------------------------

    def do_GET(self):

        # Dashboard
        if self.path in (
            "/",
            "/index.html"
        ):

            if not os.path.exists(
                HTML_FILE
            ):

                self.send_error(
                    404,
                    "pc_health_monitor.html not found."
                )

                return

            try:

                with open(
                    HTML_FILE,
                    "rb"
                ) as file:

                    content = file.read()

                self.send_response(200)

                self.send_header(
                    "Content-Type",
                    "text/html; charset=utf-8"
                )

                self.send_header(
                    "Cache-Control",
                    "no-cache"
                )

                self.send_header(
                    "Content-Length",
                    str(len(content))
                )

                self.end_headers()

                self.wfile.write(content)

            except Exception as error:

                self.send_error(
                    500,
                    f"Unable to load dashboard: {error}"
                )

            return

        # System information
        if self.path == "/api/system-info":

            try:

                info = get_system_specs()

                self.send_json(info)

            except Exception as error:

                self.send_json(
                    {
                        "success": False,
                        "error": str(error)
                    },
                    500
                )

            return

        # Real-time metrics
        if self.path == "/api/realtime-stats":

            try:

                stats = get_realtime_metrics()

                self.send_json(stats)

            except Exception as error:

                self.send_json(
                    {
                        "success": False,
                        "error": str(error)
                    },
                    500
                )

            return

        # Unknown GET request
        self.send_error(
            404,
            "Not Found"
        )

    # --------------------------------------------------------
    # POST REQUESTS
    # --------------------------------------------------------

    def do_POST(self):

        if self.path != "/api/kill-process":

            self.send_error(
                404,
                "Not Found"
            )

            return

        # ----------------------------------------------------
        # Read request body
        # ----------------------------------------------------

        try:

            content_length = int(
                self.headers.get(
                    "Content-Length",
                    0
                )
            )

        except ValueError:

            self.send_json(
                {
                    "success": False,
                    "error": "Invalid Content-Length."
                },
                400
            )

            return

        if content_length <= 0:

            self.send_json(
                {
                    "success": False,
                    "error": "Request body is empty."
                },
                400
            )

            return

        try:

            body = self.rfile.read(
                content_length
            )

            payload = json.loads(
                body.decode("utf-8")
            )

        except (
            UnicodeDecodeError,
            json.JSONDecodeError
        ):

            self.send_json(
                {
                    "success": False,
                    "error": "Invalid JSON request."
                },
                400
            )

            return

        # ----------------------------------------------------
        # Get PID
        # ----------------------------------------------------

        try:

            pid = int(
                payload.get("pid")
            )

        except (
            TypeError,
            ValueError
        ):

            self.send_json(
                {
                    "success": False,
                    "error": "A valid PID is required."
                },
                400
            )

            return

        # ----------------------------------------------------
        # Basic PID validation
        # ----------------------------------------------------

        if pid <= 0:

            self.send_json(
                {
                    "success": False,
                    "error": "Invalid PID."
                },
                400
            )

            return

        # Prevent accidentally terminating this
        # monitoring server itself.

        if pid == os.getpid():

            self.send_json(
                {
                    "success": False,
                    "error": "Cannot terminate the monitoring server itself."
                },
                400
            )

            return

        # ----------------------------------------------------
        # Terminate process
        # ----------------------------------------------------

        try:

            process = psutil.Process(pid)

            process_name = process.name()

            process.terminate()

            try:

                process.wait(
                    timeout=3
                )

            except psutil.TimeoutExpired:

                process.kill()

                process.wait(
                    timeout=2
                )

            self.send_json(
                {
                    "success": True,

                    "message":
                        f"Terminated {process_name} "
                        f"(PID: {pid})",

                    "pid": pid,

                    "process": process_name
                }
            )

        except psutil.NoSuchProcess:

            self.send_json(
                {
                    "success": False,
                    "error": f"Process {pid} no longer exists."
                },
                404
            )

        except psutil.AccessDenied:

            self.send_json(
                {
                    "success": False,
                    "error":
                        f"Access denied while terminating PID {pid}."
                },
                403
            )

        except psutil.TimeoutExpired:

            self.send_json(
                {
                    "success": False,
                    "error":
                        f"Process {pid} could not be terminated in time."
                },
                500
            )

        except Exception as error:

            self.send_json(
                {
                    "success": False,
                    "error": str(error)
                },
                500
            )

    # --------------------------------------------------------
    # SUPPRESS DEFAULT LOGGING
    # --------------------------------------------------------

    def log_message(
        self,
        format,
        *args
    ):

        # Keep the terminal clean.
        pass


# ============================================================
# REUSABLE LOCAL TCP SERVER
# ============================================================

class ReusableTCPServer(
    socketserver.ThreadingTCPServer
):

    allow_reuse_address = True

    # Worker threads will not prevent
    # the server from shutting down.
    daemon_threads = True


# ============================================================
# MAIN
# ============================================================

def main():

    import webbrowser

    # --------------------------------------------------------
    # PORT
    # --------------------------------------------------------

    if (
        len(sys.argv) > 1
        and sys.argv[1].isdigit()
    ):

        requested_port = int(
            sys.argv[1]
        )

    else:

        requested_port = DEFAULT_PORT

    # --------------------------------------------------------
    # Validate port
    # --------------------------------------------------------

    if not (
        1024
        <= requested_port
        <= 65535
    ):

        print(
            "[Error] Port must be between "
            "1024 and 65535."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Find available port
    # --------------------------------------------------------

    httpd = None

    active_port = requested_port

    for port_candidate in range(
        requested_port,
        requested_port + 10
    ):

        try:

            httpd = ReusableTCPServer(
                (
                    "127.0.0.1",
                    port_candidate
                ),
                MonitorRequestHandler
            )

            active_port = port_candidate

            break

        except OSError as error:

            # Windows: 10048
            # Linux/macOS: 48

            if (
                getattr(
                    error,
                    "winerror",
                    None
                ) == 10048

                or

                getattr(
                    error,
                    "errno",
                    None
                ) == 48
            ):

                print(
                    f"[Notice] Port "
                    f"{port_candidate} is already in use, "
                    f"trying {port_candidate + 1}..."
                )

                continue

            raise

    # --------------------------------------------------------
    # No available port
    # --------------------------------------------------------

    if httpd is None:

        print(
            "[Error] Could not find an available "
            f"port between {requested_port} "
            f"and {requested_port + 9}."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Dashboard URL
    # --------------------------------------------------------

    dashboard_url = (
        f"http://127.0.0.1:{active_port}"
    )

    # --------------------------------------------------------
    # Startup message
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print(
        " PulseCore Real-Time Hardware Monitor"
    )
    print("=" * 70)

    print(
        f" Dashboard : {dashboard_url}"
    )

    print(
        f" Hostname  : {platform.node()}"
    )

    print(
        f" CPU       : {get_cpu_model()}"
    )

    print(
        f" RAM       : "
        f"{bytes_to_gb(psutil.virtual_memory().total)} GB"
    )

    print(
        f" Processes : "
        f"{len(list(psutil.process_iter()))}"
    )

    print("-" * 70)

    print(
        " Server is running locally."
    )

    print(
        " Press Ctrl+C to stop."
    )

    print("=" * 70)
    print()

    # --------------------------------------------------------
    # Open browser
    # --------------------------------------------------------

    try:

        webbrowser.open(
            dashboard_url
        )

    except Exception:

        print(
            f"Open this URL manually: "
            f"{dashboard_url}"
        )

    # --------------------------------------------------------
    # Start server
    # --------------------------------------------------------

    try:

        httpd.serve_forever()

    except KeyboardInterrupt:

        print()
        print(
            "Shutting down PulseCore gracefully..."
        )

    finally:

        try:

            httpd.shutdown()

        except Exception:
            pass

        try:

            httpd.server_close()

        except Exception:
            pass

        print(
            "PulseCore monitor stopped."
        )


# ============================================================
# PROGRAM ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()