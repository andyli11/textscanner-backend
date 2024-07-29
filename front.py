"""
USAGE: python3 front.py
- same test script to simulate front end
"""

import requests

def send_image_url(image_url: str):
    url = 'http://127.0.0.1:5000/upload'
    payload = {
        'urls': [image_url]
    }
    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, json=payload, headers=headers)
        
    if response.status_code == 200:
        print('Image URL sent successfully!')
    else:
        print(f'Failed to send image URL. Status code: {response.status_code}')
        print(response.text)

# Example usage
send_image_url('https://upcdn.io/kW15cAr/raw/uploads/2024/07/29/4kSi4HMa3H-Screenshot%202024-07-28%20at%2010.28.19%E2%80%AFAM.png')
