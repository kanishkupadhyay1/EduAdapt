import requests

# 1. Test Beginner Student S005 on Dynamic Memory Allocation
payload_s005 = {
    "student_id": "S005",
    "topic": "Dynamic Memory Allocation",
    "top_k": 3,
}
r1 = requests.post("http://127.0.0.1:8000/api/session/generate", json=payload_s005)
assert r1.status_code == 200
data1 = r1.json()
lesson1 = data1.get("teaching", {})
struct1 = lesson1.get("structured_response", {})
print("Student S005 (Beginner) Objective:", struct1.get("learning_objective"))
print("Student S005 Code snippet:", struct1.get("c_code", "")[:60].replace("\n", " "))
print("Student S005 Personalization:", lesson1.get("personalization_applied", {}).get("instructional_strategy"))

# 2. Test Advanced Student S001 on Dynamic Memory Allocation
payload_s001 = {
    "student_id": "S001",
    "topic": "Dynamic Memory Allocation",
    "top_k": 3,
}
r2 = requests.post("http://127.0.0.1:8000/api/session/generate", json=payload_s001)
assert r2.status_code == 200
data2 = r2.json()
lesson2 = data2.get("teaching", {})
struct2 = lesson2.get("structured_response", {})
print("\nStudent S001 (Advanced) Objective:", struct2.get("learning_objective"))
print("Student S001 Code snippet:", struct2.get("c_code", "")[:60].replace("\n", " "))
print("Student S001 Personalization:", lesson2.get("personalization_applied", {}).get("instructional_strategy"))

# 3. Test Strings topic on S001
payload_strings = {
    "student_id": "S001",
    "topic": "Strings",
    "top_k": 3,
}
r3 = requests.post("http://127.0.0.1:8000/api/session/generate", json=payload_strings)
assert r3.status_code == 200
data3 = r3.json()
lesson3 = data3.get("teaching", {})
struct3 = lesson3.get("structured_response", {})
print("\nStudent S001 (Strings) Objective:", struct3.get("learning_objective"))
print("Student S001 Code snippet:", struct3.get("c_code", "")[:60].replace("\n", " "))

assert struct1.get("learning_objective") != struct2.get("learning_objective"), "Different students must receive different objectives!"
assert struct1.get("c_code") != struct2.get("c_code"), "Different students must receive different code implementations!"
assert "string" in struct3.get("c_code", "").lower() or "char" in struct3.get("c_code", "").lower(), "Strings must have string code!"
assert "malloc" not in struct3.get("c_code", "").lower(), "No DMA leakage in Strings!"

print("\nALL STUDENT-SPECIFIC PERSONALIZATION & TOPIC SPECIFICITY API CHECKS PASSED 100%!")
