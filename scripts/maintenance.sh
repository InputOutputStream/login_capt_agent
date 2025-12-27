#!/bin/bash

################################################################################
# VC Authentication System - Maintenance Tool
# Database cleanup, backups, logs, and system health
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
DATABASE_PATH="database/auth.db"
BACKUP_DIR="backups"
LOGS_DIR="logs"

# Functions
print_banner() {
    clear
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                                                              ║"
    echo "║        VC SYSTEM MAINTENANCE TOOL                            ║"
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
        print_error "Database not found: $DATABASE_PATH"
        exit 1
    fi
}

# Backup database
backup_database() {
    print_info "Creating database backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/auth_backup_$timestamp.db"
    
    cp "$DATABASE_PATH" "$backup_file"
    
    if [ $? -eq 0 ]; then
        local size=$(du -h "$backup_file" | cut -f1)
        print_success "Backup created: $backup_file ($size)"
        
        # Compress backup
        gzip "$backup_file"
        print_success "Backup compressed: $backup_file.gz"
        
        return 0
    else
        print_error "Backup failed"
        return 1
    fi
}

# List backups
list_backups() {
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}         Available Backups             ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}\n"
    
    if [ ! -d "$BACKUP_DIR" ] || [ -z "$(ls -A $BACKUP_DIR 2>/dev/null)" ]; then
        print_info "No backups found"
        return
    fi
    
    ls -lh "$BACKUP_DIR" | grep "auth_backup" | awk '{print $9, "(" $5 ")"}'
    echo ""
}

# Restore database
restore_database() {
    list_backups
    
    echo ""
    read -p "Enter backup filename to restore: " backup_name
    
    if [ ! -f "$BACKUP_DIR/$backup_name" ]; then
        print_error "Backup not found: $backup_name"
        return 1
    fi
    
    print_warning "⚠️  WARNING: This will replace the current database!"
    read -p "Are you sure? Type 'yes' to confirm: " confirm
    
    if [ "$confirm" != "yes" ]; then
        print_info "Restore cancelled"
        return 0
    fi
    
    # Create backup of current database
    print_info "Backing up current database first..."
    backup_database
    
    # Restore
    if [[ "$backup_name" == *.gz ]]; then
        print_info "Decompressing backup..."
        gunzip -c "$BACKUP_DIR/$backup_name" > "$DATABASE_PATH"
    else
        cp "$BACKUP_DIR/$backup_name" "$DATABASE_PATH"
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Database restored successfully"
    else
        print_error "Restore failed"
    fi
}

# Clean old records
clean_old_records() {
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}        Clean Old Records              ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}\n"
    
    echo "This will delete:"
    echo "  • Login attempts older than 30 days"
    echo "  • Expired lockouts"
    echo "  • Expired sessions"
    echo ""
    
    read -p "Continue? (y/n): " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "Cancelled"
        return 0
    fi
    
    # Backup first
    print_info "Creating backup before cleanup..."
    backup_database
    
    # Clean old login attempts (older than 30 days)
    local deleted_attempts=$(sqlite3 "$DATABASE_PATH" "DELETE FROM login_attempts WHERE timestamp < datetime('now', '-30 days'); SELECT changes();")
    print_success "Deleted $deleted_attempts old login attempts"
    
    # Clean expired lockouts
    local deleted_lockouts=$(sqlite3 "$DATABASE_PATH" "DELETE FROM lockouts WHERE locked_until < datetime('now'); SELECT changes();")
    print_success "Deleted $deleted_lockouts expired lockouts"
    
    # Clean expired sessions
    local deleted_sessions=$(sqlite3 "$DATABASE_PATH" "DELETE FROM sessions WHERE expires_at < datetime('now'); SELECT changes();")
    print_success "Deleted $deleted_sessions expired sessions"
    
    # Vacuum database
    print_info "Optimizing database..."
    sqlite3 "$DATABASE_PATH" "VACUUM;"
    print_success "Database optimized"
    
    echo ""
    print_success "Cleanup complete!"
}

