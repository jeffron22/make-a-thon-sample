#!/usr/bin/env python3
"""
Smart Attendance System Backend API Tests
Tests all backend endpoints with realistic data
"""

import requests
import json
import base64
from datetime import datetime, timedelta
import time
import sys
import os

# Get backend URL from frontend .env
BACKEND_URL = "https://facetrack-school.preview.emergentagent.com/api"

class AttendanceSystemTester:
    def __init__(self):
        self.base_url = BACKEND_URL
        self.teacher_token = None
        self.student_token = None
        self.teacher_data = None
        self.student_data = None
        self.test_results = []
        
    def log_test(self, test_name, success, message="", response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "response_data": response_data
        })
    
    def create_dummy_base64_image(self):
        """Create a simple base64 encoded image for testing"""
        # Create a simple 100x100 RGB image data
        import io
        try:
            from PIL import Image
            import numpy as np
            
            # Create a simple face-like image (just for testing)
            img_array = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
            img = Image.fromarray(img_array)
            
            buffer = io.BytesIO()
            img.save(buffer, format='JPEG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            return f"data:image/jpeg;base64,{img_str}"
        except ImportError:
            # Fallback: create a minimal base64 image
            # This is a 1x1 pixel JPEG
            minimal_jpeg = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/8A"
            return f"data:image/jpeg;base64,{minimal_jpeg}"
    
    def test_teacher_registration(self):
        """Test teacher account registration"""
        url = f"{self.base_url}/auth/register"
        
        # Use timestamp to ensure unique email
        import time
        timestamp = str(int(time.time()))
        
        teacher_payload = {
            "email": f"sarah.johnson.{timestamp}@school.edu",
            "password": "TeacherPass123!",
            "name": "Sarah Johnson",
            "role": "teacher"
        }
        
        try:
            response = requests.post(url, json=teacher_payload)
            
            if response.status_code == 200:
                data = response.json()
                self.teacher_token = data.get("access_token")
                self.teacher_data = data.get("user")
                self.log_test("Teacher Registration", True, f"Teacher registered successfully: {self.teacher_data['name']}")
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                # Try to login instead
                self.log_test("Teacher Registration", True, "Email already exists, will use login instead")
                return True
            else:
                self.log_test("Teacher Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Teacher Registration", False, f"Exception: {str(e)}")
            return False
    
    def test_student_registration(self):
        """Test student account registration"""
        url = f"{self.base_url}/auth/register"
        
        # Use timestamp to ensure unique email
        import time
        timestamp = str(int(time.time()))
        
        student_payload = {
            "email": f"alex.chen.{timestamp}@student.edu",
            "password": "StudentPass123!",
            "name": "Alex Chen",
            "role": "student",
            "student_id": f"STU2025{timestamp[-3:]}"  # Use last 3 digits of timestamp
        }
        
        try:
            response = requests.post(url, json=student_payload)
            
            if response.status_code == 200:
                data = response.json()
                self.student_token = data.get("access_token")
                self.student_data = data.get("user")
                self.log_test("Student Registration", True, f"Student registered successfully: {self.student_data['name']} (ID: {self.student_data['student_id']})")
                return True
            elif response.status_code == 400 and "already registered" in response.text:
                # Try to login instead
                self.log_test("Student Registration", True, "Email already exists, will use login instead")
                return True
            else:
                self.log_test("Student Registration", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Student Registration", False, f"Exception: {str(e)}")
            return False
    
    def test_teacher_login(self):
        """Test teacher login"""
        url = f"{self.base_url}/auth/login"
        
        login_payload = {
            "email": "sarah.johnson@school.edu",
            "password": "TeacherPass123!"
        }
        
        try:
            response = requests.post(url, json=login_payload)
            
            if response.status_code == 200:
                data = response.json()
                self.teacher_token = data.get("access_token")
                self.log_test("Teacher Login", True, f"Login successful for {data['user']['name']}")
                return True
            else:
                self.log_test("Teacher Login", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Teacher Login", False, f"Exception: {str(e)}")
            return False
    
    def test_student_login(self):
        """Test student login"""
        url = f"{self.base_url}/auth/login"
        
        login_payload = {
            "email": "alex.chen@student.edu",
            "password": "StudentPass123!"
        }
        
        try:
            response = requests.post(url, json=login_payload)
            
            if response.status_code == 200:
                data = response.json()
                self.student_token = data.get("access_token")
                self.student_data = data.get("user")  # Capture student data here
                self.log_test("Student Login", True, f"Login successful for {data['user']['name']}")
                return True
            else:
                self.log_test("Student Login", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Student Login", False, f"Exception: {str(e)}")
            return False
    
    def test_auth_me_valid_token(self):
        """Test GET /api/auth/me with valid token"""
        url = f"{self.base_url}/auth/me"
        
        headers = {"Authorization": f"Bearer {self.teacher_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Auth Me (Valid Token)", True, f"Retrieved user info: {data['name']} ({data['role']})")
                return True
            else:
                self.log_test("Auth Me (Valid Token)", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Auth Me (Valid Token)", False, f"Exception: {str(e)}")
            return False
    
    def test_auth_me_invalid_token(self):
        """Test GET /api/auth/me with invalid token"""
        url = f"{self.base_url}/auth/me"
        
        headers = {"Authorization": "Bearer invalid_token_12345"}
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 401:
                self.log_test("Auth Me (Invalid Token)", True, "Correctly rejected invalid token")
                return True
            else:
                self.log_test("Auth Me (Invalid Token)", False, f"Expected 401, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Auth Me (Invalid Token)", False, f"Exception: {str(e)}")
            return False
    
    def test_bulk_student_upload(self):
        """Test bulk student upload with face photos"""
        url = f"{self.base_url}/students/bulk-upload"
        
        headers = {"Authorization": f"Bearer {self.teacher_token}"}
        
        # Create dummy base64 images
        dummy_image = self.create_dummy_base64_image()
        
        students_payload = [
            {
                "student_id": "STU2025002",
                "name": "Emma Rodriguez",
                "email": "emma.rodriguez@student.edu",
                "photos": [dummy_image, dummy_image]
            },
            {
                "student_id": "STU2025003", 
                "name": "Michael Kim",
                "email": "michael.kim@student.edu",
                "photos": [dummy_image]
            }
        ]
        
        try:
            response = requests.post(url, json=students_payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                success_count = len([r for r in results if r.get("status") == "success"])
                self.log_test("Bulk Student Upload", True, f"Uploaded {success_count}/{len(students_payload)} students successfully")
                return True
            else:
                self.log_test("Bulk Student Upload", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Bulk Student Upload", False, f"Exception: {str(e)}")
            return False
    
    def test_get_students(self):
        """Test GET /api/students to retrieve all students"""
        url = f"{self.base_url}/students"
        
        headers = {"Authorization": f"Bearer {self.teacher_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                student_count = len(data)
                face_encoding_count = len([s for s in data if s.get("has_face_encoding")])
                self.log_test("Get Students", True, f"Retrieved {student_count} students, {face_encoding_count} with face encodings")
                return True
            else:
                self.log_test("Get Students", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Students", False, f"Exception: {str(e)}")
            return False
    
    def test_student_attendance_access(self):
        """Test GET /api/attendance/student/{student_id} as student"""
        if not self.student_data:
            self.log_test("Student Attendance Access", False, "No student data available")
            return False
            
        student_id = self.student_data.get("student_id")
        url = f"{self.base_url}/attendance/student/{student_id}"
        
        headers = {"Authorization": f"Bearer {self.student_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                stats = data.get("statistics", {})
                self.log_test("Student Attendance Access", True, f"Retrieved attendance: {stats.get('present_days', 0)} present days, {stats.get('percentage', 0)}% attendance")
                return True
            else:
                self.log_test("Student Attendance Access", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Student Attendance Access", False, f"Exception: {str(e)}")
            return False
    
    def test_teacher_attendance_all(self):
        """Test GET /api/attendance/all as teacher"""
        today = datetime.now().strftime('%Y-%m-%d')
        url = f"{self.base_url}/attendance/all?date={today}"
        
        headers = {"Authorization": f"Bearer {self.teacher_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Teacher Attendance All", True, f"Retrieved {len(data)} attendance records for {today}")
                return True
            else:
                self.log_test("Teacher Attendance All", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Teacher Attendance All", False, f"Exception: {str(e)}")
            return False
    
    def test_attendance_override(self):
        """Test POST /api/attendance/override (manual attendance marking)"""
        url = f"{self.base_url}/attendance/override"
        
        headers = {"Authorization": f"Bearer {self.teacher_token}"}
        
        today = datetime.now().strftime('%Y-%m-%d')
        override_payload = {
            "student_id": "STU2025001",
            "date": today,
            "status": "present"
        }
        
        try:
            response = requests.post(url, json=override_payload, headers=headers)
            
            if response.status_code == 200:
                self.log_test("Attendance Override", True, f"Successfully marked STU2025001 as present for {today}")
                return True
            else:
                self.log_test("Attendance Override", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Attendance Override", False, f"Exception: {str(e)}")
            return False
    
    def test_create_curriculum(self):
        """Test POST /api/curriculum as teacher"""
        url = f"{self.base_url}/curriculum"
        
        headers = {"Authorization": f"Bearer {self.teacher_token}"}
        
        today = datetime.now().strftime('%Y-%m-%d')
        curriculum_payload = {
            "date": today,
            "subject": "Computer Science",
            "topics": "Introduction to Machine Learning and Neural Networks",
            "notes": "Covered basic concepts of supervised learning, neural network architecture, and practical applications in image recognition."
        }
        
        try:
            response = requests.post(url, json=curriculum_payload, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Create Curriculum", True, f"Created curriculum entry: {curriculum_payload['subject']} - {curriculum_payload['topics'][:50]}...")
                return True
            else:
                self.log_test("Create Curriculum", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Curriculum", False, f"Exception: {str(e)}")
            return False
    
    def test_get_curriculum(self):
        """Test GET /api/curriculum"""
        url = f"{self.base_url}/curriculum"
        
        headers = {"Authorization": f"Bearer {self.student_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                self.log_test("Get Curriculum", True, f"Retrieved {len(data)} curriculum entries")
                return True
            else:
                self.log_test("Get Curriculum", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Get Curriculum", False, f"Exception: {str(e)}")
            return False
    
    def test_cctv_config(self):
        """Test CCTV configuration endpoints"""
        # Test POST /api/cctv/config
        url = f"{self.base_url}/cctv/config"
        headers = {"Authorization": f"Bearer {self.teacher_token}"}
        
        config_payload = {
            "stream_url": "rtsp://admin:password@192.168.1.100:554/stream1",
            "is_active": True
        }
        
        try:
            response = requests.post(url, json=config_payload, headers=headers)
            
            if response.status_code == 200:
                self.log_test("CCTV Config (POST)", True, "CCTV configuration updated successfully")
                
                # Test GET /api/cctv/config
                get_response = requests.get(url, headers=headers)
                if get_response.status_code == 200:
                    config_data = get_response.json()
                    self.log_test("CCTV Config (GET)", True, f"Retrieved config: Active={config_data.get('is_active')}")
                    return True
                else:
                    self.log_test("CCTV Config (GET)", False, f"Status: {get_response.status_code}")
                    return False
            else:
                self.log_test("CCTV Config (POST)", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("CCTV Config", False, f"Exception: {str(e)}")
            return False
    
    def test_student_dashboard(self):
        """Test GET /api/dashboard/student/{student_id}"""
        if not self.student_data:
            self.log_test("Student Dashboard", False, "No student data available")
            return False
            
        student_id = self.student_data.get("student_id")
        url = f"{self.base_url}/dashboard/student/{student_id}"
        
        headers = {"Authorization": f"Bearer {self.student_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                attendance = data.get("attendance", {})
                curriculum_count = len(data.get("curriculum", []))
                self.log_test("Student Dashboard", True, f"Dashboard loaded: {attendance.get('percentage', 0)}% attendance, {curriculum_count} curriculum entries")
                return True
            else:
                self.log_test("Student Dashboard", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Student Dashboard", False, f"Exception: {str(e)}")
            return False
    
    def test_teacher_dashboard(self):
        """Test GET /api/dashboard/teacher"""
        url = f"{self.base_url}/dashboard/teacher"
        
        headers = {"Authorization": f"Bearer {self.teacher_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                total_students = data.get("total_students", 0)
                today_attendance = data.get("today_attendance", {})
                self.log_test("Teacher Dashboard", True, f"Dashboard loaded: {total_students} total students, {today_attendance.get('present', 0)} present today")
                return True
            else:
                self.log_test("Teacher Dashboard", False, f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Teacher Dashboard", False, f"Exception: {str(e)}")
            return False
    
    def test_role_based_access_control(self):
        """Test that students cannot access teacher-only endpoints"""
        # Test student trying to access teacher-only endpoint
        url = f"{self.base_url}/students"
        headers = {"Authorization": f"Bearer {self.student_token}"}
        
        try:
            response = requests.get(url, headers=headers)
            
            if response.status_code == 403:
                self.log_test("Role-Based Access Control", True, "Student correctly denied access to teacher endpoint")
                return True
            else:
                self.log_test("Role-Based Access Control", False, f"Expected 403, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Role-Based Access Control", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend API tests"""
        print(f"\n🚀 Starting Smart Attendance System Backend API Tests")
        print(f"Backend URL: {self.base_url}")
        print("=" * 80)
        
        # Authentication Tests
        print("\n📋 AUTHENTICATION TESTS")
        print("-" * 40)
        self.test_teacher_registration()
        self.test_student_registration()
        self.test_teacher_login()
        self.test_student_login()
        self.test_auth_me_valid_token()
        self.test_auth_me_invalid_token()
        
        # Student Management Tests (Teacher only)
        print("\n👥 STUDENT MANAGEMENT TESTS")
        print("-" * 40)
        self.test_bulk_student_upload()
        self.test_get_students()
        
        # Attendance Tests
        print("\n📊 ATTENDANCE TESTS")
        print("-" * 40)
        self.test_student_attendance_access()
        self.test_teacher_attendance_all()
        self.test_attendance_override()
        
        # Curriculum Tests
        print("\n📚 CURRICULUM TESTS")
        print("-" * 40)
        self.test_create_curriculum()
        self.test_get_curriculum()
        
        # CCTV Configuration Tests
        print("\n📹 CCTV CONFIGURATION TESTS")
        print("-" * 40)
        self.test_cctv_config()
        
        # Dashboard Tests
        print("\n📈 DASHBOARD TESTS")
        print("-" * 40)
        self.test_student_dashboard()
        self.test_teacher_dashboard()
        
        # Security Tests
        print("\n🔒 SECURITY TESTS")
        print("-" * 40)
        self.test_role_based_access_control()
        
        # Summary
        print("\n" + "=" * 80)
        print("📋 TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for test in self.test_results:
                if not test["success"]:
                    print(f"  - {test['test']}: {test['message']}")
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = AttendanceSystemTester()
    passed, failed = tester.run_all_tests()
    
    # Exit with error code if tests failed
    sys.exit(0 if failed == 0 else 1)