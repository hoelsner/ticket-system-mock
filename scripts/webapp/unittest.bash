#!/bin/bash
#
# This script runs the unit tests for the web application. It should be run from the root of the repository.
#
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "$script_dir/../.." && pwd)"
webapp_dir="$repo_root/src/webapp"
python_bin="$webapp_dir/.venv/bin/python3"

cd "$webapp_dir" || exit 1

if [[ ! -x "$python_bin" ]]; then
    echo "python interpreter not found at $python_bin"
    exit 1
fi

collect_test_labels() {
    local test_packages=()

    while IFS= read -r init_file; do
        local rel_path module_name

        rel_path="${init_file#"$webapp_dir/"}"
        module_name="${rel_path%/__init__.py}"
        module_name="${module_name//\//.}"
        test_packages+=("$module_name")
    done < <(find "$webapp_dir/djangoapp" -type f -path "*/tests/__init__.py" | sort)

    if [[ ${#test_packages[@]} -eq 0 ]]; then
        return 1
    fi

    printf '%s\n' "${test_packages[@]}"
}

# Runs a command silently; only prints output if the command fails.
run_silent() {
    local tmpfile
    tmpfile=$(mktemp)
    "$@" > "$tmpfile" 2>&1
    local status=$?
    if [ $status -ne 0 ]; then
        cat "$tmpfile"
        rm -f "$tmpfile"
        exit $status
    fi
    rm -f "$tmpfile"
    echo "OK"
}

printf "running unit tests... "
mapfile -t test_labels < <(collect_test_labels)

if [[ ${#test_labels[@]} -eq 0 ]]; then
    echo "no internal tests packages found under $webapp_dir/djangoapp"
    exit 1
fi

run_silent env "$python_bin" manage.py test --noinput "${test_labels[@]}"
