import requests

def login(username, password):
    url = "https://localhost:7045/api/Auth/login"
    data = {"username": username, "password": password}
    response = requests.post(url, json=data, verify=False)
    if response.status_code == 200:
        print("Login successful")
        return response.json().get("Message")
    else:
        print(f"Login failed: {response.status_code}")
        return None

username = "testuser"
password = "password"
login(username, password)
