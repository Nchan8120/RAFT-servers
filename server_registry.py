import grpc, time
import replication_pb2_grpc
from replication_pb2 import WriteResponse, WriteRequest, AppendEntriesRequest, AppendEntriesResponse, RequestVoteResponse

ports = ['50051', '50052', '50054', '50055', '50056']

# represents a single node in this cluster
class ServerNode:
    id = ''
    port = ''
    isPrimary = False
    channel: grpc.Channel
    stub: replication_pb2_grpc.SequenceStub

    # latest term this server seen
    currentTerm = 0

    # the candidate's ID voted for in current term
    votedFor =0

    # log entries
    log = []

    # highest log entry known to be commited
    commitIndex = 0

    # index of highest log entry applied
    lastApplied = 0

    # node called election
    isElection = False

    healthThreshold = 1000
    lastHealthCheck = 0

    leaderId = 0

    def __init__(self, id, port):
        self.id = id
        self.log = [{'term':0,'value':None}]
        self.port = port
        self.lastHealthCheck = time.time() # prevent new nodes forcing an election
    
    def connect(self):
        self.channel = grpc.insecure_channel(self.port)
        self.stub = replication_pb2_grpc.SequenceStub(self.channel)

    def setHealthCheck(self):
        self.lastHealthCheck = time.time()
    
    def isStaleHealthCheck(self):
        return time.time() - self.lastHealthCheck >= self.healthThreshold

    def setLeaderId(self, id):
        self.leaderId = id


# container of all known servers
class ServerRegistry:
    servers: dict[str, ServerNode] = {}

    def __init__(self, localId):
        for port in ports:
            # dont register locally
            if localId == port:
                continue

            node = ServerNode(
                port,
                'localhost:%s' % port
            )
            self.servers[port] = node
            node.connect()

