/**
 * SomaGent Mobile App
 * React Native cross-platform monitoring and control app.
 * 
 * Features:
 * - Real-time project monitoring via WebSocket
 * - Push notifications for alerts
 * - Voice commands (integrated with voice-interface service)
 * - Approval workflows for governance
 * - Quick actions and shortcuts
 */

import React, { useState, useEffect } from 'react';
import {
  SafeAreaView,
  ScrollView,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Alert,
} from 'react-native';
import messaging from '@react-native-firebase/messaging';
import Voice from '@react-native-voice/voice';

// ============================================================================
// WEBSOCKET CONNECTION
// ============================================================================

class SomaGentWebSocket {
  constructor(url) {
    this.url = url;
    this.ws = null;
    this.listeners = [];
  }

  connect() {
    this.ws = new WebSocket(this.url);
    
    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.send({ type: 'authenticate', token: 'user-auth-token' });
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.listeners.forEach(listener => listener(data));
    };
    
    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket disconnected, reconnecting...');
      setTimeout(() => this.connect(), 5000);
    };
  }

  send(data) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  subscribe(listener) {
    this.listeners.push(listener);
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// ============================================================================
// PUSH NOTIFICATIONS
// ============================================================================

async function requestNotificationPermission() {
  const authStatus = await messaging().requestPermission();
  const enabled =
    authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
    authStatus === messaging.AuthorizationStatus.PROVISIONAL;

  if (enabled) {
    console.log('Notification permission granted');
    const token = await messaging().getToken();
    console.log('FCM Token:', token);
    return token;
  }
}

// ============================================================================
// MAIN APP COMPONENT
// ============================================================================

const App = () => {
  const [projects, setProjects] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [refreshing, setRefreshing] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [voiceText, setVoiceText] = useState('');

  // WebSocket connection
  const ws = new SomaGentWebSocket('ws://localhost:8000/ws');

  useEffect(() => {
    // Setup push notifications
    requestNotificationPermission();

    // Setup WebSocket
    ws.connect();
    ws.subscribe(handleWebSocketMessage);

    // Setup foreground message handler
    const unsubscribe = messaging().onMessage(async remoteMessage => {
      Alert.alert(
        remoteMessage.notification.title,
        remoteMessage.notification.body
      );
    });

    // Setup voice recognition
    Voice.onSpeechResults = onSpeechResults;

    // Fetch initial data
    fetchProjects();
    fetchAlerts();

    return () => {
      ws.disconnect();
      unsubscribe();
      Voice.destroy().then(Voice.removeAllListeners);
    };
  }, []);

  const handleWebSocketMessage = (data) => {
    console.log('WebSocket message:', data);
    
    switch (data.type) {
      case 'project_update':
        updateProject(data.project);
        break;
      case 'alert':
        addAlert(data.alert);
        break;
      case 'workflow_complete':
        showNotification('Workflow Complete', data.workflow.name);
        break;
    }
  };

  const fetchProjects = async () => {
    try {
      const response = await fetch('http://localhost:8000/projects');
      const data = await response.json();
      setProjects(data.projects);
    } catch (error) {
      console.error('Failed to fetch projects:', error);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await fetch('http://localhost:8000/alerts');
      const data = await response.json();
      setAlerts(data.alerts);
    } catch (error) {
      console.error('Failed to fetch alerts:', error);
    }
  };

  const onRefresh = React.useCallback(() => {
    setRefreshing(true);
    Promise.all([fetchProjects(), fetchAlerts()]).then(() => {
      setRefreshing(false);
    });
  }, []);

  const updateProject = (updatedProject) => {
    setProjects(prev =>
      prev.map(p => (p.id === updatedProject.id ? updatedProject : p))
    );
  };

  const addAlert = (alert) => {
    setAlerts(prev => [alert, ...prev].slice(0, 50)); // Keep last 50 alerts
  };

  const showNotification = (title, body) => {
    Alert.alert(title, body);
  };

  // ============================================================================
  // VOICE COMMANDS
  // ============================================================================

  const startVoiceRecognition = async () => {
    try {
      setIsListening(true);
      await Voice.start('en-US');
    } catch (error) {
      console.error('Voice start error:', error);
      setIsListening(false);
    }
  };

  const stopVoiceRecognition = async () => {
    try {
      await Voice.stop();
      setIsListening(false);
    } catch (error) {
      console.error('Voice stop error:', error);
    }
  };

  const onSpeechResults = (event) => {
    const text = event.value[0];
    setVoiceText(text);
    processVoiceCommand(text);
  };

  const processVoiceCommand = async (text) => {
    console.log('Voice command:', text);
    
    // Send to voice-interface service for parsing
    try {
      const response = await fetch('http://localhost:8011/parse-voice-command', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
      });
      
      const { intent } = await response.json();
      executeIntent(intent);
    } catch (error) {
      console.error('Failed to parse voice command:', error);
    }
  };

  const executeIntent = (intent) => {
    switch (intent.action) {
      case 'list_projects':
        fetchProjects();
        break;
      case 'check_status':
        onRefresh();
        break;
      case 'create_project':
        Alert.alert('Create Project', `Creating: ${intent.parameters.name}`);
        break;
      default:
        Alert.alert('Unknown Command', `Action: ${intent.action}`);
    }
  };

  // ============================================================================
  // APPROVAL WORKFLOWS
  // ============================================================================

  const handleApproval = async (alertId, approved) => {
    try {
      await fetch(`http://localhost:8000/approvals/${alertId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ approved })
      });
      
      // Remove from alerts
      setAlerts(prev => prev.filter(a => a.id !== alertId));
      
      Alert.alert(
        'Approval Submitted',
        approved ? 'Action approved' : 'Action rejected'
      );
    } catch (error) {
      console.error('Approval failed:', error);
    }
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>SomaGent</Text>
        <TouchableOpacity
          style={[styles.voiceButton, isListening && styles.voiceButtonActive]}
          onPress={isListening ? stopVoiceRecognition : startVoiceRecognition}
        >
          <Text style={styles.voiceButtonText}>
            {isListening ? '🎤 Listening...' : '🎤 Voice'}
          </Text>
        </TouchableOpacity>
      </View>

      {voiceText ? (
        <View style={styles.voiceTextContainer}>
          <Text style={styles.voiceTextLabel}>Voice Command:</Text>
          <Text style={styles.voiceText}>{voiceText}</Text>
        </View>
      ) : null}

      <ScrollView
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* ALERTS */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>⚠️ Alerts & Approvals</Text>
          {alerts.length === 0 ? (
            <Text style={styles.emptyText}>No alerts</Text>
          ) : (
            alerts.map(alert => (
              <View key={alert.id} style={styles.alertCard}>
                <Text style={styles.alertTitle}>{alert.title}</Text>
                <Text style={styles.alertMessage}>{alert.message}</Text>
                {alert.requires_approval && (
                  <View style={styles.approvalButtons}>
                    <TouchableOpacity
                      style={[styles.button, styles.approveButton]}
                      onPress={() => handleApproval(alert.id, true)}
                    >
                      <Text style={styles.buttonText}>✅ Approve</Text>
                    </TouchableOpacity>
                    <TouchableOpacity
                      style={[styles.button, styles.rejectButton]}
                      onPress={() => handleApproval(alert.id, false)}
                    >
                      <Text style={styles.buttonText}>❌ Reject</Text>
                    </TouchableOpacity>
                  </View>
                )}
              </View>
            ))
          )}
        </View>

        {/* PROJECTS */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>📁 Projects</Text>
          {projects.length === 0 ? (
            <Text style={styles.emptyText}>No projects</Text>
          ) : (
            projects.map(project => (
              <View key={project.id} style={styles.projectCard}>
                <Text style={styles.projectName}>{project.name}</Text>
                <Text style={styles.projectStatus}>
                  Status: {project.status}
                </Text>
                <View style={styles.projectStats}>
                  <Text style={styles.stat}>
                    ✅ {project.tasks_completed}/{project.tasks_total} tasks
                  </Text>
                  <Text style={styles.stat}>
                    ⏱️ {project.duration}s
                  </Text>
                </View>
              </View>
            ))
          )}
        </View>

        {/* QUICK ACTIONS */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>⚡ Quick Actions</Text>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => Alert.alert('Create Project', 'Voice or form?')}
          >
            <Text style={styles.actionButtonText}>➕ Create Project</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => fetchAlerts()}
          >
            <Text style={styles.actionButtonText}>🔔 Check Alerts</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.actionButton}
            onPress={() => onRefresh()}
          >
            <Text style={styles.actionButtonText}>🔄 Refresh All</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

// ============================================================================
// STYLES
// ============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#2c3e50',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#fff',
  },
  voiceButton: {
    padding: 10,
    backgroundColor: '#3498db',
    borderRadius: 8,
  },
  voiceButtonActive: {
    backgroundColor: '#e74c3c',
  },
  voiceButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  voiceTextContainer: {
    padding: 12,
    backgroundColor: '#ecf0f1',
    borderBottomWidth: 1,
    borderBottomColor: '#bdc3c7',
  },
  voiceTextLabel: {
    fontSize: 12,
    color: '#7f8c8d',
    marginBottom: 4,
  },
  voiceText: {
    fontSize: 16,
    color: '#2c3e50',
  },
  section: {
    margin: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 12,
    color: '#2c3e50',
  },
  emptyText: {
    color: '#95a5a6',
    fontStyle: 'italic',
    textAlign: 'center',
    padding: 20,
  },
  alertCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#e74c3c',
  },
  alertTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 8,
  },
  alertMessage: {
    fontSize: 14,
    color: '#7f8c8d',
    marginBottom: 12,
  },
  approvalButtons: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  button: {
    flex: 1,
    padding: 12,
    borderRadius: 6,
    marginHorizontal: 4,
  },
  approveButton: {
    backgroundColor: '#2ecc71',
  },
  rejectButton: {
    backgroundColor: '#e74c3c',
  },
  buttonText: {
    color: '#fff',
    textAlign: 'center',
    fontWeight: 'bold',
  },
  projectCard: {
    backgroundColor: '#fff',
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
  },
  projectName: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  projectStatus: {
    fontSize: 14,
    color: '#3498db',
    marginBottom: 8,
  },
  projectStats: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  stat: {
    fontSize: 12,
    color: '#7f8c8d',
  },
  actionButton: {
    backgroundColor: '#3498db',
    padding: 16,
    borderRadius: 8,
    marginBottom: 8,
  },
  actionButtonText: {
    color: '#fff',
    textAlign: 'center',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default App;
