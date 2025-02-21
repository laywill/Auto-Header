#!/bin/bash

set -euo pipefail

MESSAGE='Hello World!'

hello () {
   echo "$MESSAGE"
}

hello
