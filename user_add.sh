#!/bin/bash

# add_user.sh - Script to add users to the authentication database
# Usage: ./add_user.sh

set -e

# Configuration
DATABASE_DIR="database"
DATABASE_PATH="$DATABASE_DIR/auth.db"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_header() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════╗"
    echo "║     Góchat User Management Tool        ║"
    echo "╔════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

hash_password() {
    echo -n "$1" | sha256sum | awk '{print $1}'
}

init_database() {
    if [ ! -f "$DATABASE_PATH" ]; then
        print_info "Database not found. Creating..."
        mkdir -p "$DATABASE_DIR"
        
        sqlite3 "$DATABASE_PATH" <<EOF
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    success BOOLEAN NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lockouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    reason TEXT,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS admin_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_type TEXT NOT NULL,
    message TEXT,
    email TEXT,
    severity TEXT DEFAULT 'MEDIUM',
    resolved BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF
        print_success "Database initialized successfully"
    fi
}

add_user() {
    local name="$1"
    local email="$2"
    local password="$3"
    
    # Hash password
    local password_hash=$(hash_password "$password")
    
    # Check if email exists
    local exists=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM users WHERE email='$email';")
    
    if [ "$exists" -gt 0 ]; then
        print_error "User with email '$email' already exists!"
        return 1
    fi
    
    # Insert user
    sqlite3 "$DATABASE_PATH" "INSERT INTO users (name, email, password_hash) VALUES ('$name', '$email', '$password_hash');"
    
    if [ $? -eq 0 ]; then
        print_success "User added successfully!"
        echo -e "   ${BLUE}Name:${NC} $name"
        echo -e "   ${BLUE}Email:${NC} $email"
        echo ""
        return 0
    else
        print_error "Failed to add user"
        return 1
    fi
}

list_users() {
    local count=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM users;")
    
    if [ "$count" -eq 0 ]; then
        print_info "No users in database"
        return
    fi
    
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}Total Users: $count${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
    
    sqlite3 -header -column "$DATABASE_PATH" <<EOF
SELECT 
    id as ID,
    name as Name,
    email as Email,
    datetime(created_at, 'localtime') as 'Created At'
FROM users 
ORDER BY created_at DESC;
EOF
    echo ""
}

delete_user() {
    local email="$1"
    
    # Check if user exists
    local exists=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM users WHERE email='$email';")
    
    if [ "$exists" -eq 0 ]; then
        print_error "User with email '$email' not found!"
        return 1
    fi
    
    # Delete user
    sqlite3 "$DATABASE_PATH" "DELETE FROM users WHERE email='$email';"
    
    if [ $? -eq 0 ]; then
        print_success "User deleted successfully!"
        return 0
    else
        print_error "Failed to delete user"
        return 1
    fi
}

interactive_add() {
    echo -e "${BLUE}═══ Add New User ═══${NC}\n"
    
    # Get name
    read -p "Enter full name: " name
    if [ -z "$name" ]; then
        print_error "Name cannot be empty"
        return 1
    fi
    
    # Get email
    read -p "Enter email: " email
    if [ -z "$email" ]; then
        print_error "Email cannot be empty"
        return 1
    fi
    
    # Get password
    read -s -p "Enter password: " password
    echo ""
    if [ -z "$password" ]; then
        print_error "Password cannot be empty"
        return 1
    fi
    
    # Confirm password
    read -s -p "Confirm password: " password_confirm
    echo ""
    
    if [ "$password" != "$password_confirm" ]; then
        print_error "Passwords do not match!"
        return 1
    fi
    
    echo ""
    add_user "$name" "$email" "$password"
}

bulk_add() {
    local csv_file="$1"
    
    if [ ! -f "$csv_file" ]; then
        print_error "File '$csv_file' not found!"
        return 1
    fi
    
    print_info "Reading users from $csv_file..."
    local count=0
    local success=0
    
    # Skip header and read CSV
    tail -n +2 "$csv_file" | while IFS=',' read -r name email password; do
        count=$((count + 1))
        if add_user "$name" "$email" "$password"; then
            success=$((success + 1))
        fi
    done
    
    print_success "Imported $success users"
}

show_menu() {
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo "1) Add single user (interactive)"
    echo "2) List all users"
    echo "3) Delete user"
    echo "4) Bulk import from CSV"
    echo "5) View login attempts"
    echo "6) Exit"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo ""
}

view_login_attempts() {
    local limit=${1:-20}
    
    echo -e "${BLUE}═══ Recent Login Attempts ═══${NC}\n"
    
    sqlite3 -header -column "$DATABASE_PATH" <<EOF
SELECT 
    email as Email,
    CASE WHEN success = 1 THEN '✓' ELSE '✗' END as Status,
    ip_address as 'IP Address',
    datetime(timestamp, 'localtime') as Time
FROM login_attempts 
ORDER BY timestamp DESC 
LIMIT $limit;
EOF
    echo ""
}

# Main script
main() {
    print_header
    
    # Check for sqlite3
    if ! command -v sqlite3 &> /dev/null; then
        print_error "sqlite3 is not installed. Please install it first."
        exit 1
    fi
    
    # Initialize database
    init_database
    
    # Check for command line arguments
    if [ $# -gt 0 ]; then
        case "$1" in
            add)
                if [ $# -eq 4 ]; then
                    add_user "$2" "$3" "$4"
                else
                    print_error "Usage: $0 add <name> <email> <password>"
                    exit 1
                fi
                ;;
            list)
                list_users
                ;;
            delete)
                if [ $# -eq 2 ]; then
                    delete_user "$2"
                else
                    print_error "Usage: $0 delete <email>"
                    exit 1
                fi
                ;;
            import)
                if [ $# -eq 2 ]; then
                    bulk_add "$2"
                else
                    print_error "Usage: $0 import <csv_file>"
                    exit 1
                fi
                ;;
            attempts)
                view_login_attempts "${2:-20}"
                ;;
            *)
                print_error "Unknown command: $1"
                echo "Available commands: add, list, delete, import, attempts"
                exit 1
                ;;
        esac
    else
        # Interactive menu
        while true; do
            show_menu
            read -p "Select option: " choice
            echo ""
            
            case $choice in
                1)
                    interactive_add
                    ;;
                2)
                    list_users
                    ;;
                3)
                    read -p "Enter email to delete: " email
                    delete_user "$email"
                    ;;
                4)
                    read -p "Enter CSV file path: " csv_file
                    bulk_add "$csv_file"
                    ;;
                5)
                    view_login_attempts 20
                    ;;
                6)
                    print_success "Goodbye!"
                    exit 0
                    ;;
                *)
                    print_error "Invalid option"
                    ;;
            esac
            
            echo ""
            read -p "Press Enter to continue..."
            clear
            print_header
        done
    fi
}

# Run main function
main "$@"