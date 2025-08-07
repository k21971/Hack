cmake_minimum_required(VERSION 3.16)
project(restoHack VERSION 1.0.3 LANGUAGES C)

# Set C standard
set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

# makepkg compatibility: Remove -Werror flags that cause packaging failures
# This handles system-injected CFLAGS from makepkg.conf that include -Werror=format-security
string(REPLACE "-Werror=format-security" "" CMAKE_C_FLAGS "${CMAKE_C_FLAGS}")
string(REGEX REPLACE "-Werror[^ ]*" "" CMAKE_C_FLAGS "${CMAKE_C_FLAGS}")
string(STRIP "${CMAKE_C_FLAGS}" CMAKE_C_FLAGS)

# Modern CMake: Will use target_include_directories for better scoping
# Removed global include_directories() - using target-specific includes instead

# Find required libraries
find_library(TERMCAP_LIBRARY NAMES termcap ncurses)
if(NOT TERMCAP_LIBRARY)
    message(FATAL_ERROR "termcap or ncurses library not found")
endif()

# Check for compat library (BSD-specific, might not exist on Linux)
find_library(COMPAT_LIBRARY compat)


set(HACK_SOURCES
    src/alloc.c
    src/hack.Decl.c  
    src/hack.main.c    
    src/hack.mkobj.c   
    src/hack.invent.c  
    src/hack.worn.c    
    src/hack.mklev.c   
    src/hack.lev.c     
    src/hack.pri.c    
    src/hack.topl.c   
    src/hack.termcap.c 
    src/hack.objnam.c  
    src/hack.o_init.c  
    src/hack.pager.c   
    src/hack.makemon.c 
    src/hack.tty.c     
    src/hack.fight.c   
    src/hack.mon.c     
    src/hack.eat.c     
    src/hack.end.c     
    src/hack.do_name.c 
    src/hack.search.c  
    src/hack.monst.c   
    src/hack.cmd.c     
    src/hack.c         
    src/hack.do.c      
    src/hack.wield.c   
    src/hack.engrave.c 
    src/hack.potion.c  
    src/hack.read.c    
    src/hack.zap.c     
    src/hack.trap.c    
    src/hack.apply.c   
    src/hack.dog.c     
    src/hack.shk.c    
    src/hack.unix.c   
    src/hack.save.c   
    src/hack.vault.c  
    src/hack.worm.c   
    src/hack.mkmaze.c 
    src/hack.bones.c   
    src/hack.mhitu.c   
    src/hack.steal.c   
    src/hack.wizard.c  
    src/hack.do_wear.c 
    src/hack.ioctl.c   
    src/hack.mkshop.c  
    src/hack.rumors.c  
    src/hack.rip.c     
    src/hack.shknam.c  
    src/hack.options.c 
    src/hack.timeout.c
    src/hack.track.c
    src/hack.u_init.c
    src/hack.version.c   
    src/rnd.c           
    
)

# Build makedefs utility first
add_executable(makedefs src/makedefs.c)

# Modern CMake: Generate hack.onames.h using makedefs with proper paths
add_custom_command(
    OUTPUT ${CMAKE_CURRENT_BINARY_DIR}/hack.onames.h
    COMMAND makedefs ${CMAKE_CURRENT_SOURCE_DIR}/src/def.objects.h > ${CMAKE_CURRENT_BINARY_DIR}/hack.onames.h
    DEPENDS makedefs ${CMAKE_CURRENT_SOURCE_DIR}/src/def.objects.h
    WORKING_DIRECTORY ${CMAKE_CURRENT_BINARY_DIR}
    COMMENT "Generating hack.onames.h with authentic 1984 object definitions"
)

# Main hack executable
add_executable(hack ${HACK_SOURCES} ${CMAKE_CURRENT_BINARY_DIR}/hack.onames.h)

