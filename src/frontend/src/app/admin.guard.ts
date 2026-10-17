import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { session } from './session';

export const adminGuard: CanActivateFn = () => {
  if (session.token()) {
    return true;
  }
  return inject(Router).createUrlTree(['/admin/entrar']);
};
