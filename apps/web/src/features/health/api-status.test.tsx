import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ApiStatus } from './api-status';

describe('ApiStatus', () => {
  it('tells the user the API is reachable', () => {
    render(<ApiStatus status="success" />);

    expect(screen.getByText('API is up')).toBeInTheDocument();
  });

  it('tells the user the API is down', () => {
    render(<ApiStatus status="error" />);

    expect(screen.getByText('API is down')).toBeInTheDocument();
  });
});
