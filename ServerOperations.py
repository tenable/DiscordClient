import socket
from GatewayServer import *
from MediaServer import *
from Logger import *
from HttpServer import *

class ServerOperations():
    '''
    Handles all Discord server interactions (HTTP, Websocket, UDP)
    '''
    def __init__(self,
                 user_email,
                 user_password,
                 proxy_host,
                 proxy_port,
                 video=True):
        self.__proxy_host = proxy_host
        self.__proxy_port = proxy_port
        self.__http_server = HttpServer(user_email, user_password)
        self.__gateway_server = GatewayServer(self.__proxy_host, self.__proxy_port)
        self.__media_server = None
        self.__socket = sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__channel_id = None
        self.__guild_id = None
        self.__video = video
        self.__http_token = self.__http_server.GetToken()
        self.__media_token = None
        self.__gateway_server.Connect(self.__http_token)
        self.__server_id = None
        self.__user_id = None
        self.__session_id = None

    def CallChannel(self, channel_id, guild_id):
        self.__channel_id = channel_id
        self.__guild_id = guild_id
        token = self.__gateway_server.RequestMediaToken(self.__channel_id, self.__guild_id)
        endpoint = self.__gateway_server.GetEndpoint().decode("utf-8")
        self.__server_id = self.__gateway_server.GetServerId()
        self.__user_id = self.__gateway_server.GetUserId()
        self.__session_id = self.__gateway_server.GetSessionId()
        self.__media_server = MediaServer(endpoint, self.__server_id,  self.__user_id, self.__session_id, self.__proxy_host, self.__proxy_port, token)
        self.__media_server.StartStream()

    def SendCallAudio(self, msg):
        self.__media_server.SendCallAudio(msg)

    def SendCallStatus(self, msg):
        self.__media_server.SendCallStatus(msg)

    def SendImage(self, data):
        self.__gateway_server.StartScreenShare()
        while True:
            self.__media_server.SendScreenImage(data)
