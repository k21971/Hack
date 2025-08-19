/* Copyright (c) Stichting Mathematisch Centrum, Amsterdam, 1985. */
/* hack.search.c - version 1.0.3 */
/* $FreeBSD$ */

#include "hack.h"

extern struct monst *makemon();

int findit(void)	/* returns number of things found */
{
	int num;
	unsigned char zx,zy;
	struct trap *ttmp;
	struct monst *mtmp;
	unsigned char lx,hx,ly,hy;

	if(u.uswallow) return(0);
	for(lx = (unsigned char)u.ux; (num = levl[(unsigned char)(lx-1)][(unsigned char)u.uy].typ) && num != CORR; lx--) ; /* MODERN: Cast to unsigned char for safe array indexing */
	for(hx = (unsigned char)u.ux; (num = levl[(unsigned char)(hx+1)][(unsigned char)u.uy].typ) && num != CORR; hx++) ; /* MODERN: Cast to unsigned char for safe array indexing */
	for(ly = (unsigned char)u.uy; (num = levl[(unsigned char)u.ux][(unsigned char)(ly-1)].typ) && num != CORR; ly--) ; /* MODERN: Cast to unsigned char for safe array indexing */
	for(hy = (unsigned char)u.uy; (num = levl[(unsigned char)u.ux][(unsigned char)(hy+1)].typ) && num != CORR; hy++) ; /* MODERN: Cast to unsigned char for safe array indexing */
	num = 0;
	for(zy = ly; zy <= hy; zy++)
		for(zx = lx; zx <= hx; zx++) {
			if(levl[zx][zy].typ == SDOOR) {
				levl[zx][zy].typ = DOOR;
				atl(zx, zy, '+');
				num++;
			} else if(levl[zx][zy].typ == SCORR) {
				levl[zx][zy].typ = CORR;
				atl(zx, zy, CORR_SYM);
				num++;
			} else if(ttmp = t_at(zx, zy)) {
				if(ttmp->ttyp == PIERC){
					(void) makemon(PM_PIERCER, zx, zy);
					num++;
					deltrap(ttmp);
				} else if(!ttmp->tseen) {
					ttmp->tseen = 1;
					if(!vism_at(zx, zy))
						atl(zx,zy,'^');
					num++;
				}
			} else if(mtmp = m_at(zx,zy)) if(mtmp->mimic){
				seemimic(mtmp);
				num++;
			}
		}
	return(num);
}

int dosearch(void)
{
	unsigned char x,y;
	struct trap *trap;
	struct monst *mtmp;

	if(u.uswallow) {
		pline("What are you looking for? The exit?");
		return(1);
	}
	else
	for(x = (unsigned char)(u.ux-1); x < (unsigned char)(u.ux+2); x++)
	for(y = (unsigned char)(u.uy-1); y < (unsigned char)(u.uy+2); y++) if(x != (unsigned char)u.ux || y != (unsigned char)u.uy) {
		if(levl[x][y].typ == SDOOR) {
			if(rn2(7)) continue;
			levl[x][y].typ = DOOR;
			levl[x][y].seen = 0;	/* force prl */
			prl(x,y);
			nomul(0);
		} else if(levl[x][y].typ == SCORR) {
			if(rn2(7)) continue;
			levl[x][y].typ = CORR;
			levl[x][y].seen = 0;	/* force prl */
			prl(x,y);
			nomul(0);
		} else {
		/* Be careful not to find anything in an SCORR or SDOOR */
			if(mtmp = m_at(x,y)) if(mtmp->mimic){
				seemimic(mtmp);
				pline("You find a mimic.");
				return(1);
			}
			for(trap = ftrap; trap; trap = trap->ntrap)
			if(trap->tx == x && trap->ty == y &&
			   !trap->tseen && !rn2(8)) {
				nomul(0);
				pline("You find a%s.", traps[trap->ttyp]);
				if(trap->ttyp == PIERC) {
					deltrap(trap);
					(void) makemon(PM_PIERCER,x,y);
					return(1);
				}
				trap->tseen = 1;
				if(!vism_at(x,y)) atl(x,y,'^');
			}
		}
	}
	return(1);
}

int doidtrap(void) {
struct trap *trap;
int x,y;
	if(!getdir(1)) return(0);
	x = u.ux + u.dx;
	y = u.uy + u.dy;
	for(trap = ftrap; trap; trap = trap->ntrap)
		if(trap->tx == x && trap->ty == y && trap->tseen) {
		    if(u.dz)
			if((u.dz < 0) != (!xdnstair && trap->ttyp == TRAPDOOR))
			    continue;
		    pline("That is a%s.", traps[trap->ttyp]);
		    return(0);
		}
	pline("I can't see a trap there.");
	return(0);
}

void wakeup(struct monst *mtmp)
{
	mtmp->msleep = 0;
	setmangry(mtmp);
	if(mtmp->mimic) seemimic(mtmp);
}

/* NOTE: we must check if(mtmp->mimic) before calling this routine */
void seemimic(struct monst *mtmp)
{
		mtmp->mimic = 0;
		mtmp->mappearance = 0;
		unpmon(mtmp);
		pmon(mtmp);
}
