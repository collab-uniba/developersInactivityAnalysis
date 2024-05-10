#!/bin/bash

# File containing the tokens
file="tokens.txt"

# Read the file line by line
while IFS= read -r token
do
    # Use curl to send a GET request to the GitHub API
    response=$(curl --silent --request GET \
    --url "https://api.github.com/octocat" \
    --header "Authorization: Bearer $token" \
    --header "X-GitHub-Api-Version: 2022-11-28")

    # Check if the response is a JSON object
    if [[ "$response" =~ ^\{.*\}$ ]]; then
        # Parse the JSON response with jq to get the message field
        message=$(echo "$response" | jq -r .message)

        # Check if the message is "Bad credentials"
        if [[ "$message" == "Bad credentials" ]]; then
            echo "Token $token is invalid."
        else
            echo "Token $token is valid."
        fi
    else
        echo "Token $token is valid."
    fi
done <"$file"
