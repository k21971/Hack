/* Copyright (c) Stichting Mathematisch Centrum, Amsterdam, 1985. */
/* hack.worm.c - version 1.0.2 */
/* $FreeBSD$ */

#include "hack.h"
#ifndef NOWORM
#include "def.wseg.h"

struct wseg *wsegs[32]; /* linked list, tail first */
struct wseg *wheads[32];
long wgrowtime[32];

int getwn(struct monst *mtmp) {
  int tmp;
  for (tmp = 1; tmp < 32; tmp++)
    if (!wsegs[tmp]) {
      mtmp->wormno = tmp;
      return (1);
    }
  return (0); /* level infested with worms */
}

/* called to initialize a worm unless cut in half */
void initworm(struct monst *mtmp) {
  struct wseg *wtmp;
  int tmp = mtmp->wormno;
  if (!tmp || tmp < 0 || tmp >= 32) /* MODERN: bounds check prevents OOB access to worm arrays */
    return;
  wheads[tmp] = wsegs[tmp] = wtmp = newseg();
  wgrowtime[tmp] = 0;
  wtmp->wx = mtmp->mx;
  wtmp->wy = mtmp->my;
  /*	wtmp->wdispl = 0; */
  wtmp->nseg = 0;
}

void worm_move(struct monst *mtmp) {
  struct wseg *wtmp, *whd;
  int tmp = mtmp->wormno;
  if (tmp < 0 || tmp >= 32) return; /* MODERN: bounds check prevents OOB access to worm arrays */
  wtmp = newseg();
  wtmp->wx = mtmp->mx;
  wtmp->wy = mtmp->my;
  wtmp->nseg = 0;
  /*	wtmp->wdispl = 0; */
  whd = wheads[tmp];
  if (!whd) return; /* MODERN: null check prevents crash on corrupted worm head */
  whd->nseg = wtmp;
  wheads[tmp] = wtmp;
  if (cansee(whd->wx, whd->wy)) {
    unpmon(mtmp);
    atl(whd->wx, whd->wy, '~');
    whd->wdispl = 1;
  } else
    whd->wdispl = 0;
  if (wgrowtime[tmp] <= moves) {
    if (!wgrowtime[tmp])
      wgrowtime[tmp] = moves + rnd(5);
    else
      wgrowtime[tmp] += 2 + rnd(15);
    mtmp->mhpmax += 3;
    mtmp->mhp += 3;
    return;
  }
  whd = wsegs[tmp];
  if (!whd) return; /* MODERN: null check prevents crash on corrupted worm segment */
  wsegs[tmp] = whd->nseg;
  remseg(whd);
}

void worm_nomove(struct monst *mtmp) {
  int tmp;
  struct wseg *wtmp;
  tmp = mtmp->wormno;
  if (tmp < 0 || tmp >= 32) return; /* MODERN: bounds check prevents OOB access to worm arrays */
  wtmp = wsegs[tmp];
  if (wtmp == wheads[tmp])
    return;
  if (wtmp == 0 || wtmp->nseg == 0)
    panic("worm_nomove?");
  wsegs[tmp] = wtmp->nseg;
  remseg(wtmp);
  mtmp->mhp -= 3; /* mhpmax not changed ! */
}

void wormdead(struct monst *mtmp) {
  int tmp = mtmp->wormno;
  struct wseg *wtmp, *wtmp2;
  if (!tmp || tmp < 0 || tmp >= 32) /* MODERN: bounds check prevents OOB access to worm arrays */
    return;
  mtmp->wormno = 0;
  for (wtmp = wsegs[tmp]; wtmp; wtmp = wtmp2) {
    wtmp2 = wtmp->nseg;
    remseg(wtmp);
  }
  wsegs[tmp] = 0;
}

void wormhit(struct monst *mtmp) {
  int tmp = mtmp->wormno;
  struct wseg *wtmp;
  if (!tmp || tmp < 0 || tmp >= 32) /* MODERN: bounds check prevents OOB access to worm arrays */
    return; /* worm without tail */
  for (wtmp = wsegs[tmp]; wtmp; wtmp = wtmp->nseg)
    (void)hitu(mtmp, 1);
}

