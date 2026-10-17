export const RECORDS_URL = '/api/match/records/';

export interface PlayerRecord {
  player: string;
  matches: number;
  kills: number;
  wins: number;
  zoneDeaths: number;
  score: number;
  damage: number;
}

export interface PlayerMatch {
  matchId: string;
  mapName: string;
  createdAt: string;
  training: boolean;
  points: number;
  zoneDeath: boolean;
  damage: number;
}

export interface PlayerHistory {
  player: string;
  matches: PlayerMatch[];
}

export function playerHistoryUrl(player: string): string {
  return `/api/match/records/${encodeURIComponent(player)}/`;
}

export function formatDamage(value: number): string {
  return new Intl.NumberFormat('es-CL', { maximumFractionDigits: 1 }).format(value);
}

function numberField(row: Record<string, unknown>, key: string): number {
  const value = row[key];
  if (typeof value !== 'number' || !Number.isFinite(value)) {
    throw new Error(`Campo ${key} inválido`);
  }
  return value;
}

export function parseRecords(value: unknown): PlayerRecord[] {
  if (!Array.isArray(value)) {
    throw new Error('La respuesta no es una tabla de posiciones.');
  }

  return value.map((entry) => {
    if (entry === null || typeof entry !== 'object') {
      throw new Error('Fila inválida.');
    }

    const row = entry as Record<string, unknown>;
    const player = row['player'];
    if (typeof player !== 'string' || player.length === 0) {
      throw new Error('Jugador inválido.');
    }

    return {
      player,
      matches: numberField(row, 'matches'),
      kills: numberField(row, 'kills'),
      wins: numberField(row, 'wins'),
      zoneDeaths: numberField(row, 'zoneDeaths'),
      score: numberField(row, 'score'),
      damage: numberField(row, 'damage'),
    };
  });
}

export function parsePlayerHistory(value: unknown): PlayerHistory {
  if (value === null || typeof value !== 'object') {
    throw new Error('La respuesta no es el historial del jugador.');
  }

  const body = value as Record<string, unknown>;
  const player = body['player'];
  const matches = body['matches'];
  if (typeof player !== 'string' || player.length === 0) {
    throw new Error('Jugador inválido.');
  }
  if (!Array.isArray(matches)) {
    throw new Error('La respuesta no trae partidas.');
  }

  return {
    player,
    matches: matches.map((entry) => {
      if (entry === null || typeof entry !== 'object') {
        throw new Error('Partida inválida.');
      }
      const row = entry as Record<string, unknown>;
      return {
        matchId: textField(row, 'matchId'),
        mapName: textField(row, 'mapName'),
        createdAt: textField(row, 'createdAt'),
        training: booleanField(row, 'training'),
        points: numberField(row, 'points'),
        zoneDeath: booleanField(row, 'zoneDeath'),
        damage: numberField(row, 'damage'),
      };
    }),
  };
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
