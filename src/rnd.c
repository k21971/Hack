/* rnd.c - version 1.0.2 */
/* $FreeBSD$ */

#include <stdlib.h>

#define RND(x)  (random() % x)

#if 0
/* ORIGINAL 1984 CODE - preserved for reference */
rn1(x,y)
int x,y;
{
	return(RND(x)+y);
}

rn2(x)
int x;
{
	return(RND(x));
}

rnd(x)
int x;
{
	return(RND(x)+1);
}

d(n,x)
int n,x;
{
	int tmp = n;

	while(n--) tmp += RND(x);
	return(tmp);
}
#endif

/* MODERN: K&R to ANSI C conversion - function signatures only */
int rn1(int x, int y)
{
	return(RND(x)+y);
}

int rn2(int x)
{
	return(RND(x));
}

int rnd(int x)
{
	return(RND(x)+1);
}

int d(int n, int x)
{
	int tmp = n;

	while(n--) tmp += RND(x);
	return(tmp);
}
