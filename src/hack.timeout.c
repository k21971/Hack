/* Copyright (c) Stichting Mathematisch Centrum, Amsterdam, 1985. */
/* hack.timeout.c - version 1.0.3 */
/* $FreeBSD$ */

/* 
 * Timeout system for 1984 Hack - timed effects and events
 * Original 1984 source: docs/historical/original-source/hack.timeout.c
 * 
 * Key modernizations: ANSI C function signatures, hack_timeout() renamed for curses compatibility
 */

#include	"hack.h"

#if 0
/* ORIGINAL 1984 CODE - commented out due to curses library conflict */
void timeout(void){
struct prop *upp;
	if(Stoned) stoned_dialogue();
	for(upp = u.uprops; upp < u.uprops+SIZE(u.uprops); upp++)
	    if((upp->p_flgs & TIMEOUT) && !--upp->p_flgs) {
		if(upp->p_tofn) (*upp->p_tofn)();
		else switch(upp - u.uprops){
		case STONED:
			killer = "cockatrice";
			done("died");
			break;
		case SICK:
			pline("You die because of food poisoning.");
			killer = u.usick_cause;
			done("died");
			break;
		case FAST:
			pline("You feel yourself slowing down.");
			break;
		case CONFUSION:
			pline("You feel less confused now.");
			break;
		case BLIND:
			pline("You can see again.");
			setsee();
			break;
		case INVIS:
			on_scr(u.ux,u.uy);
			pline("You are no longer invisible.");
			break;
		case WOUNDED_LEGS:
			heal_legs();
			break;
		}
	}
}
#endif

/**
 * MODERN ADDITION (2025): Renamed timeout to avoid curses library conflict
 * 
 * WHY: curses.h may declare timeout function causing compile error.
 * Original function name conflicts with potential system function.
 * 
 * HOW: Renamed function from timeout to hack_timeout to avoid namespace collision.
 * Updated all call sites to use new name.
 * 
 * PRESERVES: Original 1984 game timeout logic for player effects unchanged.
 * Same algorithm for handling timed effects like poison, blindness, etc.
 * 
 * ADDS: Namespace safety to avoid conflicts with system libraries.
 * Allows building with curses headers without symbol conflicts.
 */
void hack_timeout(void){
struct prop *upp;
	if(Stoned) stoned_dialogue();
	for(upp = u.uprops; upp < u.uprops+SIZE(u.uprops); upp++)
	    if((upp->p_flgs & TIMEOUT) && !--upp->p_flgs) {
		if(upp->p_tofn) (*upp->p_tofn)();
		else switch(upp - u.uprops){
		case STONED:
			killer = "cockatrice";
			done("died");
			break;
		case SICK:
			pline("You die because of food poisoning.");
			killer = u.usick_cause;
			done("died");
			break;
		case FAST:
			pline("You feel yourself slowing down.");
			break;
		case CONFUSION:
			pline("You feel less confused now.");
			break;
		case BLIND:
			pline("You can see again.");
			setsee();
			break;
		case INVIS:
			on_scr(u.ux,u.uy);
			pline("You are no longer invisible.");
			break;
		case WOUNDED_LEGS:
			heal_legs();
			break;
		}
	}
}

/* He is being petrified - dialogue by inmet!tower */
/* MODERN: CONST-CORRECTNESS: petrification message strings are read-only */
const char *const stoned_texts[] = {
	"You are slowing down.",		/* 5 */
	"Your limbs are stiffening.",		/* 4 */
	"Your limbs have turned to stone.",	/* 3 */
	"You have turned to stone.",		/* 2 */
	"You are a statue."			/* 1 */
};

void stoned_dialogue(void)
{
	long i = (Stoned & TIMEOUT);

	if(i > 0 && i <= SIZE(stoned_texts))
		pline(stoned_texts[SIZE(stoned_texts) - i]);
	if(i == 5)
		Fast = 0;
	if(i == 3)
		nomul(-3);
}
