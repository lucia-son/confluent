#!/bin/bash

for var in `seq  1 2` ; do 
        echo '{"BagItem": { "id":'  $var ',' '"name": "book' $var '"' >> bagitem.json
	echo "Sent Message fo Book item of ID" $var  
done
