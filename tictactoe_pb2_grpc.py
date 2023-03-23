# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import tictactoe_pb2 as tictactoe__pb2


class TicTacToeStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SendGreeting = channel.unary_unary(
                '/TicTacToe/SendGreeting',
                request_serializer=tictactoe__pb2.GreetingMessage.SerializeToString,
                response_deserializer=tictactoe__pb2.GreetingResponse.FromString,
                )
        self.StartElection = channel.unary_unary(
                '/TicTacToe/StartElection',
                request_serializer=tictactoe__pb2.ElectionMessage.SerializeToString,
                response_deserializer=tictactoe__pb2.ElectionResult.FromString,
                )


class TicTacToeServicer(object):
    """Missing associated documentation comment in .proto file."""

    def SendGreeting(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StartElection(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_TicTacToeServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'SendGreeting': grpc.unary_unary_rpc_method_handler(
                    servicer.SendGreeting,
                    request_deserializer=tictactoe__pb2.GreetingMessage.FromString,
                    response_serializer=tictactoe__pb2.GreetingResponse.SerializeToString,
            ),
            'StartElection': grpc.unary_unary_rpc_method_handler(
                    servicer.StartElection,
                    request_deserializer=tictactoe__pb2.ElectionMessage.FromString,
                    response_serializer=tictactoe__pb2.ElectionResult.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'TicTacToe', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class TicTacToe(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def SendGreeting(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/TicTacToe/SendGreeting',
            tictactoe__pb2.GreetingMessage.SerializeToString,
            tictactoe__pb2.GreetingResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def StartElection(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/TicTacToe/StartElection',
            tictactoe__pb2.ElectionMessage.SerializeToString,
            tictactoe__pb2.ElectionResult.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)