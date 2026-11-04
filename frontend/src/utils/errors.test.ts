import { describe, expect, it } from 'vitest';
import { getErrorMessage } from './errors';

describe('getErrorMessage', () => {
  it('prefers the API detail field of an axios-style error', () => {
    const error = { message: 'Request failed', response: { data: { detail: 'Invalid credentials' } } };
    expect(getErrorMessage(error, 'fallback')).toBe('Invalid credentials');
  });

  it('falls back to the error message when no detail is present', () => {
    expect(getErrorMessage(new Error('Network Error'), 'fallback')).toBe('Network Error');
  });

  it('returns plain string errors as they are', () => {
    expect(getErrorMessage('boom', 'fallback')).toBe('boom');
  });

  it('ignores non-string detail values', () => {
    const error = { response: { data: { detail: [{ msg: 'field required' }] } } };
    expect(getErrorMessage(error, 'fallback')).toBe('fallback');
  });

  it('uses the fallback for null, undefined and empty values', () => {
    expect(getErrorMessage(null, 'fallback')).toBe('fallback');
    expect(getErrorMessage(undefined, 'fallback')).toBe('fallback');
    expect(getErrorMessage({ message: '' }, 'fallback')).toBe('fallback');
  });
});
