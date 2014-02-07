function _remove_pycs {
    find . -name "*.pyc" -exec rm {} \;
}

alias py.test="_remove_pycs; py.test"

