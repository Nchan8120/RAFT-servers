# Nathan Chan
# 251 151 037
# 2024-03-02
# Client submits request to primary and logs write operation to client.txt
import grpc
import replication_pb2
import replication_pb2_grpc

# waits for acknowledgement from priamry server then writes to log file
def write_to_primary(key, value):
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = replication_pb2_grpc.SequenceStub(channel)
        response = stub.Write(replication_pb2.WriteRequest(key=key, value=value))
        print("Response from Primary:", response.ack)

        # Log the write operation
        with open('client.txt', 'a') as f:
            f.write(f"Key: {key}, Value: {value}\n")

if __name__ == "__main__":
    with open('client.txt', 'w'): pass  # Clear client log file

    while True:
        key = input("Enter key (or 'q' to quit): ")
        if key.lower() == 'q':
            break
        value = input("Enter value: ")
        write_to_primary(key, value)
