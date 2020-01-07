import inspect

class LogLevel:
    INFO = '\033[94m'
    OK = '\033[92m'
    WARNING = '\033[93m'
    DEFAULT = '\033[m'

class Logger:
    __fileName = "discord_client.log"

    @staticmethod
    def LogMessage(msg, hex_data='', to_file=False, to_console=True, log_level=LogLevel.INFO):
        stack = inspect.stack()
        function_name = "({}->{})".format(str(stack[1][0].f_locals['self']).split(' ')[0], stack[1][3])
        if to_console is True:
            if hex_data is not '':
                print('{} {}'.format(log_level, " ".join([h.encode('hex') for h in hex_data])))
            else:
                print('{} [+] {} {}'.format(log_level, function_name, msg))
            print(LogLevel.DEFAULT) # restore console color

        if to_file is True:  # TODO improve formatting
            hLog = open(Logger.__fileName, 'wb')
            hLog.write("{} {}".format(msg, '\r\n'))
            if hex_data is not '':
                hLog.write("{} {}".format(hex_data, '\r\n'))
                hLog.write("{} {} {}".format(function_name, " ".join([h.encode('hex') for h in hex_data]), '\r\n'))
            else:
                hLog.write("{} {} {}".format(function_name, msg, '\r\n'))
            hLog.close()
