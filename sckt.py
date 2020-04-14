#!/usr/bin/python3
# EduSSHBypasser Server 0.18
import socket,threading,base64
from ssl import wrap_socket
from sys import argv
SESSOES = {}
PAY_BUFFER = 65536
CUP_BUFFER = 1024
CDN_BUFFER = 8192
def CriarSessao(endereco,sessao):
    SESSOES[endereco] = sessao
def UsarSessao(endereco):
    try:
        sessao = SESSOES[endereco]
    except:
        return False
    del SESSOES[endereco]
    return sessao
class Proxy:
    def ativar(self,lhost,lport):
        proxy = socket.socket()
        proxy.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        proxy.bind((lhost,lport))
        proxy.listen(0)
        while True:
            cliente, endereco = proxy.accept()
            cliente.settimeout(9.0)
            Master(cliente,endereco[0]).start()
class Master(threading.Thread):
    def __init__(self,cliente,endereco):
        threading.Thread.__init__(self)
        self.cliente  = cliente
        self.endereco = endereco
    def run(self):
        try:
            self.cliente = wrap_socket(self.cliente,server_side=True,certfile='/usr/sbin/scktcerts/edussh.crt',keyfile='/usr/sbin/scktcerts/edussh.key')
            req = b''
            req = self.cliente.recv(PAY_BUFFER).replace(b'\r',b'')
        except:
            self.cliente.close()
        if req:
            pay  = req.split(b'\n')
            n    = 0
            metodo = b''
            custresp  = False
            while n < len(pay):
                if pay[n].split(b': ')[0] == b'X-Action' or pay[n].split(b': ')[0] == b'Metodo':
                    metodo = pay[n].split(b': ')[1].lower()
                if pay[n].split(b': ')[0] == b'cresp':
                    custresp = base64.b85decode(pay[n].split(b': ')[1])
                n = n+1
            if req[:4] == b'SSH-':
                try:
                    self.ssh = socket.create_connection(('127.0.0.1',443))
                    self.cliente.settimeout(180.0)
                    self.ssh.send(req)                      # SSH-2.0-Evozi...
                    HandlerL(self.cliente,self.ssh).start() # SSH ~> Cliente
                    while True:                             # Cliente ~> SSH
                        try:
                            dados = self.ssh.recv(16384)
                            if not dados: break
                            self.cliente.send(dados)
                        except:
                            break
                    self.cliente.close()
                    self.ssh.close()
                except:
                    pass
            elif metodo == b'':
                try:
                    if not custresp:
                        self.cliente.sendall(b'HTTP/1.1 200 ~EduSSH~\r\nServer: EduSSHBypasser\r\n\r\n')
                    else:
                        self.cliente.sendall(custresp)
                except:
                    self.cliente.close()
                MSimples(self.cliente).start()
            elif metodo == b'create':
                try:
                    self.cliente.sendall(b'HTTP/1.1 200 Created\r\nServer: EduSSHBypasser\r\nX-Id: 0\r\n\r\n')
                    GetTunnel(self.cliente,self.endereco).start()
                except:
                    self.cliente.close()
            elif metodo == b'complete':
                try:
                    self.cliente.sendall(b'HTTP/1.1 200 Completed\r\nServer: EduSSHBypasser\r\n\r\n')
                    CriarSessao(self.endereco,self.cliente)
                except:
                    self.cliente.close()
            elif metodo == b'tohu':
                try:
                    if not custresp:
                        self.cliente.sendall(b'HTTP/1.1 200 ~EduSSH~\r\nServer: EduSSHBypasser\r\n\r\n')
                    else:
                        self.cliente.sendall(custresp)
                except:
                    self.cliente.close()
                TOH(self.cliente,self.endereco).start()
            elif metodo == b'tohd':
                try:
                    if not custresp:
                        self.cliente.send(b'HTTP/1.1 200 ~EduSSH~\r\nServer: EduSSHBypasser\r\n\r\n')
                    else:
                        self.cliente.sendall(custresp)
                    CriarSessao(self.endereco,self.cliente)
                except:
                    self.cliente.close()

            elif metodo == b'tohr':
                if not custresp:
                    self.cliente.send(b'HTTP/1.1 200 ~EduSSH~\r\nServer: EduSSHBypasser\n\n')
                else:
                    self.cliente.send(custresp)
                n = 0
                cport = 0
                csolic = False
                rspst  = True
                while n < len(pay):
                    if pay[n].split(b': ')[0] == b'cport':
                        cport = int(pay[n].split(b': ')[1])
                    elif pay[n].split(b': ')[0] == b'csolic':
                        csolic = base64.b85decode(pay[n].split(b': ')[1]).replace(b'\\n',b'\n').replace(b'\\r',b'\r')
                    elif pay[n].split(b': ')[0] == b'rspst':
                        if pay[n].split(b': ')[1] == b"False":
                            rspst = False
                    n = n+1
                if cport:
                    TOHR(self.cliente,cport,rspst,csolic,self.endereco).start()
                else:
                    self.cliente.close()
        else:
            self.cliente.close()
