import socket, struct, sys, _thread, time, threading, fcntl, os, pickle, time, re, io, signal

Server_1 = ''
Server_2 = ''

local_list1=[]
local_list2=[]
local_list3=[]

def sig_handler(signum, frame):   
    dump()
    os._exit(0)    

signal.signal(signal.SIGTERM, sig_handler)
signal.signal(signal.SIGSEGV, sig_handler)
signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGILL, sig_handler)
signal.signal(signal.SIGABRT, sig_handler)
signal.signal(signal.SIGFPE, sig_handler)


class fileNode(object):
    def __init__(self, name=None, server=None, servercopy=None, replication=None,quarantine=None ):
        self.name = name
        self.server = server
        self.servercopy = servercopy
        self.replication = replication
        self.quarantine = quarantine

#create file containining current local files' state when first started
def onUpdate():
    global local_list1, local_list2, local_list3 
    for dirpath, dirnames, files in os.walk('/dir/path/'): #replace /dir/path with file path to folder containing other folder(s) and file(s) which you want to include in the single system image
        if not dirnames:
             for file in files:
                 local_list3.append(fileNode(os.path.join(file), "Server_3", "0", "0","0"))
    #print(local_list1)
    with open('/dir/path/saveit.txt', 'r') as f: #replace /dir/path with an arbitrary path. This CANNOT be the same as /dir/path for folder included for single system image 
        header = f.readline()
#checks if server crashed or did a graceful exit.
#if crashed, it's filesystem state might not have been backed up to other servers
#so reload from its last saved state
        if header == 'crashed\n':
            for i in range(0, len(local_list3)):
                for line in f:
                    line = line.split('$')
                    #print(line[0])
                    #print(local_list2[i].name)
                    if local_list3[i].name == line[0]:
                        local_list3[i].server = line[1]
                        local_list3[i].servercopy = line[2]
                        local_list3[i].replication = line[3]
                        local_list3[i].quarantine = line[4] 


#dump files' state and attributes if server crashes
def dump(): 
    global local_list3, directory
    f = open("/dir/path/saveit.txt", "w") #replace /dir/path with an arbitrary path. This CANNOT be the same as /dir/path for folder included for single system image 
    f.write("crashed" + '\n')    
    for i in range(0,len(local_list3)):
        f.write(local_list3[i].name + '$')
        #print(local_list2[i].name)
        f.write(local_list3[i].server + '$')
        f.write(local_list3[i].servercopy + '$')
        f.write(local_list3[i].replication + '$')
        f.write(local_list3[i].quarantine + '$')
        f.write('\n')

def unique(input):
  output = []
  for x in input:
    if x.name not in output:
      output.append(x)
  return output

def get_ip_address(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(
        s.fileno(),
        0x8915,  # SIOCGIFADDR
        struct.pack('256s',  bytes(ifname[:15], 'utf-8'))
    )[20:24])

#print(get_ip_address('wlan0'))

def sendingUDP():
    global local_list1, local_list2, local_list3 
    multicast_group = '224.1.1.3' #arbitrarily set. All servers must be in the same group
    server_address = ('', 10000)
# Create the socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# Bind to the server address
    sock.bind(server_address)
    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP,socket.IP_ADD_MEMBERSHIP,mreq)

# Receive/respond loop
    while True:
        #print('\nwaiting to receive message')
        data, address = sock.recvfrom(1024)
        sock.sendto(b'ack', address)

def acceptTCP(): #when server acts as a server to other servers
    global local_list1, local_list2, local_list3 
    print ("accept TCP thread")
    LOCALHOST = get_ip_address('wlan0')
    PORT = 12346
    servertcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    servertcp.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    servertcp.bind((LOCALHOST, PORT))
    print("Server started")
    #print("Waiting for client request..")
    while True:
        servertcp.listen(1)
        clientsock, clientAddress = servertcp.accept()
        try:
            l=[]
            l.append(clientAddress)
            l.append(clientsock)
            t2 = threading.Thread(target= ClientThread, args=(l))
            t2.start()
        except:
            print("Error: thread ClientThread") 

