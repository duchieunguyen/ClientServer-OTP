import socket
import sys
import configparser
import os
import time
import json
import math
import random
from threading import Thread
######################################################################################
################################### Global variable ##################################
######################################################################################

config = configparser.ConfigParser()
global sockClient
curr_dir = os.getcwd()
config.read(curr_dir + '/data/' + 'config.ini')
jsonDir = curr_dir + '/data/database.json'
errorLogDir = curr_dir + '/data/error_log.txt'
######################################################################################
################################### Local function ###################################
######################################################################################
def connect2Server():
    global sockClient
    sockClient = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ipHost = (config['IPHOST']['IP_SERVER'],int(config['IPHOST']['PORT_SERVER']))
    print("Establishing connection...")
    try:
        sockClient.connect(ipHost)
    except Exception as e:
        print(str(e))
        storeErrorLog(str(e))
        return False
    return True

def sendData2Server(data):
    global sockClient
    sockClient.sendall(data.encode('utf8'))
    print("Sending message to client")


def storeErrorLog(data):
    file = open(errorLogDir, "a+")
    file.write(data)
    file.close()

def storeUserData(id, userName, password, OTP):
    currData = {}
    currData['id'] = str(id)
    currData['username'] = userName
    currData['password'] = password
    currData['OTP'] = " "
    # try :
    with open(jsonDir) as fileDB:
        dataUser = json.load(fileDB)
        if(not len(dataUser['dataUser'])):
            dataUser['dataUser'].append(currData)
            fileDB.close()
            if(connect2Server()):
                msg = str(id) + "|" + userName +"|" + password + "|" + " "
                sendData2Server(msg)
                respond = sockClient.recv(16).decode('utf-8')
                if(respond == "duplicated"):
                    print("Account exist, please choice other username")
                elif (respond == "OK"):
                    with open(jsonDir, "w") as jsonFile:
                        json.dump(dataUser, jsonFile, indent = 4)
                        jsonFile.close()
                    print("Your ID is : ", id)
                sockClient.close()
        else:
            cmd = input("Your device has already had an account. Type : /clear to clear account or OK to exit \r\n")
            if(cmd == "/clear"):
                with open(jsonDir, "w") as jsonFile:
                    dataUser['dataUser'] = []
                    json.dump(dataUser, jsonFile, indent = 4)
                    jsonFile.close()
            elif(cmd == "OK"):
                print("OK thanks")
            else :
                print(" Wrong command, exiting...")
    # except Exception as e :
    #     storeErrorLog(str(e) + "\r\n")
    #     pass

def generateOTP():
    with open(jsonDir) as fileDB:
        dataUser = json.load(fileDB)
        fileDB.close()
    OTP = ""
    currData = {}
    currData['id'] = str(dataUser['dataUser'][0]['id'])
    currData['username'] =  dataUser['dataUser'][0]['username']
    currData['password'] = dataUser['dataUser'][0]['password']
    element = currData['id'] + currData['username'] + currData['password']
    for i in range(6) : 
        OTP += element[math.floor(random.random() * len(element))]
    currData['OTP'] = OTP
    dataUser['dataUser'][0]['OTP'] = currData['OTP']
    with open(jsonDir, "w") as jsonFile:
        json.dump(dataUser, jsonFile, indent = 4)
        jsonFile.close()
    if(connect2Server()):
        count = 60
        msg = "OTP|" + str(currData['id']) + "|" + currData['username'] +"|" + currData['password'] + "|" + currData['OTP']
        sendData2Server(msg)
        print(" Your OTP is : ", OTP)
        while(count):
            print("OTP available in ", count)
            count-=1
            sockClient.settimeout(1)
            try :
                respond = sockClient.recv(16).decode('utf-8')
            except Exception as e:
                pass
            if (respond == "Match"):
                count = 0
                msg = "OTP|" + str(currData['id']) + "|" + currData['username'] +"|" + currData['password'] + "|" + "None"
                sendData2Server(msg)
                print(respond)
            # time.sleep(1)
        msg = "OTP|" + str(currData['id']) + "|" + currData['username'] +"|" + currData['password'] + "|" + "None"
        connect2Server()
        sendData2Server(msg)
        sockClient.close()
    dataUser['dataUser'][0]['OTP'] = ""
    with open(jsonDir, "w") as jsonFile:
        json.dump(dataUser, jsonFile, indent = 4)
        jsonFile.close()


######################################################################################
################################### Main function ####################################
######################################################################################

def App_Main():
    helpMsg = ">>> Require : python client.py /commandline. \r\n>>> Command line : \r\n"
    helpMsg+= ">>> /register <username> <password>: Register new account, username and password must not contain space\r\n"
    helpMsg+=">>> /otp: get OTP for user\r\n"
    if(len(sys.argv) == 1):
        command = input("Type /help for list command line and type and 'OK' to exit\r\n")
        if(command.lower() == 'ok'):
            print("Exit")
        elif(command == "/help"):
            print(helpMsg)
    elif(len(sys.argv) > 1):
        commandLine = sys.argv[1]
        if(commandLine == "/help"):
            print(helpMsg)
        elif(commandLine == "/register"):
            if(len(sys.argv) == 4):
                userName = sys.argv[2]
                password = sys.argv[3]
                secretID = 0
                for k in range(0, len(userName)):
                    secretID += (ord(userName[k]))
                storeUserData(secretID, userName, password, " ")
            else:
                print("Please set available username and password\r\n")
        elif(commandLine == "/otp"):
            generateOTP()
        else :
            print("Please type available command line.")

App_Main()
