import React, { useState, useEffect } from 'react';
import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box,
  IconButton,
  Alert,
  Snackbar,
  Button
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Settings as SettingsIcon,
  PlaylistAdd as PlaylistIcon,
  History as HistoryIcon,
  Menu as MenuIcon,
  Close as CloseIcon,
  CheckCircle as StreamCheckerIcon
} from '@mui/icons-material';

import Dashboard from './components/Dashboard';
import ChannelConfiguration from './components/ChannelConfiguration';
import AutomationSettings from './components/AutomationSettings';
import Changelog from './components/Changelog';
import StreamChecker from './components/StreamChecker';
import SetupWizard from './components/SetupWizard';
import { api } from './services/api';

const drawerWidth = 240;

function App() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [setupStatus, setSetupStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    checkSetupStatus();
  }, []);

  const checkSetupStatus = async () => {
    try {
      setLoading(true);
      const response = await api.get('/setup-wizard');
      setSetupStatus(response.data);
    } catch (err) {
      console.error('Failed to check setup status:', err);
      setError('Failed to connect to the backend server');
    } finally {
      setLoading(false);
    }
  };

  const handleDrawerToggle = () => {
    setDrawerOpen(!drawerOpen);
  };

  const menuItems = [
    { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
    { text: 'Stream Checker', icon: <StreamCheckerIcon />, path: '/stream-checker' },
    { text: 'Channel Configuration', icon: <PlaylistIcon />, path: '/channels' },
    { text: 'Automation Settings', icon: <SettingsIcon />, path: '/settings' },
    { text: 'Changelog', icon: <HistoryIcon />, path: '/changelog' },
  ];

  const handleNavigation = (path) => {
    navigate(path);
    setDrawerOpen(false);
  };

  const handleSetupComplete = () => {
    // Re-check status after setup completion
    checkSetupStatus();
    // Navigate to dashboard after successful setup
    navigate('/');
  };

  const setupComplete = setupStatus?.setup_complete || false;

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100vh">
        <Typography>Loading...</Typography>
      </Box>
    );
  }

  if (!setupComplete && setupStatus) {
    return <SetupWizard onComplete={handleSetupComplete} setupStatus={setupStatus} />;
  }

  if (!setupComplete && !setupStatus && error) {
    return (
      <Box display="flex" flexDirection="column" justifyContent="center" alignItems="center" height="100vh" p={3}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={checkSetupStatus}>
          Retry Connection
        </Button>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            StreamFlow for Dispatcharr
          </Typography>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="temporary"
        open={drawerOpen}
        onClose={handleDrawerToggle}
        ModalProps={{
          keepMounted: true,
        }}
        sx={{
          '& .MuiDrawer-paper': {
            boxSizing: 'border-box',
            width: drawerWidth,
          },
        }}
      >
        <Toolbar>
          <IconButton onClick={handleDrawerToggle}>
            <CloseIcon />
          </IconButton>
        </Toolbar>
        <List>
          {menuItems.map((item) => (
            <ListItem
              button
              key={item.text}
              onClick={() => handleNavigation(item.path)}
              selected={location.pathname === item.path}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItem>
          ))}
        </List>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Container maxWidth="xl">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/stream-checker" element={<StreamChecker />} />
            <Route path="/channels" element={<ChannelConfiguration />} />
            <Route path="/settings" element={<AutomationSettings />} />
            <Route path="/changelog" element={<Changelog />} />
          </Routes>
        </Container>
      </Box>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError('')}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'left' }}
      >
        <Alert onClose={() => setError('')} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default App;