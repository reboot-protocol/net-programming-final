import socket
import select
import random
import threading
import time

HOST = '127.0.0.1'
PORT = 12344

event_finished_game = threading.Event()


def finished_game(player_list,room_list,msg_queue):
    while (1):
        for msg in msg_queue.finised_queue :
            player_list.finised_game(msg)
class UniqueRandom:
    def __init__(self, start, end):
        self.pool = list(range(start, end))
        random.shuffle(self.pool)

    def get(self):
        if not self.pool:
            raise ValueError("No more unique numbers left!")
        return self.pool.pop()
class player_progess():
    def __init__(self,fd):
        self.socket= fd
        self.count= 0
        self.time = 0
    def increment(self):
        self.count = self.count + 1
    def add_time(self,time_finished):
        self.time = time_finished
    def finished(self):
        self.socket.sendall(b"time up !!!")
    def point_cal(self):
        base = 100
        speed_bonus = max(0, int(100 - self.time))
        guess_penalty = self.count * 5
        return max(0, base + speed_bonus - guess_penalty)
class game_progess():
    def __init__(self,fd):
        self.fd_list = []
        for sock in fd:
            self.fd_list.append(player_progess(sock))
    def incre(self,fd):
        for sock in self.fd_list:
            if sock.socket == fd:
                sock.increment()
            break
    def time(self,fd,time):
         for sock in self.fd_list:
            if sock.socket == fd:
                sock.add_time(time)
            break
    def time_up(self):
        for player in self.fd_list:
            player.finished()
    def announce_results(self):
    # Step 1: Create a list of tuples (score, player)
        scores = []
        for player in self.fd_list:
            score = player.point_cal()
            scores.append((score, player))

        # Step 2: Sort by score descending
        scores.sort(reverse=True, key=lambda x: x[0])

        # Step 3: Send rank and score to each player
        for rank, (score, player) in enumerate(scores, start=1):
            message = f"Game over! Your score: {score}. Your rank: {rank}."
            try:
                player.socket.sendall(message.encode())
            except Exception as e:
                print(f"Failed to send to client: {e}")

def is_convertible_to_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False
class game_message():
    def __init__(self,client_socket,message,roomid):
        self.socket = client_socket
        self.msg = message
        self.id  = roomid
class game_message_queue():
    def __init__(self):
        self.queue = []
        self.finised_queue = []
        self.leave_queue = []
    def add(self,msg,client_socket,rid):
        self.queue.append(game_message(client_socket,msg,rid))
        print("add mess to queue")
    def remove_msg(self,msga,client_socket,rid):
        for msge in self.queue:
            if msge.socket == client_socket:
                if msge.msg == msga:
                    if msge.id == rid:
                        self.queue.remove(msge)
    def add_finished_msg(self,roomid):
        self.finised_queue.append(roomid)
    def add_leave_queue(self,client_socket):
        self.leave_queue.append(client_socket)
def game_room_handle(roomid,message_queue,sockfd_list):
    game = game_progess(sockfd_list)
    result = random.randint(1,100)
    print(result)
    countdown = 30
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        remaining = countdown - elapsed

        if remaining <= 0:
            print("Time's up!")
            break
        for msge in message_queue.queue:
            if msge.id == roomid:
                if is_convertible_to_int(msge.msg) == False:
                    msge.socket.sendall(b"your result is not valid, pls go with an interger")
                    continue
                data = int(msge.msg)
                if data < result:
                    msge.socket.sendall(b"your guess is smaller than the final result")
                    game.incre(msge.socket)
                    message_queue.remove_msg(msge.msg,msge.socket,roomid)
                if data > result:
                    msge.socket.sendall(b"your guess is bigger than the final result")
                    game.incre(msge.socket)
                    message_queue.remove_msg(msge.msg,msge.socket,roomid)
                if data == result:
                    msge.socket.sendall(b"you guess is right !!!!")
                    game.incre(msge.socket)
                    game.time(msge.socket,countdown-remaining)
                    message_queue.remove_msg(msge.msg,msge.socket,roomid)
    game.time_up()
    game.announce_results()
    message_queue.add_finished_msg(roomid)


class player():
    def __init__(self,client_socket,addr):
        self.sock = client_socket
        self.address = addr
        self.in_game = False
        self.in_room = False
        self.host = False
        self.room_id = ""
    def out(self):
        print(f"{self.address}: room id {self.room_id} {self.in_room}")
class playerlist():
    def __init__(self):
        self.list = []
        self.size = 0
    def add(self,user):
        self.list.append(user)
    def leave_room(self,client_socket):
        for client in self.list:
            if client.sock == client_socket:
                client.in_room = False
                client.in_game = False
                print("a player just leave the room")
                client.room_id = ""
    def roomdisban(self,roomid):
        for client in self.list:
            if client.room_id == roomid:
                client.in_room = False
                client.in_game = False
                client.roomid = ""
    def finised_game(self,rid):
        for player in self.list :
            if player.room_id == rid:
                player.in_game = False
    def check_create_room(self,client_scoket):
        for clients in self.list:
            if clients.sock == client_scoket:
                if clients.in_room == False:
                    clients.in_room = True
                    clients.host = True
                    return 1
                else:
                    return -1
    def check_join_room(self,client_socket):
        for clients in self.list:
            if clients.sock == client_socket:
                if clients.in_room == False:
                    return 1
                else:
                    return -1
    def join_room(self,client_socket,roomid):
        for clients in self.list:
            if clients.sock == client_socket:
                clients.room_id = roomid
                clients.in_room = True
                
    def check_host(self,client_socket):
        for clients in self.list:
            if clients.sock == client_socket:
                if clients.host == True:
                    return clients.room_id
                else:
                    return -1
    def get_room_id(self, client_socket):
        for client in self.list:
            if client.sock == client_socket:
                return client.room_id
        return None

    def start_game(self,id):
        for clients in self.list:
            if clients.room_id == id :
                clients.in_game = True
                print(f"Player {clients.address} is now in game.")
    def check_ingame(self,client_socket):
        for clients in self.list:
            if clients.sock == client_socket:
                if clients.in_game == True:
                    return 1
                else:
                    return -1
    def print(self):
        for clients in self.list:
            clients.out()
