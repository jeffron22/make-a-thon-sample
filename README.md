# Smart Attendance System with Face Recognition

A comprehensive mobile application for automated attendance tracking using face recognition from CCTV feeds. Built with Expo (React Native), FastAPI, MongoDB, and DeepFace.

## Features

### For Students
- **Dashboard**: View attendance statistics and percentage
- **Attendance History**: See detailed attendance records
- **Curriculum Access**: View daily curriculum and topics covered
- **Real-time Updates**: Automatic attendance marking through face recognition

### For Teachers
- **Student Management**: Bulk upload students with face photos for enrollment
- **Attendance Management**: View and manually override attendance records
- **Curriculum Management**: Add and update daily curriculum
- **CCTV Configuration**: Configure live stream URL for automatic face recognition
- **Dashboard Analytics**: View overall statistics and today's attendance

## Technology Stack

### Frontend (Mobile App)
- **Expo/React Native**: Cross-platform mobile development
- **TypeScript**: Type-safe development
- **Expo Router**: File-based navigation
- **AsyncStorage**: Local data persistence
- **Axios**: HTTP client
- **Expo Image Picker**: Photo selection for face enrollment

### Backend
- **FastAPI**: High-performance Python web framework
- **MongoDB**: NoSQL database
- **DeepFace**: Face recognition library (using Facenet model)
- **OpenCV**: Video processing
- **JWT**: Authentication
- **Bcrypt**: Password hashing

## Architecture

### Authentication Flow
1. Users register/login with role (Student/Teacher)
2. JWT tokens issued for authenticated sessions
3. Role-based access control for different features

### Face Recognition System
1. **Enrollment**: Teacher uploads 3-5 photos per student
2. **Embedding Generation**: DeepFace creates 128-dimensional face encodings
3. **Storage**: Encodings stored in MongoDB
4. **Recognition**: CCTV stream processed in background
5. **Matching**: Detected faces compared with stored encodings
6. **Attendance**: Automatic marking when match found (once per day)

### CCTV Processing
- Background thread processes RTSP/HTTP video stream
- Processes 1 frame per second to reduce CPU usage
- Face detection using DeepFace with Facenet model
- Cosine similarity for face matching (threshold: 0.6)
- Auto-restart on configuration change

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `GET /api/auth/me` - Get current user info

### Student Management (Teacher only)
- `POST /api/students/bulk-upload` - Upload students with face photos
- `GET /api/students` - Get all students

### Attendance
- `GET /api/attendance/student/{student_id}` - Get student attendance
- `GET /api/attendance/all?date={date}` - Get all attendance for date
- `POST /api/attendance/override` - Manually update attendance

### Curriculum
- `POST /api/curriculum` - Create curriculum entry
- `GET /api/curriculum?date={date}` - Get curriculum
- `PUT /api/curriculum/{id}` - Update curriculum

### CCTV Configuration (Teacher only)
- `POST /api/cctv/config` - Configure CCTV stream
- `GET /api/cctv/config` - Get current configuration

### Dashboard
- `GET /api/dashboard/student/{student_id}` - Student dashboard data
- `GET /api/dashboard/teacher` - Teacher dashboard data

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 20+
- MongoDB
- CCTV camera with RTSP/HTTP stream support

### Backend Setup
```bash
cd /app/backend
pip install -r requirements.txt
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Frontend Setup
```bash
cd /app/frontend
yarn install
yarn start
```

### Environment Variables

**Backend (.env):**
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
JWT_SECRET="your-secret-key"
```

**Frontend (.env):**
```
EXPO_PUBLIC_BACKEND_URL=http://your-backend-url
```

## Usage Guide

### Initial Setup
1. **Teacher Registration**: Teacher creates account
2. **Student Enrollment**:
   - Teacher uploads student details (name, email, student ID)
   - Upload 3-5 clear face photos per student
   - System generates face encodings
3. **CCTV Configuration**:
   - Enter RTSP/HTTP stream URL
   - Enable face recognition
   - System starts processing video feed