# View database statistics
view_statistics() {
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}       Database Statistics             ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}\n"
    
    # Database size
    local db_size=$(du -h "$DATABASE_PATH" | cut -f1)
    echo -e "${CYAN}Database Size:${NC} $db_size"
    echo ""
    
    # Table statistics
    echo -e "${CYAN}Tables:${NC}"
    
    local users=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM users;")
    echo "  Users: $users"
    
    local attempts=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM login_attempts;")
    echo "  Login Attempts: $attempts"
    
    local lockouts=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM lockouts;")
    echo "  Lockouts: $lockouts"
    
    local sessions=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM sessions;")
    echo "  Sessions: $sessions"
    
    local alerts=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM admin_alerts;")
    echo "  Alerts: $alerts"
    
    echo ""
    
    # Recent activity
    echo -e "${CYAN}Recent Activity (Last 24 hours):${NC}"
    
    local recent_attempts=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM login_attempts WHERE timestamp > datetime('now', '-1 day');")
    echo "  Login Attempts: $recent_attempts"
    
    local successful=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM login_attempts WHERE success=1 AND timestamp > datetime('now', '-1 day');")
    echo "  Successful: $successful"
    
    local failed=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM login_attempts WHERE success=0 AND timestamp > datetime('now', '-1 day');")
    echo "  Failed: $failed"
    
    echo ""
    
    # Storage breakdown
    echo -e "${CYAN}Storage Breakdown:${NC}"
    
    local old_attempts=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM login_attempts WHERE timestamp < datetime('now', '-30 days');")
    echo "  Old login attempts (>30 days): $old_attempts"
    
    local expired_lockouts=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM lockouts WHERE locked_until < datetime('now');")
    echo "  Expired lockouts: $expired_lockouts"
    
    local expired_sessions=$(sqlite3 "$DATABASE_PATH" "SELECT COUNT(*) FROM sessions WHERE expires_at < datetime('now');")
    echo "  Expired sessions: $expired_sessions"
    
    echo ""
    
    if [ $old_attempts -gt 100 ] || [ $expired_lockouts -gt 10 ] || [ $expired_sessions -gt 10 ]; then
        print_warning "Consider running cleanup to free space"
    fi
}

