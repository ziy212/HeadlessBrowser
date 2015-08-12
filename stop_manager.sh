#!/bin/bash

ps aux | grep "phantom_manager.py" | grep -v "grep" | awk '{print $2}'|xargs kill -9
ps aux | grep "phantomjs" |grep "xpan" | grep -v "grep" | awk '{print $2}'|xargs kill -9

