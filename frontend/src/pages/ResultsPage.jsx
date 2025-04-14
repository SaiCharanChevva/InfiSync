import React from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, Container, Breadcrumbs, Link } from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import ResultView from '../components/ResultView';

const ResultsPage = ({ showNotification }) => {
  const { jobId } = useParams();

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Breadcrumbs aria-label="breadcrumb" sx={{ mb: 2 }}>
          <Link component={RouterLink} to="/" underline="hover" color="inherit">
            Home
          </Link>
          <Link component={RouterLink} to="/jobs" underline="hover" color="inherit">
            Jobs
          </Link>
          <Typography color="text.primary">Results</Typography>
        </Breadcrumbs>
        
        <Typography variant="h4" component="h1" gutterBottom>
          Meeting Results
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          View the audio, transcript, and summary of your processed meeting recording.
        </Typography>
      </Box>
      
      <ResultView jobId={jobId} showNotification={showNotification} />
    </Container>
  );
};

export default ResultsPage;