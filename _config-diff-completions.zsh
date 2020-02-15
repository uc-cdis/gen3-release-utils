#compdef _config-diff ./config-diff

function _config-diff {
    # load environments list line-by-line into an array
    suggestions=($(cat ./environments_list.txt))

    compadd $suggestions
}