#Establish tcp socket with client or a server acting as a client
def ClientThread(clientAddress,clientsocket):
    global local_list1, local_list2, local_list3, Server_1, Server_2 
    print ("ClientThread for TCP")
    csocket = clientsocket
    print ("New connection added: ", clientAddress)
    serverName = csocket.recv(7)
    print("what1")
    print(Server_1)
    if serverName==b'Server1':
        Server_1=clientAddress[0]
    if serverName==b'Server2':
        Server_2 =clientAddress[0]
    print("what2")
    print(Server_2)
    csocket.sendall(bytes("Server3",'UTF-8'))
    if serverName==b'Server1' or serverName==b'Server2':
        try:
            l=[]
            l.append(clientsocket)
            t2 = threading.Thread(target= constantSendingList, args=[clientsocket])
            t2.start()

        except:
            print("Error: initiate") 
        while True:
            data = csocket.recv(2048)
            if data == 'create':
               csocket.tcpsock.sendall(bytes("gimme",'UTF-8'))
            if serverName==b'Server1':
                gotit = pickle.loads(data)
                local_list1 = gotit
                for x in range(len(local_list1)):
                    print(local_list1[x].name)
            if serverName==b'Server2':
                gotit = pickle.loads(data)
                local_list2 = gotit
                for x in range(len(local_list2)):
                    print(local_list2[x].name)                
                
#server acting as a client to maintain single system image
    if serverName==b'Client': 
        msg = ''
        while True:
            try:
                data = csocket.recv(2048) 
                msg = data.decode()   
                if msg[0:8]=='download' :
                    val=findFile(msg[9:],csocket)
                if msg[0:4]=='show' :
                    full_list = []
                    if local_list1:  
                        full_list.extend(local_list1)
                    if local_list2:
                        full_list.extend(local_list2)
                    full_list.extend(local_list3)
                    full = unique(full_list)
                    localdir = pickle.dumps(full) 
                    csocket.send(localdir)

                if msg[0:4]=='edit' :
                    val=findFile(msg[5:],csocket)
                    #recieving edited version of file
                    in_data =  csocket.recv(2048)
                    thename= msg[5:]
                    with open("/dir/path/"+thename, 'wb') as f: #replace with path same as folder included in single system image
                        f.write(in_data)
                    for i in range(len(local_list3)):
                        if local_list3[i].name==thename:
                            IP=local_list3[i].servercopy
                    if IP=='Server_1':
                        replication(thename, Server_1)
                    if IP=='Server_2':
                        replication(thename, Server_2)

                if msg[0:6] == 'create':
                    in_data =  csocket.recv(2048)
                    thename= msg[7:]
                    with open("/dir/path/"+thename, 'wb') as f: #replace with path same as folder included in single system image
                        f.write(in_data)
                    replication(thename)

                if msg[0:6] == 'delete':
                    thename= msg[7:]
                    this_one = deletion(thename)
                    print(this_one)
                    if this_one == "this":
                        csocket.send(bytes((this_one),'UTF-8'))                    
                    if this_one == "Server_1":
                        csocket.send(bytes(("Connect to"+ Server_1),'UTF-8'))                    
                    if this_one == "Server_2":
                        csocket.send(bytes(("Connect to"+ Server_2),'UTF-8'))

                if msg[0:9] == 'Repdelete':
                    thename= msg[10:]
                    os.remove("/dir/path/"+thename) #replace with path same as folder included in single system image
                    for i in range(len(local_list3)):
                        if local_list3[i].name==thename and local_list3[i].servercopy== '0':  
                            del local_list3[i]                  
                    csocket.sendall("deleted".encode())
                    for i in range(len(local_list3)):
                        if local_list3[i].name==thename and local_list3[i].servercopy== 'Server_1':  
                            del local_list3[i]                  
                    csocket.sendall("deleted".encode())
                    for i in range(len(local_list3)):
                        if local_list3[i].name==thename and local_list3[i].servercopy== 'Server_2':  
                            del local_list3[i]                  
                    csocket.sendall("deleted".encode())

                if msg[0:9] == 'Repcreate':
                    csocket.sendall("hi".encode())
                    in_data =  csocket.recv(2048)
                    thename= msg[10:]
                    with open("/dir/path/"+thename, 'wb') as f: #replace with path same as folder included in single system image
                        f.write(in_data)
                    #send ack and wait for its name
                    #make node here
                    if clientAddress[0]== Server_1:
                        rep="Server_1"
                    if clientAddress[0]== Server_2:
                        rep="Server_2"
                    local_list3.append(fileNode(thename, "Server_3", rep, "0", "0"))
                    print(thename)
                    csocket.sendall("hi2".encode())
                if msg[0:3]=='bye':
                    print("breaking")
                    break
                else:
                    continue
                break

            except IOError as e:
                if e.errno == errno.EPIPE:
                    print("broken")
                    local_list1 = []
                    local_list2 = []
                    break        
            print (msg)
            csocket.close()

