package combat

import (
	"embed"
	"image"
	_ "image/png"
	"math"
	"path"
	"strings"
	"sync"

	"github.com/rs/zerolog/log"
)

// HUD team perception (1280x720 frame, right-hand vertical column of 3 portraits).
//
// Works in any combat scene without opening the team page:
//   - identity: zero-mean NCC of the portrait face against embedded templates in teamdata/
//     (dead portraits are grayscale of the same art, so they still match);
//   - dead: the HP bar under the portrait is empty;
//   - current: the on-field character has no element badge next to its portrait.
//
// To teach it a new character, drop a 28x28 face crop (centred on the portrait) into
// teamdata/<id>.png and add the role below.

//go:embed teamdata/*.png
var teamTemplateFS embed.FS

// Role mirrors ok-ww CharType.
type Role int

const (
	RoleMainDPS Role = iota
	RoleSubDPS
	RoleHealer
)

var charRoles = map[string]Role{
	"hiyuki":  RoleMainDPS,
	"lucilla": RoleSubDPS,
	"suisui":  RoleHealer,
}

const (
	teamTplHalf     = 14
	teamSearch      = 10
	teamMatchMin    = 0.72
	teamBarBrightPx = 6 // fewer bright bar pixels than this = dead / empty
	teamBadgeMinPx  = 8
)

// Centres of the three portraits at 1280x720 (measured on 20261101 HUD shots).
var teamCenters = [3][2]int{{1172, 153}, {1172, 238}, {1172, 326}}

type teamSlot struct {
	Name  string  // "" when unknown
	Score float64 // best NCC score
	Dead  bool
	Badge bool // element badge visible = not on field
	BarPx int
}

type teamState struct {
	Slots   [3]teamSlot
	Current int // -1 unknown
}

type teamTemplate struct {
	name string
	pix  []float64 // zero-mean, 28x28
	norm float64
}

var (
	teamTplOnce sync.Once
	teamTpls    []teamTemplate
)

func loadTeamTemplates() []teamTemplate {
	teamTplOnce.Do(func() {
		entries, err := teamTemplateFS.ReadDir("teamdata")
		if err != nil {
			return
		}
		for _, e := range entries {
			if e.IsDir() || !strings.HasSuffix(e.Name(), ".png") {
				continue
			}
			f, err := teamTemplateFS.Open(path.Join("teamdata", e.Name()))
			if err != nil {
				continue
			}
			img, _, err := image.Decode(f)
			f.Close()
			if err != nil {
				continue
			}
			b := img.Bounds()
			if b.Dx() != 2*teamTplHalf || b.Dy() != 2*teamTplHalf {
				continue
			}
			g := grayPatch(img, b.Min.X, b.Min.Y, b.Dx(), b.Dy())
			zm, norm := zeroMean(g)
			teamTpls = append(teamTpls, teamTemplate{
				name: strings.TrimSuffix(e.Name(), ".png"),
				pix:  zm,
				norm: norm,
			})
		}
	})
	return teamTpls
}

func grayPatch(img image.Image, x0, y0, w, h int) []float64 {
	out := make([]float64, w*h)
	b := img.Bounds()
	for y := 0; y < h; y++ {
		for x := 0; x < w; x++ {
			px, py := x0+x, y0+y
			if px < b.Min.X || px >= b.Max.X || py < b.Min.Y || py >= b.Max.Y {
				continue
			}
			r, g, bl, _ := img.At(px, py).RGBA()
			out[y*w+x] = 0.299*float64(r>>8) + 0.587*float64(g>>8) + 0.114*float64(bl>>8)
		}
	}
	return out
}

func zeroMean(v []float64) ([]float64, float64) {
	var sum float64
	for _, x := range v {
		sum += x
	}
	mean := sum / float64(len(v))
	out := make([]float64, len(v))
	var sq float64
	for i, x := range v {
		out[i] = x - mean
		sq += out[i] * out[i]
	}
	return out, math.Sqrt(sq)
}

// matchPortrait returns the best template name and score for a portrait centred near (cx,cy).
func matchPortrait(img image.Image, cx, cy int) (string, float64) {
	tpls := loadTeamTemplates()
	if len(tpls) == 0 {
		return "", 0
	}
	size := 2 * teamTplHalf
	win := 2*teamSearch + 1
	// Gray window covering all search offsets.
	wx0, wy0 := cx-teamTplHalf-teamSearch, cy-teamTplHalf-teamSearch
	ww := size + 2*teamSearch
	g := grayPatch(img, wx0, wy0, ww, ww)
	best, bestName := -1.0, ""
	patch := make([]float64, size*size)
	for dy := 0; dy < win; dy++ {
		for dx := 0; dx < win; dx++ {
			for y := 0; y < size; y++ {
				copy(patch[y*size:(y+1)*size], g[(dy+y)*ww+dx:(dy+y)*ww+dx+size])
			}
			zm, norm := zeroMean(patch)
			if norm < 1e-6 {
				continue
			}
			for _, t := range tpls {
				var dot float64
				for i := range zm {
					dot += zm[i] * t.pix[i]
				}
				s := dot / (norm * t.norm)
				if s > best {
					best, bestName = s, t.name
				}
			}
		}
	}
	return bestName, best
}