# View logs
view_logs() {
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}           System Logs                 ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}\n"
    
    if [ ! -d "$LOGS_DIR" ]; then
        print_info "No logs directory found"
        return
    fi
    
    local log_files=$(ls -1 "$LOGS_DIR" 2>/dev/null)
    
    if [ -z "$log_files" ]; then
        print_info "No log files found"
        return
    fi
    
    echo "Available log files:"
    echo "$log_files" | nl
    echo ""
    
    read -p "View log file number (or 'all' for all, 'q' to cancel): " choice
    
    case $choice in
        q|Q)
            return
            ;;
        all|ALL)
            for log in $LOGS_DIR/*; do
                echo -e "\n${CYAN}=== $(basename $log) ===${NC}"
                tail -n 20 "$log"
            done
            ;;
        *)
            if [[ "$choice" =~ ^[0-9]+$ ]]; then
                local log_file=$(ls -1 "$LOGS_DIR" | sed -n "${choice}p")
                if [ -n "$log_file" ]; then
                    echo -e "\n${CYAN}=== $log_file ===${NC}"
                    tail -n 50 "$LOGS_DIR/$log_file"
                else
                    print_error "Invalid selection"
                fi
            else
                print_error "Invalid input"
            fi
            ;;
    esac
    echo ""
}

# System health check
health_check() {
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo -e "${BLUE}        System Health Check            ${NC}"
    echo -e "${BLUE}═══════════════════════════════════════${NC}\n"
    
    local errors=0
    
    # Check database
    print_info "Checking database integrity..."
    local integrity=$(sqlite3 "$DATABASE_PATH" "PRAGMA integrity_check;")
    if [ "$integrity" == "ok" ]; then
        print_success "Database integrity: OK"
    else
        print_error "Database integrity: FAILED"
        errors=$((errors + 1))
    fi
    
    # Check tables
    print_info "Checking required tables..."
    local required_tables=("users" "login_attempts" "lockouts" "admin_alerts" "sessions")
    
    for table in "${required_tables[@]}"; do
        local exists=$(sqlite3 "$DATABASE_PATH" "SELECT name FROM sqlite_master WHERE type='table' AND name='$table';")
        if [ -n "$exists" ]; then
            print_success "Table '$table': OK"
        else
            print_error "Table '$table': MISSING"
            errors=$((errors + 1))
        fi
    done
    
    # Check directories
    print_info "Checking directories..."
    local required_dirs=("database" "known_faces" "captured_faces")
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$dir" ]; then
            print_success "Directory '$dir': OK"
        else
            print_error "Directory '$dir': MISSING"
            errors=$((errors + 1))
        fi
    done
    
    # Check disk space
    print_info "Checking disk space..."
    local disk_usage=$(df -h . | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $disk_usage -lt 90 ]; then
        print_success "Disk space: OK ($disk_usage% used)"
    else
        print_warning "Disk space: LOW ($disk_usage% used)"
        errors=$((errors + 1))
    fi
    
    # Summary
    echo ""
    if [ $errors -eq 0 ]; then
        print_success "✓ All health checks passed!"
    else
        print_warning "⚠️  $errors issue(s) found"
    fi
    echo ""
}

# Export database to SQL
export_to_sql() {
    print_info "Exporting database to SQL..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local output_file="database_export_$timestamp.sql"
    
    sqlite3 "$DATABASE_PATH" .dump > "$output_file"
    
    if [ $? -eq 0 ]; then
        local size=$(du -h "$output_file" | cut -f1)
        print_success "Exported to: $output_file ($size)"
    else
        print_error "Export failed"
    fi
}

# Show menu
show_menu() {
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo "  1) Backup database"
    echo "  2) List backups"
    echo "  3) Restore database"
    echo "  4) Clean old records"
    echo "  5) View statistics"
    echo "  6) View logs"
    echo "  7) Health check"
    echo "  8) Export to SQL"
    echo "  9) Optimize database"
    echo "  0) Exit"
    echo -e "${BLUE}═══════════════════════════════════════${NC}"
    echo ""
}

# Optimize database
optimize_database() {
    print_info "Optimizing database..."
    
    # Analyze
    print_info "Running ANALYZE..."
    sqlite3 "$DATABASE_PATH" "ANALYZE;"
    
    # Vacuum
    print_info "Running VACUUM..."
    sqlite3 "$DATABASE_PATH" "VACUUM;"
    
    # Reindex
    print_info "Rebuilding indexes..."
    sqlite3 "$DATABASE_PATH" "REINDEX;"
    
    print_success "Database optimized"
    
    # Show new size
    local size=$(du -h "$DATABASE_PATH" | cut -f1)
    echo "New size: $size"
}

# Main function
main() {
    print_banner
    check_prerequisites
    
    # Command line mode
    if [ $# -gt 0 ]; then
        case "$1" in
            backup)
                backup_database
                ;;
            list)
                list_backups
                ;;
            restore)
                restore_database
                ;;
            clean)
                clean_old_records
                ;;
            stats)
                view_statistics
                ;;
            logs)
                view_logs
                ;;
            health)
                health_check
                ;;
            export)
                export_to_sql
                ;;
            optimize)
                optimize_database
                ;;
            *)
                print_error "Unknown command: $1"
                echo ""
                echo "Available commands:"
                echo "  backup   - Create database backup"
                echo "  list     - List backups"
                echo "  restore  - Restore from backup"
                echo "  clean    - Clean old records"
                echo "  stats    - View statistics"
                echo "  logs     - View logs"
                echo "  health   - Run health check"
                echo "  export   - Export to SQL"
                echo "  optimize - Optimize database"
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
                1) backup_database ;;
                2) list_backups ;;
                3) restore_database ;;
                4) clean_old_records ;;
                5) view_statistics ;;
                6) view_logs ;;
                7) health_check ;;
                8) export_to_sql ;;
                9) optimize_database ;;
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

# Run
main "$@"