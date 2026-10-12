import requests

url = "https://agagdangerich.onrender.com/course"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    print("Erich Course API Response")
    print("Program:", data["program"])
    print("Section:", data["section"])
    print("Year:", data["year"])
else:
    print("Request failed.")
    print("Status Code:", response.status_code)