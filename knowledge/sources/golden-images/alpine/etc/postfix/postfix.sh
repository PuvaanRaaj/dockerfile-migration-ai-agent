#!/bin/sh

# Change Hostname
  if [ "$AWS_EXECUTION_ENV" = "AWS_ECS_FARGATE" ]; then
    sed -i "s/CONTAINER_HOSTNAME/$CONTAINER_HOSTNAME/g" /etc/postfix/main.cf
    sed -i "s/MAIL_HOST:MAIL_PORT/$MAIL_HOST:$MAIL_PORT/g" /etc/postfix/main.cf
    echo "root: $SYSADM_EMAIL" > /etc/aliases
    echo "root    $SYSADM_EMAIL" > /etc/postfix/virtual
    newaliases
    postmap /etc/postfix/virtual
  fi

# call "postfix stop" when exiting
trap "{ echo Stopping postfix; /usr/sbin/postfix stop; exit 0; }" EXIT

# start postfix
/usr/sbin/postfix -c /etc/postfix start
# avoid exiting
sleep infinity
