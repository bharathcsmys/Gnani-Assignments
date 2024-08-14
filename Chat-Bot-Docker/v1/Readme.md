# IKEA Chatbot Application

This project implements a basic chatbot for IKEA, utilizing Flask, MongoDB, and Redis. The application is containerized using Docker, with separate containers for the Flask application, Redis, and MongoDB.

## Table of Contents

- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Containers](#running-the-containers)
  - [Accessing the Application](#accessing-the-application)
- [API Endpoints](#api-endpoints)
- [Usage](#usage)
  - [User Registration](#user-registration)
  - [User Login](#user-login)
  - [Chatting with the Bot](#chatting-with-the-bot)
  - [Logging Out](#logging-out)
- [Docker Commands](#docker-commands)
- [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

Ensure you have the following installed on your system:

- [Docker](https://docs.docker.com/get-docker/)
- [Python 3.10](https://www.python.org/downloads/)

### Installation

1. **Clone the repository** (if applicable):

    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2. **Install required Python packages**:

    Inside your Docker container or local environment, run:

    ```bash
    pip3 install flask pymongo redis
    ```

### Running the Containers

1. **Start the MongoDB container**:

    ```bash
    docker run -itd --name mongo_db -p 2024:27017 mongo
    ```

2. **Start the Redis container**:

    ```bash
    docker run -itd --name redis_db -p 2025:6379 redis
    ```

3. **Start the Flask application container**:

    ```bash
    docker run -itd --name chat_app -p 2026:5002 python:3.10 
    ```

4. **Access the Flask container bash** to run the application:

    ```bash
    docker exec -it chat_app bash
    ```

5. **Navigate to the directory containing your Python code** and run:

    ```bash
    python3 app.py
    ```

### Accessing the Application

Once the containers are running, you can access the chatbot application via entering bash:

```bash
docker exec -it <container_name> bash
python app.py
```

## API Endpoints

- **GET /**: Root route providing basic information and available routes.
- **POST /register**: User registration. Requires `username` and `password` in JSON format.
- **GET /login/<username>/<password>**: User login. Initiates a session.
- **GET, POST /chat**: Chat route for interacting with the bot.
- **POST, GET /logout**: Logs the user out and stores chat history.

## Usage

### User Registration

To register a new user:

```bash
POST /register
{
    "username": "your_username",
    "password": "your_password"
}
```

### User Login

Log in using your registered username and password:

```bash
GET /login/your_username/your_password
```

### Chatting with the Bot

Once logged in, you can send messages to the bot:

```bash
POST /chat
{
    "message": "your_message"
}
```

### Logging Out

To log out and save your chat history:

```bash
GET /logout
```

## Docker Commands

Below are some useful Docker commands for managing your containers:

- **Entering the root bash**:

    ```bash
    sudo su
    ```

- **Listing all containers**:

    ```bash
    docker ps -a
    ```

- **Entering a container bash**:

    ```bash
    docker exec -it <container_name> bash
    ```

- **Inspecting a Docker container**:

    ```bash
    docker inspect <container_name>
    ```

- **Updating package lists** (inside a container):

    ```bash
    apt-get update
    ```

- **Installing Vim or other tools** (inside a container):

    ```bash
    apt install vim
    ```

## Troubleshooting

- **Cannot connect to MongoDB or Redis**: Ensure that the IP addresses in your Flask application match the IP addresses assigned to your MongoDB and Redis containers. You can inspect the container's IP with:

    ```bash
    docker inspect <container_name>
    ```

- **Flask application not starting**: Make sure you've installed all necessary Python packages inside the `chat_app` container.

- **Chat history not saving**: Check the Redis and MongoDB configurations to ensure they are correctly storing and retrieving data.

