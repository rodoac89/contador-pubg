import { Routes } from '@angular/router';

import { Admin } from './admin/admin';
import { AdminGate } from './admin/admin-gate';
import { LoadMatches } from './admin/load-matches';
import { MatchAdmin } from './admin/match-admin';
import { adminGuard } from './admin.guard';
import { Matches } from './matches/matches';
import { PlayerMatches } from './player/player-matches';
import { Standings } from './standings/standings';

export const routes: Routes = [
  { path: '', component: Standings },
  { path: 'partidas', component: Matches },
  { path: 'jugador/:player', component: PlayerMatches },
  { path: 'admin/entrar', component: AdminGate },
  {
    path: 'admin',
    component: Admin,
    canActivate: [adminGuard],
    children: [
      { path: '', pathMatch: 'full', redirectTo: 'cargar' },
      { path: 'cargar', component: LoadMatches },
      { path: 'partidas', component: MatchAdmin },
    ],
  },
];
