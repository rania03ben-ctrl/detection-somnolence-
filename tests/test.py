from twilio.rest import Client

account_sid = "AC585f55799e869303538a74b1c0aeb635"
auth_token  = "8f92111091edf4c67bae06d5ca5601c2"

client = Client(account_sid, auth_token)

message = client.messages.create(
    body="Test SMS somnolence",
    from_="+12602766149",  # ton numéro Twilio
    to="+33745307327"      # ton numéro vérifié
)

print(f"Status : {message.status}")
print(f"SID    : {message.sid}")
print(f"Error  : {message.error_message}")
