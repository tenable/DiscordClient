import websocket
import ssl
import erlang
from Logger import *
from erlang import *

class GatewayServer():
    '''
    Manages authentication and data transfer to/from http://gateway.discord.gg
    '''
    URL = "wss://gateway.discord.gg/?encoding=etf&v=6"

    class OPCODE:
        '''
        Taken from https://discordapp.com/developers/docs/topics/opcodes-and-status-codes#voice-opcodes
        '''
        # Name                  Code    Client Action   Description
        DISPATCH =              0  #    Receive         dispatches an event
        HEARTBEAT =             1  #    Send/Receive    used for ping checking
        IDENTIFY =              2  #    Send            used for client handshake
        STATUS =                3  #    Send            used to update the client status
        VOICE_STATE =           4  #    Send            used to join/move/leave voice channels
        #                       5  #    ???             ???
        RESUME =                6  #    Send            used to resume a closed connection
        RECONNECT =             7  #    Receive         used to tell clients to reconnect to the gateway
        REQUEST_GUILD_MEMBERS = 8  #    Send            used to request guild members
        INVALID_SESSION =       9  #    Receive         used to notify client they have an invalid session id
        HELLO =                 10 #    Receive         sent immediately after connecting, contains heartbeat and server debug information
        HEARTBEAT_ACK =         11 #    Sent immediately following a client heartbeat that was received
        GUILD_SYNC =            12 #    ???             ???

    def __init__(self, proxy_host, proxy_port):
        self.__proxy_host = proxy_host
        self.__proxy_port = proxy_port
        self.__ws = websocket.WebSocket(sslopt={"check_hostname": False, "cert_reqs": ssl.CERT_NONE})
        self.__session_settings = {}
        self.__ws.settimeout(5)

    def Connect(self, token):
        gateway_auth_data = {OtpErlangBinary('op',bits=8): 2,
                OtpErlangBinary('d',bits=8):
                    {OtpErlangBinary('properties',bits=8):
                        {OtpErlangBinary('client_version',bits=8): OtpErlangBinary('0.0.305',bits=8),
                        OtpErlangBinary('os',bits=8): OtpErlangBinary('Windows',bits=8),
                        OtpErlangBinary('os_version',bits=8): OtpErlangBinary('6.1.7601',bits=8),
                        OtpErlangBinary('os_arch',bits=8): OtpErlangBinary('x64',bits=8),
                        OtpErlangBinary('release_channel',bits=8): OtpErlangBinary('stable',bits=8),
                        OtpErlangBinary('client_build_number',bits=8): 44004,
                        OtpErlangBinary('browser',bits=8): OtpErlangBinary('Discord Client',bits=8),
                        OtpErlangBinary('client_event_source',bits=8): OtpErlangAtom('nil')
                        },
                    OtpErlangBinary('compress',bits=8): False,
                    OtpErlangBinary('token',bits=8): OtpErlangBinary("{}".format(token), bits=8),
                    OtpErlangBinary('presence',bits=8):
                        {OtpErlangBinary('status',bits=8): OtpErlangBinary('online',bits=8),
                        OtpErlangBinary('since',bits=8): 0,
                        OtpErlangBinary('afk',bits=8): False,
                        OtpErlangBinary('activities',bits=8): []
                        }
                    }
                }
        # Connect to gateway
        gateway_auth_data = erlang.term_to_binary(gateway_auth_data)
        if self.__proxy_host != False and self.__proxy_port != False:
            self.__ws.connect(self.URL, origin="https://discordapp.com", http_proxy_host=self.__proxy_host, http_proxy_port=self.__proxy_port, header={"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.305 Chrome/69.0.3497.128 Electron/4.0.8 Safari/537.36"})
        else:
            self.__ws.connect(self.URL, origin="https://discordapp.com", header={"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.305 Chrome/69.0.3497.128 Electron/4.0.8 Safari/537.36"})
        Logger.LogMessage('Gateway_wss connecting -> {}'.format(self.URL), log_level=LogLevel.OK)

        # Receive response
        response = self.__ws.recv()
        Logger.LogMessage('Gateway_wss received <- {} bytes'.format(len(response)))
        Logger.LogMessage('Gateway_wss data received \r\n', to_file=True, to_console=False, hex_data=response)

        # Send auth message
        Logger.LogMessage('Gateway_wss sending -> {} bytes'.format(len(gateway_auth_data)))
        self.__ws.send_binary(gateway_auth_data)
        Logger.LogMessage('Gateway_wss data sent -> \r\n', to_file=True, to_console=False, hex_data=gateway_auth_data)

        # Receive media_token
        response = self.__ws.recv()
        etf_data = erlang.binary_to_term(response)
        Logger.LogMessage('Gateway_wss received <- {} bytes'.format(len(response)))
        Logger.LogMessage('Gateway_wss data received <- \r\n', to_file=True, to_console=False, hex_data=response)
        erlang.etfDictToJson(self.__session_settings, etf_data[OtpErlangAtom('d')])
        Logger.LogMessage('Authenticated over gateway as {}'.format(self.__session_settings['user']['id']), log_level=LogLevel.OK)
        Logger.LogMessage('Session id: {}'.format(self.__session_settings['session_id']))

    def GetSessionId(self):
        if self.__session_settings.has_key('session_id'):
            return self.__session_settings['session_id']

    def GetUserId(self):
        if self.__session_settings.has_key('user_id'):
            return self.__session_settings['user_id']

    def GetServerId(self): # Discord also calls this "channel id"
        if self.__session_settings.has_key('channel_id'):
            return self.__session_settings['channel_id']

    def __recvUntilKey(self, target_key):
        while True:
            try:
                result = self.__ws.recv()
                etf_data = erlang.binary_to_term(result)
                erlang.etfDictToJson(self.__session_settings, etf_data[OtpErlangAtom('d')])
                if self.__session_settings.has_key(target_key): # TODO: this only searches 1 depth of dictionary, needs to be fixed
                    return
            except websocket._exceptions.WebSocketTimeoutException:
                return

    def StartScreenShare(self):
        self.__ws.send_binary('\x83t\x00\x00\x00\x02m\x00\x00\x00\x02opa\x04m\x00\x00\x00\x01dt\x00\x00\x00\x05m\x00\x00\x00\x08guild_ids\x03nilm\x00\x00\x00\nchannel_idm\x00\x00\x00\x12600792727298244639m\x00\x00\x00\tself_mutes\x04truem\x00\x00\x00\tself_deafs\x05falsem\x00\x00\x00\nself_videos\x04true')

    def RequestMediaToken(self, channel_id):
        if channel_id is None:
            raise Exception("channel_id is None!")
        ring_data = {OtpErlangBinary('op',bits=8): 4,
                    OtpErlangBinary('d',bits=8):
                        {
                        OtpErlangBinary('self_mute',bits=8): False,
                        OtpErlangBinary('channel_id',bits=8): OtpErlangBinary(channel_id,bits=8),
                        OtpErlangBinary('guild_id',bits=8): OtpErlangAtom('nil'),
                        OtpErlangBinary('self_deaf',bits=8): False,
                        OtpErlangBinary('self_video',bits=8): False
                        }
                    }
        ring_data = erlang.term_to_binary(ring_data)
        self.__ws.send_binary(ring_data)
        Logger.LogMessage("Sending -> {} bytes to media server".format(len(ring_data)))
        #Logger.LogMessage("Ring packet", to_file=True, hex_data=ring_data)
        self.__recvUntilKey('token')
        Logger.LogMessage("Received media token: {}".format(self.__session_settings['token']), log_level=LogLevel.OK)
        return self.__session_settings['token']

    def GetEndpoint(self):
        if self.__session_settings.has_key('endpoint'):
            return self.__session_settings['endpoint']
