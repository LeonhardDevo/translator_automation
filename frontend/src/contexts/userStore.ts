import { createContext } from 'react';
import type { Dispatch } from 'react';

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  role: string;
}

export interface Usage {
  current_usage: number;
  limit: number;
  remaining: number;
  reset_date: string;
}

export interface UserState {
  user: User | null;
  usage: Usage | null;
}

export type Action =
  | { type: 'SET_USER'; payload: User | null }
  | { type: 'SET_USAGE'; payload: Usage | null }
  | { type: 'UPDATE_TRANSLATION_COUNT' }
  | { type: 'LOGOUT' };

export const initialState: UserState = {
  user: null,
  usage: null,
};

export const userReducer = (state: UserState, action: Action): UserState => {
  switch (action.type) {
    case 'SET_USER':
      return { ...state, user: action.payload };
    case 'SET_USAGE':
      return { ...state, usage: action.payload };
    case 'UPDATE_TRANSLATION_COUNT':
      if (state.usage) {
        return {
          ...state,
          usage: {
            ...state.usage,
            current_usage: state.usage.current_usage + 1,
            remaining: Math.max(0, state.usage.limit - (state.usage.current_usage + 1)),
          },
        };
      }
      return state;
    case 'LOGOUT':
      localStorage.removeItem('token');
      sessionStorage.removeItem('token');
      return { user: null, usage: null };
    default:
      return state;
  }
};

export const UserContext = createContext<{
  state: UserState;
  dispatch: Dispatch<Action>;
}>({
  state: initialState,
  dispatch: () => { },
});
