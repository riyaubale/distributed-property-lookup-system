import grpc
import property_lookup_pb2
import property_lookup_pb2_grpc

def test_lookup():
    channel = grpc.insecure_channel("localhost:5000")
    stub = property_lookup_pb2_grpc.PropertyLookupStub(channel)
    response = stub.LookupByZip(property_lookup_pb2.LookupRequest(zip=53703, limit=5))
    print("Addresses:")
    for addr in response.addresses:
        print("  ", addr)

if __name__ == "__main__":
    test_lookup()