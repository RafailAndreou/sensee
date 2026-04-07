import os
import threading


def start_fastapi_server_in_background(get_local_ip):
    ip, _ = get_local_ip()

    def _run_server():
        import uvicorn

        ports_to_try = [8000, 8001, 8002, 8003, 8004]

        for attempt_port in ports_to_try:
            try:
                print(f"\n🌐 Access the configuration portal at: http://{ip}:{attempt_port}\n")
                os.environ["SENSEE_PORT"] = str(attempt_port)
                uvicorn.run(
                    "server.main:app",
                    host="0.0.0.0",
                    port=attempt_port,
                    log_level="info",
                )
                break
            except OSError as e:
                error_str = str(e)
                if "10048" in error_str or "Address already in use" in error_str:
                    if attempt_port == ports_to_try[-1]:
                        print(f"❌ All ports {ports_to_try} are already in use!")
                        print("   Please kill the background process or restart your system.")
                        raise SystemExit(1)
                    else:
                        print(f"⚠️  Port {attempt_port} in use, trying {attempt_port + 1}...")
                else:
                    raise
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                raise

    server_thread = threading.Thread(target=_run_server, daemon=True)
    server_thread.start()
    return ip, server_thread
