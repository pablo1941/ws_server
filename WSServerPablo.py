'''
Script general que implementa un servicio de WebSocket para la comunicacion con dispositivos ESP8266.

'''

# Importacion de librerias y modulos.
import os
import time
from collections import namedtuple
import json
from threading import Timer
from time import sleep
import datetime
import signal
import sys
import ssl
from SimpleWebSocketServer import WebSocket, SimpleWebSocketServer, SimpleSSLWebSocketServer
from optparse import OptionParser
from pprint import pprint
import sys
reload(sys)
sys.setdefaultencoding('utf8')

from conBD import connect as connSQL # modulo para insercion en base de datos de informacion, comandos.
os.environ['TZ'] = 'America/Bogota'

pathf = "/var/www/html/Logs/" 
# Declaracion variables globales

clients = []    # Lista de clientes conectados al socket
admin = []    # Lista de administradores. Por ahora solo se admite 1.
puerto = 6085  # Puerto de conexion del WebSocket.

# Diccionario de datos donde se almacena el msg en formato clave, valor.
datos = {}
palabras = []  # lista donde se almacena el mensaje recibido en clave-valor sin separar

IdESP = {}  # Diccionario donde se almacenan datos de un cliente ESP
IdESPs = []  # Lista de clientes ESP con direccion Ip, Puerto y ID del chip
serverSu = {}  # Diccionario con datos del servidor.
# Lista con datos de mediciones de STM[Diccionario], query y values.
stmDic = []

# Metodos generales del script
#
##--------------------------------------------------------------------------------------
def dataUpdate(sep1, sep2, msg, filterField):
    # formato de construccion query UPDATE `dataName` SET `field1` = 'value1', `field2` = 'value2' WHERE `dataName`.filterField(`field`='value')
    datos = {}
    fields2 = ''
    conditionString = ''
    listaDatos = []

    KVSeparados = []
    KVSeparados = msg.split(sep2)
    if(KVSeparados.count('')):
        KVSeparados.remove('')

    for palabra in KVSeparados:
        TEMPO = palabra.split(sep1)
        key = TEMPO[0]
        value = TEMPO[1]
        # Si hay un \r en el valor, remuevalo.
        if(value.find('\r') > -1):
            value = value.replace('\r', '')

        if(key == filterField):
            conditionString = "`" + filterField + "`='" + value + "'"
            print("conditionString: %s ", conditionString)
        else:
            datos[key] = value
            fields2 = fields2 + "`" + key + "`='" + value + "',"

    #fields2 = fields2 + "`update_time`=" + "'" + str(int(time.time())) + "'"
    campos = ""
    longCampos = len(fields2)
    campos= fields2[:longCampos -1]
    listaDatos = [datos, campos, conditionString]
    return listaDatos

##--------------------------------------------------------------------------------------
# Desde un mensaje crea un diccionario, campos, valores para el metodo insert SQL.
def datosDiccionario(sep1, sep2, msg):
    datos = {}  # Diccionario para guardar clave, valor del mensaje entrante.
    # String donde se construye la consulta con los campos del msg.
    fields = '('
    values = '('  # String con los valores del msg
    listaDatos = []  # Lista donde se almacena Datos[Dicc], fields, values.
    KVSeparados = []
    KVSeparados = msg.split(sep2)
    nulos = KVSeparados.count('')

    if(nulos>0):
        KVSeparados.remove('')

    for palabra in KVSeparados:
        TEMPO = palabra.split(sep1)
        key = TEMPO[0]
        value = TEMPO[1]
        # Si hay un \r en el valor, remuevalo.
        if(value.find('\r') > -1):
            value = value.replace('\r', '')

        datos[key] = value
        fields = fields + '`' + key + '`,'
        values = values + "'" + value + "',"

    fields = fields + '`T`)'
    values = values + "'" + str(int(time.time())) + "')"
    listaDatos = [datos, fields, values]

    # Retornar una lista con diccionario de datos, string con query y string con values.
    return listaDatos

