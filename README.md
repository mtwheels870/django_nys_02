docker build -f Dockerfile.psql --secret id=id=aws,src=$HOME/.aws/credentials --build-arg ARG_NAME="stuff" . -t "mtw_psql:01"
