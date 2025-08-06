/* Copyright (c) Stichting Mathematisch Centrum, Amsterdam, 1985. */
/* def.gold.h - version 1.0.2 */



struct gold {
	struct gold *ngold;
	xchar gx,gy;
	long amount;
};

extern struct gold *fgold;
struct gold *g_at(int x, int y);  /* K&R function with proper parameter declaration */
#define newgold()	(struct gold *) alloc(sizeof(struct gold))
