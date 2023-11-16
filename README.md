# Mealie Tools

## 🔗 Table of Contents

* [🔗 Table of Contents](#%F0%9F%94%97-table-of-contents)
* [❔ Why](#%E2%9D%94-why)
* [⚠️ Disclaimer](#%E2%9A%A0%EF%B8%8F-disclaimer)
* [🧾 Prerequisites](#%F0%9F%A7%BE-prerequisites)
* [💻 Installation](#%F0%9F%92%BB-installation)
* [🐳 Dev Container](#%F0%9F%90%B3-dev-container)
* [⚙️ Usage](#%E2%9A%99%EF%B8%8F-usage)
  * [Goodfood Scans Analyser](#goodfood-scans-analyser)
  * [Goodfood Scans Organiser](#goodfood-scans-organiser)
  * [Goodfood Recipe Analyser](#goodfood-recipe-analyser)
  * [Goodfood Import](#goodfood-import)
  * [Batch Recipe Updater](#batch-recipe-updater)
* [🙋‍♂️ Support \& Assistance](#%F0%9F%99%8B%E2%80%8D%E2%99%82%EF%B8%8F-support--assistance)
* [🤝 Contributing](#%F0%9F%A4%9D-contributing)
* [📋 References](#%F0%9F%93%8B-references)
* [👋 Acknowledgements](#%F0%9F%91%8B-acknowledgements)
* [⚖️ License](#%E2%9A%96%EF%B8%8F-license)

## ❔ Why

After using [Mealie](https://github.com/mealie-recipes/mealie) and its API for a
while, I noticed that a lot of what I wanted to do with Mealie could be
automated using scripts. These save time and reduce human input error to a
minimum.

## ⚠️ Disclaimer

These scripts were meant to be used and then thrown away. They were never
intended to be clean and reusable code. While they can be used as a starting
point, there are several changes required to make them stable, secure and robust
and these are outside the scope of this project.

## 🧾 Prerequisites

To these tools as-is, you'll need:

* A Mealie instance with API access
* Python 3 (was tested with version `3.11.6`)
* pip (if using Python `<3.4`)

## 💻 Installation

To install, run this command: `pip install -r tools/requirements.txt`

## 🐳 Dev Container

This project has a dev container defined with all prerequisites installed. The
container can be used for development or for running the tools.

## ⚙️ Usage

### Goodfood Scans Analyser

Runs OCR on Goodfood recipe scans' front page.

``` shell
python tools/goodfood-scans-analyser.py \
  -v DEBUG \
  -i scans/ \
  -o ocrData/ \
  -u https://mealie.your-domain.com \
  -t YOUR_API_TOKEN
```

### Goodfood Scans Organiser

Interactively organises freshly scanned files. Files will be organised like this:

``` text
output                  # Output folder defined by --ocrDataPath
├── Recipe Title A
│   ├── Back.png        # Back side scan
│   ├── Front.png       # Front side scan
│   ├── metadata.json   # Metadata to be used by other tools
│   └── ocr-front.json  # Front side raw OCR data
├── Recipe Title B
├── ...
└── Recipe Title Z
```

`ocrDataPath` expects a path where files produced by [Goodfood Scans
Analyser](#goodfood-scans-analyser) are located.

``` shell
python tools/goodfood-scans-organiser.py \
  -v DEBUG \
  -i scans/ \
  -o sorted/ \
  --ocrDataPath ocrData/
```

### Goodfood Recipe Analyser

Runs OCR on Goodfood recipes' pages (front & back) and stores the data in files.
Using this tool is faster than calling Mealie's API (i.e. faster than [Goodfood
Scans Analyser](#goodfood-scans-analyser)), as it completely removes Mealie's
overhead and does OCR directly. This script requires `tesseract` to be
installed. The dev container includes `tesseract` and can be used to run this
script.

`inputPath` expects a path where files produced by [Goodfood Scans
Organiser](#goodfood-scans-organiser) are located.

``` shell
python tools/goodfood-recipes-analyser.py \
  -v DEBUG \
  -i sorted/
```

### Goodfood Import

Script to import Goodfood recipes into Mealie automatically.

`inputPath` expects a path where files produced by [Goodfood Scans
Organiser](#goodfood-scans-organiser) are located.

``` shell
python tools/goodfood-mealie-import.py \
  -v DEBUG \
  -i sorted/ \
  -o imported/ \
  -u https://mealie.your-domain.com \
  -t YOUR_API_TOKEN
```

### Batch Recipe Updater

Script to update Mealie recipes in batches.

``` shell
python tools/batch-recipe-updater.py \
  -v DEBUG \
  -u https://mealie.your-domain.com \
  -t YOUR_API_TOKEN
```

## 🙋‍♂️ Support & Assistance

* ❤️ Please review the [Code of Conduct](.github/CODE_OF_CONDUCT.md) for
     guidelines on ensuring everyone has the best experience interacting with
     the community.
* 🙋‍♂️ Take a look at the [support](.github/SUPPORT.md) document
     on guidelines for tips on how to ask the right questions.
* 🐞 For all features/bugs/issues/questions/etc, [head over
  here](https://github.com/Bibz87/mealie-tools/issues/new/choose).

## 🤝 Contributing

* ❤️ Please review the [Code of Conduct](.github/CODE_OF_CONDUCT.md) for
     guidelines on ensuring everyone has the best experience interacting with
    the community.
* 📋 Please review the [contributing](.github/CONTRIBUTING.md) doc for
     submitting issues/a guide on submitting pull requests and helping out.

## 📋 References

* [Mealie](https://github.com/mealie-recipes/mealie)
* [Mealie API documentation](https://nightly.mealie.io/documentation/getting-started/api-usage/)

## 👋 Acknowledgements

Huge thanks to [@lrstanley](https://github.com/lrstanley) for letting me use his repository documentation
templates!

## ⚖️ License

[![Creative Commons
Licence](https://i.creativecommons.org/l/by-nc/4.0/88x31.png)](http://creativecommons.org/licenses/by-nc/4.0/)

This work is licensed under a [Creative Commons Attribution-NonCommercial 4.0
International License](http://creativecommons.org/licenses/by-nc/4.0/).

_Also located [here](LICENSE)_
