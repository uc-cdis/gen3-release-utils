_script()
{
  _suggestions="$(cat ./environments_list.txt)"

  local cur
  COMPREPLY=()
  cur="${COMP_WORDS[COMP_CWORD]}"
  COMPREPLY=( $(compgen -W "${_suggestions}" -- ${cur}) )

  return 0
}
complete -o nospace -F _script ./config-diff
