import React, { useState, useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { Box, Container, Snackbar, Alert } from '@mui/material';
import axios from 'axios';

// Components
import AppHeader from './components/AppHeader';

// Pages
import HomePage from './pages/HomePage';
import JobsPage from './pages/JobsPage';
import StatusPage from './pages/StatusPage';
import ResultsPage from './pages/ResultsPage';

// API base URL
// const API_BASE_URL = 'http://localhost:5000/api';
const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:5000/api'
  : 'https://infisync.onrender.com/api';


function App() {
  const [apiConnected, setApiConnected] = useState(false);
  const [checkingApi, setCheckingApi] = useState(true);
  const [notification, setNotification] = useState({ open: false, message: '', severity: 'info' });

  useEffect(() => {
    // Check API connection on mount
    checkApiConnection();
  }, []);

  const checkApiConnection = async () => {
    try {
      setCheckingApi(true);
      const response = await axios.get(`${API_BASE_URL}/health`);
      if (response.data && response.data.status === 'ok') {
        setApiConnected(true);
      } else {
        setApiConnected(false);
        showNotification('API connection failed', 'error');
      }
    } catch (error) {
      setApiConnected(false);
      showNotification('Could not connect to the backend API', 'error');
    } finally {
      setCheckingApi(false);
    }
  };

  const showNotification = (message, severity = 'info') => {
    setNotification({
      open: true,
      message,
      severity
    });
  };

  const closeNotification = () => {
    setNotification({
      ...notification,
      open: false
    });
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppHeader apiConnected={apiConnected} checkingApi={checkingApi} onRetryConnection={checkApiConnection} />
      
      <Container component="main" sx={{ flexGrow: 1, py: 4 }}>
        <Routes>
          <Route path="/" element={<HomePage apiConnected={apiConnected} showNotification={showNotification} />} />
          <Route path="/jobs" element={<JobsPage showNotification={showNotification} />} />
          <Route path="/status/:jobId" element={<StatusPage showNotification={showNotification} />} />
          <Route path="/results/:jobId" element={<ResultsPage showNotification={showNotification} />} />
        </Routes>
      </Container>
      
      <Box component="footer" sx={{ py: 3, bgcolor: 'background.paper', mt: 'auto' }}>
        <Container maxWidth="lg">
          <Box sx={{ textAlign: 'center', color: 'text.secondary' }}>
            Meeting Summarizer © {new Date().getFullYear()}
          </Box>
        </Container>
      </Box>
      
      <Snackbar 
        open={notification.open} 
        autoHideDuration={6000} 
        onClose={closeNotification}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={closeNotification} severity={notification.severity} sx={{ width: '100%' }}>
          {notification.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default App;
