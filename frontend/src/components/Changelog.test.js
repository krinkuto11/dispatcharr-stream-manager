import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Changelog from './Changelog';
import { changelogAPI } from '../services/api';

// Mock the API
jest.mock('../services/api', () => ({
  changelogAPI: {
    getChangelog: jest.fn(),
  },
}));

// Mock axios
jest.mock('axios', () => ({
  get: jest.fn(),
}));

describe('Changelog Component', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    jest.clearAllMocks();
    // Clear localStorage
    localStorage.clear();
  });

  test('renders without infinite re-renders', async () => {
    // Mock the changelog API to return empty data
    changelogAPI.getChangelog.mockResolvedValue({ data: [] });

    // Track how many times the component renders
    let renderCount = 0;
    const OriginalChangelog = Changelog;
    
    // This test ensures the component doesn't cause infinite re-renders
    // which would result in React error #31
    const { rerender } = render(<OriginalChangelog />);
    
    // Wait for the loading state to complete
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    }, { timeout: 3000 });

    // Verify the API was called only once (not infinite times)
    expect(changelogAPI.getChangelog).toHaveBeenCalledTimes(1);
  });

  test('loads and displays changelog without errors', async () => {
    const mockChangelogData = [
      {
        action: 'playlist_refresh',
        timestamp: '2025-10-16T12:00:00Z',
        details: {
          success: true,
          total_streams: 100,
          added_streams: [],
          removed_streams: []
        }
      }
    ];

    changelogAPI.getChangelog.mockResolvedValue({ data: mockChangelogData });

    render(<Changelog />);

    // Wait for loading to complete
    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    // Verify content is displayed
    expect(screen.getByText('Changelog')).toBeInTheDocument();
    expect(screen.getByText(/Playlist Refresh/i)).toBeInTheDocument();
  });

  test('handles empty changelog gracefully', async () => {
    changelogAPI.getChangelog.mockResolvedValue({ data: [] });

    render(<Changelog />);

    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    expect(screen.getByText(/No changelog entries found/i)).toBeInTheDocument();
  });

  test('does not recreate callbacks on days change', async () => {
    changelogAPI.getChangelog.mockResolvedValue({ data: [] });

    const { rerender } = render(<Changelog />);

    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    const initialCallCount = changelogAPI.getChangelog.mock.calls.length;

    // Force a re-render
    rerender(<Changelog />);

    // API should not be called again just from re-rendering
    // It should only be called when days changes via user interaction
    expect(changelogAPI.getChangelog.mock.calls.length).toBe(initialCallCount);
  });

  test('handles playlist_refresh action with streams having {id, name} format', async () => {
    const mockChangelogData = [
      {
        action: 'playlist_refresh',
        timestamp: '2025-10-16T12:00:00Z',
        details: {
          success: true,
          total_streams: 102,
          added_streams: [
            { id: 1, name: 'Stream 1' },
            { id: 2, name: 'Stream 2' }
          ],
          removed_streams: [
            { id: 3, name: 'Stream 3' }
          ]
        }
      }
    ];

    changelogAPI.getChangelog.mockResolvedValue({ data: mockChangelogData });

    render(<Changelog />);

    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    // Verify that stream names are displayed correctly without React errors
    expect(screen.getByText('Stream 1')).toBeInTheDocument();
    expect(screen.getByText('Stream 2')).toBeInTheDocument();
    expect(screen.getByText('Stream 3')).toBeInTheDocument();
  });

  test('handles streams_assigned action with streams having {stream_id, stream_name} format', async () => {
    const mockChangelogData = [
      {
        action: 'streams_assigned',
        timestamp: '2025-10-16T12:00:00Z',
        details: {
          total_assigned: 5,
          channel_count: 1,
          assignments: [
            {
              channel_id: 100,
              channel_name: 'Test Channel',
              stream_count: 5,
              streams: [
                { stream_id: 1, stream_name: 'Assigned Stream 1' },
                { stream_id: 2, stream_name: 'Assigned Stream 2' }
              ]
            }
          ]
        }
      }
    ];

    changelogAPI.getChangelog.mockResolvedValue({ data: mockChangelogData });

    render(<Changelog />);

    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    // Verify that stream names are displayed correctly
    expect(screen.getByText('Assigned Stream 1')).toBeInTheDocument();
    expect(screen.getByText('Assigned Stream 2')).toBeInTheDocument();
  });

  test('displays pagination when there are more than 10 entries', async () => {
    // Create 15 mock changelog entries
    const mockChangelogData = Array.from({ length: 15 }, (_, i) => ({
      action: 'playlist_refresh',
      timestamp: `2025-10-16T${String(i).padStart(2, '0')}:00:00Z`,
      details: {
        success: true,
        total_streams: 100 + i,
        added_streams: [],
        removed_streams: []
      }
    }));

    changelogAPI.getChangelog.mockResolvedValue({ data: mockChangelogData });

    render(<Changelog />);

    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    // Verify pagination is displayed
    const pagination = screen.getByRole('navigation');
    expect(pagination).toBeInTheDocument();
  });

  test('hides pagination when there are 10 or fewer entries', async () => {
    const mockChangelogData = Array.from({ length: 5 }, (_, i) => ({
      action: 'playlist_refresh',
      timestamp: `2025-10-16T${String(i).padStart(2, '0')}:00:00Z`,
      details: {
        success: true,
        total_streams: 100 + i,
        added_streams: [],
        removed_streams: []
      }
    }));

    changelogAPI.getChangelog.mockResolvedValue({ data: mockChangelogData });

    render(<Changelog />);

    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    });

    // Verify pagination is not displayed
    const pagination = screen.queryByRole('navigation');
    expect(pagination).not.toBeInTheDocument();
  });
});
