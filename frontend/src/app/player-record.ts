export const RECORDS_URL = '/api/match/records/';

export interface PlayerRecord {
  player: string;
  matches: number;
  kills: number;
  wins: number;
  zoneDeaths: number;
  score: number;
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
    };
  });
}
