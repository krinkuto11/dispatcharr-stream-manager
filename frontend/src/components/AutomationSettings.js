import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  TextField,
  FormGroup,
  FormControlLabel,
  Switch,
  Button,
  Alert,
  CircularProgress,
  Grid,
  RadioGroup,
  Radio,
  FormControl,
  FormLabel
} from '@mui/material';
import { automationAPI, streamCheckerAPI } from '../services/api';

function AutomationSettings() {
  const [config, setConfig] = useState(null);
  const [streamCheckerConfig, setStreamCheckerConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  useEffect(() => {
    loadConfig();
  }, []);

  const loadConfig = async () => {
    try {
      setLoading(true);
      const [automationResponse, streamCheckerResponse] = await Promise.all([
        automationAPI.getConfig(),
        streamCheckerAPI.getConfig()
      ]);
      setConfig(automationResponse.data);
      setStreamCheckerConfig(streamCheckerResponse.data);
    } catch (err) {
      console.error('Failed to load config:', err);
      setError('Failed to load automation configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      await Promise.all([
        automationAPI.updateConfig(config),
        streamCheckerAPI.updateConfig(streamCheckerConfig)
      ]);
      setSuccess('Configuration saved successfully');
    } catch (err) {
      setError('Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const handleConfigChange = (field, value) => {
    if (field.includes('.')) {
      const [parent, child] = field.split('.');
      setConfig(prev => ({
        ...prev,
        [parent]: {
          ...prev[parent],
          [child]: value
        }
      }));
    } else {
      setConfig(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  const handleStreamCheckerConfigChange = (field, value) => {
    if (field.includes('.')) {
      const parts = field.split('.');
      if (parts.length === 2) {
        const [parent, child] = parts;
        setStreamCheckerConfig(prev => ({
          ...prev,
          [parent]: {
            ...prev[parent],
            [child]: value
          }
        }));
      }
    } else {
      setStreamCheckerConfig(prev => ({
        ...prev,
        [field]: value
      }));
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!config || !streamCheckerConfig) {
    return (
      <Alert severity="error">
        Failed to load configuration
      </Alert>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Automation Settings
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* General Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                General Settings
              </Typography>
              
              <TextField
                label="Playlist Update Interval (minutes)"
                type="number"
                value={config.playlist_update_interval_minutes || 5}
                onChange={(e) => handleConfigChange('playlist_update_interval_minutes', parseInt(e.target.value))}
                fullWidth
                margin="normal"
                helperText="How often to check for playlist updates"
              />
            </CardContent>
          </Card>
        </Grid>

        {/* Global Check Schedule */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Global Check Schedule
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={streamCheckerConfig.global_check_schedule?.enabled !== false}
                    onChange={(e) => handleStreamCheckerConfigChange('global_check_schedule.enabled', e.target.checked)}
                  />
                }
                label="Enable Scheduled Global Check"
                sx={{ mb: 2 }}
              />
              
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Configure when the global channel check runs to verify stream quality across all channels.
              </Typography>
              
              <FormControl component="fieldset" sx={{ mb: 2 }}>
                <FormLabel component="legend">Frequency</FormLabel>
                <RadioGroup
                  row
                  value={streamCheckerConfig.global_check_schedule?.frequency ?? 'daily'}
                  onChange={(e) => handleStreamCheckerConfigChange('global_check_schedule.frequency', e.target.value)}
                >
                  <FormControlLabel 
                    value="daily" 
                    control={<Radio />} 
                    label="Daily" 
                    disabled={streamCheckerConfig.global_check_schedule?.enabled === false}
                  />
                  <FormControlLabel 
                    value="monthly" 
                    control={<Radio />} 
                    label="Monthly" 
                    disabled={streamCheckerConfig.global_check_schedule?.enabled === false}
                  />
                </RadioGroup>
              </FormControl>
              
              {(streamCheckerConfig.global_check_schedule?.frequency ?? 'daily') === 'monthly' && (
                <TextField
                  label="Day of Month"
                  type="number"
                  value={streamCheckerConfig.global_check_schedule?.day_of_month ?? 1}
                  onChange={(e) => handleStreamCheckerConfigChange('global_check_schedule.day_of_month', parseInt(e.target.value))}
                  inputProps={{ min: 1, max: 31 }}
                  disabled={streamCheckerConfig.global_check_schedule?.enabled === false}
                  fullWidth
                  margin="normal"
                  helperText="Day of the month to run the check (1-31)"
                />
              )}
              
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  label="Hour (0-23)"
                  type="number"
                  value={streamCheckerConfig.global_check_schedule?.hour ?? 3}
                  onChange={(e) => handleStreamCheckerConfigChange('global_check_schedule.hour', parseInt(e.target.value))}
                  inputProps={{ min: 0, max: 23 }}
                  disabled={streamCheckerConfig.global_check_schedule?.enabled === false}
                  sx={{ flex: 1 }}
                  helperText="Hour (24-hour format)"
                />
                <TextField
                  label="Minute (0-59)"
                  type="number"
                  value={streamCheckerConfig.global_check_schedule?.minute ?? 0}
                  onChange={(e) => handleStreamCheckerConfigChange('global_check_schedule.minute', parseInt(e.target.value))}
                  inputProps={{ min: 0, max: 59 }}
                  disabled={streamCheckerConfig.global_check_schedule?.enabled === false}
                  sx={{ flex: 1 }}
                  helperText="Minute"
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Enabled Features */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Enabled Features
              </Typography>
              
              <FormGroup>
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.enabled_features?.auto_playlist_update !== false}
                      onChange={(e) => handleConfigChange('enabled_features.auto_playlist_update', e.target.checked)}
                    />
                  }
                  label="Auto Playlist Update"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.enabled_features?.auto_stream_discovery !== false}
                      onChange={(e) => handleConfigChange('enabled_features.auto_stream_discovery', e.target.checked)}
                    />
                  }
                  label="Auto Stream Discovery"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={config.enabled_features?.changelog_tracking !== false}
                      onChange={(e) => handleConfigChange('enabled_features.changelog_tracking', e.target.checked)}
                    />
                  }
                  label="Changelog Tracking"
                />
              </FormGroup>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
        <Button
          variant="contained"
          onClick={handleSave}
          disabled={saving}
          size="large"
        >
          {saving ? <CircularProgress size={20} /> : 'Save Settings'}
        </Button>
      </Box>
    </Box>
  );
}

export default AutomationSettings;