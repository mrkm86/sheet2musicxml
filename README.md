# Sheet to MusicXML

`sheet2musicxml` is a skills-only plugin for transcribing sheet music PDFs, scans, screenshots, and photos into editable MusicXML. It works with Codex and Claude Code. The plugin does not bundle a recognition model or require MuseScore, Dorico, or another notation editor.

The required deliverable is a `.musicxml` file. An agent reads the source images, uses available optical music recognition (OMR) as a draft when helpful, checks the notation against the source, and runs the bundled Python checks. MuseScore, Dorico, or another editor can provide an additional visual review, but the core workflow and checks run without them.

## Install

### Codex

Add this repository as a plugin marketplace:

```sh
codex plugin marketplace add mrkm86/sheet2musicxml
codex plugin add sheet2musicxml@sheet2musicxml
```

The same plugin can be installed from the Codex app's plugin directory. The skill is named `transcribe` inside the `sheet2musicxml` plugin. See the [Codex plugin packaging guide](https://developers.openai.com/plugins/build/plugins) for marketplace installation and updates.

### Claude Code

```sh
claude plugin marketplace add mrkm86/sheet2musicxml
claude plugin install sheet2musicxml@sheet2musicxml --scope user
```

The skill appears as `/sheet2musicxml:transcribe`. See the [Claude Code plugin guide](https://code.claude.com/docs/en/plugins/install) for other install scopes and updates.

## Use

Attach an ordered score PDF or one or more score images and ask the agent to convert them to MusicXML. For example: “Convert these four score pages to MusicXML and review the ties and accidentals against the images.”

The bundled checkers use Python 3's standard library. PDF rendering and OMR may require tools available on the user's machine, but no specific tool is required by this package. If the source is too blurry to read reliably, the agent should identify the affected measures and request a clearer image rather than inventing notes.

Optional MuseScore-native comparison scripts are included for users who provide `.mscz` corrections or request app-specific validation. They are not part of the required conversion path.

## Scope

This repository covers source images through an editable MusicXML file. App-native project files and editor-specific playback settings are optional follow-up work. MusicXML import behavior can vary between notation editors; the score image remains the authority for transcription accuracy.

## Development and releases

Develop in a checkout of this repository. Other machines should install released versions through the plugin marketplace, without editing installed package files. Commit changes and publish a version tag before updating an installation.

This repository contains only generic skill instructions, format references, and check scripts. It does not include users' scores, generated MusicXML, local paths, credentials, or private correction logs.

## License

MIT. See [LICENSE](LICENSE).
