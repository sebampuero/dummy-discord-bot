from twilio.rest import Client
import json

class Logger:

    def save_log(self, log: str):
        raise NotImplementedError("This method is intended to be overriden")

class WhatsappLogger(Logger):

    def __init__(self):
        with open("./config/creds.json", "r") as f:
            creds = json.loads(f.read())
            account_sid = creds["twillio"]["account_sid"]
            auth_token = creds["twillio"]["token"]

        with open("./config/phone_numbers.json", "r") as f:
            numbers = json.loads(f.read())
            self.to = numbers["OWN"]["number"]
            self.from_ = numbers["TWILIO"]["number"]
        self.client = Client(account_sid, auth_token)

    def save_log(self, log: str):
        msg = self.client.messages.create(
            body=log,
            from_='whatsapp:'+str(self.from_),
            to='whatsapp:'+str(self.to)
        )
        return msg

class LoggerSaver:

    @classmethod
    def save_log(cls, log: str, logger: Logger):
        return logger.save_log(log)