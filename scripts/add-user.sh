#!/bin/bash

################################################################################
# VC Authentication System - User Management Tool
# Add, list, delete, and manage users
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
DATABASE_PATH="database/auth.db"
VENV_PATH="venv/bin/activate"

# Functions
print_banner() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║           VC USER MANAGEMENT TOOL                            ║"
    echo "║                                                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    if [ ! -f "$DATABASE_PATH" ]; then
        print_error "Database not found at $DATABASE_PATH"
        print_info "Run master_setup.sh first to initialize the system"
        exit 1
    fi
    
    if ! command -v sqlite3 &> /dev/null; then
        print_error "sqlite3 is not installed"
        echo "Install it with:"
        echo "  Ubuntu/Debian: sudo apt-get install sqlite3"
        echo "  macOS: brew install sqlite3"
        exit 1
    fi
    
    if [ ! -f "$VENV_PATH" ]; then
        print_warning "Virtual environment not found"
        print_info "Some features may not work correctly"
    fi
}

# Hash password using SHA-256
hash_password() {
    echo -n "$1" | sha256sum | awk '{print $1}'
}

# Add single user
add_user() {
    local name="$1"
    local email="$2"
    local password="$3"
    
    # Validate inputs
    if [ -z "$name" ] || [ -z "$email" ] || [ -z "$password" ]; then
        print_error "All fields are required"
        return 1
    fi
    
    # Validate email format
    if [[ ! "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        print_error "Invalid email format: $email"
        return 1
    fi
    
    # Check if email exists
    local exists=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM users WHERE email='$email';")
    
    if [ "$exists" -gt 0 ]; then
        print_error "User with email '$email' already exists"
        return 1
    fi
    
    # Hash password
    local password_hash=$(hash_password "$password")
    
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

# Interactive add user
interactive_add() {
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}         Add New User                  ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}\n"
    
    # Get name
    read -p "Full Name: " name
    if [ -z "$name" ]; then
        print_error "Name cannot be empty"
        return 1
    fi
    
    # Get email
    read -p "Email Address: " email
    if [ -z "$email" ]; then
        print_error "Email cannot be empty"
        return 1
    fi
    
    # Get password
    while true; do
        read -s -p "Password (min 6 chars): " password
        echo ""
        
        if [ ${#password} -lt 6 ]; then
            print_error "Password must be at least 6 characters"
            continue
        fi
        
        read -s -p "Confirm Password: " password_confirm
        echo ""
        
        if [ "$password" != "$password_confirm" ]; then
            print_error "Passwords do not match. Try again."
            continue
        fi
        
        break
    done
    
    echo ""
    add_user "$name" "$email" "$password"
}

# List all users
list_users() {
    local count=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM users;")
    
    if [ "$count" -eq 0 ]; then
        print_info "No users in database"
        return
    fi
    
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}Total Users: $count${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
    
    sqlite3 -header -column "$DATABASE_PATH" <<EOF
.mode column
.width 5 25 35 20
SELECT 
    id as ID,
    name as Name,
    email as Email,
    datetime(created_at, 'localtime') as 'Created'
FROM users 
ORDER BY created_at DESC;
EOF
    echo ""
}

# View user details
view_user() {
    local email="$1"
    
    if [ -z "$email" ]; then
        read -p "Enter user email: " email
    fi
    
    local user=$(sqlite3 -line "$DATABASE_PATH" "SELECT * FROM users WHERE email='$email';")
    
    if [ -z "$user" ]; then
        print_error "User not found: $email"
        return 1
    fi
    
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}         User Details                   ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}\n"
    
    echo "$user"
    echo ""
    
    # Get login attempts count
    local attempts=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM login_attempts WHERE email='$email';")
    local successful=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM login_attempts WHERE email='$email' AND success=1;")
    local failed=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM login_attempts WHERE email='$email' AND success=0;")
    
    echo -e "${CYAN}Login Statistics:${NC}"
    echo "  Total Attempts: $attempts"
    echo "  Successful: $successful"
    echo "  Failed: $failed"
    echo ""
}

# Delete user
delete_user() {
    local email="$1"
    
    if [ -z "$email" ]; then
        read -p "Enter email to delete: " email
    fi
    
    # Check if user exists
    local exists=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM users WHERE email='$email';")
    
    if [ "$exists" -eq 0 ]; then
        print_error "User not found: $email"
        return 1
    fi
    
    # Show user info
    local name=$(sqlite3 "$DATABASE_PATH" "SELECT name FROM users WHERE email='$email';")
    
    echo -e "${YELLOW}⚠️  WARNING: You are about to delete:${NC}"
    echo "  Name: $name"
    echo "  Email: $email"
    echo ""
    read -p "Are you sure? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_info "Deletion cancelled"
        return 0
    fi
    
    # Delete user
    sqlite3 "$DATABASE_PATH" "DELETE FROM users WHERE email='$email';"
    
    if [ $? -eq 0 ]; then
        print_success "User deleted successfully"
        
        # Ask if should delete login attempts
        read -p "Delete login history for this user? (y/n): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sqlite3 "$DATABASE_PATH" "DELETE FROM login_attempts WHERE email='$email';"
            print_success "Login history deleted"
        fi
    else
        print_error "Failed to delete user"
    fi
}

# Bulk import from CSV
bulk_import() {
    local csv_file="$1"
    
    if [ -z "$csv_file" ]; then
        read -p "Enter CSV file path: " csv_file
    fi
    
    if [ ! -f "$csv_file" ]; then
        print_error "File not found: $csv_file"
        return 1
    fi
    
    print_info "Importing users from $csv_file..."
    echo ""
    
    local count=0
    local success=0
    local failed=0
    
    # Read CSV (skip header if exists)
    local line_num=0
    while IFS=',' read -r name email password; do
        line_num=$((line_num + 1))
        
        # Skip header or empty lines
        if [ $line_num -eq 1 ] && [ "$name" == "name" ]; then
            continue
        fi
        
        if [ -z "$name" ] || [ -z "$email" ] || [ -z "$password" ]; then
            continue
        fi
        
        # Remove quotes if present
        name=$(echo "$name" | tr -d '"')
        email=$(echo "$email" | tr -d '"')
        password=$(echo "$password" | tr -d '"')
        
        count=$((count + 1))
        
        if add_user "$name" "$email" "$password" > /dev/null 2>&1; then
            success=$((success + 1))
            echo -e "${GREEN}✓${NC} $email"
        else
            failed=$((failed + 1))
            echo -e "${RED}✗${NC} $email (already exists or error)"
        fi
    done < "$csv_file"
    
    echo ""
    print_info "Import Summary:"
    echo "  Processed: $count"
    echo "  Successful: $success"
    echo "  Failed: $failed"
    echo ""
}

# Update user password
update_password() {
    local email="$1"
    
    if [ -z "$email" ]; then
        read -p "Enter user email: " email
    fi
    
    # Check if user exists
    local exists=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM users WHERE email='$email';")
    
    if [ "$exists" -eq 0 ]; then
        print_error "User not found: $email"
        return 1
    fi
    
    local name=$(sqlite3 "$DATABASE_PATH" "SELECT name FROM users WHERE email='$email';")
    echo -e "Updating password for: ${CYAN}$name ($email)${NC}\n"
    
    # Get new password
    while true; do
        read -s -p "New Password (min 6 chars): " password
        echo ""
        
        if [ ${#password} -lt 6 ]; then
            print_error "Password must be at least 6 characters"
            continue
        fi
        
        read -s -p "Confirm Password: " password_confirm
        echo ""
        
        if [ "$password" != "$password_confirm" ]; then
            print_error "Passwords do not match"
            continue
        fi
        
        break
    done
    
    # Hash and update password
    local password_hash=$(hash_password "$password")
    sqlite3 "$DATABASE_PATH" "UPDATE users SET password_hash='$password_hash', updated_at=CURRENT_TIMESTAMP WHERE email='$email';"
    
    if [ $? -eq 0 ]; then
        print_success "Password updated successfully"
    else
        print_error "Failed to update password"
    fi
}

# View recent login attempts
view_login_attempts() {
    local limit=${1:-20}
    local email=${2:-}
    
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}     Recent Login Attempts             ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}\n"
    
    if [ -n "$email" ]; then
        sqlite3 -header -column "$DATABASE_PATH" <<EOF
.mode column
.width 30 10 15 20
SELECT 
    email as Email,
    CASE WHEN success = 1 THEN '✓ Success' ELSE '✗ Failed' END as Status,
    ip_address as 'IP Address',
    datetime(timestamp, 'localtime') as Time
FROM login_attempts 
WHERE email = '$email'
ORDER BY timestamp DESC 
LIMIT $limit;
EOF
    else
        sqlite3 -header -column "$DATABASE_PATH" <<EOF
.mode column
.width 30 10 15 20
SELECT 
    email as Email,
    CASE WHEN success = 1 THEN '✓ Success' ELSE '✗ Failed' END as Status,
    ip_address as 'IP Address',
    datetime(timestamp, 'localtime') as Time
FROM login_attempts 
ORDER BY timestamp DESC 
LIMIT $limit;
EOF
    fi
    echo ""
}

# View system statistics
view_statistics() {
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}       System Statistics                ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}\n"
    
    local total_users=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM users;")
    local total_attempts=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM login_attempts;")
    local successful=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM login_attempts WHERE success=1;")
    local failed=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM login_attempts WHERE success=0;")
    local faces_captured=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM login_attempts WHERE face_captured=1;")
    local active_lockouts=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM lockouts WHERE locked_until > datetime('now');")
    
    echo -e "${CYAN}Users:${NC}"
    echo "  Total: $total_users"
    echo ""
    
    echo -e "${CYAN}Login Attempts:${NC}"
    echo "  Total: $total_attempts"
    echo "  Successful: $successful"
    echo "  Failed: $failed"
    echo "  Faces Captured: $faces_captured"
    echo ""
    
    echo -e "${CYAN}Security:${NC}"
    echo "  Active Lockouts: $active_lockouts"
    echo ""
}

