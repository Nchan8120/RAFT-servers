Replication Servers with RAFT election.

generate gRPC stubs with:
    python3 -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. replication.proto
    python3 -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. heartbeat_service.proto

run servers:
    python3 server.py 50051
    python3 server.py 50052
    python3 server.py 50054
    python3 server.py 50055
    python3 server.py 50056

