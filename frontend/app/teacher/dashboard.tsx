import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  RefreshControl,
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
}

interface DashboardData {
  total_students: number;
  students_with_face_encoding: number;
  today_attendance: {
    total: number;
    present: number;
    absent: number;
    percentage: number;
  };
  recent_curriculum: any[];
}

export default function TeacherDashboard() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const userStr = await AsyncStorage.getItem('user');
      if (userStr) {
        const userData = JSON.parse(userStr);
        setUser(userData);
        await fetchDashboardData();
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchDashboardData = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/dashboard/teacher`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setDashboardData(response.data);
    } catch (error: any) {
      console.error('Error fetching dashboard:', error);
      Alert.alert('Error', 'Failed to load dashboard data');
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await fetchDashboardData();
    setRefreshing(false);
  };

  const handleLogout = async () => {
    await AsyncStorage.removeItem('token');
    await AsyncStorage.removeItem('user');
    router.replace('/');
  };

  const navigateTo = (screen: string) => {
    router.push(screen as any);
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
          <Text style={styles.welcomeText}>Teacher Portal</Text>
          <Text style={styles.userName}>{user?.name}</Text>
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
        {/* Statistics Cards */}
        <View style={styles.statsGrid}>
          <View style={[styles.statCard, { backgroundColor: '#dbeafe' }]}>
            <Ionicons name="people" size={32} color="#2563eb" />
            <Text style={styles.statValue}>{dashboardData?.total_students || 0}</Text>
            <Text style={styles.statLabel}>Total Students</Text>
          </View>
          <View style={[styles.statCard, { backgroundColor: '#d1fae5' }]}>
            <Ionicons name="checkmark-circle" size={32} color="#10b981" />
            <Text style={styles.statValue}>
              {dashboardData?.today_attendance.present || 0}
            </Text>
            <Text style={styles.statLabel}>Present Today</Text>
          </View>
          <View style={[styles.statCard, { backgroundColor: '#fef3c7' }]}>
            <Ionicons name="camera" size={32} color="#f59e0b" />
            <Text style={styles.statValue}>
              {dashboardData?.students_with_face_encoding || 0}
            </Text>
            <Text style={styles.statLabel}>Enrolled Faces</Text>
          </View>
          <View style={[styles.statCard, { backgroundColor: '#e0e7ff' }]}>
            <Ionicons name="stats-chart" size={32} color="#6366f1" />
            <Text style={styles.statValue}>
              {dashboardData?.today_attendance.percentage || 0}%
            </Text>
            <Text style={styles.statLabel}>Attendance Rate</Text>
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.card}>
          <Text style={styles.cardTitle}>Quick Actions</Text>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => navigateTo('/teacher/students')}
          >
            <View style={styles.actionIcon}>
              <Ionicons name="person-add" size={24} color="#6366f1" />
            </View>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Manage Students</Text>
              <Text style={styles.actionSubtitle}>Upload and manage student records</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => navigateTo('/teacher/attendance')}
          >
            <View style={styles.actionIcon}>
              <Ionicons name="calendar" size={24} color="#10b981" />
            </View>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>View Attendance</Text>
              <Text style={styles.actionSubtitle}>Check and modify attendance records</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => navigateTo('/teacher/curriculum')}
          >
            <View style={styles.actionIcon}>
              <Ionicons name="book" size={24} color="#f59e0b" />
            </View>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Manage Curriculum</Text>
              <Text style={styles.actionSubtitle}>Add and update daily curriculum</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => navigateTo('/teacher/cctv')}
          >
            <View style={styles.actionIcon}>
              <Ionicons name="videocam" size={24} color="#ef4444" />
            </View>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>CCTV Configuration</Text>
              <Text style={styles.actionSubtitle}>Configure stream URL for face recognition</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#9ca3af" />
          </TouchableOpacity>
        </View>

        {/* Recent Curriculum */}
        {dashboardData?.recent_curriculum && dashboardData.recent_curriculum.length > 0 && (
          <View style={styles.card}>
            <Text style={styles.cardTitle}>Recent Curriculum</Text>
            {dashboardData.recent_curriculum.map((item: any) => (
              <View key={item._id} style={styles.curriculumItem}>
                <View style={styles.curriculumHeader}>
                  <Text style={styles.curriculumDate}>{item.date}</Text>
                  <Text style={styles.curriculumSubject}>{item.subject}</Text>
                </View>
                <Text style={styles.curriculumTopics}>{item.topics}</Text>
              </View>
            ))}
          </View>
        )}
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
  logoutButton: {
    padding: 8,
  },
  content: {
    flex: 1,
    padding: 16,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 16,
  },
  statCard: {
    flex: 1,
    minWidth: '47%',
    padding: 16,
    borderRadius: 16,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#111827',
    marginTop: 8,
  },
  statLabel: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 4,
    textAlign: 'center',
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
  cardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#111827',
    marginBottom: 16,
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  actionIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: '#f3f4f6',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  actionContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#111827',
  },
  actionSubtitle: {
    fontSize: 14,
    color: '#6b7280',
    marginTop: 2,
  },
  curriculumItem: {
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f3f4f6',
  },
  curriculumHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  curriculumDate: {
    fontSize: 14,
    color: '#6b7280',
  },
  curriculumSubject: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6366f1',
  },
  curriculumTopics: {
    fontSize: 14,
    color: '#374151',
  },
});
