import { HttpErrorResponse, httpResource } from '@angular/common/http';
import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { map } from 'rxjs';

import {
  formatDamage,
  parsePlayerHistory,
  PlayerHistory,
  PlayerMatch,
  playerHistoryUrl,
} from '../player-record';

@Component({
  selector: 'app-player-matches',
  imports: [RouterLink],
  templateUrl: './player-matches.html',
  styleUrl: './player-matches.css',
})
export class PlayerMatches {
  private readonly route = inject(ActivatedRoute);

  protected readonly playerName = toSignal(
    this.route.paramMap.pipe(map((params) => params.get('player') ?? '')),
    { initialValue: this.route.snapshot.paramMap.get('player') ?? '' },
  );

  protected readonly history = httpResource<PlayerHistory | null>(
    () => {
      const name = this.playerName();
      return name ? playerHistoryUrl(name) : undefined;
    },
    { parse: parsePlayerHistory, defaultValue: null },
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

  protected formatDamage(value: number): string {
    return formatDamage(value);
  }

  protected matches(): PlayerMatch[] | null {
    if (this.history.status() !== 'resolved') {
      return null;
    }
    const history = this.history.value();
    return history ? history.matches : [];
  }

  protected notFound(): boolean {
    const error = this.history.error();
    return error instanceof HttpErrorResponse && error.status === 404;
  }
}
