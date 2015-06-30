#!/bin/bash

curl -X POST http://localhost:4040/api/web-contents/fetch -d '{"url":"'$1'"}' --header "Content-Type: application/json"
