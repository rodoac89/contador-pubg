import { HttpErrorResponse } from '@angular/common/http';

const TOKEN_KEY = 'contador.token';
const USER_KEY = 'contador.username';
const PLAYER_KEY = 'contador.player';

export interface Session {
  token: string;
  id: number;
  username: string;
  email: string;
}

export const session = {
  token(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  username(): string | null {
    return localStorage.getItem(USER_KEY);
  },

  playerName(): string {
    return localStorage.getItem(PLAYER_KEY) ?? '';
  },

  save(value: Session): void {
    localStorage.setItem(TOKEN_KEY, value.token);
    localStorage.setItem(USER_KEY, value.username);
  },

  savePlayer(name: string): void {
    localStorage.setItem(PLAYER_KEY, name);
  },

  clear(): void {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

export function errorDetail(error: unknown, fallback: string): string {
  if (error instanceof HttpErrorResponse) {
    const detail = error.error?.detail;
    if (typeof detail === 'string' && detail.length > 0) {
      return detail;
    }
  }
  return fallback;
}
