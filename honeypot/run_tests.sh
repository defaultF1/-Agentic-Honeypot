#!/bin/bash

# Comprehensive Honeypot API Test Script
# Tests all critical scenarios automatically

set -e  # Exit on error

echo "======================================================================"
echo "HONEYPOT API COMPREHENSIVE TEST SUITE"
echo "======================================================================"
echo ""

# Configuration
API_URL="${API_URL:-http://localhost:8000}"
API_KEY="${API_KEY:-test-key-change-in-production}"
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to make API calls
make_request() {
    local endpoint="$1"
    local data="$2"
    local headers="$3"
    
    curl -s -w "\n%{http_code}" -X POST "${API_URL}${endpoint}" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: ${API_KEY}" \
        ${headers} \
        -d "${data}" 2>/dev/null
}

# Function to test and report
test_scenario() {
    local name="$1"
    local data="$2"
    local expected_status="$3"
    local check_field="$4"
    local expected_value="$5"
    
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    
    echo -n "Testing: ${name}... "
    
    START_TIME=$(date +%s.%N)
    
    # Make request
    RESPONSE=$(make_request "/api/v1/honeypot" "${data}")
    
    END_TIME=$(date +%s.%N)
    DURATION=$(echo "$END_TIME - $START_TIME" | bc)
    
    # Extract status code (last line)
    HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
    BODY=$(echo "$RESPONSE" | sed '$d')
    
    # Check status code
    if [ "$HTTP_STATUS" != "$expected_status" ]; then
        echo -e "${RED}FAILED${NC}"
        echo "  Expected status: $expected_status, got: $HTTP_STATUS"
        echo "  Response: $BODY"
        FAILED_TESTS=$((FAILED_TESTS + 1))
        return 1
    fi
    
    # Check response time
    if (( $(echo "$DURATION > 3.0" | bc -l) )); then
        echo -e "${YELLOW}SLOW${NC} (${DURATION}s)"
    fi
    
    # Check specific field if requested
    if [ -n "$check_field" ] && [ -n "$expected_value" ]; then
        ACTUAL_VALUE=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)${check_field})" 2>/dev/null || echo "NOT_FOUND")
        
        if [ "$ACTUAL_VALUE" != "$expected_value" ]; then
            echo -e "${RED}FAILED${NC}"
            echo "  Expected ${check_field}=${expected_value}, got: ${ACTUAL_VALUE}"
            FAILED_TESTS=$((FAILED_TESTS + 1))
            return 1
        fi
    fi
    
    echo -e "${GREEN}PASSED${NC} (${DURATION}s)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    return 0
}

# Test 1: Health Check
echo "----------------------------------------------------------------------"
echo "1. HEALTH CHECK"
echo "----------------------------------------------------------------------"

HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "${API_URL}/health")
if [ "$HTTP_STATUS" == "200" ]; then
    echo -e "Health endpoint: ${GREEN}PASSED${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "Health endpoint: ${RED}FAILED${NC} (Status: $HTTP_STATUS)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
TOTAL_TESTS=$((TOTAL_TESTS + 1))

# Test 2: Authentication
echo ""
echo "----------------------------------------------------------------------"
echo "2. AUTHENTICATION TESTS"
echo "----------------------------------------------------------------------"

# Missing API key
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "Testing: Missing API Key... "
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/api/v1/honeypot" \
    -H "Content-Type: application/json" \
    -d '{"message": "test"}')
HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_STATUS" == "401" ]; then
    echo -e "${GREEN}PASSED${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}FAILED${NC} (Expected 401, got $HTTP_STATUS)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Invalid API key
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "Testing: Invalid API Key... "
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${API_URL}/api/v1/honeypot" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: wrong-key" \
    -d '{"message": "test"}')
HTTP_STATUS=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_STATUS" == "403" ]; then
    echo -e "${GREEN}PASSED${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}FAILED${NC} (Expected 403, got $HTTP_STATUS)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 3: Scam Detection Scenarios
echo ""
echo "----------------------------------------------------------------------"
echo "3. SCAM DETECTION TESTS"
echo "----------------------------------------------------------------------"

# Digital Arrest
test_scenario "Digital Arrest Scam" \
    '{"message": "This is Inspector Raj from CBI. Your Aadhaar is linked to money laundering. Transfer Rs 50000 to account 123456789012 IFSC SBIN0001234 or face arrest. Call +919876543210"}' \
    "200" \
    "['scam_detection']['is_scam']" \
    "True"

# UPI Fraud
test_scenario "UPI Fraud" \
    '{"message": "Paytm Support here. Send Rs 1 to verify@paytm for KYC verification or account will be blocked."}' \
    "200" \
    "['scam_detection']['is_scam']" \
    "True"

# Job Scam
test_scenario "Job Scam" \
    '{"message": "Congratulations! You got the job. Pay Rs 999 registration fee to account 112233445566. Contact hr@company.in"}' \
    "200" \
    "['scam_detection']['is_scam']" \
    "True"

# Non-scam
test_scenario "Non-scam Message" \
    '{"message": "Hi, what is the price of your product?"}' \
    "200" \
    "['scam_detection']['is_scam']" \
    "False"

# Test 4: Extraction Tests
echo ""
echo "----------------------------------------------------------------------"
echo "4. INTELLIGENCE EXTRACTION TESTS"
echo "----------------------------------------------------------------------"

# Bank account extraction
test_scenario "Bank Account Extraction" \
    '{"message": "Send money to account 1234567890123456 IFSC code SBIN0001234"}' \
    "200" \
    "" \
    ""

# UPI ID extraction
test_scenario "UPI ID Extraction" \
    '{"message": "My UPI is fraudster@ybl for payment"}' \
    "200" \
    "" \
    ""

