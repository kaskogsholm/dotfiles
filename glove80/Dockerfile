FROM nixpkgs/nix:nixos-23.11

ENV PATH=/root/.nix-profile/bin:/usr/bin:/bin

RUN set -euo pipefail; \
    nix-env -iA cachix -f https://cachix.org/api/v1/install; \
    cachix use moergo-glove80-zmk-dev; \
    mkdir /config; \
    git clone --mirror https://github.com/moergo-sc/zmk /zmk; \
    GIT_DIR=/zmk git worktree add --detach /src

RUN cd /src && nix-shell --run true -A zmk ./default.nix

COPY --chmod=755 entrypoint.sh /bin/entrypoint.sh
ENTRYPOINT ["/bin/entrypoint.sh"]
