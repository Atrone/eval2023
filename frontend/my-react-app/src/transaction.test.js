import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/extend-expect';
import BitcoinTransaction from './path-to-your-BitcoinTransaction-file';  // adjust the path accordingly

global.fetch = jest.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve({ success: true, data: [{ address: 'testAddress' }] }),
  })
);

describe('BitcoinTransaction Component', () => {

  beforeEach(() => {
    fetch.mockClear();
  });

  it('renders without crashing', () => {
    render(<BitcoinTransaction />);
  });

  it('fetches address options when rendered', async () => {
    render(<BitcoinTransaction />);
    expect(fetch).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(screen.getByText('testAddress')).toBeInTheDocument());
  });

  it('updates toAddress state on To Address selection', async () => {
    render(<BitcoinTransaction />);
    fireEvent.change(screen.getByPlaceholderText('To Address'), { target: { value: 'testAddress' } });
    await waitFor(() => expect(screen.getByPlaceholderText('To Address').value).toBe('testAddress'));
  });


});