# Phone extraction
test_scenario "Phone Number Extraction" \
    '{"message": "Call me on +919876543210 for details"}' \
    "200" \
    "" \
    ""

# URL extraction
test_scenario "URL Extraction" \
    '{"message": "Click here to verify: http://fake-bank-site.tk/login"}' \
    "200" \
    "" \
    ""

# Test 5: Complex Scenarios
echo ""
echo "----------------------------------------------------------------------"
echo "5. COMPLEX SCENARIOS"
echo "----------------------------------------------------------------------"

# Multi-intel extraction
test_scenario "Multiple Intel Types" \
    '{"message": "Inspector Sharma here. Transfer to account 9876543210987654 IFSC HDFC0005678. Contact me at +919988776655 or email inspector@cbi-fake.in. Visit http://cbi-verify.tk for details."}' \
    "200" \
    "" \
    ""

# Long message
test_scenario "Long Message (500+ chars)" \
    '{"message": "This is a very long scam message with lots of details about how you have committed a crime and need to pay money immediately to avoid arrest. The CBI is monitoring your account and you must transfer funds to account number 1111222233334444 with IFSC code ICIC0001234. You can also use UPI ID criminal@okicici or call us at +919999888777. Visit our website at http://police-verification.xyz for more information about your case. This is urgent and you must act within 24 hours or face legal action."}' \
    "200" \
    "" \
    ""

# Test 6: JSON Structure Validation
echo ""
echo "----------------------------------------------------------------------"
echo "6. JSON STRUCTURE VALIDATION"
echo "----------------------------------------------------------------------"

TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "Testing: JSON Structure Consistency... "

RESPONSE=$(make_request "/api/v1/honeypot" '{"message": "Test message for structure validation"}')
BODY=$(echo "$RESPONSE" | sed '$d')

# Check required fields
REQUIRED_FIELDS=("session_id" "timestamp" "scam_detection" "honeypot_response" "extracted_intelligence" "engagement_metrics" "conversation_state")
ALL_FIELDS_PRESENT=true

for field in "${REQUIRED_FIELDS[@]}"; do
    if ! echo "$BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); exit(0 if '${field}' in d else 1)" 2>/dev/null; then
        echo -e "${RED}FAILED${NC} - Missing field: ${field}"
        ALL_FIELDS_PRESENT=false
        break
    fi
done

if [ "$ALL_FIELDS_PRESENT" = true ]; then
    echo -e "${GREEN}PASSED${NC}"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 7: Performance Check
echo ""
echo "----------------------------------------------------------------------"
echo "7. PERFORMANCE TESTS"
echo "----------------------------------------------------------------------"

TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "Testing: Response Time Under 3 Seconds... "

START=$(date +%s.%N)
RESPONSE=$(make_request "/api/v1/honeypot" '{"message": "Speed test message"}')
END=$(date +%s.%N)
DURATION=$(echo "$END - $START" | bc)

if (( $(echo "$DURATION < 3.0" | bc -l) )); then
    echo -e "${GREEN}PASSED${NC} (${DURATION}s)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo -e "${RED}FAILED${NC} (${DURATION}s - too slow)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Test 8: Session Management
echo ""
echo "----------------------------------------------------------------------"
echo "8. SESSION MANAGEMENT"
echo "----------------------------------------------------------------------"

# Create session
TOTAL_TESTS=$((TOTAL_TESTS + 1))
echo -n "Testing: Session Creation... "
RESPONSE=$(make_request "/api/v1/honeypot" '{"message": "First message"}')
BODY=$(echo "$RESPONSE" | sed '$d')
SESSION_ID=$(echo "$BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])" 2>/dev/null || echo "")

if [ -n "$SESSION_ID" ] && [ "$SESSION_ID" != "None" ]; then
    echo -e "${GREEN}PASSED${NC} (Session: ${SESSION_ID:0:8}...)"
    PASSED_TESTS=$((PASSED_TESTS + 1))
    
    # Test session continuation
    TOTAL_TESTS=$((TOTAL_TESTS + 1))
    echo -n "Testing: Session Continuation... "
    
    CONT_RESPONSE=$(make_request "/api/v1/honeypot" "{\"session_id\": \"${SESSION_ID}\", \"message\": \"Second message\", \"conversation_history\": [{\"role\": \"scammer\", \"content\": \"First message\"}]}")
    CONT_BODY=$(echo "$CONT_RESPONSE" | sed '$d')
    CONT_SESSION=$(echo "$CONT_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['session_id'])" 2>/dev/null || echo "")
    TURN_NUMBER=$(echo "$CONT_BODY" | python3 -c "import sys,json; print(json.load(sys.stdin)['engagement_metrics']['turn_number'])" 2>/dev/null || echo "0")
    
    if [ "$CONT_SESSION" == "$SESSION_ID" ] && [ "$TURN_NUMBER" -ge 2 ]; then
        echo -e "${GREEN}PASSED${NC}"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}FAILED${NC}"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo -e "${RED}FAILED${NC} (No session_id returned)"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

# Summary
echo ""
echo "======================================================================"
echo "TEST SUMMARY"
echo "======================================================================"
echo ""
echo "Total Tests:    $TOTAL_TESTS"
echo -e "Passed:         ${GREEN}$PASSED_TESTS${NC}"
echo -e "Failed:         ${RED}$FAILED_TESTS${NC}"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✅ ALL TESTS PASSED - READY FOR DEPLOYMENT${NC}"
    echo ""
    exit 0
else
    echo -e "${RED}❌ SOME TESTS FAILED - FIX ISSUES BEFORE DEPLOYMENT${NC}"
    echo ""
    exit 1
fi