# Modern CMake: Target-specific include directories (better than global includes)
target_include_directories(hack PRIVATE
    ${CMAKE_CURRENT_SOURCE_DIR}
    ${CMAKE_CURRENT_SOURCE_DIR}/src
    ${CMAKE_CURRENT_BINARY_DIR}
)
# Compiler flags
target_compile_options(hack PRIVATE 
    $<$<C_COMPILER_ID:GNU>:-Wno-stringop-truncation>
    $<$<C_COMPILER_ID:Clang>:-Wno-string-plus-int>
    # Packaging compatibility: Suppress warnings that might be treated as errors
    -Wno-error=format-security
    -Wno-error
    # Buffer overflow protection for save system safety
    $<$<C_COMPILER_ID:GNU>:-fstack-protector-strong>
    $<$<C_COMPILER_ID:Clang>:-fstack-protector-strong>
    # Enable debugging symbols for crash analysis
    -g
)

# Fortify source for additional buffer overflow detection
target_compile_definitions(hack PRIVATE _FORTIFY_SOURCE=2)

# Runtime path configuration - inject absolute paths to prevent hardcoded path issues
target_compile_definitions(hack PRIVATE 
    HACKDIR="${CMAKE_BINARY_DIR}/hackdir"
    SAVE_VERSION="${PROJECT_VERSION}"
)

