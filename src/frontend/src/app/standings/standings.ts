import { httpResource } from '@angular/common/http';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

import { parseRecords, PlayerRecord, RECORDS_URL } from '../player-record';
import { StandingsTable } from './standings-table';

@Component({
  selector: 'app-standings',
  imports: [RouterLink, StandingsTable],
  templateUrl: './standings.html',
  styleUrl: './standings.css',
})
export class Standings {
  protected readonly records = httpResource<PlayerRecord[]>(() => RECORDS_URL, {
    parse: parseRecords,
    defaultValue: [],
  });
}
