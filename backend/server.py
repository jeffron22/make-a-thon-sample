from fastapi import FastAPI, APIRouter, HTTPException, Depends, BackgroundTasks, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import bcrypt
import jwt
from bson import ObjectId
import threading
import time
import base64
from io import BytesIO
from PIL import Image
import numpy as np
import cv2
from deepface import DeepFace
import asyncio

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days

# Security
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============= Models =============

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str  # 'student' or 'teacher'
    student_id: Optional[str] = None  # Required for students

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict

class StudentUpload(BaseModel):
    student_id: str
    name: str
    email: EmailStr
    photos: List[str]  # Base64 encoded images

class AttendanceOverride(BaseModel):
    student_id: str
    date: str
    status: str  # 'present' or 'absent'

class CurriculumCreate(BaseModel):
    date: str
    subject: str
    topics: str
    notes: Optional[str] = None

class CCTVConfig(BaseModel):
    stream_url: str
    is_active: bool

# ============= Helper Functions =============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_id: str, email: str, role: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def base64_to_numpy(base64_string: str):
    """Convert base64 string to numpy array"""
    try:
        # Remove data URL prefix if present
        if 'base64,' in base64_string:
            base64_string = base64_string.split('base64,')[1]
        
        img_data = base64.b64decode(base64_string)
        img = Image.open(BytesIO(img_data))
        return np.array(img)
    except Exception as e:
        logging.error(f"Error converting base64 to numpy: {e}")
        return None

def numpy_to_base64(img_array):
    """Convert numpy array to base64 string"""
    try:
        img = Image.fromarray(img_array)
        buffer = BytesIO()
        img.save(buffer, format='JPEG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        return f"data:image/jpeg;base64,{img_str}"
    except Exception as e:
        logging.error(f"Error converting numpy to base64: {e}")
        return None

def extract_face_embedding(img_array):
    """Extract face embedding using DeepFace"""
    try:
        # DeepFace expects BGR format
        embedding = DeepFace.represent(img_array, model_name='Facenet', enforce_detection=False)[0]['embedding']
        return embedding
    except Exception as e:
        logging.error(f"Error extracting face embedding: {e}")
        return None

def compare_faces(embedding1, embedding2, threshold=0.6):
    """Compare two face embeddings"""
    try:
        # Calculate cosine similarity
        embedding1 = np.array(embedding1)
        embedding2 = np.array(embedding2)
        similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        return similarity > threshold
    except Exception as e:
        logging.error(f"Error comparing faces: {e}")
        return False

# ============= Background CCTV Processing =============

class CCTVProcessor:
    def __init__(self):
        self.is_running = False
        self.thread = None
        self.stream_url = None
        
    def start(self, stream_url: str):
        if not self.is_running:
            self.stream_url = stream_url
            self.is_running = True
            self.thread = threading.Thread(target=self._process_stream, daemon=True)
            self.thread.start()
            logging.info(f"CCTV processor started with URL: {stream_url}")
    
    def stop(self):
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=5)
        logging.info("CCTV processor stopped")
    
    def _process_stream(self):
        """Process CCTV stream and mark attendance"""
        cap = None
        try:
            cap = cv2.VideoCapture(self.stream_url)
            frame_count = 0
            
            while self.is_running:
                ret, frame = cap.read()
                if not ret:
                    logging.warning("Failed to read frame from CCTV stream")
                    time.sleep(5)
                    cap = cv2.VideoCapture(self.stream_url)
                    continue
                
                # Process every 30th frame (reduce CPU usage)
                frame_count += 1
                if frame_count % 30 != 0:
                    continue
                
                # Detect and recognize faces
                asyncio.run(self._process_frame(frame))
                
                time.sleep(1)  # Process 1 frame per second
                
        except Exception as e:
            logging.error(f"Error in CCTV processing: {e}")
        finally:
            if cap:
                cap.release()
    
    async def _process_frame(self, frame):
        """Process a single frame and mark attendance"""
        try:
            # Get all face encodings from database
            face_encodings_cursor = db.face_encodings.find({})
            face_encodings_list = await face_encodings_cursor.to_list(length=1000)
            
            if not face_encodings_list:
                return
            
            # Try to detect faces in frame
            try:
                # Extract face embeddings from current frame
                detected_embeddings = DeepFace.represent(frame, model_name='Facenet', enforce_detection=True)
            except:
                return  # No faces detected
            
            today = datetime.utcnow().strftime('%Y-%m-%d')
            
            # Match each detected face
            for detected in detected_embeddings:
                detected_embedding = detected['embedding']
                
                # Compare with stored embeddings
                for stored in face_encodings_list:
                    student_id = stored['student_id']
                    
                    # Check if already marked present today
                    existing_attendance = await db.attendance.find_one({
                        'student_id': student_id,
                        'date': today
                    })
                    
                    if existing_attendance and existing_attendance.get('status') == 'present':
                        continue
                    
                    # Compare each stored encoding with detected face
                    for stored_embedding in stored['embeddings']:
                        if compare_faces(detected_embedding, stored_embedding):
                            # Mark attendance
                            await db.attendance.update_one(
                                {'student_id': student_id, 'date': today},
                                {
                                    '$set': {
                                        'student_id': student_id,
                                        'date': today,
                                        'status': 'present',
                                        'marked_by': 'auto',
                                        'timestamp': datetime.utcnow()
                                    }
                                },
                                upsert=True
                            )
                            logging.info(f"Marked attendance for student: {student_id}")
                            break
        
        except Exception as e:
            logging.error(f"Error processing frame: {e}")

