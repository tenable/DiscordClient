import socket
import struct
from Logger import *
import threading
import libnacl
import random

class AVStreamingServer:
    '''
    Manages Audio/Visual streaming data for call
    '''

    def __init__(self, media_server_ip, media_server_port):
        self.__sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__media_server_ip = media_server_ip
        self.__media_server_port = media_server_port
        self.__sock.connect((media_server_ip, media_server_port))
        self.__client_udp_port = None
        self.__secret_key = None
        self.__CurrentPacketNumAudio = 0
        self.__CurrentPacketNumImage = 0

    def GetExternalClientPort(self):
        # TODO figure data this out
        self.__sock.send(bytes.fromhex('0001004600000001000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'))
        response = self.__sock.recv(1024)
        self.__client_udp_port = struct.unpack(">H", response[-2::])[0]
        Logger.LogMessage("Obtained client's external UDP port: {}".format(self.__client_udp_port))
        return self.__client_udp_port


    def StartStream(self, secret_key):
        self.__secret_key = secret_key
        self.__sock.send(struct.pack('<Q', 1)) # Hello?
        threading.Thread(target=self.__recvStream).start()

    def __recvStream(self):
        while True:
            data = self.__sock.recv(4098)
            self.__decrypt(data)

    def SendStatus(self, msg):
        cipherText = b'\x80\xc8\x00\x06\x00\x00\x00\x01'
        cipherText = cipherText+self.__encrypt(msg)
        cipherText = cipherText + struct.pack('<I', self.__CurrentPacketNumAudio)
        self.__sock.send(cipherText)
        self.__CurrentPacketNumAudio = self.__CurrentPacketNumAudio + 1

    def SendAudio(self, msg):
        cipherText = bytes('\x90\x78{}\x2f\xa5\x6c\xab\x00\x00\x00\x01'.format(struct.pack('>h', self.__CurrentPacketNumAudio)), 'utf-8')
        cipherText = cipherText + self.__encrypt(msg)
        cipherText = cipherText + struct.pack('<I', self.__CurrentPacketNumAudio)
        self.__sock.send(cipherText)
        self.__CurrentPacketNumAudio = self.__CurrentPacketNumAudio+1

    def SendScreenImage(self, data):
        cipherText = '\x90\x67{}\x7f\xf2\x05\x57\x00\x00\x00\x05'.format(struct.pack('>h', self.__CurrentPacketNumImage))
        cipherText = cipherText + self.__encrypt(data)
        cipherText = cipherText + struct.pack('<I', self.__CurrentPacketNumImage)
        self.__sock.send(cipherText)
        self.__CurrentPacketNumImage = self.__CurrentPacketNumImage + 1

    def __encrypt(self, plaintext):
        cipherText =  libnacl.crypto_secretbox(plaintext, struct.pack('<I', self.__CurrentPacketNumAudio) + b"\x00" * 20, self.__secret_key)
        if(self.__CurrentPacketNumAudio > 32766):
            self.__CurrentPacketNumAudio = 0
        return cipherText

    def __decrypt(self, msg):
        nonce = msg[-4:]+b"\x00"*20
        if msg[:2] == '\x81\xc9':
            msg = msg[0x18:-4]
        elif msg[:2] == '\x90\x78':
            msg = msg[0x1C:-4]
        else:
            msg = msg[0x18:-4]
            Logger.LogMessage('wtf header received: {}'.format(msg.hex()), log_level=LogLevel.WARNING)

        plaintext = libnacl.crypto_secretbox(msg, nonce, self.__secret_key)
        Logger.LogMessage("Decrypted %d bytes %s:" % (len(plaintext), plaintext[0x10:].hex()))
        return plaintext
