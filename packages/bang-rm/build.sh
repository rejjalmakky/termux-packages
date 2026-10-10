TERMUX_PKG_HOMEPAGE="https://github.com/rejjalmakky/termux-packages"
TERMUX_PKG_DESCRIPTION="BANG RM Gemini AI agent for Termux"
TERMUX_PKG_LICENSE="MIT"
TERMUX_PKG_MAINTAINER="RM <rejjalmakky@gmail.com>"
TERMUX_PKG_VERSION=0.1.0
TERMUX_PKG_REVISION=3
TERMUX_PKG_DEPENDS="python"
TERMUX_PKG_CONFLICTS="bang-rm-agent"
TERMUX_PKG_REPLACES="bang-rm-agent"

termux_step_get_source() {
    mkdir -p "$TERMUX_PKG_SRCDIR"
    cp "$TERMUX_PKG_BUILDER_DIR/agent.py" "$TERMUX_PKG_SRCDIR/"
    cp "$TERMUX_PKG_BUILDER_DIR/safety.py" "$TERMUX_PKG_SRCDIR/"
    cp "$TERMUX_PKG_BUILDER_DIR/LICENSE" "$TERMUX_PKG_SRCDIR/"
}

termux_step_make_install() {
    install -Dm755 "$TERMUX_PKG_SRCDIR/agent.py" \
        "$TERMUX_PREFIX/share/bang-rm/agent.py"

    install -Dm644 "$TERMUX_PKG_SRCDIR/safety.py" \
        "$TERMUX_PREFIX/share/bang-rm/safety.py"

    cat > "$TERMUX_PREFIX/bin/bang-rm" <<'WRAPPER'
#!/data/data/com.bangrm.termux/files/usr/bin/sh
exec python "$PREFIX/share/bang-rm/agent.py" "$@"
WRAPPER

    chmod 755 "$TERMUX_PREFIX/bin/bang-rm"
}
