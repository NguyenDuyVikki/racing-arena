# Racing Arena - Project Architecture

This document explains the comprehensive project architecture for Racing Arena, a multiplayer math racing game.

## Project Structure

```
racing-area/
├── config/                 # Configuration settings
│   ├── __init__.py
│   └── settings.py         # Game configuration constants
├── src/                    # Main source code
│   ├── __init__.py
│   ├── client/             # Client implementation
│   │   ├── __init__.py
│   │   └── racing_client.py
│   ├── server/             # Server implementation  
│   │   ├── __init__.py
│   │   └── racing_server.py
│   ├── game/               # Core game logic
│   │   ├── __init__.py
│   │   ├── player.py       # Player model
│   │   ├── state.py        # Game state management
│   │   ├── expressions.py  # Math expression generator
│   │   └── round_processor.py # Round processing logic
│   └── utils/              # Utility functions
│       ├── __init__.py
│       ├── network.py      # Network utilities
│       └── messaging.py    # Message processing
├── tests/                  # Test files
│   ├── test_client.py      # Automated test client
│   └── test_game.py        # Unit tests
├── main.py                 # Main entry point with orchestrator class
├── setup.py                # Package setup
├── requirements.txt        # Dependencies
├── Makefile               # Build and development tasks
├── ARCHITECTURE.md        # This file
└── README.md              # Project documentation
```

## Module Breakdown

### Configuration (`config/`)
- **settings.py**: All game configuration constants (host, port, timeouts, scoring, math ranges, etc.)
- **__init__.py**: Package initialization

### Core Game Logic (`src/game/`)
- **player.py**: Player model with scoring and state management
- **state.py**: Overall game state management (rounds, track, etc.)
- **expressions.py**: Math expression generation and validation
- **round_processor.py**: Logic for processing rounds and scoring
- **__init__.py**: Package initialization with exports

### Server (`src/server/`)
- **racing_server.py**: Complete server implementation with socket handling, player management, and game orchestration
- **__init__.py**: Package initialization

### Client (`src/client/`)
- **racing_client.py**: Client implementation for connecting to server and handling user interaction
- **__init__.py**: Package initialization

### Utilities (`src/utils/`)
- **network.py**: Network utilities (port checking, finding available ports)
- **messaging.py**: Message creation and parsing utilities for JSON communication
- **__init__.py**: Package initialization with utility exports

### Tests (`tests/`)
- **test_game.py**: Comprehensive unit tests for all game components
- **test_client.py**: Integration tests and automated client testing

### Main Entry Point
- **main.py**: Advanced orchestrator class with multiple running modes:
  - Interactive menu system
  - Command-line interface
  - Server-only mode
  - Client-only mode
  - Local testing mode with bots
  - Multiple client testing
  - Integrated test runner
  - Resource management and cleanup

## Key Architectural Improvements

1. **Separation of Concerns**: Each module has a single, well-defined responsibility
2. **Configurability**: All settings centralized in config module for easy customization
3. **Testability**: Modular design enables comprehensive unit and integration testing
4. **Maintainability**: Clear structure makes code easier to understand and modify
5. **Reusability**: Components can be imported and used independently
6. **Scalability**: Threaded architecture supports multiple concurrent clients
7. **User Experience**: Advanced main orchestrator with multiple interaction modes
8. **Error Handling**: Comprehensive error handling and graceful degradation
9. **Resource Management**: Proper cleanup and resource management

## Running the Application

### Interactive Mode (Recommended)
```bash
python main.py
```
This launches an interactive menu with options for:
- Starting server only
- Starting client only  
- Local game with bots
- Multiple client testing
- Project information
- Running tests

### Command Line Interface
```bash
# Start server only
python main.py --mode server

# Start client only
python main.py --mode client

# Local game with 2 bots
python main.py --mode local --bots 2

# Custom host and port
python main.py --mode server --host 0.0.0.0 --port 8080
```

### Development Commands
```bash
# Run tests with pytest
python main.py --mode test

# Or run tests directly
python -m pytest tests/ -v

# Run specific test files
python tests/test_game.py
python tests/test_client.py
```

## Architecture Patterns

### 1. **Modular Design**
- Clear separation between client, server, game logic, and utilities
- Each module is independently testable and maintainable

### 2. **Configuration Management**
- Centralized configuration in `config/settings.py`
- Environment-specific settings can be easily modified

### 3. **Network Communication**
- JSON-based messaging protocol
- Buffered message handling for partial receives
- Automatic port discovery and fallback

### 4. **Game State Management**
- Centralized game state in server
- Player state tracking and persistence
- Round-based processing with timing controls

### 5. **Threading Model**
- Non-blocking server using `select()` for I/O multiplexing
- Threaded client operations for responsive UI
- Background server processes for game orchestration

### 6. **Error Handling**
- Graceful handling of network disconnections
- Input validation and sanitization
- Comprehensive logging and error reporting

## Technology Stack

### Core Technologies
- **Python 3.12+**: Main programming language
- **Socket Programming**: TCP/IP networking for client-server communication
- **JSON**: Lightweight data interchange format for messaging
- **Threading**: Concurrent execution for multiple clients and background tasks
- **Select**: I/O multiplexing for efficient network handling

### Development Tools
- **pytest**: Testing framework for unit and integration tests
- **argparse**: Command-line argument parsing
- **typing**: Type hints for better code documentation and IDE support

### Project Organization
- **Package Structure**: Proper Python package hierarchy with `__init__.py` files
- **Import Management**: Clean import structure with absolute and relative imports
- **Configuration Management**: Centralized settings with environment flexibility

## Game Flow Architecture

### 1. **Server Startup**
```
Server Initialize → Bind Socket → Listen for Connections → Wait for Players
```

### 2. **Client Connection**
```
Client Connect → Register Nickname → Wait for Game Start → Ready to Play
```

### 3. **Game Loop**
```
Generate Expression → Broadcast to Clients → Collect Responses → 
Process Round → Update Scores → Check Win Condition → Next Round
```

### 4. **Round Processing**
```
Evaluate Answers → Calculate Timing → Award Points → Update Positions → 
Broadcast Results → Check Game End → Continue or Reset
```

## Security Considerations

### 1. **Input Validation**
- Nickname sanitization and length limits
- Mathematical expression validation
- Network message size limits

### 2. **Network Security**
- Connection timeout handling
- Buffer overflow prevention
- Graceful handling of malformed messages

### 3. **Resource Management**
- Client connection limits
- Memory usage monitoring
- Proper socket cleanup

## Future Architecture Enhancements

### 1. **Scalability**
- Database integration for persistent player stats
- Load balancing for multiple server instances
- Redis for session management

### 2. **Security**
- Authentication and authorization
- Encrypted communication (TLS/SSL)
- Rate limiting and DDoS protection

### 3. **Features**
- Web-based client interface
- Spectator mode
- Tournament system
- Replay system

### 4. **Monitoring**
- Performance metrics collection
- Error tracking and alerting
- Player analytics and statistics

## Development Workflow

### 1. **Local Development**
```bash
# Setup virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python main.py --mode local
```

### 2. **Testing**
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_game.py
python -m pytest tests/test_client.py

# Test with coverage
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html
```

### 3. **Production Deployment**
```bash
# Server deployment
python main.py --mode server --host 0.0.0.0 --port 8080

# Health check
curl http://localhost:8080/health  # If health endpoint is implemented
```

This architecture provides a solid foundation for a scalable, maintainable multiplayer gaming application with room for future enhancements and professional deployment.
