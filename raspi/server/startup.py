import os


def run_uvicorn_with_port_retry(
    app_import_path,
    ip,
    host="0.0.0.0",
    ports_to_try=None,
    log_level=None,
    context_label="Server running at",
):
    import uvicorn

    if ports_to_try is None:
        ports_to_try = [8000, 8001, 8002, 8003, 8004]

    for attempt_port in ports_to_try:
        try:
            print(f"\n🌐 {context_label}: http://{ip}:{attempt_port}\n")
            os.environ["SENSEE_PORT"] = str(attempt_port)

            run_kwargs = {
                "app": app_import_path,
                "host": host,
                "port": attempt_port,
            }
            if log_level is not None:
                run_kwargs["log_level"] = log_level

            uvicorn.run(**run_kwargs)
            return attempt_port
        except OSError as e:
            error_str = str(e)
            if "10048" in error_str or "Address already in use" in error_str:
                if attempt_port == ports_to_try[-1]:
                    print(f"❌ All ports {ports_to_try} are already in use!")
                    print("   Please kill the background process or restart your system.")
                    raise SystemExit(1)
                print(f"⚠️  Port {attempt_port} in use, trying {attempt_port + 1}...")
            else:
                raise
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            raise

    raise SystemExit(1)