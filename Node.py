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
        print(f"Received election message from process {request.prev_ids[-1]}")
        if self.id in request.prev_ids:
            result = tictactoe_pb2.ElectionResult()
            result.leader_id = max(request.prev_ids)
            result.success = True
            return result
        else:
            id = (request.prev_ids[-1]+1)%3
            with grpc.insecure_channel(f'localhost:{id+1}') as channel:
                stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                request.prev_ids.append(id)
                response = stub.StartElection(tictactoe_pb2.ElectionMessage(prev_ids=request.prev_ids))
                return response
    
        
        
def initiate_election(id):
    with grpc.insecure_channel(f'localhost:{(id+1)%3}') as channel:
        stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
        li = [id]
        response = stub.StartElection(tictactoe_pb2.ElectionMessage(prev_ids=li))
        if response.success:
            print(f"Election completed successfully. Coordinator ID is {response.leader_id}")
            if response.leader_id == id:
                print("I am the coordinator")
            else:
                print(f"{response.leader_id} is the coordinaor")
                """
                 with grpc.insecure_channel(f'localhost:{response.leader_id}') as channel:
                    stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
                    response = stub.StartElection(tictactoe_pb2.ElectionMessage(sender_ids=(request.sender_ids+1)%3))
                    return response
                """
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