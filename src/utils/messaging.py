"""
Message processing utilities for Racing Arena
"""
import json
from typing import List, Dict, Any


def process_client_data(buffer: str, data: str) -> tuple[str, List[Dict[str, Any]]]:
    """
    Process potentially multiple JSON messages from client data
    Returns: (updated_buffer, list_of_messages)
    """
    buffer += data
    messages = []
    
    # Split by newlines to handle multiple messages
    lines = buffer.split('\n')
    
    # Keep the last incomplete line in buffer
    updated_buffer = lines[-1]
    
    # Process complete lines
    for line in lines[:-1]:
        line = line.strip()
        if line:
            try:
                message = json.loads(line)
                messages.append(message)
            except json.JSONDecodeError as e:
                print(f"Error parsing message: {line} - {e}")
    
    return updated_buffer, messages


def create_message(content: str) -> bytes:
    """Create a JSON message with newline delimiter"""
    return (json.dumps({"message": content}) + "\n").encode()


def create_data_message(data: Dict[str, Any]) -> bytes:
    """Create a JSON message from data dictionary with newline delimiter"""
    return (json.dumps(data) + "\n").encode()