cctv_processor = CCTVProcessor()

# ============= Authentication Routes =============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate role
    if user_data.role not in ['student', 'teacher']:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    # For students, student_id is required
    if user_data.role == 'student' and not user_data.student_id:
        raise HTTPException(status_code=400, detail="Student ID required for students")
    
    # Create user
    user_doc = {
        "_id": str(uuid.uuid4()),
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "name": user_data.name,
        "role": user_data.role,
        "student_id": user_data.student_id,
        "created_at": datetime.utcnow()
    }
    
    await db.users.insert_one(user_doc)
    
    # Generate token
    token = create_token(user_doc["_id"], user_doc["email"], user_doc["role"])
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user_doc["_id"],
            "email": user_doc["email"],
            "name": user_doc["name"],
            "role": user_doc["role"],
            "student_id": user_doc["student_id"]
        }
    }

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    # Find user
    user = await db.users.find_one({"email": credentials.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    if not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Generate token
    token = create_token(user["_id"], user["email"], user["role"])
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["_id"],
            "email": user["email"],
            "name": user["name"],
            "role": user["role"],
            "student_id": user.get("student_id")
        }
    }

@api_router.get("/auth/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"_id": current_user["user_id"]})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": user["_id"],
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "student_id": user.get("student_id")
    }

# ============= Student Management (Teacher Only) =============