##--------------------------------------------------------------------------------------
# Metodo que recibe el mensaje de mediciones de la ESP, separa los datos en clave-valor,
# y realiza la insercion a la base de datos y envia al Admin Web para graficar.
def ESP_MSG(msg_receive):

    try:
        stmDic = datosDiccionario("\t", "\n", msg_receive)
        print("List STM:" + str(stmDic))
        connSQL(2, stmDic[1], stmDic[2])
        return str(BOF_RESPONSE)

    except Exception as inst:
        print(type(inst))     # the exception instance
        print(inst.args)      # arguments stored in .args
        with open(pathf + str(time.strftime('%Y-%m-%d'))+"_exception.txt", "a+") as fp:
            fp.write('\n****\n' + str(time.strftime('%Y-%m-%d-%H:%M:%S')) + ";" +
                     'ESP_MSG(msg_receive) Instance: ' + str(type(inst)) + "; args: " + str(inst.args) + '\n****\n')
            fp.close()

##--------------------------------------------------------------------------------------
# Definicion de la clase de Websocket Simplechat
class SimpleChat(WebSocket):

    def handleMessage(self):

            # self.sendMessage(self.data)
        try:
            path2 = pathf +  str(time.strftime('%Y-%m-%d')) + "/"
            msg_receive = self.data
            indexWRL_ID = msg_receive.find("WRL_ID\t")
            nombreESP = ""
            if indexWRL_ID > -1:
                strClaveSinWRL = msg_receive[indexWRL_ID:]
                initValor  = strClaveSinWRL.find("\t")
                corteValor = strClaveSinWRL.find("\n")
                strFinal   = strClaveSinWRL[initValor+1:corteValor - 1]
                nombreESP  = strFinal
                print(" ********** hello,  my WRL is:  ", strFinal)

            print("*******************Init handle------------------------------------------------")
            if len(msg_receive) > 0:
                with open(pathf + str(time.strftime('%Y-%m-%d')) + "_data.txt", "a+") as f:

                    f.write('\n****\n' + str(time.strftime('%Y-%m-%d-%H:%M:%S')) + ";" +
                            'datos recibidos:' + msg_receive + ";\r\n" + str(int(time.time())) + '\n')
                    f.close
            print("MSG: " + str(msg_receive))

            # Mensaje de mediciones desde ESP para Base de datos y Admin WEB
            if msg_receive.find("KW\tINFO") > -1:

                auxResponse = ESP_MSG(msg_receive)

                responseWS = ""
                print("--------------------------------------responseWS: ", responseWS)
                if(auxResponse.find("SIN_BOF") > -1 ):
                    print("--------------------------------------Banderas sin desbordamiento -------- ")       
                else:
                 	#print("--------------------------------------responseWS==0, sending response -------- ")   
                 	# responseWS = ""
                 	responseWS  = "PID\tWS\r\nVK\tRSP\r\nMSG\tCLR-"+ str(auxResponse) + "\r\nCHCKSM\t3685"
                 	self.sendMessage(responseWS)


                
                if(len(admin)):
                    # print("Enviando a ADMIN!")
                    admin[0].sendMessage(u'' + msg_receive)

                   # client.close()
            elif self.data.find("CONNECTED") > -1:
                # Borrar lista cada vez que hay una conexion de un cliente ESP.
                lista = []
                msg_update = self.data + "\r\nIP\t" + \
                    str(self.address[0]) + "\r\nPORT\t" + str(self.address[1]) + "\r\n"
                #print("Connected event: "  + msg_update)
                lista = dataUpdate("\t", "\r\n", msg_update, "WRL_ID")
                # Borrar diccionario cada vez que hay una conexion de un cliente ESP.
                IdESP={}
                # Lista[0] contiene el diccionario, lista[1] contiene query, lista[2] contiene values
                IdESP=lista[0]
                connSQL(1,lista[1],lista[2])
                IdESP["IP"]=self.address[0]
                IdESP["PORT"]=self.address[1]

                print("Connected event: after add ip and port: ...."  + str(IdESP))

                if len(admin) > 0:  # si hay un admnistrador le actualizo el nuevo cliente connectado
                    #print("ESP conectada, Hay ADMIN.")
                    admin[0].sendMessage(u'NEW-CLIENT{ "clientes": [' + ' {"IP":"'+str(
                        IdESP["IP"])+'", "Puerto": "' + str(IdESP["PORT"]) + '", "IdESP":"' + str(IdESP["IDESP"]) + '"}]}')

                IdESPs.append(IdESP)
                print(IdESPs)
                # Borrar diccionario cada vez que hay una conexion de un cliente ESP.
                IdESP={}


            # Manejo de mensajes desde SuperUsuario
            elif(self.data.find("USER\tSU_SERVER") > -1):
                print("Comando desde SuperUsuario!" + self.data)

                for espclient in clients:    
                  espclient.sendMessage(u"" + self.data+"/FechaTx: "+datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                
        except Exception as inst:
            print(type(inst))     # the exception instance
            print(inst.args)      # arguments stored in .args

            with open(pathf + str(time.strftime('%Y-%m-%d')) + "_exception.txt", "a+") as fp:
                fp.write('\n****\n' + str(time.strftime('%Y-%m-%d-%H:%M:%S')) + ";" +
                         'handleMessage(self) Instance: ' + str(type(inst)) + "; args: " + str(inst.args) + '\n****\n')
                fp.close()

    def handleConnected(self):

        print(self.address, ' Conectado')
        # self.sendMessage(u'Your direction-'+ str(self.address)  )
        clients.append(self)
        msg_con="START\tOK\r\nPUERTO\t" + \
            str(self.address[1]) + "\r\nIP\t" + str(self.address[0]) + "\r\n"
        self.sendMessage(u""+msg_con)
        # Almacenar clientes conectados.
        if (len(clients) > 0):
            with open(pathf + str(time.strftime('%Y-%m-%d')) + "_conexion.txt", "a+") as fc:
                msgWrite='\n**********\n' + 'Cliente conectado: ' + \
                    str(self.address) + '; Hora Conexion: ' + \
                    str(time.strftime('%Y-%m-%d-%H:%M:%S')) + '\n**********\n'
                fc.write(msgWrite)
                msgWrite=""
                fc.close()

    def handleClose(self):

        print(self.address, ' closed')

        clienteDesc=""  # Mensaje para almacenar en Log de conexion
        # Si hay al menos un cliente ESP, verifique cual es para removerlo de la lista IdESPs
        if(len(IdESPs) > 0):
            for IdESP in IdESPs:
                if IdESP["address"] == self.address[0] and IdESP["port"] == self.address[1]:
                    clienteDesc='Cliente ESP desconectado: ' + str(IdESP)
                    print("Cliente ESP desconectado: " + str(IdESP))
                    IdESPs.remove(IdESP)

        print(IdESPs)

        # Se remueve en todo caso de la lista de clientes..
        clients.remove(self)
        # Registro de desconexion de clientes.
        with open(pathf + str(time.strftime('%Y-%m-%d')) + "_conexion.txt", "a+") as fd:
            msgWrite='\n**********\n' + clienteDesc + '; Hora Desconexion: ' + \
                str(time.strftime('%Y-%m-%d-%H:%M:%S')) + '\n**********\n'
            fd.write(msgWrite)
            msgWrite=""
            fd.close()


# Inicio del programa principal.
if __name__ == "__main__":

    parser=OptionParser(usage="usage: %prog [options]", version="%prog 1.0")
    parser.add_option("--host", default='', type='string',
                      action="store", dest="host", help="hostname (localhost)")
    parser.add_option("--port", default=puerto, type='int',
                      action="store", dest="port", help="port (8000)")
    parser.add_option("--example", default='echo', type='string',
                      action="store", dest="example", help="echo, chat")
    parser.add_option("--ssl", default=0, type='int', action="store",
                      dest="ssl", help="ssl (1: on, 0: off (default))")
    parser.add_option("--cert", default='./cert.pem', type='string',
                      action="store", dest="cert", help="cert (./cert.pem)")
    parser.add_option("--key", default='./key.pem', type='string',
                      action="store", dest="key", help="key (./key.pem)")
    parser.add_option("--ver", default=ssl.PROTOCOL_TLSv1,
                      type=int, action="store", dest="ver", help="ssl version")

    (options, args)=parser.parse_args()

    cls=SimpleChat

    if options.ssl == 1:
        server=SimpleSSLWebSocketServer(
            options.host, options.port, cls, options.cert, options.key, version=options.ver)
    else:
        server=SimpleWebSocketServer(options.host, options.port, cls)

    def close_sig_handler(signal, frame):
        server.close()
        sys.exit()

    signal.signal(signal.SIGINT, close_sig_handler)

#------------------------------------------------------------------------------------------------------------
# Main loop del servidor WebSocket.

    while True:
        server.serveonce()
