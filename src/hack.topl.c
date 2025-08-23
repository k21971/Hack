/* Copyright (c) Stichting Mathematisch Centrum, Amsterdam, 1985. */
/* hack.topl.c - version 1.0.2 */
/* $FreeBSD$ */

/* 
 * Top line display for 1984 Hack - message handling and screen output
 * Original 1984 source: docs/historical/original-source/hack.topl.c
 * 
 * Key modernizations: ANSI C function signatures, stdarg.h for varargs
 */

#include "hack.h"
#include <stdio.h>
#include <stdarg.h>
extern char *eos(char *s);
extern int CO;

char toplines[BUFSZ];
xchar tlx, tly;			/* set by pline; used by addtopl */

struct topl {
	struct topl *next_topl;
	char *topl_text;
} *old_toplines, *last_redone_topl;
#define	OTLMAX	20		/* max nr of old toplines remembered */

int
doredotopl(void)
{
	if(last_redone_topl)
		last_redone_topl = last_redone_topl->next_topl;
	if(!last_redone_topl)
		last_redone_topl = old_toplines;
	if(last_redone_topl){
		(void) strncpy(toplines, last_redone_topl->topl_text, BUFSZ-1);
		toplines[BUFSZ-1] = '\0';  /* MODERN: Ensure null termination */
	}
	redotoplin();
	return(0);
}

void
redotoplin(void)
{
	home();
	if(index(toplines, '\n')) cl_end();
	putstr(toplines);
	cl_end();
	tlx = curx;
	tly = cury;
	flags.toplin = 1;
	if(tly > 1)
		more();
}

void
remember_topl(void)
{
struct topl *tl;
int cnt = OTLMAX;
	if(last_redone_topl &&
	   !strcmp(toplines, last_redone_topl->topl_text)) return;
	if(old_toplines &&
	   !strcmp(toplines, old_toplines->topl_text)) return;
	last_redone_topl = 0;
	tl = (struct topl *)
		alloc((unsigned)(strlen(toplines) + sizeof(struct topl) + 1));
	tl->next_topl = old_toplines;
	tl->topl_text = (char *)(tl + 1);
	(void) strcpy(tl->topl_text, toplines);  /* MODERN: Safe - allocated exact size */
	old_toplines = tl;
	while(cnt && tl){
		cnt--;
		tl = tl->next_topl;
	}
	if(tl && tl->next_topl){
		free((char *) tl->next_topl);
		tl->next_topl = 0;
	}
}

void
/* MODERN: CONST-CORRECTNESS: addtopl message is read-only */
addtopl(const char *s)
{
	curs(tlx,tly);
	if(tlx + (int)strlen(s) > CO) putsym('\n');  /* MODERN: Cast strlen to int for screen coordinate math */
	putstr(s);
	tlx = curx;
	tly = cury;
	flags.toplin = 1;
}

void
/* MODERN: CONST-CORRECTNESS: xmore message is read-only */
xmore(const char *s)	/* allowed chars besides space/return */
{
	if(flags.toplin) {
		curs(tlx, tly);
		/* Original 1984: if(tlx + 8 > CO) putsym('\n'), tly++; */
		if(tlx + 8 > CO) putsym('\n');  /* MODERN: Removed redundant tly++ - putsym('\n') already increments tly in line 225 */
	}

	if(flags.standout)
		standoutbeg();
	putstr("--More--");
	if(flags.standout)
		standoutend();

	xwaitforspace(s);
	if(flags.toplin && tly > 1) {
		home();
		cl_end();
		docorner(1, tly-1);
	}
	flags.toplin = 0;
}

void
more(void)
{
	xmore("");
}

void
/* MODERN: CONST-CORRECTNESS: cmore message is read-only */
cmore(const char *s)
{
	xmore(s);
}

void
clrlin(void)
{
	if(flags.toplin) {
		home();
		cl_end();
		if(tly > 1) docorner(1, tly-1);
		remember_topl();
	}
	flags.toplin = 0;
}

/*VARARGS1*/
void
/* MODERN: CONST-CORRECTNESS: pline message is read-only */
pline(const char *line, ...)
{
	char pbuf[BUFSZ];
	char *bp = pbuf, *tl;
	int n,n0;
	va_list args;

	if(!line || !*line) return;
	if(!index(line, '%')) {
		(void) strncpy(pbuf, line, BUFSZ-1);
		pbuf[BUFSZ-1] = '\0';  /* MODERN: Ensure null termination */
	} else {
		va_start(args, line);
		(void) vsnprintf(pbuf, BUFSZ, line, args);  /* MODERN: Safe vsprintf replacement - identical output, prevents overflow */
		va_end(args);
	}
	if(flags.toplin == 1 && !strcmp(pbuf, toplines)) return;
	nscr();		/* %% */

	/* If there is room on the line, print message on same line */
	/* But messages like "You die..." deserve their own line */
	n0 = strlen(bp);
	if(flags.toplin == 1 && tly == 1 &&
	    n0 + (int)strlen(toplines) + 3 < CO-8 &&  /* leave room for --More-- */
	    n0 + strlen(toplines) + 3 < BUFSZ-1 &&  /* MODERN: prevent buffer overflow */
	    strncmp(bp, "You ", 4)) {
		(void) strncat(toplines, "  ", BUFSZ-1-strlen(toplines));
		(void) strncat(toplines, bp, BUFSZ-1-strlen(toplines));
		tlx += 2;
		addtopl(bp);
		return;
	}
	if(flags.toplin == 1) more();
	remember_topl();
	toplines[0] = 0;
	while(n0){
		if(n0 >= CO){
			/* look for appropriate cut point */
			n0 = 0;
			for(n = 0; n < CO; n++) if(bp[n] == ' ')
				n0 = n;
			if(!n0) for(n = 0; n < CO-1; n++)
				if(!letter(bp[n])) n0 = n;
			if(!n0) n0 = CO-2;
		}
		tl = eos(toplines);
		/* MODERN: Bounds check before copying */
		if(tl - toplines + n0 + 2 < BUFSZ) {  /* +2 for \n and \0 */
			(void) strncpy(tl, bp, n0);
			tl[n0] = 0;
			bp += n0;

			/* remove trailing spaces, but leave one */
			while(n0 > 1 && tl[n0-1] == ' ' && tl[n0-2] == ' ')
				tl[--n0] = 0;

			n0 = strlen(bp);
			if(n0 && tl[0]) {
				if(tl - toplines + strlen(tl) + 1 < BUFSZ)
					(void) strcat(tl, "\n");
			}
		} else {
			/* Buffer full - truncate gracefully */
			break;
		}
	}
	redotoplin();
}

void
putsym(char c)
{
	switch(c) {
	case '\b':
		backsp();
		return;
	case '\n':
		curx = 1;
		cury++;
		if(cury > tly) tly = cury;
		break;
	default:
		if(curx == CO)
			putsym('\n');	/* 1 <= curx <= CO; avoid CO */
		else
			curx++;
	}
	(void) putchar(c);
}

void
/* MODERN: CONST-CORRECTNESS: putstr message is read-only */
putstr(const char *s)
{
	while(*s) putsym(*s++);
}