# Struct packing control for save system consistency
option(ENABLE_STRUCT_PACKING "Enable struct packing for save system compatibility" ON)
if(ENABLE_STRUCT_PACKING)
    # Check if compiler supports pragma pack
    include(CheckCSourceCompiles)
    check_c_source_compiles("
        #pragma pack(1)
        struct test { char a; int b; };
        #pragma pack()
        int main() { return sizeof(struct test); }
    " HAVE_PRAGMA_PACK)
    
    if(HAVE_PRAGMA_PACK)
        target_compile_definitions(hack PRIVATE HAVE_PRAGMA_PACK=1)
        message(STATUS "Struct packing enabled for save system consistency")
    else()
        message(WARNING "Compiler doesn't support #pragma pack - save compatibility may be affected")
    endif()
endif()

# Save system build options and debugging
option(ENABLE_SAVE_DEBUG "Enable save system debug logging" OFF)
if(ENABLE_SAVE_DEBUG)
    target_compile_definitions(hack PRIVATE SAVE_DEBUG=1)
    message(STATUS "Save system debug logging enabled")
endif()

option(ENABLE_SAVE_VALIDATION "Enable save file integrity checks" ON)
if(ENABLE_SAVE_VALIDATION)
    target_compile_definitions(hack PRIVATE SAVE_VALIDATION=1)
    message(STATUS "Save file validation enabled")
endif()

# Add sanitizers for learning and debugging (optional)
option(ENABLE_SANITIZERS "Enable AddressSanitizer and UndefinedBehaviorSanitizer" OFF)
if(ENABLE_SANITIZERS)
    target_compile_options(hack PRIVATE -fsanitize=address -fsanitize=undefined -g)
    target_link_options(hack PRIVATE -fsanitize=address -fsanitize=undefined)
    message(STATUS "Sanitizers enabled - great for learning memory safety!")
endif()

# Enhanced memory sanitizers specifically for save/load operations
option(ENABLE_SAVE_SANITIZERS "Enable memory sanitizers for save/load debugging" OFF)
if(ENABLE_SAVE_SANITIZERS)
    target_compile_options(hack PRIVATE -fsanitize=memory -fsanitize-memory-track-origins -g)
    target_link_options(hack PRIVATE -fsanitize=memory)
    message(STATUS "Memory sanitizers enabled for save system debugging")
endif()

# Link libraries
target_link_libraries(hack ${TERMCAP_LIBRARY})
if(COMPAT_LIBRARY)
    target_link_libraries(hack ${COMPAT_LIBRARY})
endif()

# Data files
set(DATA_FILES rumors help hh data)

# MODERN ADDITION (2025): Create hackdir structure in build directory
# Use custom target instead of POST_BUILD for reliability
# All hardcoded file paths from config.h that need to exist after chdir("./hackdir")

# Versioned save system configuration
set(HACK_VERSION "${PROJECT_VERSION}")
set(SAVE_DIR "${CMAKE_BINARY_DIR}/hackdir/save")
set(VERSIONED_SAVE_DIR "${SAVE_DIR}/v${HACK_VERSION}")
set(BACKUP_SAVE_DIR "${SAVE_DIR}/backup")

add_custom_target(setup_hackdir ALL
    # Copy hackdir structure and ensure write permissions on record file
    COMMAND ${CMAKE_COMMAND} -E copy_directory ${CMAKE_SOURCE_DIR}/hackdir ${CMAKE_BINARY_DIR}/hackdir
    # Ensure all config.h defined files exist in hackdir after chdir
    COMMAND ${CMAKE_COMMAND} -E copy_if_different ${CMAKE_SOURCE_DIR}/data ${CMAKE_BINARY_DIR}/hackdir/data
    COMMAND ${CMAKE_COMMAND} -E copy_if_different ${CMAKE_SOURCE_DIR}/help ${CMAKE_BINARY_DIR}/hackdir/help  
    COMMAND ${CMAKE_COMMAND} -E copy_if_different ${CMAKE_SOURCE_DIR}/hh ${CMAKE_BINARY_DIR}/hackdir/hh
    COMMAND ${CMAKE_COMMAND} -E copy_if_different ${CMAKE_SOURCE_DIR}/rumors ${CMAKE_BINARY_DIR}/hackdir/rumors
    # Create required directories and lock files
    COMMAND ${CMAKE_COMMAND} -E make_directory ${SAVE_DIR}
    COMMAND ${CMAKE_COMMAND} -E make_directory ${VERSIONED_SAVE_DIR}
    COMMAND ${CMAKE_COMMAND} -E make_directory ${BACKUP_SAVE_DIR}
    COMMAND ${CMAKE_COMMAND} -E touch ${CMAKE_BINARY_DIR}/hackdir/perm
    # Ensure record file exists and is writable (game checks this at startup)
    COMMAND ${CMAKE_COMMAND} -E touch ${CMAKE_BINARY_DIR}/hackdir/record
    # Also copy files to build root for pre-chdir access (legacy compatibility)
    COMMAND ${CMAKE_COMMAND} -E touch ${CMAKE_BINARY_DIR}/perm
    COMMAND ${CMAKE_COMMAND} -E copy_if_different ${CMAKE_SOURCE_DIR}/data ${CMAKE_BINARY_DIR}/data
    COMMAND ${CMAKE_COMMAND} -E copy_if_different ${CMAKE_SOURCE_DIR}/help ${CMAKE_BINARY_DIR}/help
    COMMAND ${CMAKE_COMMAND} -E copy_if_different ${CMAKE_SOURCE_DIR}/hh ${CMAKE_BINARY_DIR}/hh
    COMMAND ${CMAKE_COMMAND} -E copy_if_different ${CMAKE_SOURCE_DIR}/rumors ${CMAKE_BINARY_DIR}/rumors
    # Clean all possible lock files (HLOCK, LLOCK, record_lock in all locations)
    COMMAND ${CMAKE_COMMAND} -E remove -f ${CMAKE_BINARY_DIR}/record_lock ${CMAKE_BINARY_DIR}/safelock ${CMAKE_BINARY_DIR}/hackdir/record_lock ${CMAKE_BINARY_DIR}/hackdir/safelock
    COMMAND ${CMAKE_COMMAND} -E remove -f ${SAVE_DIR}/* ${VERSIONED_SAVE_DIR}/* ${BACKUP_SAVE_DIR}/*
    COMMENT "Setting up versioned save system: v${HACK_VERSION} with backup support"
    VERBATIM
)

# Ensure hack depends on the setup
add_dependencies(hack setup_hackdir)

# Custom clean target to remove all generated files and lock files
add_custom_target(clean-all
    COMMAND ${CMAKE_COMMAND} -E remove_directory ${CMAKE_BINARY_DIR}/hackdir
    COMMAND ${CMAKE_COMMAND} -E remove -f ${CMAKE_BINARY_DIR}/perm ${CMAKE_BINARY_DIR}/data ${CMAKE_BINARY_DIR}/help ${CMAKE_BINARY_DIR}/hh ${CMAKE_BINARY_DIR}/rumors
    COMMAND ${CMAKE_COMMAND} -E remove -f ${CMAKE_BINARY_DIR}/record_lock ${CMAKE_BINARY_DIR}/safelock
    COMMENT "Clean all hack files and lock files"
)

# Install rules
install(TARGETS hack DESTINATION bin)
install(FILES ${DATA_FILES} DESTINATION share/hack)
install(FILES man/hack.6 DESTINATION share/man/man6)

# Modern CMake: CPack configuration for professional distribution
set(CPACK_PACKAGE_NAME "restohack")
set(CPACK_PACKAGE_VERSION "${PROJECT_VERSION}")
set(CPACK_PACKAGE_DESCRIPTION_SUMMARY "Authentic 1984 Hack game restoration - modernized for contemporary systems")
set(CPACK_PACKAGE_DESCRIPTION "restoHack brings the legendary 1984 Hack game back from the dead with 94.2% authentic code preservation. This isn't a reimagining - it's historical software preservation with modern compatibility. Features complete K&R to ANSI C conversion, cross-platform builds, and 100% authentic 1984 gameplay experience.")

set(CPACK_PACKAGE_VENDOR "restoHack Project")
set(CPACK_PACKAGE_CONTACT "https://github.com/Critlist/restoHack.git")
set(CPACK_PACKAGE_HOMEPAGE_URL "https://github.com/Critlist/restoHack.git")

# Package metadata
set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/LICENSE")
set(CPACK_RESOURCE_FILE_README "${CMAKE_CURRENT_SOURCE_DIR}/README.md")

# Source package configuration
set(CPACK_SOURCE_PACKAGE_FILE_NAME "${CPACK_PACKAGE_NAME}-${CPACK_PACKAGE_VERSION}-src")
set(CPACK_SOURCE_IGNORE_FILES
    "/build/"
    "/\\.git/"
    "/\\.gitignore"
    "hackdir/record_lock"
    "hackdir/safelock"
    "\\.DS_Store"
    ".*~$"
)
# Platform-specific packaging #   #I'm hopeful people want to play this on their systems, so this will be implemented for later use
if(WIN32)
    # Windows NSIS installer
    set(CPACK_GENERATOR "NSIS;ZIP")
    set(CPACK_NSIS_DISPLAY_NAME "restoHack - Authentic 1984 Hack Game")
    set(CPACK_NSIS_HELP_LINK "https://github.com/Critlist/restoHack.git")
    set(CPACK_NSIS_URL_INFO_ABOUT "https://github.com/Critlist/restoHack.git")
elseif(APPLE)
    # macOS packages
    set(CPACK_GENERATOR "TGZ;DragNDrop")
    set(CPACK_DMG_VOLUME_NAME "restoHack")
else()
    # Linux packages (DEB, RPM, tar.gz)
    set(CPACK_GENERATOR "DEB;RPM;TGZ")
    
    # Debian package configuration
    set(CPACK_DEBIAN_PACKAGE_MAINTAINER "restoHack Project <noreply@example.com>")
    set(CPACK_DEBIAN_PACKAGE_SECTION "games")
    set(CPACK_DEBIAN_PACKAGE_PRIORITY "optional")
    set(CPACK_DEBIAN_PACKAGE_DEPENDS "libc6, libncurses5 | libncurses6")
    set(CPACK_DEBIAN_FILE_NAME DEB-DEFAULT)
    
    # RPM package configuration  
    set(CPACK_RPM_PACKAGE_GROUP "Amusements/Games")
    set(CPACK_RPM_PACKAGE_LICENSE "BSD-3-Clause")
    set(CPACK_RPM_PACKAGE_REQUIRES "glibc, ncurses")
    set(CPACK_RPM_FILE_NAME RPM-DEFAULT)
endif()

# Enable CPack
include(CPack)