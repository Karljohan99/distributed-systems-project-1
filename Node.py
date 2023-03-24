import grpc
from concurrent import futures
import time
import sys
import datetime
from tictactoe import TicTacToe
import tictactoe_pb2
import tictactoe_pb2_grpc


class TicTacToeServicer(tictactoe_pb2_grpc.TicTacToeServicer):
    def __init__(self):
        self.id = int(sys.argv[1])
        self.date_time = datetime.datetime.utcnow()
        self.games = []
        self.coordinator = False

    def ProcessCommand(self, command, stub, game):
        cmd = command
        cmd = cmd.split()
        base_cmd = cmd[0].strip()
        if base_cmd == "Set-Symbol":
            move = cmd[1].split(',')
            pos = move[0].strip()
            player = move[1].strip()
            if game.make_move(pos, player):
                stub.Game(tictactoe_pb2.GameRequest(next_move="Move made", board=None, is_action=False))
                return True
        elif base_cmd == "List-Board":
            stub.Game(tictactoe_pb2.GameRequest(next_move=None, board=game.get_board(), is_action=False))
            return True
        elif base_cmd == "Set-node-time":
            # TODO
            pass

        return False

    def GameRequest(self,  request, context):
        next_move = request.next_move
        board = request.board
        is_action = request.is_action
        if is_action:
            print(f"Its yout turn, current board\n{board}")
            print(f"You are currently palying as {next_move}")
            player_input = input("Please input your choice: ")
            return tictactoe_pb2.GameResponse(command=player_input)
        else:
            if board is not None:
                print(f'Current board\n{board}')
            else:
                print(next_move)

    def SendGreeting(self, request, context):
        response = tictactoe_pb2.GreetingResponse(
            responder_id=self.id, message="Hello there!", success=True)
        return response

    def StartElection(self, request, context):
        print(
            f"[Election] - received election message from process {request.prev_ids[-1]}")
        if self.id in request.prev_ids:
            result = tictactoe_pb2.ElectionResult()
            result.leader_id = max(request.prev_ids)
            result.success = True
            return result
        else:
            id = (request.prev_ids[-1]+1) % 3
            with grpc.insecure_channel(f'localhost:{id+1}') as channel:
                stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                request.prev_ids.append(id)
                response = stub.StartElection(
                    tictactoe_pb2.ElectionMessage(prev_ids=request.prev_ids))
                return response

    def EndElection(self, request, context):
        if request.leader_id == self.id:
            self.coordinator == True
            self.StartGame()
        else:
            self.coordinator == False
        return tictactoe_pb2.Empty()

    def StartGame(self):
        p1, p2 = [1, 2, 3,].remove(self.id)
        self.games.append(TicTacToe(p1, p2, len(self.games)))
        for game in self.games:
            while not game.check_winner():
                for i in range(1, 4):
                    if i != self.id:
                        processed = False
                        while not processed:
                            with grpc.insecure_channel(f'localhost:{i}') as channel:
                                stub = tictactoe_pb2_grpc.TicTacToeStub(
                                    channel)
                                response = stub.Game(tictactoe_pb2.GameRequest(
                                    next_move=game.next_move(), board=game.get_board(), is_action=True))
                                processed = self.ProcessCommand(
                                    response, stub, game)

    def GetDateTime(self, request, context):
        current_time = datetime.datetime.utcnow()
        response = tictactoe_pb2.DateTimeResponse()
        response.date_time = current_time.strftime(
            "%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"
        return response

    def SetDateTime(self, request, context):
        print(f"[Time sync] - old: {self.date_time}")
        print(f"[Time sync] - adjustment: {request.adjustment}")
        self.date_time += datetime.timedelta(seconds=float(request.adjustment))
        print(f"[Time sync] - new: {self.date_time}")
        response = tictactoe_pb2.Result()
        response.success = True
        return response


def poll_times(id):
    responses = dict()
    for i in range(1, 4):
        with grpc.insecure_channel(f'localhost:{i}') as channel:
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
        with grpc.insecure_channel(f'localhost:{i}') as channel:
            stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
            response = stub.SetDateTime(
                tictactoe_pb2.DateTimeMessage(adjustment=adjustments[i]))

# Berkeley algorithm


def time_sync(i):
    print("[Time sync] - Started")
    responded_times = poll_times(i)
    average_time = datetime.datetime.fromtimestamp(sum(map(datetime.datetime.timestamp, responded_times.values(
    ))) / len(responded_times.values()))  # https://stackoverflow.com/a/39757012
    adjustments = dict()
    for key in responded_times.keys():
        adjustments[key] = str(
            (average_time - responded_times[key]).total_seconds())
    print(f"[Time sync] - sending adjustments: {adjustments}")
    send_time_adjustments(i, adjustments)


def initiate_election(id):
    with grpc.insecure_channel(f'localhost:{(id+1)%3}') as channel:
        stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
        li = [id]
        response = stub.StartElection(
            tictactoe_pb2.ElectionMessage(prev_ids=li))
        if response.success:
            for i in range(1, 3):
                with grpc.insecure_channel(f'localhost:{i}') as channel:
                    stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                    stub.EndElection(response)
            print(
                f"[Election] - election completed successfully. Coordinator ID is {response.leader_id}")
            """
            if response.leader_id == id:
                print("I am the coordinator")
            else:
                print(f"{response.leader_id} is the coordinaor")
                with grpc.insecure_channel(f'localhost:{response.leader_id}') as channel:
                    stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                    response = stub.StartElection(tictactoe_pb2.ElectionMessage(sender_ids=(request.sender_ids+1)%3))
                    return response
            """
        else:
            print("[Election] - failed")


def send_greeting(id):
    responses = 0
    for i in range(1, 3):
        if i == id:
            continue
        with grpc.insecure_channel(f'localhost:{i}') as channel:
            stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
            response = stub.SendGreeting(
                tictactoe_pb2.GreetingMessage(sender_id=id, message="Hi!"))
            if response.success:
                responses += 1

    if responses == 2:
        time_sync(id)
        initiate_election(id)


def serve():
    id = int(sys.argv[1])
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tictactoe_pb2_grpc.add_TicTacToeServicer_to_server(
        TicTacToeServicer(), server)
    server.add_insecure_port(f'localhost:{id}')
    server.start()
    print("Server started listening on DESIGNATED port")
    try:
        while True:
            send_greeting(id)
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == '__main__':
    serve()
