import csv
import gzip
import grpc
from concurrent import futures
import property_lookup_pb2
import property_lookup_pb2_grpc

# Global dictionary to store addresses by ZIP code
ADDRESSES = {}

def load_addresses():
    """Load Madison addresses from addresses.csv.gz and index by ZipCode."""
    global ADDRESSES
    with gzip.open("addresses.csv.gz", "rt", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            zip_str = row.get("ZipCode", "").strip()
            if not zip_str.isdigit():
                continue
            zipcode = int(zip_str)
            address = row.get("Address", "").strip()
            if not address:
                continue
            if zipcode not in ADDRESSES:
                ADDRESSES[zipcode] = []
            ADDRESSES[zipcode].append(address)
    # Sort each ZIP’s addresses alphabetically
    for z in ADDRESSES:
        ADDRESSES[z].sort()
    print(f"Loaded {sum(len(v) for v in ADDRESSES.values())} addresses across {len(ADDRESSES)} ZIP codes.")
    print("Sample ZIPs:", list(ADDRESSES.keys())[:5])

class PropertyLookupServicer(property_lookup_pb2_grpc.PropertyLookupServicer):
    """Implements the PropertyLookup service defined in the proto file."""

    def LookupByZip(self, request, context):
        zip_code = request.zip
        limit = request.limit
        print(f"Received LookupByZip request: zip={zip_code}, limit={limit}")
        results = ADDRESSES.get(zip_code, [])[:limit]
        print(f"Returning {len(results)} addresses.")
        return property_lookup_pb2.LookupResponse(addresses=results)

def serve():
    """Start the gRPC server."""
    load_addresses()
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=1),
        options=[("grpc.so_reuseport", 0)]
    )
    property_lookup_pb2_grpc.add_PropertyLookupServicer_to_server(
        PropertyLookupServicer(), server
    )
    server.add_insecure_port("0.0.0.0:5000")
    server.start()
    print("PropertyLookup gRPC server running on port 5000...")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()