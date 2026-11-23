import { createContext, useContext, useState, type ReactNode } from 'react';

export interface AuthUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const isLoading = false;

  // shortcut: mock auth in memory, replace with POST /api/v1/auth/token/ + GET /api/v1/auth/me/ when backend auth is ready
  const login = async (email: string, _password: string) => {
    setUser({
      id: '00000000-0000-0000-0000-000000000001',
      email,
      first_name: 'Dev',
      last_name: 'User',
    });
  };

  const logout = () => {
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: user !== null,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return ctx;
}
