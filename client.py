# Nathan Chan
# 251 151 037
# 2024-03-02
# Client submits request to primary and logs write operation to client.txt
import grpc
import replication_pb2
import replication_pb2_grpc
from server_registry import ports


primaryPort = ''

# waits for acknowledgement from priamry server then writes to log file
def write_to_primary(key, value):
    global primaryPort
    uris = ports.copy()
    
    if primaryPort is not None and len(primaryPort) > 0:
        uris.insert(0, primaryPort)

    while len(uris) > 0:
        port = uris.pop(0)

        try:
            with grpc.insecure_channel('localhost:%s'%port) as channel:
                stub = replication_pb2_grpc.SequenceStub(channel)
                response = stub.Write(replication_pb2.WriteRequest(key=key, value=value))

                # were we instructed to use a different leader ??
                if response.leaderId > 0 and response.ack != 'COMMITTED':
                    uris.insert(0, str(response.leaderId))
                    continue

                print("Response from Primary:", response.ack)

                # Log the write operation
                with open('client.txt', 'a') as f:
                    f.write(f"Key: {key}, Value: {value}\n")
                
                # update the primary's port
                primaryPort = port
                print('[!] NEW PRIMARY PORT = %s' % primaryPort)

                return
        except grpc.RpcError as ex:
            print('[ERROR] ', ex)
    
    print('[ERROR] Failed to write to any primary')

if __name__ == "__main__":
    with open('client.txt', 'w'): pass  # Clear client log file

    while True:
        key = input("Enter key (or 'q' to quit): ")
        if key.lower() == 'q':
            break
        value = input("Enter value: ")
        write_to_primary(key, value)
