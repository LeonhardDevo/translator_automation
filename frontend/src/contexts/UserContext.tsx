import React, { createContext, useContext, useReducer } from 'react';

interface User {
  id: number;
  email: string;
  is_active: boolean;
  role: string;  // 'user' or 'admin'
}

interface Usage {
  current_usage: number;
  limit: number;
  remaining: number;
  reset_date: string;
}

interface UserState {
  user: User | null;
  usage: Usage | null;
}

interface Action {
  type: string;
  payload?: any;
}

const initialState: UserState = {
  user: null,
  usage: null,
};

const userReducer = (state: UserState, action: Action): UserState => {
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

const UserContext = createContext<{
  state: UserState;
  dispatch: React.Dispatch<Action>;
}>({
  state: initialState,
  dispatch: () => { },
});

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(userReducer, initialState);

  return (
    <UserContext.Provider value={{ state, dispatch }}>
      {children}
    </UserContext.Provider>
  );
};

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) {
    throw new Error('useUser must be used within a UserProvider');
  }
  return context;
};