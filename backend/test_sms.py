from sms_service import send_sms

# 🔴 Your verified Indian phone number
result = send_sms(
    '+916281149755',
    'Test from Disaster Prep System! SMS is working!'
)

if result['success']:
    print("SUCCESS! Check your phone!")
    print(f"SID: {result.get('sid')}")
else:
    print(f"FAILED: {result['error']}")