if [ $# -ne 1 ]; then
    echo "specify github username"
    exit 1
fi

blender -b\
    -P main.py\
    -o $1_\
    -E CYCLES\
    -f 1\
    -- $1
