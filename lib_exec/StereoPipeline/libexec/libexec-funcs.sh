#!/bin/sh

msg() {
    echo $* >&2
}

die() {
    msg $*
    kill $self
}

# if 1 is greater than or equal to 2 .. return 0. Else return 1.
version_comp() {
    retval=$(echo $1 $2 | awk '{ a_len=split( $1, a, "."); b_len=split( $2, b, "." );
                                 len=a_len; if (b_len>len) {len=b_len};
                                 for ( i = 1; i <= len; i++ ) {
                                   l=a[i];
                                   r=b[i];
                                   if ( !length(l) ) { l=0 }
                                   if ( !length(r) ) { r=0 }
                                   if ( l > r ) { print "0"; exit }
                                   else if ( l < r ) { print "1"; exit }
                                 };
                                 print "0"
                               }')
    return $retval
}

# Keep this in sync with the function in funcs.sh
isis_version() {
    local ROOT="${1:-$ISISROOT}"
    local ISIS_HEADER="${ROOT}/version"
    if test -s ${ISIS_HEADER}; then
        local version="$(head -1 < $ISIS_HEADER | sed 's/\([0-9]*\.[0-9]*\.[0-9]*\).*/\1/')"
    else
        local ISIS_HEADER="${ROOT}/src/base/objs/Constants/Constants.h"
        local version="$(grep version $ISIS_HEADER 2>/dev/null | cut -d\" -f2)"
    fi
    if test -z "${version}"; then
        msg "Unable to locate ISIS version header."
        msg "Expected it at $ISIS_HEADER"
        die "Perhaps your ISISROOT ($ROOT) is incorrect?"
    fi
    echo "$version"
}

# Keep this in sync with the function in funcs.sh
libc_version() {
    local locations="/lib/x86_64-linux-gnu/libc.so.6 /lib/i386-linux-gnu/libc.so.6 /lib/i686-linux-gnu/libc.so.6 /lib/libc.so.6 /lib64/libc.so.6 /lib32/libc.so.6"
    for library in $locations; do
        if [ -e $library ]; then
            local version="$($library | head -1 | sed 's/[^0-9.]*\([0-9.]*\).*/\1/' )"
            echo $version
            return
        fi
    done
    msg "Unable to determine libc version. This is likely our fault since we don't know where your OS put it."
    die "Could you email the ASP developers with your OS information?"
}

check_isis() {
    if test -z "$ISISROOT"; then
        die "Please set ISISROOT before you run $0"
    fi
    local current="$(isis_version)"
    if test "$BAKED_ISIS_VERSION" != "$current"; then
        msg "This version of Stereo Pipeline requires version $BAKED_ISIS_VERSION"
        die "but your ISISROOT points to version $current"
    fi
}

check_libc() {
    local curent="$(libc_version)"
    if ! version_comp $current $BAKED_LIBC_VERSION ; then
        msg "This version of Stereo Pipeline requires a libc version of $BAKED_LIBC_VERSION"
        die "but your operating system features an older $current"
    fi
}

set_lib_paths() {
    local add_paths="$ISISROOT/lib:$ISISROOT/3rdParty/lib:${1}"
    export GDAL_DATA=${TOPLEVEL}/share/gdal
    export ASP_DATA=${TOPLEVEL}/share
    case $(uname -s) in
        Linux)
            export LD_LIBRARY_PATH="${add_paths}${LD_LIBRARY_PATH:+:}$LD_LIBRARY_PATH"
            export OSG_LIBRARY_PATH="${LD_LIBRARY_PATH}"
            ;;
        Darwin)
            export DYLD_FALLBACK_LIBRARY_PATH="${add_paths}${DYLD_FALLBACK_LIBRARY_PATH:+:}$DYLD_FALLBACK_LIBRARY_PATH"
            export DYLD_FALLBACK_FRAMEWORK_PATH="${add_paths}${DYLD_FALLBACK_FRAMEWORK_PATH:+:}$DYLD_FALLBACK_FRAMEWORK_PATH"
            export OSG_LIBRARY_PATH="${DYLD_FALLBACK_LIBRARY_PATH}"
            ;;
        *)
            die "Unknown OS: $(uname -s)"
            ;;
    esac
}