// rgbToHSV uses OpenCV ranges: H 0..179, S/V 0..255.
func rgbToHSV(r, g, b uint8) (h, s, v int) {
	mx, mn := r, r
	if g > mx {
		mx = g
	}
	if b > mx {
		mx = b
	}
	if g < mn {
		mn = g
	}
	if b < mn {
		mn = b
	}
	v = int(mx)
	if mx == 0 {
		return 0, 0, 0
	}
	d := float64(mx) - float64(mn)
	s = int(d / float64(mx) * 255)
	if d == 0 {
		return 0, s, v
	}
	var hf float64
	switch mx {
	case r:
		hf = 60 * (float64(g) - float64(b)) / d
	case g:
		hf = 120 + 60*(float64(b)-float64(r))/d
	default:
		hf = 240 + 60*(float64(r)-float64(g))/d
	}
	if hf < 0 {
		hf += 360
	}
	return int(hf / 2), s, v
}

func pixelRGB(img image.Image, x, y int) (uint8, uint8, uint8) {
	r, g, b, _ := img.At(x, y).RGBA()
	return uint8(r >> 8), uint8(g >> 8), uint8(b >> 8)
}

// barBrightPx counts white-ish pixels on the brightest row of the HP bar band.
func barBrightPx(img image.Image, cx, cy int) int {
	best := 0
	for y := cy + 18; y < cy+34; y++ {
		n := 0
		for x := cx - 28; x < cx+28; x++ {
			r, g, b := pixelRGB(img, x, y)
			_, s, v := rgbToHSV(r, g, b)
			if v > 190 && s < 60 {
				n++
			}
		}
		if n > best {
			best = n
		}
	}
	return best
}

// badgeBluePx counts saturated blue pixels where the element badge sits.
func badgeBluePx(img image.Image, cx, cy int) int {
	n := 0
	for y := cy - 4; y < cy+20; y++ {
		for x := cx + 8; x < cx+34; x++ {
			r, g, b := pixelRGB(img, x, y)
			h, s, v := rgbToHSV(r, g, b)
			if h >= 90 && h <= 112 && s > 110 && v > 140 {
				n++
			}
		}
	}
	return n
}

// readTeam reads the HUD portrait column. prev (optional) keeps a name when the new match is weak
// (e.g. portrait covered by the switch-cooldown number).
func readTeam(img image.Image, prev *teamState) teamState {
	var st teamState
	st.Current = -1
	cur := -1
	curCount := 0
	for i, c := range teamCenters {
		cx, cy := c[0], c[1]
		name, score := matchPortrait(img, cx, cy)
		slot := teamSlot{Score: score}
		if score >= teamMatchMin {
			slot.Name = name
		} else if prev != nil {
			slot.Name = prev.Slots[i].Name
		}
		slot.BarPx = barBrightPx(img, cx, cy)
		slot.Dead = slot.BarPx < teamBarBrightPx
		slot.Badge = badgeBluePx(img, cx, cy) >= teamBadgeMinPx
		st.Slots[i] = slot
		if !slot.Dead && !slot.Badge {
			cur = i
			curCount++
		}
	}
	// Two slots claiming the same character: the weaker match falls back to the previous name.
	for i := 0; i < 3; i++ {
		for j := i + 1; j < 3; j++ {
			if st.Slots[i].Name == "" || st.Slots[i].Name != st.Slots[j].Name {
				continue
			}
			lose := j
			if st.Slots[j].Score > st.Slots[i].Score {
				lose = i
			}
			st.Slots[lose].Name = ""
			if prev != nil && prev.Slots[lose].Name != st.Slots[3-i-j].Name && prev.Slots[lose].Name != st.Slots[i+j-lose].Name {
				st.Slots[lose].Name = prev.Slots[lose].Name
			}
		}
	}
	// Everyone "dead" at once = HUD dimmed/hidden (cutscene, liberation), not a wipe.
	if st.Slots[0].Dead && st.Slots[1].Dead && st.Slots[2].Dead {
		if prev != nil {
			out := *prev
			out.Current = -1
			return out
		}
		for i := range st.Slots {
			st.Slots[i].Dead = false
		}
		return st
	}
	// HUD not readable (no portrait recognised): do not trust bar/badge heuristics.
	known := 0
	for _, s := range st.Slots {
		if s.Name != "" {
			known++
		}
	}
	if known == 0 {
		for i := range st.Slots {
			st.Slots[i].Dead = false
		}
		return st
	}
	if curCount == 1 {
		st.Current = cur
	}
	return st
}

func (t teamState) role(i int) (Role, bool) {
	r, ok := charRoles[t.Slots[i].Name]
	return r, ok
}

// nextAlive returns the next living slot after cur in cyclic order, or cur when nobody else is alive.
func (t teamState) nextAlive(cur int) int {
	if t.aliveCount() == 0 {
		return (cur + 1) % 3 // unreadable HUD: cyclic fallback
	}
	for k := 1; k <= 3; k++ {
		n := (cur + k) % 3
		if n != cur && !t.Slots[n].Dead {
			return n
		}
	}
	return cur
}

func (t teamState) summary() string {
	var sb strings.Builder
	for i, s := range t.Slots {
		if i > 0 {
			sb.WriteString(" | ")
		}
		name := s.Name
		if name == "" {
			name = "?"
		}
		sb.WriteString(name)
		if s.Dead {
			sb.WriteString("(dead)")
		}
		if i == t.Current {
			sb.WriteString("*")
		}
	}
	return sb.String()
}

// logTeamChange logs the roster only when it changed.
func logTeamChange(last *string, t teamState) bool {
	s := t.summary()
	if s == *last {
		return false
	}
	*last = s
	log.Info().Str("team", s).Msg("CombatLoop: team")
	return true
}

func (t teamState) aliveCount() int {
	n := 0
	for _, s := range t.Slots {
		if !s.Dead {
			n++
		}
	}
	return n
}
