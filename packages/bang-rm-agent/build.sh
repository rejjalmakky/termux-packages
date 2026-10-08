TERMUX_PKG_HOMEPAGE=https://github.com/rejjalmakky
TERMUX_PKG_DESCRIPTION="BANG RM local AI agent"
TERMUX_PKG_LICENSE="MIT"
TERMUX_PKG_MAINTAINER="BANG RM <rejjalmakky@gmail.com>"
TERMUX_PKG_VERSION="0.1.0"
TERMUX_PKG_PLATFORM_INDEPENDENT=true
TERMUX_PKG_BUILD_IN_SRC=true

termux_step_make_install() {
    install -Dm700 "$TERMUX_PKG_BUILDER_DIR/bang-rm" \
        "$TERMUX_PREFIX/bin/bang-rm"
}