class MSimples(threading.Thread):
    def __init__(self,cliente):
        threading.Thread.__init__(self)
        self.cliente = cliente
    def run(self):
        dados = ''
        l     = 0
        while l < 4:
            l = l+1
            try:
                dados = self.cliente.recv(PAY_BUFFER)
                if not dados:break
            except:
                break
            if dados[:4] == b'SSH-':
                try:
                    self.ssh = socket.create_connection(('127.0.0.1',22))
                    self.cliente.settimeout(180.0)
                    self.ssh.send(dados)                # SSH-2.0-Evozi...
                except:
                    break
                HandlerL(self.cliente,self.ssh).start() # Cliente ~> SSH
                while True:                             # SSH ~> Cliente
                    try:
                        dados = self.ssh.recv(CDN_BUFFER)
                        if not dados: break
                        self.cliente.send(dados)
                    except:
                        break
            else:
                try:
                    self.cliente.sendall(b'HTTP/1.1 200 ~EduSSH~\r\nServer: EduSSHBypasser\r\n\r\n')
                except:
                    break
        try:
            self.cliente.close()
            self.ssh.close()
        except:
            pass
class GetTunnel(threading.Thread):
    def __init__(self,cliente,endereco):
        threading.Thread.__init__(self)
        self.cliente  = cliente
        self.endereco = endereco
    def run(self):
        try:
            req = self.cliente.recv(PAY_BUFFER)
        except:
            pass
        if req:
            pay = req.split(b'\r\n')
            n = 1
            acao = b''
            while n < len(pay)-1:
                if pay[n].split(b': ')[0] == b'X-Action':
                    acao = pay[n].split(b': ')[1]
                n = n+1
            if acao == b'data':
                cliente = b''
                ssh = b''
                try:
                    self.cliente.settimeout(180.0)
                    ssh = socket.create_connection(('127.0.0.1',443))
                    cliente = UsarSessao(self.endereco)
                    cliente.settimeout(180.0)
                    if cliente and ssh:
                        HandlerL(self.cliente,ssh).start()  # Cliente ~> SSH
                        while True:                         # SSH ~> Cliente
                            try:
                                dados = self.ssh.recv(CDN_BUFFER)
                                if not dados: break
                                cliente.send(dados)
                            except:
                                break
                        try:
                            self.ssh.close()
                            cliente.close()
                        except:
                            pass
                except:
                    self.cliente.close()
            else:
                self.cliente.close()
class TOH(threading.Thread):
    def __init__(self,cliente, endereco):
        threading.Thread.__init__(self)
        self.tohu     = cliente
        self.endereco = endereco
    def run(self):
        try:
            dados = self.tohu.recv(PAY_BUFFER)
        except:
            pass
        if dados[:4] == b'SSH-':
            try:
                self.ssh = socket.create_connection(('127.0.0.1',443))
                self.tohu.settimeout(180.0)
                self.tohd = UsarSessao(self.endereco)
                self.tohd.settimeout(180.0)
                self.ssh.send(dados)                    # SSH-2.0-Evozi...
                HandlerL(self.tohu,self.ssh).start()    # Cliente ~> SSH
                while True:                             # SSH ~> Cliente
                    try:
                        dados = self.ssh.recv(CDN_BUFFER)
                        if not dados: break
                        self.tohd.send(dados)
                    except:
                        break
            except:
                pass
        try:
            self.tohu.close()
            self.tohd.close()
            self.ssh.close()
        except:
            pass
class TOHR(threading.Thread):
    def __init__(self,cliente,cport,resposta,payload,endereco):
        threading.Thread.__init__(self)
        self.cliente   = cliente
        self.cport     = cport
        self.resposta  = resposta
        self.payload   = payload
        self.endereco  = endereco
    def run(self):
        try:
            reverso = socket.create_connection((self.endereco,self.cport))
        except socket.error:
            reverso.close()
        if self.payload:
            reverso.sendall(self.payload)
        else:
            reverso.sendall(b'GET / HTTP/1.1\r\n\r\n')
        if self.resposta:
            rsp = reverso.recv(PAY_BUFFER)
        try:
            self.ssh = socket.create_connection(('127.0.0.1',443))
            self.cliente.settimeout(180.0)
        except:
            self.cliente.close()
            self.ssh.close()
            reverso.close()
        HandlerL(self.cliente,self.ssh).start()
        while True:
            try:
                dados = self.ssh.recv(CDN_BUFFER)
                if not dados:break
                reverso.send(dados)
            except:
                break
        try:
            self.cliente.close()
            self.ssh.close()
            reverso.close()
        except:
            pass
class HandlerL(threading.Thread):
    def __init__(self,s1,s2):
        threading.Thread.__init__(self)
        self.s1 = s1
        self.s2 = s2
    def run(self):
        while True:
            try:
                dados = self.s1.recv(CUP_BUFFER)
                if not dados: break
                self.s2.send(dados)
            except:
                break
        try:
            self.s1.close()
            self.s2.close()
        except:
            pass
if __name__ == '__main__':
    try:
        lhost = '127.0.0.1'
        lport = int(argv[1])
        servidor = Proxy()
        print('[~ SERVIDOR ~]\n[~> Endereco: {}:{}'.format(lhost,lport))
        servidor.ativar(lhost,lport)
    except socket.error as err:
        print('[~ ERRO ~]\n{}'.format(err))
    except KeyboardInterrupt:
        print('\n[!] Encerrando...')