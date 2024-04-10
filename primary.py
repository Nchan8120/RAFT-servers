# Nathan Chan
# 251 151 037
# 2024-03-02
# primary server
import grpc
from concurrent import futures
import replication_pb2
import replication_pb2_grpc
import heartbeat_service_pb2
import heartbeat_service_pb2_grpc
import time  

class Primary(replication_pb2_grpc.SequenceServicer):
    def __init__(self, backup_stubs, heartbeat_stub):
        self.data = {}
        self.backup_stubs = backup_stubs
        self.heartbeat_stub = heartbeat_stub

    def Write(self, request, context):
        # Forward request to all backup servers
        for backup_stub in self.backup_stubs:
            try:
                backup_stub.Write(request)
            except grpc.RpcError as e:
                # Handle RPC errors, e.g., backup server is unavailable
                print(f"Error while forwarding write request to backup: {e}")

        # Apply write operation locally
        self.data[request.key] = request.value

        # Log the write operation
        with open('primary.txt', 'a') as f:
            f.write(f"Key: {request.key}, Value: {request.value}\n")

        return replication_pb2.WriteResponse(ack="Write successful")

def send_heartbeat(heartbeat_stub):
    while True:
        heartbeat_stub.Heartbeat(heartbeat_service_pb2.HeartbeatRequest(service_identifier='primary'))
        time.sleep(5)  # Send heartbeat every 5 seconds

def serve():
    with open('primary.txt', 'w'): pass  # Clear primary log file

    # Initialize heartbeat service stub
    heartbeat_channel = grpc.insecure_channel('localhost:50053')
    heartbeat_stub = heartbeat_service_pb2_grpc.ViewServiceStub(heartbeat_channel)

    # Initialize backup stubs
    backup_stubs = []
    backup_channels = ['localhost:50052', 'localhost:50054','localhost:50055', 'localhost:50056']  # Add addresses of all backup servers
    for channel in backup_channels:
        backup_channel = grpc.insecure_channel(channel)
        heartbeat_stub.AddBackupStub(heartbeat_service_pb2.AddBackupStubRequest(backup_address=channel))
        backup_stub = replication_pb2_grpc.SequenceStub(backup_channel)
        backup_stubs.append(backup_stub)

        
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    primary_servicer = Primary(backup_stubs, heartbeat_stub)
    replication_pb2_grpc.add_SequenceServicer_to_server(primary_servicer, server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("Primary server started.")

    # Start sending heartbeat
    send_heartbeat(heartbeat_stub)

    server.wait_for_termination()

if __name__ == '__main__':
    serve()
