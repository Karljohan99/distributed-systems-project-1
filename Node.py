import grpc
from concurrent import futures
import time
import sys
import random
import datetime

import tictactoe_pb2
import tictactoe_pb2_grpc

class TicTacToeServicer(tictactoe_pb2_grpc.TicTacToeServicer):
    def __init__(self):
        self.id = int(sys.argv[1])
        self.date_time = datetime.datetime.utcnow()
        
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

    def GetDateTime(self, request, context):
        current_time = datetime.datetime.utcnow()
        response = tictactoe_pb2.DateTimeResponse()
        response.date_time = current_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] + "Z"
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
                estimated_time = datetime.datetime.strptime(response.date_time, "%Y-%m-%d %H:%M:%S.%fZ") + datetime.timedelta(seconds=(end_time - start_time) / 2)
                responses[i] = estimated_time
    return responses

def send_time_adjustments(id, adjustments):
    for i in range(1, 4):
        with grpc.insecure_channel(f'localhost:{i}') as channel:
            stub = tictactoe_pb2_grpc.TicTacToeStub(channel)
            response = stub.SetDateTime(tictactoe_pb2.DateTimeMessage(adjustment=adjustments[i]))

# Berkeley algorithm
def time_sync(i):
    print("[Time sync] - Started")
    responded_times = poll_times(i)
    average_time = datetime.datetime.fromtimestamp(sum(map(datetime.datetime.timestamp, responded_times.values())) / len(responded_times.values())) # https://stackoverflow.com/a/39757012
    adjustments = dict()
    for key in responded_times.keys():
        adjustments[key] = str((average_time - responded_times[key]).total_seconds())
    print(f"[Time sync] - sending adjustments: {adjustments}")
    send_time_adjustments(i, adjustments)
        
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
        #time_sync(id)
            

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