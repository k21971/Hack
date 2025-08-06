/* alloc.c - version 1.0.2 */
/* $FreeBSD$ */

#include <stdlib.h>
#include "hack.h"

#ifdef LINT

/*
   a ridiculous definition, suppressing
	"possible pointer alignment problem" for (long *) malloc()
	"enlarg defined but never used"
	"ftell defined (in <stdio.h>) but never used"
   from lint
*/
#include <stdio.h>
void *
alloc(unsigned n){
long dummy = ftell(stderr);
	if(n) dummy = 0;	/* make sure arg is used */
	return(&dummy);
}

#else

void *
alloc(unsigned lth)
{
	char *ptr;

	if(!(ptr = malloc(lth)))
		panic("Cannot get %d bytes", lth);
	return(ptr);
}

void *
enlarge(char *ptr, unsigned lth)
{
	char *nptr;

	if(!(nptr = realloc(ptr,lth)))
		panic("Cannot reallocate %d bytes", lth);
	return(nptr);
}

#endif /* LINT */
