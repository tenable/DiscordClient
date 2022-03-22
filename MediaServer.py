import json
from Logger import *
import ssl
import websocket
import requests
from AVStreamingServer import *

class MediaServer():
    '''
    Manages call status/settings updates to wss://us-west725.discord.media
    '''

    class OPCODE:
        '''
        Taken from https://discordapp.com/developers/docs/topics/opcodes-and-status-codes#voice-opcodes
        '''
        # Name              Code    Sent by     Description
        IDENTIFY            = 0     # client    begin a voice websocket connection
        SELECT_PROTOCOL     = 1     # client    select the voice protocol
        READY               = 2     # server    complete the websocket handshake
        HEARTBEAT           = 3     # client    keep the websocket connection alive
        SESSION_DESCRIPTION = 4     # server    describe the session
        SPEAKING            = 5     # client and server   indicate which users are speaking
        HEARTBEAT_ACK       = 6     # server    sent immediately following a received client heartbeat
        RESUME              = 7     # client    resume a connection
        HELLO               = 8     # server    the continuous interval in milliseconds after which the client should send a heartbeat
        INVALIDATE_SESSION  = 9     # server    acknowledge Resume
        #                     10    # ???       ???
        #                     11    # ???       ???
        CLIENT_CONNECT      = 12    # ???       ???
        CLIENT_DISCONNECT   = 13    # server    a client has disconnected from the voice channel

    def __init__(self, endpoint, server_id, user_id, session_id, proxy_host, proxy_port, token):
        self.__avstreaming_server = None
        self.__ws = websocket.WebSocket(sslopt={"check_hostname": False, "cert_reqs": ssl.CERT_NONE})
        self.__ws.settimeout(5)
        self.__server_id = server_id
        self.__endpoint = "wss://{}/?v=4".format(endpoint.split(':')[0])
        self.__token = token
        self.__media_session_id = None
        self.__av_client_port = None
        self.__user_id = user_id
        self.__session_id = session_id
        self.__isSpeaking = False
        self.__isSharingImage = False
        self.__secret_key = None
        self.__proxy_host = proxy_host
        self.__proxy_port = proxy_port
        self.__server_port = None
        self.__server_ip = None
        self.__client_ip = requests.get('https://api.ipify.org').text # TODO: should be getting this from AVStreaming Server

    def __getNextOpcode(self, opcode):
        try:
            while True:
                result = json.loads(self.__ws.recv())
                Logger.LogMessage('Media_wss received <- : {}'.format(result))
                if result['op'] == opcode:
                    return result
        except websocket._exceptions.WebSocketTimeoutException:
            return None

    def __sendOpcode(self, opcode, data):
        if type(opcode) != int:
            raise Exception("opcode {} should be type integer".format(opcode))
        data = json.dumps({"op": opcode, "d": data})
        self.__ws.send(data)
        Logger.LogMessage("Media_wss sent -> : {}".format(data))

    def __hello(self):
        self.__sendOpcode(self.OPCODE.IDENTIFY, {"server_id": str(self.__server_id), "user_id": str(self.__user_id),
                                        "session_id": str(self.__session_id), "token": str(self.__token), "video": True})

    def __getOpcodeData(self, frame, key):
        return frame['d'][key]

    def StartStream(self):
        if self.__proxy_host != False and self.__proxy_port != False:
            self.__ws.connect(self.__endpoint, http_proxy_host=self.__proxy_host, http_proxy_port=self.__proxy_port, header={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9004 Chrome/91.0.4472.164 Electron/13.6.6 Safari/537.36"})
        else:
            self.__ws.connect(self.__endpoint, header={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/1.0.9004 Chrome/91.0.4472.164 Electron/13.6.6 Safari/537.36"})
        Logger.LogMessage("Starting media server stream")
        self.__hello()
        self.__getServerNetworkSettings()
        self.__sendClientNetworkSettings()
        data = self.__getNextOpcode(self.OPCODE.SESSION_DESCRIPTION)
        self.__secret_key = "".join([chr(c) for c in data['d']['secret_key']])
        self.__media_session_id = data['d']['media_session_id']
        self.__avstreaming_server.StartStream(self.__secret_key)

    def SendCallAudio(self, msg):
        if not self.__isSpeaking:
            self.__sendOpcode(self.OPCODE.SPEAKING, {"ssrc": 1, "delay":0, "speaking": 1})
            self.__isSpeaking = True
        self.__avstreaming_server.SendAudio(msg)

    def SendCallStatus(self, msg):
        self.__avstreaming_server.SendStatus(msg)

    def SendScreenImage(self, data):
        if not self.__isSharingImage:
            self.__sendOpcode(self.OPCODE.CLIENT_CONNECT, {"audio_ssrc": 1, "video_ssrc": 2, "rtx_ssrc": 3})
            self.__isSharingImage = True
        self.__avstreaming_server.SendScreenImage(data)

    def __getServerNetworkSettings(self):
        clientHandshakeResponse = self.__getNextOpcode(self.OPCODE.READY)
        self.__server_port = self.__getOpcodeData(clientHandshakeResponse, 'port')
        self.__server_ip = self.__getOpcodeData(clientHandshakeResponse, 'ip')
        self.__avstreaming_server = AVStreamingServer(self.__server_ip, self.__server_port)

    def __sendClientNetworkSettings(self):
        self.__av_client_port = self.__avstreaming_server.GetExternalClientPort()
        self.__sendOpcode(self.OPCODE.SELECT_PROTOCOL, {"protocol": "udp",
            "data": {"address": self.__client_ip, "port": self.__av_client_port, "mode": "xsalsa20_poly1305_lite"},
            "address": "localhost", "port": self.__av_client_port, "mode": "xsalsa20_poly1305_lite",
            "codecs": [{"name": "opus", "type": "audio", "priority": 1000, "payload_type": 120},
                       {"name": "H264", "type": "video", "priority": 1000, "payload_type": 101},
                       {"name": "VP8", "type": "video", "priority": 2000, "payload_type": 103, "rtx_payload_type": 104},
                       {"name": "VP9", "type": "video", "priority": 3000, "payload_type": 105, "rtx_payload_type": 106},
            ],
            "rtc_connection_id": 0 # TODO: what is this
        })
