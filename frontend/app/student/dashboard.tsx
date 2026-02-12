import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { Ionicons } from '@expo/vector-icons';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  student_id: string;
}

interface AttendanceRecord {
  date: string;
  status: string;
  marked_by: string;
}

interface CurriculumItem {
  _id: string;
  date: string;
  subject: string;
  topics: string;
  notes?: string;
}

export default function StudentDashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [attendance, setAttendance] = useState<any>(null);
  const [curriculum, setCurriculum] = useState<CurriculumItem[]>([]);

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const userStr = await AsyncStorage.getItem('user');
      if (userStr) {
        const userData = JSON.parse(userStr);
        setUser(userData);
        await fetchDashboardData(userData.student_id);
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDashboardData = async (studentId: string) => {
    try {
      const token = await AsyncStorage.getItem('token');
      const today = new Date().toISOString().split('T')[0];
      
      // Get period-wise curriculum with attendance status
      const curriculumResponse = await axios.get(
        `${API_URL}/api/curriculum/student/${studentId}?date=${today}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      
      // Get overall attendance stats
      const attendanceResponse = await axios.get(
        `${API_URL}/api/attendance/student/${studentId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      
      setAttendance(attendanceResponse.data);
      setCurriculum(curriculumResponse.data);
    } catch (error: any) {
      console.error('Error fetching dashboard:', error);
      Alert.alert('Error', 'Failed to load dashboard data');
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    if (user) {
      await fetchDashboardData(user.student_id);
    }
    setRefreshing(false);
  };

  const handleLogout = async () => {
    await AsyncStorage.removeItem('token');
    await AsyncStorage.removeItem('user');
    router.replace('/');
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#6366f1" />
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View>
          <Text style={styles.welcomeText}>Welcome back,</Text>
          <Text style={styles.userName}>{user?.name}</Text>
          <Text style={styles.studentId}>ID: {user?.student_id}</Text>
        </View>
        <TouchableOpacity onPress={handleLogout} style={styles.logoutButton}>
          <Ionicons name="log-out" size={24} color="#ef4444" />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.content}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Attendance Summary */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons name="calendar" size={24} color="#6366f1" />
            <Text style={styles.cardTitle}>Attendance Summary</Text>
          </View>
          {attendance && (
            <>
              <View style={styles.progressContainer}>
                <View style={styles.progressBar}>
                  <View
                    style={[
                      styles.progressFill,
                      { width: `${attendance.percentage}%` },
                    ]}
                  />
                </View>
                <Text style={styles.percentageText}>
                  {attendance.percentage}%
                </Text>
              </View>
              <View style={styles.statsRow}>
                <View style={styles.statItem}>
                  <Text style={styles.statValue}>{attendance.total_days}</Text>
                  <Text style={styles.statLabel}>Total Days</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={[styles.statValue, { color: '#10b981' }]}>
                    {attendance.present_days}
                  </Text>
                  <Text style={styles.statLabel}>Present</Text>
                </View>
                <View style={styles.statItem}>
                  <Text style={[styles.statValue, { color: '#ef4444' }]}>
                    {attendance.absent_days}
                  </Text>
                  <Text style={styles.statLabel}>Absent</Text>
                </View>
              </View>
            </>
          )}
        </View>

        {/* Recent Attendance */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Recent Attendance</Text>
          {attendance?.recent_records.map((record: AttendanceRecord, index: number) => (
            <View key={index} style={styles.attendanceItem}>
              <View style={styles.attendanceDate}>
                <Ionicons
                  name="calendar-outline"
                  size={16}
                  color="#6b7280"
                />
                <Text style={styles.dateText}>{record.date}</Text>
              </View>
              <View
                style={[
                  styles.statusBadge,
                  record.status === 'present'
                    ? styles.statusPresent
                    : styles.statusAbsent,
                ]}
              >
                <Text
                  style={[
                    styles.statusText,
                    record.status === 'present'
                      ? styles.statusTextPresent
                      : styles.statusTextAbsent,
                  ]}
                >
                  {record.status.toUpperCase()}
                </Text>
              </View>
            </View>
          ))}
        </View>

        {/* Today's Period-wise Curriculum */}
        <View style={styles.card}>
          <View style={styles.cardHeader}>
            <Ionicons name="book" size={24} color="#6366f1" />
            <Text style={styles.cardTitle}>Today's Curriculum</Text>
          </View>
          <Text style={styles.periodSubtitle}>
            Your attendance status for each period
          </Text>
          {curriculum.length === 0 ? (
            <Text style={styles.emptyText}>No curriculum added for today</Text>
          ) : (
            curriculum.map((item: any) => (
              <View
                key={item._id}
                style={[
                  styles.periodCard,
                  {
                    backgroundColor:
                      item.color === 'green'
                        ? '#d1fae5'
                        : item.color === 'red'
                        ? '#fee2e2'
                        : '#f3f4f6',
                    borderLeftWidth: 4,
                    borderLeftColor:
                      item.color === 'green'
                        ? '#10b981'
                        : item.color === 'red'
                        ? '#ef4444'
                        : '#9ca3af',
                  },
                ]}
              >
                <View style={styles.periodHeader}>
                  <View style={styles.periodInfo}>
                    <Text style={styles.periodNumber}>Period {item.period}</Text>
                    <Text style={styles.periodSubject}>{item.subject}</Text>
                  </View>
                  <View
                    style={[
                      styles.attendanceIcon,
                      {
                        backgroundColor:
                          item.color === 'green'
                            ? '#10b981'
                            : item.color === 'red'
                            ? '#ef4444'
                            : '#9ca3af',
                      },
                    ]}
                  >
                    <Ionicons
                      name={
                        item.color === 'green'
                          ? 'checkmark'
                          : item.color === 'red'
                          ? 'close'
                          : 'help'
                      }
                      size={20}
                      color="#fff"
                    />
                  </View>
                </View>
                <Text style={styles.periodTopics}>{item.topics}</Text>
                {item.notes && (
                  <Text style={styles.periodNotes}>{item.notes}</Text>
                )}
                <Text style={styles.attendanceLabel}>
                  {item.attendance_status === 'present'
                    ? 'You were present'
                    : item.attendance_status === 'absent'
                    ? 'You were absent'
                    : 'Attendance not marked'}
                </Text>
              </View>
            ))
          )}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f9fafb',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f9fafb',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 24,
    paddingTop: 48,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  welcomeText: {
    fontSize: 14,
    color: '#6b7280',
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#111827',
    marginTop: 4,
  },
  studentId: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  logoutButton: {
    padding: 8,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 8,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
  },
  progressContainer: {
    marginBottom: 20,
  },
  progressBar: {
    height: 12,
    backgroundColor: '#e5e7eb',
    borderRadius: 6,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#6366f1',
    borderRadius: 6,
  },
  percentageText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#6366f1',
    textAlign: 'center',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginTop: 16,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#111827',
  },
  statLabel: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 4,
  },
  attendanceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  attendanceDate: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  dateText: {
    fontSize: 16,
    color: '#374151',
  },
  statusBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusPresent: {
    backgroundColor: '#d1fae5',
  },
  statusAbsent: {
    backgroundColor: '#fee2e2',
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
  },
  statusTextPresent: {
    color: '#065f46',
  },
  statusTextAbsent: {
    color: '#991b1b',
  },
  curriculumItem: {
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  curriculumHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  curriculumDate: {
    fontSize: 14,
    color: '#6b7280',
  },
  curriculumSubject: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6366f1',
  },
  curriculumTopics: {
    fontSize: 16,
    color: '#111827',
    marginBottom: 4,
  },
  curriculumNotes: {
    fontSize: 14,
    color: '#6b7280',
    fontStyle: 'italic',
  },
  emptyText: {
    fontSize: 14,
    color: '#9ca3af',
    textAlign: 'center',
    paddingVertical: 20,
  },
  periodSubtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginBottom: 16,
  },
  periodCard: {
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  periodHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  periodInfo: {
    flex: 1,
  },
  periodNumber: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6b7280',
    marginBottom: 4,
  },
  periodSubject: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
  },
  attendanceIcon: {
    width: 36,
    height: 36,
    borderRadius: 18,
    justifyContent: 'center',
    alignItems: 'center',
  },
  periodTopics: {
    fontSize: 16,
    color: '#374151',
    marginBottom: 8,
    lineHeight: 22,
  },
  periodNotes: {
    fontSize: 14,
    color: '#6b7280',
    fontStyle: 'italic',
    marginBottom: 8,
  },
  attendanceLabel: {
    fontSize: 12,
    fontWeight: '600',
    color: '#6b7280',
    marginTop: 4,
  },
});
