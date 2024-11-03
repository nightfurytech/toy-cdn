import os, json, requests
from flask import Flask, request, Response
from hashlib import md5

app = Flask(__name__)

origin_map = {"127.0.0.1:9000": "https://www.google.com/"}

cache_dir = "./cache"
os.makedirs(cache_dir, exist_ok=True)


@app.route("/", defaults={"path": ""}, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.route("/<path:path>", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
def proxy(path):
    origin_base = origin_map.get(request.host)
    if not origin_base:
        return Response(f"Unknown origin: {request.host}", status=404)
    origin_url = request.host.replace(request.host, origin_base)
    url_hash = md5(origin_url.encode()).hexdigest()

    if response := cache_get(url_hash):
        print(f"cache hit: {url_hash}")
        return response

    print(f"{request.url} --> {origin_url}")
    print(f"fetching from origin {origin_url}")
    # handling only get requests here, add more methods of your choice
    origin_response = requests.get(origin_url)
    if origin_response.status_code == 200:
        cache_put(url_hash, origin_response)
        return Response(origin_response.text)
    else:
        return Response(f"Error from origin: {origin_response.status_code}", status=origin_response.status_code)


def cache_get(url_hash):
    cache_path = os.path.join(cache_dir, url_hash)
    if not os.path.exists(cache_path):
        return None
    with open(cache_path, "r") as f:
        data = json.load(f)
    return Response(data["text"])


def cache_put(url_hash, origin_response):
    cache_path = os.path.join(cache_dir, url_hash)
    with open(cache_path, "w") as f:
        f.write(json.dumps({
            "text": origin_response.text,
        }))


if __name__ == '__main__':
    app.run(port=9000)
