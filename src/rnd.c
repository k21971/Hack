/* rnd.c - version 1.0.2 */
/* $FreeBSD$ */

/*
 * Random number utilities for 1984 Hack - dice rolling and random generation
 * Original 1984 source: docs/historical/original-source/rnd.c
 *
 * Key modernizations: ANSI C function signatures
 */

#include <stdlib.h>

#define RND(x) (random() % x)

/* MODERN: K&R to ANSI C conversion - function signatures only */
int rn1(int x, int y) { return (RND(x) + y); }

int rn2(int x) { return (RND(x)); }

int rnd(int x) { return (RND(x) + 1); }

int d(int n, int x) {
  int tmp = n;

  while (n--)
    tmp += RND(x);
  return (tmp);
}