#Deletes file in local system
#Checks where else on other servers it exists
#Calls repdelete on the other server, to get them to delete their local copy too             
def deletion(thename):   
    global Server_2, local_list1,local_list2,local_list3 , Server_1
    print(thename)
    for i in range(len(local_list3)):
        if local_list3[i].name==thename and local_list3[i].servercopy== '0':
            print("delete 0")
            os.remove("/dir/path/"+thename) #replace with path same as folder included in single system image
            del local_list3[i]
            return("this")
        if local_list3[i].name==thename and local_list3[i].servercopy== 'Server_1':
            print("del copy1")
            a = i
            if Server_1 == '': 
                print(Server_1)
                local_list3[i].quarantine = "1"
            else:
                SERVER= Server_1  
                print(SERVER)
            PORT = 12346
            tcpsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            tcpsock.connect((SERVER, PORT))
            tcpsock.sendall(bytes("Client",'UTF-8'))
            in_data =  tcpsock.recv(1048)  #recieve server name
            tcpsock.sendall(bytes("Repdelete "+thename,'UTF-8'))
            blah=tcpsock.recv(1048) #deleted recieved here
            os.remove("/dir/path/"+thename) #replace with path same as folder included in single system image
            del local_list3[a]
            return("this")
        if local_list3[i].name==thename and local_list3[i].servercopy== 'Server_2':
            print("del copy3")
            a = i
            if Server_2 == '': 
                print(Server_2)
                local_list3[i].quarantine = "1"
            else:
                SERVER= Server_2  
                print(SERVER) 
            PORT = 12346
            tcpsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            tcpsock.connect((SERVER, PORT))
            tcpsock.sendall(bytes("Client",'UTF-8'))
            in_data =  tcpsock.recv(1048)  #recieve server name
            tcpsock.sendall(bytes("Repdelete "+thename,'UTF-8'))
            blah=tcpsock.recv(1048) #deleted recieved here
            os.remove("/dir/path/"+thename) #replace with path same as folder included in single system image
            del local_list3[a]
            return("this")

    for i in range(len(local_list1)):
        if local_list1[i].name==thename:
            return('Server_1')

    for i in range(len(local_list2)):
        if local_list2[i].name==thename: 
            return('Server_2')
    return('Not Found')


#Replicates file created on this server's local file system, on another server
#chooses the other server on the basis of least number of files
#Assumption: All files to be roughly of same size
def replication(thename, IP=None):
    global Server_2, local_list1,local_list2,local_list3 , Server_1
    #check where to replicate
    rep=""
    temp=""
    #for x in range(len(local_list2)):
        #print(local_list2.name)
    if IP==None:
        if len(local_list1)>len(local_list2):
            rep="Server_1"
            if Server_1=='':
                temp=Server_2
                print(temp)
            else:
                temp=Server_1
                print(temp)
        if len(local_list1)<len(local_list2):
            rep="Server_2"
            if Server_2=='':
                temp=Server_1
                print(temp)
            else:
                temp=Server_2
                print(temp)
        print("in the rep thread")
        #print(Server_3)
        local_list3.append(fileNode(thename, "Server_3", rep, "0", "0"))
        SERVER=temp
        print("hi")
        print(SERVER)
        print("hi2")
    else:
        SERVER=IP
    print(SERVER)
    PORT = 12346
    tcpsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    tcpsock.connect((SERVER, PORT))
    tcpsock.sendall(bytes("Client",'UTF-8'))
    in_data =  tcpsock.recv(1048)  #server name
    tcpsock.sendall(bytes("Repcreate "+thename,'UTF-8'))
    blah=tcpsock.recv(1048)#hi
    creating = open("/dir/path/"+thename).read() #replace with path same as folder included in single system image
    tcpsock.sendall(creating.encode())
    blah=tcpsock.recv(1048)#hi2
    tcpsock.sendall("bye".encode())


