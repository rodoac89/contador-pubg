import { httpResource, HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';

import { errorDetail, session, Session } from '../session';

interface Setup {
  registrationOpen: boolean;
}

@Component({
  selector: 'app-admin-gate',
  imports: [RouterLink],
  templateUrl: './admin-gate.html',
  styleUrl: './admin.css',
})
export class AdminGate {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  protected readonly username = signal('');
  protected readonly password = signal('');
  protected readonly confirm = signal('');
  protected readonly busy = signal(false);
  protected readonly error = signal('');

  protected readonly setup = httpResource<Setup>(() => '/api/user/setup/', {
    parse: parseSetup,
    defaultValue: { registrationOpen: false },
  });

  constructor() {
    if (session.token()) {
      void this.router.navigateByUrl('/admin');
    }
  }

  protected onUsername(event: Event): void {
    this.username.set(readInput(event));
  }

  protected onPassword(event: Event): void {
    this.password.set(readInput(event));
  }

  protected onConfirm(event: Event): void {
    this.confirm.set(readInput(event));
  }

  protected submit(event: Event): void {
    event.preventDefault();
    if (this.busy()) {
      return;
    }
    const username = this.username().trim();
    const password = this.password();
    const registrationOpen = this.setup.value()?.registrationOpen === true;
    if (!username || !password) {
      this.error.set('Usuario y contraseña son obligatorios.');
      return;
    }
    if (registrationOpen && password !== this.confirm()) {
      this.error.set('Las contraseñas no coinciden.');
      return;
    }

    this.busy.set(true);
    this.error.set('');
    const url = registrationOpen ? '/api/user/register/' : '/api/user/login/';
    this.http.post<Session>(url, { username, password }).subscribe({
      next: (value) => {
        session.save(value);
        void this.router.navigateByUrl('/admin');
      },
      error: (error: unknown) => {
        this.busy.set(false);
        this.error.set(errorDetail(error, 'No se pudo entrar.'));
      },
    });
  }
}

function parseSetup(value: unknown): Setup {
  if (value === null || typeof value !== 'object' || !('registrationOpen' in value)) {
    throw new Error('No se pudo leer el estado del registro.');
  }
  return { registrationOpen: Boolean((value as { registrationOpen: unknown }).registrationOpen) };
}

function readInput(event: Event): string {
  const input = event.target;
  return input instanceof HTMLInputElement ? input.value : '';
}
