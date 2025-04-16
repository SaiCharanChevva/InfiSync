// import React, { useState, useEffect } from 'react';
// import {
//   Box,
//   Typography,
//   Paper,
//   Tabs,
//   Tab,
//   CircularProgress,
//   Alert,
//   Button,
//   Divider,
//   IconButton
// } from '@mui/material';
// import {
//   AudioFileOutlined,
//   TextSnippetOutlined,
//   SummarizeOutlined,
//   FileDownloadOutlined,
//   ContentCopyOutlined,
//   ReplayOutlined
// } from '@mui/icons-material';
// import Markdown from 'markdown-to-jsx';
// import axios from 'axios';

// const API_BASE_URL = 'http://localhost:5000/api';

// const ResultView = ({ jobId, showNotification }) => {
//   const [currentTab, setCurrentTab] = useState(0);
//   const [results, setResults] = useState({
//     audio: null,
//     transcript: null,
//     summary: null
//   });
//   const [loading, setLoading] = useState({
//     status: true,
//     audio: false,
//     transcript: false,
//     summary: false
//   });
//   const [error, setError] = useState(null);

//   useEffect(() => {
//     fetchJobStatus();
//   }, [jobId]);

//   const fetchJobStatus = async () => {
//     try {
//       setLoading({ ...loading, status: true });
//       const response = await axios.get(`${API_BASE_URL}/status/${jobId}`);
      
//       if (response.data.status === 'completed') {
//         // Capture result URLs
//         setResults({
//           ...results,
//           audio: response.data.results.audio,
//           transcript: response.data.results.transcript,
//           summary: response.data.results.summary
//         });
        
//         // Fetch initial data based on selected tab
//         fetchTabData(currentTab);
//       } else if (response.data.status === 'failed') {
//         setError(response.data.error || 'Job processing failed');
//       } else {
//         setError('Job has not completed processing yet');
//       }
//     } catch (err) {
//       setError(err.response?.data?.error || 'Failed to fetch job data');
//       showNotification && showNotification('Failed to fetch results', 'error');
//     } finally {
//       setLoading({ ...loading, status: false });
//     }
//   };

//   const fetchTabData = (tabIndex) => {
//     switch (tabIndex) {
//       case 0: // Audio
//         // Audio is loaded in the audio player, no need to fetch
//         break;
//       case 1: // Transcript
//         fetchTranscript();
//         break;
//       case 2: // Summary
//         fetchSummary();
//         break;
//       default:
//         break;
//     }
//   };

//   const fetchTranscript = async () => {
//     if (results.transcript && !results.transcriptContent && !loading.transcript) {
//       try {
//         setLoading({ ...loading, transcript: true });
//         const response = await axios.get(`${API_BASE_URL}/results/${jobId}/transcript`);
//         setResults({ ...results, transcriptContent: response.data.transcript });
//       } catch (err) {
//         showNotification && showNotification('Failed to load transcript', 'error');
//       } finally {
//         setLoading({ ...loading, transcript: false });
//       }
//     }
//   };

//   const fetchSummary = async () => {
//     if (results.summary && !results.summaryContent && !loading.summary) {
//       try {
//         setLoading({ ...loading, summary: true });
//         const response = await axios.get(`${API_BASE_URL}/results/${jobId}/summary`);
//         setResults({ ...results, summaryContent: response.data.summary });
//       } catch (err) {
//         showNotification && showNotification('Failed to load summary', 'error');
//       } finally {
//         setLoading({ ...loading, summary: false });
//       }
//     }
//   };

//   const handleTabChange = (event, newValue) => {
//     setCurrentTab(newValue);
//     fetchTabData(newValue);
//   };

//   const copyToClipboard = (content, type) => {
//     navigator.clipboard.writeText(content).then(
//       () => {
//         showNotification && showNotification(`${type} copied to clipboard`, 'success');
//       },
//       () => {
//         showNotification && showNotification(`Failed to copy ${type.toLowerCase()}`, 'error');
//       }
//     );
//   };

//   const downloadFile = (url, filename) => {
//     const link = document.createElement('a');
//     link.href = url;
//     link.download = filename;
//     document.body.appendChild(link);
//     link.click();
//     document.body.removeChild(link);
//   };

//   // Render loading state
//   if (loading.status) {
//     return (
//       <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
//         <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
//           <CircularProgress sx={{ mb: 3 }} />
//           <Typography variant="h6">Loading results...</Typography>
//         </Box>
//       </Paper>
//     );
//   }

