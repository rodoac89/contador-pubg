import { HttpClient, httpResource } from '@angular/common/http';
import { Component, computed, inject, signal } from '@angular/core';
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

interface MatchDay {
  key: string;
  label: string;
  matches: MatchBoard[];
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

  protected readonly days = computed(() => groupByDate(this.boards.value()));

  protected formatDate(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return dateTimeFormat.format(date);
  }

  protected formatTime(value: string): string {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return value;
    }
    return timeFormat.format(date);
  }

  protected matchCount(count: number): string {
    return count === 1 ? '1 partida' : `${count} partidas`;
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

const dateTimeFormat = new Intl.DateTimeFormat('es-CL', {
  dateStyle: 'short',
  timeStyle: 'short',
});

const timeFormat = new Intl.DateTimeFormat('es-CL', {
  timeStyle: 'short',
});

const dayFormat = new Intl.DateTimeFormat('es-CL', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
  year: 'numeric',
});

function groupByDate(matches: MatchBoard[]): MatchDay[] {
  const groups: MatchDay[] = [];
  const byDay = new Map<string, MatchDay>();
  for (const match of matches) {
    const date = new Date(match.createdAt);
    const valid = !Number.isNaN(date.getTime());
    const key = valid ? localDayKey(date) : match.createdAt;
    let group = byDay.get(key);
    if (!group) {
      group = {
        key,
        label: valid ? dayFormat.format(date) : match.createdAt,
        matches: [],
      };
      byDay.set(key, group);
      groups.push(group);
    }
    group.matches.push(match);
  }
  return groups;
}

function localDayKey(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${date.getFullYear()}-${month}-${day}`;
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
