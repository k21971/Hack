/* Copyright (c) Stichting Mathematisch Centrum, Amsterdam, 1985. */
/* hack.Decl.c - version 1.0.3 */

/*
 * Global variable declarations for 1984 Hack - game state and data structures
 * Original 1984 source: docs/historical/original-source/hack.Decl.c
 *
 * Key modernizations: ANSI C compatibility
 */

#include "hack.h"
char nul[40];                     /* contains zeros */
char plname[PL_NSIZ];             /* player name */
char lock[PL_NSIZ + 4] = "1lock"; /* long enough for login name .99 */

boolean in_mklev, restoring;

struct rm levl[COLNO][ROWNO]; /* level map */
#ifndef QUEST
struct mkroom rooms[MAXNROFROOMS + 1];
coord doors[DOORMAX];
#endif /* QUEST */
struct monst *fmon = 0;
struct trap *ftrap = 0;
struct gold *fgold = 0;
struct obj *fobj = 0, *fcobj = 0, *invent = 0, *uwep = 0, *uarm = 0, *uarm2 = 0,
           *uarmh = 0, *uarms = 0, *uarmg = 0, *uright = 0, *uleft = 0,
           *uchain = 0, *uball = 0;
struct flag flags;
struct you u;
struct monst youmonst; /* dummy; used as return value for boomhit */

xchar dlevel = 1;
/* Original 1984: xchar xupstair, yupstair, xdnstair, ydnstair; */
unsigned char xupstair, yupstair, xdnstair,
    ydnstair; /* MODERN: unsigned to prevent buffer underflow */
char *save_cm = 0;
const char *nomovemsg; /* MODERN: const because assigned string literals */
const char *killer;    /* MODERN: CONST-CORRECTNESS: killer points to read-only
                          death reasons */

long moves = 1;
long wailmsg = 0;

int multi = 0;
char genocided[60];
char fut_geno[60];

xchar curx, cury;
/* Original 1984: xchar seelx, seehx, seely, seehy; */
unsigned char seelx, seehx, seely,
    seehy; /* corners of lit room - MODERN: unsigned to prevent buffer underflow
            */

coord bhitpos;

char quitchars[] = " \r\n\033";