class gameroom():
    def __init__(self,host,iden):
        self.host_sock = host
        self.guest_sock =[]
        self.capacity = 4
        self.id = iden
        self.state = -1 # -1 : not ready, 0: ready, 1: game in progess
    def addplayer(self,player):
        self.guest_sock.append(player)
    def fdlist(self):
        temp =[]
        temp.append(self.host_sock)
        for sock in self.guest_sock:
            temp.append(sock)
        return temp
    def roomleave(self,clientsocket):
        for client in self.guest_sock:
            if client == client_socket:
                self.guest_sock.remove(client)
class roomlist():
    def __init__(self):
        self.rlist = []
        self.length = 0
    def leaveroom(self,rid,client_socket):
        for room in self.rlist:
            if room.id == rid:
                room.roomleave(client_socket)  
    def add(self,room):
        self.rlist.append(room)
    def addguest(self,guest_socket,room_id):
        for room in self.rlist:
            if room.id == room_id:
                room.addplayer(guest_socket)
    def socklist(self,room_id):
        for room in self.rlist:
            if room.id == room_id:
                temp = room.fdlist()
                return temp
    def disband(self,room_id):
        for room in self.rlist:
            if room.id == room_id:
                self.rlist.remove(room)
    
# Create server socket
player_list= playerlist()
room_list= roomlist()
ur = UniqueRandom(0, 10)
msg_queue = game_message_queue()
threading.Thread(target=finished_game,args= (player_list,room_list,msg_queue,)).start()
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen()
server_socket.setblocking(False)  # Make server socket non-blocking

# List of sockets to monitor for incoming data
sockets_list = [server_socket]
clients = {}

print(f"Server listening on {HOST}:{PORT}...")

while True:
    # Use select to get sockets ready for reading
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            # New connection
            client_socket, client_address = server_socket.accept()
            client_socket.setblocking(False)
            sockets_list.append(client_socket)
            clients[client_socket] = client_address
            print(f"Accepted new connection from {client_address}")
            player_list.add(player(client_socket,client_address))

        else:
            try:
                data = notified_socket.recv(1024)
                if data:
                    print(f"Received from {clients[notified_socket]}: {data.decode().strip()}")
                    if player_list.check_ingame(notified_socket) == 1:
                        roomid = player_list.get_room_id(notified_socket)
                        print(f"request check room id {roomid}")
                        if roomid is not None:
                            msg_queue.add(data, notified_socket, roomid)
                            
                    if (data.decode().strip() == "/leave room"):
                        if player_list.check_join_room(notified_socket) == -1:
                            roomid = player_list.get_room_id(notified_socket)
                            player_list.leave_room(notified_socket)
                            room_list.leaveroom(roomid,notified_socket)
                        else:
                            notified_socket.sendall(b"you are not in any room")

                    if (data.decode().strip() == "/disban"):
                        roomid = player_list.check_host(notified_socket)
                        if roomid == -1:
                            notified_socket.sendall("you are not the host to do that")
                        else:
                            player_list.roomdisban(roomid)
                    if (data.decode().strip() == "/create room"):
                            temp = player_list.check_create_room(notified_socket)
                            if temp == 1:
                                roomid = ur.get()
                                room_list.add(gameroom(notified_socket,roomid))
                                player_list.join_room(notified_socket,roomid)
                                msg = "success create a game room " + str(roomid)
                                notified_socket.sendall(msg.encode())
                            if temp == -1: 
                                notified_socket.sendall(b"you already in a game room")
                    if (data.decode().strip() == "/startgame"):
                        roomid = player_list.check_host(notified_socket)
                        if roomid == -1:
                            notified_socket.sendall(b"you are not the host")
                        else:
                            player_list.start_game(roomid)
                            temp = room_list.socklist(roomid)
                            player_list.print()
                            threading.Thread(target=game_room_handle,args= (roomid,msg_queue,temp,)).start()

                    parts = data.decode().strip().split()
                    if(parts[0] == "/joinroom"):
                        print(f"a clients just join{parts[1]}")
                        if player_list.check_join_room(notified_socket) == 1:
                            room_id = int(parts[1])
                            print(f"{room_id}")
                            room_list.addguest(notified_socket,room_id)
                            player_list.join_room(notified_socket,room_id)
                            notified_socket.sendall(b"joined successfully")
                        else:
                            notified_socket.sendall(b"you already in a room")

                else:
                    # No data — client disconnected
                    print(f"Closed connection from {clients[notified_socket]}")
                    sockets_list.remove(notified_socket)
                    del clients[notified_socket]
                    notified_socket.close()
            except ConnectionResetError:
                print(f"Connection reset by {clients[notified_socket]}")
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                notified_socket.close()

    for err_socket in exception_sockets:
        sockets_list.remove(err_socket)
        err_socket.close()
        del clients[err_socket]
