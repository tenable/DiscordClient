from Logger import *
import requests
import json

class HttpServer:
    '''
    Manages HTTP authentication
    '''
    URL = "https://discordapp.com/api/v6/auth/login"

    def __init__(self, user_email, user_password):
        self.__user_email = user_email
        self.__user_password = user_password
        self.__token = None

    def Connect(self):
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) discord/0.0.305 Chrome/69.0.3497.128 Electron/4.0.8 Safari/537.36"})
        session.headers.update({'X-Super-Properties': ''})
        session.headers.update({"Content-Type": "application/json"})
        http_auth_data = '{{"email": "{}", "password": "{}", "undelete": false, "captcha_key": null, "login_source": null, "gift_code_sku_id": null}}'.format(self.__user_email, self.__user_password)
        Logger.LogMessage('Post -> {}'.format(self.URL))
        Logger.LogMessage('{}'.format(http_auth_data))
        response = session.post(self.URL, data=http_auth_data)
        Logger.LogMessage('Response <- {}'.format(response.content), log_level=LogLevel.OK)
        self.__token = json.loads(response.content)['token']

    def GetToken(self):
        if self.__token is None:
            self.Connect()
        return self.__token
