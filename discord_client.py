from ServerOperations import *
import time
import random

class DiscordClient:
    def __init__(self, user_email, user_password, proxy_host=False, proxy_port=False):
        self.__user_email = user_email
        self.__user_password = user_password
        self.__server_operations = ServerOperations(self.__user_email, self.__user_password, proxy_host, proxy_port)

    def Call(self, channel_id, guild_id):
        self.__server_operations.CallChannel(channel_id, guild_id)

    def SendCallStatus(self, msg):
        self.__server_operations.SendCallStatus(msg)

    def SendCallAudio(self, msg):
        self.__server_operations.SendCallAudio(msg)

    def SendImage(self, data):
        self.__server_operations.SendImage(data)

if __name__ == '__main__':
        #dc = DiscordClient(user_email="your_email", user_password="your_password")
        #dc.Call(channel_id=b'right_click_voice_channel_and_copy_id', guild_id=b'the_first_one_in_the_url')
        #dc.SendCallStatus('000000000000000100000000000000000000000080bc07b0'.decode('hex'))
        #dc.SendCallAudio(msg=)
