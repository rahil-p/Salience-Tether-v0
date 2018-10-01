echo "---------- Welcome to Salience TETHER ----------"

while getopts c:l:f: option
  do
    case "${option}"
      in
        c)
          CAP=${OPTARG};;
        l)
          LAG=${OPTARG};;
        f)
          FREQ=${OPTARG};;
    esac
  done

if [[ -z $CAP ]]
  then
    read -p "- Please enter a spending cap: " CAP
fi

LAG="${LAG:-1440}"
FREQ="${FREQ:-1}"

python salience.py -c $CAP -l $LAG -f $FREQ
