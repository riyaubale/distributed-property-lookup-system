# Distributed Property Lookup System – Multi-Container Database Application

A distributed multi-container application that provides zipcode-based property address lookup using gRPC, Flask, Docker, replication, retries, and LRU caching.

---

## Project Overview

This project implements a fault-tolerant distributed system consisting of:
- Dataset servers that host property address data
- Cache servers that expose an HTTP API and communicate with dataset servers using gRPC

The system supports:
- Load balancing
- Replication
- Retry handling
- LRU caching
- Multi-container deployment with Docker Compose

---

## Architecture

The application consists of two service layers:

### Dataset Layer
- 2 replicated gRPC dataset servers
- Hosts Madison property address data
- Responds to zipcode lookup requests

### Cache Layer
- 3 replicated HTTP cache servers
- Built using Flask
- Uses gRPC to query dataset servers
- Implements LRU caching
- Handles retries and failover

---

## Features

- Implemented gRPC-based microservice communication
- Built fault-tolerant replicated dataset servers
- Added retry logic with automatic failover
- Implemented round-robin load balancing across dataset servers
- Designed an LRU cache with size 3
- Supported cache-first lookup behavior
- Allowed continued operation during dataset server failures
- Containerized services using Docker
- Automated deployment with Docker Compose

---

## Technologies Used

- Python
- Flask
- gRPC
- Protocol Buffers
- Docker
- Docker Compose
- LRU Caching
- Distributed Systems Concepts

---

## Core Components

### `dataset.py`
gRPC dataset server responsible for:
- Reading `addresses.csv.gz`
- Sorting and storing address data
- Serving zipcode lookup requests

### `cache.py`
HTTP caching server responsible for:
- Handling REST requests
- Communicating with dataset servers via gRPC
- Managing retries and failover
- Implementing LRU cache logic

### `property_lookup.proto`
Defines:
- `PropertyLookup` service
- `LookupByZip` RPC method
- Request/response message structures

---

## gRPC Service

### RPC Method

```proto id="jlwmya"
rpc LookupByZip(LookupRequest) returns (LookupReply)
