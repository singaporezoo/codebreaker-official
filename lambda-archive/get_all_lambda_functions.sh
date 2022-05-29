# Parallelly download all aws-lambda functions
# Assumes you have ran `aws configure` and have output-mode as "text"
# Works with "aws-cli/1.16.72 Python/3.6.7 Linux/4.15.0-42-generic botocore/1.12.62"

download_code () {
    local OUTPUT=$1
    aws lambda get-function --function-name $OUTPUT --query 'Code.Location' | xargs wget -O ./lambda_functions/$OUTPUT.zip
}

mkdir -p lambda_functions

for run in $(aws lambda list-functions | cut -f 6 | xargs);
do
	download_code "$run" &
done

echo "Completed Downloading all the Lamdba Functions!"

# If you want to download only ones with specific prefix
# https://github.com/sambhajis-gdb/download_all_lambda_function/blob/master/get_lambda_with_prefix.sh
# Credits to https://stackoverflow.com/users/6908140/sambhaji-sawant for the
