/* Copyright (c) Stichting Mathematisch Centrum, Amsterdam, 1985. */
/* hack.version.c - version 1.0.3 */
/* $FreeBSD$ */

/* 
 * Version information for 1984 Hack - game version and build date display
 * Original 1984 source: docs/historical/original-source/hack.version.c
 * 
 * Key modernizations: ANSI C function signatures
 */

#include	"hack.h"
#include	"date.h"
int doversion(void){
	pline("%s 1.0.3 - last edit %s.", (
#ifdef QUEST
		"Quest"
#else
		"Hack"
#endif /* QUEST */
		), datestring);
	return(0);
}
