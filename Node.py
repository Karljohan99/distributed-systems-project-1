import grpc
from concurrent import futures
import time
import sys
import datetime
import re
from tictactoe import TicTacToe
import tictactoe_pb2
import tictactoe_pb2_grpc

MAX_NODES = 3
LOCALHOST = True

class TicTacToeServicer(tictactoe_pb2_grpc.TicTacToeServicer):
    def __init__(self, id):
        #self.id = int(sys.argv[1])
        self.id = id
        self.date_time = datetime.datetime.utcnow()
        self.games = []
        self.coordinator = False
        self.leader_ID = 0
        self.game_ID = None
        self.moves = ["X", "O"]

    def ProcessCommand(self, request, stub, game):
        cmd = request.command
        if not check_command_correctness(cmd):
            return (False, "[Command] - Unknown command")
        cmd = cmd.split(" ")
        base_cmd = cmd[0].strip()
        match base_cmd:
            case "Set-symbol":
                players = game.get_players()
                player_index = players.index(request.player_id)
                if self.moves.index(game.get_move()) != player_index:
                    return (False, f"It's not your turn!")
                move = cmd[1].split(',')
                pos = int(move[0].strip())
                player = move[1].strip()
                if game.get_move() != player:
                    return (False, f"Not your symbol!")
                move_made = game.make_move(pos, player)
                time_sync(self.id)
                if move_made:
                    game.next_move()
                    return (True, f"Move done! Current board: {game.get_board()}")
            case "List-board":
                return (False, f"Current board: {game.get_board()}")
            case "Set-node-time":
                set_node = int(cmd[1].split('-')[1])
                h, m, s = cmd[2].split(':')
                #time_adjustment = str(int(h) * 3600 + int(m) * 60 + int(s))
                new_time = str(datetime.date.today()) + "-" + str(cmd[2])
                if set_node != request.player_id and request.player_id == self.leader_ID:
                    with grpc.insecure_channel(f'localhost:{request.player_id}' 
                                               if LOCALHOST else f'192.168.76.5{request.player_id}:50051') as channel:
                        stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                        stub.SetDateTimeCoordinator(
                            tictactoe_pb2.DateTimeMessageCoordinator(node_ID=set_node, adjustment="", time=new_time))
                        return (False, "Time adjusted.")
                elif set_node == request.player_id:
                    with grpc.insecure_channel(f'localhost:{request.player_id}' 
                                               if LOCALHOST else f'192.168.76.5{request.player_id}:50051') as channel:
                        stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                        stub.SetDateTime(tictactoe_pb2.DateTimeMessage(adjustment="", time=new_time))
                        return (False, "Time adjusted.")
                else:
                    print(f"[Command] - Only coordinator can change other node's internal clock.")
                pass
            #case _:
            #print("[Command] - Unknown command")

        return (False, "[Command] - Unknown command")

    
    def Coordinator(self, request, context):
        game = self.games[request.game_id]

        move_made, msg = self.ProcessCommand(request, None, game)
        
        winner = game.check_winner_new()
        if winner is not None:
            if winner == "draw":
                win_msg = 'Nobody won, draw!'
            else:
                win_msg = f'{winner} won!'
            return tictactoe_pb2.CoordinatorResponse(msg=f"{msg} {win_msg}")
        
        if self.id == request.player_id:
            return tictactoe_pb2.CoordinatorResponse(msg=msg)
        
        players = game.get_players()
        player_index = players.index(request.player_id)
        other_player = players[1-player_index]
        if move_made:
            with grpc.insecure_channel(f'localhost:{other_player}' 
                                       if LOCALHOST else f'192.168.76.5{other_player}:50051') as channel:
                stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                stub.Player(tictactoe_pb2.PlayerMessage(
                    next_move=game.get_move(),
                    player_symbol = self.moves[1-player_index],
                    board=game.get_board(),
                    start=False,
                    game_id=request.game_id,
                    opponent=players[1-player_index]))
        return tictactoe_pb2.CoordinatorResponse(msg=msg)


    def Player(self, request, context):
        if request.start:
            self.game_ID = request.game_id
            print(f"\rGame has started! You are playing against Node {request.opponent}.")
            if request.next_move == request.player_symbol:
                print(f"It's your turn! Your symbol is {request.player_symbol}\nCurrent board: {request.board}")
            else:
                print(f"It's your opponent's turn. Your symbol is {request.player_symbol}.")
        else:
            print(f"\rIt's your turn! Your symbol is {request.player_symbol}\nCurrent board: {request.board}")
        #print(f"Node-{self.id}> ", end='')
        return tictactoe_pb2.Empty()
    
    
    def Ping(self, request, context):
        return tictactoe_pb2.Empty()


    def StartElection(self, request, context):
        print(
            f"[Election] - received election message from process {request.prev_ids[-1]}")
        if self.id in request.prev_ids:
            result = tictactoe_pb2.ElectionResult()
            result.leader_id = max(request.prev_ids)
            result.success = True
            return result
        else:
            id = self.id
            request.prev_ids.append(id)
            next_node = id % MAX_NODES + 1
            while True:
                with grpc.insecure_channel(f'localhost:{next_node}'
                                           if LOCALHOST else f'192.168.76.5{next_node}:50051') as channel:
                    stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                    try:
                        response = stub.StartElection(
                            tictactoe_pb2.ElectionMessage(prev_ids=request.prev_ids))
                        return response
                    except:
                        next_node = next_node % MAX_NODES + 1
                


    def EndElection(self, request, context):
        if request.leader_id == self.id:
            self.coordinator = True
            self.StartGame()
        else:
            self.coordinator = False
        self.leader_ID = request.leader_id
        print(f"[Election] - election completed successfully. Coordinator ID is {request.leader_id}")
        return tictactoe_pb2.Empty()


    def StartGame(self):
        IDs = []
        for i in range(1, MAX_NODES+1):
            if i == self.id:
                continue
            with grpc.insecure_channel(f'localhost:{i}' if LOCALHOST else f'192.168.76.5{i}:50051') as channel:
                stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                try:
                    stub.Ping(tictactoe_pb2.Empty())
                    IDs.append(i)
                except:
                    pass

        prev_i = 0
        for i in range(2, len(IDs)+1, 2):
            p1, p2 = IDs[prev_i:i] # X and O
            self.games.append(TicTacToe(p1, p2, len(self.games)))
            prev_i = i
  
        for game in self.games:
            p1, p2 = game.get_players()
            with grpc.insecure_channel(f'localhost:{p1}' if LOCALHOST else f'192.168.76.5{p1}:50051') as channel:
                stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                stub.Player(tictactoe_pb2.PlayerMessage(
                    next_move=game.get_move(), 
                    player_symbol="X",
                    board=game.get_board(), 
                    start=True, 
                    game_id=game.get_game_id(),
                    opponent=p2))
                
            with grpc.insecure_channel(f'localhost:{p2}' if LOCALHOST else f'192.168.76.5{p2}:50051') as channel:
                stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                stub.Player(tictactoe_pb2.PlayerMessage(
                    next_move=game.get_move(), 
                    player_symbol="O", 
                    board=game.get_board(), 
                    start=True, 
                    game_id=game.get_game_id(),
                    opponent=p1))


    def GetDateTime(self, request, context):
        current_time = self.date_time
        response = tictactoe_pb2.DateTimeResponse()
        response.date_time = current_time.strftime(
            "%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"
        return response


    def SetDateTime(self, request, context):
        if request.adjustment:
            print(f"[Time sync] - old: {self.date_time}")
            print(f"[Time sync] - adjustment: {request.adjustment}")
            self.date_time += datetime.timedelta(seconds=float(request.adjustment))
            print(f"[Time sync] - new: {self.date_time}")
        else:
            print(f"[Time sync] - old: {self.date_time}")
            self.date_time = datetime.datetime.strptime(request.time, "%Y-%m-%d-%H:%M:%S")
            print(f"[Time sync] - new: {self.date_time}")
        response = tictactoe_pb2.Result()
        response.success = True
        return response

    def SetDateTimeCoordinator(self, request, context):
        message = tictactoe_pb2.DateTimeMessage(adjustment="", time=request.time)
        with grpc.insecure_channel(f'localhost:{request.node_ID}' 
                                   if LOCALHOST else f'192.168.76.5{request.node_ID}:50051') as channel:
            stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
            stub.SetDateTime(message)
            response = tictactoe_pb2.Result()
            response.success = True
            return response


    def GetLeader(self, request, context):
        response = tictactoe_pb2.LeaderResponse()
        response.leader_id = self.leader_ID
        return response


def poll_times(id):
    responses = dict()
    for i in range(1, 4):
        with grpc.insecure_channel(f'localhost:{i}' if LOCALHOST else f'192.168.76.5{i}:50051') as channel:
            stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
            start_time = time.time()
            response = stub.GetDateTime(tictactoe_pb2.DateTimeRequest())
            end_time = time.time()
            if response.date_time:
                estimated_time = datetime.datetime.strptime(
                    response.date_time, "%Y-%m-%d %H:%M:%S.%fZ") + datetime.timedelta(seconds=(end_time - start_time) / 2)
                responses[i] = estimated_time
    return responses


def send_time_adjustments(id, adjustments):
    for i in range(1, 4):
        with grpc.insecure_channel(f'localhost:{i}' if LOCALHOST else f'192.168.76.5{i}:50051') as channel:
            stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
            response = stub.SetDateTime(
                tictactoe_pb2.DateTimeMessage(adjustment=adjustments[i], time=""))

# Berkeley algorithm


def time_sync(i):
    print("[Time sync] - Started")
    responded_times = poll_times(i)
    average_time = datetime.datetime.fromtimestamp(sum(map(datetime.datetime.timestamp, responded_times.values(
    ))) / len(responded_times.values()))  # https://stackoverflow.com/a/39757012
    print(responded_times[1], responded_times[2], responded_times[3])
    print(average_time)
    adjustments = dict()
    for key in responded_times.keys():
        adjustments[key] = str(
            (average_time - responded_times[key]).total_seconds())
    print(f"[Time sync] - sending adjustments: {adjustments}")
    send_time_adjustments(i, adjustments)


def initiate_election(id):
    with grpc.insecure_channel(f'localhost:{id%MAX_NODES+1}' if LOCALHOST else f'192.168.76.5{id%MAX_NODES+1}:50051') as channel:
        stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
        li = [id]
        response = stub.StartElection(
            tictactoe_pb2.ElectionMessage(prev_ids=li))
        if response.success:
            for i in range(1, 4):
                with grpc.insecure_channel(f'localhost:{i}' if LOCALHOST else f'192.168.76.5{i}:50051') as channel:
                    stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                    stub.EndElection(response)
            #print(f"[Election] - election completed successfully. Coordinator ID is {response.leader_id}")
        else:
            print("[Election] - failed")


def try_election(id):
    responses = 0
    for i in range(1, MAX_NODES+1):
        if i == id:
            continue
        with grpc.insecure_channel(f'localhost:{i}' if LOCALHOST else f'192.168.76.5{i}:50051') as channel:
            stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
            try:
                stub.Ping(tictactoe_pb2.Empty())
                responses += 1
            except:
                pass

    if responses >= 2:
        time_sync(id)
        initiate_election(id)
        return True
    else:
        return False


def get_leader(id):
    with grpc.insecure_channel(f'localhost:{id}' if LOCALHOST else f'192.168.76.5{id}:50051') as channel:
        stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
        response = stub.GetLeader(
            tictactoe_pb2.LeaderRequest(sender_id=id))
        return response.leader_id
    
def check_command_correctness(command):
    return (command == "List-board" or 
            bool(re.fullmatch("Set-symbol [0-8],(O|X)", command)) or 
            bool(re.fullmatch("Set-node-time Node-\d+ \d\d:\d\d:\d\d", command)))
    
def get_id():
    for i in range(1, MAX_NODES+1):
        with grpc.insecure_channel(f'localhost:{i}' if LOCALHOST else f'192.168.76.5{i}:50051') as channel:
            stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
            try:
                stub.Ping(tictactoe_pb2.Empty())
            except:
                return i
    return None
    

def serve():
    leader_id = None
    id = get_id()
    if id is None:
        print("No room available!")
        return
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tictactoe_pb2_grpc.add_TicTacToeServicer_to_server(
        TicTacToeServicer(id), server)
    server.add_insecure_port(f'localhost:{id}' if LOCALHOST else f'192.168.76.5{id}:50051')
    server.start()
    print(f"Server started listening on port 50051")
    try:
        while get_leader(id) == 0:
            player_input = input(f"Node-{id}> ")
            if player_input == "Start-game" and try_election(id):
                break
            
        # wait for game start
        leader = get_leader(id)
        if leader == 0:
            print("Waiting for leader", end="")
            while True:
                print(".", end="")
                leader = get_leader(id)
                if leader != 0:
                    leader_id = leader
                    break
                time.sleep(1)
            print(f"\nLeader selected: {leader_id}")
            print(f"Starting game...")
        else:
            leader_id = leader

        while True:
            player_input = input(f"Node-{id}> ")
            with grpc.insecure_channel(f'localhost:{leader_id}' if LOCALHOST else f'192.168.76.5{leader_id}:50051') as channel:
                stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                response = stub.Coordinator(tictactoe_pb2.CoordinatorRequest(command=player_input, game_id=0, player_id=id))
                print(f"{response.msg}")
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
