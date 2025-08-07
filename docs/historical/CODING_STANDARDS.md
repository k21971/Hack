# restoHack Coding Standards

## Documentation Policy for Non-Original Code

This project preserves authentic 1984 Hack source code while making minimal modern additions for buildability and stability. To maintain clear distinction between original and modern code:

### Documentation Requirement

**ALL** code that is not part of the original 1984 codebase or simple K&R to ANSI C conversion MUST be documented with structured comments explaining:

1. **WHY** the addition was necessary
2. **HOW** it was implemented  
3. **WHAT** it preserves from the original
4. **WHAT** it adds that's modern

### Documentation Format

```c
/**
 * MODERN ADDITION (YYYY): Brief description
 * 
 * WHY: Explanation of the problem that required this addition
 * 
 * HOW: Technical explanation of the implementation approach
 * 
 * PRESERVES: What original 1984 behavior/logic is maintained
 * ADDS: What modern functionality or compatibility is provided
 */
```

### Examples of Code Requiring Documentation

- **Bug fixes** that add new logic (not just syntax fixes)
- **Defensive programming** additions (error checking, resource cleanup)
- **Compatibility shims** for modern systems
- **New functions** not present in original codebase
- **Modified algorithms** or data structures
- **Added includes** for modern headers not in original

### Examples of Code NOT Requiring Documentation

- **K&R to ANSI C conversion**: Function signature modernization
- **Simple syntax fixes**: Adding void, const keywords
- **Header organization**: Moving declarations to proper files
- **Build system**: CMake, compiler flags, etc.
- **Whitespace/formatting**: Code style consistency

### Preservation Principle

The goal is to make it easy for future developers to:

1. **Identify authentic 1984 code** vs modern additions
2. **Understand why** modern additions were necessary
3. **Evaluate whether** additions could be removed or improved
4. **Learn from** the historical code while understanding modern adaptations

### Existing Documented Additions

As of July 2025, the following modern additions have been documented:

1. **hack.u_init.c**: Mutable role strings for ANSI C compatibility
2. **hack.end.c**: Stale lock detection and cleanup for robustness

All future additions should follow this documentation standard to maintain the educational and preservation value of the project.