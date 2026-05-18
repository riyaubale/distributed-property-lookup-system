import os
import flask
from flask import Flask
import grpc
import property_lookup_pb2
import property_lookup_pb2_grpc
import threading
import time
from collections import OrderedDict

app = Flask("p2")

lock = threading.Lock()
use_server_1 = True

CACHE_SIZE = 3
CACHE_ENTRY_LIMIT = 8
lru_cache = OrderedDict()

PROJECT = os.environ.get("PROJECT", "p2")
SERVER_1_ADDR = f"{PROJECT}-dataset-1:5000"
SERVER_2_ADDR = f"{PROJECT}-dataset-2:5000"

channel1 = grpc.insecure_channel(SERVER_1_ADDR)
stub1 = property_lookup_pb2_grpc.PropertyLookupStub(channel1)
channel2 = grpc.insecure_channel(SERVER_2_ADDR)
stub2 = property_lookup_pb2_grpc.PropertyLookupStub(channel2)

@app.route("/lookup/<zipcode>")
def lookup(zipcode):
    global use_server_1
    addresses = []
    source = "?"
    final_error = None

    try:
        zipcode = int(zipcode)
        limit = flask.request.args.get("limit", default=4, type=int)

        # Check cache first
        with lock:
            if zipcode in lru_cache:
                lru_cache.move_to_end(zipcode)  # mark as recently used
                cached_addresses = lru_cache[zipcode]
                print(f"Cache HIT for zipcode {zipcode}", flush=True)
                if limit <= CACHE_ENTRY_LIMIT:
                    return flask.jsonify({
                        "addrs": cached_addresses[:limit],
                        "source": "cache",
                        "error": None
                    })
                # If limit > 8, continue to fetch full set via gRPC
            else:
                print(f"Cache MISS for zipcode {zipcode}", flush=True)

        # gRPC retry loop
        for attempt in range(5):
            with lock:
                if use_server_1:
                    current_stub = stub1
                    current_source_label = "1"
                    use_server_1 = False
                else:
                    current_stub = stub2
                    current_source_label = "2"
                    use_server_1 = True

            try:
                # For large limits, request full limit from server
                grpc_limit = limit if limit > CACHE_ENTRY_LIMIT else CACHE_ENTRY_LIMIT
                response = current_stub.LookupByZip(
                    property_lookup_pb2.LookupRequest(zip=zipcode, limit=grpc_limit)
                )
                addresses_from_grpc = list(response.addresses)
                source = current_source_label
                final_error = None

                # Cache only first 8 addresses
                with lock:
                    lru_cache[zipcode] = addresses_from_grpc[:CACHE_ENTRY_LIMIT]
                    lru_cache.move_to_end(zipcode)
                    if len(lru_cache) > CACHE_SIZE:
                        evicted, _ = lru_cache.popitem(last=False)
                        print(f"Cache EVICTION: evicted {evicted}", flush=True)

                addresses = addresses_from_grpc
                break  # success

            except grpc.RpcError as e:
                final_error = f"gRPC error: {e.code()} - {e.details()}"
                if attempt < 4:
                    time.sleep(0.1)
                continue

        # After all retries — fail if no success
        if not addresses and final_error:
            print(f"All retries failed for {zipcode}: {final_error}", flush=True)
            return flask.jsonify({
                "addrs": [],
                "source": "?",
                "error": final_error
            })

    except ValueError:
        final_error = "Invalid zipcode format."
    except Exception as e:
        final_error = str(e)

    return flask.jsonify({
        "addrs": addresses[:limit],
        "source": source,
        "error": final_error
    })

def main():
    app.run("0.0.0.0", port=8080, debug=False, threaded=False)

if __name__ == "__main__":
    main()