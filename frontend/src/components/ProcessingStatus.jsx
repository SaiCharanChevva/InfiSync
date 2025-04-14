import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Stepper,
  Step,
  StepLabel,
  LinearProgress,
  Alert,
  Button,
  Chip,
  Divider
} from '@mui/material';
import {
  CloudDoneOutlined,
  AudioFileOutlined,
  TextSnippetOutlined,
  SummarizeOutlined,
  ErrorOutline,
  ReplayOutlined
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

const ProcessingStatus = ({ jobId, showNotification }) => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [pollingInterval, setPollingInterval] = useState(null);
  const navigate = useNavigate();

  // Processing steps
  const steps = [
    { label: 'Upload Complete', status: 'uploaded', icon: <CloudDoneOutlined /> },
    { label: 'Extracting Audio', status: 'extracting_audio', icon: <AudioFileOutlined /> },
    { label: 'Transcribing', status: 'transcribing', icon: <TextSnippetOutlined /> },
    { label: 'Generating Summary', status: 'summarizing', icon: <SummarizeOutlined /> }
  ];

  // Get active step index
  const getActiveStep = () => {
    if (!status) return 0;
    
    const currentStatusIndex = steps.findIndex(step => step.status === status.status);
    
    if (currentStatusIndex === -1) {
      if (status.status === 'processing') return 0;
      if (status.status === 'completed') return steps.length;
      if (status.status === 'failed') return steps.length;
      return 0;
    }
    
    return currentStatusIndex;
  };

  // Initialize polling on component mount
  useEffect(() => {
    fetchStatus();
    
    // Set up polling at 3-second intervals
    const interval = setInterval(fetchStatus, 3000);
    setPollingInterval(interval);
    
    // Clean up interval when component unmounts
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [jobId]);

  // Handle completed or failed status
  useEffect(() => {
    if (status) {
      if (status.status === 'completed') {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
        
        // Navigate to results page after a short delay
        const timer = setTimeout(() => {
          navigate(`/results/${jobId}`);
        }, 2000);
        
        return () => clearTimeout(timer);
      } else if (status.status === 'failed') {
        if (pollingInterval) {
          clearInterval(pollingInterval);
          setPollingInterval(null);
        }
        
        showNotification('Processing failed. Please check the error message.', 'error');
      }
    }
  }, [status, jobId, navigate, pollingInterval, showNotification]);

  const fetchStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/status/${jobId}`);
      setStatus(response.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to fetch job status');
      // Stop polling if there's an error
      if (pollingInterval) {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
      showNotification('Error fetching job status', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = async () => {
    try {
      await axios.post(`${API_BASE_URL}/process/${jobId}`);
      showNotification('Restarted processing', 'info');
      fetchStatus();
      
      // Restart polling
      if (!pollingInterval) {
        const interval = setInterval(fetchStatus, 3000);
        setPollingInterval(interval);
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to restart processing');
      showNotification('Failed to restart processing', 'error');
    }
  };

  if (loading && !status) {
    return (
      <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
          <LinearProgress sx={{ width: '100%', mb: 3 }} />
          <Typography variant="h6">Loading job status...</Typography>
        </Box>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
        <Button 
          variant="outlined" 
          startIcon={<ReplayOutlined />}
          onClick={fetchStatus}
        >
          Retry
        </Button>
      </Paper>
    );
  }

  const activeStep = getActiveStep();
  const isCompleted = status?.status === 'completed';
  const isFailed = status?.status === 'failed';

  return (
    <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
      <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
        <Box>
          <Typography variant="h5" gutterBottom>
            Processing Status
          </Typography>
          <Typography variant="body1" color="text.secondary">
            {status?.filename}
          </Typography>
        </Box>

        <Chip 
          label={status?.status?.replace('_', ' ')}
          color={
            isFailed ? 'error' : 
            isCompleted ? 'success' : 
            'primary'
          }
          variant="filled"
          sx={{ 
            textTransform: 'capitalize',
            fontWeight: 500
          }}
        />
      </Box>

      <Divider sx={{ my: 3 }} />

      <Stepper activeStep={activeStep} alternativeLabel sx={{ mb: 4 }}>
        {steps.map((step, index) => (
          <Step key={step.label} completed={activeStep > index || isCompleted}>
            <StepLabel StepIconProps={{ icon: step.icon }}>
              {step.label}
            </StepLabel>
          </Step>
        ))}
      </Stepper>

      {!isCompleted && !isFailed && (
        <Box sx={{ width: '100%', mt: 2 }}>
          <LinearProgress />
          <Typography align="center" variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            {activeStep === 0 && 'Preparing for processing...'}
            {activeStep === 1 && 'Extracting audio from video file...'}
            {activeStep === 2 && 'Transcribing audio to text using AI...'}
            {activeStep === 3 && 'Generating meeting summary...'}
          </Typography>
        </Box>
      )}

      {isCompleted && (
        <Box sx={{ textAlign: 'center', mt: 2 }}>
          <Alert severity="success" sx={{ mb: 3 }}>
            Processing completed successfully!
          </Alert>
          <Typography>
            Redirecting to results page...
          </Typography>
        </Box>
      )}

      {isFailed && (
        <Box sx={{ mt: 2 }}>
          <Alert severity="error" sx={{ mb: 3 }}>
            {status.error || 'Processing failed'}
          </Alert>
          <Button 
            variant="contained" 
            color="primary"
            startIcon={<ReplayOutlined />}
            onClick={handleRetry}
          >
            Retry Processing
          </Button>
        </Box>
      )}
    </Paper>
  );
};

export default ProcessingStatus;