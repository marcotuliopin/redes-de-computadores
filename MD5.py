while
    message= receive
    while( nao tem \n)
          message+=message
    chk=checksum(message)
    send(chk)
    send(\n)