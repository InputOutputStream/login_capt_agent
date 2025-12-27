#!/bin/bash

################################################################################
# VC Authentication System - Quick Start
# One command to setup and run everything
################################################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

clear
echo -e "${CYAN}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║        VC AUTHENTICATION SYSTEM - QUICK START                ║
║                                                              ║
║        One-Command Setup & Launch                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}\n"

print_step() {
    echo -e "\n${BLUE}▶ $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ $1${NC}"
}

# Check if already setup
if [ -d "venv" ] && [ -f "database/auth.db" ]; then
    print_success "System already installed!"
    echo ""
    read -p "Start the server now? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_step "Starting VC Authentication System"
        source venv/bin/activate
        
        echo ""
        echo -e "${GREEN}╔══════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║                                                              ║${NC}"
        echo -e "${GREEN}║                 SERVER STARTED!                              ║${NC}"
        echo -e "${GREEN}║                                                              ║${NC}"
        echo -e "${GREEN}╚══════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo -e "${CYAN} Backend:${NC} http://localhost:5000"
        echo -e "${CYAN} Frontend:${NC} Open index.html in your browser"
        echo ""
        echo -e "${YELLOW} Test Credentials:${NC}"
        echo -e "   Email: ${GREEN}test@example.com${NC}"
        echo -e "   Password: ${GREEN}password123${NC}"
        echo ""
        echo -e "${YELLOW}⚠️  Press Ctrl+C to stop the server${NC}"
        echo ""
        
        python app.py
    else
        echo ""
        print_info "To start later, run: ./start.sh"
        exit 0
    fi
else
    # Need to install first
    echo -e "${YELLOW}System not installed. Running setup...${NC}"
    echo ""
    
    if [ -f "master_setup.sh" ]; then
        chmod +x master_setup.sh
        ./master_setup.sh
        
        # After setup, ask if should start
        echo ""
        read -p "Setup complete! Start the server now? (y/n) " -n 1 -r
        echo ""
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            source venv/bin/activate
            echo ""
            print_step "Starting server..."
            python app.py
        else
            print_info "To start later, run: ./start.sh"
        fi
    else
        print_error "master_setup.sh not found!"
        print_info "Please ensure all setup files are present"
        exit 1
    fi
fi