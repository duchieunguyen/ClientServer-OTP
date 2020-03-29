import socket
import sys
import time
import os
import json
from threading import Thread
from threading import Lock
DbMutex = Lock()
######################################################################################
################################### Global variable ##################################
######################################################################################
sock = socket.socket()
port = 1000
curr_dir = os.getcwd()
jsonDir = curr_dir + '/data/database.json'
errorLogDir = curr_dir + '/data/error_log.txt'
global queueUserData
queueUserData = []
######################################################################################
################################### Local function ###################################
######################################################################################
def storeErrorLog(data):
    file = open(errorLogDir, "a+")
    file.write(data)
    file.close()

def storeUserData(data):
    dataConvert = data.split('|')
    currData = {}
    isExist = False
    currData['id'] = str(dataConvert[0])
    currData['username'] = dataConvert[1]
    currData['password'] = dataConvert[2]
    if(len(dataConvert) == 4):
        currData['OTP'] = dataConvert[3]
    else:
        currData['OTP'] = ""
    DbMutex.acquire()
    try :
        with open(jsonDir) as fileDB:
            dataUser = json.load(fileDB)
            for i in range(0, len(dataUser['dataUser'])):
                if(currData['username'] == dataUser['dataUser'][i]['username']):
                    dataUser['dataUser'][i]['OTP'] = currData['OTP']
                    fileDB.close()
                    with open(jsonDir, "w") as jsonFile:
                        json.dump(dataUser, jsonFile, indent = 4)
                        jsonFile.close()
                    isExist = True
            if(not isExist):
                dataUser['dataUser'].append(currData)
                fileDB.close()
                with open(jsonDir, "w") as jsonFile:
                    json.dump(dataUser, jsonFile, indent = 4)
                    jsonFile.close()
            # else:
            #     print("User name has exist. OTP available")
        DbMutex.release()
    except Exception as e :
        storeErrorLog(str(e) + "\r\n")
        DbMutex.release()
        pass

def serverTask():
    sock.bind(('', port))
    sock.listen(2)
    global queueUserData
    global listClient
    #Store current client which holding OTP
    listClient = []
    while True:
        # try:
        client, addr  = sock.accept()
        # client.sendall(b'Connected OK')
        print("Request connect from ", addr)
        data = client.recv(1024)
        if data:
            dataParse = data.decode("utf-8")
            dataParse = dataParse.split("|")
            if((dataParse[0] == "OTP") and (len(dataParse) == 5)):
                updateOTP = dataParse[1] + "|" + dataParse[2] + "|" + dataParse[3] + "|" + dataParse[4]
                storeUserData(updateOTP)
                client.sendall(b'ReceivedOTP')
                dictClient = {}
                dictClient['id'] = dataParse[1]
                dictClient['client'] = client
                listClient.append(dictClient)
            else:
                if(queryDataBase(dataParse[1], dataParse[2]) == None):
                    queueUserData.append(data)
                    client.sendall(b'OK')
                else:
                    client.sendall(b'duplicated')
        while(len(queueUserData)):
            storeUserData(queueUserData.pop(0).decode("utf-8"))
        time.sleep(1)
        # except Exception as e :
        #     storeErrorLog(str(e) + "\r\n")
        # pass

def queryDataBase(username, password):
    currData ={}
    currData['username'] = username
    currData['password'] = password
    DbMutex.acquire()
    try:
        with open(jsonDir) as fileDB:
            dataUser = json.load(fileDB)
            for i in range(0, len(dataUser['dataUser'])):
                if((currData['username'] == dataUser['dataUser'][i]['username']) and (currData['password'] == dataUser['dataUser'][i]['password'])):
                    currData['id'] = dataUser['dataUser'][i]['id']
                    currData['OTP'] = dataUser['dataUser'][i]['OTP']
                    DbMutex.release()
                    return currData
            DbMutex.release()
            return None
    except Exception as e :
        storeErrorLog(str(e) + "\r\n")
        DbMutex.release()
        return None
        pass

def verityOTP(userID, OTP, realOTP):
    global listClient
    if(OTP == realOTP):
        print("Correct OTP")
        for i in range(0, len(listClient)):
            if(listClient[i]['id'] == userID):
                listClient[i]['client'].sendall(b'Match')
    else:
        print("Wrong OTP")

def handleCommandTask():
    helpMsg = ">>> Require : python client.py /commandline. \r\n>>> Command line : \r\n"
    helpMsg+= ">>> /register <username> <password>: Register new account, username and password must not contain space\r\n"
    helpMsg+=">>> /login <username> <password>: Login for user has already has account\r\n"
    print(helpMsg)
    while True :
        command = input()
        command = command.split(' ')
        if(len(command) == 1):
            if(command[0].lower() == 'ok'):
                print("Thank you\r\n")
            elif(command[0] == "/help"):
                print(helpMsg)
            else :
                print("Invalid command!\r\n")
        elif(len(command) > 1):
            commandLine = command[0]
            if(commandLine == "/register"):
                if(len(command) == 3):
                    userName = command[1]
                    password = command[2]
                    secretID = 0
                    for k in range(0, len(userName)):
                        secretID += (ord(userName[k]))
                    dataUser = str(secretID) + "|" + userName +"|" + password
                    storeUserData(dataUser)
                    print("Your ID is : ", secretID)
                else:
                    print("Please set available username and password\r\n")
            elif(commandLine == "/login"):
                if(len(command) == 3):
                    userName = command[1]
                    password = command[2]
                    resultDB = queryDataBase(userName, password)
                    if(resultDB != None):
                        idUser = input("Enter User ID :")
                        if(idUser == resultDB['id']):
                            OTP = input("Enter OTP :")
                            verityOTP(resultDB['id'], OTP, resultDB['OTP'])
                        else:
                            print("Wrong User ID\r\n")
                    else:
                        print("Wrong password and user name")
                else:
                    print("Wrong password and user name")
            else :
                print("Please type available command line.")
######################################################################################
################################### Main function ####################################
######################################################################################

def App_main():
    Thread_GetUserCmd = Thread(target=handleCommandTask)
    Thread_GetUserCmd.setDaemon(True)
    Thread_GetUserCmd.start()
    Thread_ListenFromClient = Thread(target=serverTask)
    Thread_ListenFromClient.setDaemon(True)
    Thread_ListenFromClient.start()
    while True :
        time.sleep(1)

App_main()