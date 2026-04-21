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
