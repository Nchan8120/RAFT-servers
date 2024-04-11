# CS4459 Assignment 2
# David Tkachuk (dtkachu2@uwo.ca)


from concurrent import futures
from pydoc import ispackage
import grpc
import sys, time, random
from threading import Event, Thread



import replication_pb2_grpc
#import redis

from replication_pb2 import WriteResponse, WriteRequest, AppendEntriesRequest, AppendEntriesResponse, RequestVoteResponse, RequestVoteRequest
from replication_pb2_grpc import SequenceServicer
from heartbeat_client import HeartbeatClient
from server_registry import ServerNode, ServerRegistry

fh = None

HEALTH_THRESHOLD = 0.5


# Server Service
class ServerSequenceServicer(SequenceServicer):
    serverState: ServerNode
    registry: ServerRegistry

    stub: replication_pb2_grpc.SequenceStub

    def __init__(self, serverState, downgradeToFollower, registry: ServerRegistry): #, backupStub: replication_pb2_grpc.SequenceStub):
        self.database = {}
        self.downgradeToFollower = downgradeToFollower
        self.serverState = serverState
        self.registry = registry
        # self.stub = backupStub

    # Handle write RPC messages
    def Write(self, request, context):
        # check for leader
        if self.serverState.isPrimary is False:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return WriteResponse(ack="FAIL: NOT LEADER", leaderId=int(self.serverState.leaderId))

        entry = '%s=%s' % (request.key, request.value)
        print('[!] WRITE %s'%entry)
        self.addEntry(self.serverState.currentTerm, entry)

        def writeToServer(self:ServerSequenceServicer, server:ServerNode):
            index = 1
            while index <= self.serverState.commitIndex:
                try:
                    entries = self.serverState.log[-index:]
                    resp = server.stub.AppendEntries(AppendEntriesRequest(
                        term=self.serverState.currentTerm,
                        leaderId=int(self.serverState.id),
                        prevLogIndex=self.serverState.commitIndex-index,
                        prevLogTerm=self.serverState.log[-index]['term'],
                        leaderCommit=self.serverState.commitIndex,
                        entries = [e['value'] for e in entries],
                        entriesTerms = [int(e['term']) for e in entries]
                    ))

                    if resp.success:
                        return True
                except grpc.RpcError as ex:
                    if ex.code() == grpc.StatusCode.DATA_LOSS:
                        index += 1
                    else:
                        print('[!] FAILED TO WRITE TO %s :' % id)
                        return False
            return False

        committed = 1

        for id in self.registry.servers:
            # dont write to self self
            if id == self.serverState.id:
                continue

            server = self.registry.servers[id]
            if writeToServer(self, server):
                committed += 1

        if committed >= len(self.registry.servers.keys())/2:
            return WriteResponse(ack="COMMITTED", leaderId=int(self.serverState.leaderId))

        # all else something went wrong
        context.set_code(grpc.StatusCode.UNAVAILABLE)
        return WriteResponse(ack="FAIL: NOT COMITTED", leaderId=int(self.serverState.leaderId))

    def addEntry(self, term, value):
        self.serverState.log.append({
            'term': term,
            'value': value
        })
        fh.write('[TERM=%s, INDEX=%s] :: %s\n' % (term, self.serverState.commitIndex, value))
        fh.flush()
        self.serverState.commitIndex += 1

    def AppendEntries(self, request, context):
        # print('append')
        # this node has a higher term so fail to append
        if request.term < self.serverState.currentTerm:
            context.set_code(grpc.StatusCode.DATA_LOSS)
            return AppendEntriesResponse(success=False, term=self.serverState.currentTerm)
        
        # log doesnt have entry at index of prevLogIndex or its term doesnt match
        if len(self.serverState.log) < request.prevLogIndex or self.serverState.log[request.prevLogIndex]['term'] != request.prevLogTerm:
            context.set_code(grpc.StatusCode.DATA_LOSS)
            return AppendEntriesResponse(success=False, term=self.serverState.currentTerm)
        
        # got stuff from a leader, so we cancel our election
        self.serverState.isElection = False
        self.serverState.setHealthCheck()
        
        # new leader ID
        if self.serverState.leaderId != request.leaderId:
            self.serverState.currentTerm = request.term
            self.serverState.setLeaderId(request.leaderId)
            self.downgradeToFollower()
            print('[!] NEW LEADER: ', self.serverState.leaderId)

        # empty entries, is a heartbeat from leader
        if len(request.entries) == 0:
            # print("GOT HEARTBEAT FROM ", request.leaderId)
            return AppendEntriesResponse(success=True, term=self.serverState.currentTerm)
        
        else:
            i = self.serverState.commitIndex

            # append entry
            # for entry in request.entries:
                # self.addEntry(request.term, entry)
            
            remainingEntries = len(request.entries)
            j = request.prevLogIndex
            i = 0

            while remainingEntries > 0:
                entry = request.entries[i]

                # append
                if j not in self.serverState.log:
                    self.addEntry(request.term, entry)
                
                else:
                    term = request.entriesTerms[i]
                    value = request.entries[i]

                    if self.serverState.log[j]['term'] != term or self.serverState.log[j]['value'] != value:
                        self.serverState.log[j] = {
                            'term': term,
                            'value': value
                        }
                        fh.write('[OVERWRITE TERM=%s, INDEX=%s] :: %s\n' % (term, j, value))
                        fh.flush()

                i += 1
                j += 1
                remainingEntries -= 1
            

        
        if request.leaderCommit > self.serverState.commitIndex:
            self.serverState.commitIndex = min(self.serverState.commitIndex, request.leaderCommit)

        return AppendEntriesResponse(success=True, term=self.serverState.currentTerm)


    def RequestVote(self, request, context):
        # this node has a higher term
        if request.term < self.serverState.currentTerm:
            return RequestVoteResponse(term = self.serverState.currentTerm, vote_granted = False)
        
        # didnt vote before, and candidate's log is at least up to date as ours
        if request.last_log_index >= self.serverState.commitIndex and request.last_log_term >= self.serverState.currentTerm:
            self.serverState.votedFor = request.candidate_id
            print('[!] VOTING FOR %s' % self.serverState.votedFor)
            return RequestVoteResponse(term = self.serverState.currentTerm, vote_granted = True)
        
        # all else, no vote
        return RequestVoteResponse(term = self.serverState.currentTerm, vote_granted = False)


