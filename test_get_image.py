import requests

url = "http://localhost:8000/images/cd45a523-eb42-4382-bb87-98b2c7fb4aac"
r = requests.get(url)
print(f"GET /images/id: Status {r.status_code}")
if r.status_code == 200:
    data = r.json()
    if data['images']:
        image_id = data['images'][0]['id']
        print(f"Found image_id: {image_id}")
        img_url = f"http://localhost:8000/images/file/{image_id}"
        r2 = requests.get(img_url)
        print(f"GET /images/file/id: Status {r2.status_code}, length: {len(r2.content)}")
        if r2.status_code != 200:
            print("Error:", r2.text)
