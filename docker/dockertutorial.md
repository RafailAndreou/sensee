# Step 1

Install Docker on your pc/raspberry pi/device

# Step 2

cd to docker(current folder)

# Step 3

build docker using:

```bash
docker compose up-d
```

# Step 4

visit localhost:8123
Create an account
go to profile(down left) -> security and create a long term long lived access token name the token sensee

# Step 6

copy your token
create a ha_config.json inside raspi/server

```json
{
  "url": "http://localhost:8123",
  "token": "LONG TOKEN"
}
```
