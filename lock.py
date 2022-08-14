

class Lock:
    def __init__(self, date, license):
        self.date = date
        self.paid = False
        self.license = license
        self.unlockPass = [None ,0xABCD, 0xBCDE, 0xCDEF][int(str(license)[-1])]

    def setPaid(self, paid):
        self.paid = paid

    def checkPassword(self, password):
        if password.isnumeric():
            if int(password) ^ self.license == self.unlockPass:
                self.paid = True

        return self.paid
