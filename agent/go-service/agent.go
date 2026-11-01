package main

import (
	"os"
	"path/filepath"
	"strings"

	"github.com/MaaXYZ/maa-framework-go/v4"
	"github.com/rs/zerolog/log"
	"github.com/yuanhao-wei/maa-ww/agent/go-service/account"
	"github.com/yuanhao-wei/maa-ww/agent/go-service/combat"
)

// runAgent starts the MaaFramework Agent Server subprocess loop.
// Hosts (MaaPiCli / MaaFwApp) launch: agent/go-service <socket_id>
func runAgent(identifier string) {
	log.Info().
		Str("identifier", identifier).
		Msg("Starting agent server")

	libDir := os.Getenv("MAAFW_BINARY_PATH")
	if libDir == "" {
		libDir = filepath.Join(getCwd(), "maafw")
	}
	libDir = prepareAgentLibDir(libDir)
	log.Info().Str("libDir", libDir).Msg("Initializing MAA framework")

	if err := maa.Init(maa.WithLibDir(libDir)); err != nil {
		log.Fatal().Err(err).Msg("Failed to initialize MAA framework")
	}
	defer maa.Release()
	log.Info().Msg("MAA framework initialized")

	userPath := getCwd()
	if err := maa.ConfigInitOption(userPath, "{}"); err != nil {
		log.Warn().Str("userPath", userPath).Err(err).Msg("Failed to init toolkit config option")
	}

	combat.Register()
	account.Register()

	if err := maa.AgentServerStartUp(identifier); err != nil {
		log.Fatal().Err(err).Msg("Failed to start agent server")
	}
	log.Info().Msg("Agent server started")

	maa.AgentServerJoin()
	maa.AgentServerShutDown()
	log.Info().Msg("Agent server shutdown")
}

func getCwd() string {
	cwd, err := os.Getwd()
	if err != nil {
		return "."
	}
	return cwd
}

// prepareAgentLibDir builds a filtered native-lib dir for dlopen.
//
// Host sets LD_LIBRARY_PATH={nativeLibs}. That folder also contains AndroidX
// libtracing_perfetto.so, which shadows system symbols and makes
// dlopen(libMaaFramework) fail on Android 15. Keep Maa/OCR deps only.
func prepareAgentLibDir(src string) string {
	entries, err := os.ReadDir(src)
	if err != nil {
		log.Warn().Err(err).Str("src", src).Msg("agent lib dir unreadable, using as-is")
		return src
	}

	dst := filepath.Join("/data/local/tmp", "maaww-maa-libs")
	if err := os.MkdirAll(dst, 0o755); err != nil {
		log.Warn().Err(err).Str("dst", dst).Msg("cannot create filtered lib dir, using as-is")
		return src
	}

	// Drop stale links so removed deps do not linger.
	if old, err := os.ReadDir(dst); err == nil {
		for _, e := range old {
			_ = os.Remove(filepath.Join(dst, e.Name()))
		}
	}

	linked := 0
	for _, e := range entries {
		name := e.Name()
		if e.IsDir() || !strings.HasSuffix(name, ".so") {
			continue
		}
		if skipAgentLib(name) {
			continue
		}
		from := filepath.Join(src, name)
		to := filepath.Join(dst, name)
		_ = os.Remove(to)
		if err := os.Symlink(from, to); err != nil {
			log.Warn().Err(err).Str("name", name).Msg("symlink agent lib failed")
			continue
		}
		linked++
	}
	if linked == 0 {
		log.Warn().Str("src", src).Msg("no agent libs linked, using source dir")
		return src
	}

	_ = os.Setenv("MAAFW_BINARY_PATH", dst)
	_ = os.Setenv("LD_LIBRARY_PATH", dst)
	log.Info().Str("dst", dst).Int("linked", linked).Msg("filtered agent native libs")
	return dst
}

func skipAgentLib(name string) bool {
	switch {
	case strings.Contains(name, "tracing_perfetto"):
		return true
	case strings.HasPrefix(name, "libandroidx."):
		return true
	case name == "libdatastore_shared_counter.so":
		return true
	case name == "libgo-service.so", name == "libagentexec.so", name == "liblauncher.so", name == "libbridge.so":
		return true
	default:
		return false
	}
}
