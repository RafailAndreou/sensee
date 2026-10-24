This tutorial is for setting up home assistant docker on windows. If you want to check for raspberry pi check dockertutorpi.md(dockerpi folder)

# Step 1

Install Docker on your pc/raspberry pi/device

# Step 2

cd to docker(current folder)

# Step 3

build Docker using:

```bash
docker compose up -d
```

# Step 4

Visit `http://localhost:8123`

- Create an account
- Go to **Profile** (bottom left) → **Security**
- Create a long-lived access token and name it `sensee`

# Step 5

Copy your token and create `ha_config.json` inside `raspi/server/`:

```json
{
  "url": "http://localhost:8123",
  "token": "LONG TOKEN"
}
```

# Step 6: Pair devices through Sensee

Install/update Sensee's Python dependencies (`pip install -r requirements.txt`
from `raspi/`), restart the engine, and open Pair New Device in the web or
Flutter app. Select a discovered device and follow its setup steps. Android TV
Remote asks for the PIN shown on the TV; it may include letters.

Sensee also scans for Android TV Remote announcements on its own LAN, outside
Home Assistant's container. Selecting a TV found this way supplies its address
automatically. Windows Firewall/router multicast restrictions can still prevent
this fallback from finding a TV.

If the TV is not discovered, select **Add Android TV by IP** in Sensee.
Enter its IP address or hostname, then its on-screen PIN. This completes
Home Assistant integration setup without opening the Home Assistant UI.
The saved Home Assistant token must belong to an administrator for pairing.
Complex integration forms/external authorization may still require HA's UI.

## Automatic discovery and Docker networking

The Windows compose file publishes port 8123 for the web/API interface.
That alone does not forward LAN multicast discovery into Docker Desktop.
Manual-IP pairing working while automatic discovery fails can indicate this
network limitation. Windows host networking is not equivalent to native Linux
networking; changing a port mapping alone does not guarantee mDNS discovery.

For a Linux/Raspberry Pi Sensee appliance, use the host-network configuration:

```bash
cd docker
docker compose -f docker-compose.linux.yml up -d
```

This uses the same `docker/config` directory as the Windows compose file. Do not
run both configurations at once. The existing `dockerpi/docker-compose.yml`
also uses host networking, but stores configuration in a different directory.

If discovery remains empty:

- Keep Home Assistant and the awake TV on the same LAN, with guest/client
  isolation disabled. Multicast must be allowed between them (mDNS uses UDP 5353).
- Ensure Android TV Remote Service is installed and enabled on the TV.
- In Home Assistant, check Settings > System > Network > Zeroconf Browser for
  `_androidtvremote2._tcp.local.`. If absent, troubleshoot TV/network discovery.
- Ensure Home Assistant's `default_config:` or `zeroconf:` integration is enabled.
- If the service appears but Sensee shows a connection error, check the saved
  Home Assistant address/token and administrator permissions.

Discovery combines pending Home Assistant setup flows with local Android TV
announcements. Local announcements can include a TV already configured in HA;
selecting it may report `already_configured`. Use the existing smart-device list
for devices that are already set up.

References:
- https://www.home-assistant.io/integrations/androidtv_remote/
- https://www.home-assistant.io/installation/linux/#docker-compose
- https://docs.docker.com/engine/network/drivers/host/
