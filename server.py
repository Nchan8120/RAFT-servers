# CS4459 Assignment 2
# David Tkachuk (dtkachu2@uwo.ca)


from concurrent import futures
from pydoc import ispackage
import grpc
import sys, time, random
from threading import Event, Thread

from soupsieve import iselect


import replication_pb2_grpc
#import redis

from replication_pb2 import WriteResponse, WriteRequest, AppendEntriesRequest, AppendEntriesResponse, RequestVoteResponse, RequestVoteRequest
from replication_pb2_grpc import SequenceServicer
from heartbeat_client import HeartbeatClient
from server_registry import ServerNode, ServerRegistry

fh = None



# Server Service
class ServerSequenceServicer(SequenceServicer):
    serverState: ServerNode

    stub: replication_pb2_grpc.SequenceStub

    def __init__(self, serverState): #, backupStub: replication_pb2_grpc.SequenceStub):
        self.database = {}
        self.serverState = serverState
        # self.stub = backupStub

    # Handle write RPC messages
    def Write(self, request, context):
        # check for leader
        if self.serverState.isPrimary is False:
            context.set_code(grpc.StatusCode.UNAVAILABLE)
            return WriteResponse(ack="FAIL: NOT LEADER")

        key = request.key
        value = request.value
        print('Got: key=%s, value=%s' % (key,value))
        try:
            # try to send this to the bakcup
            response = self.stub.Write(WriteRequest(key=key, value=value))
            if response.ack == key:  #verify the ack respond
                # write to our dictionary and outputs
                self.database[key] = value
                #fh.write("%s = %s\n" % (key, value))
                #fh.flush()
                return WriteResponse(ack=key)
        except Exception as ex:
            print('ERROR: ', ex)

        # all else something went wrong
        context.set_code(grpc.StatusCode.UNAVAILABLE)
        return WriteResponse(ack="FAIL: NOT LEADER")

    def addEntry(self, term, value):
        self.serverState.log.append({
            'term': term,
            'value': value
        })
        self.serverState.commitIndex += 1

    def AppendEntries(self, request, context):
        # this node has a higher term so fail to append
        if request.term < self.serverState.currentTerm:
            return AppendEntriesResponse(success=False, term=self.serverState.currentTerm)
        
        # log doesnt have entry at index of prevLogIndex or its term doesnt match
        if len(self.serverState.log) < request.prevLogIndex or self.serverState.log[request.prevLogIndex]['term'] != request.prevLogTerm:
            return AppendEntriesResponse(success=False, term=self.serverState.currentTerm)
        
        # empty entries, is a heartbeat from leader
        if len(request.entries) == 0:
            print("GOT HEARTBEAT")
            return AppendEntriesResponse(success=True, term=self.serverState.currentTerm)
        
        else:
            # append entry
            for entry in request.entries:
                self.addEntry(request.term, entry)
        
        if request.leaderCommit > self.serverState.commitIndex:
            self.serverState.commitIndex = min(self.serverState.commitIndex, request.leaderCommit)


    def RequestVote(self, request, context):
        # this node has a higher term
        if request.term < self.serverState.currentTerm:
            return RequestVoteResponse(term = self.serverState.currentTerm, success = False)
        
        # didnt vote before, and candidate's log is at least up to date as ours
        if request.last_log_index >= self.serverState.commitIndex and request.last_log_term >= self.serverState.currentTerm:
            self.serverState.votedFor = request.candidate_id
            return RequestVoteResponse(term = self.serverState.currentTerm, success = True)
        
        # all else, no vote
        return RequestVoteResponse(term = self.serverState.currentTerm, success = False)


class Server:
    grpcServer = None  # grpc server instance
    backup = None  # bakcup server URI
    port = ''  # primary URI/port
    id = '' # server's identifier

    serverState: ServerNode

    registry: ServerRegistry = None

    stub: replication_pb2_grpc.SequenceStub  # stub to communicate with backup server

    heartBeatHandler = None
    isElection = False

    def __init__(self, port, id):
        # register the heart beat client
        # self.heartbeatClient = HeartbeatClient(id)
        self.id = id
        self.port = port
        self.serverState = ServerNode(id, port)

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
            ServerSequenceServicer(self.serverState),
            server=self.grpcServer
        )
        self.grpcServer.add_insecure_port(port)

        # setup registry
        self.registry = ServerRegistry(id)
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
            except grpc.RpcError as ex:
                print('[!] FAILED TO SEND HEARTBEAT TO %s :' % id, ex)

    def setFollower(self):
        if self.serverState.isPrimary:
            print("[!] leader downgraded to follower")

            # end heart beat
            if self.heartBeatHandler is not None:
                self.heartBeatHandler()

        self.serverState.isPrimary = False

    # set the local server as the leader if it wasnt before
    def setLeader(self):
        if self.serverState.isPrimary:
            return
        
        print('[!] I was elected by the people')
        self.serverState.isPrimary = True

        def schedule(self, interval=1):
            stopped = Event()
            def loop():
                while not stopped.wait(interval):
                    self.sendHeartbeats()
            Thread(target=loop).start()
            return stopped.set

        # send instantly    
        self.sendHeartbeats()
        self.heartBeatHandler = schedule(self)

    def startElection(self):
        # ignore primary or current elections
        if self.isElection or self.serverState.isPrimary:
            return
        
        # voted for self
        self.serverState.currentTerm += 1
        self.serverState.votedFor = int(self.port)
        votes = 1


        for id in self.registry.servers:
            try:
                server = self.registry.servers[id]
                resp = server.stub.RequestVote(RequestVoteRequest(
                    term = self.serverState.currentTerm,
                    candidate_id = int(self.serverState.id),
                    last_log_index = self.serverState.commitIndex,
                    last_log_term = self.serverState.log[self.serverState.commitIndex]['term']
                ))

                if resp.vote_granted:
                    votes += 1
            except grpc.RpcError as ex:
                print('Failed to get election from %s'%id, ex)

        if votes >= len(self.registry.servers.keys())/2:
            self.setLeader()



if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python %s <port>" % sys.argv[0])
        exit(1)
    
    port = sys.argv[1]
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