class Server:
    grpcServer = None  # grpc server instance
    backup = None  # bakcup server URI
    port = ''  # primary URI/port
    id = '' # server's identifier

    serverState: ServerNode

    registry: ServerRegistry = None

    stub: replication_pb2_grpc.SequenceStub  # stub to communicate with backup server

    heartBeatHandler = None

    def __init__(self, port, id):
        # register the heart beat client
        # self.heartbeatClient = HeartbeatClient(id)
        self.id = id
        self.port = port
        self.serverState = ServerNode(id, port)

        # setup registry
        self.registry = ServerRegistry(id)

        # # setup a gRPC connection to the backup server
        # with grpc.insecure_channel(backupServer) as c:
        #     print('[!] Connected to *backup* gRPC server on %s' % backupServer)
        #     self.channel = c
        #     self.stub = replication_pb2_grpc.SequenceStub(c)

        # setup the primary server gRPC instances and services
        self.grpcServer = grpc.server(
            futures.ThreadPoolExecutor(max_workers=10)
        )
        replication_pb2_grpc.add_SequenceServicer_to_server(
            ServerSequenceServicer(self.serverState, self.setFollower, self.registry),
            server=self.grpcServer
        )
        self.grpcServer.add_insecure_port(port)

        self.setFollower()

        # run primary server
        self.start()

    # Primary server start
    def start(self):
        print('[!] gRPC Server is starting on %s' % (self.port))
        self.grpcServer.start()
        self.grpcServer.wait_for_termination()

    # shut everything down
    def stop(self):
        # kill heartbeat
        if self.heartBeatHandler is not None:
            self.heartBeatHandler()
        self.grpcServer.stop(0)

    # send a heartbeat to all followers
    def sendHeartbeats(self):
        if not self.serverState.isPrimary:
            return
        
        for id in self.registry.servers:
            # dont ping self
            if id == self.serverState.id:
                continue

            server = self.registry.servers[id]
            try:
                resp = server.stub.AppendEntries(AppendEntriesRequest(
                    term=self.serverState.currentTerm,
                    leaderId=int(self.serverState.id),
                    prevLogIndex=self.serverState.commitIndex-1,
                    prevLogTerm=self.serverState.log[-1]['term'],
                    leaderCommit=self.serverState.commitIndex,
                    entries = []
                ))

                # update this node's last seen time
                server.setHealthCheck()
            except grpc.RpcError as ex:
                # print('[!] FAILED TO SEND HEARTBEAT TO %s :' % id)
                pass

    def setFollower(self):
        if self.serverState.isPrimary:
            print("[!] leader downgraded to follower")

            # end existing heart beat timer task
            if self.heartBeatHandler is not None:
                self.heartBeatHandler()

        self.serverState.isPrimary = False

        def schedule(self: Server, interval=1):
            stopped = Event()
            def loop():
                while not stopped.wait(interval):
                    # the healthchceck is stale
                    if self.serverState.isStaleHealthCheck():
                        self.startElection()
            Thread(target=loop).start()
            return stopped.set
        
        timeout =HEALTH_THRESHOLD+(random.randint(150,300)/1000)
        self.serverState.healthThreshold = timeout
        self.heartBeatHandler = schedule(self, interval=timeout)

    # set the local server as the leader if it wasnt before
    def setLeader(self):
        if self.serverState.isPrimary:
            return
        
        # end existing heart beat timer task
        if self.heartBeatHandler is not None:
            self.heartBeatHandler()

        print('[!] I was elected by the people')
        self.serverState.isPrimary = True
        self.serverState.setLeaderId(self.serverState.id)

        def schedule(self, interval=1):
            stopped = Event()
            def loop():
                while not stopped.wait(interval):
                    self.sendHeartbeats()
            Thread(target=loop).start()
            return stopped.set

        # send instantly    
        self.sendHeartbeats()
        self.heartBeatHandler = schedule(self, interval=HEALTH_THRESHOLD)

    def startElection(self):
        # ignore primary or current elections
        if self.serverState.isElection or self.serverState.isPrimary:
            return
        
        # voted for self
        self.serverState.isElection = True
        self.serverState.currentTerm += 1
        self.serverState.votedFor = int(self.id)
        votes = 1

        minVotes = 1

        print('[!] Starting a new election')

        for id in self.registry.servers:
            try:
                server = self.registry.servers[id]
                resp = server.stub.RequestVote(RequestVoteRequest(
                    term = self.serverState.currentTerm,
                    candidate_id = int(self.serverState.id),
                    last_log_index = self.serverState.commitIndex,
                    last_log_term = self.serverState.log[self.serverState.commitIndex]['term']
                ))

                minVotes += 1
                if resp.vote_granted:
                    votes += 1
            except grpc.RpcError as ex:
                print('Failed to get election from %s'%id, ex)

        print('[!] Got %d votes out of %d' % (votes, minVotes))

        if not self.serverState.isElection:
            print('[!] Election was cancelled')
            return

        if votes >= minVotes/2:
            print('[!] Elected!')
            self.setLeader()



if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python %s <port>" % sys.argv[0])
        exit(1)
    
    port = sys.argv[1]
    with open('%s.log' % port, 'w'): pass
    fh = open('%s.log' % port, 'a')

    print('[!] Starting server, port and ID = %s' % port)
    server = None
    try:
        server = Server('localhost:%s' % port, port)
        fh.close()
        exit(0)
    except KeyboardInterrupt:
        if server is not None:
            server.stop()
        print('GOOD BYE')
        fh.close()
        exit(0)
    except Exception as ex:
        print(ex)

    fh.close()

