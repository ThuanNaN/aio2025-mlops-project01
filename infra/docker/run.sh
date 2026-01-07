#!/bin/bash

# Script to manage all platform services
# Usage: ./start.sh [up|down|restart|status]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Services array
SERVICES=("mlflow" "kafka" "monitor" "airflow")

# Function to print colored messages
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

# Function to start all services
start_services() {
    print_message "$GREEN" "Starting all platform services..."
    echo ""
    
    for service in "${SERVICES[@]}"; do
        if [ -d "$SCRIPT_DIR/$service" ] && [ -f "$SCRIPT_DIR/$service/docker-compose.yaml" ]; then
            print_message "$BLUE" "Starting $service..."
            cd "$SCRIPT_DIR/$service"
            docker compose up -d
            echo ""
        else
            print_message "$YELLOW" "Warning: $service directory or docker-compose.yaml not found"
        fi
    done
    
    print_message "$GREEN" "All services started successfully!"
}

# Function to stop all services
stop_services() {
    print_message "$RED" "Stopping all platform services..."
    echo ""
    
    for service in "${SERVICES[@]}"; do
        if [ -d "$SCRIPT_DIR/$service" ] && [ -f "$SCRIPT_DIR/$service/docker-compose.yaml" ]; then
            print_message "$BLUE" "Stopping $service..."
            cd "$SCRIPT_DIR/$service"
            docker compose down
            echo ""
        else
            print_message "$YELLOW" "Warning: $service directory or docker-compose.yaml not found"
        fi
    done
    
    print_message "$GREEN" "All services stopped successfully!"
}

# Function to restart all services
restart_services() {
    print_message "$YELLOW" "Restarting all platform services..."
    echo ""
    stop_services
    echo ""
    start_services
}

# Function to show status of all services
status_services() {
    print_message "$BLUE" "Checking status of all platform services..."
    echo ""
    
    for service in "${SERVICES[@]}"; do
        if [ -d "$SCRIPT_DIR/$service" ] && [ -f "$SCRIPT_DIR/$service/docker-compose.yaml" ]; then
            print_message "$BLUE" "Status of $service:"
            cd "$SCRIPT_DIR/$service"
            docker compose ps
            echo ""
        else
            print_message "$YELLOW" "Warning: $service directory or docker-compose.yaml not found"
        fi
    done
}

# Function to show help
show_help() {
    echo "Platform Services Management Script"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  up        - Start all platform services"
    echo "  down      - Stop all platform services"
    echo "  restart   - Restart all platform services"
    echo "  status    - Show status of all platform services"
    echo "  help      - Show this help message"
    echo ""
    echo "Services managed:"
    for service in "${SERVICES[@]}"; do
        echo "  - $service"
    done
}

# Main script logic
case "${1:-}" in
    up)
        start_services
        ;;
    down)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        status_services
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_message "$RED" "Error: Invalid command '${1:-}'"
        echo ""
        show_help
        exit 1
        ;;
esac
