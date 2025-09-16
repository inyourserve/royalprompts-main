#!/bin/bash

# Quick start script for RoyalPrompts
# This script provides easy commands to manage your RoyalPrompts deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    echo "RoyalPrompts Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start all services"
    echo "  stop      Stop all services"
    echo "  restart   Restart all services"
    echo "  status    Show service status"
    echo "  logs      Show logs (all services)"
    echo "  logs-api  Show backend logs"
    echo "  logs-web  Show frontend logs"
    echo "  logs-nginx Show nginx logs"
    echo "  logs-db   Show backend logs (includes database connection)"
    echo "  update    Update and restart services"
    echo "  backup    Backup database"
    echo "  health    Check service health"
    echo "  shell     Open shell in backend container"
    echo "  help      Show this help message"
    echo ""
}

start_services() {
    print_status "Starting RoyalPrompts services..."
    docker-compose -f docker-compose.production.yml up -d
    print_success "Services started!"
    show_status
}

stop_services() {
    print_status "Stopping RoyalPrompts services..."
    docker-compose -f docker-compose.production.yml down
    print_success "Services stopped!"
}

restart_services() {
    print_status "Restarting RoyalPrompts services..."
    docker-compose -f docker-compose.production.yml restart
    print_success "Services restarted!"
    show_status
}

show_status() {
    print_status "Service Status:"
    docker-compose -f docker-compose.production.yml ps
}

show_logs() {
    print_status "Showing logs for all services (Press Ctrl+C to exit)..."
    docker-compose -f docker-compose.production.yml logs -f
}

show_logs_api() {
    print_status "Showing backend logs (Press Ctrl+C to exit)..."
    docker-compose -f docker-compose.production.yml logs -f backend
}

show_logs_web() {
    print_status "Showing frontend logs (Press Ctrl+C to exit)..."
    docker-compose -f docker-compose.production.yml logs -f frontend
}

show_logs_nginx() {
    print_status "Showing nginx logs (Press Ctrl+C to exit)..."
    docker-compose -f docker-compose.production.yml logs -f nginx
}

show_logs_db() {
    print_status "Showing backend logs (includes MongoDB Atlas connection info) (Press Ctrl+C to exit)..."
    docker-compose -f docker-compose.production.yml logs -f backend
}

update_services() {
    print_status "Updating services..."
    docker-compose -f docker-compose.production.yml pull
    docker-compose -f docker-compose.production.yml up --build -d
    print_success "Services updated!"
    show_status
}

backup_database() {
    print_status "Creating database backup from MongoDB Atlas..."
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Use mongodump from backend container to connect to Atlas
    docker-compose -f docker-compose.production.yml exec -T backend mongodump --uri="$MONGODB_URL" --out /tmp/backup
    docker cp royalprompts_backend:/tmp/backup "$BACKUP_DIR/"
    
    print_success "Database backup created in $BACKUP_DIR"
    print_warning "Note: This requires mongodump to be installed in the backend container"
}

check_health() {
    print_status "Checking service health..."
    
    # Check if containers are running
    if docker-compose -f docker-compose.production.yml ps | grep -q "Up"; then
        print_success "Containers are running"
    else
        print_error "Some containers are not running"
        return 1
    fi
    
    # Check API health (includes MongoDB Atlas connection)
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend API and MongoDB Atlas connection are healthy"
    else
        print_error "Backend API is not responding (check MongoDB Atlas connection)"
    fi
    
    # Check Frontend health
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend is healthy"
    else
        print_error "Frontend is not responding"
    fi
    
    # Check Nginx health
    if curl -f http://localhost/health > /dev/null 2>&1; then
        print_success "Nginx is healthy"
    else
        print_error "Nginx is not responding"
    fi
}

open_shell() {
    print_status "Opening shell in backend container..."
    docker-compose -f docker-compose.production.yml exec backend /bin/bash
}

# Main script logic
case "${1:-help}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    logs-api)
        show_logs_api
        ;;
    logs-web)
        show_logs_web
        ;;
    logs-nginx)
        show_logs_nginx
        ;;
    logs-db)
        show_logs_db
        ;;
    update)
        update_services
        ;;
    backup)
        backup_database
        ;;
    health)
        check_health
        ;;
    shell)
        open_shell
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
