import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Typography, 
  Button, 
  Paper, 
  LinearProgress,
  CircularProgress,
  Alert,
  Stack,
  IconButton
} from '@mui/material';
import { 
  CloudUploadOutlined, 
  InsertDriveFileOutlined, 
  DeleteOutline,
  UploadFileOutlined
} from '@mui/icons-material';
import axios from 'axios';

// const API_BASE_URL = 'http://localhost:5000/api';
const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:5000/api'
  : 'https://infisync.onrender.com/api';

const FileUpload = ({ apiConnected, showNotification }) => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    validateAndSetFile(file);
  };

  const handleDragOver = (event) => {
    event.preventDefault();
  };

  const handleDrop = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    validateAndSetFile(file);
  };

  const validateAndSetFile = (file) => {
    setError(null);
    
    // Check if a file was selected
    if (!file) {
      return;
    }
    
    // Check if file is a video
    if (!file.type.startsWith('video/')) {
      setError('Please select a video file');
      return;
    }
    
    // Check file size (100MB limit)
    if (file.size > 100 * 1024 * 1024) {
      setError('File size exceeds 100MB limit');
      return;
    }
    
    setSelectedFile(file);
  };

  const handleUpload = async () => {
    if (!selectedFile || !apiConnected) return;

    try {
      setUploading(true);
      setUploadProgress(0);
      setError(null);

      // Create form data
      const formData = new FormData();
      formData.append('file', selectedFile);

      // Upload file
      const uploadResponse = await axios.post(`${API_BASE_URL}/upload`, formData, {
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          setUploadProgress(percentCompleted);
        },
      });

      if (uploadResponse.data && uploadResponse.data.job_id) {
        // Start processing
        await axios.post(`${API_BASE_URL}/process/${uploadResponse.data.job_id}`);
        
        // Navigate to status page
        navigate(`/status/${uploadResponse.data.job_id}`);
        
        showNotification('Video uploaded successfully. Processing started.', 'success');
      }
    } catch (error) {
      console.error('Upload error:', error);
      setError(error.response?.data?.error || 'Failed to upload file');
      showNotification('Failed to upload file', 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' bytes';
    else if (bytes < 1048576) return (bytes / 1024).toFixed(2) + ' KB';
    else return (bytes / 1048576).toFixed(2) + ' MB';
  };

  return (
    <Paper
      elevation={3}
      sx={{
        p: 4,
        borderRadius: 2,
        bgcolor: 'background.paper',
        maxWidth: 600,
        mx: 'auto',
      }}
    >
      <Typography variant="h5" component="h2" gutterBottom sx={{ fontWeight: 500 }}>
        Upload Meeting Recording
      </Typography>
      
      <Typography variant="body1" color="text.secondary" paragraph>
        Upload a video recording of your meeting to extract audio, transcribe, and generate a summary.
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <Box
        sx={{
          border: '2px dashed',
          borderColor: 'divider',
          borderRadius: 2,
          p: 3,
          mb: 3,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'background.default',
          cursor: !uploading ? 'pointer' : 'default',
          transition: 'all 0.2s ease-in-out',
          '&:hover': {
            borderColor: !uploading ? 'primary.main' : 'divider',
            backgroundColor: !uploading ? 'rgba(25, 118, 210, 0.04)' : 'background.default',
          },
        }}
        onClick={() => !uploading && fileInputRef.current?.click()}
        onDragOver={handleDragOver}
        onDrop={!uploading ? handleDrop : undefined}
      >
        <input
          type="file"
          accept="video/*"
          onChange={handleFileSelect}
          ref={fileInputRef}
          style={{ display: 'none' }}
          disabled={uploading}
        />

        {selectedFile ? (
          <Box sx={{ width: '100%', textAlign: 'center' }}>
            <InsertDriveFileOutlined sx={{ fontSize: 48, color: 'primary.main', mb: 1 }} />
            <Typography variant="body1" fontWeight={500} noWrap>
              {selectedFile.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {formatFileSize(selectedFile.size)}
            </Typography>
            
            {!uploading && (
              <IconButton 
                color="error" 
                onClick={(e) => {
                  e.stopPropagation();
                  handleRemoveFile();
                }}
                size="small"
                sx={{ mt: 1 }}
              >
                <DeleteOutline />
              </IconButton>
            )}
          </Box>
        ) : (
          <>
            <CloudUploadOutlined sx={{ fontSize: 48, color: 'text.secondary', mb: 2 }} />
            <Typography variant="h6" align="center" gutterBottom>
              Drag and drop video file here
            </Typography>
            <Typography variant="body2" align="center" color="text.secondary">
              or click to browse
            </Typography>
            <Typography variant="caption" align="center" color="text.secondary" sx={{ mt: 1 }}>
              Supported formats: MP4, MOV, AVI, WMV, etc.
            </Typography>
          </>
        )}
      </Box>

      {uploading && (
        <Box sx={{ width: '100%', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
            <Box sx={{ width: '100%', mr: 1 }}>
              <LinearProgress variant="determinate" value={uploadProgress} />
            </Box>
            <Box sx={{ minWidth: 35 }}>
              <Typography variant="body2" color="text.secondary">{`${uploadProgress}%`}</Typography>
            </Box>
          </Box>
        </Box>
      )}

      <Stack direction="row" spacing={2} justifyContent="center">
        <Button
          variant="contained"
          color="primary"
          size="large"
          startIcon={uploading ? <CircularProgress size={20} color="inherit" /> : <UploadFileOutlined />}
          onClick={handleUpload}
          disabled={!selectedFile || uploading || !apiConnected}
          sx={{ minWidth: 150 }}
        >
          {uploading ? 'Uploading...' : 'Upload & Process'}
        </Button>
      </Stack>
    </Paper>
  );
};

export default FileUpload;
