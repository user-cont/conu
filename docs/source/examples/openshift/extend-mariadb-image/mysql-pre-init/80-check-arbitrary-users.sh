check_arbitrary_users() {
  if ! [[ -v MYSQL_OPERATIONS_USER && -v MYSQL_OPERATIONS_PASSWORD && -v MYSQL_DATABASE ]]; then
    echo "You need to specify all these variables: MYSQL_OPERATIONS_USER, MYSQL_OPERATIONS_PASSWORD, and MYSQL_DATABASE"
    return 1
  fi
}

if ! [ -v MYSQL_RUNNING_AS_SLAVE ]; then
  check_arbitrary_users
fi
