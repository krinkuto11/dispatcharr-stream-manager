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
});
