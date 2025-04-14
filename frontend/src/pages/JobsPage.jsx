import React from 'react';
import { Box, Typography, Container } from '@mui/material';
import JobsList from '../components/JobsList';

const JobsPage = ({ showNotification }) => {
  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Processing Jobs
        </Typography>
        <Typography variant="body1" color="text.secondary" paragraph>
          View and manage your meeting processing jobs.
        </Typography>
      </Box>
      
      <JobsList showNotification={showNotification} />
    </Container>
  );
};

export default JobsPage;