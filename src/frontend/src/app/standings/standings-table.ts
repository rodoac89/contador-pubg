import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { formatDamage, PlayerRecord } from '../player-record';

@Component({
  selector: 'app-standings-table',
  imports: [RouterLink],
  templateUrl: './standings-table.html',
  styleUrl: './standings-table.css',
})
export class StandingsTable {
  readonly rows = input.required<PlayerRecord[]>();
  readonly caption = input('Puntaje y daño acumulados de las partidas que cuentan');

  protected readonly formatDamage = formatDamage;
}
