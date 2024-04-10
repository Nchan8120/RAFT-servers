import grpc

ports = ['50051', '50052', '50054', '50055', '50056']

class ServerNode:
    id = ''
    port = ''
    isPrimary = False
    channel: grpc.Channel

    # latest term this server seen
    currentTerm = 0

    # the candidate's ID voted for in current term
    votedFor =0

    # log entries
    log = [None]

    # highest log entry known to be commited
    commitIndex = 0

    # index of highest log entry applied
    lastApplied = 0

    def __init__(self, id, port):
        self.id = id
        self.port = port
    
    def connect(self):
        self.channel = grpc.insecure_channel(self.port)

class ServerRegistry:
    servers = {}

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

