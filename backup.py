# Nathan Chan
# 251 151 037
# 2024-03-02
# backup server
import grpc
from concurrent import futures
import replication_pb2
import replication_pb2_grpc
import heartbeat_service_pb2
import heartbeat_service_pb2_grpc
import time  
import sys
import random

class Backup(replication_pb2_grpc.SequenceServicer):
    def __init__(self, heartbeat_stub, port, backup_stubs):
        self.data = {}
        self.heartbeat_stub = heartbeat_stub
        self.election_timer = 0
        self.current_term = 0
        self.voted_for = 0
        self.primary_last_heartbeat = None
        self.port = port
        self.backup_stubs = backup_stubs
        self.log = []
        self.last_log_index = 0
        self.last_log_term = 0
        self.outfile = outfile = 'backup_'+port+'.txt'


    def Write(self, request, context):
        # Apply write operation
        self.data[request.key] = request.value

        log_entry = {'term': self.current_term, 'key': request.key, 'value': request.value}
        self.log.append(log_entry)

        last_log_index = len(self.log) -1

        # Log the write operation
        with open(self.outfile, 'a') as f:
            f.write(f"Key: {request.key}, Value: {request.value}\n")

        return replication_pb2.WriteResponse(ack="Write successful")

    def Heartbeat(self, request, context):
        service_identifier = request.service_identifier
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        self.primary_last_heartbeat = current_time
        print(f"Heartbeat received from {service_identifier} at {current_time}")
        return heartbeat_service_pb2.HeartbeatResponse(message="Heartbeat received")

    def reset_election_timer(self):
        self.election_timer = random.randint(150, 300)

    def RequestVote(self, request, context):
        # Extract information from the request
        candidate_term = request.term
        candidate_id = request.candidate_id
        candidate_last_log_index = request.last_log_index
        candidate_last_log_term = request.last_log_term

        # Check if the candidate's term is at least as up-to-date as the current term
        if candidate_term >= self.current_term:
            # Check if the backup has not voted in this term and if the candidate's log is at least as up-to-date as its own log
            if self.voted_for == 0 and (candidate_last_log_term > self.last_log_term or (candidate_last_log_term == self.last_log_term and candidate_last_log_index >= self.last_log_index)):
                # Vote for the candidate
                self.voted_for = candidate_id
                self.current_term = candidate_term
                return replication_pb2.RequestVoteResponse(vote_granted=True)
        
        # Reject the vote request
        return replication_pb2.RequestVoteResponse(vote_granted=False)


    def start_election(self):
        # Step 1: Increment current term
        self.current_term += 1

        # Step 2: Vote for self
        self.voted_for = self.port

        # Step 3: Request votes from other backups
        for backup_stub in self.backup_stubs:
            try:
                print("current_term:", self.current_term)
                print("port:", self.port)
                print("last_log_index:", self.last_log_index)
                print("last_log_term:", self.log[self.last_log_index]['term'])
        
                response = backup_stub.RequestVote(replication_pb2.RequestVoteRequest(
                    term=self.current_term,
                    candidate_id=int(self.port),  
                    last_log_index=self.last_log_index,
                    last_log_term=(self.log[(self.last_log_index)]['term'])
                ))
                # TODO Process the response 
            except grpc.RpcError as e:
                # Handle RPC errors
                print(f"Error requesting vote from backup: {e}")

        # Step 4: Reset election timer
        self.reset_election_timer()

    def check_heartbeats(self):
        current_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        if self.primary_last_heartbeat and time.time() - time.mktime(time.strptime(self.primary_last_heartbeat, '%Y-%m-%d %H:%M:%S')) > 10:
            self.start_election()

    


def serve(port):
    outfile = 'backup_'+port+'.txt'
    with open(outfile, 'w'): pass  # Clear backup log file
    heartbeat_channel = grpc.insecure_channel('localhost:50053')
    heartbeat_stub = heartbeat_service_pb2_grpc.ViewServiceStub(heartbeat_channel)

    # Determine the ports for other backup servers
    backup_ports = ['50052', '50054', '50055', '50056']
    backup_ports.remove(port)

    # Establish connections to other backup servers
    backup_stubs = []
    for backup_port in backup_ports:
        backup_channel = grpc.insecure_channel(f'localhost:{backup_port}')
        backup_stub = replication_pb2_grpc.SequenceStub(backup_channel)
        backup_stubs.append(backup_stub)

    backup_instance = Backup(heartbeat_stub, port, backup_stubs)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    replication_pb2_grpc.add_SequenceServicer_to_server(backup_instance, server)
    server.add_insecure_port('[::]:'+port)
    server.start()
    print("Backup server started on "+port+".")

    # Start sending and checking heartbeats
    while True:
        backup_id = 'backup'+port
        heartbeat_stub.Heartbeat(heartbeat_service_pb2.HeartbeatRequest(service_identifier=backup_id))
        backup_instance.check_heartbeats()
        time.sleep(5)  # Send heartbeat every 5 seconds

    server.wait_for_termination()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python backup.py <port#>")
        sys.exit(1)
    port = sys.argv[1]
    serve(port)
