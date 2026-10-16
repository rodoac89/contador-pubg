import { httpResource } from '@angular/common/http';
import { Component } from '@angular/core';

import { parseRecords, PlayerRecord, RECORDS_URL } from '../player-record';

@Component({
  selector: 'app-standings',
  templateUrl: './standings.html',
  styleUrl: './standings.css',
})
export class Standings {
  protected readonly records = httpResource<PlayerRecord[]>(() => RECORDS_URL, {
    parse: parseRecords,
    defaultValue: [],
  });
}
