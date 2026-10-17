import { httpResource, HttpClient } from '@angular/common/http';
import { Component, inject, signal } from '@angular/core';

import { errorDetail } from '../session';

export interface AdminMatch {
  matchId: string;
  mapName: string;
  createdAt: string;
  training: boolean;
  participantCount: number;
}

export interface Participant {
  player: string;
  place: number;
  kills: number;
  assists: number;
  damage: number;
  timeSurvived: number;
  death: string;
}

export interface MatchDetail {
  matchId: string;
  mapName: string;
  createdAt: string;
  training: boolean;
  participants: Participant[];
}

@Component({
  selector: 'app-match-admin',
  templateUrl: './match-admin.html',
  styleUrl: './admin.css',
})
export class MatchAdmin {
  private readonly http = inject(HttpClient);

  protected readonly selectedId = signal<string | null>(null);
  protected readonly error = signal('');
  protected readonly savingId = signal<string | null>(null);

  protected readonly matches = httpResource<AdminMatch[]>(() => '/api/match/', {
    parse: parseMatches,
    defaultValue: [],
  });

  protected readonly detail = httpResource<MatchDetail | null>(
    () => {
      const id = this.selectedId();
      return id ? `/api/match/${id}/` : undefined;
    },
    { parse: parseDetail, defaultValue: null },
  );

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

  protected select(matchId: string): void {
    this.error.set('');
    this.selectedId.set(this.selectedId() === matchId ? null : matchId);
  }

  protected onTraining(match: AdminMatch, event: Event): void {
    const input = event.target;
    if (!(input instanceof HTMLInputElement) || this.savingId()) {
      return;
    }
    this.savingId.set(match.matchId);
    this.error.set('');
    this.http.patch(`/api/match/${match.matchId}/`, { training: input.checked }).subscribe({
      next: () => {
        this.savingId.set(null);
        this.matches.reload();
        if (this.selectedId() === match.matchId) {
          this.detail.reload();
        }
      },
      error: (error: unknown) => {
        this.savingId.set(null);
        input.checked = match.training;
        this.error.set(errorDetail(error, 'No se pudo actualizar la partida.'));
      },
    });
  }
}

function parseMatches(value: unknown): AdminMatch[] {
  if (!Array.isArray(value)) {
    throw new Error('La respuesta no es una lista de partidas.');
  }
  return value.map((entry) => {
    if (entry === null || typeof entry !== 'object') {
      throw new Error('Partida inválida.');
    }
    const row = entry as Record<string, unknown>;
    return {
      matchId: text(row, 'matchId'),
      mapName: text(row, 'mapName'),
      createdAt: text(row, 'createdAt'),
      training: row['training'] === true,
      participantCount: numberField(row, 'participantCount'),
    };
  });
}

function parseDetail(value: unknown): MatchDetail {
  if (value === null || typeof value !== 'object') {
    throw new Error('La partida no es válida.');
  }
  const row = value as Record<string, unknown>;
  const participants = row['participants'];
  if (!Array.isArray(participants)) {
    throw new Error('La partida no trae participantes.');
  }
  return {
    matchId: text(row, 'matchId'),
    mapName: text(row, 'mapName'),
    createdAt: text(row, 'createdAt'),
    training: row['training'] === true,
    participants: participants.map((entry) => {
      if (entry === null || typeof entry !== 'object') {
        throw new Error('Participante inválido.');
      }
      const person = entry as Record<string, unknown>;
      return {
        player: text(person, 'player'),
        place: numberField(person, 'place'),
        kills: numberField(person, 'kills'),
        assists: numberField(person, 'assists'),
        damage: numberField(person, 'damage'),
        timeSurvived: numberField(person, 'timeSurvived'),
        death: text(person, 'death'),
      };
    }),
  };
}

function text(row: Record<string, unknown>, key: string): string {
  const value = row[key];
  if (typeof value !== 'string') {
    throw new Error(`Campo ${key} inválido`);
  }
  return value;
}

function numberField(row: Record<string, unknown>, key: string): number {
  const value = row[key];
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new Error(`Campo ${key} inválido`);
  }
  return value;
}
