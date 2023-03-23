import grpc
from concurrent import futures
import time
import sys

import tictactoe_pb2
import tictactoe_pb2_grpc

class TicTacToeServicer(tictactoe_pb2_grpc.TicTacToeServicer):
    def __init__(self):
        self.id = int(sys.argv[1])
        
    def SendGreeting(self, request, context):
        print(request.message)
        response = tictactoe_pb2.GreetingResponse(responder_id=self.id, message="Hello there!")
        return response
        

def send_greeting(id):
    for i in range(1, 3):
        if i == id:
            continue
        with grpc.insecure_channel(f'localhost:{i}') as channel:
            stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
            print("ID:", i)
            response = stub.SendGreeting(tictactoe_pb2.GreetingMessage(sender_id=id, message="Hi!"))
            print(response.responder_id, response.message)

def serve():
    id = int(sys.argv[1])
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server.add_insecure_port(f'localhost:{id}')
    server.start()
    print("Server started listening on DESIGNATED port")
    try:
        while True:
            #send_greeting(id)
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)

if __name__ == '__main__':
    serve()