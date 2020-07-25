from twilio.rest import Client
import json

class Logger:

    def save_log(self, log: str):
        raise NotImplementedError("This method is intended to be overriden")

class WhatsappLogger(Logger):

    def __init__(self):
        with open("./twilio.txt", "r") as f:
            creds = f.read().split(",")
            account_sid = creds[0]
            auth_token = creds[1]

        with open("./config/phone_numbers.json", "r") as f:
            numbers = json.loads(f.read())
            self.to = numbers["OWN"]["number"]
            self.from_ = numbers["TWILIO"]["number"]
        self.client = Client(account_sid, auth_token)

    def save_log(self, log: str):
        self.client.messages.create(
            body=log,
            from_='whatsapp:'+str(self.from_),
            to='whatsapp:'+str(self.to)
        )

class LoggerSaver:

    @classmethod
    def save_log(cls, log: str, logger: Logger):
        logger.save_log(log)