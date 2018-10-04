create_arbitrary_users() {
  # Do not care what option is compulsory here, just create what is specified
  log_info "Creating user specified by MYSQL_OPERATIONS_USER (${MYSQL_OPERATIONS_USER}) ..."
mysql $mysql_flags <<EOSQL
    CREATE USER '${MYSQL_OPERATIONS_USER}'@'%' IDENTIFIED BY '${MYSQL_OPERATIONS_PASSWORD}';
EOSQL

  log_info "Granting privileges to user ${MYSQL_OPERATIONS_USER} for ${MYSQL_DATABASE} ..."
mysql $mysql_flags <<EOSQL
      GRANT ALL ON \`${MYSQL_DATABASE}\`.* TO '${MYSQL_OPERATIONS_USER}'@'%' ;
      FLUSH PRIVILEGES ;
EOSQL
}

if ! [ -v MYSQL_RUNNING_AS_SLAVE ]; then
  create_arbitrary_users
fi
