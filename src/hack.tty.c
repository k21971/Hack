/*-
 * Copyright (c) 1988, 1993
 *	The Regents of the University of California.  All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 * 3. All advertising materials mentioning features or use of this software
 *    must display the following acknowledgement:
 *	This product includes software developed by the University of
 *	California, Berkeley and its contributors.
 * 4. Neither the name of the University nor the names of its contributors
 *    may be used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND
 * ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE REGENTS OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
 * OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
 * SUCH DAMAGE.
 */

#ifndef lint
#if 0
static char sccsid[] = "@(#)hack.tty.c	8.1 (Berkeley) 5/31/93";
#endif
static const char rcsid[] =
 "$FreeBSD$";
#endif /* not lint */

/* Copyright (c) Stichting Mathematisch Centrum, Amsterdam, 1985. */
/* hack.tty.c - version 1.0.3 */
/* With thanks to the people who sent code for SYSV - hpscdi!jon,
   arnold@ucsf-cgl, wcs@bo95b, cbcephus!pds and others. */

#include	"hack.h"
#include	<stdio.h>
#include	<stdarg.h>
#include	<string.h>

/*
 * The distinctions here are not BSD - rest but rather USG - rest, as
 * BSD still has the old sgttyb structure, but SYSV has termio. Thus:
 * On modern systems, we use termios.h regardless of the original BSD/USG setting
 */
/**
 * MODERN ADDITION (2025): POSIX terminal interface compatibility
 * 
 * WHY: Original 1984 code supported only BSD (sgttyb) and SYSV (termio) interfaces.
 * Modern Unix-like systems use POSIX termios interface, which is more standardized
 * and portable across different platforms (Linux, macOS, BSD variants).
 * 
 * HOW: Added detection for modern POSIX systems (__linux__, __unix__, _POSIX_VERSION)
 * and route them to use termios.h interface instead of the legacy interfaces.
 * 
 * PRESERVES: All original terminal functionality and behavior
 * ADDS: POSIX compliance and modern system compatibility
 */
#if defined(__linux__) || defined(__unix__) || defined(_POSIX_VERSION)
#define	MODERN_TERMIOS
#else
#ifdef BSD
#define	V7
#else
#define USG
#endif
#endif

/*
 * Some systems may have getchar() return EOF for various reasons, and
 * we should not quit before seeing at least NR_OF_EOFS consecutive EOFs.
 */
#ifndef BSD
#define	NR_OF_EOFS	20
#endif /* BSD */


#ifdef MODERN_TERMIOS

#include	<termios.h>
#include	<unistd.h>
#include	<sys/ioctl.h>
#include	<string.h>
#define termstruct	termios
#define kill_sym	c_cc[VKILL]
#define erase_sym	c_cc[VERASE]
/* Modern systems use different tab constants */
#ifdef TAB3
#define EXTABS		TAB3
#elif defined(TABDLY)
#define EXTABS		TABDLY
#else
#define EXTABS		0x1800  /* fallback */
#endif
#define tabflgs		c_oflag
#define echoflgs	c_lflag
#define cbrkflgs	c_lflag
#define CBRKMASK	ICANON
#define CBRKON		! /* reverse condition */
#define OSPEED(x)	((x).c_ospeed)
#define GTTY(x)		(tcgetattr(0, x))
#define STTY(x)		(tcsetattr(0, TCSANOW, x))

#elif defined(USG)

#include	<termio.h>
#include	<unistd.h>
#define termstruct	termio
#define kill_sym	c_cc[VKILL]
#define erase_sym	c_cc[VERASE]
#define EXTABS		TAB3
#define tabflgs		c_oflag
#define echoflgs	c_lflag
#define cbrkflgs	c_lflag
#define CBRKMASK	ICANON
#define CBRKON		! /* reverse condition */
#define OSPEED(x)	((x).c_cflag & CBAUD)
#define GTTY(x)		(ioctl(0, TCGETA, x))
#define STTY(x)		(ioctl(0, TCSETA, x))	/* TCSETAF? TCSETAW? */

#else	/* V7 */

#include	<sgtty.h>
#include	<unistd.h>
#define termstruct	sgttyb
#define	kill_sym	sg_kill
#define	erase_sym	sg_erase
#define EXTABS		XTABS
#define tabflgs		sg_flags
#define echoflgs	sg_flags
#define cbrkflgs	sg_flags
#define CBRKMASK	CBREAK
#define CBRKON		/* empty */
#define OSPEED(x)	(x).sg_ospeed
#define GTTY(x)		(gtty(0, x))
#define STTY(x)		(stty(0, x))

