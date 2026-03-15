import requests
import cv2
import numpy as np

# Create a small blank image
img = np.zeros((100, 100, 3), dtype=np.uint8)
cv2.imwrite("dummy.jpg", img)

with open("dummy.jpg", "rb") as f:
    files = {"image": f}
    response = requests.post("http://localhost:8000/api/upload/", files=files)
    
print("Status Code:", response.status_code)
if response.status_code == 500:
    print("500 Error HTML starts with:", response.text[:2000])
else:
    print("Response JSON:", response.text)
