import React, { useState, useEffect, useCallback } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  CircularProgress,
  Alert,
  LinearProgress,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckIcon,
  PlaylistPlay as GlobalActionIcon
} from '@mui/icons-material';
import { streamCheckerAPI } from '../services/api';

function StreamChecker() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const loadStatus = useCallback(async () => {
    try {
      const response = await streamCheckerAPI.getStatus();
      setStatus(response.data);
      setError('');
    } catch (err) {
      console.error('Failed to load stream checker status:', err);
      // Only show error on first load
      if (loading) {
        setError('Failed to load stream checker status');
      }
    } finally {
      setLoading(false);
    }
  }, [loading]);

  useEffect(() => {
    loadStatus();
    const interval = setInterval(loadStatus, 10000);
    return () => clearInterval(interval);
  }, [loadStatus]);

  const handleToggle = async () => {
    try {
      setActionLoading('toggle');
      if (status?.running) {
        await streamCheckerAPI.stop();
        setSuccess('Stream checker stopped');
      } else {
        await streamCheckerAPI.start();
        setSuccess('Stream checker started');
      }
      await loadStatus();
    } catch (err) {
      setError(`Failed to ${status?.running ? 'stop' : 'start'} stream checker`);
    } finally {
      setActionLoading('');
    }
  };

  const handleClearQueue = async () => {
    try {
      setActionLoading('clear');
      await streamCheckerAPI.clearQueue();
      setSuccess('Queue cleared');
      await loadStatus();
    } catch (err) {
      setError('Failed to clear queue');
    } finally {
      setActionLoading('');
    }
  };



  const handleGlobalAction = async () => {
    try {
      setActionLoading('globalAction');
      const response = await streamCheckerAPI.triggerGlobalAction();
      setSuccess(response.data?.message || 'Global action triggered: Update, Match, and Check all channels');
      await loadStatus();
    } catch (err) {
      setError('Failed to trigger global action');
    } finally {
      setActionLoading('');
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  const queue = status?.queue || {};
  const progress = status?.progress || null;
  const config = status?.config || {};

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Stream Checker
        </Typography>
        <Box>
          <Button
            variant="contained"
            color={status?.running ? "error" : "primary"}
            startIcon={status?.running ? <StopIcon /> : <StartIcon />}
            onClick={handleToggle}
            disabled={actionLoading === 'toggle'}
            sx={{ mr: 1 }}
          >
            {actionLoading === 'toggle' ? (
              <CircularProgress size={20} />
            ) : status?.running ? (
              'Stop Checker'
            ) : (
              'Start Checker'
            )}
          </Button>
          <IconButton
            onClick={loadStatus}
            disabled={loading}
            color="primary"
          >
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess('')} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Status
              </Typography>
              <Box display="flex" alignItems="center" mt={1}>
                {status?.running ? (
                  <Chip
                    icon={<CheckIcon />}
                    label="Running"
                    color="success"
                    size="small"
                  />
                ) : (
                  <Chip label="Stopped" color="default" size="small" />
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Queue Size
              </Typography>
              <Typography variant="h4">
                {queue.queue_size || 0}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                channels pending
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Completed
              </Typography>
              <Typography variant="h4" color="success.main">
                {queue.total_completed || 0}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                channels checked
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Failed
              </Typography>
              <Typography variant="h4" color="error.main">
                {queue.total_failed || 0}
              </Typography>
              <Typography variant="caption" color="textSecondary">
                with errors
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {progress && status?.checking && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Current Check
                </Typography>
                <Typography variant="body2" gutterBottom>
                  Channel: <strong>{progress.channel_name}</strong> (ID: {progress.channel_id})
                </Typography>
                <Typography variant="body2" gutterBottom>
                  Stream: {progress.current_stream}/{progress.total_streams} - {progress.current_stream_name}
                </Typography>
                
                {/* Overall Progress Bar */}
                <Box sx={{ mt: 2, mb: 1 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                    <Typography variant="caption" color="textSecondary">
                      Overall Progress
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      {progress.percentage}%
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={progress.percentage || 0}
                    sx={{ height: 10, borderRadius: 5 }}
                  />
                </Box>

                {/* Step Progress Bar */}
                {progress.step && (
                  <Box sx={{ mt: 2, mb: 1 }}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                      <Typography variant="caption" color="textSecondary" fontWeight="bold">
                        Current Step: {progress.step}
                      </Typography>
                      <Chip 
                        label={progress.status || 'processing'} 
                        size="small" 
                        color="primary"
                        sx={{ height: 20 }}
                      />
                    </Box>
                    {progress.step_detail && (
                      <Typography variant="caption" color="textSecondary" display="block" sx={{ mb: 0.5 }}>
                        {progress.step_detail}
                      </Typography>
                    )}
                    <LinearProgress
                      variant="indeterminate"
                      sx={{ height: 8, borderRadius: 5 }}
                      color="secondary"
                    />
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                <Typography variant="h6">
                  Queue Status
                </Typography>
                <Box>
                  <Tooltip title="Update M3U → Match streams → Check all channels (bypasses 2-hour immunity)">
                    <Button
                      size="small"
                      variant="contained"
                      color="secondary"
                      onClick={handleGlobalAction}
                      disabled={actionLoading === 'globalAction' || !status?.running}
                      startIcon={<GlobalActionIcon />}
                      sx={{ mr: 1 }}
                    >
                      {actionLoading === 'globalAction' ? 'Running...' : 'Global Action'}
                    </Button>
                  </Tooltip>
                  <Button
                    size="small"
                    variant="outlined"
                    color="error"
                    onClick={handleClearQueue}
                    disabled={actionLoading === 'clear' || queue.queue_size === 0}
                  >
                    Clear Queue
                  </Button>
                </Box>
              </Box>
              <Divider sx={{ mb: 2 }} />
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Queue Size"
                    secondary={`${queue.queue_size || 0} channels waiting`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="In Progress"
                    secondary={`${queue.in_progress || 0} channels being checked`}
                  />
                </ListItem>
                <ListItem>
                  <ListItemText
                    primary="Total Queued"
                    secondary={`${queue.total_queued || 0} channels queued (lifetime)`}
                  />
                </ListItem>
                {queue.current_channel && (
                  <ListItem>
                    <ListItemText
                      primary="Current Channel"
                      secondary={`Channel ID: ${queue.current_channel}`}
                    />
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Pipeline Information
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <List dense>
                <ListItem>
                  <ListItemText
                    primary="Active Pipeline"
                    secondary={(() => {
                      const mode = status?.config?.pipeline_mode || 'pipeline_1_5';
                      const modeNames = {
                        'disabled': 'Disabled',
                        'pipeline_1': 'Pipeline 1: Update → Match → Check (with 2hr immunity)',
                        'pipeline_1_5': 'Pipeline 1.5: Pipeline 1 + Scheduled Global Action',
                        'pipeline_2': 'Pipeline 2: Update → Match only (no checking)',
                        'pipeline_2_5': 'Pipeline 2.5: Pipeline 2 + Scheduled Global Action',
                        'pipeline_3': 'Pipeline 3: Only Scheduled Global Action'
                      };
                      return modeNames[mode] || mode;
                    })()}
                  />
                </ListItem>
                {['pipeline_1_5', 'pipeline_2_5', 'pipeline_3'].includes(status?.config?.pipeline_mode) && (
                  <ListItem>
                    <ListItemText
                      primary="Scheduled Global Action"
                      secondary={
                        config.global_check_schedule
                          ? `${config.global_check_schedule.frequency || 'daily'} at ${config.global_check_schedule.hour}:${String(config.global_check_schedule.minute).padStart(2, '0')}`
                          : 'Not configured'
                      }
                    />
                  </ListItem>
                )}
                <ListItem>
                  <ListItemText
                    primary="Last Global Action"
                    secondary={
                      status?.last_global_check
                        ? new Date(status.last_global_check).toLocaleString()
                        : 'Never'
                    }
                  />
                </ListItem>
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12}>
          <Alert severity="info">
            <Typography variant="body2">
              <strong>How it works:</strong> The stream checker automatically monitors channels for M3U updates
              and checks their streams for quality based on your pipeline mode. Streams are analyzed for bitrate, 
              resolution, codec quality, and errors, then automatically reordered with the best streams at the top.
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              <strong>Global Action:</strong> Performs a complete update cycle (Update M3U → Match streams → 
              Check all channels) bypassing the 2-hour immunity. Use this for manual full updates or schedule it
              for off-peak hours.
            </Typography>
          </Alert>
        </Grid>
      </Grid>
    </Box>
  );
}

export default StreamChecker;
