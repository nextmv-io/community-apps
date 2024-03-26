package mip

import (
	"os"
	"slices"
	"strings"
	"testing"

	"github.com/nextmv-io/sdk/golden"
	"gopkg.in/yaml.v2"
)

func TestMain(m *testing.M) {
	code := m.Run()
	os.Exit(code)
}

const configFile = "workflow-configuration.yml"

type ScriptConfig struct {
	Name   string `yaml:"name"`
	Silent bool   `yaml:"silent"`
	Skip   bool   `yaml:"skip"`
}

type AppConfig struct {
	Name    string         `yaml:"name"`
	Scripts []ScriptConfig `yaml:"scripts"`
}

type Config struct {
	Apps []AppConfig `yaml:"apps"`
}

func (s Config) scriptConfig(app string, script string) ScriptConfig {
	for _, appConfig := range s.Apps {
		if appConfig.Name == app {
			for _, scriptConfig := range appConfig.Scripts {
				if scriptConfig.Name == script {
					return scriptConfig
				}
			}
		}
	}
	return ScriptConfig{}
}

func TestGolden(t *testing.T) {
	// Read info on scripts to skip
	fileContent, err := os.ReadFile(configFile)
	if err != nil {
		t.Fatalf("error reading config file: %v", err)
	}
	var config Config
	err = yaml.Unmarshal(fileContent, &config)
	if err != nil {
		t.Fatalf("error unmarshalling config file: %v", err)
	}

	// Define replacements
	replacements := []golden.VolatileRegexReplacement{
		// Replace "duration": 0.354 with "duration":0.123
		{Regex: `duration":\d+\.\d+`, Replacement: `duration":0.123`},
		// Replace xpress.init(...) with
		// xpress.init("path/to/xpress")
		{Regex: `xpress\.init\(.*\)`, Replacement: `xpress.init("path/to/xpress")`},
	}

	// Run all readme tests
	dirs, err := os.ReadDir(".")
	if err != nil {
		t.Fatalf("error reading directory: %v", err)
	}
	for _, dir := range dirs {
		if !dir.IsDir() {
			continue
		}
		app := dir.Name()

		// Find all scripts of the app
		scripts := []string{}
		appDir, err := os.ReadDir(app)
		if err != nil {
			t.Fatalf("error reading app directory: %v", err)
		}
		for _, script := range appDir {
			if script.IsDir() {
				continue
			}
			scriptFile := script.Name()
			if strings.HasSuffix(scriptFile, ".sh") {
				scripts = append(scripts, scriptFile)
			}
		}
		slices.Sort(scripts)

		// Run all scripts of the app
		for _, script := range scripts {
			scriptConfig := config.scriptConfig(app, script)
			if scriptConfig.Skip {
				continue
			}
			t.Run(app+"/"+script, func(t *testing.T) {
				golden.BashTestFile(
					t,
					app+"/"+script,
					golden.BashConfig{
						DisplayStdout: !scriptConfig.Silent,
						WorkingDir:    "../../" + app,
						OutputProcessConfig: golden.OutputProcessConfig{
							VolatileRegexReplacements: replacements,
						},
					},
				)
			})
		}
	}
}
