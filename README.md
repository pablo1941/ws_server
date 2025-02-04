# WSServerPablo

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Main Functions](#main-functions)
- [License](#license)

## Overview
This project uses Python to implement a WebSocket server hosted on a remote Linux server.  The server handles communication with ESP IoT devices.

* Python language
* Environment: Linux
* Link: https://github.com/pablo1941/ws_server

## Features

- Handles WebSocket connections
- Supports multiple clients
- Easy to integrate with existing applications
- Logs client connections and messages
- Inserts data into a database

## Main Functions

### `dataUpdate(sep1, sep2, msg, filterField)`
Updates data in the database based on the provided message and filter field.

### `clientConnected(client, server)`
Handles the event when a new client connects to the WebSocket server.

### `clientDisconnected(client, server)`
Handles the event when a client disconnects from the WebSocket server.

### `messageReceived(client, server, message)`
Processes the message received from a client and performs necessary actions such as logging and database insertion.


## License

This project is licensed under the MIT License.