@api_router.post("/students/bulk-upload")
async def bulk_upload_students(students: List[StudentUpload], current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can upload students")
    
    results = []
    
    for student_data in students:
        try:
            # Check if student already exists
            existing = await db.users.find_one({"student_id": student_data.student_id})
            if existing:
                results.append({"student_id": student_data.student_id, "status": "already_exists"})
                continue
            
            # Create user account for student
            user_doc = {
                "_id": str(uuid.uuid4()),
                "email": student_data.email,
                "password_hash": hash_password("default123"),  # Default password
                "name": student_data.name,
                "role": "student",
                "student_id": student_data.student_id,
                "created_at": datetime.utcnow()
            }
            await db.users.insert_one(user_doc)
            
            # Process face images and create embeddings
            embeddings = []
            for photo_base64 in student_data.photos:
                img_array = base64_to_numpy(photo_base64)
                if img_array is not None:
                    embedding = extract_face_embedding(img_array)
                    if embedding:
                        embeddings.append(embedding)
            
            if embeddings:
                # Store face encodings
                face_doc = {
                    "_id": str(uuid.uuid4()),
                    "student_id": student_data.student_id,
                    "embeddings": embeddings,
                    "photos": student_data.photos,
                    "created_at": datetime.utcnow()
                }
                await db.face_encodings.insert_one(face_doc)
                results.append({"student_id": student_data.student_id, "status": "success", "embeddings_count": len(embeddings)})
            else:
                results.append({"student_id": student_data.student_id, "status": "no_face_detected"})
        
        except Exception as e:
            logging.error(f"Error processing student {student_data.student_id}: {e}")
            results.append({"student_id": student_data.student_id, "status": "error", "message": str(e)})
    
    return {"results": results}

@api_router.get("/students")
async def get_students(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view all students")
    
    students = await db.users.find({"role": "student"}).to_list(1000)
    
    # Get face enrollment status
    result = []
    for student in students:
        face_encoding = await db.face_encodings.find_one({"student_id": student["student_id"]})
        result.append({
            "id": student["_id"],
            "name": student["name"],
            "email": student["email"],
            "student_id": student["student_id"],
            "has_face_encoding": face_encoding is not None
        })
    
    return result

# ============= Attendance Routes =============

@api_router.get("/attendance/student/{student_id}")
async def get_student_attendance(student_id: str, current_user: dict = Depends(get_current_user)):
    # Students can only view their own attendance
    if current_user["role"] == "student" and current_user.get("user_id"):
        user = await db.users.find_one({"_id": current_user["user_id"]})
        if user and user.get("student_id") != student_id:
            raise HTTPException(status_code=403, detail="Cannot view other student's attendance")
    
    attendance_records = await db.attendance.find({"student_id": student_id}).sort("date", -1).to_list(1000)
    
    # Calculate statistics
    total_days = len(attendance_records)
    present_days = len([r for r in attendance_records if r["status"] == "present"])
    percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    return {
        "student_id": student_id,
        "attendance_records": attendance_records,
        "statistics": {
            "total_days": total_days,
            "present_days": present_days,
            "absent_days": total_days - present_days,
            "percentage": round(percentage, 2)
        }
    }

@api_router.post("/attendance/override")
async def override_attendance(data: AttendanceOverride, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can override attendance")
    
    await db.attendance.update_one(
        {"student_id": data.student_id, "date": data.date},
        {
            "$set": {
                "student_id": data.student_id,
                "date": data.date,
                "status": data.status,
                "marked_by": "teacher",
                "teacher_id": current_user["user_id"],
                "timestamp": datetime.utcnow()
            }
        },
        upsert=True
    )
    
    return {"message": "Attendance updated successfully"}

@api_router.get("/attendance/all")
async def get_all_attendance(date: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view all attendance")
    
    query = {}
    if date:
        query["date"] = date
    else:
        # Default to today
        query["date"] = datetime.utcnow().strftime('%Y-%m-%d')
    
    attendance_records = await db.attendance.find(query).to_list(1000)
    
    # Get student details
    result = []
    for record in attendance_records:
        student = await db.users.find_one({"student_id": record["student_id"]})
        if student:
            result.append({
                "student_id": record["student_id"],
                "student_name": student["name"],
                "date": record["date"],
                "status": record["status"],
                "marked_by": record.get("marked_by", "auto"),
                "timestamp": record.get("timestamp")
            })
    
    return result

# ============= Curriculum Routes =============

@api_router.post("/curriculum")
async def create_curriculum(data: CurriculumCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can create curriculum")
    
    curriculum_doc = {
        "_id": str(uuid.uuid4()),
        "date": data.date,
        "subject": data.subject,
        "topics": data.topics,
        "notes": data.notes,
        "teacher_id": current_user["user_id"],
        "created_at": datetime.utcnow()
    }
    
    await db.curriculum.insert_one(curriculum_doc)
    
    return {"message": "Curriculum created successfully", "id": curriculum_doc["_id"]}

@api_router.get("/curriculum")
async def get_curriculum(date: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if date:
        query["date"] = date
    
    curriculum_records = await db.curriculum.find(query).sort("date", -1).to_list(1000)
    
    return curriculum_records

@api_router.put("/curriculum/{curriculum_id}")
async def update_curriculum(curriculum_id: str, data: CurriculumCreate, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can update curriculum")
    
    result = await db.curriculum.update_one(
        {"_id": curriculum_id},
        {
            "$set": {
                "date": data.date,
                "subject": data.subject,
                "topics": data.topics,
                "notes": data.notes,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Curriculum not found")
    
    return {"message": "Curriculum updated successfully"}

# ============= CCTV Configuration =============

@api_router.post("/cctv/config")
async def configure_cctv(config: CCTVConfig, current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can configure CCTV")
    
    # Store configuration
    await db.cctv_config.update_one(
        {},
        {
            "$set": {
                "stream_url": config.stream_url,
                "is_active": config.is_active,
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )
    
    # Start or stop processor
    if config.is_active:
        cctv_processor.start(config.stream_url)
    else:
        cctv_processor.stop()
    
    return {"message": "CCTV configuration updated"}

@api_router.get("/cctv/config")
async def get_cctv_config(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view CCTV configuration")
    
    config = await db.cctv_config.find_one({})
    
    if not config:
        return {"stream_url": "", "is_active": False}
    
    return {
        "stream_url": config.get("stream_url", ""),
        "is_active": config.get("is_active", False)
    }

# ============= Dashboard Statistics =============

@api_router.get("/dashboard/student/{student_id}")
async def get_student_dashboard(student_id: str, current_user: dict = Depends(get_current_user)):
    # Students can only view their own dashboard
    if current_user["role"] == "student":
        user = await db.users.find_one({"_id": current_user["user_id"]})
        if user and user.get("student_id") != student_id:
            raise HTTPException(status_code=403, detail="Cannot view other student's dashboard")
    
    # Get attendance records
    attendance_records = await db.attendance.find({"student_id": student_id}).sort("date", -1).to_list(1000)
    
    # Convert ObjectIds to strings for JSON serialization
    for record in attendance_records:
        if "_id" in record:
            record["_id"] = str(record["_id"])
    
    total_days = len(attendance_records)
    present_days = len([r for r in attendance_records if r["status"] == "present"])
    percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    # Get recent curriculum
    recent_curriculum = await db.curriculum.find({}).sort("date", -1).limit(10).to_list(10)
    
    # Convert ObjectIds to strings for JSON serialization
    for curriculum in recent_curriculum:
        if "_id" in curriculum:
            curriculum["_id"] = str(curriculum["_id"])
    
    return {
        "attendance": {
            "total_days": total_days,
            "present_days": present_days,
            "absent_days": total_days - present_days,
            "percentage": round(percentage, 2),
            "recent_records": attendance_records[:10]
        },
        "curriculum": recent_curriculum
    }

@api_router.get("/dashboard/teacher")
async def get_teacher_dashboard(current_user: dict = Depends(get_current_user)):
    if current_user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can view this dashboard")
    
    # Get total students
    total_students = await db.users.count_documents({"role": "student"})
    
    # Get today's attendance
    today = datetime.utcnow().strftime('%Y-%m-%d')
    today_attendance = await db.attendance.find({"date": today}).to_list(1000)
    present_today = len([r for r in today_attendance if r["status"] == "present"])
    
    # Get students with face encodings
    students_with_faces = await db.face_encodings.count_documents({})
    
    # Get recent curriculum
    recent_curriculum = await db.curriculum.find({}).sort("date", -1).limit(5).to_list(5)
    
    return {
        "total_students": total_students,
        "students_with_face_encoding": students_with_faces,
        "today_attendance": {
            "total": total_students,
            "present": present_today,
            "absent": total_students - present_today,
            "percentage": round((present_today / total_students * 100) if total_students > 0 else 0, 2)
        },
        "recent_curriculum": recent_curriculum
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    cctv_processor.stop()
    client.close()

@app.on_event("startup")
async def startup_event():
    # Check if CCTV should be auto-started
    config = await db.cctv_config.find_one({})
    if config and config.get('is_active'):
        cctv_processor.start(config['stream_url'])
