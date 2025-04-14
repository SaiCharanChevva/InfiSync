import React, { useState } from 'react';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import {
  AppBar,
  Box,
  Toolbar,
  Typography,
  Button,
  Container,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Chip,
  Tooltip,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import {
  HomeOutlined,
  ListAltOutlined,
  MenuOutlined,
  CloudDoneOutlined,
  CloudOffOutlined,
  RefreshOutlined,
} from '@mui/icons-material';

const navItems = [
  { text: 'Home', path: '/', icon: <HomeOutlined /> },
  { text: 'Jobs', path: '/jobs', icon: <ListAltOutlined /> },
];

const AppHeader = ({ apiConnected, checkingApi, onRetryConnection }) => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <Box onClick={handleDrawerToggle} sx={{ textAlign: 'center' }}>
      <Typography variant="h6" sx={{ my: 2 }}>
        Meeting Summarizer
      </Typography>
      <List>
        {navItems.map((item) => (
          <ListItem
            key={item.text}
            component={RouterLink}
            to={item.path}
            button
            selected={location.pathname === item.path}
            sx={{
              color: location.pathname === item.path ? 'primary.main' : 'text.primary',
              '&.Mui-selected': {
                backgroundColor: 'rgba(25, 118, 210, 0.08)',
              },
            }}
          >
            <ListItemIcon>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} />
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <AppBar position="sticky" color="default" elevation={1} sx={{ backgroundColor: 'background.paper' }}>
      <Container maxWidth="xl">
        <Toolbar disableGutters sx={{ display: 'flex', justifyContent: 'space-between' }}>
          {/* Left: Logo and Mobile Menu */}
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {isMobile && (
              <IconButton
                color="inherit"
                aria-label="open drawer"
                edge="start"
                onClick={handleDrawerToggle}
                sx={{ mr: 2 }}
              >
                <MenuOutlined />
              </IconButton>
            )}
            <RouterLink to="/" style={{ textDecoration: 'none', color: 'inherit', display: 'flex', alignItems: 'center' }}>
              <Typography
                variant="h6"
                component="div"
                sx={{
                  fontWeight: 700,
                  letterSpacing: '.1rem',
                  color: 'text.primary',
                }}
              >
                MEETING SUMMARIZER
              </Typography>
            </RouterLink>
          </Box>

          {/* Middle: Navigation (desktop only) */}
          {!isMobile && (
            <Box sx={{ flexGrow: 1, display: 'flex', justifyContent: 'center' }}>
              {navItems.map((item) => (
                <Button
                  key={item.text}
                  component={RouterLink}
                  to={item.path}
                  sx={{
                    mx: 1,
                    color: location.pathname === item.path ? 'primary.main' : 'text.primary',
                    fontWeight: location.pathname === item.path ? 700 : 500,
                    '&:hover': {
                      backgroundColor: 'rgba(25, 118, 210, 0.04)',
                    },
                  }}
                  startIcon={item.icon}
                >
                  {item.text}
                </Button>
              ))}
            </Box>
          )}

          {/* Right: API Status */}
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {checkingApi ? (
              <Chip 
                label="Checking API" 
                color="default" 
                size="small" 
                variant="outlined" 
                sx={{ mr: isMobile ? 0 : 2 }}
              />
            ) : apiConnected ? (
              <Tooltip title="API Connected">
                <Chip 
                  icon={<CloudDoneOutlined />} 
                  label="API Connected" 
                  color="success" 
                  size="small" 
                  variant="outlined" 
                  sx={{ mr: isMobile ? 0 : 2 }}
                />
              </Tooltip>
            ) : (
              <Tooltip title="Retry Connection">
                <Chip 
                  icon={<CloudOffOutlined />}
                  label="API Disconnected" 
                  color="error" 
                  size="small" 
                  variant="outlined" 
                  onClick={onRetryConnection}
                  onDelete={onRetryConnection}
                  deleteIcon={<RefreshOutlined />}
                  sx={{ mr: isMobile ? 0 : 2 }}
                />
              </Tooltip>
            )}
          </Box>
        </Toolbar>
      </Container>

      <Drawer
        variant="temporary"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile.
        }}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 280 },
        }}
      >
        {drawer}
      </Drawer>
    </AppBar>
  );
};

export default AppHeader;
