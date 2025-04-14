import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  IconButton,
  CircularProgress,
  Alert,
  Tooltip
} from '@mui/material';
import {
  PlayArrowOutlined,
  VisibilityOutlined,
  ReplayOutlined,
  RefreshOutlined
} from '@mui/icons-material';
import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api';

const JobsList = ({ showNotification }) => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/jobs`);
      setJobs(response.data.jobs);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to fetch jobs');
      showNotification('Failed to load jobs list', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleViewStatus = (jobId) => {
    navigate(`/status/${jobId}`);
  };

  const handleViewResults = (jobId) => {
    navigate(`/results/${jobId}`);
  };

  const handleRetryProcessing = async (jobId) => {
    try {
      await axios.post(`${API_BASE_URL}/process/${jobId}`);
      showNotification('Processing restarted', 'success');
      
      // Update the job status in the list
      setJobs(jobs.map(job => 
        job.job_id === jobId 
          ? { ...job, status: 'processing' } 
          : job
      ));
      
      // Navigate to status page
      navigate(`/status/${jobId}`);
    } catch (err) {
      showNotification('Failed to restart processing', 'error');
    }
  };

  const getStatusChip = (status) => {
    let color;
    let label = status.replace('_', ' ');
    
    switch (status) {
      case 'uploaded':
        color = 'default';
        break;
      case 'processing':
      case 'extracting_audio':
      case 'transcribing':
      case 'summarizing':
        color = 'primary';
        break;
      case 'completed':
        color = 'success';
        break;
      case 'failed':
        color = 'error';
        break;
      default:
        color = 'default';
    }
    
    return (
      <Chip 
        label={label} 
        color={color} 
        size="small"
        sx={{ textTransform: 'capitalize' }}
      />
    );
  };

  if (loading) {
    return (
      <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
          <CircularProgress sx={{ mb: 3 }} />
          <Typography variant="h6">Loading jobs...</Typography>
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
          onClick={fetchJobs}
        >
          Retry
        </Button>
      </Paper>
    );
  }

  return (
    <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" component="h2">
          Processing Jobs
        </Typography>
        
        <Tooltip title="Refresh">
          <IconButton onClick={fetchJobs} color="primary">
            <RefreshOutlined />
          </IconButton>
        </Tooltip>
      </Box>
      
      {jobs.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1" color="text.secondary">
            No processing jobs found
          </Typography>
          <Button 
            variant="contained" 
            onClick={() => navigate('/')}
            sx={{ mt: 2 }}
          >
            Upload a Video
          </Button>
        </Box>
      ) : (
        <TableContainer>
          <Table sx={{ minWidth: 650 }}>
            <TableHead>
              <TableRow>
                <TableCell>Filename</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="right">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {jobs.map((job) => (
                <TableRow key={job.job_id} hover>
                  <TableCell>
                    <Typography variant="body2" noWrap sx={{ maxWidth: 250 }}>
                      {job.filename}
                    </Typography>
                  </TableCell>
                  <TableCell>{getStatusChip(job.status)}</TableCell>
                  <TableCell align="right">
                    {job.status === 'completed' ? (
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<VisibilityOutlined />}
                        onClick={() => handleViewResults(job.job_id)}
                      >
                        View Results
                      </Button>
                    ) : job.status === 'failed' ? (
                      <Button
                        variant="outlined"
                        size="small"
                        color="error"
                        startIcon={<ReplayOutlined />}
                        onClick={() => handleRetryProcessing(job.job_id)}
                      >
                        Retry
                      </Button>
                    ) : (
                      <Button
                        variant="outlined"
                        size="small"
                        startIcon={<PlayArrowOutlined />}
                        onClick={() => handleViewStatus(job.job_id)}
                      >
                        View Status
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Paper>
  );
};

export default JobsList;