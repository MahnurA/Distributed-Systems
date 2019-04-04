import socket, struct, sys, errno, pickle, io, sys, os
from tkinter import *
from tkinter.filedialog   import asksaveasfilename

class fileNode(object):
    def __init__(self, name=None, server=None, servercopy=None, replication=None,quarantine=None ):
        self.name = name
        self.server = server
        self.servercopy = servercopy
        self.replication = replication
        self.quarantine = quarantine

def unique(input):
  output = []
  for x in input:
    if x not in output:
      output.append(x)
  return output

def saveas():
    global text  
    global thename
    t = text.get("1.0", "end-1c")
    savelocation=asksaveasfilename()
    file1=open(savelocation, "w+")
    file1.write(t)
    file1.close()
    thename=savelocation

def open_file(input_file_name):
    if input_file_name:
        global file_name
        file_name = input_file_name
        root.title('{}'.format(os.path.basename(file_name)))
        text.delete(1.0, END)
        with open(file_name) as _file:
            text.insert(1.0, _file.read())
message = b'Any server up?'
multicast_group = ('224.1.1.3', 10000)

redirect = ''
command=""
# Create the datagram socket for UDP
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.settimeout(10)

ttl = struct.pack('b', 1)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)
flag = 0
tcpflag = 0
commandFlag=0
text=""
try:
    while True:
        try:
	    # Send data to the multicast group
            print('Connecting...')
            sent = sock.sendto(message, multicast_group)
            #print('waiting to receive')
            data, server = sock.recvfrom(1024)
        except socket.timeout:
            print('timed out, no more responses')
            break
        else:
            #print('received {!r} from {}'.format(data, server))
            print('Established Connection')
            if tcpflag == 1:
                SERVER = redirect
                tcpflag = 0
                commandFlag=1           
                redirect="" 
            else :
                SERVER = server[0]    
            PORT = 12346 #arbitrarily set
            try :
                tcpsock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
                tcpsock.connect((SERVER, PORT))                
                tcpsock.sendall(bytes("Client",'UTF-8'))
                in_data =  tcpsock.recv(1048)  #recieve server name
                #print(in_data)
                while True: 
                    #ask human user what it wants                     
                    if commandFlag==0:
                        print("Please enter input:")
                        out_data = input()
                    if commandFlag==1:
                        out_data=command
                        commandFlag=0
                    if out_data=='bye':
                        print('Exiting')
                        tcpsock.close()
                        flag=1
                        break
                    tcpsock.sendall(out_data.encode())
                    #in_data =  tcpsock.recv(4096)
                    if out_data[0:8]=='download':
                        in_data =  tcpsock.recv(1024)
                        if in_data== b'File':
                            in_data =  tcpsock.recv(2048)
                            with open(out_data[9:], 'wb') as f:
                                f.write(in_data)
                            root=Tk()
                            text=Text(root)
                            text.grid()
                            open_file(out_data[9:])
                            button=Button(root, text="Save", command=saveas) 
                            button.grid()
                            root.mainloop()
                        dec_data=in_data.decode()
                        print(dec_data)
                        if dec_data[0:10]=='Connect to': #reconnecting to the server that has the file without human user knowing
                            #print("reconnecting")
                            redirect = dec_data[10:]
                            tcpflag=1
                            command=out_data
                            break
                        if in_data== b'Not Found':
                            print("Your file was not found")
                    if out_data[0:4]=='edit':
                        in_data =  tcpsock.recv(1024)
                        
                        if in_data== b'File':
                            in_data =  tcpsock.recv(2048)
                            print(in_data)
                            with open(out_data[5:], 'wb') as f:
                                f.write(in_data)
                            print(in_data)
                            root=Tk()
                            text=Text(root)
                            text.grid()
                            open_file(out_data[5:])
                            button=Button(root, text="Save", command=saveas) 
                            button.grid()
                            root.mainloop()
                            creating = open(out_data[5:]).read()
                            tcpsock.sendall(creating.encode())
                            print("file successfully created")
                        dec_data=in_data.decode()
                        print(dec_data)
                        if dec_data[0:10]=='Connect to':
                            #print("reconnecting")
                            redirect = dec_data[10:]
                            tcpflag=1
                            command=out_data
                            break
                        if in_data== b'Not Found':
                            print("Your file was not found")

                    if out_data[0:6]=='delete':
                        in_data =  tcpsock.recv(1024)
                        print(in_data)
                        dec_data=in_data.decode()
                        print(dec_data)
                        if dec_data[0:10]=='Connect to':
                            #print("reconnecting")
                            redirect = dec_data[10:]
                            tcpflag=1
                            command=out_data
                            break
                        if in_data== b'Not Found':
                            print("Your file was not found")

                    if out_data == 'show':
                        in_data =  tcpsock.recv(4096)
                        gotit = pickle.loads(in_data)
                        ordered=[]
                        for x in range(len(gotit)):
                            ordered.append(gotit[x].name)
                        full=unique(ordered)
                        for x in range(len(full)):
                            print(full[x])
                           
                    if out_data[0:6]=='create':
                        root=Tk()
                        text=Text(root)
                        text.grid()
                        button=Button(root, text="Save", command=saveas) 
                        button.grid()
                        root.mainloop()
                        print(thename)
                        creating = open(thename).read()
                        tcpsock.sendall(creating.encode())
                        print("file created")
                                           
                if flag==1 :
                    break
                            
            except socket.error as e:
                print('Broken Pipe Error.Establish new TCP socket')
        

finally:
    print('Cannot establish connection')
    print('exiting now')
    sock.close()
