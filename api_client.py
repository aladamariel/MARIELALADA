import requests

url = "https://marielalada.onrender.com/attendance"

response = requests.get(url)

if response.status_code == 200:
    data = response.json()

    print("Student Name:", data["student_name"])
    print("Attendance Status:", data["attendance_status"])
    print("Attendance Percentage:", data["attendance_percentage"])
else:
    print("Request failed.")
    print("Status Code:", response.status_code)