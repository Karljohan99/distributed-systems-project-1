import grpc
from concurrent import futures
import time
import sys
from tictactoe import TicTacToe
import tictactoe_pb2
import tictactoe_pb2_grpc

class TicTacToeServicer(tictactoe_pb2_grpc.TicTacToeServicer):
    def __init__(self):
        self.id = int(sys.argv[1])
        self.game = TicTacToe()
        
        
    def GameRequest(self, request, context):
        cmd = request.command
        cmd = cmd.split()
        base_cmd = cmd[0].strip()
        if base_cmd == "Set-Symbol":
            move = cmd[1].split(',')
            pos = move[0].strip()
            player = move[1].strip()
            if self.game.make_move(pos, player):
                return tictactoe_pb2.GameResponse(response="OK", board=self.game.get_board())
            else:
                return tictactoe_pb2.GameResponse(response="FAIL")
        elif base_cmd == "List-Board":
            return tictactoe_pb2.GameResponse(response="OK", board=self.game.get_board())
        elif base_cmd == "Set-node-time":
            pass
        else:
            print("Unknown command")
        
        
    def SendGreeting(self, request, context):
        response = tictactoe_pb2.GreetingResponse(responder_id=self.id, message="Hello there!", success=True)
        return response
    
    def StartElection(self, request, context):
        print(f"Received election message from process {request.sender_id} with election ID {request.election_id}")
        if request.sender_id == 3:
            print("I am process 3 and I am initiating the election")
            result = tictactoe_pb2.ElectionResult()
            result.leader_id = 3
            result.success = True
            return result
        else:
            print(f"Forwarding election message from process {request.sender_id} to process {request.sender_id+1}")
            with grpc.insecure_channel(f'localhost:{request.sender_id+1}') as channel:
                stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                response = stub.StartElection(tictactoe_pb2.ElectionMessage(sender_id=request.sender_id+1, election_id=request.election_id))
                return response
        
        
def initiate_election(id):
    with grpc.insecure_channel(f'localhost:{(id+1)%3}') as channel:
        stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
        response = stub.StartElection(tictactoe_pb2.ElectionMessage(sender_id=id, election_id=1))
        if response.success:
            print(f"Election completed successfully. Coordinator ID is {response.leader_id}")
        else:
            print("Election failed")
            
            
def send_greeting(id):
    responses = 0
    for i in range(1, 3):
        if i == id:
            continue
        with grpc.insecure_channel(f'localhost:{i}') as channel:
            stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
            response = stub.SendGreeting(tictactoe_pb2.GreetingMessage(sender_id=id, message="Hi!"))
            if response.success:
                responses += 1
                
    if responses == 2:
        initiate_election(id)
        
            

def serve():
    id = int(sys.argv[1])
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tictactoe_pb2_grpc.add_TicTacToeServicer_to_server(TicTacToeServicer(), server)
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