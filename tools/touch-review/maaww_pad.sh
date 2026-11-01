#!/system/bin/sh
# Inject Xbox buttons onto the display where 鸣潮 is actually showing.
# Background mode puts the game on a virtual display. The physical pad follows
# system focus (the main screen), so sendevent never reaches the game.
# `input gamepad -d <id>` does.
#
# Usage: maaww_pad.sh attack|resonance|liberation|echo|dodge|heavy|swap1|swap2|swap3|beat

set -u

disp=$(dumpsys window | awk '
    {
        i = index($0, "com.kurogame.mingchao/com.epicgames.ue4.GameActivity")
        if (i == 0) next
        rest = substr($0, i)
        if (match(rest, /displayId=[0-9]+/)) {
            v = substr(rest, RSTART, RLENGTH)
            sub("displayId=", "", v)
            print v
            exit
        }
    }
')
if [ -z "${disp:-}" ]; then
    disp=0
fi

# Android keycodes. Xbox X=attack, Y=resonance, RT=liberation, LT=echo, RB=dodge.
press() {
    code=$1
    hold_ms=$2
    input gamepad -d "$disp" keyevent --duration "$hold_ms" "$code"
}

attack() { press 99 50; }
heavy() { press 99 450; }
resonance() { press 100 60; }
liberation() { press 105 60; }
echo_skill() { press 104 60; }
dodge() { press 103 50; }
swap1() { press 19 50; }
swap2() { press 22 50; }
swap3() { press 20 50; }

beat() {
    attack
    sleep 0.08
    attack
    sleep 0.08
    attack
    resonance
    sleep 0.12
    liberation
    sleep 0.12
    echo_skill
    sleep 0.08
    heavy
    slot_file=/data/local/tmp/maaww_pad_slot
    slot=$(cat "$slot_file" 2>/dev/null || echo 0)
    case "$slot" in
        1) swap2 ;;
        2) swap3 ;;
        *) swap1 ;;
    esac
    next=$(( (slot + 1) % 3 ))
    echo "$next" > "$slot_file"
}

case "${1:-}" in
    attack) attack ;;
    heavy) heavy ;;
    resonance) resonance ;;
    liberation) liberation ;;
    echo) echo_skill ;;
    dodge) dodge ;;
    swap1) swap1 ;;
    swap2) swap2 ;;
    swap3) swap3 ;;
    beat) beat ;;
    where)
        echo "display=$disp"
        ;;
    *)
        echo "usage: maaww_pad.sh attack|heavy|resonance|liberation|echo|dodge|swap1|swap2|swap3|beat|where" >&2
        exit 2
        ;;
esac
