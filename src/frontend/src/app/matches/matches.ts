import { HttpClient, httpResource } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { errorDetail, session } from '../session';
import { parseRecords, PlayerRecord } from '../player-record';
import { StandingsTable } from '../standings/standings-table';

export interface MatchBoard {
  matchId: string;
  mapName: string;
  createdAt: string;
  training: boolean;
  rows: PlayerRecord[];
}

@Component({
  selector: 'app-matches',
  imports: [RouterLink, StandingsTable],
  templateUrl: './matches.html',
  styleUrl: './matches.css',
})
export class Matches {
  private readonly http = inject(HttpClient);

  protected readonly signedIn = session.token() !== null;
  protected readonly confirming = signal<string | null>(null);
  protected readonly deleting = signal<string | null>(null);
  protected readonly actionError = signal('');

  protected readonly boards = httpResource<MatchBoard[]>(() => '/api/match/board/', {
    parse: parseBoards,
    defaultValue: [],
  });

  protected formatDate(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return new Intl.DateTimeFormat('es-CL', {
      dateStyle: 'short',
      timeStyle: 'short',
    }).format(date);
  }

  protected caption(match: MatchBoard): string {
    const when = this.formatDate(match.createdAt);
    const kind = match.training ? ', calentamiento' : '';
    return `${match.mapName} del ${when}${kind}`;
  }

  protected ask(matchId: string): void {
    this.actionError.set('');
    this.confirming.set(matchId);
  }

  protected cancel(): void {
    this.confirming.set(null);
  }

  protected discard(match: MatchBoard): void {
    this.deleting.set(match.matchId);
    this.actionError.set('');
    this.http.delete(`/api/match/${match.matchId}/`).subscribe({
      next: () => {
        this.confirming.set(null);
        this.deleting.set(null);
        this.boards.reload();
      },
      error: (error: unknown) => {
        this.deleting.set(null);
        this.actionError.set(errorDetail(error, 'No se pudo quitar la partida.'));
      },
    });
  }
}

function parseBoards(value: unknown): MatchBoard[] {
  if (!Array.isArray(value)) {
    throw new Error('La respuesta no es la lista de partidas.');
  }
  return value.map((entry) => {
    if (entry === null || typeof entry !== 'object') {
      throw new Error('Partida inválida.');
    }
    const row = entry as Record<string, unknown>;
    return {
      matchId: textField(row, 'matchId'),
      mapName: textField(row, 'mapName'),
      createdAt: textField(row, 'createdAt'),
      training: booleanField(row, 'training'),
      rows: parseRecords(row['rows']),
    };
  });
}

function textField(row: Record<string, unknown>, key: string): string {
  const value = row[key];
  if (typeof value !== 'string') {
    throw new Error(`Campo ${key} inválido`);
  }
  return value;
}

function booleanField(row: Record<string, unknown>, key: string): boolean {
  const value = row[key];
  if (typeof value !== 'boolean') {
    throw new Error(`Campo ${key} inválido`);
  }
  return value;
}