void wormsee(int tmp) {
  if (tmp < 0 || tmp >= 32) return; /* MODERN: bounds check prevents OOB access to worm arrays */
  struct wseg *wtmp = wsegs[tmp];
  if (!wtmp)
    panic("wormsee: wtmp==0");
  for (; wtmp->nseg; wtmp = wtmp->nseg)
    if (!cansee(wtmp->wx, wtmp->wy) && wtmp->wdispl) {
      newsym(wtmp->wx, wtmp->wy);
      wtmp->wdispl = 0;
    }
}

void pwseg(struct wseg *wtmp) {
  if (!wtmp->wdispl) {
    atl(wtmp->wx, wtmp->wy, '~');
    wtmp->wdispl = 1;
  }
}

void cutworm(struct monst *mtmp, xchar x, xchar y,
             uchar weptyp) /* uwep->otyp or 0 */
{
  struct wseg *wtmp, *wtmp2;
  struct monst *mtmp2;
  int tmp, tmp2;
  if (mtmp->mx == x && mtmp->my == y)
    return; /* hit headon */

  /* cutting goes best with axe or sword */
  tmp = rnd(20);
  if (weptyp == LONG_SWORD || weptyp == TWO_HANDED_SWORD || weptyp == AXE)
    tmp += 5;
  if (tmp < 12)
    return;

  /* if tail then worm just loses a tail segment */
  tmp = mtmp->wormno;
  wtmp = wsegs[tmp];
  if (!wtmp)
    return; /* MODERN: defensive check against null worm segment */
  if (wtmp->wx == x && wtmp->wy == y) {
    wsegs[tmp] = wtmp->nseg;
    remseg(wtmp);
    return;
  }

  /* cut the worm in two halves */
  mtmp2 = newmonst(0);
  if (!mtmp2) return; /* MODERN: null check prevents crash on memory allocation failure */
  *mtmp2 = *mtmp;
  mtmp2->mxlth = mtmp2->mnamelth = 0;

  /* sometimes the tail end dies */
  if (rn2(3) || !getwn(mtmp2)) {
    monfree(mtmp2);
    tmp2 = 0;
  } else {
    tmp2 = mtmp2->wormno;
    wsegs[tmp2] = wsegs[tmp];
    wgrowtime[tmp2] = 0;
  }
  do {
    if (!wtmp->nseg) break; /* MODERN: null check prevents crash on segment chain corruption */
    if (wtmp->nseg->wx == x && wtmp->nseg->wy == y) {
      if (tmp2)
        wheads[tmp2] = wtmp;
      wsegs[tmp] = wtmp->nseg->nseg;
      remseg(wtmp->nseg);
      wtmp->nseg = 0;
      if (tmp2) {
        pline("You cut the worm in half.");
        mtmp2->mhpmax = mtmp2->mhp = (schar)d(mtmp2->data->mlevel, 8); /* MODERN: Safe cast - HP bounded by dice */
        mtmp2->mx = wtmp->wx;
        mtmp2->my = wtmp->wy;
        mtmp2->nmon = fmon;
        fmon = mtmp2;
        pmon(mtmp2);
      } else {
        pline("You cut off part of the worm's tail.");
        remseg(wtmp);
      }
      mtmp->mhp /= 2;
      return;
    }
    wtmp2 = wtmp->nseg;
    if (!tmp2)
      remseg(wtmp);
    wtmp = wtmp2;
  } while (wtmp &&
           wtmp->nseg); /* MODERN: check wtmp not null before dereferencing */
  panic("Cannot find worm segment");
}

void remseg(struct wseg *wtmp) {
  if (!wtmp)
    return; /* MODERN: defensive check against null segment */
  if (wtmp->wdispl)
    newsym(wtmp->wx, wtmp->wy);
  free((char *)wtmp);
}
#endif /* NOWORM */