//   // Render error state
//   if (error) {
//     return (
//       <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
//         <Alert severity="error" sx={{ mb: 3 }}>
//           {error}
//         </Alert>
//         <Button 
//           variant="outlined" 
//           startIcon={<ReplayOutlined />}
//           onClick={fetchJobStatus}
//         >
//           Retry Loading
//         </Button>
//       </Paper>
//     );
//   }

//   return (
//     <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
//       <Typography variant="h5" gutterBottom>
//         Meeting Results
//       </Typography>
      
//       <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
//         <Tabs 
//           value={currentTab} 
//           onChange={handleTabChange} 
//           aria-label="result tabs"
//           variant="fullWidth"
//         >
//           <Tab icon={<AudioFileOutlined />} label="Audio" />
//           <Tab icon={<TextSnippetOutlined />} label="Transcript" />
//           <Tab icon={<SummarizeOutlined />} label="Summary" />
//         </Tabs>
//       </Box>

//       <Box sx={{ py: 2, minHeight: 400 }}>
//         {/* Audio Tab */}
//         {currentTab === 0 && (
//           <Box sx={{ textAlign: 'center' }}>
//             <Typography variant="h6" gutterBottom>
//               Extracted Audio
//             </Typography>
            
//             {results.audio ? (
//               <>
//                 <Box sx={{ my: 3 }}>
//                   <audio 
//                     controls 
//                     style={{ width: '100%', maxWidth: '500px' }}
//                     src={`${API_BASE_URL}/results/${jobId}/audio`}
//                   />
//                 </Box>
                
//                 <Button
//                   variant="outlined"
//                   startIcon={<FileDownloadOutlined />}
//                   onClick={() => downloadFile(`${API_BASE_URL}/results/${jobId}/audio`, 'meeting-audio.wav')}
//                 >
//                   Download Audio
//                 </Button>
//               </>
//             ) : (
//               <Alert severity="info">
//                 Audio file not available
//               </Alert>
//             )}
//           </Box>
//         )}
        
//         {/* Transcript Tab */}
//         {currentTab === 1 && (
//           <Box>
//             <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
//               <Typography variant="h6">
//                 Meeting Transcript
//               </Typography>
              
//               {results.transcriptContent && (
//                 <IconButton 
//                   onClick={() => copyToClipboard(results.transcriptContent, 'Transcript')}
//                   color="primary"
//                   title="Copy transcript"
//                 >
//                   <ContentCopyOutlined />
//                 </IconButton>
//               )}
//             </Box>
            
//             <Divider sx={{ mb: 2 }} />
            
//             {loading.transcript ? (
//               <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
//                 <CircularProgress />
//               </Box>
//             ) : results.transcriptContent ? (
//               <Box 
//                 sx={{ 
//                   p: 2, 
//                   bgcolor: 'background.default', 
//                   borderRadius: 1,
//                   whiteSpace: 'pre-wrap',
//                   fontFamily: 'monospace',
//                   fontSize: '0.9rem',
//                   overflowY: 'auto',
//                   maxHeight: '500px'
//                 }}
//               >
//                 {results.transcriptContent}
//               </Box>
//             ) : (
//               <Alert severity="info">
//                 Transcript not available. Click the tab to load the transcript.
//               </Alert>
//             )}
//           </Box>
//         )}
        
//         {/* Summary Tab */}
//         {currentTab === 2 && (
//           <Box>
//             <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
//               <Typography variant="h6">
//                 Meeting Summary
//               </Typography>
              
//               {results.summaryContent && (
//                 <IconButton 
//                   onClick={() => copyToClipboard(results.summaryContent, 'Summary')}
//                   color="primary"
//                   title="Copy summary"
//                 >
//                   <ContentCopyOutlined />
//                 </IconButton>
//               )}
//             </Box>
            
//             <Divider sx={{ mb: 2 }} />
            
//             {loading.summary ? (
//               <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
//                 <CircularProgress />
//               </Box>
//             ) : results.summaryContent ? (
//               <Box 
//                 sx={{ 
//                   p: 2, 
//                   bgcolor: 'background.default', 
//                   borderRadius: 1,
//                   overflowY: 'auto',
//                   maxHeight: '500px'
//                 }}
//               >
//                 <Markdown>
//                   {results.summaryContent}
//                 </Markdown>
//               </Box>
//             ) : (
//               <Alert severity="info">
//                 Summary not available. Click the tab to load the summary.
//               </Alert>
//             )}
//           </Box>
//         )}
//       </Box>
//     </Paper>
//   );
// };

// export default ResultView;













import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Button,
  Divider,
  IconButton
} from '@mui/material';
import {
  AudioFileOutlined,
  TextSnippetOutlined,
  SummarizeOutlined,
  FileDownloadOutlined,
  ContentCopyOutlined,
  ReplayOutlined
} from '@mui/icons-material';
import Markdown from 'markdown-to-jsx';
import axios from 'axios';

