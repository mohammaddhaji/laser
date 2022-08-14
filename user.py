import datetime
import pickle
import os

from paths import USERS_DATA


class User:
    def __init__(self, number, name):
        self.phoneNumber = number
        self.name = name
        self.sessionNumber = 1
        self.sessions = {} 
        self.note = ''
        bodyParts = ['face', 'arm', 'armpit', 'body', 'bikini', 'leg']
        self.shot = dict.fromkeys(bodyParts, 0)
        self.currentSession = 'finished'
        self.nextSession = None
    
    
    def setCurrentSession(self, status):
        self.currentSession = status

    def incShot(self, part):
        self.shot[part] = self.shot[part] + 1

    def setPhoneNumber(self, number):
        self.phoneNumber = number

    def setName(self, name):
        self.name = name

    def setNote(self, note):
        self.note = note

    def setNextSession(self, date):
        self.nextSession = date

    def addSession(self):
        session = self.shot.copy()
        session['date'] = datetime.datetime.now()
        self.sessions[self.sessionNumber] = session
        self.shot = dict.fromkeys(self.shot, 0)
        self.sessionNumber += 1

    def __str__(self):
        return '<' + self.name + '> ' + '(' + self.phoneNumber + ')'


def loadUsers():
    try:
        if os.path.isfile(USERS_DATA):
            with open(USERS_DATA, 'rb') as f:
                usersData = pickle.load(f)
            
        else:
            usersData = {}
            with open(USERS_DATA, 'wb') as f:
                pickle.dump(usersData, f)

        return usersData
    except Exception as e:
        print(e)
