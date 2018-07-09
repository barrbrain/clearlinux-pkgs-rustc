%global rust_triple x86_64-unknown-linux-gnu

# ALL Rust libraries are private, because they don't keep an ABI.
%global _privatelibs lib.*-[[:xdigit:]]*[.]so.*
%global __provides_exclude ^(%{_privatelibs})$
%global __requires_exclude ^(%{_privatelibs})$

# While we don't want to encourage dynamic linking to Rust shared libraries, as
# there's no stable ABI, we still need the unallocated metadata (.rustc) to
# support custom-derive plugins like #[proc_macro_derive(Foo)].  But eu-strip is
# very eager by default, so we have to limit it to -g, only debugging symbols.
%global _find_debuginfo_opts -g

# Use hardening ldflags.
%global rustflags -Clink-arg=-Wl,-z,relro,-z,now

Name:           rustc
Version:        1.27.0
Release:        41
Summary:        The Rust Programming Language
License:        Apache-2.0 BSD-2-Clause BSD-3-Clause ISC MIT
URL:            https://www.rust-lang.org
Source0:        https://static.rust-lang.org/dist/rustc-1.27.0-src.tar.gz
Patch1:         0001-Fix-new-renamed_and_removed_lints-warning-247.patch

BuildRequires:  cargo >= 0.18.0
BuildRequires:  %{name} >= 0.17.0
BuildRequires:  make
BuildRequires:  gcc
BuildRequires:  gcc-dev
BuildRequires:  ncurses-dev
BuildRequires:  zlib-dev
BuildRequires:  python3
BuildRequires:  curl
BuildRequires:  llvm-dev >= 3.7

# make check needs "ps" for src/test/run-pass/wait-forked-but-failed-child.rs
BuildRequires:  procps-ng

# debuginfo-gdb tests need gdb
BuildRequires:  gdb

# TODO: work on unbundling these!
Provides:       bundled(libbacktrace) = 6.1.0
Provides:       bundled(miniz) = 1.16~beta+r1

Requires:       binutils
Requires:       gcc
Requires:       gcc-dev
Requires:       libc6-dev


%description
Rust is a systems programming language that runs blazingly fast, prevents
segfaults, and guarantees thread safety.

%prep

%setup -q -n rustc-%{version}-src

pushd src/vendor/error-chain
%patch1 -p1
popd

%build
%configure \
    --build=%{rust_triple} \
    --host=%{rust_triple} \
    --target=%{rust_triple} \
    --disable-option-checking \
    --libdir=/usr/lib \
    --enable-local-rust \
    --local-rust-root=/usr \
    --llvm-root=/usr \
    --disable-codegen-tests \
    --enable-llvm-link-shared \
    --disable-jemalloc \
    --disable-rpath \
    --enable-debuginfo \
    --enable-vendor \
    --release-channel=stable

# The configure macro will modify some autoconf-related files, which upsets
# cargo when it tries to verify checksums in those files.  If we just truncate
# that file list, cargo won't have anything to complain about.
find src/vendor -name .cargo-checksum.json \
     -exec sed -i.uncheck -e 's/"files":{[^}]*}/"files":{ }/' '{}' '+'

python3 x.py build

%install
export RUSTFLAGS="%{rustflags}"

DESTDIR=%{buildroot} python3 x.py install

# # Remove installer artifacts (manifests, uninstall scripts, etc.)
find %{buildroot}/usr/lib/rustlib -maxdepth 1 -type f -exec rm -v '{}' '+'

# # The shared libraries should be executable for debuginfo extraction.
find %{buildroot}/usr/lib/rustlib/ -type f -name '*.so' -exec chmod -v +x '{}' '+'

# # FIXME: __os_install_post will strip the rlibs
# # -- should we find a way to preserve debuginfo?

# # Remove unwanted documentation files
rm -fr %{buildroot}/usr/share/doc

%files
/usr/bin/rust-gdb
/usr/bin/rust-lldb
/usr/bin/rustc
/usr/bin/rustdoc
/usr/lib/*.so
/usr/lib/rustlib/etc/*.py
/usr/lib/rustlib/x86_64-unknown-linux-gnu/lib/*.rlib
/usr/lib/rustlib/x86_64-unknown-linux-gnu/lib/*.so
/usr/lib/rustlib/x86_64-unknown-linux-gnu/codegen-backends/*.so
/usr/share/man/man1/rustc.1
/usr/share/man/man1/rustdoc.1
