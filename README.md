# Fog-Computing-Project
Prototyping Assignment in the Fog Computing course

## Scripts and Dependencies

`./cloud/server` contains the server component that runs on the cloud (for example GCE).

`./local/client` contains the local component that runs on the local machine and communicates with the server.

`./lib` contains the necessary dependencies for the components.

## Run Scripts

Runs the server component on the cloud

```bash
python -m cloud.server
```
Runs the client component on the local machine

```bash
python -m local.client
```
## Paramters
The following parameters should be adjusted in the mentioned components:

1. HOST = The server's IP address.
2. PORT = The port used by the server.
3. TIMEOUT = Time out in seconds before a messeage is retransmitted.
4. buffer_max_size = Max size of internal buffer that saves messages for retransmission.

## Requirements

The prototype fulfills the following requirements:

- [X] The application comprises a local component that runs on your own machine, and a component running in the Cloud, e.g., on GCE.

 - [X] The local component collects and makes use of (simulated) environmental information. For this purpose,four virtual sensors that continuously generate realistic data are used.

 - [X] Data is transmitted regularly (multiple times a minute) between the local component and the Cloud component in both directions.

 - [X] When disconnected and/or crashed, the local and Cloud component keeps working while preserving data for later transmission. Upon reconnection, the queued data needs to be delivered.
