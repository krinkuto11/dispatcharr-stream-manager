import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
  TableSortLabel,
  InputAdornment
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Search as SearchIcon
} from '@mui/icons-material';
import { channelsAPI, regexAPI } from '../services/api';

function ChannelConfiguration() {
  const [channels, setChannels] = useState([]);
  const [patterns, setPatterns] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [openDialog, setOpenDialog] = useState(false);
  const [editingPattern, setEditingPattern] = useState(null);
  const [formData, setFormData] = useState({
    channel_id: '',
    name: '',
    regex: [''],
    enabled: true
  });
  const [testResults, setTestResults] = useState(null);
  const [testingPattern, setTestingPattern] = useState(false);
  
  // Search and sorting state
  const [searchQuery, setSearchQuery] = useState('');
  const [orderBy, setOrderBy] = useState('channel_number');
  const [order, setOrder] = useState('asc');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [channelsResponse, patternsResponse] = await Promise.all([
        channelsAPI.getChannels(),
        regexAPI.getPatterns()
      ]);
      
      setChannels(channelsResponse.data);
      setPatterns(patternsResponse.data);
    } catch (err) {
      console.error('Failed to load data:', err);
      setError('Failed to load channel data');
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDialog = (channel = null) => {
    if (channel) {
      const existingPattern = patterns.patterns?.[channel.id];
      setEditingPattern(channel.id);
      setFormData({
        channel_id: channel.id,
        name: existingPattern?.name || channel.name,
        regex: existingPattern?.regex || [''],
        enabled: existingPattern?.enabled !== false
      });
    } else {
      setEditingPattern(null);
      setFormData({
        channel_id: '',
        name: '',
        regex: [''],
        enabled: true
      });
    }
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    setEditingPattern(null);
    setTestResults(null);
    setFormData({
      channel_id: '',
      name: '',
      regex: [''],
      enabled: true
    });
  };

  const handleTestPattern = async () => {
    try {
      setTestingPattern(true);
      setError('');
      
      // Filter out empty patterns
      const validPatterns = formData.regex.filter(r => r.trim() !== '');
      
      if (validPatterns.length === 0) {
        setError('Please enter at least one pattern to test');
        setTestingPattern(false);
        return;
      }
      
      const response = await regexAPI.testPatternLive({
        patterns: [{
          channel_id: formData.channel_id || 'test',
          channel_name: formData.name || 'Test Channel',
          regex: validPatterns
        }],
        case_sensitive: false,
        max_matches: 50
      });
      
      setTestResults(response.data);
      setSuccess(`Found ${response.data.results[0]?.match_count || 0} matching streams`);
    } catch (err) {
      console.error('Failed to test pattern:', err);
      setError('Failed to test pattern: ' + (err.response?.data?.error || err.message));
    } finally {
      setTestingPattern(false);
    }
  };

  const handleSavePattern = async () => {
    try {
      await regexAPI.addPattern(formData);
      setSuccess('Pattern saved successfully');
      handleCloseDialog();
      await loadData();
    } catch (err) {
      setError('Failed to save pattern: ' + (err.response?.data?.error || err.message));
    }
  };

  const handleDeletePattern = async (channelId) => {
    try {
      await regexAPI.deletePattern(channelId);
      setSuccess('Pattern deleted successfully');
      await loadData();
    } catch (err) {
      setError('Failed to delete pattern');
    }
  };

  const addRegexField = () => {
    setFormData(prev => ({
      ...prev,
      regex: [...prev.regex, '']
    }));
  };

  const updateRegexField = (index, value) => {
    setFormData(prev => ({
      ...prev,
      regex: prev.regex.map((r, i) => i === index ? value : r)
    }));
  };

  const removeRegexField = (index) => {
    setFormData(prev => ({
      ...prev,
      regex: prev.regex.filter((_, i) => i !== index)
    }));
  };

  // Sorting handler
  const handleRequestSort = (property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  // Filter and sort channels
  const getFilteredAndSortedChannels = () => {
    let filteredChannels = channels;

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filteredChannels = channels.filter(channel => 
        channel.channel_number?.toString().includes(query) ||
        channel.name?.toLowerCase().includes(query)
      );
    }

    // Apply sorting
    return filteredChannels.sort((a, b) => {
      let aValue, bValue;

      switch (orderBy) {
        case 'channel_number':
          aValue = a.channel_number || 0;
          bValue = b.channel_number || 0;
          break;
        case 'name':
          aValue = a.name?.toLowerCase() || '';
          bValue = b.name?.toLowerCase() || '';
          break;
        case 'patterns':
          aValue = patterns.patterns?.[a.id]?.regex?.length || 0;
          bValue = patterns.patterns?.[b.id]?.regex?.length || 0;
          break;
        case 'status':
          aValue = patterns.patterns?.[a.id]?.enabled !== false ? 1 : 0;
          bValue = patterns.patterns?.[b.id]?.enabled !== false ? 1 : 0;
          break;
        default:
          return 0;
      }

      if (aValue < bValue) {
        return order === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return order === 'asc' ? 1 : -1;
      }
      return 0;
    });
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Channel Configuration
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

      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Regex Patterns for Automatic Stream Assignment
          </Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            Configure regex patterns to automatically assign new streams to channels based on stream names.
          </Typography>

          {/* Search Field */}
          <Box sx={{ mb: 2 }}>
            <TextField
              placeholder="Search by channel number or name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              size="small"
              fullWidth
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Box>

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell sortDirection={orderBy === 'channel_number' ? order : false}>
                    <TableSortLabel
                      active={orderBy === 'channel_number'}
                      direction={orderBy === 'channel_number' ? order : 'asc'}
                      onClick={() => handleRequestSort('channel_number')}
                    >
                      Channel Number
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sortDirection={orderBy === 'name' ? order : false}>
                    <TableSortLabel
                      active={orderBy === 'name'}
                      direction={orderBy === 'name' ? order : 'asc'}
                      onClick={() => handleRequestSort('name')}
                    >
                      Channel Name
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sortDirection={orderBy === 'patterns' ? order : false}>
                    <TableSortLabel
                      active={orderBy === 'patterns'}
                      direction={orderBy === 'patterns' ? order : 'asc'}
                      onClick={() => handleRequestSort('patterns')}
                    >
                      Patterns
                    </TableSortLabel>
                  </TableCell>
                  <TableCell sortDirection={orderBy === 'status' ? order : false}>
                    <TableSortLabel
                      active={orderBy === 'status'}
                      direction={orderBy === 'status' ? order : 'asc'}
                      onClick={() => handleRequestSort('status')}
                    >
                      Status
                    </TableSortLabel>
                  </TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {getFilteredAndSortedChannels().map((channel) => {
                  const pattern = patterns.patterns?.[channel.id];
                  return (
                    <TableRow key={channel.id}>
                      <TableCell>
                        <Typography variant="body2">
                          #{channel.channel_number}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {channel.name}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {pattern?.regex ? (
                          pattern.regex.map((regex, index) => (
                            <Chip key={index} label={regex} size="small" sx={{ mr: 1, mb: 1 }} />
                          ))
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            No patterns configured
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={pattern?.enabled !== false ? 'Enabled' : 'Disabled'}
                          color={pattern?.enabled !== false ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <IconButton
                          onClick={() => handleOpenDialog(channel)}
                          size="small"
                        >
                          {pattern ? <EditIcon /> : <AddIcon />}
                        </IconButton>
                        {pattern && (
                          <IconButton
                            onClick={() => handleDeletePattern(channel.id)}
                            size="small"
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Pattern Edit Dialog */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingPattern ? 'Edit Pattern' : 'Add Pattern'}
        </DialogTitle>
        <DialogContent>
          <TextField
            label="Channel ID"
            value={formData.channel_id}
            onChange={(e) => setFormData(prev => ({ ...prev, channel_id: e.target.value }))}
            fullWidth
            margin="normal"
            disabled={!!editingPattern}
          />
          <TextField
            label="Channel Name"
            value={formData.name}
            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
            fullWidth
            margin="normal"
          />
          
          <Typography variant="h6" sx={{ mt: 2, mb: 1 }}>
            Regex Patterns
          </Typography>
          
          {formData.regex.map((regex, index) => (
            <Box key={index} display="flex" alignItems="center" gap={1} mb={1}>
              <TextField
                label={`Pattern ${index + 1}`}
                value={regex}
                onChange={(e) => updateRegexField(index, e.target.value)}
                fullWidth
                placeholder="e.g., .*CNN.*|.*News.*"
              />
              {formData.regex.length > 1 && (
                <IconButton onClick={() => removeRegexField(index)} color="error">
                  <DeleteIcon />
                </IconButton>
              )}
            </Box>
          ))}
          
          <Button onClick={addRegexField} startIcon={<AddIcon />} sx={{ mt: 1 }}>
            Add Pattern
          </Button>
          
          <Box sx={{ mt: 2, mb: 2 }}>
            <Button 
              onClick={handleTestPattern} 
              variant="outlined" 
              disabled={testingPattern || formData.regex.every(r => !r.trim())}
              fullWidth
            >
              {testingPattern ? 'Testing...' : 'Test Patterns Against Live Streams'}
            </Button>
          </Box>
          
          {testResults && testResults.results && testResults.results[0] && (
            <Box sx={{ mt: 2, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                Test Results: {testResults.results[0].match_count} matches found (out of {testResults.total_streams} total streams)
              </Typography>
              
              {testResults.results[0].matched_streams.length > 0 && (
                <Box sx={{ maxHeight: 200, overflow: 'auto', mt: 1 }}>
                  {testResults.results[0].matched_streams.slice(0, 10).map((stream, idx) => (
                    <Box key={idx} sx={{ py: 0.5, borderBottom: '1px solid', borderColor: 'divider' }}>
                      <Typography variant="body2">
                        {stream.stream_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        Matched by: {stream.matched_pattern}
                      </Typography>
                    </Box>
                  ))}
                  {testResults.results[0].matched_streams.length > 10 && (
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      ... and {testResults.results[0].matched_streams.length - 10} more
                    </Typography>
                  )}
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>Cancel</Button>
          <Button onClick={handleSavePattern} variant="contained">
            Save
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default ChannelConfiguration;