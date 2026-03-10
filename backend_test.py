#!/usr/bin/env python3
import requests
import sys
import json
from datetime import datetime
import time

class EchoBizAPITester:
    def __init__(self, base_url="https://voice-ledger-12.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_username = f"testuser_{int(time.time())}"
        self.test_password = "TestPass123!"

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
            if details:
                print(f"   Details: {details}")
        else:
            print(f"❌ {name} - FAILED")
            if details:
                print(f"   Error: {details}")
        print()

    def make_request(self, method, endpoint, data=None, expected_status=200):
        """Make API request with error handling"""
        url = f"{self.api_url}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            
            success = response.status_code == expected_status
            return success, response.status_code, response.json() if response.text else {}
            
        except requests.exceptions.Timeout:
            return False, 0, {"error": "Request timeout"}
        except requests.exceptions.ConnectionError:
            return False, 0, {"error": "Connection error"}
        except Exception as e:
            return False, 0, {"error": str(e)}

    def test_user_registration(self):
        """Test user registration endpoint"""
        print("🔍 Testing User Registration...")
        
        success, status, response = self.make_request(
            'POST', '/auth/register', 
            {"username": self.test_username, "password": self.test_password},
            201
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.log_test("User Registration", True, f"Username: {self.test_username}")
            return True
        else:
            error_detail = response.get('detail', f"Status: {status}")
            self.log_test("User Registration", False, error_detail)
            return False

    def test_user_login(self):
        """Test user login endpoint"""
        print("🔍 Testing User Login...")
        
        success, status, response = self.make_request(
            'POST', '/auth/login',
            {"username": self.test_username, "password": self.test_password},
            200
        )
        
        if success and 'token' in response:
            self.token = response['token']
            self.log_test("User Login", True, f"Token received")
            return True
        else:
            error_detail = response.get('detail', f"Status: {status}")
            self.log_test("User Login", False, error_detail)
            return False

    def test_command_processing_sale(self):
        """Test command processing for sales"""
        print("🔍 Testing Sale Command Processing...")
        
        command = "Sold 5 tables for 1000 each"
        success, status, response = self.make_request(
            'POST', '/command',
            {"command": command},
            200
        )
        
        if success and 'message' in response:
            self.log_test("Sale Command Processing", True, f"Message: {response['message']}")
            return True
        else:
            error_detail = response.get('detail', f"Status: {status}")
            self.log_test("Sale Command Processing", False, error_detail)
            return False

    def test_command_processing_expense(self):
        """Test command processing for expenses"""
        print("🔍 Testing Expense Command Processing...")
        
        command = "Bought raw material for 3000"
        success, status, response = self.make_request(
            'POST', '/command',
            {"command": command},
            200
        )
        
        if success and 'message' in response:
            self.log_test("Expense Command Processing", True, f"Message: {response['message']}")
            return True
        else:
            error_detail = response.get('detail', f"Status: {status}")
            self.log_test("Expense Command Processing", False, error_detail)
            return False

    def test_command_processing_payment(self):
        """Test command processing for payments"""
        print("🔍 Testing Payment Command Processing...")
        
        command = "Customer paid 5000 in cash"
        success, status, response = self.make_request(
            'POST', '/command',
            {"command": command},
            200
        )
        
        if success and 'message' in response:
            self.log_test("Payment Command Processing", True, f"Message: {response['message']}")
            return True
        else:
            error_detail = response.get('detail', f"Status: {status}")
            self.log_test("Payment Command Processing", False, error_detail)
            return False

    def test_daily_summary(self):
        """Test daily summary endpoint"""
        print("🔍 Testing Daily Summary...")
        
        success, status, response = self.make_request('GET', '/summary', expected_status=200)
        
        if success and 'sales' in response and 'expenses' in response and 'profit' in response:
            details = f"Sales: ₹{response['sales']}, Expenses: ₹{response['expenses']}, Profit: ₹{response['profit']}"
            self.log_test("Daily Summary", True, details)
            return True
        else:
            error_detail = response.get('detail', f"Status: {status}")
            self.log_test("Daily Summary", False, error_detail)
            return False

    def test_inventory_status(self):
        """Test inventory endpoint"""
        print("🔍 Testing Inventory Status...")
        
        success, status, response = self.make_request('GET', '/inventory', expected_status=200)
        
        if success and isinstance(response, list):
            self.log_test("Inventory Status", True, f"Found {len(response)} inventory items")
            return True
        else:
            error_detail = response.get('detail', f"Status: {status}")
            self.log_test("Inventory Status", False, error_detail)
            return False

    def test_transaction_history(self):
        """Test transaction history endpoint"""
        print("🔍 Testing Transaction History...")
        
        success, status, response = self.make_request('GET', '/transactions', expected_status=200)
        
        if success and isinstance(response, list):
            self.log_test("Transaction History", True, f"Found {len(response)} transactions")
            return True
        else:
            error_detail = response.get('detail', f"Status: {status}")
            self.log_test("Transaction History", False, error_detail)
            return False

    def test_authentication_required(self):
        """Test authentication is required for protected endpoints"""
        print("🔍 Testing Authentication Protection...")
        
        # Temporarily remove token
        original_token = self.token
        self.token = None
        
        success, status, response = self.make_request('GET', '/summary', expected_status=401)
        
        # Restore token
        self.token = original_token
        
        if status == 401:
            self.log_test("Authentication Protection", True, "Protected endpoints require authentication")
            return True
        else:
            self.log_test("Authentication Protection", False, f"Expected 401, got {status}")
            return False

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting EchoBiz API Testing")
        print("=" * 50)
        print(f"Backend URL: {self.base_url}")
        print(f"Test User: {self.test_username}")
        print("=" * 50)
        print()

        # Test registration and authentication
        if not self.test_user_registration():
            print("❌ Registration failed, trying existing user login...")
            if not self.test_user_login():
                print("❌ Both registration and login failed. Stopping tests.")
                return self.get_summary()
        
        # Test authentication protection
        self.test_authentication_required()
        
        # Test command processing
        self.test_command_processing_sale()
        time.sleep(2)  # Wait for LLM processing
        
        self.test_command_processing_expense()
        time.sleep(2)  # Wait for LLM processing
        
        self.test_command_processing_payment()
        time.sleep(2)  # Wait for LLM processing
        
        # Test data retrieval endpoints
        self.test_daily_summary()
        self.test_inventory_status()
        self.test_transaction_history()
        
        return self.get_summary()

    def get_summary(self):
        """Get test summary"""
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print("=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        print("=" * 50)
        
        return {
            "total_tests": self.tests_run,
            "passed_tests": self.tests_passed,
            "failed_tests": self.tests_run - self.tests_passed,
            "success_rate": success_rate,
            "all_passed": self.tests_passed == self.tests_run
        }

def main():
    tester = EchoBizAPITester()
    results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if results["all_passed"] else 1

if __name__ == "__main__":
    sys.exit(main())