import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { session } from './session';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = session.token();
  const authed =
    token && needsAuth(req.url)
      ? req.clone({ setHeaders: { Authorization: `Token ${token}` } })
      : req;

  return next(authed).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse && error.status === 401 && needsAuth(req.url)) {
        session.clear();
        void inject(Router).navigateByUrl('/admin/entrar');
      }
      return throwError(() => error);
    }),
  );
};

function needsAuth(url: string): boolean {
  if (!url.startsWith('/api/')) {
    return false;
  }
  if (url.startsWith('/api/match/records') || url.startsWith('/api/health')) {
    return false;
  }
  if (
    url.startsWith('/api/user/setup') ||
    url.startsWith('/api/user/register') ||
    url.startsWith('/api/user/login')
  ) {
    return false;
  }
  return true;
}
