# Connect, but only using TLS version 1.2
from multiprocessing import Process
import io
import os
import sys
from ftplib import FTP, FTP_TLS, error_perm
import ssl
from datetime import datetime
from time import sleep
import xml.etree.ElementTree as ET

class Config:
    def __init__(self, configs):
        self.OperationType = configs["OperationType"]
        self.OperationName = configs["OperationName"]
        self.IsDefault = configs["IsDefault"]
        self.Protocol = configs["Protocol"]
        self.Host = configs["Host"]
        self.PortNumber = configs["PortNumber"]
        self.Username = configs["Username"]
        self.Password = configs["Password"]
        self.FTPSecure = configs["FTPSecure"]
        self.FTPMode = configs["FTPMode"]
        self.Certificate = configs["Certificate"]
        self.SourcePath = configs["SourcePath"]
        self.DestPath = configs["DestPath"]
        self.FileMask = configs["FileMask"]
        self.IsRemove = configs["IsRemove"]

def connect(host, username, password, protocol):
    ftp_address = host
    ftp_username = username
    ftp_password = password

    ftp = FTP()
    if (protocol.lower() == 'tls'):
        ftp = FTP_TLS()
        ftp.ssl_version = ssl.PROTOCOL_TLS

    ftp.set_debuglevel(0)
    ftp.set_pasv(False)
    ftp.encoding = "utf-8"
    ftp.connect(ftp_address)
    ftp.login(ftp_username, ftp_password)
    if (protocol.lower() == 'tls'):
        ftp.prot_p()
    return ftp

def download(ftp, local_current_path):
    files = ftp.nlst()
    for item in files:
        localpath = os.path.join(local_current_path, item)
        try:
            #this will check if file is folder
            ftp.cwd(item)
            if (not os.path.exists(localpath)):
                os.mkdir(localpath)
            download(ftp, localpath)
            ftp.cwd("..")
            ftp.rmd(item)
        except error_perm as e:
            print("Downloading..." + item)

            with open(localpath, "wb") as file_content:
                ftp.retrbinary(f"RETR {item}", file_content.write)

            ftp.delete(item)

def download_content(config):
    ftp_current_path = config.SourcePath
    local_current_path = config.DestPath
    while (True):
        try:
            ftp = connect(config.Host, config.Username, config.Password, config.Protocol)
            ftp.cwd(ftp_current_path)
            files = ftp.nlst()
            if (len(files) == 0):
                ftp.close()
                sleep(10)
            else:
                start = datetime.now()
                download(ftp, local_current_path)
                ftp.close()
                end = datetime.now()
                diff = end - start
                print('All files downloaded for ' + str(diff.seconds) + 's')
        except:
            sleep(1)
            print('Something went wrong. I should be patient.')
            continue
            pass

def upload(ftp, local_current_path):
    files = os.listdir(local_current_path)
    if (len(files) != 0):
        for item in files:
            localpath = os.path.join(local_current_path, item)
            if os.path.isfile(localpath):
                print("Uploading..." + item)
                with open(localpath, "rb") as file_content:
                    ftp.storbinary(f"STOR {item}", file_content)
                os.remove(localpath)
            elif os.path.isdir(localpath):
                try:
                    ftp.mkd(item)
                    # ignore "directory already exists"
                except error_perm as e:
                    if not e.args[0].startswith('550'):
                        raise
                ftp.cwd(item)
                upload(ftp, localpath)
                ftp.cwd("..")
                os.removedirs(localpath)

def upload_content(config):
    local_current_path = config.SourcePath
    ftp_current_path = config.DestPath
    while (True):
        try:
            files = os.listdir(local_current_path)
            if (len(files) == 0):
                sleep(10)
            else:
                start = datetime.now()
                ftp = connect(config.Host, config.Username, config.Password, config.Protocol)
                ftp.cwd(ftp_current_path)
                upload(ftp, local_current_path)
                ftp.close()
                end = datetime.now()
                diff = end - start
                print('All files uploaded for ' + str(diff.seconds) + 's')
        except:
            sleep(1)
            print('Something went wrong. I should be patient.')
            continue
            pass

if (__name__ == '__main__'):
    print("Hi, This is a ftp tool to transfer your files between client and ftp server...")

    tree = ET.parse('config.xml')
    root = tree.getroot()

    configs = []
    for child in root:
        config = Config(child.attrib)
        configs.append(config)

    for item in configs:
        if (item.OperationType == "Get"):
            Process(target=download_content, args=(item,)).start()
        elif (item.OperationType == "Put"):
            Process(target=upload_content, args=(item,)).start()