### Daily Operations
1. **Automatic Attendance**: 
   - CCTV processes video stream
   - Detects and recognizes faces
   - Marks attendance automatically
2. **Manual Override**: Teacher can manually mark/change attendance
3. **Curriculum Entry**: Teacher updates daily topics and notes

### Student Access
1. Students login with credentials
2. View attendance percentage and history
3. Check daily curriculum updates

## CCTV Stream Examples

### RTSP
```
rtsp://192.168.1.100:554/stream
rtsp://username:password@192.168.1.100:554/stream
```

### HTTP
```
http://192.168.1.100:8080/video
http://username:password@192.168.1.100:8080/video
```

## Face Recognition Details

### Enrollment Requirements
- **Photo Count**: 3-5 photos per student recommended
- **Photo Quality**: Clear, well-lit face photos
- **Face Position**: Front-facing, minimal angle
- **Resolution**: Higher resolution better for accuracy

### Recognition Parameters
- **Model**: Facenet (128-dimensional embeddings)
- **Similarity Threshold**: 0.6 (cosine similarity)
- **Processing Rate**: 1 frame per second
- **Detection**: Enforce detection for accuracy

### Performance Optimization
- Frame skipping (process every 30th frame)
- Background processing thread
- Efficient database queries
- Once-per-day attendance marking

## Database Schema

### Collections

**users**
```json
{
  "_id": "uuid",
  "email": "student@example.com",
  "password_hash": "bcrypt_hash",
  "name": "John Doe",
  "role": "student",
  "student_id": "STU001",
  "created_at": "timestamp"
}
```

**face_encodings**
```json
{
  "_id": "uuid",
  "student_id": "STU001",
  "embeddings": [[128-dim vector], ...],
  "photos": ["base64_image1", ...],
  "created_at": "timestamp"
}
```

**attendance**
```json
{
  "student_id": "STU001",
  "date": "2025-01-15",
  "status": "present",
  "marked_by": "auto",
  "timestamp": "timestamp"
}
```

**curriculum**
```json
{
  "_id": "uuid",
  "date": "2025-01-15",
  "subject": "Mathematics",
  "topics": "Calculus fundamentals",
  "notes": "Chapter 1-3",
  "teacher_id": "uuid",
  "created_at": "timestamp"
}
```

**cctv_config**
```json
{
  "stream_url": "rtsp://...",
  "is_active": true,
  "updated_at": "timestamp"
}
```

## Security Considerations

1. **Authentication**: JWT tokens with expiration
2. **Password Hashing**: Bcrypt with salt
3. **Role-Based Access**: Students can only view own data
4. **CCTV Credentials**: Stored securely in database
5. **Face Data**: Stored as mathematical embeddings, not raw images

## Troubleshooting

### Face Recognition Issues
- **No faces detected**: Check camera angle and lighting
- **Low accuracy**: Add more training photos per student
- **False positives**: Adjust similarity threshold
- **Slow processing**: Reduce frame processing rate

### CCTV Connection Issues
- Verify stream URL is accessible
- Check network connectivity
- Ensure RTSP/HTTP protocol is correct
- Validate credentials if using authentication

### Performance Issues
- Reduce processing frame rate
- Optimize database queries
- Limit concurrent face comparisons
- Use proper indexing on MongoDB

## Future Enhancements

- [ ] Real-time push notifications
- [ ] Multi-camera support
- [ ] Advanced analytics and reports
- [ ] Export attendance to Excel/PDF
- [ ] SMS/Email alerts for absentees
- [ ] Geofencing for attendance validation
- [ ] Face mask detection
- [ ] Temperature screening integration
- [ ] Multi-language support
- [ ] Dark mode UI

## License

MIT License - Feel free to use and modify for your needs.

## Support

For issues and questions, please create an issue in the repository.

---

**Note**: This system requires proper CCTV infrastructure and adequate lighting conditions for optimal face recognition performance. Test thoroughly with your specific setup before production deployment.
