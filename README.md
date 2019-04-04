# Distributed-Systems

This distributed file system utilizes Upload/ Download model and semantics of immutable files to give a single system image to the user. 

Skip the project explanation below and jump to 'Getting started' on notes how to run this. 

## Servers

### Making local files existence globally available 

The servers at startup, build the single system image which they then show the client, by exchanging the files each has on its local directory. This is done through traversing a part of its directory that has been exposed, and picking up leaf nodes  such that only files within folders are picked up, and not folders themselves. Here, picking up implies getting the name of the target object. As each file name is returned, a node is created and the name is added as part of an attribute of a node. Other attributes in the node are namely, “server” to indicate on which server was the file first created on, “copy,” which server is the file replicated on, and a “replication” flag to show has the file been replicated or not.
Each node has these attributes and together they make a structure that is a list of nodes. This list of nodes is appended to the nth index of an empty list. Each server carries this activity out when it starts and appends its own list to its corresponding place on an empty list, e.g Server 2 will append the list of nodes to the first index of the empty list, this will later become the global list, that contains the names of all the files on all servers combined. 

### Server to Server communication

This is followed by calling a function that enables the server to join a multicast group so that its IP can then be made known to other servers. All servers join the same multicast group so they can then get to know each other's IP address. Upon getting others' addresses, socket connections over TCP are established amongst each other. Each Server thus has a socket connection established with every server in the multicast group. This completes the server to server line of communication. 

These sockets are then used to exchange the list of nodes containing names of the files present locally on every Server's system. When a server receives another server's list of nodes it saves it as local_listA, where A is the number of the server that was assigned to it and harcoded in every server's code. These local lists of all the servers are updated every time a file present locally is created or deleted. Each server thus keeps sending its list of nodes periodically over the sockets to all other servers it is connected to, to ensure that every server has the latest information on which server has what file.

A server when receives an incoming TCP connection first determines whether the the incoming connection is that from another server or from a client by checking what's sent first, 'Server' or 'Client' respectively. This determines how further communication would proceed. Also, as each new connection is requested the server accepts and makes a thread for the newly arrived client. This way multiple clients are handled, leaving the server to accept more connections and handle/process other requests.

### Client to Server communication

#### Accessing and creating files

Every server has functionality that enables it to search whether a specific file requested by the client is present locally or not. If it is present, it's downloaded by the client. If not, then the server determines on which server it is and subsequently redirects the client to it. Files can be created, edited, downloaded, and replicated. If a client requests a file to be created of a name that already exists, the client is advised to use another name and no file is created unless a unique name is chosen. To edit a file, since this system implements immutable semantics, editing of sorts can be done through downloading a file, opening it in Tkinter, making the necessary changes and re-uploading it to the server. A file is created on the server the client is at that moment of creation request, connected to. 

#### Replication 

Replication of each file is done after it's creation. A file is replicated on two servers out of three, excluding the one with the primary copy. The primary copy exists and is first created on the server that the client is connected to, that server then traverses the structure it has containing all the filenames to see which server has the least number of files. The server with the lesser number of files then gets chosen as the server on which that file is replicated. If both remaining server's have an equal number of files, the one assigned a lower number in its identifier then has the file replicated on it. This is done by the server with the primary copy calling the create file function much like a client would on the other server through the server to server socket connection. When a replicated file is updated, similar procedure takes place, except for the first part where a server needs to be chosen, that is replaced by traversing through the structure to find out where else the file has been replicated and then calling create on those servers only. 
Assumption: Files are small and approximately similar in size to each other. 

#### Editing a file

Editing of a file in this architecture is done as it would generally be done in an immutable file system. The user is given the illusion of editing a file, while its downloaded, edited and then re-uploaded to the server, thus overwriting the copy the server has with the new version. Since each file is replicated, the severcopy attribute is checked in the node of the file being edited to see where it has been replicated. And here, the server whose file has now been overwritten with the new version and thus has the local copy, that server calls create on the server that needs the updated version of the file. This way, the other server's file is also overwritten with the new version.

#### Deleting a file 

Deletion of a file, if replicated, happens in the following way; the server receives the name of the file that is to be deleted from the client, checks if it has it or it's copy, or not. This is checked by traversing through the other server's lists and checking if the file name exists, if it exists, the server assumes that other server whose list was being traversed, has the file. If not it redirects client to connect to that server and send it the same command. If it does have the file however, the server, checks the file's 'servercopy' attribute, it establishes a connection to the server that has the copy, and asks it to delete its copy, after that has been done, the server delete's its file also.

#### Saving state

Also to ensure consistency and decrease chances of loss of information regarding which file is replicated where (info. Saved in the attributes of nodes within the list structure), when the list is updated, the attributes of each node of the files present locally are dumped in a file. This is to prevent loss of attributes' info of a file replicated on two servers, in the scenario when both those servers crash or go down. If dumping of attributes isn't done, if only one of the server's on which the file is replicated on, re-starts, it will not be able to set the replicated flag of such a file as 'on' when rebuilding its list of nodes, since the server its replicated on would still be down, thus giving the illusion that the file has not been replicated. So after a crash, attributes will be populated from the dump file. 

## Clients

Clients establish connection with the server through joining a multicast group and searching if any server is up or not. On the availability of any server, the client gets the IP address by UDP, will immediately connect to it, and establish a socket connection over TCP. The client as mentioned above, can create, delete and download any file available on the system. When the client first connects, it receives all the names of files available on all the servers combined as a list. This list can be requested again later when needed. If a client disconnects from the server it's been connected to, it automatically reconnects to any other server available and it's last request is replayed to the newly connected to server without any input from the user, if no other server is available, a message conveying that is displayed. 

If a client has sent a request to download a file that is not available on the server that it is presently connected to then the server sends back an IP address of a server which does have that file. The client without any indication to the end user will take the IP address returned to it, disconnect from the server it is connected to currently, and connect to the server that has the file. The request to download is also sent, and the client then successfully receives the requested file. 

### List of commands for the user: 

show – To show a list of the files available on the system
create [filename] – To create a file of the given name. 
download [filename] – To download a file of the given name. 
edit [filename] - To edit a file.
bye – To disconnect from the server 

## Getting Started

Download Server1, Server2, Server3 and client files. Put all three servers on different computers. All computers with the server files on them must be connected to the same LAN. Client file can be copied to make as many clients as required. Client file can also be run on the same machine as a one of the servers, provided they're run on different terminals and saved in different directiories that are not in each other's path.

Replace /dir/path/ in all server files as directed in the comments of each file. 

## Pre-requisites

Python3 must be installed. 

And that's it!




