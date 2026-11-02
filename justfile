set shell := ["bash", "-euo", "pipefail", "-c"]
set quiet
set fallback
set positional-arguments
set default-list

uv_dev := "uv run --extra=dev"

# Run ruff format
[group('linting')]
format *args=".":
    {{ uv_dev }} ruff format "$@"

# Run ruff check
[group('linting')]
check *args=".":
    {{ uv_dev }} ruff check "$@"

# Format Django templates with djangofmt.
[group('linting')]
djangofmt *args="":
    -{{ uv_dev }} djangofmt {{ args }} .

[group('linting')]
djangofmt-check:
    just djangofmt
    git diff --exit-code -- '*.html' || (echo "HTML templates are not formatted. Run 'just djangofmt' to fix." && exit 1)

# Check that VCS files and the sdist match (CI runs this)
[group('linting')]
check-manifest:
    uv run --no-project --with check-manifest check-manifest

# Run all formatters and linters
[group('linting')]
fmt: (check "--fix") format djangofmt && fmt-done

[private]
fmt-done:
    echo '{{ GREEN }}Formatting complete{{ NORMAL }}'

# Run all code quality checks
[group('linting')]
fmt-check: (format "--check") check djangofmt-check && check-done

[private]
check-done:
    echo '{{ GREEN }}All checks passed{{ NORMAL }}'

# Run tests (installs pretalx if not already present)
[group('tests')]
test *args: ensure-pretalx
    {{ uv_dev }} pytest "$@"

# Install the pretalx release this plugin is tested with
[group('development')]
install-pretalx:
    uv pip install "pretalx[dev]==2026.2.1"

# Install a local editable copy of pretalx (for development)
[group('development')]
install-pretalx-local path:
    uv pip install -e "{{ path }}[dev]"

# Ensure pretalx is importable, installing the release if needed
[private]
ensure-pretalx:
    {{ uv_dev }} python -c "import pretalx" 2>/dev/null || just install-pretalx

# Languages the plugin is translated into, besides English
languages := "de"

# Generate (or update) the locale files for all languages
[group('development')]
[script('bash')]
localegen: ensure-pretalx
    cd pretalx_checklister
    args=()
    for language in {{ languages }}; do args+=(-l "$language"); done
    {{ uv_dev }} django-admin makemessages --add-location file "${args[@]}"

# Compile locale files
[group('development')]
[script('bash')]
localecompile: ensure-pretalx
    cd pretalx_checklister
    {{ uv_dev }} django-admin compilemessages
