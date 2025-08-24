/* Copyright (c) Stichting Mathematisch Centrum, Amsterdam, 1985. */
/* hack.track.c - version 1.0.2 */
/* $FreeBSD$ */

/*
 * Player tracking system for 1984 Hack - movement history for monsters
 * Original 1984 source: docs/historical/original-source/hack.track.c
 *
 * Key modernizations: ANSI C function signatures
 */

#include "hack.h"

#define UTSZ 50

coord utrack[UTSZ];
int utcnt = 0;
int utpnt = 0;

void initrack(void) { utcnt = utpnt = 0; }

/* add to track */
void settrack(void) {
  if (utcnt < UTSZ)
    utcnt++;
  if (utpnt == UTSZ)
    utpnt = 0;
  utrack[utpnt].x = u.ux;
  utrack[utpnt].y = u.uy;
  utpnt++;
}

coord *gettrack(int x, int y) {
  int i, cnt, dist;
  coord tc;
  cnt = utcnt;
  for (i = utpnt - 1; cnt--; i--) {
    if (i == -1)
      i = UTSZ - 1;
    tc = utrack[i];
    dist = (x - tc.x) * (x - tc.x) + (y - tc.y) * (y - tc.y);
    if (dist < 3)
      return (dist ? &(utrack[i]) : 0);
  }
  return (0);
}