#endif /* V7 */

#if 0
extern short ospeed;
#endif
static char erase_char, kill_char;
static boolean settty_needed = FALSE;
struct termstruct inittyb, curttyb;

/* Function prototypes */
void clearlocks(void);
void setctty(void);
void cgetret(char *s);
char *parse(void);
extern void getioctls(void);
extern void setioctls(void);

/*
 * Get initial state of terminal, set ospeed (for termcap routines)
 * and switch off tab expansion if necessary.
 * Called by startup() in termcap.c and after returning from ! or ^Z
 */
void
gettty(void){
	if(GTTY(&inittyb) < 0) {
		/**
		 * MODERN ADDITION (2025): Terminal compatibility for modern systems
		 * 
		 * WHY: Original 1984 code assumed working terminal I/O control (ioctl).
		 * Modern terminals/emulators may not support all classic ioctl operations,
		 * causing the game to exit rather than gracefully handle the failure.
		 * 
		 * HOW: Instead of exiting on ioctl failure, set reasonable defaults and
		 * continue with degraded terminal functionality. Warns user but stays playable.
		 * 
		 * PRESERVES: Game remains playable in all terminal environments
		 * ADDS: Modern terminal compatibility without breaking authentic behavior
		 */
		printf("Warning: Cannot get terminal settings (modern terminal)\n");
		/* Set reasonable defaults */
		memset(&inittyb, 0, sizeof(inittyb));
		memset(&curttyb, 0, sizeof(curttyb));
		erase_char = '\b';
		kill_char = 21; /* Ctrl-U */
		settty_needed = TRUE;
		return;
	}
	curttyb = inittyb;
#if 0
	ospeed = OSPEED(inittyb);
#endif
	erase_char = inittyb.erase_sym;
	kill_char = inittyb.kill_sym;
	getioctls();

	/* do not expand tabs - they might be needed inside a cm sequence */
	if(curttyb.tabflgs & EXTABS) {
		curttyb.tabflgs &= ~EXTABS;
		setctty();
	}
	settty_needed = TRUE;
}

/* reset terminal to original state */
void
settty(char *s) {
	clear_screen();
	end_screen();
	if(s) printf("%s", s);
	(void) fflush(stdout);
	if(STTY(&inittyb) < 0) {
		/**
		 * MODERN ADDITION (2025): Terminal restoration compatibility
		 * 
		 * WHY: Original 1984 code assumed terminal settings could always be restored.
		 * Modern terminals may not support restoration of all settings, but game
		 * should exit gracefully rather than crash on ioctl failure.
		 * 
		 * HOW: Warn user but continue with game exit - terminal may not restore
		 * perfectly but system remains stable.
		 * 
		 * PRESERVES: Graceful game termination in all environments
		 * ADDS: Error tolerance for modern terminal limitations
		 */
		printf("Warning: Cannot restore terminal settings (modern terminal)\n");
		return;
	}
	flags.echo = (inittyb.echoflgs & ECHO) ? ON : OFF;
	flags.cbreak = (CBRKON(inittyb.cbrkflgs & CBRKMASK)) ? ON : OFF;
	setioctls();
}

void
setctty(void){
	if(STTY(&curttyb) < 0)
		perror("Hack (setctty)");
}


void
setftty(void){
int ef = 0;			/* desired value of flags & ECHO */
int cf = CBRKON(CBRKMASK);	/* desired value of flags & CBREAK */
int change = 0;
	flags.cbreak = ON;
	flags.echo = OFF;
	/* Should use (ECHO|CRMOD) here instead of ECHO */
	if((curttyb.echoflgs & ECHO) != ef){
		curttyb.echoflgs &= ~ECHO;
/*		curttyb.echoflgs |= ef;					*/
		change++;
	}
	if((curttyb.cbrkflgs & CBRKMASK) != cf){
		curttyb.cbrkflgs &= ~CBRKMASK;
		curttyb.cbrkflgs |= cf;
#if defined(USG) || defined(MODERN_TERMIOS)
		/* be satisfied with one character; no timeout */
		curttyb.c_cc[VMIN] = 1;		/* was VEOF */
		curttyb.c_cc[VTIME] = 0;	/* was VEOL */
#endif /* USG || MODERN_TERMIOS */
		change++;
	}
	if(change){
		setctty();
	}
	start_screen();
}


