PROJECT := "steamboat"
OPEN := if os() == "macos" { "open" } else { "xdg-open" }
VERSION := `poetry version -s`

# format code with ruff
fmt:
    poetry run ruff format .
    poetry run ruff check --fix .

# check format and lint with ruff
check-fmt:
    poetry run ruff format --check .
    poetry run ruff check .

# lint code with ruff
lint:
    poetry run ruff check .

# install latest version with poetry
install:
    poetry install --no-interaction

# run tests with pytest
test:
    poetry run pytest -v

# check formatting and linting
check: check-fmt lint

# prints out the commands to run to tag the release and push it
tag:
    @echo "Run \`git tag -a {{ VERSION }} -m <message>\` to tag the release"
    @echo "Then run \`git push origin {{ VERSION }}\` to push the tag"

# build a python release
build:
    poetry build --no-interaction
