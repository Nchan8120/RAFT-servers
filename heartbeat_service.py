# Nathan Chan
# 251 151 037
# 2024-03-02
# checks the availability of primary and backup server via heartbeats
import grpc
from concurrent import futures
import heartbeat_service_pb2_grpc
import heartbeat_service_pb2
import replication_pb2
import replication_pb2_grpc
import time
from google.protobuf.empty_pb2 import Empty


class HeartbeatService(heartbeat_service_pb2_grpc.ViewServiceServicer):
    _instance = None
    

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.primary_last_heartbeat = None 
            cls._instance.backup_last_heartbeat = None
            cls._instance.primary_down = True
            cls._instance.backup_down = True
            cls._instance.backup_stubs = {}
        return cls._instance

    # Method to add backup stub
    def AddBackupStub(self, request, context):
        channel = request.backup_address
        backup_channel = grpc.insecure_channel(channel)
        backup_stub = replication_pb2_grpc.SequenceStub(backup_channel)
        self.backup_stubs[channel] = backup_stub
        return Empty()

    # Remove backup after transition to primary
    def RemoveBackupStub(self, request, context):
        channel = request.backup_address
        if channel in self.backup_stubs:
            del self.backup_stubs[channel]
        return Empty()

    # Method to forward heartbeat to all backup servers
    def forward_heartbeat_to_backups(self):
        for backup_stub in self.backup_stubs.values():
            backup_stub.Heartbeat(heartbeat_service_pb2.HeartbeatRequest(service_identifier='primary'))

    # tracks what server we are receiving heartbeats from and the time
    def Heartbeat(self, request, context):
        service_identifier = request.service_identifier
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        print(f"Heartbeat received from {service_identifier} at {current_time}")

        if service_identifier == 'primary':
            self.primary_last_heartbeat = current_time
            self.primary_down = False
            self.forward_heartbeat_to_backups()
        else:
            self.backup_last_heartbeat = current_time
            self.backup_down = False

        return Empty()

    # checks what heartbeats are recieved and logs whether the server is up or not
    def check_heartbeats(self):
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())

        with open('heartbeat.txt', 'a') as f:
            if self.primary_last_heartbeat and time.time() - time.mktime(time.strptime(self.primary_last_heartbeat, '%Y-%m-%d %H:%M:%S')) > 10:
                self.primary_down = True
                f.write(f"Primary might be down. Latest heartbeat received at {self.primary_last_heartbeat}\n")
            elif not self.primary_down:
                self.primary_down = False
                f.write(f"Primary is alive. Latest heartbeat received at {self.primary_last_heartbeat}\n")

            if self.backup_last_heartbeat and time.time() - time.mktime(time.strptime(self.backup_last_heartbeat, '%Y-%m-%d %H:%M:%S')) > 10:
                self.backup_down = True
                f.write(f"Backup might be down. Latest heartbeat received at {self.backup_last_heartbeat}\n")
            elif not self.backup_down:
                self.backup_down = False
                f.write(f"Backup is alive. Latest heartbeat received at {self.backup_last_heartbeat}\n")


def serve():
    with open('heartbeat.txt', 'w'): pass  # Clear heartbeat log file

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    heartbeat_service_pb2_grpc.add_ViewServiceServicer_to_server(HeartbeatService(), server)
    server.add_insecure_port('[::]:50053')
    server.start()
    print("Heartbeat server started.")
    
    while(True):
        # Start checking heartbeats
        HeartbeatService().check_heartbeats()
        time.sleep(5)

    server.wait_for_termination()

if __name__ == '__main__':
    serve()
