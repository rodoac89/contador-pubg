import { HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { session } from '../session';

@Component({
  selector: 'app-admin',
  imports: [RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './admin.html',
  styleUrl: './admin.css',
})
export class Admin {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  protected readonly username = signal(session.username() ?? '');

  protected logout(): void {
    this.http.post('/api/user/logout/', {}).subscribe({
      next: () => this.leave(),
      error: () => this.leave(),
    });
  }

  private leave(): void {
    session.clear();
    void this.router.navigateByUrl('/admin/entrar');
  }
}
