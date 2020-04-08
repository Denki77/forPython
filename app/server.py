#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports


class ServerProtocol(asyncio.Protocol):
    login: str = None
    loginList = []
    stackMessage = []
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        # print(data)

        try:
            decoded = data.decode()
        except UnicodeDecodeError:
            print('Клиент печатает не на Unicode')
            self.transport.write(f'\n\r{self.login}, я не понимаю вас:(((\n\r'.encode())
            decoded = ""

        if self.login is not None:
            self.send_message(decoded)
        else:
            if decoded.startswith('login:'):
                self.login = decoded.replace('login:', "").replace('\r', "").replace('\n', "")
                if self.login in self.loginList:
                    self.transport.write(
                        f'Извините нас пожалуйста, но логин <{self.login}> сейчас занят, попробуйте зайти позже!\n\r'.encode())
                    self.transport.close()
                else:
                    self.transport.write(f'Привет, {self.login}!\n\r'.encode())
                    self.loginList.append(self.login)
                    self.send_history()
                    self.transport.write('Напишите что-нибудь здесь: '.encode())
            else:
                self.transport.write('Неправильный логин\n\r'.encode())
                self.transport.write('Введите ваш логин командой login:<YourLogin>: '.encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print('Пришел новый клиент')
        self.transport.write('Введите ваш логин командой login:<YourLogin>: '.encode())

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print('Клиент вышел')

    def send_history(self):
        self.transport.write(f'#################################################################\n\r'.encode())
        self.transport.write(f'{self.login}, ознакомьтесь с последними десятью сообщениями чата!\n\r'.encode())
        for message in self.stackMessage:
            self.transport.write(message.encode())
        self.transport.write(f'#################################################################\n\r'.encode())

    def send_message(self, content: str):
        message = f'<{self.login}>: {content}\n\r'
        self.stackMessage.append(message)
        if len(self.stackMessage) > 10:
            del self.stackMessage[0]

        for user in self.server.clients:
            user.transport.write(message.encode())
        self.transport.write('Продолжите писать здесь: '.encode())


class Server:
    clients: list

    def __init__(self):
        self.clients = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8889
        )

        print('Сервер запущен ...')

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print('Сервер остановлен вручную')