# Export users to CSV
export_users() {
    local output_file="users_export_$(date +%Y%m%d_%H%M%S).csv"
    
    echo "name,email,created_at" > "$output_file"
    sqlite3 -csv "$DATABASE_PATH" "SELECT name, email, created_at FROM users ORDER BY created_at DESC;" >> "$output_file"
    
    print_success "Users exported to: $output_file"
}

# Show menu
show_menu() {
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo "  1) Add user (interactive)"
    echo "  2) List all users"
    echo "  3) View user details"
    echo "  4) Update password"
    echo "  5) Delete user"
    echo "  6) Bulk import (CSV)"
    echo "  7) View login attempts"
    echo "  8) View statistics"
    echo "  9) Export users to CSV"
    echo "  0) Exit"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo ""
}

# Main function
main() {
    print_banner
    check_prerequisites
    
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
            view)
                view_user "$2"
                ;;
            delete)
                delete_user "$2"
                ;;
            import)
                bulk_import "$2"
                ;;
            attempts)
                view_login_attempts "${2:-20}" "${3:-}"
                ;;
            stats)
                view_statistics
                ;;
            export)
                export_users
                ;;
            password)
                update_password "$2"
                ;;
            *)
                print_error "Unknown command: $1"
                echo ""
                echo "Available commands:"
                echo "  add <name> <email> <password>"
                echo "  list"
                echo "  view <email>"
                echo "  delete <email>"
                echo "  import <csv_file>"
                echo "  attempts [limit] [email]"
                echo "  stats"
                echo "  export"
                echo "  password <email>"
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
                1) interactive_add ;;
                2) list_users ;;
                3) view_user ;;
                4) update_password ;;
                5) delete_user ;;
                6) bulk_import ;;
                7) 
                    read -p "Show how many attempts? (default 20): " limit
                    limit=${limit:-20}
                    read -p "Filter by email (leave empty for all): " email
                    view_login_attempts "$limit" "$email"
                    ;;
                8) view_statistics ;;
                9) export_users ;;
                0)
                    print_success "Goodbye!"
                    exit 0
                    ;;
                *)
                    print_error "Invalid option"
                    ;;
            esac
            
            echo ""
            read -p "Press Enter to continue..." -r
            print_banner
        done
    fi
}

# Run main function
main "$@"