// const API_BASE_URL = 'http://localhost:5000/api';
const API_BASE_URL = window.location.hostname === 'localhost' 
  ? 'http://localhost:5000/api'
  : 'https://infisync.onrender.com/api';

const ResultView = ({ jobId, showNotification }) => {
  const [currentTab, setCurrentTab] = useState(0);
  const [results, setResults] = useState({
    audio: null,
    transcript: null,
    summary: null,
    transcriptContent: null,
    summaryContent: null
  });
  const [loading, setLoading] = useState({
    status: true,
    audio: false,
    transcript: false,
    summary: false
  });
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchJobStatus();
  }, [jobId]);

  const fetchJobStatus = async () => {
    try {
      setLoading(prev => ({ ...prev, status: true }));
      console.log(`Fetching status for job ${jobId}`);
      
      const response = await axios.get(`${API_BASE_URL}/status/${jobId}`);
      console.log('Job status response:', response.data);
      
      if (response.data.status === 'completed') {
        // Capture result URLs
        const updatedResults = {
          ...results,
          audio: response.data.results?.audio || null,
          transcript: response.data.results?.transcript || null,
          summary: response.data.results?.summary || null
        };
        setResults(updatedResults);
        
        // Fetch initial data based on selected tab
        if (currentTab === 1 && updatedResults.transcript) {
          fetchTranscript();
        } else if (currentTab === 2 && updatedResults.summary) {
          fetchSummary();
        }
      } else if (response.data.status === 'failed') {
        setError(response.data.error || 'Job processing failed');
      } else {
        setError('Job has not completed processing yet');
      }
    } catch (err) {
      console.error('Error fetching job status:', err);
      setError('Failed to fetch job data. Please try again.');
      showNotification && showNotification('Failed to fetch results', 'error');
    } finally {
      setLoading(prev => ({ ...prev, status: false }));
    }
  };

  const fetchTranscript = async () => {
    if (!results.transcript) {
      console.log('Transcript URL not available');
      return;
    }
    
    if (results.transcriptContent) {
      console.log('Transcript content already loaded');
      return;
    }

    try {
      setLoading(prev => ({ ...prev, transcript: true }));
      console.log(`Fetching transcript from: ${API_BASE_URL}/results/${jobId}/transcript`);
      
      const response = await axios.get(`${API_BASE_URL}/results/${jobId}/transcript`);
      console.log('Transcript response:', response.data);
      
      if (response.data.transcript) {
        setResults(prev => ({ ...prev, transcriptContent: response.data.transcript }));
      } else {
        console.error('Transcript response missing transcript field:', response.data);
        showNotification && showNotification('Invalid transcript data received', 'error');
      }
    } catch (err) {
      console.error('Error fetching transcript:', err);
      showNotification && showNotification('Failed to load transcript', 'error');
    } finally {
      setLoading(prev => ({ ...prev, transcript: false }));
    }
  };

  const fetchSummary = async () => {
    if (!results.summary) {
      console.log('Summary URL not available');
      return;
    }
    
    if (results.summaryContent) {
      console.log('Summary content already loaded');
      return;
    }

    try {
      setLoading(prev => ({ ...prev, summary: true }));
      console.log(`Fetching summary from: ${API_BASE_URL}/results/${jobId}/summary`);
      
      const response = await axios.get(`${API_BASE_URL}/results/${jobId}/summary`);
      console.log('Summary response:', response.data);
      
      if (response.data.summary) {
        setResults(prev => ({ ...prev, summaryContent: response.data.summary }));
      } else {
        console.error('Summary response missing summary field:', response.data);
        showNotification && showNotification('Invalid summary data received', 'error');
      }
    } catch (err) {
      console.error('Error fetching summary:', err);
      showNotification && showNotification('Failed to load summary', 'error');
    } finally {
      setLoading(prev => ({ ...prev, summary: false }));
    }
  };

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
    
    // Fetch data for the selected tab if not already loaded
    if (newValue === 1 && results.transcript && !results.transcriptContent && !loading.transcript) {
      fetchTranscript();
    } else if (newValue === 2 && results.summary && !results.summaryContent && !loading.summary) {
      fetchSummary();
    }
  };

  const copyToClipboard = (content, type) => {
    navigator.clipboard.writeText(content).then(
      () => {
        showNotification && showNotification(`${type} copied to clipboard`, 'success');
      },
      () => {
        showNotification && showNotification(`Failed to copy ${type.toLowerCase()}`, 'error');
      }
    );
  };

  const downloadFile = (url, filename) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Render loading state
  if (loading.status) {
    return (
      <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
          <CircularProgress sx={{ mb: 3 }} />
          <Typography variant="h6">Loading results...</Typography>
        </Box>
      </Paper>
    );
  }

  // Render error state
  if (error) {
    return (
      <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
        <Button 
          variant="outlined" 
          startIcon={<ReplayOutlined />}
          onClick={fetchJobStatus}
        >
          Retry Loading
        </Button>
      </Paper>
    );
  }

  return (
    <Paper elevation={3} sx={{ p: 4, borderRadius: 2 }}>
      <Typography variant="h5" gutterBottom>
        Meeting Results
      </Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs 
          value={currentTab} 
          onChange={handleTabChange} 
          aria-label="result tabs"
          variant="fullWidth"
        >
          <Tab icon={<AudioFileOutlined />} label="Audio" />
          <Tab icon={<TextSnippetOutlined />} label="Transcript" />
          <Tab icon={<SummarizeOutlined />} label="Summary" />
        </Tabs>
      </Box>

      <Box sx={{ py: 2, minHeight: 400 }}>
        {/* Audio Tab */}
        {currentTab === 0 && (
          <Box sx={{ textAlign: 'center' }}>
            <Typography variant="h6" gutterBottom>
              Extracted Audio
            </Typography>
            
            {results.audio ? (
              <>
                <Box sx={{ my: 3 }}>
                  <audio 
                    controls 
                    style={{ width: '100%', maxWidth: '500px' }}
                    src={`${API_BASE_URL}${results.audio}`}
                  />
                </Box>
                
                <Button
                  variant="outlined"
                  startIcon={<FileDownloadOutlined />}
                  onClick={() => downloadFile(`${API_BASE_URL}${results.audio}`, 'meeting-audio.wav')}
                >
                  Download Audio
                </Button>
              </>
            ) : (
              <Alert severity="info">
                Audio file not available
              </Alert>
            )}
          </Box>
        )}
        
        {/* Transcript Tab */}
        {currentTab === 1 && (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Meeting Transcript
              </Typography>
              
              {results.transcriptContent && (
                <IconButton 
                  onClick={() => copyToClipboard(results.transcriptContent, 'Transcript')}
                  color="primary"
                  title="Copy transcript"
                >
                  <ContentCopyOutlined />
                </IconButton>
              )}
            </Box>
            
            <Divider sx={{ mb: 2 }} />
            
            {loading.transcript ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : results.transcriptContent ? (
              <Box 
                sx={{ 
                  p: 2, 
                  bgcolor: 'background.default', 
                  borderRadius: 1,
                  whiteSpace: 'pre-wrap',
                  fontFamily: 'monospace',
                  fontSize: '0.9rem',
                  overflowY: 'auto',
                  maxHeight: '500px'
                }}
              >
                {results.transcriptContent}
              </Box>
            ) : (
              <Alert severity="info" sx={{ mb: 2 }}>
                {results.transcript ? 
                  'Click the button below to load the transcript.' : 
                  'Transcript not available for this job.'}
              </Alert>
            )}
            
            {results.transcript && !results.transcriptContent && !loading.transcript && (
              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Button 
                  variant="outlined"
                  onClick={fetchTranscript}
                >
                  Load Transcript
                </Button>
              </Box>
            )}
          </Box>
        )}
        
        {/* Summary Tab */}
        {currentTab === 2 && (
          <Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Meeting Summary
              </Typography>
              
              {results.summaryContent && (
                <IconButton 
                  onClick={() => copyToClipboard(results.summaryContent, 'Summary')}
                  color="primary"
                  title="Copy summary"
                >
                  <ContentCopyOutlined />
                </IconButton>
              )}
            </Box>
            
            <Divider sx={{ mb: 2 }} />
            
            {loading.summary ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            ) : results.summaryContent ? (
              <Box 
                sx={{ 
                  p: 2, 
                  bgcolor: 'background.default', 
                  borderRadius: 1,
                  overflowY: 'auto',
                  maxHeight: '500px'
                }}
              >
                <Markdown>
                  {results.summaryContent}
                </Markdown>
              </Box>
            ) : (
              <Alert severity="info" sx={{ mb: 2 }}>
                {results.summary ? 
                  'Click the button below to load the summary.' : 
                  'Summary not available for this job.'}
              </Alert>
            )}
            
            {results.summary && !results.summaryContent && !loading.summary && (
              <Box sx={{ textAlign: 'center', mt: 2 }}>
                <Button 
                  variant="outlined"
                  onClick={fetchSummary}
                >
                  Load Summary
                </Button>
              </Box>
            )}
          </Box>
        )}
      </Box>
    </Paper>
  );
};

export default ResultView;
