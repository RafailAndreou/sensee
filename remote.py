import urllib3

download_base = "https://cdn.jsdelivr.net/gh/probonopd/irdb@master/codes/"

http = urllib3.PoolManager()

with open("assets/index", "r") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue  # skip empty lines or comments

        url = download_base + line
        response = http.request("GET", url)

        if response.status == 200:
            print(f"✅ Downloaded: {url}")
            # Optional: Save the file locally
            with open(f"downloads/{line.replace('/', '_')}", "wb") as out_file:
                out_file.write(response.data)
        else:
            print(f"❌ Failed to download: {url} (Status: {response.status})")
