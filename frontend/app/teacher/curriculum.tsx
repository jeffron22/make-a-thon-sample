import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  Alert,
  ActivityIndicator,
  Modal,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { router } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';
import { Ionicons } from '@expo/vector-icons';

const API_URL = process.env.EXPO_PUBLIC_BACKEND_URL;

interface CurriculumItem {
  _id: string;
  date: string;
  period: number;
  subject: string;
  topics: string;
  notes?: string;
}

export default function CurriculumManagement() {
  const [curriculum, setCurriculum] = useState<CurriculumItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [modalVisible, setModalVisible] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [selectedId, setSelectedId] = useState('');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [period, setPeriod] = useState(1);
  const [subject, setSubject] = useState('');
  const [topics, setTopics] = useState('');
  const [notes, setNotes] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchCurriculum();
  }, []);

  const fetchCurriculum = async () => {
    try {
      const token = await AsyncStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/curriculum`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCurriculum(response.data);
    } catch (error: any) {
      Alert.alert('Error', 'Failed to load curriculum');
    } finally {
      setLoading(false);
    }
  };

  const openAddModal = () => {
    setEditMode(false);
    setDate(new Date().toISOString().split('T')[0]);
    setPeriod(1);
    setSubject('');
    setTopics('');
    setNotes('');
    setModalVisible(true);
  };

  const openEditModal = (item: CurriculumItem) => {
    setEditMode(true);
    setSelectedId(item._id);
    setDate(item.date);
    setPeriod(item.period || 1);
    setSubject(item.subject);
    setTopics(item.topics);
    setNotes(item.notes || '');
    setModalVisible(true);
  };

  const handleSave = async () => {
    if (!date || !subject || !topics) {
      Alert.alert('Error', 'Please fill in all required fields');
      return;
    }

    setSaving(true);

    try {
      const token = await AsyncStorage.getItem('token');
      const payload = { date, period, subject, topics, notes };

      if (editMode) {
        await axios.put(
          `${API_URL}/api/curriculum/${selectedId}`,
          payload,
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        Alert.alert('Success', 'Curriculum updated successfully');
      } else {
        await axios.post(`${API_URL}/api/curriculum`, payload, {
          headers: { Authorization: `Bearer ${token}` },
        });
        Alert.alert('Success', 'Curriculum added successfully');
      }

      setModalVisible(false);
      fetchCurriculum();
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to save curriculum');
    } finally {
      setSaving(false);
    }
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
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton}>
          <Ionicons name="arrow-back" size={24} color="#111827" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Curriculum</Text>
        <TouchableOpacity
          onPress={openAddModal}
          style={styles.addButton}
        >
          <Ionicons name="add" size={24} color="#fff" />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content}>
        {curriculum.length === 0 ? (
          <View style={styles.emptyState}>
            <Ionicons name="book" size={64} color="#d1d5db" />
            <Text style={styles.emptyText}>No curriculum added yet</Text>
            <Text style={styles.emptySubtext}>Tap the + button to add curriculum</Text>
          </View>
        ) : (
          curriculum.map((item) => (
            <TouchableOpacity
              key={item._id}
              style={styles.curriculumCard}
              onPress={() => openEditModal(item)}
            >
              <View style={styles.cardHeader}>
                <View style={styles.dateContainer}>
                  <Ionicons name="calendar" size={16} color="#6366f1" />
                  <Text style={styles.date}>{item.date} - Period {item.period || 1}</Text>
                </View>
                <Text style={styles.subject}>{item.subject}</Text>
              </View>
              <Text style={styles.topics}>{item.topics}</Text>
              {item.notes && (
                <Text style={styles.notes}>{item.notes}</Text>
              )}
            </TouchableOpacity>
          ))
        )}
      </ScrollView>

      {/* Add/Edit Curriculum Modal */}
      <Modal
        visible={modalVisible}
        animationType="slide"
        presentationStyle="pageSheet"
        onRequestClose={() => setModalVisible(false)}
      >
        <KeyboardAvoidingView
          behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
          style={styles.modalContainer}
        >
          <View style={styles.modalHeader}>
            <TouchableOpacity onPress={() => setModalVisible(false)}>
              <Ionicons name="close" size={28} color="#111827" />
            </TouchableOpacity>
            <Text style={styles.modalTitle}>
              {editMode ? 'Edit Curriculum' : 'Add Curriculum'}
            </Text>
            <View style={{ width: 28 }} />
          </View>

          <ScrollView style={styles.modalContent}>
            <Text style={styles.inputLabel}>Date *</Text>
            <TextInput
              style={styles.textInput}
              placeholder="YYYY-MM-DD"
              value={date}
              onChangeText={setDate}
            />

            <Text style={styles.inputLabel}>Period *</Text>
            <View style={styles.periodSelector}>
              {[1, 2, 3, 4, 5, 6, 7, 8].map((p) => (
                <TouchableOpacity
                  key={p}
                  style={[
                    styles.periodButton,
                    period === p && styles.periodButtonActive,
                  ]}
                  onPress={() => setPeriod(p)}
                >
                  <Text
                    style={[
                      styles.periodButtonText,
                      period === p && styles.periodButtonTextActive,
                    ]}
                  >
                    {p}
                  </Text>
                </TouchableOpacity>
              ))}
            </View>

            <Text style={styles.inputLabel}>Subject *</Text>
            <TextInput
              style={styles.textInput}
              placeholder="Enter subject name"
              value={subject}
              onChangeText={setSubject}
            />

            <Text style={styles.inputLabel}>Topics Covered *</Text>
            <TextInput
              style={[styles.textInput, styles.multilineInput]}
              placeholder="Enter topics covered in class"
              value={topics}
              onChangeText={setTopics}
              multiline
              numberOfLines={4}
            />

            <Text style={styles.inputLabel}>Additional Notes (Optional)</Text>
            <TextInput
              style={[styles.textInput, styles.multilineInput]}
              placeholder="Enter any additional notes"
              value={notes}
              onChangeText={setNotes}
              multiline
              numberOfLines={4}
            />

            <TouchableOpacity
              style={[styles.submitButton, saving && styles.submitButtonDisabled]}
              onPress={handleSave}
              disabled={saving}
            >
              {saving ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text style={styles.submitButtonText}>
                  {editMode ? 'Update Curriculum' : 'Add Curriculum'}
                </Text>
              )}
            </TouchableOpacity>
          </ScrollView>
        </KeyboardAvoidingView>
      </Modal>
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
    padding: 16,
    paddingTop: 48,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
  },
  addButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#6366f1',
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    flex: 1,
    padding: 16,
  },
  emptyState: {
    alignItems: 'center',
    marginTop: 64,
  },
  emptyText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#6b7280',
    marginTop: 16,
  },
  emptySubtext: {
    fontSize: 14,
    color: '#9ca3af',
    marginTop: 8,
  },
  curriculumCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  dateContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  date: {
    fontSize: 14,
    color: '#6b7280',
  },
  subject: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6366f1',
  },
  topics: {
    fontSize: 16,
    color: '#111827',
    marginBottom: 8,
  },
  notes: {
    fontSize: 14,
    color: '#6b7280',
    fontStyle: 'italic',
  },
  modalContainer: {
    flex: 1,
    backgroundColor: '#fff',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    paddingTop: 48,
    borderBottomWidth: 1,
    borderBottomColor: '#e5e7eb',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#111827',
  },
  modalContent: {
    flex: 1,
    padding: 20,
  },
  inputLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: '#374151',
    marginBottom: 8,
    marginTop: 16,
  },
  textInput: {
    backgroundColor: '#f9fafb',
    borderWidth: 1,
    borderColor: '#e5e7eb',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#111827',
  },
  multilineInput: {
    height: 120,
    textAlignVertical: 'top',
  },
  submitButton: {
    backgroundColor: '#6366f1',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 24,
    marginBottom: 32,
  },
  submitButtonDisabled: {
    backgroundColor: '#9ca3af',
  },
  submitButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  periodSelector: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  periodButton: {
    paddingVertical: 12,
    paddingHorizontal: 20,
    backgroundColor: '#f3f4f6',
    borderRadius: 8,
    borderWidth: 2,
    borderColor: '#e5e7eb',
  },
  periodButtonActive: {
    backgroundColor: '#6366f1',
    borderColor: '#6366f1',
  },
  periodButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6b7280',
  },
  periodButtonTextActive: {
    color: '#fff',
  },
});
