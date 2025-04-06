from requests import get

print(get("http://127.0.0.1:8080/api?project=v1&aaaaaa=false").json())
