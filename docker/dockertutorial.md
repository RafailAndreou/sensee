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

# Step 6

In the browser(http://localhost:8123) press + sign -> add device, select your device
Your device won't be autommatically find through homeassistant on windows so you have to manually put the ip
for example:
+-> add device -> android tv remote -> host = tv_ip and submit

then run your gesture.py and your app and it will work fine
