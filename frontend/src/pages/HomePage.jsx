import React from 'react';
import { Box, Typography, Container, Grid, Paper, Card, CardContent, Button } from '@mui/material';
import { AudioFileOutlined, TextSnippetOutlined, SummarizeOutlined, Upload } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import FileUpload from '../components/FileUpload';

const HomePage = ({ apiConnected, showNotification }) => {
  const navigate = useNavigate();

  const features = [
    {
      title: 'Audio Extraction',
      description: 'Extract high-quality audio from your meeting recordings automatically.',
      icon: <AudioFileOutlined sx={{ fontSize: 40, color: 'primary.main' }} />,
    },
    {
      title: 'Transcription',
      description: 'Convert speech to text using advanced AI speech recognition.',
      icon: <TextSnippetOutlined sx={{ fontSize: 40, color: 'primary.main' }} />,
    },
    {
      title: 'Smart Summaries',
      description: 'Generate concise meeting summaries with key points and action items.',
      icon: <SummarizeOutlined sx={{ fontSize: 40, color: 'primary.main' }} />,
    },
  ];

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 6 }}>
        <Grid container spacing={4}>
          {/* Left column: Hero content */}
          <Grid item xs={12} md={6}>
            <Box sx={{ py: 4 }}>
              <Typography 
                variant="h2" 
                component="h1" 
                gutterBottom 
                sx={{ 
                  fontWeight: 700,
                  fontSize: { xs: '2.5rem', md: '3.5rem' }
                }}
              >
                Meeting Assistant
              </Typography>
              
              <Typography 
                variant="h5" 
                component="h2" 
                color="text.secondary" 
                paragraph
                sx={{ mb: 4 }}
              >
                Upload your meeting recordings and let AI do the rest.
                Get audio extraction, transcripts, and smart summaries in minutes.
              </Typography>
              
              <Button 
                variant="contained" 
                size="large" 
                endIcon={<Upload />}
                onClick={() => document.getElementById('file-upload-section').scrollIntoView({ behavior: 'smooth' })}
                sx={{ mb: 2 }}
              >
                Upload a Meeting
              </Button>
              
              <Button 
                variant="outlined" 
                size="large" 
                onClick={() => navigate('/jobs')}
                sx={{ ml: { xs: 0, sm: 2 }, mb: 2 }}
              >
                View Previous Jobs
              </Button>
            </Box>
          </Grid>
          
          {/* Right column: Features */}
          <Grid item xs={12} md={6}>
            <Box 
              sx={{ 
                display: 'flex', 
                flexDirection: 'column', 
                gap: 2,
                height: '100%',
                justifyContent: 'center'
              }}
            >
              {features.map((feature, index) => (
                <Card key={index} variant="outlined" sx={{ borderRadius: 2 }}>
                  <CardContent sx={{ display: 'flex', alignItems: 'flex-start', p: 3 }}>
                    <Box sx={{ mr: 2 }}>
                      {feature.icon}
                    </Box>
                    <Box>
                      <Typography variant="h6" component="h3" gutterBottom>
                        {feature.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {feature.description}
                      </Typography>
                    </Box>
                  </CardContent>
                </Card>
              ))}
            </Box>
          </Grid>
        </Grid>
      </Box>
      
      <Box id="file-upload-section" sx={{ py: 4 }}>
        <FileUpload apiConnected={apiConnected} showNotification={showNotification} />
      </Box>
    </Container>
  );
};

export default HomePage;
