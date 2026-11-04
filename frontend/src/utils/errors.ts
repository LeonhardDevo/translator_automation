interface ErrorLike {
  message?: unknown;
  response?: { data?: { detail?: unknown } | null } | null;
}

export const getErrorMessage = (error: unknown, fallback: string): string => {
  if (typeof error === 'string' && error) {
    return error;
  }
  if (typeof error === 'object' && error !== null) {
    const { message, response } = error as ErrorLike;
    const detail = response?.data?.detail;
    if (typeof detail === 'string' && detail) {
      return detail;
    }
    if (typeof message === 'string' && message) {
      return message;
    }
  }
  return fallback;
};
