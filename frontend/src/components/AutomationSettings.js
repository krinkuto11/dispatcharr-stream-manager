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
  Grid
} from '@mui/material';
import { automationAPI } from '../services/api';

function AutomationSettings() {
  const [config, setConfig] = useState(null);
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
      const response = await automationAPI.getConfig();
      setConfig(response.data);
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
      await automationAPI.updateConfig(config);
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

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (!config) {
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