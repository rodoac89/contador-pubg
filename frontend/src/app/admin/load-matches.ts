import { HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';

import { errorDetail, session } from '../session';

interface LoadResult {
  saved: number;
  matches: string[];
}

@Component({
  selector: 'app-load-matches',
  templateUrl: './load-matches.html',
  styleUrl: './admin.css',
})
export class LoadMatches {
  private readonly http = inject(HttpClient);

  protected readonly asking = signal(false);
  protected readonly bulk = signal(false);
  protected readonly playerName = signal(session.playerName());
  protected readonly busy = signal(false);
  protected readonly error = signal('');
  protected readonly message = signal('');

  protected onPlayer(event: Event): void {
    const input = event.target;
    this.playerName.set(input instanceof HTMLInputElement ? input.value : '');
  }

  protected chooseLatest(): void {
    this.bulk.set(false);
    this.asking.set(true);
    this.error.set('');
    this.message.set('');
  }

  protected chooseBulk(): void {
    this.bulk.set(true);
    this.error.set('');
    this.message.set('');
    if (!this.playerName().trim()) {
      this.asking.set(true);
      this.error.set('Ingresa el usuario para traer las partidas.');
      return;
    }
    this.send();
  }

  protected submit(event: Event): void {
    event.preventDefault();
    this.send();
  }

  private send(): void {
    const playerName = this.playerName().trim();
    if (!playerName) {
      this.asking.set(true);
      this.error.set('Ingresa el usuario para traer las partidas.');
      return;
    }
    if (this.busy()) {
      return;
    }

    session.savePlayer(playerName);
    this.busy.set(true);
    this.error.set('');
    this.message.set('');
    const url = this.bulk() ? '/api/match/load/?bulk=true' : '/api/match/load/';
    this.http.post<LoadResult>(url, { player_name: playerName }).subscribe({
      next: (result) => {
        this.busy.set(false);
        this.asking.set(false);
        this.message.set(
          result.saved === 0
            ? 'No se encontraron partidas custom para ese usuario.'
            : `Se guardaron ${result.saved} partidas.`,
        );
      },
      error: (error: unknown) => {
        this.busy.set(false);
        this.error.set(errorDetail(error, 'No se pudieron traer las partidas.'));
      },
    });
  }
}