#Server checks if it has file in its local filesystem, if not, searches which 
#server has it and reconnects client to that server. 
#if no file found on any server, informs client that no such file exists.
def findFile(fileName,c):
    global local_list1, local_list2, local_list3, Server_1, Server_2
    test=1
    print(fileName)
    for i in range(len(local_list3)):
        if local_list3[i].name==fileName:
            myfile = open('/dir/path/'+fileName, "rb") #replace with path same as folder included in single system image
            c.sendall(bytes("File",'UTF-8'))
            c.send(myfile.read(2048))
            test=0
            return
        else:
            test=2
    #others
    if test ==2:        
        for i in range(len(local_list1)):    
            if local_list1[i].name==fileName:
                c.send(bytes(("Connect to"+ Server_1),'UTF-8'))
                test=0
                return
            else:
                test=3
    if test==3:
        for i in range(len(local_list2)):    
            if local_list2[i].name==fileName:
                c.send(bytes(("Connect to"+ Server_2),'UTF-8'))
                test=0
                return
            else:
                test=1
    if test==1:
        c.send(bytes("Not Found",'UTF-8'))

#servers send each other their updated list of files every 10 seconds
#overhead     
#system image can be inconsistent for a few seconds list hasn't been sent,
# client makes a change in files and another client accesses the file system    
def constantSendingList(cl):
    print("constant")
    global local_list1, local_list2, local_list3 
    while True:
        try :
            csocket=cl
            localdir = pickle.dumps(local_list3)
            csocket.send(localdir)
        except pickle.UnpicklingError as e:
    		# normal, somewhat expected
            continue
        except (AttributeError,  EOFError, ImportError, IndexError) as e:
    	# secondary errors
            local_list1 = []
            local_list2 = []
            print(traceback.format_exc(e))
            #continue
        except Exception as e:
            # everything else, possibly fatal
            local_list1 = []
            local_list2 = []
            print(traceback.format_exc(e))
            continue
        except csocket.error as e:
            print('Broken Pipe Error1')
            local_list1 = []
            local_list2 = []
        finally : 
            time.sleep(10)      

def recUDP():   # Acting like a client to other servers
    global local_list1, local_list2, local_list3 
    print("rec udp starts")
    test=1
    #make new connections from the udp you recieve
    message = b'any one there from Server3?'
    multicast_group = ('224.1.1.3', 10000)

# Create the datagram socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(10)
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
# Look for responses from all recipients
    try:
        sent = sock.sendto(message, multicast_group)
        while True: 
            try:
                data, server = sock.recvfrom(1024)
            except socket.timeout:
                print('')
            else:
                print('received {!r} from {}'.format(data, server))
                if data!='Server' and  server[0]!=get_ip_address('wlan0'):    
                    try:
                        l=[]
                        l.append(server[0])
                        t2 = threading.Thread(target= initiateTCP, args=l)
                        t2.start()
                    except:
                        print("Error: initiate") 
    finally:
        print('closing socket')
        sock.close()

def initiateTCP(ip):
    global local_list1, local_list2, local_list3, Server_1, Server_2
    print("initiate TCP Thread")
    SERVER =ip
    PORT = 12346
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((SERVER, PORT))
        client.sendall(bytes("Server3",'UTF-8'))
        serverName = client.recv(7)
        print(serverName)
        try:
            t2 = threading.Thread(target= constantSendingList, args=[client])
            t2.start()
        except:
            print("Error: thread constantSendingList") 
        while True:
            data = client.recv(4096)
            if serverName== b'Server1':
                Server_1=ip
                gotit = pickle.loads(data)
                local_list1 = gotit
                for x in range(len(gotit)):
                    print(local_list1[x].name)
            if serverName==b'Server2':
                Server_2=ip
                gotit = pickle.loads(data)
                local_list2 = gotit
                for x in range(len(gotit)):
                    print(local_list2[x].name)
    except socket.error as e:
        print('Broken Pipe Error2')
        local_list1 = []
        local_list2 = []
    


#main thread

try:
   t6 = threading.Thread(target= onUpdate)
   t6.start()
except:
   print("Error: Cannot start onUpdate thread")
try:
   t2= threading.Thrertiad(target= sendingUDP)
   t2.start()
except:
   print("Error: Cannot start sendingUDP thread")
try:
   t4 = threading.Thread(target= acceptTCP)
   t4.start()
except:
   print("Error: Cannot start acceptTCP thread")
try:
   t5 = threading.Thread(target= recUDP)
   t5.start()
except:
   print("Error: Cannot start recUDP thread")


