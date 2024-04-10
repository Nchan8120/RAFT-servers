Replication Servers with RAFT election.

generate gRPC stubs with:
    python3 -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. replication.proto
    python3 -m grpc_tools.protoc -I . --python_out=. --grpc_python_out=. heartbeat_service.proto

run heartbeat service:
    python3 heartbeat_service.py

run backup servers:
    python3 backup.py 50052
    python3 backup.py 50054
    python3 backup.py 50055
    python3 backup.py 50056

run primary server:
    python3 primary.py

* All backup servers must be running before the primary server is run.