/* fatal error */
/*VARARGS1*/
void
error(char *s, ...) {
	va_list args;
	va_start(args, s);
	if(settty_needed)
		settty((char *) 0);
	vprintf(s, args);
	va_end(args);
	putchar('\n');
	exit(1);
}

/*
 * Read a line closed with '\n' into the array char bufp[BUFSZ].
 * (The '\n' is not stored. The string is closed with a '\0'.)
 * Reading can be interrupted by an escape ('\033') - now the
 * resulting string is "\033".
 */
void
getlin(char *bufp)
{
	char *obufp = bufp;
	int c;

	flags.toplin = 2;		/* nonempty, no --More-- required */
	for(;;) {
		(void) fflush(stdout);
		if((c = getchar()) == EOF) {
			*bufp = 0;
			return;
		}
		if(c == '\033') {
			*obufp = c;
			obufp[1] = 0;
			return;
		}
		if(c == erase_char || c == '\b') {
			if(bufp != obufp) {
				bufp--;
				putstr("\b \b"); /* putsym converts \b */
			} else	bell();
		} else if(c == '\n') {
			*bufp = 0;
			return;
		} else if(' ' <= c && c < '\177') {
				/* avoid isprint() - some people don't have it
				   ' ' is not always a printing char */
			*bufp = c;
			bufp[1] = 0;
			putstr(bufp);
			if(bufp-obufp < BUFSZ-1 && bufp-obufp < COLNO)
				bufp++;
		} else if(c == kill_char || c == '\177') { /* Robert Viduya */
				/* this test last - @ might be the kill_char */
			while(bufp != obufp) {
				bufp--;
				putstr("\b \b");
			}
		} else
			bell();
	}
}

void
getret(void) {
	cgetret("");
}

void
cgetret(char *s)
{
	putsym('\n');
	if(flags.standout)
		standoutbeg();
	putstr("Hit ");
	putstr(flags.cbreak ? "space" : "return");
	putstr(" to continue: ");
	if(flags.standout)
		standoutend();
	xwaitforspace(s);
}

char morc;	/* tell the outside world what char he used */

void
xwaitforspace(char *s)	/* chars allowed besides space or return */
{
int c;

	morc = 0;

	while((c = readchar()) != '\n') {
	    if(flags.cbreak) {
		if(c == ' ') break;
		if(s && strchr(s,c)) {
			morc = c;
			break;
		}
		bell();
	    }
	}
}

char *
parse(void)
{
	static char inputline[COLNO];
	int foo;

	flags.move = 1;
	if(!Invisible) curs_on_u(); else home();
	while((foo = readchar()) >= '0' && foo <= '9')
		multi = 10*multi+foo-'0';
	if(multi) {
		multi--;
		save_cm = inputline;
	}
	inputline[0] = foo;
	inputline[1] = 0;
	if(foo == 'f' || foo == 'F'){
		inputline[1] = getchar();
#ifdef QUEST
		if(inputline[1] == foo) inputline[2] = getchar(); else
#endif /* QUEST */
		inputline[2] = 0;
	}
	if(foo == 'm' || foo == 'M'){
		inputline[1] = getchar();
		inputline[2] = 0;
	}
	clrlin();
	return(inputline);
}

char
readchar(void) {
	int sym;

	(void) fflush(stdout);
	if((sym = getchar()) == EOF)
#ifdef NR_OF_EOFS
	{ /*
	   * Some SYSV systems seem to return EOFs for various reasons
	   * (?like when one hits break or for interrupted systemcalls?),
	   * and we must see several before we quit.
	   */
		int cnt = NR_OF_EOFS;
		while (cnt--) {
		    clearerr(stdin);	/* omit if clearerr is undefined */
		    if((sym = getchar()) != EOF) goto noteof;
		}
		end_of_input();
	     noteof:	;
	}
#else
		end_of_input();
#endif /* NR_OF_EOFS */
	if(flags.toplin == 1)
		flags.toplin = 2;
	return((char) sym);
}

void
end_of_input(void)
{
	settty("End of input?\n");
	clearlocks();
	exit(0);
}
